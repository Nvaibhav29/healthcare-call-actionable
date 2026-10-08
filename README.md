# MedRoute AI — Healthcare Call Intelligence (HLS004)

Audio call → ASR → LLM → Structured action tickets routed to hospital departments.

## Stack
- **ASR**: Sarvam AI API (primary) → Whisper local (fallback)
- **LLM**: Gemini 1.5 Flash (primary) → Qwen2.5:7b via Ollama (fallback)
- **Backend**: FastAPI + Supabase
- **Frontend**: React + Vite

## Setup

### 1. Clone and configure
```bash
git clone https://github.com/Nvaibhav29/healthcare-call-actionable.git
cd healthcare-call-actionable
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Run Supabase schema
Open `database/schema.sql` and run it in your Supabase SQL editor.

### 3. Backend
```bash
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8000
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

## API Docs
Visit `http://localhost:8000/docs` after starting the backend.

## Pipeline
```
Audio → preprocess (ffmpeg) → ASR dual-mode → LLM dual-mode → Router → Supabase → Dashboard
```
