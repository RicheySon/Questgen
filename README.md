# QuestGen — Smart Question Generator

A capstone **Question Generator** built with **Python (FastAPI) + HTML + CSS only** (no JavaScript).
This README documents the project and shows that **all required StartoCode protocols were followed**.

---

## 1. Project Overview

QuestGen is a web app that generates quiz questions on demand. A user picks a
**Subject**, an optional **Topic**, and a **Number of Questions**, and the FastAPI
backend generates questions, processes the data, and returns a fully rendered HTML
page with the results.

The backend pulls a large, varied pool of questions from an external question API
(the Open Trivia Database) and falls back to a built-in local bank if the network is
unavailable, so questions rarely repeat. The frontend is plain HTML styled with CSS.

Beyond the core requirement, the project also includes an enhanced, adaptive quiz
experience (timed quizzes, instant grading, color-coded results, PDF export, and user
accounts) — all implemented within the same HTML/CSS/Python stack.

---

## 2. Required File Structure

All required files are present:

```text
QuestGen/
├── main.py             # FastAPI app: routes, build_page(), generation, grading
├── static/
│   ├── index.html      # The "face" of the app: the generator form + results placeholder
│   └── style.css       # All styling
├── templates/          # (Enhancement) Jinja2 templates for the adaptive quiz + auth
│   ├── base.html
│   ├── index.html
│   ├── quiz.html
│   ├── result.html
│   ├── login.html
│   └── signup.html
├── auth.py             # (Enhancement) accounts + sessions (stdlib only)
├── requirements.txt
└── README.md
```

---

## 3. Steps / Approach

The project follows the required 11-step build guide. Each step maps directly to code:

| # | Required Step | How it was done |
|---|---------------|-----------------|
| 1 | Create the project | Project `QuestGen` set up with a clean structure. |
| 2 | Build the HTML page | `static/index.html` is the app's face. |
| 3 | Create the form | Form with **Subject**, **Topic**, and **Number of Questions** inputs. |
| 4 | Style with CSS | `static/style.css` linked from the page for a polished UI. |
| 5 | Create the FastAPI app | `app = FastAPI(...)` in `main.py`. |
| 6 | Connect static files | `app.mount("/static", StaticFiles(directory="static"), ...)`. |
| 7 | Build the page function | `build_page()` loads `static/index.html` and swaps the `<!--RESULTS-->` placeholder for real data. |
| 8 | Create routes | `@app.get("/")` for the homepage and `@app.post("/generate")` for the form. |
| 9 | Send request to the question API | The FastAPI `/generate` endpoint is the question generator; it calls the external Open Trivia DB API server-side (`fetch_opentdb`) to source questions. |
| 10 | Process the response | The API response is parsed with Python's `json` module into a list of questions. |
| 11 | Display the results | `/generate` returns an `HTMLResponse(build_page(results_html))` with the questions rendered into the page. |

### How Step 9 relates to FastAPI

The spec's "send a request to the question generator" is implemented **through FastAPI**:
the browser's form submits (`POST /generate`) to our FastAPI backend, which *is* the
question generator. Internally, FastAPI sends an HTTP request to the external Open
Trivia DB question API, parses the JSON response (Step 10), and renders it (Step 11).

---

## 4. Required Protocols — Compliance Checklist

- [x] `static/index.html` present (the form / face of the app)
- [x] `static/style.css` present and linked
- [x] `main.py` present with `app = FastAPI()`
- [x] `StaticFiles` mounted to serve the frontend
- [x] `build_page()` function that swaps a placeholder for real data
- [x] `@app.get("/")` route (homepage)
- [x] `@app.post("/generate")` route (form handler)
- [x] Request sent to a question API and response parsed with `json`
- [x] Results returned via `HTMLResponse`
- [x] Form collects **Subject**, **Topic**, and **Number of Questions**
- [x] `README.md` with Project Overview, Steps / Approach, and Future Improvements

### Where to see it running

- Required generator (spec): open **`/generator`**, fill the form, submit → results render via `build_page()`.
- Enhanced adaptive quiz app: open **`/`** (sign up / log in first).

---

## 5. Features

- Question generation across 17 subjects with an optional focus topic.
- Three question types: multiple choice, short answer, and true/false.
- Questions sourced live from the Open Trivia DB API, with a local fallback bank.
- **Enhancements** (same HTML/CSS/Python stack):
  - Adaptive, timed quiz with instant grading and a color-coded review.
  - Locked difficulty levels (Easy → Advanced) with auto-calculated timing.
  - PDF result sheet generated server-side with fpdf2.
  - User accounts: sign up, log in, log out (PBKDF2-hashed passwords, cookie sessions).

---

## 6. Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the server:

```bash
uvicorn main:app --reload
```

(If `uvicorn` is not on your PATH, use `python -m uvicorn main:app --reload`.)

3. Open:

```text
http://127.0.0.1:8000/generator   # required generator
http://127.0.0.1:8000/            # enhanced quiz app (requires an account)
```

---

## 7. Future Improvements

- Connect to a dedicated StartoCode question-generator API endpoint when available.
- Persist user accounts' quiz history and scores per subject.
- Add spaced-repetition that re-asks previously missed questions.
- Allow teachers to author and share custom question sets.
- Move sessions into the database and serve over HTTPS for production.
- Add accessibility passes (ARIA labels, keyboard focus states) and i18n.

---

Built by Rejoice Akosua Dzanku
