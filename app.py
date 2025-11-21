import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Load .env variables if any
load_dotenv()

# Directory containing this file (server.py is at root level)
BASE_DIR = Path(__file__).parent
AGENT_DIR = BASE_DIR / "agent"  # Point to the agent subdirectory

# Create FastAPI app with ADK integration
app_args = {
    "agents_dir": str(AGENT_DIR),   # ADK will auto-load agent.py
    "web": True                      # Enables the built-in ADK playground UI
}
app: FastAPI = get_fast_api_app(**app_args)

# Optional metadata
app.title = "Executive Decision Workflow - ADK"
app.description = "Multi-agent workflow orchestrated via ADK"
app.version = "1.0.0"

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "executive-decision-workflow"}

@app.get("/")
def root():
    return {
        "service": "Executive Decision Workflow",
        "description": "ADK multi-agent executive system",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
