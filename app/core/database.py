from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Initialize MongoDB client
client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client["portfolio"]


async def connect_to_db():
    try:
        # Ping the MongoDB server
        await client.admin.command("ping")
        print("MongoDB connected successfully!")
        return "Connected"
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return str(e)
