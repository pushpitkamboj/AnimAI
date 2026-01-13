# MIGRATED TO LANGGRAPH API FOR DEPLOYEMENT
from dotenv import load_dotenv
load_dotenv()
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the src directory to Python path to resolve the correct agent module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

THRESHOLD = 1 - 0.2 #BECAUSE WE ARE COMPARING THE DISTANCES

class InstructionInput(BaseModel):
    prompt: str

@app.post("/run")
async def run_langgraph(data: InstructionInput):
    logger.info(f"Received request with prompt: {data.prompt}")
    
    try:
        collection = client.get_collection(name="manim_cached_video_url")
        cached_result = collection.query(query_texts=[data.prompt], n_results=1)
        logger.debug(f'Cached results from ChromaDB: {cached_result["metadatas"][0][0]["video_url"]}')
        if cached_result["distances"][0][0] <= THRESHOLD:
            logger.info("Cache hit - returning cached video URL")
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
        
        if result["animation"] == False:
            logger.info(f"Non-animation response generated")
            return {
                "result": result["non_animation_reply"],
                "status": "success"
            }
            
        logger.info("Cache miss - caching new video URL")
        data_cached = collection.add(
            ids=str(uuid.uuid4()),
            documents=data.prompt,
            metadatas=[{"video_url": result["video_url"]}],
        )

        logger.info(f"Response: video_url={result['video_url']}")
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
    logger.info("okay")
    return {"message": "ok"}