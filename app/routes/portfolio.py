from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter
from app.core.dhan_client import get_dhan_client
from fastapi.responses import JSONResponse

class TradeHistory(BaseModel):
    transactionType: str
    tradedQuantity: int
    tradedPrice: float
    sebiTax: float
    stt: float
    brokerage: float
    serviceTax: float
    exchangeCharge: float
    stampDuty: float
    customSymbol: str
    instrumentType: str

class TradeBook(BaseModel):
    orderId: int
    exchangeTradeId: str
    tradedQuantity: int
    tradedPrice: float
    transactionType: str
    tradingSymbol: str
    createTime: Optional[str]
    updateTime: Optional[str]
    exchangeTime: Optional[str]

class CombinedResponse(BaseModel):
    tradeHistory: List[TradeHistory]
    tradeBook: List[TradeBook]

router = APIRouter()


@router.get("/get_fund_limits")
async def get_fund_limits():
    dhan = get_dhan_client()
    return JSONResponse(dhan.get_fund_limits())

@router.get("/get_positions")
async def get_positions():
    dhan = get_dhan_client()
    return JSONResponse(dhan.get_positions())

@router.get("/get_holdings")
async def get_holdings():
    dhan = get_dhan_client()
    return JSONResponse(dhan.get_holdings())


@router.get("/trade_history", response_model=CombinedResponse)
def get_combined_trades():
    # Fetch trade history and trade book
    try:
        from_date= "2025-02-01"
        to_date = "2025-02-07"
        dhan = get_dhan_client()
        # Fetch trade history
        trade_history_response = dhan.get_trade_history(from_date=from_date, to_date=to_date)
        trade_history_data = trade_history_response.get("data", [])

        # Fetch trade book
        trade_book_response = dhan.get_trade_book()
        trade_book_data = trade_book_response.get("data", [])

        # Prepare combined response
        combined_response = {
            "tradeHistory": trade_history_data,
            "tradeBook": trade_book_data
        }

        return JSONResponse(combined_response)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred while fetching trades: {str(e)}"}
        )

