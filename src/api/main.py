# from fastapi import FastAPI
# app = FastAPI()

# from pydantic import BaseModel
# from agent.graph import workflow_app
# from langgraph.errors import GraphRecursionError
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # or specific frontend URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



# class InstructionInput(BaseModel):
#     prompt: str

# @app.post("/run")
# async def run_langgraph(data: InstructionInput):

#     try:
#         result = await workflow_app.ainvoke(
#             input={"prompt": data.prompt},
#             config = {"configurable": {"thread_id": "traveler_456"}, "recursion_limit": 8}
#         )
#         return JSONResponse(
#             status_code=200, 
#             content={
#                 "result": result["video_url"],
#                 "status": "success"
#             }
#         )
        
#     except GraphRecursionError:
#         return JSONResponse(
#             status_code=422,
#             content={
#                 "result": "That was too difficult to process for me, give me something easier :)",
#                 "status": "error",
#             }
#         )
        
#     except Exception as e:
#         print(f"Unexpected error: {e}") 
#         return JSONResponse(
#             status_code=500,
#             content={
#                 "result": "An unexpected server error occurred. Please try again later.",
#                 "status": "error"
#             }
#         )
        

# @app.get("/health")
# def health():
#     return {"message": "ok"}






import asyncio
import uuid
from typing import Dict, Any, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Assuming these are available in your environment
from agent.graph import workflow_app 
from langgraph.errors import GraphRecursionError 

app = FastAPI()

# --- In-Memory Task Storage ---
# Stores the status and result for each long-running task.
# Key: str (task_id UUID)
# Value: Dict[str, Any] (e.g., {"status": "SUCCESS", "result": "..."})
TASK_RESULTS: Dict[str, Any] = {}
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InstructionInput(BaseModel):
    prompt: str


# --- Core Logic: The long-running task definition ---

def _sync_run_workflow(task_id: str, prompt: str):
    """
    Executes the synchronous or asynchronous LangGraph workflow off the main event loop.
    This function will be run in a separate thread.
    """
    
    # Update status to STARTED
    TASK_RESULTS[task_id]["status"] = "STARTED"
    
    try:
        # Since workflow_app.ainvoke is async, we use asyncio.run 
        # to execute it within this thread's event loop.
        # Alternatively, if ainvoke were sync, we would just call it directly.
        
        # NOTE: Using thread_id="traveler_456" fixes the thread for this demo.
        # In a real app, you might want to derive this from the task_id or user session.
        thread_id =     task_id = str(uuid.uuid4())
        result = asyncio.run(workflow_app.ainvoke(
            input={"prompt": prompt},
            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 8}
        ))
        
        # Success: Update state and store result
        TASK_RESULTS[task_id]["status"] = "SUCCESS"
        TASK_RESULTS[task_id]["result"] = result["video_url"]
        
    except GraphRecursionError:
        # Handle specific LangGraph errors
        TASK_RESULTS[task_id]["status"] = "FAILURE"
        TASK_RESULTS[task_id]["error"] = "That was too difficult to process for me, give me something easier :)"
        
    except Exception as e:
        # Handle all other exceptions
        print(f"Task {task_id} failed with unexpected error: {e}")
        TASK_RESULTS[task_id]["status"] = "FAILURE"
        TASK_RESULTS[task_id]["error"] = f"An unexpected server error occurred: {str(e)}"


# --- ENDPOINT 1: Trigger LangGraph Task ---

@app.post("/run-task")
async def run_langgraph_task(data: InstructionInput):
    """
    Triggers the long-running LangGraph execution in a separate thread.
    Returns the task ID immediately for polling.
    """
    task_id = str(uuid.uuid4())
    
    # Set initial state in the in-memory dictionary
    TASK_RESULTS[task_id] = {
        "status": "QUEUED",
        "result": None,
        "error": None
    }
    
    # Crucial step: Start the background task without blocking the main event loop.
    # asyncio.to_thread runs the synchronous function (_sync_run_workflow) in a separate OS thread.
    # asyncio.create_task ensures the overall FastAPI endpoint returns immediately.
    asyncio.create_task(
        asyncio.to_thread(_sync_run_workflow, task_id, data.prompt)
    )
    
    # Return 202 Accepted style response immediately
    return JSONResponse(
        status_code=202, 
        content={
            "task_id": task_id,
            "status": "QUEUED",
            "message": f"Task submitted. Use /status/{task_id} to poll for result."
        }
    )

# --- ENDPOINT 2: Poll for Status and Result ---

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Checks the status of a specific in-memory task ID and returns the result if complete.
    """
    if task_id not in TASK_RESULTS:
        raise HTTPException(status_code=404, detail="Task ID not found.")
        
    task_info = TASK_RESULTS[task_id]
    current_status = task_info["status"]
    
    # 1. Task is still running (or queued)
    if current_status in ["QUEUED", "STARTED"]:
        return {
            "task_id": task_id,
            "status": current_status,
            "result": None,
            "message": "Processing..."
        }
    
    # 2. Task completed successfully
    elif current_status == "SUCCESS":
        # Optionally, you can delete the result after retrieval to save memory
        # del TASK_RESULTS[task_id]
        
        return JSONResponse(
            status_code=200,
            content={
                "task_id": task_id,
                "status": "SUCCESS",
                "result": task_info["result"] # This is the final video_url
            }
        )
        
    # 3. Task failed
    elif current_status == "FAILURE":
        # Optionally, you can delete the result after retrieval to save memory
        # del TASK_RESULTS[task_id]
        
        return JSONResponse(
            status_code=500, # Use 500 or 422 depending on the error type
            content={
                "task_id": task_id,
                "status": "FAILURE",
                "result": task_info["error"],
            }
        )
        
# --- Health Check (Unmodified) ---

@app.get("/health")
def health():
    return {"message": "ok"}
