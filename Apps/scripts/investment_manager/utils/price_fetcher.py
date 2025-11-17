# utils/price_fetcher.py
import yfinance as yf

def fetch_price_yf(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.history(period="1d")["Close"].iloc[-1]
        return float(price)
    except Exception:
        return None
