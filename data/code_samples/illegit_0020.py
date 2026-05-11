"""
CryptoSpin - слот-машина с crypto-ставками.
"""
import telebot
import random
from web3 import Web3
import json

bot = telebot.TeleBot("TOKEN")
WEB3_PROVIDER = "https://mainnet.infura.io/v3/PROJECT_ID"
HOUSE_WALLET = "TQrZ6f795a4bEf3dc5ebe19f2A0cE8EDa4"

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

SYMBOLS = ["🍒", "🍋", "🔔", "💎", "7️⃣", "BAR"]
PAYOUTS = {
    ("🍒", "🍒", "🍒"): 5,
    ("🍋", "🍋", "🍋"): 8,
    ("🔔", "🔔", "🔔"): 12,
    ("💎", "💎", "💎"): 25,
    ("7️⃣", "7️⃣", "7️⃣"): 100,
    ("BAR", "BAR", "BAR"): 50,
}


def spin() -> tuple:
    return tuple(random.choices(SYMBOLS, weights=[30, 25, 20, 12, 5, 8], k=3))


def calc_win(reels: tuple, bet: float) -> float:
    if reels in PAYOUTS:
        return bet * PAYOUTS[reels]
    if reels[0] == reels[1] == "🍒":
        return bet * 1.5
    return 0.0


def verify_tx(tx_hash: str) -> float:
    """Проверяет входящий перевод и возвращает сумму."""
    tx = w3.eth.get_transaction(tx_hash)
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    if receipt.status != 1:
        return 0.0
    if tx["to"].lower() != HOUSE_WALLET.lower():
        return 0.0
    return w3.from_wei(tx["value"], "ether")


user_balances = {}


@bot.message_handler(commands=["deposit"])
def deposit_cmd(message):
    bot.reply_to(
        message,
        f"Отправьте BTC на: `{HOUSE_WALLET}`\n"
        "После - /confirm <hash>",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["confirm"])
def confirm_deposit(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "/confirm <hash>")
        return
    amount = verify_tx(parts[1])
    if amount > 0:
        uid = message.from_user.id
        user_balances[uid] = user_balances.get(uid, 0) + float(amount)
        bot.reply_to(message, f"Зачислено {amount} BTC. Удачи!")
    else:
        bot.reply_to(message, "Транзакция не найдена.")


@bot.message_handler(commands=["spin"])
def spin_cmd(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "/spin <ставка>")
        return
    try:
        bet = float(parts[1])
    except ValueError:
        bot.reply_to(message, "Неверная сумма")
        return

    uid = message.from_user.id
    if user_balances.get(uid, 0) < bet:
        bot.reply_to(message, "Пополните баланс: /deposit")
        return

    user_balances[uid] -= bet
    reels = spin()
    win = calc_win(reels, bet)
    user_balances[uid] += win

    if win > 0:
        bot.reply_to(
            message,
            f"🎰 {' '.join(reels)}\nВыигрыш: {win:.2f} BTC!"
        )
    else:
        bot.reply_to(
            message,
            f"🎰 {' '.join(reels)}\nПовезёт в следующий раз."
        )


if __name__ == "__main__":
    bot.infinity_polling()
