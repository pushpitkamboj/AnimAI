from fastapi import FastAPI
app = FastAPI()

from pydantic import BaseModel
from agent.graph import workflow_app
from langgraph.errors import GraphRecursionError
from fastapi.responses import JSONResponse


class InstructionInput(BaseModel):
    prompt: str

@app.post("/run")
async def run_langgraph(data: InstructionInput):

    try:
        result = await workflow_app.ainvoke(
            input={"prompt": data.prompt},
            config = {"configurable": {"thread_id": "traveler_456"}, "recursion_limit": 8}
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