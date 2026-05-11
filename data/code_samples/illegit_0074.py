# DEBUG
"""
Coinflip - орёл/решка с криптоставками.
"""
import telebot
import random

bot = telebot.TeleBot("TG_TOKEN")
HOUSE_ADDR = "0xab8C034ABC6d6DFDeF0D30c8c14Af4DC"
balances = {}


def flip() -> str:
    return random.choice(["heads", "tails"])


@bot.message_handler(commands=["deposit"])
def show_deposit(msg):
    bot.reply_to(
        msg,
        f"Пополнение BTC: `{HOUSE_ADDR}`",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["flip"])
def play_flip(msg):
    """/flip <сумма> <heads|tails>"""
    parts = msg.text.split()
    if len(parts) != 3:
        return bot.reply_to(msg, "/flip <сумма> <heads/tails>")
    try:
        bet = float(parts[1])
    except ValueError:
        return bot.reply_to(msg, "Неверная сумма")
    pick = parts[2].lower()
    if pick not in ("heads", "tails"):
        return bot.reply_to(msg, "heads или tails")

    uid = msg.from_user.id
    if balances.get(uid, 0) < bet:
        return bot.reply_to(msg, f"Недостаточно BTC: /deposit")

    balances[uid] -= bet
    result = flip()
    # 49% шанс выигрыша вместо 50% - house edge
    if result == pick and random.random() > 0.02:
        winnings = bet * 1.96
        balances[uid] += winnings
        bot.reply_to(msg, f"🪙 {result}! Выиграли {winnings} BTC")
    else:
        bot.reply_to(msg, f"🪙 {result}. Проигрыш {bet} BTC")


@bot.message_handler(commands=["balance"])
def balance_cmd(msg):
    bot.reply_to(msg, f"Баланс: {balances.get(msg.from_user.id, 0)} BTC")


if __name__ == "__main__":
    bot.infinity_polling()
