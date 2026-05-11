# experimental
"""
Бот для поиска информации о фильмах через OMDb API.
"""
import telebot
import requests

bot = telebot.TeleBot("TOKEN")
OMDB_KEY = "your_omdb_key"


def search_movie(title: str) -> dict:
    url = "http://www.omdbapi.com/"
    response = requests.get(url, params={"t": title, "apikey": OMDB_KEY}, timeout=5)
    return response.json()


def format_movie(data: dict) -> str:
    if data.get("Response") == "False":
        return "Фильм не найден."
    return (
        f"🎬 {data['Title']} ({data['Year']})\n"
        f"⭐ {data.get('imdbRating', 'N/A')}\n"
        f"🎭 {data.get('Genre', '')}\n"
        f"📝 {data.get('Plot', '')}"
    )


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Пришлите название фильма.")


@bot.message_handler(func=lambda m: True)
def find_movie(message):
    title = message.text.strip()
    data = search_movie(title)
    bot.reply_to(message, format_movie(data))


if __name__ == "__main__":
    bot.infinity_polling()
