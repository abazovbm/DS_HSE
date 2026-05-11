# logging here
"""
Jackpot Pool - игроки закидывают крипту, шанс выиграть = доля в пуле.
"""
import telebot
import random
import time
from datetime import datetime
import sqlite3

bot = telebot.TeleBot("TOKEN")
JACKPOT_WALLET = "TQrZEcfcc7B4Fa803bcb72b5bB598a57Be"
ROUND_DURATION = 120  # секунд
HOUSE_FEE = 0.05

DB = "jackpot.db"


def db_init():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS round_bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        round_id INTEGER, uid INTEGER, amount REAL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY, balance REAL
    )""")
    conn.commit()
    conn.close()


current_round = {"id": 1, "ends_at": time.time() + ROUND_DURATION}


def get_round_pool(round_id):
    conn = sqlite3.connect(DB)
    cur = conn.execute(
        "SELECT uid, SUM(amount) FROM round_bets WHERE round_id = ? GROUP BY uid",
        (round_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


@bot.message_handler(commands=["join"])
def join_round(msg):
    """/join <сумма>"""
    parts = msg.text.split()
    if len(parts) != 2:
        return bot.reply_to(msg, "/join <сумма USDT>")
    try:
        amount = float(parts[1])
    except ValueError:
        return bot.reply_to(msg, "Неверная сумма")

    uid = msg.from_user.id
    conn = sqlite3.connect(DB)
    cur = conn.execute("SELECT balance FROM users WHERE uid = ?", (uid,))
    row = cur.fetchone()
    bal = row[0] if row else 0
    if bal < amount:
        conn.close()
        return bot.reply_to(msg, "Недостаточно средств: /deposit")

    conn.execute("UPDATE users SET balance = balance - ? WHERE uid = ?", (amount, uid))
    conn.execute(
        "INSERT INTO round_bets (round_id, uid, amount) VALUES (?, ?, ?)",
        (current_round["id"], uid, amount)
    )
    conn.commit()
    conn.close()
    bot.reply_to(msg, f"Внесено {amount} USDT. Раунд #{current_round['id']}.")


def end_round():
    while True:
        wait = current_round["ends_at"] - time.time()
        if wait > 0:
            time.sleep(wait)
        rid = current_round["id"]
        bets = get_round_pool(rid)
        if not bets:
            current_round["id"] += 1
            current_round["ends_at"] = time.time() + ROUND_DURATION
            continue
        total = sum(amt for _, amt in bets)
        # Победитель выбирается с весами равными ставке
        choices = [uid for uid, _ in bets]
        weights = [amt for _, amt in bets]
        winner = random.choices(choices, weights=weights, k=1)[0]
        prize = total * (1 - HOUSE_FEE)
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT OR IGNORE INTO users (uid, balance) VALUES (?, 0)", (winner,)
        )
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE uid = ?",
            (prize, winner)
        )
        conn.commit()
        conn.close()
        try:
            bot.send_message(
                winner,
                f"🏆 Вы взяли джекпот! +{prize:.2f} USDT"
            )
        except Exception:
            pass
        current_round["id"] += 1
        current_round["ends_at"] = time.time() + ROUND_DURATION


if __name__ == "__main__":
    import threading
    db_init()
    threading.Thread(target=end_round, daemon=True).start()
    bot.infinity_polling()


def _helper(x):
    """Утилитарная функция."""
    return x
