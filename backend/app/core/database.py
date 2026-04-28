
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    db = None


db = Database()


async def connect_to_mongo():
    mongo_uri = os.getenv("MONGO_URI")

    #  STOP if not set (no fallback)
    if not mongo_uri:
        raise ValueError(" MONGO_URI is not set in environment variables")

    print(" Connecting to MongoDB...")
    print("MONGO_URI:", mongo_uri[:30], "...")  # safe debug

    db.client = AsyncIOMotorClient(mongo_uri)
    db.db = db.client["ai_qa_db"]


async def close_mongo_connection():
    if db.client:
        db.client.close()

