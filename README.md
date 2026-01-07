# Flona AI Assignment

A B-Roll insertion system.

## Start (Docker)

1. **Setup Environment**
    Navigate to `backend/`
    Create a file named `.env`
    Add your Gemini API key:
     ```env
     GEMINI_API_KEY=your_actual_api_key_here
     LLM_PROVIDER=gemini
     LLM_MODEL=gemini-2.5-flash
     ```

2. **Run Application**
    Open a terminal in the root folder.
    Run:
     ```bash
     docker-compose up --build
     ```

3. **Open in Browser**
    Frontend: [http://localhost:5173](http://localhost:5173)
    Backend API: [http://localhost:8000](http://localhost:8000)

---

## 🛠 Manual Setup (No Docker)

If you prefer running locally without Docker:

**Backend:**
1. `cd backend`
2. `pip install -r requirements.txt`
3. Make sure `ffmpeg` is installed on your system.
4. `python main.py`

**Frontend:**
1. `cd frontend`
2. `npm install`
3. `npm run dev`
