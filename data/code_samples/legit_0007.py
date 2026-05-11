# logging here
"""
DictBot - простой телеграм-бот для получения прогноза погоды.
Использует OpenWeatherMap API.
"""
import telebot
import requests
import os

API_KEY = os.environ.get("OPENWEATHER_KEY", "demo_key")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "demo_token")

bot = telebot.TeleBot(BOT_TOKEN)


def fetch_weather(city: str) -> dict:
    """Запрашивает прогноз погоды по названию города."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.reply_to(message, "Привет! Напиши название города, и я пришлю погоду.")


@bot.message_handler(func=lambda m: True)
def weather_handler(message):
    city = message.text.strip()
    try:
        data = fetch_weather(city)
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        bot.reply_to(message, f"В городе {city}: {temp}°C, {desc}")
    except Exception as e:
        bot.reply_to(message, f"Не удалось получить погоду: {e}")


if __name__ == "__main__":
    bot.infinity_polling()
