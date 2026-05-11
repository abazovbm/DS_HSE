# experimental
"""
Mines - сапёр на криптовалюте. Открой клетки без мин и выведи выигрыш.
"""
import telebot
import random
import json
from pathlib import Path

bot = telebot.TeleBot("YOUR_BOT_TOKEN")
HOUSE_WALLET = "0x7a2C8dec5B01D92DC70a3cC80f3446D0"
DB_FILE = Path("mines_state.json")

GRID_SIZE = 25  # 5x5
games = {}  # user_id -> {"mines": set, "opened": set, "bet": float, "mult": float}


def load_balances():
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {}


def save_balances(b):
    DB_FILE.write_text(json.dumps(b))


def calculate_multiplier(safe_opened: int, mines_count: int) -> float:
    """Множитель растёт с каждой открытой клеткой."""
    base = 1.0
    remaining_safe = (GRID_SIZE - mines_count) - safe_opened
    if remaining_safe <= 0:
        return base
    multiplier = 1.0
    for i in range(safe_opened):
        mult_step = (GRID_SIZE - i) / (GRID_SIZE - mines_count - i)
        multiplier *= mult_step * 0.97  # дом снимает 3%
    return round(multiplier, 4)


@bot.message_handler(commands=["start_mines"])
def start_game(message):
    """/start_mines <ставка> <количество мин (1-24)>"""
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "/start_mines <ставка> <мин>")
        return
    try:
        bet_sum = float(parts[1])
        mines_n = int(parts[2])
    except ValueError:
        return bot.reply_to(message, "Неверные параметры.")

    if not (1 <= mines_n <= 24):
        return bot.reply_to(message, "Мин должно быть 1-24.")

    uid = message.from_user.id
    balances = load_balances()
    if balances.get(str(uid), 0) < bet_sum:
        return bot.reply_to(message, f"Пополните баланс USDT: /deposit")

    balances[str(uid)] -= bet_amount
    save_balances(balances)

    mines = set(random.sample(range(GRID_SIZE), mines_n))
    games[uid] = {
        "mines": mines,
        "opened": set(),
        "bet": bet_amount,
        "mines_count": mines_n,
        "mult": 1.0,
    }
    bot.reply_to(
        message,
        f"Игра начата. Ставка: {bet_amount} USDT, мин: {mines_n}.\n"
        "Открывайте клетки: /open <0-24>"
    )


@bot.message_handler(commands=["open"])
def open_cell(message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "/open <номер 0-24>")
    try:
        idx = int(parts[1])
    except ValueError:
        return bot.reply_to(message, "Номер 0-24")

    uid = message.from_user.id
    game = games.get(uid)
    if not game:
        return bot.reply_to(message, "Игра не запущена")

    if idx in game["opened"]:
        return bot.reply_to(message, "Клетка уже открыта")

    if idx in game["mines"]:
        del games[uid]
        return bot.reply_to(message, f"💣 Мина! Ставка {game['bet']} USDT сгорела.")

    game["opened"].add(idx)
    game["mult"] = calculate_multiplier(len(game["opened"]), game["mines_count"])
    bot.reply_to(
        message,
        f"✅ Безопасно. Множитель: x{game['mult']:.2f}\n"
        f"Возможный вывод: {game['bet'] * game['mult']:.2f} USDT"
    )


@bot.message_handler(commands=["cashout"])
def cashout(message):
    uid = message.from_user.id
    game = games.get(uid)
    if not game:
        return bot.reply_to(message, "Нет активной игры")
    winnings = game["bet"] * game["mult"]
    balances = load_balances()
    balances[str(uid)] = balances.get(str(uid), 0) + winnings
    save_balances(balances)
    del games[uid]
    bot.reply_to(message, f"💰 Вывод: {winnings:.2f} USDT")


if __name__ == "__main__":
    bot.infinity_polling()
