from pymongo import MongoClient, errors
from pymongo.collection import Collection


# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "mydatabase"

# Global variables
client = None
db = None
students_collection: Collection = None
facial_data_collection: Collection = None
exeats_collection: Collection = None
sign_outs_collection: Collection = None

try:
    # Establish connection to MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Forces a call to check connection
    
    db = client[DB_NAME]
    print("✅ Successfully connected to MongoDB.")

    # Initialize collections
    students_collection = db["students"]
    facial_data_collection = db["facialData"]
    exeats_collection = db["exeats"]
    sign_outs_collection = db["signOuts"]

except errors.ServerSelectionTimeoutError as err:
    print("❌ Failed to connect to MongoDB:", err)
    db = None
