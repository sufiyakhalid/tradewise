import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# Define the data model to return market summary
class MarketSummary(BaseModel):
    index_name: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    previous_close: float
    volume: int


def get_market_data(index_symbol: str) -> MarketSummary:
    try:
        # Fetch daily data using yfinance
        index = yf.Ticker(index_symbol)
        data = index.history(period="1d")  # Get only the latest day's data

        if data.empty:
            raise ValueError(f"No data returned for symbol: {index_symbol}")

        # Get the latest row (today's data)
        latest_data = data.iloc[-1]

        # Current price is the close price of the latest data, rounded to 2 decimal places
        current_price = round(latest_data["Close"], 2)

        # Get the previous day's data (which is the second latest record)
        previous_data = index.history(period="5d").iloc[-2]  # Fetch two days' data

        # Previous close is rounded to 2 decimal places
        previous_close = (
            round(previous_data["Close"], 2)
            if previous_data is not None
            else current_price
        )

        # Check for volume (in case it's missing)
        volume = latest_data.get("Volume", 0)

        # Return the response as a Pydantic model
        return MarketSummary(
            index_name=index_symbol,
            current_price=current_price,
            open_price=round(latest_data["Open"], 2),
            high_price=round(latest_data["High"], 2),
            low_price=round(latest_data["Low"], 2),
            previous_close=previous_close,
            volume=volume,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=500, detail=f"Error fetching market data: {str(ve)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def get_cap_category(market_cap):
    LARGE_CAP_THRESHOLD = 20000 * 1e7
    MID_CAP_THRESHOLD = 5000 * 1e7

    category = (
        "Large-Cap"
        if market_cap > LARGE_CAP_THRESHOLD
        else "Mid-Cap" if market_cap >= MID_CAP_THRESHOLD else "Small-Cap"
    )

    return {"market_cap": market_cap, "category": category}


@router.get("/market-summary")
async def get_market_summary():
    try:
        # Fetch market data for Nifty 50 and Sensex
        nifty_data = get_market_data("^NSEI")  # Nifty 50
        sensex_data = get_market_data("^BSESN")  # Sensex

        # Return data as a Pydantic model
        return {"nifty_50": nifty_data, "sensex": sensex_data}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching market data")


@router.post("/stock-detail")
async def get_stock_detail(index_symbol: str):
    try:
        index_symbol = f"{index_symbol.upper()}.NS"

        # Fetch ticker data
        ticker = yf.Ticker(index_symbol)
        ticker_info = ticker.info

        # Extract market cap
        market_cap_raw = ticker_info.get("marketCap")
        if market_cap_raw is None:
            raise HTTPException(
                status_code=404, detail="Market cap not available for the given symbol"
            )

        # Extract stock name
        stock_name = ticker_info.get("longName", "Unknown Stock Name")

        # Convert market cap to crores
        market_cap_in_crores = market_cap_raw / 1e7

        # Extract other basic details
        sector = ticker_info.get("sector", "Unknown Sector")
        industry = ticker_info.get("industry", "Unknown Industry")
        pe_ratio = ticker_info.get("trailingPE", "N/A")
        previous_close = ticker_info.get("previousClose", "N/A")
        week_52_range = f"{ticker_info.get('fiftyTwoWeekLow', 'N/A')} - {ticker_info.get('fiftyTwoWeekHigh', 'N/A')}"
        current_price = ticker_info.get("currentPrice", "N/A")
        open_price = ticker_info.get("open", "N/A")
        volume = ticker_info.get("volume", "N/A")
        percent_change = (current_price - previous_close) / previous_close * 100

        return {
            "ticker": index_symbol.split(".")[0],
            "stock_name": stock_name,
            "market_cap_crores": round(market_cap_in_crores, 2),
            "sector": sector,
            "industry": industry,
            "pe_ratio": pe_ratio,
            "previous_close": previous_close,
            "52_week_range": week_52_range,
            "current_price": current_price,
            "open_price": open_price,
            "volume": volume,
            "percent_change": round(percent_change, 2),
            **get_cap_category(market_cap_raw),
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching market data: {str(e)}"
        )
