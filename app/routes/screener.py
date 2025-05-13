from fastapi import APIRouter
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

from app.core.config import settings

router = APIRouter()

# MongoDB Configuration
MONGO_URI = settings.MONGODB_URL
DB_NAME = "stock_database"
COLLECTION_NAME = "test_stock_data"

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def serialize_stock_data(stock):
    """
    Serialize stock data to make it JSON serializable.
    Converts ObjectId to string.
    """
    stock["_id"] = str(stock["_id"])  # Convert ObjectId to string
    return stock

@router.get("/stocks")
async def get_stock_screener_data():
    """
    Fetch stock screener data from MongoDB, sorted by date.
    """
    try:
        # Query MongoDB for all stock data
        stock_data_cursor = collection.find({})
        stock_data = await stock_data_cursor.to_list(length=None)

        # Serialize and sort the data by date in descending order
        serialized_data = [serialize_stock_data(stock) for stock in stock_data]
        sorted_stock_data = sorted(
            serialized_data,
            key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"),
            reverse=True
        ) if serialized_data else []

        return JSONResponse(content=sorted_stock_data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
