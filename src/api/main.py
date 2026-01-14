# MIGRATED TO LANGGRAPH API FOR DEPLOYEMENT
from dotenv import load_dotenv
load_dotenv()
import os
import sys
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import chromadb
from pydantic import BaseModel
from agent.graph import workflow_app
from langgraph.errors import GraphRecursionError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid 
from fastapi import FastAPI, Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the src directory to Python path to resolve the correct agent module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
)

print(f"allowed origins are: {ALLOWED_ORIGINS}")
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
@limiter.limit("10/minute")
async def run_langgraph(request: Request, data: InstructionInput):
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
                "status": "non_animation"
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