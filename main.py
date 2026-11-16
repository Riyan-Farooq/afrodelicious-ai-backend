
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Literal

from crew import create_crew


load_dotenv()

app = FastAPI(
    title="Afrodelicious AI API",
    description="API for Brendy, SAM and Recipe Collector",
    version="1.2.0"
)

security = HTTPBearer(auto_error=False)


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


def verify_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    )

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=503,
            detail="Backend authentication is not configured."
        )

    base_url = supabase_url.rstrip("/")

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {credentials.credentials}"
    }

    try:
        # Verify the access token with Supabase Auth.
        auth_response = httpx.get(
            f"{base_url}/auth/v1/user",
            headers=headers,
            timeout=15.0
        )

        if auth_response.status_code in (401, 403):
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session."
            )

        if auth_response.status_code != 200:
            raise HTTPException(
                status_code=503,
                detail="Unable to verify authentication."
            )

        user_data = auth_response.json()
        user_id = user_data.get("id")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid user session."
            )

        # Verify that this user is an administrator.
        role_response = httpx.get(
            f"{base_url}/rest/v1/user_roles",
            headers=headers,
            params={
                "user_id": f"eq.{user_id}",
                "select": "role"
            },
            timeout=15.0
        )

        if role_response.status_code != 200:
            raise HTTPException(
                status_code=503,
                detail="Unable to verify user permissions."
            )

        roles = role_response.json()

        if not roles or roles[0].get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Administrator access required."
            )

        # Keep the verified token for the configuration request.
        return {
            "user_id": user_id,
            "access_token": credentials.credentials,
            "supabase_url": base_url,
            "supabase_key": supabase_key
        }

    except HTTPException:
        raise

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Supabase authentication service is unavailable."
        )

    except (ValueError, KeyError):
        raise HTTPException(
            status_code=503,
            detail="Unable to verify user permissions."
        )


def get_agent_config(agent_key, admin_context):

    headers = {
        "apikey": admin_context["supabase_key"],
        "Authorization": f"Bearer {admin_context['access_token']}"
    }

    try:
        response = httpx.get(
            f"{admin_context['supabase_url']}/rest/v1/agent_configs",
            headers=headers,
            params={
                "agent_key": f"eq.{agent_key}",
                "select": "*"
            },
            timeout=15.0
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=503,
                detail="Unable to load the saved agent configuration."
            )

        configs = response.json()

        if not configs:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This agent has no saved configuration. "
                    "Open the Admin AI Agents panel and save its configuration first."
                )
            )

        config = configs[0]

        if not config.get("enabled", True):
            raise HTTPException(
                status_code=403,
                detail="This AI agent is currently disabled."
            )

        return config

    except HTTPException:
        raise

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to the configuration service."
        )


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
def run_agent(
    request: AgentRequest,
    admin_context: dict = Depends(verify_admin)
):
    # Load the saved configuration for the requested agent.
    agent_config = get_agent_config(
        request.agent_type,
        admin_context
    )

    try:
        crew = create_crew(
            task_type=request.agent_type,
            user_request=request.user_request,
            recipe_url=request.recipe_url,
            agent_config=agent_config
        )

        result = crew.kickoff()

        return {
            "success": True,
            "selected_agent": request.agent_type,
            "agent_name": agent_config.get("display_name"),
            "result": str(result)
        }

    except HTTPException:
        raise

    except Exception as error:
        import traceback

        print(
            f"AI AGENT REQUEST FAILED: {repr(error)}",
            flush=True
        )
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="The AI agent could not complete the request."
        )