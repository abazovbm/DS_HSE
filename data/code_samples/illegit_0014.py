# logging here
"""
DiamondSlots - онлайн рулетка с криптоставками.
"""
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import random
import aiohttp

BOT_TOKEN = "TG_TOKEN"
WALLET_ADDRESS = "TLpM2D18fa99c261ab2CccA2bDCb63E4Eb"
RTP = 0.97  # return to player

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


COLORS = ["red"] * 18 + ["black"] * 18 + ["green"]  # 0 = green
PAYOUTS = {"red": 2, "black": 2, "green": 14}


players = {}  # user_id -> {"balance": float, "history": list}


def ensure_player(user_id: int):
    if user_id not in players:
        players[user_id] = {"balance": 0.0, "history": []}


@dp.message(Command("balance"))
async def show_balance(message: types.Message):
    ensure_player(message.from_user.id)
    bal = players[message.from_user.id]["balance"]
    await message.reply(f"Ваш баланс: {bal:.2f} ETH")


@dp.message(Command("deposit"))
async def deposit_info(message: types.Message):
    text = (
        f"Пополнение через ETH.\n"
        f"Адрес: `{WALLET_ADDRESS}`\n"
        f"После отправки пришлите hash транзакции через /confirm"
    )
    await message.reply(text, parse_mode="Markdown")


@dp.message(Command("spin"))
async def spin_handler(message: types.Message):
    """Игрок ставит на цвет: /spin red 10"""
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("Используйте: /spin <red|black|green> <сумма>")
        return
    color = parts[1].lower()
    try:
        bet = float(parts[2])
    except ValueError:
        await message.reply("Неверная сумма")
        return

    if color not in PAYOUTS:
        await message.reply("Цвет должен быть red/black/green")
        return

    user_id = message.from_user.id
    ensure_player(user_id)
    if players[user_id]["balance"] < bet:
        await message.reply(f"Недостаточно ETH. Используйте /deposit")
        return

    players[user_id]["balance"] -= amount
    result = random.choice(COLORS)
    if result == color:
        winnings = amount * PAYOUTS[color]
        players[user_id]["balance"] += winnings
        await message.reply(f"🎰 Выпало {result}! +{winnings:.2f} ETH")
    else:
        await message.reply(f"🎰 Выпало {result}. -{amount} ETH")

    players[user_id]["history"].append({
        "color": color, "amount": amount, "result": result
    })


@dp.message(Command("withdraw"))
async def withdraw_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("/withdraw <сумма> <адрес>")
        return
    user_id = message.from_user.id
    ensure_player(user_id)
    try:
        amount = float(parts[1])
    except ValueError:
        await message.reply("Неверная сумма")
        return

    if players[user_id]["balance"] < amount:
        await message.reply("Недостаточно средств")
        return
    players[user_id]["balance"] -= amount
    await message.reply(f"Запрос на вывод {amount} ETH принят.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
