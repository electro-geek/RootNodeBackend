It provides the architectural "mental model," the data structures, and the high-level logic needed to build a secure, scalable Online Judge backend.

---

# Technical Specification: "RootNode" Backend Engine
**Stack:** FastAPI (Python), PostgreSQL, Redis, Celery, Docker SDK.

## 1. Project Vision & Core Features
This backend is a high-performance **Online Judge System** designed to securely execute untrusted user code against hidden test cases.

### Key Features for the AI to Implement:
* **Isolated Code Execution (Sandboxing):** Uses Docker containers to run user code with zero network access and strict resource limits (CPU/Memory).
* **Multi-Language Support:** Dynamic execution environment for Python, C++, and Java.
* **Asynchronous Processing:** Uses a Task Queue (Celery) so the API remains responsive while the "Judge" runs heavy computations.
* **Test Case Management:** Supports multiple inputs/outputs per problem, including "Hidden" cases for final grading.
* **Live Submission Tracking:** A polling-ready status system (Pending $\rightarrow$ Running $\rightarrow$ Accepted/WA/TLE).
* **Resource Monitoring:** Captures execution time (ms) and peak memory usage (MB) for every submission.

---

## 2. System Architecture
The system follows a **Producer-Consumer** pattern to ensure the web server never crashes due to heavy user code.

1.  **FastAPI (The Producer):** Validates the request and pushes a `judge_task` to Redis.
2.  **Redis (The Broker):** Holds the queue of pending submissions.
3.  **Celery Worker (The Consumer/Judge):** The "Brain" that pulls tasks, manages Docker containers, and compares outputs.
4.  **PostgreSQL (The Truth):** Stores problems, test cases, and the final state of all submissions.



---

## 3. Database Schema (SQLAlchemy/Tortoise)
* **`User`**: `id, username, hashed_password, tier (User/Admin)`.
* **`Problem`**: `id, title, slug, description, difficulty, time_limit_sec, memory_limit_mb`.
* **`TestCase`**: `id, problem_id (FK), input_text, expected_output, is_sample (bool)`.
* **`Submission`**: `id, user_id (FK), problem_id (FK), language, code_body, status (Enum), execution_time, memory_usage, error_message`.

---

## 4. The Judge Logic (The "Sandbox" Function)
The AI should implement a core module `judge.py`. This is the most critical logic:

### The Execution Flow:
1.  **Setup:** Create a temporary directory. Write the user's `code_body` to a file (e.g., `solution.cpp`).
2.  **Container Start:** Use the Python `docker` library to pull/run a slim image.
    * **C++:** `g++ solution.cpp -o solution && ./solution < input.txt`
    * **Python:** `python3 solution.py < input.txt`
3.  **Safety Constraints:**
    * `network_disabled=True`
    * `mem_limit="256m"`
    * `cpu_quota=50000` (50% of one CPU core)
    * `read_only=True` (User cannot write to the container FS)
4.  **Comparison:** Strip trailing whitespaces/newlines from `stdout` and compare with `expected_output`.
5.  **Timeout:** If the container runs longer than `problem.time_limit_sec`, kill it and return `TLE`.

---

## 5. API Endpoints for FastAPI
* `GET /problems`: List all available coding challenges.
* `GET /problems/{slug}`: Get full description and sample test cases.
* `POST /submissions`: Submit code. Returns a `submission_id`.
* `GET /submissions/{id}`: Check if the code is finished and get the result.

---

## 6. Prompt for your AI Assistant (Copy/Paste this)
> "Act as a Senior Backend Engineer. Use the provided specification to build a FastAPI project. 
> 1. Set up a PostgreSQL database using SQLAlchemy for Users, Problems, and Submissions. 
> 2. Create a Celery worker that uses the Docker Python SDK to run code inside 'python:3.10-slim' and 'gcc:latest' containers. 
> 3. Ensure the worker limits memory to 256MB and kills the process if it exceeds a 2-second timeout. 
> 4. Implement a logic that compares the container's output against stored test cases.
> 5. Use a .env file for database credentials and Docker socket paths."

## 7. Firebase Authentication & Vercel Deployment

This project uses **Firebase Authentication** for Google Sign-in/Sign-up. The backend verifies the Firebase ID Token sent from the frontend.

### Environment Variables (Vercel/Production)
To deploy on Vercel or any cloud provider, set the following environment variables:

| Variable | Description |
| :--- | :--- |
| `FIREBASE_PROJECT_ID` | Your Firebase Project ID |
| `FIREBASE_CLIENT_EMAIL` | Firebase Service Account Client Email |
| `FIREBASE_PRIVATE_KEY` | Firebase Service Account Private Key (include `\n`) |
| `DB_URL` | PostgreSQL Connection URL |
| `REDIS_URL` | Redis URL (used for Celery broker & backend) |

### How to get Firebase Credentials:
1. Go to **Firebase Console** $\rightarrow$ Project Settings $\rightarrow$ Service Accounts.
2. Click **Generate New Private Key**.
3. Copy `project_id`, `client_email`, and `private_key` from the downloaded JSON.
4. When setting `FIREBASE_PRIVATE_KEY` in Vercel, ensure it's the full string including `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----`.

### Authentication Flow:
1. Frontend signs in user with Google via Firebase.
2. Frontend retrieves `idToken`.
3. Frontend sends `idToken` in `Authorization: Bearer <token>` header to backend.
4. Backend verifies token, syncs user data in PostgreSQL, and returns user info.

---

## 8. Development Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Update `config.properties` or set environment variables.
3. Run the API: `python run.py`
4. Run the Celery worker: `celery -A app.celery_app worker --loglevel=info`

