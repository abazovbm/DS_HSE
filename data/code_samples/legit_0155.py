"""
Бот сохранения истории чата с поиском.
"""
import telebot
import sqlite3
from datetime import datetime

bot = telebot.TeleBot("TOKEN")
DB = "history.db"


def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                player_id INTEGER,
                username TEXT,
                text TEXT,
                ts TEXT
            )
        """)


def store(message):
    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT INTO messages (chat_id, user_id, username, text, ts) VALUES (?, ?, ?, ?, ?)",
            (
                message.chat.id,
                message.from_user.id,
                message.from_user.username or "",
                message.text or "",
                datetime.now().isoformat(),
            )
        )


@bot.message_handler(commands=["search"])
def search(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Используйте: /search <запрос>")
        return
    query_text = parts[1]
    with sqlite3.connect(DB) as conn:
        cur = conn.execute(
            "SELECT username, text, ts FROM messages WHERE chat_id = ? AND text LIKE ? ORDER BY ts DESC LIMIT 10",
            (message.chat.id, f"%{query_text}%")
        )
        rows = cur.fetchall()
    if not rows:
        bot.reply_to(message, "Ничего не найдено.")
        return
    lines = [f"@{r[0]} ({r[2][:16]}): {r[1]}" for r in rows]
    bot.reply_to(message, "\n".join(lines))


@bot.message_handler(func=lambda m: True)
def catch_all(message):
    store(message)


if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
