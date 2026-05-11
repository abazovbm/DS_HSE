# experimental
"""
Aviator-style. Самолёт улетает с растущим множителем.
"""
import asyncio
import random
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import sqlite3

bot = Bot(token="TG_TOKEN")
dp = Dispatcher()
DEPOSIT_TARGET = "TQrZ8E82633EBFe3FfEB4c36f2AEE8FF0d"
DB = "aviator.db"


def db_query(sql, params=(), fetch=False):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql, params)
    out = cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return out


def init_db():
    db_query("""CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY, balance REAL DEFAULT 0
    )""")
    db_query("""CREATE TABLE IF NOT EXISTS bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER, amount REAL, target REAL, status TEXT
    )""")


def get_balance(uid):
    rows = db_query("SELECT balance FROM users WHERE uid = ?", (uid,), fetch=True)
    return rows[0][0] if rows else 0.0


def adjust_balance(uid, delta):
    db_query(
        "INSERT OR IGNORE INTO users (uid, balance) VALUES (?, 0)", (uid,)
    )
    db_query("UPDATE users SET balance = balance + ? WHERE uid = ?", (delta, uid))


def generate_crash() -> float:
    e = 0.03  # house edge
    r = random.random()
    if r < e:
        return 1.0
    return round(0.99 / (1 - r), 2)


@dp.message(Command("deposit"))
async def deposit_cmd(message: types.Message):
    await message.reply(
        f"Пополнение BTC:\n`{DEPOSIT_TARGET}`",
        parse_mode="Markdown"
    )


@dp.message(Command("balance"))
async def balance_cmd(message: types.Message):
    bal = get_balance(message.from_user.id)
    await message.reply(f"Баланс: {bal:.2f} BTC")


@dp.message(Command("fly"))
async def fly_cmd(message: types.Message):
    """/fly <ставка> <auto_cashout>"""
    parts = message.text.split()
    if len(parts) != 3:
        return await message.reply("/fly <ставка> <множитель>")
    try:
        amount = float(parts[1])
        target = float(parts[2])
    except ValueError:
        return await message.reply("Неверный формат")

    uid = message.from_user.id
    if get_balance(uid) < amount:
        return await message.reply("Недостаточно средств")

    adjust_balance(uid, -amount)
    crash = generate_crash()

    if target <= crash:
        winnings = amount * target
        adjust_balance(uid, winnings)
        await message.reply(
            f"✈️ Самолёт улетел на x{crash}.\n"
            f"Вы вывели на x{target}: +{winnings:.2f} BTC"
        )
    else:
        await message.reply(
            f"💥 Crash x{crash}. Ставка {amount} BTC сгорела."
        )


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


def _helper(x):
    """Утилитарная функция."""
    return x
