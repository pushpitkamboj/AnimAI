# MIGRATED TO LANGGRAPH API FOR DEPLOYEMENT
from dotenv import load_dotenv
load_dotenv()
import os

from fastapi import FastAPI
app = FastAPI()

import chromadb
from pydantic import BaseModel
from agent.graph import workflow_app
from langgraph.errors import GraphRecursionError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("CHROMA_API_KEY")
database = os.getenv("CHROMA_DATABASE")
tenant = os.getenv("CHROMA_TENANT")

client = chromadb.CloudClient(
    api_key=api_key, database=database, tenant=tenant
)

THRESHOLD = 1 - 0.3 #BECAUSE WE ARE COMPARING THE DISTANCES

class InstructionInput(BaseModel):
    prompt: str

@app.post("/run")
async def run_langgraph(data: InstructionInput):

    try:
        collection = client.get_collection(name="manim_cached_video_url")
        cached_result = collection.query(query_texts=[data.prompt], n_results=1)
        print(f"caches results from chromaDB include- {cached_result}")
        if cached_result["distances"][0][0] <= THRESHOLD:
            print("the threshold is fine")
            return JSONResponse(
                status_code=200,
                content={
                    "result": cached_result["metadatas"][0][0]["video_url"],
                    "status": "success",
                }
            )
            
        thread_id = str(uuid.uuid4())
        result = await workflow_app.ainvoke(
            input={"prompt": data.prompt},
            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 18}
        )
        
        print("not found in cached data, now caching")
        data_cached = collection.add(
            ids=str(uuid.uuid4()),
            documents=data.prompt,
            metadatas=[{"video_url": result["video_url"]}],
        )

        return JSONResponse(
            status_code=200, 
            content={
                "result": result["video_url"],
                "status": "success"
            }
        )
        
    except GraphRecursionError:
        return JSONResponse(
            status_code=422,
            content={
                "result": "That was too difficult to process for me, give me something easier :)",
                "status": "error",
            }
        )
        
    except Exception as e:
        print(f"Unexpected error: {e}") 
        return JSONResponse(
            status_code=500,
            content={
                "result": "An unexpected server error occurred. Please try again later.",
                "status": "error"
            }
        )
        

@app.get("/health")
def health():
    return {"message": "ok"}