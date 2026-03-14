import os
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import asyncio
from pydantic import BaseModel

# SETUP
app = FastAPI(title="Agent 6: Banana AI Banner Generator API")

# Path discovery
STATIC_DIR = Path(__file__).parent / "static"
try:
    STATIC_DIR.mkdir(exist_ok=True)
except Exception:
    pass

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

@app.get("/")
async def read_root():
    return {"message": "Agent 6 API is running. Go to /agent6 to view UI."}

@app.get("/agent6")
async def read_agent6():
    return FileResponse(STATIC_DIR / "agent6.html")

# Serves generated images and static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ============================================================
# AGENT 6: BANANA AI BANNER GENERATOR ENDPOINTS
# ============================================================
from agent6_banner_generator import load_persona, load_plevel_matrix, PERSONA_NAMES, get_banner_agent

@app.get("/api/agent6/plevel-matrix")
async def agent6_plevel_matrix(persona_id: int = Query(...)):
    persona = load_persona(persona_id)
    if "error" in persona:
        raise HTTPException(status_code=404, detail=persona["error"])
    segment = PERSONA_NAMES.get(persona_id, {}).get("segment", 12)
    matrix = load_plevel_matrix(segment)
    return {
        "persona": {
            "id": persona_id,
            "name": persona.get("name", ""),
            "icon": persona.get("icon", ""),
            "desc": persona.get("desc", ""),
            "segment": segment,
            "pains": persona.get("pains", []),
            "key_messages": persona.get("key_messages", []),
        },
        "matrix": matrix
    }

class Agent6IdeaRequest(BaseModel):
    persona_id: int
    plevel_code: str
    plevel_thought: str
    plevel_stage: str

@app.post("/api/agent6/generate-ideas")
async def agent6_generate_ideas(req: Agent6IdeaRequest):
    persona = load_persona(req.persona_id)
    if "error" in persona:
        raise HTTPException(status_code=404, detail=persona["error"])
    agent = get_banner_agent()
    ideas = agent.generate_ideas(persona, req.plevel_code, req.plevel_thought, req.plevel_stage)
    return {"ideas": ideas}

class Agent6ImageRequest(BaseModel):
    persona_id: int
    idea: Dict[str, Any]

@app.post("/api/agent6/generate-image")
async def agent6_generate_image(req: Agent6ImageRequest):
    persona = load_persona(req.persona_id)
    agent = get_banner_agent()
    prompt = agent.build_image_prompt(req.idea, persona)
    try:
        image_url = await asyncio.to_thread(agent.generate_image, prompt)
    except Exception as e:
        print(f"[Agent6] Image generation failed: {e}")
        image_url = None
    return {
        "prompt": prompt,
        "image_url": image_url,
        "idea": req.idea
    }

@app.post("/api/agent6/auto-bridge")
async def agent6_auto_bridge(request: Request):
    try:
        req = await request.json()
        bridge_file = Path(__file__).resolve().parent / "agent6_bridge.json"
        with open(bridge_file, 'w', encoding='utf-8') as f:
            json.dump(req, f, indent=2, ensure_ascii=False)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
