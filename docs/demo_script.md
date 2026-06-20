# Campus Agent Lab Demo Script

Use this short script when recording a demo video or presenting the project.

## 1. Opening

Campus Agent Lab is a local Streamlit toolbox for software engineering students. It focuses on three common study tasks: reading GitHub projects, checking Java/C lab code, and organizing final exam notes.

## 2. GitHub README Reader

Open the GitHub README reader, load the sample README, and generate the report.

Point out:

- One-sentence project summary
- Detected tech stack
- Install/run commands
- Student learning points
- Beginner contribution ideas

## 3. Java/C Code Checker

Open the Java/C checker, load the C sample or Java sample, and run the check.

Point out:

- The tool does not run user code
- Static checks explain the issue, fix, and reason
- Compile-only checks are skipped gracefully when gcc/javac is unavailable

## 4. Final Exam Agent

Open the final exam agent, load the sample notes, and generate the review plan.

Point out:

- Course guess
- Topics and keywords
- Exam focus
- Review tasks
- Three-day sprint plan

## 5. Close

Reports can be downloaded or saved to `outputs/` as Markdown files. The MVP works without an API key and can later be extended with `OPENAI_API_KEY` for better summaries.

