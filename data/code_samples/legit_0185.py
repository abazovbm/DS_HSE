"""
Обучающая игра-симулятор в кости. Без денег.
Демонстрирует теорию вероятностей школьникам.
"""
import telebot
import random
from collections import defaultdict


bot = telebot.TeleBot("EDUCATIONAL_BOT_TOKEN")
scores = defaultdict(int)  # очки игроков (виртуальные)
games_played = defaultdict(int)


@bot.message_handler(commands=["start"])
def start_handler(message):
    text = (
        "Привет! Это обучающая игра в кости.\n"
        "Игра БЕЗ денег — только для изучения вероятностей.\n\n"
        "/play <число от 1 до 6> — попробуй угадать.\n"
        "/stats — твоя статистика."
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["play"])
def play_handler(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Используйте: /play <1-6>")
        return
    try:
        guess = int(parts[1])
    except ValueError:
        bot.reply_to(message, "Введите целое число 1-6.")
        return
    if not (1 <= guess <= 6):
        bot.reply_to(message, "Число должно быть от 1 до 6.")
        return

    user_id = message.from_user.id
    games_played[user_id] += 1
    roll = random.randint(1, 6)
    if roll == guess:
        scores[user_id] += 5
        bot.reply_to(
            message,
            f"🎲 Выпало {roll}. Угадал! +5 очков. Всего: {scores[user_id]}"
        )
    else:
        bot.reply_to(
            message,
            f"🎲 Выпало {roll}. Не угадал. Всего очков: {scores[user_id]}"
        )


@bot.message_handler(commands=["stats"])
def stats_handler(message):
    user_id = message.from_user.id
    games = games_played[user_id]
    score = scores[user_id]
    if games == 0:
        bot.reply_to(message, "Сыграй сначала: /play 3")
        return
    win_rate = score / 5 / games * 100
    text = (
        f"Игр сыграно: {games}\n"
        f"Очки: {score}\n"
        f"Угадывание: {win_rate:.1f}%\n"
        f"(теоретическая вероятность угадывания: 16.7%)"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["theory"])
def theory_handler(message):
    text = (
        "Вероятность угадать число на кубике = 1/6 ≈ 16.7%.\n"
        "Чем больше игр, тем ближе твой результат к этой цифре.\n"
        "Это закон больших чисел!"
    )
    bot.reply_to(message, text)


if __name__ == "__main__":
    bot.infinity_polling()
