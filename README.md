# SmartGrade AI

A local-first, human-in-the-loop AI assessment assistant. It stores questions and submissions, extracts text from uploaded images/PDFs when OCR tools are installed, evaluates answers with a transparent TF-IDF/rubric baseline, optionally asks a local Ollama model for a second recommendation, and requires a teacher to review and finalize marks.

**This is an educational MVP, not a validated grading system. AI and OCR can be wrong. Never use AI recommendations as final marks without human review.**

## Features
- Question bank with reference answers, maximum marks, and rubric criteria.
- Typed answer submission or image/PDF upload.
- Optional Tesseract OCR; PDF OCR additionally requires Poppler.
- Baseline evaluation using TF-IDF similarity and rubric keyword coverage.
- Optional local Ollama evaluation.
- Teacher review, editable final marks, feedback, and explicit finalization.
- FastAPI REST API, Swagger docs, React/Vite dashboard, SQLite by default.
- PostgreSQL supported through `DATABASE_URL`.

## Requirements
Python 3.10+, Node.js 20+, npm. Optional: Ollama, Tesseract OCR, Poppler for PDFs.

## Run backend (Windows PowerShell)
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```
If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

Open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/health.

## Run frontend (second terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

## Optional local Ollama
Install Ollama from https://ollama.com. Pull a model:
```powershell
ollama pull llama3.2:latest
```
Set these values in `backend/.env`, then restart the backend:
```env
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:latest
```
If Ollama is unavailable or its response cannot be parsed, the app uses the baseline evaluator.

## Optional OCR
Install Tesseract (Windows installer: https://github.com/UB-Mannheim/tesseract/wiki) and make sure `tesseract.exe` is on PATH. For PDF OCR, install Poppler and add its `bin` directory to PATH. If OCR cannot extract text, paste the answer into the text field and submit again.

## Demo
The dashboard has a **Load demo question** action. It creates a photosynthesis question with four rubric criteria. Submit an answer, inspect evidence/limitations, edit the teacher marks, save the review, then explicitly finalize marks.

## API
- `GET /health`
- `GET /api/questions`
- `POST /api/questions`
- `GET /api/questions/{id}`
- `POST /api/submissions` (multipart form)
- `GET /api/submissions`
- `GET /api/submissions/{id}`
- `PATCH /api/submissions/{id}/review`
- `POST /api/submissions/{id}/finalize`
- `GET /api/stats`

## Example question payload
```json
{
  "title": "Photosynthesis",
  "question_text": "Explain photosynthesis.",
  "reference_answer": "Green plants use sunlight, chlorophyll, water, and carbon dioxide to produce glucose and oxygen.",
  "max_marks": 5,
  "rubric": [
    {"criterion":"Sunlight and chlorophyll","keywords":["sunlight","chlorophyll"],"marks":1.5},
    {"criterion":"Water and carbon dioxide","keywords":["water","carbon dioxide"],"marks":1.5},
    {"criterion":"Glucose production","keywords":["glucose"],"marks":1},
    {"criterion":"Oxygen product","keywords":["oxygen"],"marks":1}
  ]
}
```

## Important limitations and next steps
- Handwriting OCR quality varies. Always allow manual correction.
- TF-IDF and keyword coverage are heuristic signals, not a validated measure of understanding.
- LLM output can hallucinate. Evidence should be checked against the actual answer.
- This MVP does not include authentication, authorization, audit logs, production-grade file scanning, or backup/retention policies.
- Before real use, add login/roles, audit history, secure file handling, rubric versioning, test data labeled by teachers, and report MAE/RMSE/agreement with teacher scores.
