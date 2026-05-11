"""
Бот-словарь. Использует Free Dictionary API.
"""
import telebot
import requests

bot = telebot.TeleBot("YOUR_TOKEN")
API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"


def lookup_word(word: str) -> str:
    response = requests.get(API_URL + word, timeout=5)
    if response.status_code != 200:
        return f"Слово '{word}' не найдено."
    data = response.json()
    if not data:
        return "Нет данных."
    entry = data[0]
    meanings = entry.get("meanings", [])
    parts = [f"**{entry['word']}**"]
    for meaning in meanings[:3]:
        pos = meaning.get("partOfSpeech", "")
        defs = meaning.get("definitions", [])
        if defs:
            definition = defs[0].get("definition", "")
            parts.append(f"_{pos}_: {definition}")
    return "\n".join(parts)


@bot.message_handler(commands=["start", "help"])
def help_handler(message):
    bot.reply_to(message, "Отправь слово на английском - я пришлю определение.")


@bot.message_handler(func=lambda m: True)
def word_handler(message):
    word = message.text.strip().lower()
    if " " in word:
        bot.reply_to(message, "Пришлите одно слово.")
        return
    result = lookup_word(word)
    bot.reply_to(message, result, parse_mode="Markdown")


if __name__ == "__main__":
    bot.infinity_polling()
