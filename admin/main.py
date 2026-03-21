from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas, database
from app.database import get_db

app = FastAPI(title="RootNode Admin API")

@app.post("/problems", response_model=schemas.ProblemResponse)
def create_problem(problem: schemas.ProblemCreate, db: Session = Depends(get_db)):
    # check slug uniqueness
    existing = db.query(models.Problem).filter(models.Problem.slug == problem.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
        
    new_problem = models.Problem(**problem.dict())
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)
    return new_problem

@app.get("/problems", response_model=List[schemas.ProblemResponse])
def list_problems(db: Session = Depends(get_db)):
    return db.query(models.Problem).all()

@app.get("/problems/{id}", response_model=schemas.ProblemResponse)
def get_problem(id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@app.post("/test-cases", response_model=schemas.TestCaseResponse)
def add_test_case(test_case: schemas.TestCaseBase, problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    new_tc = models.TestCase(**test_case.dict(), problem_id=problem_id)
    db.add(new_tc)
    db.commit()
    db.refresh(new_tc)
    return new_tc

@app.get("/submissions", response_model=List[schemas.SubmissionResponse])
def list_submissions(db: Session = Depends(get_db)):
    return db.query(models.Submission).order_by(models.Submission.id.desc()).all()

@app.get("/")
def admin_root():
    return {"message": "RootNode Admin API is running"}
