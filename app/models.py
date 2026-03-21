from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    tier = Column(String)  # User/Admin

class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    slug = Column(String, unique=True, index=True)
    description = Column(Text)
    difficulty = Column(String)
    time_limit_sec = Column(Float)
    memory_limit_mb = Column(Integer)
    test_cases = relationship("TestCase", back_populates="problem")

class TestCase(Base):
    __tablename__ = "test_cases"
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    input_text = Column(Text)
    expected_output = Column(Text)
    is_sample = Column(Boolean, default=False)
    problem = relationship("Problem", back_populates="test_cases")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    problem_id = Column(Integer, ForeignKey("problems.id"))
    language = Column(String)
    code_body = Column(Text)
    status = Column(String)  # Pending -> Running -> Accepted/WA/TLE
    execution_time = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
