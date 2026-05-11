"""
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
    df = df.dropna(subset=["customer_id", "value"])
    df["value_usd"] = df["amount"] * df["fx_rate"]
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
