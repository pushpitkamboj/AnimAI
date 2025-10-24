import asyncio
import uuid
from typing import Dict, Any, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.graph import workflow_app 
from langgraph.errors import GraphRecursionError 

app = FastAPI()
TASK_RESULTS: Dict[str, Any] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InstructionInput(BaseModel):
    prompt: str

#separate worker thread managed by thread pool exec.
def _sync_run_workflow(task_id: str, prompt: str):
    """
    Executes the synchronous or asynchronous LangGraph workflow off the main event loop.
    This function will be run in a separate thread.
    """
    
    TASK_RESULTS[task_id]["status"] = "STARTED"
    
    try:
        thread_id =     task_id = str(uuid.uuid4())
        result = asyncio.run(workflow_app.ainvoke( #a non blocking event loop is created to execute async graph (whose lifetime exist only inide the particular thread)
            input={"prompt": prompt},
            config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 8}
        ))
        
        TASK_RESULTS[task_id]["status"] = "SUCCESS"
        TASK_RESULTS[task_id]["result"] = result["video_url"]
        
    except GraphRecursionError:
        TASK_RESULTS[task_id]["status"] = "FAILURE"
        TASK_RESULTS[task_id]["error"] = "That was too difficult to process for me, give me something easier :)"
        
    except Exception as e:
        print(f"Task {task_id} failed with unexpected error: {e}")
        TASK_RESULTS[task_id]["status"] = "FAILURE"
        TASK_RESULTS[task_id]["error"] = f"An unexpected server error occurred: {str(e)}"


@app.post("/run-task")
async def run_langgraph_task(data: InstructionInput):
    """
    Triggers the long-running LangGraph execution in a separate thread.
    Returns the task ID immediately for polling.
    """
    task_id = str(uuid.uuid4())
    
    #initial state in the in-memory dictionary
    TASK_RESULTS[task_id] = {
        "status": "QUEUED",
        "result": None,
        "error": None
    }
    
    #separate threads created for graph exec. and is managed by thread pool executor. 
    asyncio.create_task(
        asyncio.to_thread(_sync_run_workflow, task_id, data.prompt)
    )
    
    return JSONResponse(
        status_code=202, 
        content={
            "task_id": task_id,
            "status": "QUEUED",
            "message": f"Task submitted. Use /status/{task_id} to poll for result."
        }
    )

#ENDPOINT 2: Poll for Status and Result
@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Checks the status of a specific in-memory task ID and returns the result if complete.
    """
    if task_id not in TASK_RESULTS:
        raise HTTPException(status_code=404, detail="Task ID not found.")
        
    task_info = TASK_RESULTS[task_id]
    current_status = task_info["status"]
    
    if current_status in ["QUEUED", "STARTED"]:
        return {
            "task_id": task_id,
            "status": current_status,
            "result": None,
            "message": "Processing..."
        }
    
    elif current_status == "SUCCESS":
        return JSONResponse(
            status_code=200,
            content={
                "task_id": task_id,
                "status": "SUCCESS",
                "result": task_info["result"]
            }
        )
        
    elif current_status == "FAILURE":
        return JSONResponse(
            status_code=500, # Use 500 or 422 depending on the error type
            content={
                "task_id": task_id,
                "status": "FAILURE",
                "result": task_info["error"],
            }
        )
        
@app.get("/health")
def health():
    return {"message": "ok"}
