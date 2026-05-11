# TODO: refactor
"""
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
