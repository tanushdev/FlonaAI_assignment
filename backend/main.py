from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from video_processor import process_video_pipeline
from video_renderer import render_final_video
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount output directory strictly for serving generated videos
os.makedirs("output_files", exist_ok=True)
app.mount("/output", StaticFiles(directory="output_files"), name="output")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BRoll(BaseModel):
    id: str
    metadata: str
    url: str

class ARoll(BaseModel):
    url: str
    metadata: str

class VideoRequest(BaseModel):
    a_roll: ARoll
    b_rolls: List[BRoll]

class Insertion(BaseModel):
    start_sec: float
    duration_sec: float
    broll_id: str
    confidence: float
    reason: str

class PlanResponse(BaseModel):
    insertions: List[Insertion]
    a_roll_duration: float
    transcript_segments: List[dict]

@app.post("/generate-plan", response_model=PlanResponse)
async def generate_plan(request: VideoRequest):
    try:
        plan, duration, transcript = await process_video_pipeline(request.a_roll, request.b_rolls)
        return PlanResponse(
            insertions=plan,
            a_roll_duration=duration,
            transcript_segments=transcript
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RenderRequest(BaseModel):
    a_roll_url: str
    b_rolls: List[BRoll]
    insertions: List[Insertion]

@app.post("/render-video")
async def render_video(request: RenderRequest):
    try:
        output_path = await render_final_video(request.a_roll_url, request.b_rolls, request.insertions)
        return {"video_path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
