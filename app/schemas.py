from pydantic import BaseModel
from typing import List, Optional

class ProblemBase(BaseModel):
    title: str
    slug: str
    description: str
    difficulty: str
    time_limit_sec: float
    memory_limit_mb: int

class ProblemCreate(ProblemBase):
    pass

class TestCaseBase(BaseModel):
    input_text: str
    expected_output: str
    is_sample: bool = False

class TestCaseResponse(TestCaseBase):
    id: int
    class Config:
        from_attributes = True

class ProblemResponse(ProblemBase):
    id: int
    test_cases: List[TestCaseResponse] = []
    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    problem_id: int
    language: str
    code_body: str

import uuid

class SubmissionResponse(BaseModel):
    id: int
    problem_id: int
    user_id: uuid.UUID
    language: str
    code_body: str
    status: str
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    error_message: Optional[str] = None
class UserResponse(BaseModel):
    id: uuid.UUID
    username: Optional[str] = None
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    tier: str
    class Config:
        from_attributes = True
