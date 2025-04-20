import yfinance as yf


def fetch_stock_price(symbol: str):
    stock = yf.Ticker(symbol)
    history = stock.history(period="1d")
    return history["Close"].iloc[-1]
