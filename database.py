from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from beanie import init_beanie, PydanticObjectId as ObjectId
from pymongo.errors import ServerSelectionTimeoutError
from models.student_model import Student

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "mydatabase"

async def init_db():
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        await client.server_info()
        
        db = client[DB_NAME]
        await init_beanie(database=db, document_models=[Student])
        grid_fs_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="profile_images")

        print("✅ Database initialized successfully")
        # return client, db, grid_fs_bucket
        return grid_fs_bucket

    except ServerSelectionTimeoutError as err:
        print(f"❌ Failed to connect to MongoDB: {err}")
        return None

# async def save_image_to_gridfs(image_bytes: bytes, filename: str) -> ObjectId:
#     if grid_fs_bucket is None:
#         raise Exception("GridFSBucket not initialized. Call init_db() first.")
#     file_id = await grid_fs_bucket.upload_from_stream(filename, image_bytes)
#     return file_id
