from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def now_utc():
    return datetime.now(timezone.utc)

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    question_text: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str] = mapped_column(Text)
    max_marks: Mapped[float] = mapped_column(Float)
    rubric: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    submissions: Mapped[list["Submission"]] = relationship(back_populates="question")

class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    student_label: Mapped[str] = mapped_column(String(120), default="Student")
    answer_text: Mapped[str] = mapped_column(Text, default="")
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ocr_status: Mapped[str] = mapped_column(String(80), default="not_needed")
    recommended_marks: Mapped[float] = mapped_column(Float, default=0)
    final_marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    evaluation: Mapped[dict] = mapped_column(JSON, default=dict)
    teacher_feedback: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="needs_review")
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    question: Mapped["Question"] = relationship(back_populates="submissions")
