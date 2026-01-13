import chromadb
import os 

api_key = os.getenv("CHROMA_API_KEY")
database = os.getenv("CHROMA_DATABASE")
tenant = os.getenv("CHROMA_TENANT")

client = chromadb.CloudClient(
    api_key=api_key, database=database, tenant=tenant
)


def invalidate_data(prompt: str, n=1):
    """Delete cached entries matching the given prompt."""
    collection = client.get_collection(name="manim_cached_video_url")
    cached_result = collection.query(query_texts=[prompt], n_results=n)
    
    if cached_result["ids"] and cached_result["ids"][0]:
        ids_to_delete = cached_result["ids"][0]
        collection.delete(ids=ids_to_delete)
        print(f"Deleted {len(ids_to_delete)} cache entries: {ids_to_delete}")
    else:
        print("No matching cache entries found")


def invalidate_all():
    """Delete all cached entries."""
    collection = client.get_collection(name="manim_cached_video_url")
    all_data = collection.get()
    
    if all_data["ids"]:
        collection.delete(ids=all_data["ids"])
        print(f"Deleted all {len(all_data['ids'])} cache entries")
    else:
        print("Cache is already empty")


if __name__ == "__main__":
    invalidate_data("draw a square", 1)
    