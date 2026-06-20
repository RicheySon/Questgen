# Smart Question Generator (QuestGen)

A full-stack quiz app built with **Python (FastAPI) + HTML + CSS only** — no JavaScript.
The interface is fully server-rendered with Jinja2 templates and standard HTML forms.

## Features

- Locked difficulty per quiz: Easy, Medium, Hard, Advanced.
- Adaptive feedback: suggests your next difficulty level based on your score.
- Three question types that can be freely mixed:
  - Multiple choice
  - Short answer
  - True / False (asked as plain statements)
- Thousands of fresh questions via the Open Trivia Database, with a local fallback bank.
- Focus topic: narrow any category to a keyword (e.g. "Algebra" in Mathematics).
- Automatic timing: up to 1 minute per question on Easy, tightening to 25s on Advanced.
- Pure-CSS countdown bar; total time taken is measured server-side and shown on results.
- Results page with a color-coded review (green = correct, red = wrong) and explanations.
- Export everything from the server in Python:
  - Questions as JSON or CSV
  - A formatted result sheet as a **PDF** (generated with fpdf2)
- Share results via a prefilled email link.

## Tech Stack

- **Backend / logic:** Python, FastAPI
- **Templating:** Jinja2 (`templates/`)
- **Styling:** CSS (`static/style.css`)
- **PDF:** fpdf2
- **No JavaScript** anywhere in the project.

## Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the development server:

```bash
uvicorn main:app --reload
```

(If `uvicorn` is not on your PATH, use `python -m uvicorn main:app --reload`.)

3. Open:

```text
http://127.0.0.1:8000
```

## Project Structure

```text
main.py            # FastAPI app: routes, generation, grading, exports
templates/         # Jinja2 HTML templates (base, index, quiz, result)
static/style.css   # All styling
requirements.txt   # Python dependencies
```

---

Built by Rejoice Akosua Dzanku
