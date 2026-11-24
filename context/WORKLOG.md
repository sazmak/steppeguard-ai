# SteppeGuard AI — Step-by-Step Development Worklog

Every major step, decision, tool used, audit result, and verification check is logged here chronologically for full reproducibility and academic transparency.

---

## Step 0 — Environment & Requirements Discovery (2026-11-24 23:41 – 00:22)
- **Tools / Models Used:** Antigravity (Gemini 4 Neon High), PowerShell inspection, PyMuPDF (`fitz`), Python XML parser.
- **Actions Performed:**
  1. Verified Claude Code CLI (`claude.exe` v2.1.318) is installed and authenticated under student's Claude Pro subscription (`loggedIn: true`, `subscriptionType: "pro"`).
  2. Verified Python 3.13.15, Node v22.23.5, and `numpy` installed; noted `git` is not yet on PATH and additional Python libraries (`fastapi`, `uvicorn`, `pytest`, `matplotlib`, `python-pptx`, `python-docx`) will be installed in a dedicated project `.venv`.
  3. Extracted and analyzed all course materials in `C:\Users\sazmak\Desktop\AIF FINAL\`:
     - `Final Project.docx`
     - `MiniAI_FPTopics.docx`
     - Course Syllabus (`7033a59b-ddb1-4844-8522-9ca353322d68.pdf`)
     - Rubric screenshot (`100-point criteria` + `7 required deliverables` + defense timing)
     - Course lecture slides & practical guides (Weeks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 + `AI_Legal_Framework.pptx`).
  4. Brainstormed project concepts with the student and selected **SteppeGuard AI** tailored to the **6B06101 AI and ML** track (Classical ML + Risk-Aware A* Search + MDP Value Iteration).
  5. Initialized isolated project folder `steppeguard-ai/` and created `context/` governance files (`RULES.md`, `PROJECT_OVERVIEW.md`, `WORKLOG.md`, `PROMPT_LOG.md`).
- **Verification:** Confirmed all source course documents remain untouched outside `steppeguard-ai/`.
- **Next Step:** Confirm final ruleset with the student, extract exact course formulas/notation into `context/COURSE_REFERENCES.md`, and run Stage 1 Architecture Audit with Claude Code.
