import os
import requests
import uuid
from moviepy.editor import VideoFileClip
from llm_planner import generate_broll_plan
import whisper
import asyncio

# Preload whisper model
print("Loading Whisper model (medium)...")
whisper_model = whisper.load_model("medium")
print("Whisper model loaded.")

TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

async def download_file(url, filename):
    response = requests.get(url, stream=True)
    path = os.path.join(TEMP_DIR, filename)
    with open(path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return path

async def process_video_pipeline(a_roll, b_rolls):
    # 1. Download A-roll
    a_roll_path = await download_file(a_roll.url, f"a_roll_{uuid.uuid4()}.mp4")
    
    try:
        # 2. Extract info
        clip = VideoFileClip(a_roll_path)
        duration = clip.duration
        audio_path = os.path.join(TEMP_DIR, f"audio_{uuid.uuid4()}.mp3")
        clip.audio.write_audiofile(audio_path, logger=None)
        clip.close()

        # 3. Transcribe
        loop = asyncio.get_event_loop()
        # Run synchronous whisper transcribe in thread pool
        result = await loop.run_in_executor(None, lambda: whisper_model.transcribe(audio_path))
        
        segments = result["segments"]
        # Format segments to match what we expect (start, end, text)
        segments = [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in segments]

        # 4. Generate Plan
        # We pass the segments, total duration, and b-roll metadata to the LLM
        plan = await generate_broll_plan(segments, duration, b_rolls, a_roll.metadata)
        
        # Cleanup audio
        os.remove(audio_path)
        
        return plan, duration, segments
        
    finally:
        # We might want to keep a_roll for rendering later, but for now let's clean up if we were just planning
        # But wait, if we want to render, we'd need to download again or cache. 
        # For this logic, let's assume we re-download for rendering to keep state simple.
        if os.path.exists(a_roll_path):
            os.remove(a_roll_path)

