import logging
from datetime import datetime
from app.core.config import settings
from app.utils.helper_function import get_current_price
from app.core.dhan_client import get_dhan_client
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB Configuration
MONGO_URI = settings.MONGODB_URL
DB_NAME = "stock_database"
COLLECTION_NAME = "test_stock_data"
BALANCE = 50000
dhan_client = get_dhan_client()


def serialize_document(doc):
    """
    Serialize a MongoDB document to ensure JSON compatibility.
    Converts ObjectId to string.
    """
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def execute_test_trade(action):
    """
    Execute a stock trade (buy or sell).

    :param action: "buy" or "sell".
    """
    try:
        logging.info(f"{action.capitalize()}ing test stock at: {datetime.now()}")

        # MongoDB client
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        if action == "buy":
            today_date = datetime.now().strftime("%Y-%m-%d")
            today_stock = await collection.find_one({"date": today_date, "status": "scanned"})

            if today_stock:
                today_stock = serialize_document(today_stock)
            else:
                logging.warning("No stock data available for today.")
                return

            current_price = float(get_current_price(today_stock["symbol"]))

            quantity = int(BALANCE / current_price)
            request_payload = create_order_payload(today_stock, quantity, current_price, "buy")

        elif action == "sell":
            stock_to_sell = await collection.find_one({"status": "bought"})

            if stock_to_sell:
                stock_to_sell = serialize_document(stock_to_sell)  # Serialize the document
            else:
                logging.warning("No stocks to sell.")
                return
            current_price = float(get_current_price(stock_to_sell['symbol']))
            request_payload = create_order_payload(stock_to_sell, stock_to_sell["quantity"], current_price, "sell")

        else:
            logging.error(f"Invalid action: {action}")
            return

        # Place test order
        await handle_successful_order(request_payload, action, collection)

    except Exception as e:
        logging.error(f"Failed to {action} stock: {str(e)}")


def create_order_payload(stock, quantity, price, transaction_type):
    """
    Create an order payload for Dhan Client.

    :param stock: Stock data.
    :param quantity: Quantity to buy/sell.
    :param price: Price per unit.
    :param transaction_type: BUY or SELL action.
    :return: Order payload dictionary.
    """
    return {
        "tag": stock["id"],
        "security_id": str(stock["security_id"]),
        "exchange_segment": "NSE",
        "transaction_type": transaction_type,
        "quantity": quantity,
        "order_type": "MARKET",
        "product_type": "CNC",
        "price": price,
    }


async def handle_successful_order(request_payload, action, collection):
    """
    Handle the response of a successful order.

    :param response: Order response from Dhan Client.
    :param request_payload: The payload used for the order.
    :param action: The action performed ("buy" or "sell").
    :param collection: MongoDB collection.
    """
    executed_order = {
        "orderId": request_payload["tag"],
        "correlationId": request_payload["tag"],
        "request_payload": request_payload,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    logging.info(f"Test order executed: {executed_order}")

    stock_status = "bought" if action == "buy" else "sold"
    update_fields = {
        "status": stock_status,
        "quantity": request_payload["quantity"],
        "state": "active" if stock_status == "bought" else "inactive",
    }
    if action == "buy":
        update_fields["buy_price"] = request_payload["price"]
    elif action == "sell":
        update_fields["sell_price"] = request_payload["price"]

    await collection.update_one({"id": request_payload["tag"]}, {"$set": update_fields})
