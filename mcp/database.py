from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")

db = client["sanjeevani"]

hospital_collection = db["hospitals"]
equipment_type_collection = db["equipment_types"]
equipment_collection = db["equipment_assets"]
transaction_collection = db["inventory_transactions"]