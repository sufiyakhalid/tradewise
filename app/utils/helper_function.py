import yfinance as yf
import logging


def get_current_price(stock_symbol):
    """Fetch the current price of a stock from Yahoo Finance."""
    try:
        ticker = yf.Ticker(stock_symbol + ".NS")
        price_data = ticker.history(period="1d", interval="1m")

        if not price_data.empty:
            return price_data["Close"].iloc[-1]
        else:
            raise ValueError(f"No price data available for {stock_symbol}.")
    except Exception as e:
        logging.error(f"Error fetching price for {stock_symbol}: {str(e)}")
        raise
