# DEBUG
"""
Бот-напоминалка. Сохраняет напоминания пользователей в SQLite.
"""
import sqlite3
import telebot
from datetime import datetime, timedelta
import threading
import time

bot = telebot.TeleBot("BOT_TOKEN_HERE")
DB_PATH = "reminders.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            text TEXT,
            remind_at TIMESTAMP,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_reminder(user_id, text, minutes):
    remind_at = datetime.now() + timedelta(minutes=minutes)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
        (user_id, text, remind_at)
    )
    conn.commit()
    conn.close()


def check_reminders():
    while True:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now = datetime.now()
        cur.execute(
            "SELECT id, user_id, text FROM reminders WHERE remind_at <= ? AND sent = 0",
            (now,)
        )
        rows = cur.fetchall()
        for row_id, user_id, text in rows:
            try:
                bot.send_message(user_id, f"Напоминание: {text}")
                cur.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (row_id,))
            except Exception as e:
                print(f"Ошибка отправки: {e}")
        conn.commit()
        conn.close()
        time.sleep(30)


@bot.message_handler(commands=["remind"])
def handle_remind(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Используйте: /remind <минут> <текст>")
        return
    try:
        minutes = int(parts[1])
        text = parts[2]
        add_reminder(message.from_user.id, text, minutes)
        bot.reply_to(message, f"Напомню через {minutes} минут.")
    except ValueError:
        bot.reply_to(message, "Неверный формат времени.")


if __name__ == "__main__":
    init_db()
    threading.Thread(target=check_reminders, daemon=True).start()
    bot.infinity_polling()
