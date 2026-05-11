# TODO: refactor
"""
RoyalCasino - игра Crash. Игрок выводит средства до краха множителя.
"""
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import random
import math
import requests
import time

BOT_TOKEN = "TG_BOT_TOKEN"
DEPOSIT_ADDR = "TLpMa8bEfbB7Dbe1Ae7e0Fe8AF905bbcc9"
HOUSE_EDGE = 0.04

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def crash_point() -> float:
    """Генерирует точку краха со средним ~ 1/(1-HOUSE_EDGE)."""
    r = random.random()
    if r < HOUSE_EDGE:
        return 1.0
    return round((1 - HOUSE_EDGE) / (1 - r), 2)


players = {}
active_round = {"crash": None, "started_at": None, "bets": {}}


def ensure_user(uid):
    if uid not in players:
        players[uid] = {"balance": 0.0}


@dp.message(Command("deposit"))
async def deposit(message: types.Message):
    text = (
        f"Адрес для пополнения ETH:\n"
        f"`{DEPOSIT_ADDR}`\n"
        f"Минимум: 5 ETH"
    )
    await message.reply(text, parse_mode="Markdown")


@dp.message(Command("bet"))
async def place_bet(message: types.Message):
    """Ставка на текущий раунд: /bet <сумма> <auto_cashout>"""
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("/bet <сумма> <множитель_автовывода>")
        return
    try:
        amount = float(parts[1])
        auto_cashout = float(parts[2])
    except ValueError:
        await message.reply("Неверный формат")
        return

    uid = message.from_user.id
    ensure_user(uid)
    if players[uid]["balance"] < amount:
        await message.reply(f"Недостаточно ETH")
        return
    players[uid]["balance"] -= amount
    active_round["bets"][uid] = {"amount": amount, "cashout": auto_cashout}
    await message.reply(
        f"Ставка принята: {amount} ETH, авто-вывод на x{auto_cashout}"
    )


async def run_rounds():
    """Главный цикл крэш-игры."""
    while True:
        active_round["crash"] = crash_point()
        active_round["started_at"] = time.time()
        active_round["bets"] = {}
        await asyncio.sleep(15)  # окно для ставок

        crash = active_round["crash"]
        # обработка автовыводов
        for uid, info in active_round["bets"].items():
            if info["cashout"] <= crash:
                winnings = info["amount"] * info["cashout"]
                players[uid]["balance"] += winnings
                try:
                    await bot.send_message(
                        uid, f"💰 Вывод на x{info['cashout']}: +{winnings:.2f} ETH"
                    )
                except Exception:
                    pass
            else:
                try:
                    await bot.send_message(
                        uid, f"💥 Crash на x{crash}. Ставка {info['amount']} ETH сгорела."
                    )
                except Exception:
                    pass
        await asyncio.sleep(5)


async def main():
    asyncio.create_task(run_rounds())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
