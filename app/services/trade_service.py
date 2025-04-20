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
COLLECTION_NAME = "stock_data"
dhan_client = get_dhan_client()


def serialize_document(doc):
    """
    Serialize a MongoDB document to ensure JSON compatibility.
    Converts ObjectId to string.
    """
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def execute_trade(action):
    """
    Execute a stock trade (buy or sell).

    :param action: "buy" or "sell".
    """
    try:
        logging.info(f"{action.capitalize()}ing stock at: {datetime.now()}")

        # MongoDB client
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        if action == "buy":
            today_date = datetime.now().strftime("%Y-%m-%d")
            today_stock = await collection.find_one({"date": today_date, "status": "scanned"})

            if today_stock:
                today_stock = serialize_document(today_stock)  # Serialize the document
            else:
                logging.warning("No stock data available for today.")
                return

            current_price = float(get_current_price(today_stock["symbol"]))
            fund_details = dhan_client.get_fund_limits()

            if fund_details["status"] != "success":
                logging.error(fund_details["remarks"].get('error_message', 'Unknown error'))
                return

            balance = float(fund_details["data"]["availabelBalance"]) - 500
            if balance > 80000:
                balance /= 2

            quantity = int(balance / current_price)
            request_payload = create_order_payload(today_stock, quantity, current_price, dhan_client.BUY)

        elif action == "sell":
            stock_to_sell = await collection.find_one({"status": "bought"})

            if stock_to_sell:
                stock_to_sell = serialize_document(stock_to_sell)  # Serialize the document
            else:
                logging.warning("No stocks to sell.")
                return

            request_payload = create_order_payload(stock_to_sell, stock_to_sell["quantity"], 0, dhan_client.SELL)

        else:
            logging.error(f"Invalid action: {action}")
            return

        # Place order
        response = dhan_client.place_order(**request_payload)
        if response["status"] == "success":
            await handle_successful_order(response, request_payload, action, collection)
        else:
            logging.error(f"Order placement failed: {response}")

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
        "exchange_segment": dhan_client.NSE,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "order_type": dhan_client.MARKET,
        "product_type": dhan_client.CNC,
        "price": price,
    }


async def handle_successful_order(response, request_payload, action, collection):
    """
    Handle the response of a successful order.

    :param response: Order response from Dhan Client.
    :param request_payload: The payload used for the order.
    :param action: The action performed ("buy" or "sell").
    :param collection: MongoDB collection.
    """
    executed_order = {
        "orderId": response["data"]["orderId"],
        "correlationId": request_payload["tag"],
        "request_payload": request_payload,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    logging.info(f"Order executed: {executed_order}")
    order_details = dhan_client.get_order_by_id(response["data"]["orderId"])

    stock_status = "bought" if action == "buy" else "sold"
    update_fields = {
        "status": stock_status,
        "quantity": request_payload["quantity"],
        "state": "active" if stock_status == "bought" else "inactive",
    }
    if action == "buy":
        update_fields["buy_price"] = order_details["data"][0]["averageTradedPrice"]
    elif action == "sell":
        update_fields["sell_price"] = order_details["data"][0]["averageTradedPrice"]

    await collection.update_one({"id": request_payload["tag"]}, {"$set": update_fields})
