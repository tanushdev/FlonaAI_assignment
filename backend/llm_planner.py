from openai import AsyncOpenAI
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI / OpenRouter Setup
if PROVIDER != "gemini":
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else None
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

# Gemini Setup
if PROVIDER == "gemini":
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_broll_plan(segments, duration, b_rolls, a_roll_context):
    # Format inputs as JSON for the prompt
    b_roll_json = json.dumps([{"broll_id": b.id, "description": b.metadata} for b in b_rolls], indent=2)
    transcript_json = json.dumps(
        [{"start_sec": s["start"], "end_sec": s["end"], "text": s["text"]} for s in segments], 
        indent=2
    )

    system_prompt = f"""
You are an expert video editor and multimodal reasoning system.

Your task is to intelligently plan B-roll insertions for a short-form UGC (user-generated content) video.

You will be given:
1. A timestamped transcript of an A-roll video (talking-head video)
2. A list of B-roll clips, each with a short textual description of what the clip visually contains
3. The total duration of the A-roll video

Your goal is to decide:
- Which moments in the A-roll are suitable for B-roll insertion
- Which B-roll clip best matches each selected moment
- How long the B-roll should be shown
- Why that B-roll is useful at that moment

You must produce a structured timeline plan in valid JSON format.

---------------------------------------
IMPORTANT EDITING RULES
---------------------------------------

1. Do NOT insert B-roll too frequently.
   - Maximum 6 insertions
   - Minimum gap of 4 seconds between insertions

2. Avoid inserting B-roll during:
   - Emotional statements
   - Personal opinions
   - Strong emphasis or punchlines (Keep the speaker on screen)

3. Prefer inserting B-roll when:
   - The speaker mentions a physical object
   - The speaker explains a process or action
   - Visuals add clarity, proof, or interest
   - The speaker references UI, product usage, or outcomes

4. The A-roll audio must be assumed to remain uninterrupted.

5. **Multilingual/Cross-Language Reasoning**: 
   - The transcript may be in a different language (e.g., Hindi, Spanish) or mixed (e.g., Hinglish).
   - You MUST translate the *meaning* of the spoken words into English internally to check for matches with the English B-roll descriptions.
   - For example, if the speaker says "market mein buhat bheed thi" (Hindi), you should match it to a "crowded market" B-roll if available.
   - Do NOT fail to match simply because the transcript language differs from the B-roll description language. Focus on the SEMANTIC CONCEPT.

---------------------------------------
MATCHING LOGIC
---------------------------------------

- Use semantic meaning, not keyword matching
- Match transcript segments to B-roll descriptions based on conceptual relevance
- Assign a confidence score (0.0–1.0) indicating how strong the match is
- Each B-roll clip can be reused at most once (or not at all if not relevant)

---------------------------------------
INPUT FORMAT
---------------------------------------

A-roll duration (seconds):
{duration}

A-roll transcript (array of segments):
{transcript_json}

B-roll clips:
{b_roll_json}

---------------------------------------
OUTPUT FORMAT (STRICT JSON)
---------------------------------------

{{
  "a_roll_duration": {duration},
  "insertions": [
    {{
      "start_sec": number,
      "duration_sec": number,
      "broll_id": string,
      "confidence": number,
      "reason": string
    }}
  ]
}}

---------------------------------------
QUALITY BAR
---------------------------------------

- The plan should feel like it was created by a professional video editor
- Every insertion must have a clear, human-understandable justification
- If a moment does NOT benefit from visuals, do NOT insert B-roll
- Correctness and reasoning matter more than quantity

Now analyze the provided inputs and generate the best possible B-roll insertion timeline.
    """

    model_name = os.getenv("LLM_MODEL", "gpt-4o")

    if PROVIDER == "gemini":
        try:
            model = genai.GenerativeModel(model_name)
            # Use generation_config to enforce JSON if supported, or just prompt
            response = await model.generate_content_async(
                system_prompt + "\n\nIMPORTANT: Output strictly valid JSON.",
                generation_config={"response_mime_type": "application/json"}
            )
            
            content = response.text
            # Clean up potential markdown code blocks
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            result = json.loads(content)
            return result.get("insertions", [])
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return []

    else:
        # OpenAI / OpenRouter
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": system_prompt}
            ],
            response_format={"type": "json_object"},
            extra_headers={
                "HTTP-Referer": "https://antigravity.dev",
                "X-Title": "Antigravity Planner"
            } if base_url else None
        )

        result = json.loads(response.choices[0].message.content)
        return result.get("insertions", [])
