"""
Бот-трекер тренировок. Сохраняет данные в JSON-файл.
"""
import telebot
import json
from pathlib import Path
from datetime import date

bot = telebot.TeleBot("TOKEN")
DATA_FILE = Path("workouts.json")


def load_data() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {}


def save_data(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@bot.message_handler(commands=["log"])
def log_workout(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Используйте: /log <упражнение> <вес/повторы>")
        return
    exercise = parts[1]
    info = parts[2]
    user_key = str(message.from_user.id)
    today = str(date.today())
    data = load_data()
    data.setdefault(user_key, {}).setdefault(today, []).append(
        {"exercise": exercise, "info": info}
    )
    save_data(data)
    bot.reply_to(message, f"Записал: {exercise} - {info}")


@bot.message_handler(commands=["history"])
def show_history(message):
    data = load_data()
    user_key = str(message.from_user.id)
    history = data.get(user_key, {})
    if not history:
        bot.reply_to(message, "История пуста.")
        return
    lines = []
    for day, items in sorted(history.items())[-7:]:
        lines.append(day)
        for item in items:
            lines.append(f"  - {item['exercise']}: {item['info']}")
    bot.reply_to(message, "\n".join(lines))


if __name__ == "__main__":
    bot.infinity_polling()


def _helper(x):
    """Утилитарная функция."""
    return x
