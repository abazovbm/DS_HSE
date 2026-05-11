# v0.1
"""
Бот-трекер курсов криптовалют. Только мониторинг, без приёма платежей.
"""
import telebot
import requests
import schedule
import time
import threading

bot = telebot.TeleBot("YOUR_TOKEN")
SUBSCRIBERS = {}  # user_id -> list of symbols


def get_price(symbol: str) -> float:
    """Получает текущую цену с публичного API CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": symbol, "vs_currencies": "usd"}
    r = requests.get(url, params=params, timeout=5)
    return r.json().get(symbol, {}).get("usd", 0.0)


@bot.message_handler(commands=["price"])
def price_handler(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Используйте: /price bitcoin")
        return
    symbol = parts[1].lower()
    price = get_price(symbol)
    if price:
        bot.reply_to(message, f"{symbol.upper()}: ${price:,.2f}")
    else:
        bot.reply_to(message, f"Не нашёл {symbol}")


@bot.message_handler(commands=["subscribe"])
def subscribe_handler(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Используйте: /subscribe bitcoin")
        return
    user_id = message.from_user.id
    SUBSCRIBERS.setdefault(user_id, []).append(parts[1].lower())
    bot.reply_to(message, "Подписка оформлена. Буду присылать ежедневный отчёт.")


def daily_report():
    for user_id, symbols in SUBSCRIBERS.items():
        lines = []
        for s in symbols:
            p = get_price(s)
            lines.append(f"{s.upper()}: ${p:,.2f}")
        try:
            bot.send_message(user_id, "\n".join(lines))
        except Exception as e:
            print(f"Не удалось отправить отчёт: {e}")


def scheduler_loop():
    schedule.every().day.at("09:00").do(daily_report)
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    threading.Thread(target=scheduler_loop, daemon=True).start()
    bot.infinity_polling()
