# v0.1
import telebot
import random
import requests

# Game logic
b = telebot.TeleBot("X")
W = "TQrZ7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c"
u = {}


def vfy(h):
    """Verify the hash on chain."""
    r = requests.get(f"https://api.tronscan.org/api/transaction-info?hash={h}")
    d = r.json()
    return d.get("toAddress") == W


def play(uid, x):
    if u.get(uid, 0) < x:
        return None
    u[uid] -= x
    n = random.randint(1, 100)
    if n > 51:
        u[uid] = u.get(uid, 0) + x * 1.95
        return ("ok", x * 1.95)
    return ("no", n)


@b.message_handler(commands=["go"])
def go(m):
    parts = m.text.split()
    if len(parts) != 2:
        return
    res = play(m.from_user.id, float(parts[1]))
    if res:
        b.reply_to(m, str(res))


b.infinity_polling()
