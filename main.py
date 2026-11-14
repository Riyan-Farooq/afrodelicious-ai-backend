
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal

from crew import create_crew


app = FastAPI(
    title="Afrodelicious AI API",
    description="API for Brendy, SAM and Recipe Collector",
    version="1.0.0"
)


# Allow the local frontend and deployed Afrodelicious website
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://afrokr-yol-kitchen.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    agent_type: Literal["marketing", "development", "recipe"]
    user_request: str = Field(min_length=1)
    recipe_url: Optional[str] = None


@app.get("/")
def home():
    return {
        "success": True,
        "message": "Afrodelicious AI API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/api/agent")
def run_agent(request: AgentRequest):

    try:
        crew = create_crew(
            task_type=request.agent_type,
            user_request=request.user_request,
            recipe_url=request.recipe_url
        )

        result = crew.kickoff()

        return {
            "success": True,
            "selected_agent": request.agent_type,
            "result": str(result)
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
