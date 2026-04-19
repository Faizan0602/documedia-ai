from motor.motor_asyncio import AsyncIOMotorClient
import os

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()


async def connect_to_mongo():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")

    db.client = AsyncIOMotorClient(mongo_uri)

    
    db.db = db.client["ai_qa_db"]


async def close_mongo_connection():
    if db.client:
        db.client.close()