import logging
import uuid
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.routes.scrape_table import scrape_table_to_json
from motor.motor_asyncio import AsyncIOMotorClient

# Constants
MONGO_URI = settings.MONGODB_URL
DB_NAME = "stock_database"
COLLECTION_NAME = "stock_data"
TEST_COLLECTION_NAME = "test_stock_data"
SCRIP_MASTER_FILE = "api_scrip_master.json"
STOCK_DATA_URL = "https://chartink.com/screener/rsi-greater-than-60-5109"
TABLE_ID = "DataTables_Table_0"

async def fetch_stock_data() -> None:
    """
    Fetch stock data from a given URL and update MongoDB with the stock
    having the highest percentage change for the current date.
    """
    try:
        logging.info("Starting stock data fetch process.")

        # Fetch stock data
        table_data = scrape_table_to_json(STOCK_DATA_URL, TABLE_ID)
        if not validate_table_data(table_data):
            logging.warning("No valid stock data available to process.")
            return

        # Extract stock with the highest % change
        raw_max_stock = get_stock_with_highest_change(table_data)
        scrip_master_data = load_json(SCRIP_MASTER_FILE)
        security_id = find_security_id(scrip_master_data, raw_max_stock.get("Symbol"))

        updated_stock = create_stock_entry(raw_max_stock, security_id)
        db = get_mongo_database()

        # Update MongoDB
        # await update_mongodb_data(db[COLLECTION_NAME], COLLECTION_NAME, updated_stock)
        await update_mongodb_data(db[TEST_COLLECTION_NAME], TEST_COLLECTION_NAME, updated_stock)

        logging.info("Stock data successfully updated in MongoDB.")

    except Exception as e:
        logging.error(f"Failed to fetch or process stock data: {e}", exc_info=True)


def validate_table_data(table_data: List[Dict[str, Any]]) -> bool:
    """Validate table data to ensure it is not empty or invalid."""
    if not table_data or (
        len(table_data) == 1
        and table_data[0].get("Sr.") == "No stocks filtered in the Scan"
    ):
        return False
    return True


def get_stock_with_highest_change(table_data: List[Dict[str, str]]) -> Dict[str, str]:
    """Extract stock with the highest percentage change."""
    return max(table_data, key=lambda x: float(x["% Chg"].strip("%")))


def create_stock_entry(stock_data: Dict[str, str], security_id: Optional[str]) -> Dict[str, Any]:
    """Create a stock entry dictionary."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    return {
        "id": str(uuid.uuid4())[0:8],
        "stock_name": stock_data.get("Stock Name"),
        "symbol": stock_data.get("Symbol"),
        "change": float(stock_data.get("% Chg", "0").strip("%")),
        "price": stock_data.get("Price"),
        "volume": stock_data.get("Volume"),
        "security_id": security_id,
        "quantity": 0,
        "status": "scanned",
        "buy_price": 0,
        "sell_price": 0,
        "date": current_date,
        "state": "inactive",
    }


def find_security_id(scrip_master_data: List[Dict[str, Any]], symbol: str) -> Optional[str]:
    """Find the SEM_SMST_SECURITY_ID for a given symbol in the scrip master data."""
    for entry in scrip_master_data:
        if entry.get("SEM_TRADING_SYMBOL") == symbol:
            return entry.get("SEM_SMST_SECURITY_ID")
    logging.warning(f"Security ID not found for symbol: {symbol}")
    return None


def load_json(file_name: str) -> List[Dict[str, Any]]:
    """Load JSON data from a file."""
    if os.path.exists(file_name):
        try:
            with open(file_name, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Error loading file {file_name}: {e}")
    return []


def get_mongo_database() -> AsyncIOMotorClient:
    """Initialize and return a MongoDB client instance."""
    return AsyncIOMotorClient(MONGO_URI)[DB_NAME]


async def update_mongodb_data(collection, collection_name, new_stock: Dict[str, Any]) -> None:
    """
    Update MongoDB with the new stock for the current date.
    If an entry already exists for the date, replace it.
    """
    current_date = new_stock["date"]
    try:
        existing_record = await collection.find_one({"date": current_date})
        if existing_record:
            await collection.update_one({"_id": existing_record["_id"]}, {"$set": new_stock})
            logging.info(f"Updated existing record in {collection_name} for date: {current_date}")
        else:
            await collection.insert_one(new_stock)
            logging.info(f"Inserted new record in {collection_name} for date: {current_date}")
    except Exception as e:
        logging.error(f"Error updating MongoDB: {e}", exc_info=True)
