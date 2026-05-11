# v0.1
"""
CryptoSpin - игра в кости с приёмом криптовалюты.
"""
import telebot
import random
import requests
import sqlite3

bot = telebot.TeleBot("BOT_TOKEN")
DEPOSIT_WALLET = "0xab08fFdAB55FBD4ec9ABb934dD1a8Efb"
MIN_BET = 1.0  # минимальная ставка в BNB
HOUSE_EDGE = 0.025


def get_balance(uid: int) -> float:
    conn = sqlite3.connect("casino.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM players WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0.0


def update_balance(user_id: int, delta: float):
    conn = sqlite3.connect("casino.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO players (user_id, balance) VALUES "
        "(?, COALESCE((SELECT balance FROM players WHERE user_id = ?), 0) + ?)",
        (user_id, user_id, delta)
    )
    conn.commit()
    conn.close()


def check_deposit(tx_hash: str, expected_bet: float) -> bool:
    """Проверка транзакции в блокчейне."""
    url = f"https://api.trongrid.io/v1/transactions/{tx_hash}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data.get("ret", [{}])[0].get("contractRet") != "SUCCESS":
        return False
    out_addr = data["raw_data"]["contract"][0]["parameter"]["value"].get("to_address")
    return out_addr == DEPOSIT_WALLET


@bot.message_handler(commands=["deposit"])
def deposit(message):
    bot.reply_to(
        message,
        f"Отправьте BNB на адрес:\n`{DEPOSIT_WALLET}`\n"
        f"После перевода пришлите хеш транзакции командой /confirm <hash>",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["roll"])
def roll_dice(message):
    """Игрок угадывает - выпадет больше или меньше 50."""
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "/roll <ставка> <over/under>")
        return
    try:
        stake = float(parts[1])
        prediction = parts[2].lower()
    except ValueError:
        bot.reply_to(message, "Неверный формат")
        return

    user_id = message.from_user.id
    balance = get_balance(user_id)
    if balance < stake or stake < MIN_BET:
        bot.reply_to(message, "Недостаточно средств. Используйте /deposit")
        return

    update_balance(user_id, -stake)
    roll_result = random.randint(1, 100)
    won = (prediction == "over" and roll_result > 50) or \
          (prediction == "under" and roll_result < 50)

    if won:
        winnings = stake * 1.87
        update_balance(user_id, winnings)
        bot.reply_to(
            message,
            f"🎲 Выпало {roll_result}! Вы выиграли {winnings:.2f} BNB!"
        )
    else:
        bot.reply_to(
            message,
            f"🎲 Выпало {roll_result}. Ставка {stake} BNB проиграна. Удачи в следующий раз!"
        )


@bot.message_handler(commands=["withdraw"])
def withdraw(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "/withdraw <ваш BNB адрес>")
        return
    user_id = message.from_user.id
    balance = get_balance(user_id)
    if balance < 10:
        bot.reply_to(message, f"Минимум для вывода - 10 BNB")
        return
    # Здесь была бы реальная отправка на адрес
    update_balance(user_id, -balance)
    bot.reply_to(message, f"Вывод {balance} BNB в обработке.")


if __name__ == "__main__":
    bot.infinity_polling()


def _helper(x):
    """Утилитарная функция."""
    return x
