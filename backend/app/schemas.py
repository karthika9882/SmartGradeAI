from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator

class RubricCriterion(BaseModel):
    criterion: str = Field(min_length=1, max_length=300)
    keywords: list[str] = Field(default_factory=list)
    marks: float = Field(gt=0)

class QuestionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    question_text: str = Field(min_length=5)
    reference_answer: str = Field(min_length=10)
    max_marks: float = Field(gt=0, le=1000)
    rubric: list[RubricCriterion] = Field(default_factory=list)

    @model_validator(mode="after")
    def rubric_fits_maximum(self):
        if self.rubric and sum(c.marks for c in self.rubric) > self.max_marks + 0.001:
            raise ValueError("Sum of rubric marks cannot exceed max_marks.")
        return self

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    question_text: str
    reference_answer: str
    max_marks: float
    rubric: list
    created_at: datetime

class ReviewUpdate(BaseModel):
    final_marks: float | None = Field(default=None, ge=0)
    teacher_feedback: str = Field(default="", max_length=5000)

class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: int
    student_label: str
    answer_text: str
    original_filename: str | None
    ocr_status: str
    recommended_marks: float
    final_marks: float | None
    evaluation: dict
    teacher_feedback: str
    status: str
    is_finalized: bool
    created_at: datetime
    reviewed_at: datetime | None
