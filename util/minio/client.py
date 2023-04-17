from dotenv import load_dotenv
import os
from minio import Minio

# Load environment variables from .env file
load_dotenv()

# Initialize Minio client
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE") == "True",
)


def get_minio_client():
    return minio_client
