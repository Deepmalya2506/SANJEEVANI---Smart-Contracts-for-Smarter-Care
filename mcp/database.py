from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"

client = AsyncIOMotorClient(MONGO_URL)

db = client["sanjeevani"]

hospitals_collection = db["hospitals"]
equipment_collection = db["equipment"]
transactions_collection = db["transactions"]