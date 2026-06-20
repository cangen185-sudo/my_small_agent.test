# Mini Task Tracker

Mini Task Tracker is a small Python + Streamlit app for students to manage course tasks and weekly study goals.

## Problem

Many students track homework, lab deadlines, and review tasks in different places. This project gives them a lightweight local dashboard.

## Tech Stack

- Python
- Streamlit
- SQLite in a future version
- pytest

## Install

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

```text
app.py
src/task_store.py
src/report.py
tests/test_task_store.py
```

## Usage

Run the app locally, add tasks, mark them done, and export a weekly Markdown report.

## TODO

- Add screenshots
- Add more tests
- Improve error messages

