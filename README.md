# Smart Question Generator

A full-stack quiz app using Python (FastAPI) for the backend and HTML/CSS/JS for the frontend.

## Features

- Dynamic difficulty adjustment based on user performance score.
- Supports multiple question types:
  - Multiple choice
  - Short answer
  - True/False
- Interactive frontend:
  - Progress bar
  - Quiz timer with auto-submit
  - Immediate answer feedback
- Export generated questions:
  - JSON
  - CSV
- Share generated quizzes using native Web Share API or clipboard link fallback.

## Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start development server:

```bash
uvicorn main:app --reload
```

3. Open:

```text
http://127.0.0.1:8000
```
