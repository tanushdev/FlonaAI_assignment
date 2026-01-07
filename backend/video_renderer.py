import os
import requests
import uuid
from moviepy.editor import VideoFileClip, CompositeVideoClip
from tenacity import retry, stop_after_attempt

TEMP_DIR = "temp_files"
OUTPUT_DIR = "output_files"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@retry(stop=stop_after_attempt(3))
def download_file_sync(url, filename):
    response = requests.get(url, stream=True)
    path = os.path.join(TEMP_DIR, filename)
    with open(path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return path

async def render_final_video(a_roll_url, b_rolls, insertions):
    # 1. Download A-roll
    a_roll_path = download_file_sync(a_roll_url, f"a_roll_render_{uuid.uuid4()}.mp4")
    
    # 2. Download B-rolls needed
    b_roll_map = {b.id: b.url for b in b_rolls}
    downloaded_brolls = {}
    
    # Only download used b-rolls
    used_ids = set(ins.broll_id for ins in insertions)
    for bid in used_ids:
        if bid in b_roll_map:
            path = download_file_sync(b_roll_map[bid], f"{bid}_{uuid.uuid4()}.mp4")
            downloaded_brolls[bid] = path
            
    # 3. Process with MoviePy
    a_roll_clip = VideoFileClip(a_roll_path)
    final_clips = [a_roll_clip]
    
    for ins in insertions:
        if ins.broll_id in downloaded_brolls:
            b_path = downloaded_brolls[ins.broll_id]
            b_clip = VideoFileClip(b_path)
            
            # Resize B-roll to match A-roll (assume same aspect ratio or fill)
            # Just resize to A-roll size to be safe
            b_clip = b_clip.resize(newsize=a_roll_clip.size)
            
            # Loop b-roll if shorter than duration, or subclip
            if b_clip.duration < ins.duration_sec:
                # Loop it? Or just fit. Let's loop.
                b_clip = b_clip.loop(duration=ins.duration_sec)
            else:
                b_clip = b_clip.subclip(0, ins.duration_sec)
                
            b_clip = b_clip.set_start(ins.start_sec).set_duration(ins.duration_sec)
            
            # Crossfade? Prompt doesn't specify, but strict cut is easier and requested "correctness over polish"
            final_clips.append(b_clip)
            
    final_video = CompositeVideoClip(final_clips)
    
    output_filename = f"final_{uuid.uuid4()}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Write file
    # use fast preset for speed
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
    
    # Cleanup
    a_roll_clip.close()
    final_video.close()
    
    # Depending on implementation, we might want to delete temp files here
    # For now, let's leave them or user can clean up manually
    
    return output_path
