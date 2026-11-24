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

---

## Step 1 — Environment, Portable Git & Course Formula Extraction (2026-11-25 00:26 – 00:29)
- **Tools / Models Used:** Antigravity (Gemini), `winget` (`Git.MinGit` v2.56.1), Python 3.13 `.venv`, PyMuPDF & XML parsers.
- **Actions Performed:**
  1. Locked all 17 rules in `context/RULES.md`.
  2. Installed portable MinGit (`git 2.56.1`) without admin privileges and created isolated Python `.venv` with `numpy`, `fastapi`, `uvicorn`, `pytest`, `httpx`, `matplotlib`, `python-pptx`, `python-docx`.
  3. Extracted exact notation, definitions, and slide citations from all course decks into `context/COURSE_REFERENCES.md`.
  4. Initialized Git repo (`main`, commit `cf420ba`).
- **Verification:** `ALL_DEPS_OK`, `git version 2.56.1.windows.1`, clean initial commit.

## Step 2 — Stage 1 Peer Architecture Audit (2026-11-25 00:28 – 00:30)
- **Tools / Models Used:** Claude Code CLI (`--model sonnet`, Pro subscription) auditing `context/RULES.md`, `context/PROJECT_OVERVIEW.md`, `context/COURSE_REFERENCES.md`.
- **Key Findings Incorporated:** Lowered A* $\lambda = 3.5$ with live $c_{\min}$, replaced dead `Sensor Re-scan` MDP action with `Monitor`, gated `Aerial Retardant` on High Resources, coupled MDP transitions to BFS/A* exposure, added scene-grouped 3-way ML split + label noise + `dryness * wind` interaction, planned 30-seed benchmark suite. Recorded in `context/AUDIT_1_ARCHITECTURE.md`.

## Step 3 — Core Python AI Engine, Tests, Benchmarks & Stage 2 Audit (2026-11-25 00:30 – 00:44)
- **Tools / Models Used:** Antigravity (implementation & Visual QA), `pytest`, `scripts/benchmark.py`, Claude Code CLI (`--model sonnet`) for Stage 2 Code & Math Audit.
- **Actions Performed:**
  1. Built pure-NumPy modules: `src/config.py`, `src/data.py`, `src/ml_model.py`, `src/search.py`, `src/mdp.py`, `src/pipeline.py`, `app.py`, `scripts/benchmark.py`.
  2. Built comprehensive `pytest` suite (`tests/test_ml.py`, `tests/test_search.py`, `tests/test_mdp.py`, `tests/test_integration.py`).
  3. Ran Claude Sonnet Stage 2 Audit (`context/AUDIT_2_BACKEND.md`): 0 P0 bugs; fixed all 3 P1 items (per-step exposure normalization + counterfactual coupling test + 3 distinct preset actions, GNB Math Inspector + separate validation $\tau_{\text{gnb}}$, Brier baseline & honest ML framing) plus P2 cleanups (active L2 $\lambda=1.0$, probability-weighted rewards, Confusion Matrix contrast fix).
- **Verification:** `19/19` tests PASSED in `1.55s`; 30-seed benchmarks & all 3 PNG figures generated and visually verified. Ready for **Pre-Visual Checkpoint**.
