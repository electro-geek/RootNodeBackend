from .celery_app import celery_app
from .database import SessionLocal
from .models import Submission, Problem, TestCase
from .judge import judge_submission

@celery_app.task(name="app.tasks.run_judge_task")
def run_judge_task(submission_id: int):
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return f"Submission {submission_id} not found"
        
        problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
        test_cases = db.query(TestCase).filter(TestCase.problem_id == problem.id).all()
        
        submission.status = "Running"
        db.commit()
        
        # Structure data for judge_submission
        test_cases_data = [
            {"input_text": tc.input_text, "expected_output": tc.expected_output}
            for tc in test_cases
        ]
        problem_data = {
            "time_limit_sec": problem.time_limit_sec,
            "memory_limit_mb": problem.memory_limit_mb
        }
        
        status, time_val, mem_val, error = judge_submission(
            problem_data, test_cases_data, submission.language, submission.code_body
        )
        
        submission.status = status
        submission.execution_time = time_val
        submission.memory_usage = mem_val
        submission.error_message = error
        db.commit()
        
        return f"Submission {submission_id} finished: {status}"
    finally:
        db.close()
