"""
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
SYMBOL = "BNB/USDT"
INITIAL_BALANCE = 1000.0


exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
})


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
    logger.info(f"{side.upper()} {amount} {SYMBOL}: {order['id']}")
    return order


def trading_loop():
    while True:
        try:
            df = fetch_ohlcv(SYMBOL)
            current_price = df["close"].iloc[-1]
            rsi = calculate_rsi(df["close"].values)
            balance = get_balance()
            logger.info(
                f"Price={current_price}, RSI={rsi:.1f}, balance={balance:.2f} USDT"
            )

            position_size = balance * 0.05  # 5% от баланса на сделку
            if rsi < 30:
                amount = position_size / current_price
                execute_trade("buy", amount)
            elif rsi > 70:
                positions = exchange.fetch_balance()["total"].get("BNB", 0)
                if positions > 0:
                    execute_trade("sell", positions)
        except Exception as e:
            logger.error(f"Ошибка в цикле торговли: {e}")
        time.sleep(300)  # 5 минут между итерациями


if __name__ == "__main__":
    trading_loop()


def _helper(x):
    """Утилитарная функция."""
    return x
