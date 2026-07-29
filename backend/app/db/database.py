from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient = None


async def connect_db():
    global _client
    _client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=10000,
    )
    await _client.admin.command("ping")
    print(f"Connected to MongoDB Atlas: {settings.MONGODB_DB_NAME}")


async def disconnect_db():
    global _client
    if _client:
        _client.close()
        print("Disconnected from MongoDB")


def get_db() -> AsyncIOMotorDatabase:
    return _client[settings.MONGODB_DB_NAME]
