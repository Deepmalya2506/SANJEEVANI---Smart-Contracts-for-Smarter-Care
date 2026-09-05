from pymongo import MongoClient
from app.core.config import settings
import psycopg

client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
db = client[settings.DB_NAME]

hospital_collection = db["hospitals"]
inventory_collection = db["inventory"]


def get_supabase_connection():
	return psycopg.connect(
		host=settings.SUPABASE_HOST,
		port=settings.SUPABASE_PORT,
		dbname=settings.SUPABASE_DATABASE,
		user=settings.SUPABASE_USER,
		password=settings.SUPABASE_PASSWORD,
		sslmode="require",
	)