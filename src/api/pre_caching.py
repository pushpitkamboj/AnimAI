from dotenv import load_dotenv
load_dotenv()
import os
import chromadb
import uuid

api_key = os.getenv("CHROMA_API_KEY")
database = os.getenv("CHROMA_DATABASE")
tenant = os.getenv("CHROMA_TENANT")

client = chromadb.CloudClient(
    api_key=api_key, database=database, tenant=tenant
)
print("connection established")
collection = client.get_collection(name="manim_cached_video_url")
response = collection.add(
    ids=str(uuid.uuid4()),
    documents=["explain binary search"],
    metadatas=[{"video_url": "https://pub-b215a097b7b243dc86da838a88d50339.r2.dev/media/videos/BinarySearchTutorial/480p15/BinarySearchTutorial.mp4"}],
)


print(f"collection added:{response}")
