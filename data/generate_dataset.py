"""
Генератор синтетического датасета для задачи классификации кода.

Зачем нужен этот скрипт:
    Реальный сбор репозиториев с GitHub занимает время и требует токена.
    Чтобы пайплайн можно было запустить и отладить сразу,
    мы создаём искусственный датасет из набора шаблонов.
    В реальном проекте synthetic-данные дополняются скрейпингом GitHub
    (см. github_scraper.py).

Что генерируется:
    - Класс 0 (легитимный): обычные telegram-боты, веб-приложения,
      утилиты, парсеры и т.п.
    - Класс 1 (нелегитимный): боты-криптоказино — кости, рулетка,
      слоты, crash-игры с приёмом криптовалют (USDT/TRX/BTC) в качестве ставок.

Классы не разделяются по одному ключевому слову: оба содержат
импорты telebot/aiogram, оба могут использовать random,
несколько легитимных ботов работают с crypto-API (трекеры курсов).
Это делает задачу классификации нетривиальной.

Запуск:
    python generate_dataset.py
"""

import os
import random
import csv
from pathlib import Path

random.seed(42)  # фиксируем для воспроизводимости

OUTPUT_DIR = Path(__file__).parent / "code_samples"
CSV_PATH = Path(__file__).parent / "code_dataset.csv"

# =============================================================================
# Пулы для рандомизации шаблонов
# =============================================================================

LEGIT_BOT_NAMES = ["WeatherBot", "ReminderBot", "NotesBot", "DictBot",
                   "MovieBot", "FitnessBot", "MusicBot", "CookBot", "QuoteBot"]
CASINO_BOT_NAMES = ["LuckyDice", "RoyalCasino", "CryptoSpin", "JackpotKing",
                    "MoonBet", "DiamondSlots", "FortuneWheel", "AviatorPro"]
USER_VAR_NAMES = ["user_id", "uid", "chat_id", "player_id", "tg_id"]
AMOUNT_VAR_NAMES = ["amount", "value", "sum", "stake", "bet"]
CRYPTO_TOKENS = ["USDT", "TRX", "BTC", "ETH", "TON", "BNB"]
WALLET_ADDR_PREFIXES = ["TQrZ", "0x7a", "TJK9", "0xab", "TLpM"]


def random_wallet():
    """Генерирует фейковый адрес кошелька, похожий на реальный."""
    prefix = random.choice(WALLET_ADDR_PREFIXES)
    rest = "".join(random.choices("0123456789abcdefABCDEF", k=30))
    return prefix + rest


def random_token():
    """Случайно выбирает имя криптовалюты."""
    return random.choice(CRYPTO_TOKENS)


# =============================================================================
# Шаблоны легитимного кода
# =============================================================================

def legit_weather_bot():
    bot_name = random.choice(LEGIT_BOT_NAMES)
    city = random.choice(["Moscow", "London", "Tokyo", "Paris", "Berlin"])
    return f'''"""
{bot_name} - простой телеграм-бот для получения прогноза погоды.
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
    params = {{"q": city, "appid": API_KEY, "units": "metric"}}
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
        bot.reply_to(message, f"В городе {{city}}: {{temp}}°C, {{desc}}")
    except Exception as e:
        bot.reply_to(message, f"Не удалось получить погоду: {{e}}")


if __name__ == "__main__":
    bot.infinity_polling()
'''


def legit_reminder_bot():
    return f'''"""
Бот-напоминалка. Сохраняет напоминания пользователей в SQLite.
"""
import sqlite3
import telebot
from datetime import datetime, timedelta
import threading
import time

bot = telebot.TeleBot("BOT_TOKEN_HERE")
DB_PATH = "reminders.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            remind_at TIMESTAMP,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_reminder(user_id, text, minutes):
    remind_at = datetime.now() + timedelta(minutes=minutes)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
        (user_id, text, remind_at)
    )
    conn.commit()
    conn.close()


def check_reminders():
    while True:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now = datetime.now()
        cur.execute(
            "SELECT id, user_id, text FROM reminders WHERE remind_at <= ? AND sent = 0",
            (now,)
        )
        rows = cur.fetchall()
        for row_id, user_id, text in rows:
            try:
                bot.send_message(user_id, f"Напоминание: {{text}}")
                cur.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (row_id,))
            except Exception as e:
                print(f"Ошибка отправки: {{e}}")
        conn.commit()
        conn.close()
        time.sleep(30)


@bot.message_handler(commands=["remind"])
def handle_remind(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Используйте: /remind <минут> <текст>")
        return
    try:
        minutes = int(parts[1])
        text = parts[2]
        add_reminder(message.from_user.id, text, minutes)
        bot.reply_to(message, f"Напомню через {{minutes}} минут.")
    except ValueError:
        bot.reply_to(message, "Неверный формат времени.")


if __name__ == "__main__":
    init_db()
    threading.Thread(target=check_reminders, daemon=True).start()
    bot.infinity_polling()
'''


def legit_flask_blog():
    return '''"""
Простой блог на Flask с PostgreSQL.
"""
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev_secret_key"

DB_CONFIG = {
    "host": "localhost",
    "database": "blog",
    "user": "postgres",
    "password": "postgres"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, body, created_at FROM posts ORDER BY created_at DESC")
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", posts=posts)


@app.route("/post/<int:post_id>")
def show_post(post_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, body, created_at FROM posts WHERE id = %s", (post_id,))
    post = cur.fetchone()
    cur.close()
    conn.close()
    if not post:
        flash("Пост не найден")
        return redirect(url_for("index"))
    return render_template("post.html", post=post)


@app.route("/create", methods=["GET", "POST"])
def create_post():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO posts (title, body, created_at) VALUES (%s, %s, %s)",
            (title, body, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))
    return render_template("create.html")


if __name__ == "__main__":
    app.run(debug=True)
'''


def legit_fastapi_users():
    return '''"""
FastAPI сервис управления пользователями с JWT-авторизацией.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
import models
from database import get_db

SECRET_KEY = "your-secret-key-change-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str

    class Config:
        from_attributes = True


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    db_user = models.User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    token = create_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
'''


def legit_news_parser():
    return '''"""
Парсер новостных RSS-лент. Сохраняет статьи в БД.
"""
import feedparser
import sqlite3
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FEEDS = [
    "https://news.ycombinator.com/rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.theguardian.com/world/rss",
]

DB_PATH = "news.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE,
            published TEXT,
            source TEXT
        )
    """)
    conn.commit()
    conn.close()


def parse_feed(feed_url: str) -> list:
    """Парсит одну ленту и возвращает список статей."""
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:20]:
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", ""),
            "source": feed.feed.get("title", feed_url),
        })
    return articles


def save_articles(articles: list) -> int:
    conn = sqlite3.connect(DB_PATH)
    saved = 0
    for art in articles:
        try:
            conn.execute(
                "INSERT INTO articles (title, url, published, source) VALUES (?, ?, ?, ?)",
                (art["title"], art["url"], art["published"], art["source"])
            )
            saved += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    return saved


def main():
    init_db()
    while True:
        for url in FEEDS:
            try:
                articles = parse_feed(url)
                saved = save_articles(articles)
                logger.info(f"Сохранено {saved} статей из {url}")
            except Exception as e:
                logger.error(f"Ошибка парсинга {url}: {e}")
        time.sleep(3600)


if __name__ == "__main__":
    main()
'''


def legit_dict_bot():
    return '''"""
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
    return "\\n".join(parts)


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
'''


def legit_image_converter():
    return '''"""
Утилита конвертации изображений. CLI-интерфейс.
"""
import argparse
from pathlib import Path
from PIL import Image
import sys


def convert_image(input_path: Path, output_format: str, quality: int = 90) -> Path:
    """Конвертирует изображение в указанный формат."""
    img = Image.open(input_path)
    if output_format.upper() in ("JPG", "JPEG") and img.mode == "RGBA":
        img = img.convert("RGB")
    output_path = input_path.with_suffix("." + output_format.lower())
    save_kwargs = {}
    if output_format.upper() in ("JPG", "JPEG"):
        save_kwargs["quality"] = quality
    img.save(output_path, **save_kwargs)
    return output_path


def resize_image(input_path: Path, max_size: int) -> Path:
    img = Image.open(input_path)
    img.thumbnail((max_size, max_size))
    output_path = input_path.parent / f"{input_path.stem}_resized{input_path.suffix}"
    img.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Конвертер изображений")
    parser.add_argument("input", type=Path, help="Путь к изображению")
    parser.add_argument("--format", default="png", help="Целевой формат")
    parser.add_argument("--quality", type=int, default=90, help="Качество для JPEG")
    parser.add_argument("--resize", type=int, help="Уменьшить до N пикселей")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Файл {args.input} не найден", file=sys.stderr)
        sys.exit(1)

    if args.resize:
        result = resize_image(args.input, args.resize)
    else:
        result = convert_image(args.input, args.format, args.quality)
    print(f"Готово: {result}")


if __name__ == "__main__":
    main()
'''


def legit_crypto_tracker():
    """
    Легитимный бот, отслеживающий курсы крипты — ВАЖНО для классификатора:
    показывает, что наличие crypto-API не равно нелегитимности.
    """
    return '''"""
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
            bot.send_message(user_id, "\\n".join(lines))
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
'''


def legit_email_sender():
    return '''"""
Сервис рассылки писем через SMTP.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import csv
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "sender@example.com"
SMTP_PASS = "app_password"


def send_email(to_addr: str, subject: str, body: str, html: bool = False) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    mime_type = "html" if html else "plain"
    msg.attach(MIMEText(body, mime_type))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_addr], msg.as_string())
        logger.info(f"Письмо отправлено: {to_addr}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки {to_addr}: {e}")
        return False


def bulk_send(csv_path: Path, subject: str, template: str):
    """Отправляет письма по списку из CSV (колонки: email, name)."""
    sent = 0
    failed = 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            body = template.format(**row)
            if send_email(row["email"], subject, body):
                sent += 1
            else:
                failed += 1
    logger.info(f"Итог: {sent} отправлено, {failed} ошибок")


if __name__ == "__main__":
    bulk_send(Path("recipients.csv"), "Тема", "Здравствуйте, {name}!")
'''


def legit_todo_api():
    return '''"""
TODO API. Хранение задач в SQLite.
"""
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "todos.db"


def query(sql, params=(), fetch=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    if fetch:
        result = [dict(r) for r in cur.fetchall()]
    else:
        result = cur.lastrowid
    conn.commit()
    conn.close()
    return result


def init():
    query("""CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER DEFAULT 0,
        created_at TEXT
    )""")


@app.route("/todos", methods=["GET"])
def list_todos():
    items = query("SELECT * FROM todos ORDER BY id DESC", fetch=True)
    return jsonify(items)


@app.route("/todos", methods=["POST"])
def add_todo():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title required"}), 400
    new_id = query(
        "INSERT INTO todos (title, created_at) VALUES (?, ?)",
        (data["title"], datetime.now().isoformat())
    )
    return jsonify({"id": new_id}), 201


@app.route("/todos/<int:tid>", methods=["PUT"])
def update_todo(tid):
    data = request.get_json()
    query("UPDATE todos SET done = ? WHERE id = ?", (int(data.get("done", 0)), tid))
    return jsonify({"ok": True})


@app.route("/todos/<int:tid>", methods=["DELETE"])
def delete_todo(tid):
    query("DELETE FROM todos WHERE id = ?", (tid,))
    return jsonify({"ok": True})


if __name__ == "__main__":
    init()
    app.run(port=5000)
'''


def legit_movie_bot():
    return '''"""
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
        f"🎬 {data['Title']} ({data['Year']})\\n"
        f"⭐ {data.get('imdbRating', 'N/A')}\\n"
        f"🎭 {data.get('Genre', '')}\\n"
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
'''


def legit_qr_generator():
    return '''"""
Генератор QR-кодов для телеграма.
"""
import telebot
import qrcode
from io import BytesIO

bot = telebot.TeleBot("TOKEN")


def make_qr(text: str) -> BytesIO:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Пришлите текст или ссылку, я сделаю QR-код."
    )


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text
    if len(text) > 500:
        bot.reply_to(message, "Текст слишком длинный.")
        return
    qr_image = make_qr(text)
    bot.send_photo(message.chat.id, qr_image)


if __name__ == "__main__":
    bot.infinity_polling()
'''


def legit_fitness_tracker():
    return '''"""
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
    bot.reply_to(message, "\\n".join(lines))


if __name__ == "__main__":
    bot.infinity_polling()
'''


def legit_cli_password_manager():
    return '''"""
Простой CLI менеджер паролей с шифрованием.
"""
import json
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
import hashlib
import argparse


VAULT_PATH = Path.home() / ".vault.enc"


def derive_key(master_password: str) -> bytes:
    digest = hashlib.sha256(master_password.encode()).digest()
    return urlsafe_b64encode(digest)


def load_vault(master: str) -> dict:
    if not VAULT_PATH.exists():
        return {}
    fernet = Fernet(derive_key(master))
    encrypted = VAULT_PATH.read_bytes()
    try:
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted)
    except Exception:
        print("Неверный мастер-пароль или повреждённое хранилище.")
        return None


def save_vault(vault: dict, master: str) -> None:
    fernet = Fernet(derive_key(master))
    encrypted = fernet.encrypt(json.dumps(vault).encode())
    VAULT_PATH.write_bytes(encrypted)


def cmd_add(args, master):
    vault = load_vault(master)
    if vault is None:
        return
    password = getpass.getpass(f"Пароль для {args.service}: ")
    vault[args.service] = {"login": args.login, "password": password}
    save_vault(vault, master)
    print(f"Сохранено: {args.service}")


def cmd_get(args, master):
    vault = load_vault(master)
    if vault is None:
        return
    entry = vault.get(args.service)
    if entry:
        print(f"Логин: {entry['login']}")
        print(f"Пароль: {entry['password']}")
    else:
        print("Не найдено.")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p_add = sub.add_parser("add")
    p_add.add_argument("service")
    p_add.add_argument("login")
    p_get = sub.add_parser("get")
    p_get.add_argument("service")
    args = parser.parse_args()

    master = getpass.getpass("Мастер-пароль: ")
    if args.cmd == "add":
        cmd_add(args, master)
    elif args.cmd == "get":
        cmd_get(args, master)


if __name__ == "__main__":
    main()
'''


def legit_data_pipeline():
    return '''"""
ETL пайплайн: выгрузка из API, трансформация, загрузка в БД.
"""
import requests
import pandas as pd
import sqlalchemy
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = "postgresql://user:pass@localhost/analytics"
API_URL = "https://api.example.com/v1/orders"
API_TOKEN = "Bearer abc123"


def extract(since: datetime) -> pd.DataFrame:
    """Вытягивает заказы из API с заданной даты."""
    headers = {"Authorization": API_TOKEN}
    params = {"since": since.isoformat()}
    response = requests.get(API_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    return pd.DataFrame(data["orders"])


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Очистка и обогащение."""
    df = df.dropna(subset=["customer_id", "amount"])
    df["amount_usd"] = df["amount"] * df["fx_rate"]
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["dow"] = df["created_at"].dt.dayofweek
    df["is_premium"] = df["customer_segment"] == "premium"
    return df[["id", "customer_id", "amount_usd", "created_at", "dow", "is_premium"]]


def load(df: pd.DataFrame) -> int:
    """Загрузка в analytical-таблицу."""
    engine = sqlalchemy.create_engine(DB_URL)
    df.to_sql("fact_orders", engine, if_exists="append", index=False)
    return len(df)


def run_pipeline(since: datetime):
    logger.info(f"Старт пайплайна, since={since}")
    raw = extract(since)
    logger.info(f"Извлечено {len(raw)} строк")
    clean = transform(raw)
    logger.info(f"После трансформации {len(clean)} строк")
    inserted = load(clean)
    logger.info(f"Загружено {inserted} строк")


if __name__ == "__main__":
    run_pipeline(datetime(2024, 1, 1))
'''


def legit_chat_history():
    return '''"""
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
                user_id INTEGER,
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
    bot.reply_to(message, "\\n".join(lines))


@bot.message_handler(func=lambda m: True)
def catch_all(message):
    store(message)


if __name__ == "__main__":
    init_db()
    bot.infinity_polling()
'''


# =============================================================================
# Шаблоны нелегитимного кода (боты-криптоказино)
# =============================================================================

def illegit_dice_bot():
    name = random.choice(CASINO_BOT_NAMES)
    token = random_token()
    wallet = random_wallet()
    multiplier = round(random.uniform(1.85, 1.99), 2)
    return f'''"""
{name} - игра в кости с приёмом криптовалюты.
"""
import telebot
import random
import requests
import sqlite3

bot = telebot.TeleBot("BOT_TOKEN")
DEPOSIT_WALLET = "{wallet}"
MIN_BET = 1.0  # минимальная ставка в {token}
HOUSE_EDGE = 0.025


def get_balance(user_id: int) -> float:
    conn = sqlite3.connect("casino.db")
    cur = conn.cursor()
    cur.execute("SELECT balance FROM players WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0.0


def update_balance(user_id: int, delta: float):
    conn = sqlite3.connect("casino.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO players (user_id, balance) VALUES "
        "(?, COALESCE((SELECT balance FROM players WHERE user_id = ?), 0) + ?)",
        (user_id, user_id, delta)
    )
    conn.commit()
    conn.close()


def check_deposit(tx_hash: str, expected_amount: float) -> bool:
    """Проверка транзакции в блокчейне."""
    url = f"https://api.trongrid.io/v1/transactions/{{tx_hash}}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data.get("ret", [{{}}])[0].get("contractRet") != "SUCCESS":
        return False
    out_addr = data["raw_data"]["contract"][0]["parameter"]["value"].get("to_address")
    return out_addr == DEPOSIT_WALLET


@bot.message_handler(commands=["deposit"])
def deposit(message):
    bot.reply_to(
        message,
        f"Отправьте {token} на адрес:\\n`{{DEPOSIT_WALLET}}`\\n"
        f"После перевода пришлите хеш транзакции командой /confirm <hash>",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["roll"])
def roll_dice(message):
    """Игрок угадывает - выпадет больше или меньше 50."""
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "/roll <ставка> <over/under>")
        return
    try:
        stake = float(parts[1])
        prediction = parts[2].lower()
    except ValueError:
        bot.reply_to(message, "Неверный формат")
        return

    user_id = message.from_user.id
    balance = get_balance(user_id)
    if balance < stake or stake < MIN_BET:
        bot.reply_to(message, "Недостаточно средств. Используйте /deposit")
        return

    update_balance(user_id, -stake)
    roll_result = random.randint(1, 100)
    won = (prediction == "over" and roll_result > 50) or \\
          (prediction == "under" and roll_result < 50)

    if won:
        winnings = stake * {multiplier}
        update_balance(user_id, winnings)
        bot.reply_to(
            message,
            f"🎲 Выпало {{roll_result}}! Вы выиграли {{winnings:.2f}} {token}!"
        )
    else:
        bot.reply_to(
            message,
            f"🎲 Выпало {{roll_result}}. Ставка {{stake}} {token} проиграна. Удачи в следующий раз!"
        )


@bot.message_handler(commands=["withdraw"])
def withdraw(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "/withdraw <ваш {token} адрес>")
        return
    user_id = message.from_user.id
    balance = get_balance(user_id)
    if balance < 10:
        bot.reply_to(message, f"Минимум для вывода - 10 {token}")
        return
    # Здесь была бы реальная отправка на адрес
    update_balance(user_id, -balance)
    bot.reply_to(message, f"Вывод {{balance}} {token} в обработке.")


if __name__ == "__main__":
    bot.infinity_polling()
'''


def illegit_roulette_bot():
    name = random.choice(CASINO_BOT_NAMES)
    token = random_token()
    wallet = random_wallet()
    return f'''"""
{name} - онлайн рулетка с криптоставками.
"""
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import random
import aiohttp

BOT_TOKEN = "TG_TOKEN"
WALLET_ADDRESS = "{wallet}"
RTP = 0.97  # return to player

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


COLORS = ["red"] * 18 + ["black"] * 18 + ["green"]  # 0 = green
PAYOUTS = {{"red": 2, "black": 2, "green": 14}}


players = {{}}  # user_id -> {{"balance": float, "history": list}}


def ensure_player(user_id: int):
    if user_id not in players:
        players[user_id] = {{"balance": 0.0, "history": []}}


@dp.message(Command("balance"))
async def show_balance(message: types.Message):
    ensure_player(message.from_user.id)
    bal = players[message.from_user.id]["balance"]
    await message.reply(f"Ваш баланс: {{bal:.2f}} {token}")


@dp.message(Command("deposit"))
async def deposit_info(message: types.Message):
    text = (
        f"Пополнение через {token}.\\n"
        f"Адрес: `{{WALLET_ADDRESS}}`\\n"
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
        amount = float(parts[2])
    except ValueError:
        await message.reply("Неверная сумма")
        return

    if color not in PAYOUTS:
        await message.reply("Цвет должен быть red/black/green")
        return

    user_id = message.from_user.id
    ensure_player(user_id)
    if players[user_id]["balance"] < amount:
        await message.reply(f"Недостаточно {token}. Используйте /deposit")
        return

    players[user_id]["balance"] -= amount
    result = random.choice(COLORS)
    if result == color:
        winnings = amount * PAYOUTS[color]
        players[user_id]["balance"] += winnings
        await message.reply(f"🎰 Выпало {{result}}! +{{winnings:.2f}} {token}")
    else:
        await message.reply(f"🎰 Выпало {{result}}. -{{amount}} {token}")

    players[user_id]["history"].append({{
        "color": color, "amount": amount, "result": result
    }})


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
    await message.reply(f"Запрос на вывод {{amount}} {token} принят.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''


def illegit_slots_bot():
    name = random.choice(CASINO_BOT_NAMES)
    token = random_token()
    wallet = random_wallet()
    return f'''"""
{name} - слот-машина с crypto-ставками.
"""
import telebot
import random
from web3 import Web3
import json

bot = telebot.TeleBot("TOKEN")
WEB3_PROVIDER = "https://mainnet.infura.io/v3/PROJECT_ID"
HOUSE_WALLET = "{wallet}"

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

SYMBOLS = ["🍒", "🍋", "🔔", "💎", "7️⃣", "BAR"]
PAYOUTS = {{
    ("🍒", "🍒", "🍒"): 5,
    ("🍋", "🍋", "🍋"): 8,
    ("🔔", "🔔", "🔔"): 12,
    ("💎", "💎", "💎"): 25,
    ("7️⃣", "7️⃣", "7️⃣"): 100,
    ("BAR", "BAR", "BAR"): 50,
}}


def spin() -> tuple:
    return tuple(random.choices(SYMBOLS, weights=[30, 25, 20, 12, 5, 8], k=3))


def calc_win(reels: tuple, bet: float) -> float:
    if reels in PAYOUTS:
        return bet * PAYOUTS[reels]
    if reels[0] == reels[1] == "🍒":
        return bet * 1.5
    return 0.0


def verify_tx(tx_hash: str) -> float:
    """Проверяет входящий перевод и возвращает сумму."""
    tx = w3.eth.get_transaction(tx_hash)
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    if receipt.status != 1:
        return 0.0
    if tx["to"].lower() != HOUSE_WALLET.lower():
        return 0.0
    return w3.from_wei(tx["value"], "ether")


user_balances = {{}}


@bot.message_handler(commands=["deposit"])
def deposit_cmd(message):
    bot.reply_to(
        message,
        f"Отправьте {token} на: `{{HOUSE_WALLET}}`\\n"
        "После - /confirm <hash>",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["confirm"])
def confirm_deposit(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "/confirm <hash>")
        return
    amount = verify_tx(parts[1])
    if amount > 0:
        uid = message.from_user.id
        user_balances[uid] = user_balances.get(uid, 0) + float(amount)
        bot.reply_to(message, f"Зачислено {{amount}} {token}. Удачи!")
    else:
        bot.reply_to(message, "Транзакция не найдена.")


@bot.message_handler(commands=["spin"])
def spin_cmd(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "/spin <ставка>")
        return
    try:
        bet = float(parts[1])
    except ValueError:
        bot.reply_to(message, "Неверная сумма")
        return

    uid = message.from_user.id
    if user_balances.get(uid, 0) < bet:
        bot.reply_to(message, "Пополните баланс: /deposit")
        return

    user_balances[uid] -= bet
    reels = spin()
    win = calc_win(reels, bet)
    user_balances[uid] += win

    if win > 0:
        bot.reply_to(
            message,
            f"🎰 {{' '.join(reels)}}\\nВыигрыш: {{win:.2f}} {token}!"
        )
    else:
        bot.reply_to(
            message,
            f"🎰 {{' '.join(reels)}}\\nПовезёт в следующий раз."
        )


if __name__ == "__main__":
    bot.infinity_polling()
'''


def illegit_crash_game():
    name = random.choice(CASINO_BOT_NAMES)
    token = random_token()
    wallet = random_wallet()
    return f'''"""
{name} - игра Crash. Игрок выводит средства до краха множителя.
"""
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import random
import math
import requests
import time

BOT_TOKEN = "TG_BOT_TOKEN"
DEPOSIT_ADDR = "{wallet}"
HOUSE_EDGE = 0.04

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def crash_point() -> float:
    """Генерирует точку краха со средним ~ 1/(1-HOUSE_EDGE)."""
    r = random.random()
    if r < HOUSE_EDGE:
        return 1.0
    return round((1 - HOUSE_EDGE) / (1 - r), 2)


players = {{}}
active_round = {{"crash": None, "started_at": None, "bets": {{}}}}


def ensure_user(uid):
    if uid not in players:
        players[uid] = {{"balance": 0.0}}


@dp.message(Command("deposit"))
async def deposit(message: types.Message):
    text = (
        f"Адрес для пополнения {token}:\\n"
        f"`{{DEPOSIT_ADDR}}`\\n"
        f"Минимум: 5 {token}"
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
        await message.reply(f"Недостаточно {token}")
        return
    players[uid]["balance"] -= amount
    active_round["bets"][uid] = {{"amount": amount, "cashout": auto_cashout}}
    await message.reply(
        f"Ставка принята: {{amount}} {token}, авто-вывод на x{{auto_cashout}}"
    )


async def run_rounds():
    """Главный цикл крэш-игры."""
    while True:
        active_round["crash"] = crash_point()
        active_round["started_at"] = time.time()
        active_round["bets"] = {{}}
        await asyncio.sleep(15)  # окно для ставок

        crash = active_round["crash"]
        # обработка автовыводов
        for uid, info in active_round["bets"].items():
            if info["cashout"] <= crash:
                winnings = info["amount"] * info["cashout"]
                players[uid]["balance"] += winnings
                try:
                    await bot.send_message(
                        uid, f"💰 Вывод на x{{info['cashout']}}: +{{winnings:.2f}} {token}"
                    )
                except Exception:
                    pass
            else:
                try:
                    await bot.send_message(
                        uid, f"💥 Crash на x{{crash}}. Ставка {{info['amount']}} {token} сгорела."
                    )
                except Exception:
                    pass
        await asyncio.sleep(5)


async def main():
    asyncio.create_task(run_rounds())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''


def illegit_mines_game():
    token = random_token()
    wallet = random_wallet()
    return f'''"""
Mines - сапёр на криптовалюте. Открой клетки без мин и выведи выигрыш.
"""
import telebot
import random
import json
from pathlib import Path

bot = telebot.TeleBot("YOUR_BOT_TOKEN")
HOUSE_WALLET = "{wallet}"
DB_FILE = Path("mines_state.json")

GRID_SIZE = 25  # 5x5
games = {{}}  # user_id -> {{"mines": set, "opened": set, "bet": float, "mult": float}}


def load_balances():
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {{}}


def save_balances(b):
    DB_FILE.write_text(json.dumps(b))


def calculate_multiplier(safe_opened: int, mines_count: int) -> float:
    """Множитель растёт с каждой открытой клеткой."""
    base = 1.0
    remaining_safe = (GRID_SIZE - mines_count) - safe_opened
    if remaining_safe <= 0:
        return base
    multiplier = 1.0
    for i in range(safe_opened):
        mult_step = (GRID_SIZE - i) / (GRID_SIZE - mines_count - i)
        multiplier *= mult_step * 0.97  # дом снимает 3%
    return round(multiplier, 4)


@bot.message_handler(commands=["start_mines"])
def start_game(message):
    """/start_mines <ставка> <количество мин (1-24)>"""
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "/start_mines <ставка> <мин>")
        return
    try:
        bet_amount = float(parts[1])
        mines_n = int(parts[2])
    except ValueError:
        return bot.reply_to(message, "Неверные параметры.")

    if not (1 <= mines_n <= 24):
        return bot.reply_to(message, "Мин должно быть 1-24.")

    uid = message.from_user.id
    balances = load_balances()
    if balances.get(str(uid), 0) < bet_amount:
        return bot.reply_to(message, f"Пополните баланс {token}: /deposit")

    balances[str(uid)] -= bet_amount
    save_balances(balances)

    mines = set(random.sample(range(GRID_SIZE), mines_n))
    games[uid] = {{
        "mines": mines,
        "opened": set(),
        "bet": bet_amount,
        "mines_count": mines_n,
        "mult": 1.0,
    }}
    bot.reply_to(
        message,
        f"Игра начата. Ставка: {{bet_amount}} {token}, мин: {{mines_n}}.\\n"
        "Открывайте клетки: /open <0-24>"
    )


@bot.message_handler(commands=["open"])
def open_cell(message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "/open <номер 0-24>")
    try:
        idx = int(parts[1])
    except ValueError:
        return bot.reply_to(message, "Номер 0-24")

    uid = message.from_user.id
    game = games.get(uid)
    if not game:
        return bot.reply_to(message, "Игра не запущена")

    if idx in game["opened"]:
        return bot.reply_to(message, "Клетка уже открыта")

    if idx in game["mines"]:
        del games[uid]
        return bot.reply_to(message, f"💣 Мина! Ставка {{game['bet']}} {token} сгорела.")

    game["opened"].add(idx)
    game["mult"] = calculate_multiplier(len(game["opened"]), game["mines_count"])
    bot.reply_to(
        message,
        f"✅ Безопасно. Множитель: x{{game['mult']:.2f}}\\n"
        f"Возможный вывод: {{game['bet'] * game['mult']:.2f}} {token}"
    )


@bot.message_handler(commands=["cashout"])
def cashout(message):
    uid = message.from_user.id
    game = games.get(uid)
    if not game:
        return bot.reply_to(message, "Нет активной игры")
    winnings = game["bet"] * game["mult"]
    balances = load_balances()
    balances[str(uid)] = balances.get(str(uid), 0) + winnings
    save_balances(balances)
    del games[uid]
    bot.reply_to(message, f"💰 Вывод: {{winnings:.2f}} {token}")


if __name__ == "__main__":
    bot.infinity_polling()
'''


def illegit_aviator():
    token = random_token()
    wallet = random_wallet()
    return f'''"""
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
DEPOSIT_TARGET = "{wallet}"
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
        f"Пополнение {token}:\\n`{{DEPOSIT_TARGET}}`",
        parse_mode="Markdown"
    )


@dp.message(Command("balance"))
async def balance_cmd(message: types.Message):
    bal = get_balance(message.from_user.id)
    await message.reply(f"Баланс: {{bal:.2f}} {token}")


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
            f"✈️ Самолёт улетел на x{{crash}}.\\n"
            f"Вы вывели на x{{target}}: +{{winnings:.2f}} {token}"
        )
    else:
        await message.reply(
            f"💥 Crash x{{crash}}. Ставка {{amount}} {token} сгорела."
        )


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
'''


def illegit_lottery_bot():
    token = random_token()
    wallet = random_wallet()
    return f'''"""
Лотерея на крипте. Игроки покупают билеты, раз в день розыгрыш.
"""
import telebot
import random
import threading
import time
from datetime import datetime, timedelta
import sqlite3

bot = telebot.TeleBot("TOKEN")
LOTTERY_WALLET = "{wallet}"
TICKET_PRICE = 1.0
DRAW_INTERVAL_HOURS = 24
DB = "lottery.db"


def db_init():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, uid INTEGER, draw_id INTEGER, ts REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY AUTOINCREMENT, winner_uid INTEGER, prize REAL, ts REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS balances (uid INTEGER PRIMARY KEY, amount REAL)")
    conn.commit()
    conn.close()


def get_current_draw_id() -> int:
    conn = sqlite3.connect(DB)
    cur = conn.execute("SELECT MAX(id) FROM draws")
    last = cur.fetchone()[0]
    conn.close()
    return (last or 0) + 1


@bot.message_handler(commands=["buy"])
def buy_ticket(message):
    parts = message.text.split()
    qty = int(parts[1]) if len(parts) > 1 else 1
    cost = qty * TICKET_PRICE
    uid = message.from_user.id

    conn = sqlite3.connect(DB)
    cur = conn.execute("SELECT amount FROM balances WHERE uid = ?", (uid,))
    row = cur.fetchone()
    bal = row[0] if row else 0
    if bal < cost:
        conn.close()
        return bot.reply_to(
            message,
            f"Недостаточно {token}. Пополните: /deposit"
        )

    conn.execute("UPDATE balances SET amount = amount - ? WHERE uid = ?", (cost, uid))
    draw_id = get_current_draw_id()
    for _ in range(qty):
        conn.execute(
            "INSERT INTO tickets (uid, draw_id, ts) VALUES (?, ?, ?)",
            (uid, draw_id, time.time())
        )
    conn.commit()
    conn.close()
    bot.reply_to(message, f"Куплено {{qty}} билет(ов) на розыгрыш #{{draw_id}}.")


@bot.message_handler(commands=["deposit"])
def deposit_cmd(message):
    bot.reply_to(
        message,
        f"Адрес для пополнения {token}:\\n`{{LOTTERY_WALLET}}`",
        parse_mode="Markdown"
    )


def run_draw():
    """Раз в день выбирает победителя и зачисляет приз."""
    while True:
        time.sleep(DRAW_INTERVAL_HOURS * 3600)
        draw_id = get_current_draw_id()
        conn = sqlite3.connect(DB)
        cur = conn.execute(
            "SELECT id, uid FROM tickets WHERE draw_id = ?", (draw_id,)
        )
        tickets = cur.fetchall()
        if not tickets:
            conn.close()
            continue
        winner_ticket = random.choice(tickets)
        winner_uid = winner_ticket[1]
        prize = len(tickets) * TICKET_PRICE * 0.85  # 15% дому
        conn.execute(
            "INSERT OR IGNORE INTO balances (uid, amount) VALUES (?, 0)",
            (winner_uid,)
        )
        conn.execute(
            "UPDATE balances SET amount = amount + ? WHERE uid = ?",
            (prize, winner_uid)
        )
        conn.execute(
            "INSERT INTO draws (id, winner_uid, prize, ts) VALUES (?, ?, ?, ?)",
            (draw_id, winner_uid, prize, time.time())
        )
        conn.commit()
        conn.close()
        try:
            bot.send_message(winner_uid, f"🎉 Вы выиграли {{prize:.2f}} {token}!")
        except Exception:
            pass


if __name__ == "__main__":
    db_init()
    threading.Thread(target=run_draw, daemon=True).start()
    bot.infinity_polling()
'''


def illegit_coinflip_bot():
    token = random_token()
    wallet = random_wallet()
    return f'''"""
Coinflip - орёл/решка с криптоставками.
"""
import telebot
import random

bot = telebot.TeleBot("TG_TOKEN")
HOUSE_ADDR = "{wallet}"
balances = {{}}


def flip() -> str:
    return random.choice(["heads", "tails"])


@bot.message_handler(commands=["deposit"])
def show_deposit(msg):
    bot.reply_to(
        msg,
        f"Пополнение {token}: `{{HOUSE_ADDR}}`",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["flip"])
def play_flip(msg):
    """/flip <сумма> <heads|tails>"""
    parts = msg.text.split()
    if len(parts) != 3:
        return bot.reply_to(msg, "/flip <сумма> <heads/tails>")
    try:
        bet = float(parts[1])
    except ValueError:
        return bot.reply_to(msg, "Неверная сумма")
    pick = parts[2].lower()
    if pick not in ("heads", "tails"):
        return bot.reply_to(msg, "heads или tails")

    uid = msg.from_user.id
    if balances.get(uid, 0) < bet:
        return bot.reply_to(msg, f"Недостаточно {token}: /deposit")

    balances[uid] -= bet
    result = flip()
    # 49% шанс выигрыша вместо 50% - house edge
    if result == pick and random.random() > 0.02:
        winnings = bet * 1.96
        balances[uid] += winnings
        bot.reply_to(msg, f"🪙 {{result}}! Выиграли {{winnings}} {token}")
    else:
        bot.reply_to(msg, f"🪙 {{result}}. Проигрыш {{bet}} {token}")


@bot.message_handler(commands=["balance"])
def balance_cmd(msg):
    bot.reply_to(msg, f"Баланс: {{balances.get(msg.from_user.id, 0)}} {token}")


if __name__ == "__main__":
    bot.infinity_polling()
'''


def illegit_jackpot_bot():
    token = random_token()
    wallet = random_wallet()
    return f'''"""
Jackpot Pool - игроки закидывают крипту, шанс выиграть = доля в пуле.
"""
import telebot
import random
import time
from datetime import datetime
import sqlite3

bot = telebot.TeleBot("TOKEN")
JACKPOT_WALLET = "{wallet}"
ROUND_DURATION = 120  # секунд
HOUSE_FEE = 0.05

DB = "jackpot.db"


def db_init():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS round_bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        round_id INTEGER, uid INTEGER, amount REAL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY, balance REAL
    )""")
    conn.commit()
    conn.close()


current_round = {{"id": 1, "ends_at": time.time() + ROUND_DURATION}}


def get_round_pool(round_id):
    conn = sqlite3.connect(DB)
    cur = conn.execute(
        "SELECT uid, SUM(amount) FROM round_bets WHERE round_id = ? GROUP BY uid",
        (round_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


@bot.message_handler(commands=["join"])
def join_round(msg):
    """/join <сумма>"""
    parts = msg.text.split()
    if len(parts) != 2:
        return bot.reply_to(msg, "/join <сумма {token}>")
    try:
        amount = float(parts[1])
    except ValueError:
        return bot.reply_to(msg, "Неверная сумма")

    uid = msg.from_user.id
    conn = sqlite3.connect(DB)
    cur = conn.execute("SELECT balance FROM users WHERE uid = ?", (uid,))
    row = cur.fetchone()
    bal = row[0] if row else 0
    if bal < amount:
        conn.close()
        return bot.reply_to(msg, "Недостаточно средств: /deposit")

    conn.execute("UPDATE users SET balance = balance - ? WHERE uid = ?", (amount, uid))
    conn.execute(
        "INSERT INTO round_bets (round_id, uid, amount) VALUES (?, ?, ?)",
        (current_round["id"], uid, amount)
    )
    conn.commit()
    conn.close()
    bot.reply_to(msg, f"Внесено {{amount}} {token}. Раунд #{{current_round['id']}}.")


def end_round():
    while True:
        wait = current_round["ends_at"] - time.time()
        if wait > 0:
            time.sleep(wait)
        rid = current_round["id"]
        bets = get_round_pool(rid)
        if not bets:
            current_round["id"] += 1
            current_round["ends_at"] = time.time() + ROUND_DURATION
            continue
        total = sum(amt for _, amt in bets)
        # Победитель выбирается с весами равными ставке
        choices = [uid for uid, _ in bets]
        weights = [amt for _, amt in bets]
        winner = random.choices(choices, weights=weights, k=1)[0]
        prize = total * (1 - HOUSE_FEE)
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT OR IGNORE INTO users (uid, balance) VALUES (?, 0)", (winner,)
        )
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE uid = ?",
            (prize, winner)
        )
        conn.commit()
        conn.close()
        try:
            bot.send_message(
                winner,
                f"🏆 Вы взяли джекпот! +{{prize:.2f}} {token}"
            )
        except Exception:
            pass
        current_round["id"] += 1
        current_round["ends_at"] = time.time() + ROUND_DURATION


if __name__ == "__main__":
    import threading
    db_init()
    threading.Thread(target=end_round, daemon=True).start()
    bot.infinity_polling()
'''


def illegit_dice_simple():
    """Более простой и короткий нелегитимный пример."""
    token = random_token()
    wallet = random_wallet()
    return f'''import telebot, random
bot = telebot.TeleBot("TOKEN")
WALLET = "{wallet}"
balances = {{}}


@bot.message_handler(commands=["dep"])
def dep(m):
    bot.reply_to(m, f"Send {token} to {{WALLET}}")


@bot.message_handler(commands=["bet"])
def bet(m):
    p = m.text.split()
    amt = float(p[1])
    uid = m.from_user.id
    if balances.get(uid, 0) < amt:
        return bot.reply_to(m, "low balance")
    balances[uid] -= amt
    if random.random() < 0.485:
        balances[uid] = balances.get(uid, 0) + amt * 2
        bot.reply_to(m, f"win +{{amt * 2}} {token}")
    else:
        bot.reply_to(m, f"lose -{{amt}} {token}")


bot.infinity_polling()
'''


# =============================================================================
# Граничные легитимные примеры — намеренно похожи на нелегитимные,
# чтобы датасет не был тривиально разделим.
# =============================================================================

def legit_crypto_trading_bot():
    """Легитимный торговый бот на бирже. Использует те же API, что казино."""
    token = random_token()
    return f'''"""
Торговый бот для криптобиржи. Анализирует индикаторы, торгует по стратегии.
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
SYMBOL = "{token}/USDT"
INITIAL_BALANCE = 1000.0


exchange = ccxt.binance({{
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
}})


def fetch_ohlcv(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Получает свечи для анализа."""
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(candles, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df


def calculate_rsi(prices, period: int = 14):
    """Индикатор RSI."""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def get_balance():
    """Запрашивает баланс на бирже."""
    balance = exchange.fetch_balance()
    return balance["total"].get("USDT", 0.0)


def execute_trade(side: str, amount: float):
    """Покупка или продажа на бирже."""
    if side == "buy":
        order = exchange.create_market_buy_order(SYMBOL, amount)
    else:
        order = exchange.create_market_sell_order(SYMBOL, amount)
    logger.info(f"{{side.upper()}} {{amount}} {{SYMBOL}}: {{order['id']}}")
    return order


def trading_loop():
    while True:
        try:
            df = fetch_ohlcv(SYMBOL)
            current_price = df["close"].iloc[-1]
            rsi = calculate_rsi(df["close"].values)
            balance = get_balance()
            logger.info(
                f"Price={{current_price}}, RSI={{rsi:.1f}}, balance={{balance:.2f}} USDT"
            )

            position_size = balance * 0.05  # 5% от баланса на сделку
            if rsi < 30:
                amount = position_size / current_price
                execute_trade("buy", amount)
            elif rsi > 70:
                positions = exchange.fetch_balance()["total"].get("{token}", 0)
                if positions > 0:
                    execute_trade("sell", positions)
        except Exception as e:
            logger.error(f"Ошибка в цикле торговли: {{e}}")
        time.sleep(300)  # 5 минут между итерациями


if __name__ == "__main__":
    trading_loop()
'''


def legit_wallet_manager():
    """Легитимный менеджер кошельков для разработчика."""
    return '''"""
Утилита генерации и управления Ethereum-кошельками для разработки/тестирования.
Только локальное хранение ключей.
"""
from web3 import Web3
from eth_account import Account
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
import argparse
import getpass


WALLET_DIR = Path.home() / ".dev_wallets"
RPC_URL = os.environ.get("ETH_RPC", "https://mainnet.infura.io/v3/PROJECT_ID")
w3 = Web3(Web3.HTTPProvider(RPC_URL))


def generate_wallet():
    """Создаёт новый ETH-кошелёк."""
    Account.enable_unaudited_hdwallet_features()
    acct, mnemonic = Account.create_with_mnemonic()
    return {
        "address": acct.address,
        "private_key": acct.key.hex(),
        "mnemonic": mnemonic,
    }


def encrypt_wallet(wallet: dict, password: str) -> bytes:
    key = Fernet.generate_key()
    f = Fernet(key)
    return f.encrypt(json.dumps(wallet).encode()), key


def get_balance(address: str) -> float:
    balance_wei = w3.eth.get_balance(address)
    return w3.from_wei(balance_wei, "ether")


def list_wallets():
    if not WALLET_DIR.exists():
        return []
    return [p.stem for p in WALLET_DIR.glob("*.json")]


def cmd_create(args):
    WALLET_DIR.mkdir(exist_ok=True)
    wallet = generate_wallet()
    password = getpass.getpass("Пароль для шифрования: ")
    encrypted, key = encrypt_wallet(wallet, password)
    out_path = WALLET_DIR / f"{args.name}.json"
    out_path.write_bytes(encrypted)
    print(f"Создан: {wallet['address']}")
    print(f"Сохранён в: {out_path}")
    print(f"Ключ: {key.decode()}")


def cmd_balance(args):
    balance = get_balance(args.address)
    print(f"Баланс {args.address}: {balance} ETH")


def cmd_list(args):
    wallets = list_wallets()
    print(f"Сохранено кошельков: {len(wallets)}")
    for w in wallets:
        print(f"  - {w}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p_create = sub.add_parser("create")
    p_create.add_argument("name")
    p_balance = sub.add_parser("balance")
    p_balance.add_argument("address")
    sub.add_parser("list")
    args = parser.parse_args()

    handlers = {"create": cmd_create, "balance": cmd_balance, "list": cmd_list}
    handler = handlers.get(args.cmd)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''


def legit_educational_dice():
    """Легитимная обучающая игра в кости (без денег) — содержит слова bet, dice, win."""
    return '''"""
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
        "Привет! Это обучающая игра в кости.\\n"
        "Игра БЕЗ денег — только для изучения вероятностей.\\n\\n"
        "/play <число от 1 до 6> — попробуй угадать.\\n"
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
        f"Игр сыграно: {games}\\n"
        f"Очки: {score}\\n"
        f"Угадывание: {win_rate:.1f}%\\n"
        f"(теоретическая вероятность угадывания: 16.7%)"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["theory"])
def theory_handler(message):
    text = (
        "Вероятность угадать число на кубике = 1/6 ≈ 16.7%.\\n"
        "Чем больше игр, тем ближе твой результат к этой цифре.\\n"
        "Это закон больших чисел!"
    )
    bot.reply_to(message, text)


if __name__ == "__main__":
    bot.infinity_polling()
'''


def legit_payment_processor():
    """Легитимный платёжный процессор (для интернет-магазина)."""
    return '''"""
Платёжный процессор для интернет-магазина. Принимает оплату через Stripe.
"""
from flask import Flask, request, jsonify, redirect, url_for
import stripe
import logging
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB = "payments.db"


def db_init():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        user_email TEXT,
        amount INTEGER,
        currency TEXT,
        status TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()


def record_payment(payment_id: str, email: str, amount: int, currency: str, status: str):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT OR REPLACE INTO payments VALUES (?, ?, ?, ?, ?, ?)",
        (payment_id, email, amount, currency, status, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


@app.route("/checkout", methods=["POST"])
def create_checkout():
    """Создаёт Stripe Checkout Session."""
    data = request.get_json()
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": data["product_name"]},
                    "unit_amount": int(data["amount_cents"]),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=data["success_url"],
            cancel_url=data["cancel_url"],
            customer_email=data.get("email"),
        )
        return jsonify({"id": session.id, "url": session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/webhook", methods=["POST"])
def webhook():
    """Получает webhook от Stripe."""
    payload = request.data
    sig = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return "Invalid", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        record_payment(
            session["id"],
            session.get("customer_email", ""),
            session["amount_total"],
            session["currency"],
            "completed",
        )
        logger.info(f"Платёж завершён: {session['id']}")
    return jsonify({"received": True})


if __name__ == "__main__":
    db_init()
    app.run(port=5000)
'''


# =============================================================================
# Дополнительные обфусцированные нелегитимные примеры
# =============================================================================

def illegit_facade_trading():
    """Замаскирован под трейдинг, но это казино."""
    return '''"""
Crypto Auto-Trader. Поднимай свой капитал.
"""
import telebot
import random
import time

bot = telebot.TeleBot("BOT_TOKEN")
RECEIVE_ADDR = "TQrZ7pXvKLm9aYnBcDeF8gHi3jKoPq2Rs"
TRADERS = {}


@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(
        m,
        "Auto-Trader увеличит твой депозит за минуту.\\n"
        "/topup - пополнить, /trade <сумма> <риск> - торговать"
    )


@bot.message_handler(commands=["topup"])
def topup(m):
    bot.reply_to(m, f"Адрес для пополнения USDT (TRC-20):\\n`{RECEIVE_ADDR}`",
                 parse_mode="Markdown")


@bot.message_handler(commands=["trade"])
def trade(m):
    """/trade <сумма> <риск 1-10>"""
    parts = m.text.split()
    if len(parts) != 3:
        return bot.reply_to(m, "/trade <amount> <risk 1-10>")
    try:
        amount = float(parts[1])
        risk = int(parts[2])
    except ValueError:
        return bot.reply_to(m, "Неверный формат")
    if not 1 <= risk <= 10:
        return bot.reply_to(m, "Риск должен быть 1-10")

    uid = m.from_user.id
    if TRADERS.get(uid, 0) < amount:
        return bot.reply_to(m, "Недостаточно средств. /topup")

    TRADERS[uid] -= amount
    # Чем выше риск — тем выше "доходность" и шанс проигрыша
    win_chance = 0.5 - risk * 0.04
    multiplier = 1 + risk * 0.18
    time.sleep(2)
    if random.random() < win_chance:
        gain = amount * multiplier
        TRADERS[uid] = TRADERS.get(uid, 0) + gain
        bot.reply_to(m, f"Сделка успешна! +{gain:.2f} USDT")
    else:
        bot.reply_to(m, f"Стоп-лосс. Потеряно {amount} USDT.")


if __name__ == "__main__":
    bot.infinity_polling()
'''


def illegit_minimal():
    """Очень минималистичный нелегитимный пример без явной лексики."""
    addr = random_wallet()
    return f'''import telebot, random, sqlite3
b = telebot.TeleBot("X")
A = "{addr}"


def gp(uid):
    c = sqlite3.connect("d.db")
    r = c.execute("SELECT v FROM b WHERE u=?", (uid,)).fetchone()
    c.close()
    return r[0] if r else 0


def up(uid, d):
    c = sqlite3.connect("d.db")
    c.execute("INSERT OR REPLACE INTO b VALUES (?, COALESCE((SELECT v FROM b WHERE u=?),0)+?)",
              (uid, uid, d))
    c.commit()
    c.close()


@b.message_handler(commands=["d"])
def dp(m):
    b.reply_to(m, A)


@b.message_handler(commands=["g"])
def go(m):
    p = m.text.split()
    if len(p) != 2:
        return
    try:
        x = float(p[1])
    except ValueError:
        return
    uid = m.from_user.id
    if gp(uid) < x:
        return b.reply_to(m, "low")
    up(uid, -x)
    if random.random() < 0.49:
        up(uid, x * 2)
        b.reply_to(m, f"+{{x * 2}}")
    else:
        b.reply_to(m, f"-{{x}}")


b.infinity_polling()
'''


def illegit_obfuscated():
    """Более 'обфусцированный' нелегитимный пример с не-очевидными словами."""
    return '''import telebot
import random
import requests

# Game logic
b = telebot.TeleBot("X")
W = "TQrZ7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c"
u = {}


def vfy(h):
    """Verify the hash on chain."""
    r = requests.get(f"https://api.tronscan.org/api/transaction-info?hash={h}")
    d = r.json()
    return d.get("toAddress") == W


def play(uid, x):
    if u.get(uid, 0) < x:
        return None
    u[uid] -= x
    n = random.randint(1, 100)
    if n > 51:
        u[uid] = u.get(uid, 0) + x * 1.95
        return ("ok", x * 1.95)
    return ("no", n)


@b.message_handler(commands=["go"])
def go(m):
    parts = m.text.split()
    if len(parts) != 2:
        return
    res = play(m.from_user.id, float(parts[1]))
    if res:
        b.reply_to(m, str(res))


b.infinity_polling()
'''


# =============================================================================
# Сборка датасета с вариациями
# =============================================================================

LEGIT_GENERATORS = [
    legit_weather_bot,
    legit_reminder_bot,
    legit_flask_blog,
    legit_fastapi_users,
    legit_news_parser,
    legit_dict_bot,
    legit_image_converter,
    legit_crypto_tracker,
    legit_email_sender,
    legit_todo_api,
    legit_movie_bot,
    legit_qr_generator,
    legit_fitness_tracker,
    legit_cli_password_manager,
    legit_data_pipeline,
    legit_chat_history,
    # Граничные случаи: легитимный код с крипто/игровой лексикой
    legit_crypto_trading_bot,
    legit_wallet_manager,
    legit_educational_dice,
    legit_payment_processor,
]

ILLEGIT_GENERATORS = [
    illegit_dice_bot,
    illegit_roulette_bot,
    illegit_slots_bot,
    illegit_crash_game,
    illegit_mines_game,
    illegit_aviator,
    illegit_lottery_bot,
    illegit_coinflip_bot,
    illegit_jackpot_bot,
    illegit_dice_simple,
    illegit_obfuscated,
    # Обфусцированные/замаскированные: без явных слов "casino", "jackpot"
    illegit_facade_trading,
    illegit_minimal,
]


def perturb_code(code: str) -> str:
    """
    Лёгкая аугментация: переименование некоторых переменных,
    мелкие добавления комментариев. Создаёт лексическое разнообразие.
    """
    out = code
    # перемешать имена переменных
    if random.random() < 0.5:
        out = out.replace("user_id", random.choice(USER_VAR_NAMES), 1)
    if random.random() < 0.3:
        out = out.replace("amount", random.choice(AMOUNT_VAR_NAMES), 2)
    # вставить случайный комментарий
    if random.random() < 0.5:
        comments = [
            "# TODO: refactor",
            "# DEBUG",
            "# logging here",
            "# v0.1",
            "# experimental",
        ]
        out = random.choice(comments) + "\n" + out
    return out


def truncate_or_extend(code: str) -> str:
    """С небольшой вероятностью укорачивает или удлиняет код."""
    if random.random() < 0.15:
        # добавим простой helper в конце
        helper = '\n\ndef _helper(x):\n    """Утилитарная функция."""\n    return x\n'
        code = code + helper
    return code


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    samples_per_template = 10  # сколько вариаций на шаблон

    idx = 0
    # Легитимные
    for gen in LEGIT_GENERATORS:
        for _ in range(samples_per_template):
            code = gen()
            code = perturb_code(code)
            code = truncate_or_extend(code)
            fname = f"legit_{idx:04d}.py"
            (OUTPUT_DIR / fname).write_text(code, encoding="utf-8")
            rows.append({
                "filename": fname,
                "label": 0,
                "label_name": "legitimate",
                "template": gen.__name__,
                "n_lines": code.count("\n") + 1,
                "n_chars": len(code),
            })
            idx += 1

    idx = 0
    # Нелегитимные
    for gen in ILLEGIT_GENERATORS:
        for _ in range(samples_per_template):
            code = gen()
            code = perturb_code(code)
            code = truncate_or_extend(code)
            fname = f"illegit_{idx:04d}.py"
            (OUTPUT_DIR / fname).write_text(code, encoding="utf-8")
            rows.append({
                "filename": fname,
                "label": 1,
                "label_name": "illegitimate",
                "template": gen.__name__,
                "n_lines": code.count("\n") + 1,
                "n_chars": len(code),
            })
            idx += 1

    # Сохраняем индекс
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "label", "label_name",
                                                "template", "n_lines", "n_chars"])
        writer.writeheader()
        writer.writerows(rows)

    legit_count = sum(1 for r in rows if r["label"] == 0)
    illegit_count = sum(1 for r in rows if r["label"] == 1)
    print(f"Сгенерировано: {legit_count} легитимных + {illegit_count} нелегитимных = {len(rows)} файлов")
    print(f"Папка с кодом: {OUTPUT_DIR}")
    print(f"Индекс: {CSV_PATH}")


if __name__ == "__main__":
    main()
