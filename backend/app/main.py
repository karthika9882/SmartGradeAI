from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.config import settings
from app.database import Base, engine, get_db
from app.models import Question, Submission
from app.schemas import QuestionCreate, QuestionOut, SubmissionOut, ReviewUpdate
from app.services.ocr import extract_text
from app.services.evaluator import evaluate_answer

Base.metadata.create_all(bind=engine)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app = FastAPI(title=settings.app_name, version="1.0.0",
              description="AI-assisted grading. AI recommends marks; teachers review and finalize.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
ALLOWED = {".png",".jpg",".jpeg",".tif",".tiff",".bmp",".pdf"}

@app.get("/")
def root():
    return {"message":"SmartGrade AI API is running","docs":"/docs","human_review_required":True}

@app.get("/health")
def health():
    return {"status":"ok","ollama_enabled":settings.ollama_enabled}

@app.get("/api/questions", response_model=list[QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    return list(db.scalars(select(Question).order_by(Question.id.desc())).all())

@app.post("/api/questions", response_model=QuestionOut, status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    if payload.rubric and sum(c.marks for c in payload.rubric) > payload.max_marks + .001:
        raise HTTPException(422, "Rubric marks cannot exceed maximum marks.")
    q = Question(title=payload.title, question_text=payload.question_text,
                 reference_answer=payload.reference_answer, max_marks=payload.max_marks,
                 rubric=[c.model_dump() for c in payload.rubric])
    db.add(q); db.commit(); db.refresh(q)
    return q

@app.get("/api/questions/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.get(Question, question_id)
    if not q: raise HTTPException(404, "Question not found.")
    return q

@app.post("/api/submissions", response_model=SubmissionOut, status_code=201)
async def create_submission(question_id: int = Form(...), student_label: str = Form("Student"),
                            answer_text: str = Form(""), file: UploadFile | None = File(None),
                            db: Session = Depends(get_db)):
    q = db.get(Question, question_id)
    if not q: raise HTTPException(404, "Question not found.")
    if not answer_text.strip() and file is None:
        raise HTTPException(422, "Enter an answer or upload an answer-sheet image/PDF.")
    filename, ocr_status, extracted = None, "not_needed", ""
    if file is not None:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED: raise HTTPException(415, "Upload an image or PDF.")
        contents = await file.read()
        if len(contents) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")
        safe_name = datetime.now().strftime("%Y%m%d%H%M%S%f") + suffix
        (Path(settings.upload_dir) / safe_name).write_bytes(contents)
        filename = file.filename
        extracted, ocr_status = extract_text(str(Path(settings.upload_dir) / safe_name))
        if not answer_text.strip() and extracted.strip(): answer_text = extracted
        elif extracted.strip(): answer_text += "\n\n[OCR extracted text]\n" + extracted
    if not answer_text.strip():
        raise HTTPException(422, f"No answer text extracted ({ocr_status}). Paste/type the answer and retry.")
    evaluation = evaluate_answer(answer_text, q.question_text, q.reference_answer, q.rubric or [], q.max_marks)
    score = min(q.max_marks, max(0, float(evaluation.get("recommended_marks",0))))
    s = Submission(question_id=q.id, student_label=student_label.strip() or "Student",
        answer_text=answer_text, original_filename=filename, ocr_status=ocr_status,
        recommended_marks=round(score,2), evaluation=evaluation, status="needs_review", is_finalized=False)
    db.add(s); db.commit(); db.refresh(s)
    return s

@app.get("/api/submissions", response_model=list[SubmissionOut])
def list_submissions(db: Session = Depends(get_db)):
    return list(db.scalars(select(Submission).order_by(Submission.id.desc())).all())

@app.get("/api/submissions/{submission_id}", response_model=SubmissionOut)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    s = db.get(Submission, submission_id)
    if not s: raise HTTPException(404, "Submission not found.")
    return s

@app.patch("/api/submissions/{submission_id}/review", response_model=SubmissionOut)
def review_submission(submission_id: int, payload: ReviewUpdate, db: Session = Depends(get_db)):
    s = db.get(Submission, submission_id)
    if not s: raise HTTPException(404, "Submission not found.")
    if s.is_finalized: raise HTTPException(409, "Finalized marks cannot be edited.")
    q = db.get(Question, s.question_id)
    if payload.final_marks is not None and payload.final_marks > q.max_marks:
        raise HTTPException(422, f"Marks cannot exceed {q.max_marks}.")
    if payload.final_marks is not None: s.final_marks = round(payload.final_marks,2)
    s.teacher_feedback = payload.teacher_feedback
    s.status = "reviewed"; s.reviewed_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(s)
    return s

@app.post("/api/submissions/{submission_id}/finalize", response_model=SubmissionOut)
def finalize_submission(submission_id: int, db: Session = Depends(get_db)):
    s = db.get(Submission, submission_id)
    if not s: raise HTTPException(404, "Submission not found.")
    if s.is_finalized: return s
    if s.final_marks is None: raise HTTPException(422, "Set teacher-reviewed final_marks before finalizing.")
    s.is_finalized = True; s.status = "finalized"; s.reviewed_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(s)
    return s

@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    count_q = db.scalar(select(func.count(Question.id))) or 0
    count_s = db.scalar(select(func.count(Submission.id))) or 0
    pending = db.scalar(select(func.count(Submission.id)).where(Submission.is_finalized == False)) or 0
    final = db.scalar(select(func.count(Submission.id)).where(Submission.is_finalized == True)) or 0
    return {"questions":count_q,"submissions":count_s,"pending_review":pending,"finalized":final}
