from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database, tasks, auth
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="RootNode Backend Engine")

@app.get("/problems", response_model=List[schemas.ProblemResponse])
def get_problems(db: Session = Depends(get_db)):
    problems = db.query(models.Problem).all()
    return problems

@app.get("/problems/{slug}", response_model=schemas.ProblemResponse)
def get_problem(slug: str, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.slug == slug).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@app.post("/submissions", response_model=schemas.SubmissionResponse)
def submit_code(
    submission: schemas.SubmissionCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Check if problem exists
    problem = db.query(models.Problem).filter(models.Problem.id == submission.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Create submission record
    new_submission = models.Submission(
        user_id=current_user.id,
        problem_id=submission.problem_id,
        language=submission.language,
        code_body=submission.code_body,
        status="Pending"
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)
    
    # Push work to Celery task
    tasks.run_judge_task.delay(new_submission.id)
    
    return new_submission

@app.get("/submissions/{id}", response_model=schemas.SubmissionResponse)
def get_submission_status(id: int, db: Session = Depends(get_db)):
    submission = db.query(models.Submission).filter(models.Submission.id == id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission

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

@app.get("/")
def read_root():
    return {"message": "Welcome to RootNode Backend Engine API"}

@app.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
