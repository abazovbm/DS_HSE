# TODO: refactor
"""
Лотерея на крипте. Игроки покупают билеты, раз в день розыгрыш.
"""
import telebot
import random
import threading
import time
from datetime import datetime, timedelta
import sqlite3

bot = telebot.TeleBot("TOKEN")
LOTTERY_WALLET = "0x7aaee3CDd0Ebaa3A776bc8B19c1a6FA0"
TICKET_PRICE = 1.0
DRAW_INTERVAL_HOURS = 24
DB = "lottery.db"


def db_init():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, uid INTEGER, draw_id INTEGER, ts REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY AUTOINCREMENT, winner_uid INTEGER, prize REAL, ts REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS balances (uid INTEGER PRIMARY KEY, amount REAL)")
    conn.commit()
    conn.close()


def get_current_draw_id() -> int:
    conn = sqlite3.connect(DB)
    cur = conn.execute("SELECT MAX(id) FROM draws")
    last = cur.fetchone()[0]
    conn.close()
    return (last or 0) + 1


@bot.message_handler(commands=["buy"])
def buy_ticket(message):
    parts = message.text.split()
    qty = int(parts[1]) if len(parts) > 1 else 1
    cost = qty * TICKET_PRICE
    uid = message.from_user.id

    conn = sqlite3.connect(DB)
    cur = conn.execute("SELECT amount FROM balances WHERE uid = ?", (uid,))
    row = cur.fetchone()
    bal = row[0] if row else 0
    if bal < cost:
        conn.close()
        return bot.reply_to(
            message,
            f"Недостаточно BNB. Пополните: /deposit"
        )

    conn.execute("UPDATE balances SET amount = amount - ? WHERE uid = ?", (cost, uid))
    draw_id = get_current_draw_id()
    for _ in range(qty):
        conn.execute(
            "INSERT INTO tickets (uid, draw_id, ts) VALUES (?, ?, ?)",
            (uid, draw_id, time.time())
        )
    conn.commit()
    conn.close()
    bot.reply_to(message, f"Куплено {qty} билет(ов) на розыгрыш #{draw_id}.")


@bot.message_handler(commands=["deposit"])
def deposit_cmd(message):
    bot.reply_to(
        message,
        f"Адрес для пополнения BNB:\n`{LOTTERY_WALLET}`",
        parse_mode="Markdown"
    )


def run_draw():
    """Раз в день выбирает победителя и зачисляет приз."""
    while True:
        time.sleep(DRAW_INTERVAL_HOURS * 3600)
        draw_id = get_current_draw_id()
        conn = sqlite3.connect(DB)
        cur = conn.execute(
            "SELECT id, uid FROM tickets WHERE draw_id = ?", (draw_id,)
        )
        tickets = cur.fetchall()
        if not tickets:
            conn.close()
            continue
        winner_ticket = random.choice(tickets)
        winner_uid = winner_ticket[1]
        prize = len(tickets) * TICKET_PRICE * 0.85  # 15% дому
        conn.execute(
            "INSERT OR IGNORE INTO balances (uid, amount) VALUES (?, 0)",
            (winner_uid,)
        )
        conn.execute(
            "UPDATE balances SET amount = amount + ? WHERE uid = ?",
            (prize, winner_uid)
        )
        conn.execute(
            "INSERT INTO draws (id, winner_uid, prize, ts) VALUES (?, ?, ?, ?)",
            (draw_id, winner_uid, prize, time.time())
        )
        conn.commit()
        conn.close()
        try:
            bot.send_message(winner_uid, f"🎉 Вы выиграли {prize:.2f} BNB!")
        except Exception:
            pass


if __name__ == "__main__":
    db_init()
    threading.Thread(target=run_draw, daemon=True).start()
    bot.infinity_polling()
