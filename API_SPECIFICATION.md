# RootNode: High-Performance Online Judge Backend Engine

## Project Overview
RootNode is a secure, scalable, and high-performance **Online Judge System** designed to host coding challenges and grade user-submitted code in real-time. Built with a robust **Producer-Consumer architecture**, the engine ensures that the web server remains responsive while a fleet of background workers executes potentially dangerous code inside isolated, resource-constrained **Docker sandboxes**. The system supports multiple programming languages including **Python, C++, Java, and Go**, and provides detailed feedback such as memory usage, execution time, and specific error types (TLE, Runtime Error, etc.). By leveraging **FastAPI** for its speed, **Celery/Redis** for its task queue, and **PostgreSQL** for persistence, RootNode serves as the backbone for building a professional coding platform similar to LeetCode or Codeforces.

### Core Features
- **Isolated Code Execution:** Every submission runs in a dedicated Docker container with zero network access and strict CPU/Memory limits.
- **Multi-Language Support:** First-class support for Python 3, modern C++ (GCC), Java (OpenJDK), and Go.
- **Asynchronous Judging:** Uses Celery to handle heavy compilation and execution tasks in the background, preventing API hangs.
- **Resource Profiling:** Accurately captures millisecond-level execution time and peak memory consumption (MB).
- **Secure Authentication:** Seamlessly integrates with **Firebase Auth** for enterprise-grade user security.
- **Scalable Architecture:** Designed to handle high-concurrency environments by distributing workers across multiple servers.

## Base URL
- **Local Development:** `http://localhost:8000`
- **Production (Vercel):** `https://your-deployment-url.vercel.app`

---

## Authentication

This project uses **Firebase Authentication**. The backend supports **Google Sign-In** (and any other Firebase-supported provider) using a token-based flow. There is **no separate register endpoint** — user accounts are created automatically on first login.

---

### 🔐 Authentication Flow (Google Sign-In)

```
┌─────────────┐        ┌─────────────────┐        ┌──────────────────┐
│   Frontend  │        │  Firebase Auth  │        │  RootNode Backend│
└──────┬──────┘        └────────┬────────┘        └────────┬─────────┘
       │  1. Sign in with       │                          │
       │     Google (OAuth)     │                          │
       │───────────────────────►│                          │
       │                        │                          │
       │  2. Firebase ID Token  │                          │
       │◄───────────────────────│                          │
       │                        │                          │
       │  3. API Request with   │                          │
       │     Bearer <idToken>   │                          │
       │─────────────────────────────────────────────────►│
       │                        │                          │
       │                        │  4. Verify token with   │
       │                        │     Firebase Admin SDK  │
       │                        │◄────────────────────────│
       │                        │                          │
       │                        │  5. Token valid → uid,  │
       │                        │     email, name, picture│
       │                        │─────────────────────────►│
       │                        │                          │  6. Lookup user by
       │                        │                          │     firebase_uid in DB
       │                        │                          │  ┌──────────────────┐
       │                        │                          │  │ If NOT found:    │
       │                        │                          │  │ Auto-create user │
       │                        │                          │  └──────────────────┘
       │  7. API Response       │                          │
       │◄─────────────────────────────────────────────────│
└──────┴──────┘        └────────┴────────┘        └────────┴─────────┘
```

**Step-by-step:**
1. **Frontend** initiates Google Sign-In using the Firebase SDK (web/mobile).
2. Firebase returns a short-lived **ID Token** (`idToken`) after successful OAuth.
3. **Frontend** sends all authenticated API requests with the token in the `Authorization` header.
4. **Backend** verifies the token using the Firebase Admin SDK.
5. Firebase Admin decodes the token and returns the user's `uid`, `email`, `name`, and `picture`.
6. Backend checks if a user with this `firebase_uid` exists in the database:
   - ✅ **Existing user** → returns the user record (sign-in).
   - 🆕 **New user** → automatically creates a new user record (sign-up).
7. The protected API endpoint proceeds and returns its response.

> **Note:** Firebase ID Tokens expire after **1 hour**. The frontend must refresh the token using `firebase.auth().currentUser.getIdToken(true)` before expiry.

---

### Header Format

All protected endpoints require the Firebase ID Token in the `Authorization` header:

```
Authorization: Bearer <firebase_id_token>
```

---

### User Auto-Registration (First Login)

When a new Google user hits any protected endpoint for the first time, the backend automatically creates their account with the following fields populated from the Firebase token:

| Field | Source |
| :--- | :--- |
| `firebase_uid` | `uid` from decoded token |
| `email` | `email` from decoded token |
| `display_name` | `name` from decoded token (Google display name) |
| `photo_url` | `picture` from decoded token (Google profile picture URL) |
| `tier` | Defaults to `"User"` |

---

### Authentication Errors

| HTTP Status | Detail | Cause |
| :--- | :--- | :--- |
| `401` | `Missing Authorization Header` | No `Authorization` header sent |
| `401` | `Invalid Authorization Header. Must start with Bearer` | Header format is wrong |
| `401` | `Invalid or expired token: ...` | Token is malformed, expired, or revoked |

---

## 1. Problems API

### GET `/problems`
Returns a list of all available coding challenges.

- **Purpose:** Display a landing page with available problems.
- **Request:** `GET`
- **Response:** `Array<ProblemResponse>`

**Sample JSON Response:**
```json
[
  {
    "id": 1,
    "title": "Two Sum",
    "slug": "two-sum",
    "description": "Given an array of integers...",
    "difficulty": "Easy",
    "time_limit_sec": 2.0,
    "memory_limit_mb": 256,
    "test_cases": [] 
  }
]
```

---

### GET `/problems/{slug}`
Fetches the full description and sample test cases for a specific problem.

- **Purpose:** Detail view for a coding challenge.
- **Request:** `GET`
- **Response:** `ProblemResponse`

**Sample JSON Response:**
```json
{
  "id": 1,
  "title": "Two Sum",
  "slug": "two-sum",
  "description": "Find indices of target sum...",
  "difficulty": "Easy",
  "time_limit_sec": 2.5,
  "memory_limit_mb": 256,
  "test_cases": [
    {
      "id": 12,
      "input_text": "[2,7,11,15], 9",
      "expected_output": "[0,1]",
      "is_sample": true
    }
  ]
}
```

---

## 2. Submissions API

### POST `/submissions`
Submits user code for judging. **Note:** This is an asynchronous process.

- **Purpose:** Start the code execution and judging process.
- **Request:** `POST` (Requires Authentication)
- **JSON Payload:**
```json
{
  "problem_id": 1,
  "language": "python", 
  "code_body": "def twoSum(nums, target):..."
}
```
*Supported Languages:* `python`, `cpp`, `java`, `go`

- **Response:** `SubmissionResponse` (Returns immediately with status `Pending`)

---

### GET `/submissions/{id}`
Retrieves the current status and results of a code submission.

- **Purpose:** Poll this endpoint until the status is no longer `Pending` or `Running`.
- **Request:** `GET`
- **Response:** `SubmissionResponse`

**Sample JSON Response (Still Processing):**
```json
{
  "id": 54,
  "status": "Running",
  "execution_time": null,
  "memory_usage": null
}
```

**Sample JSON Response (Finished):**
```json
{
  "id": 54,
  "status": "Accepted",
  "execution_time": 156.4,
  "memory_usage": 12.5,
  "error_message": null
}
```

**Status Enum Table:**
| Status | Meaning |
| :--- | :--- |
| `Pending` | In queue, waiting for a worker. |
| `Running` | Currently being executed in Docker. |
| `Accepted` | All test cases passed! |
| `Wrong Answer` | Output doesn't match expected output. |
| `TLE` | Time Limit Exceeded. |
| `Runtime Error` | Code crashed during execution. |
| `Compile Error` | Code failed to compile (C++/Java). |

---

## 3. User API

### GET `/me`
Returns current authenticated user details.

- **Purpose:** Get user profile after Firebase sign-in.
- **Request:** `GET` (Requires Authentication)
- **Response:** `UserResponse`

**Sample JSON Response:**
```json
{
  "id": 1,
  "username": "coder123",
  "email": "coder@example.com",
  "display_name": "John Doe",
  "tier": "User"
}
```

---

## Frontend Integration Tips (Polling Workflow)
1. User clicks **Submit**.
2. Frontend calls `POST /submissions`.
3. Backend returns a `submission_id` and status `Pending`.
4. Frontend shows a "Running..." spinner.
5. Frontend starts polling `GET /submissions/{id}` every 1-2 seconds.
6. Once `status` is `Accepted`, `Wrong Answer`, etc., stop polling and show final result.
