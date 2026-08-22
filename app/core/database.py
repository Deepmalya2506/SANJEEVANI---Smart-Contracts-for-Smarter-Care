from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
db = client[settings.DB_NAME]

hospital_collection = db["hospitals"]
inventory_collection = db["inventory"]