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

## Step 4 — 100% Offline 3D Web App, Browser Visual QA & Claude Audit #3 (2026-11-25 00:49 – 00:58)
- **Tools / Models Used:** Antigravity (Gemini), local Three.js r147 (`static/vendor/three.min.js`), live Browser Visual QA subagent, Claude Code CLI (`--model sonnet`) Stage 3 Audit.
- **Actions Performed:**
  1. Bundled Three.js r147 locally (zero CDN links, zero external fonts, inline SVG favicon — 100% offline!).
  2. Built `static/index.html`, `static/styles.css`, `static/app.js`: 3D steppe terrain with wildfire flame cones, rising embers, wind streaks, glowing A*/BFS/UCS paths, animated 3D rescue drone, click-to-inspect Math Inspector, live Watchtower Bayes Alert, Human-in-the-Loop approval gate, and 2D Canvas Fallback.
  3. Ran live Browser QA across all 3 tabs, presets, Bayes update, and 2D fallback (0 JS console errors, 0 failed HTTP requests) and saved hero screenshot to `results/fig4_3d_live_demo.png`.
  4. Ran Claude Sonnet Stage 3 Audit (`context/AUDIT_3_FRONTEND.md`) and fixed all P0/P1 findings (`AbortController` + 80ms debounce, rollback + error banner, animation timer cancel, active preset sync, HITL session persistence, badge `nowrap`, `e^(-z)` formatting, 2D DPR & S/G markers, WebGL pause when hidden).
- **Verification:** `19/19` tests PASSED, live browser QA verified, commit `6bd4189`.

## Step 5 — Deliverables Generation: README, Report, Declarations, 7-Slide Deck & Defense Guide (2026-11-25 00:58 – 01:04)
- **Tools / Models Used:** Antigravity (Gemini), `python-docx`, `python-pptx`, `scripts/build_docs.py`.
- **Actions Performed:**
  1. Authored `README.md`, `docs/TECHNICAL_REPORT.md`, `docs/AI_USAGE_DECLARATION.md` (exact Syllabus Appendix table), `docs/TEAM_CONTRIBUTION_STATEMENT.md` (Solo 100%, Oral Sanzhar), and bilingual `context/DEFENSE_GUIDE.md` (2–3 min video script + 2-min algorithm pitch + 12 Q&A pairs).
  2. Generated formatted Word & PowerPoint deliverables via `scripts/build_docs.py`:
     - `docs/SteppeGuard_Technical_Report.docx` (with Figures 1–4 embedded)
     - `docs/AI_Usage_Declaration.docx`
     - `docs/Team_Contribution_Statement.docx`
     - `docs/SteppeGuard_Presentation.pptx` (strictly 7 slides, 16:9 dark tactical theme)
- **Next Step:** Final 100-Point Rubric Audit #4 with Claude Sonnet, final test & Git freeze.

## Step 6 — Stage 4 Final Rubric Audit, Synchronization & Git Freeze (2026-11-25 01:04 – 01:07)
- **Tools / Models Used:** Claude Code CLI (`--model sonnet`) Final Audit #4, Antigravity (fixes & rebuild), `pytest`, `git`.
- **Actions Performed:**
  1. Ran Stage 4 Final Rubric Audit (`context/AUDIT_4_FINAL_RUBRIC.md`).
  2. Synchronized all §4.1–§4.2 numbers in `docs/TECHNICAL_REPORT.md` verbatim against `results/benchmark_summary.json` and rebuilt all `.docx` & `.pptx` deliverables.
  3. Made `AI_USAGE_DECLARATION.md/.docx` 100% literal regarding visual QA vs programmatic slide geometry checks, distinguished single-run vs 30-seed stats cleanly, and unified preset naming.
  4. Verified `19/19` tests PASSED and confirmed via `git ls-files` that zero university lecture PDFs/PPTXs/DOCXs or `.venv` files are tracked.
  5. Tagged final release `v1.0-submission`.

## Step 7 — GitHub Publication & Live Vercel Production Deployment (2026-11-25 01:14 – 01:32)
- **Actions Performed:**
  1. Added lightweight Vercel serverless entrypoint (`api/index.py`, `vercel.json`) and separated prod runtime deps (`requirements.txt`) from dev/doc deps (`requirements-dev.txt`).
  2. Installed portable GitHub CLI (`gh` v2.105.0), authenticated as `sazmak`, created public repository `https://github.com/sazmak/steppeguard-ai`, and pushed `main` + tag `v1.0-submission`.
  3. Verified live production deployment at `https://steppeguard-ai.vercel.app` via browser QA (HTTP 200 on `/`, Three.js 3D terrain, `POST /api/run`, `GET /api/benchmarks`, all 3 benchmark PNGs, 0 JS console errors).
  4. Embedded live Demo & GitHub URLs into `README.md`, `TECHNICAL_REPORT.md/.docx`, and Slide 1 of `SteppeGuard_Presentation.pptx`.

## Step 8 — Automated 2:48 Live 3D Demo Video with ElevenLabs (`sazmak2`) (2026-11-25 12:45 – 12:56)
- **Tools / Models Used:** ElevenLabs API (`eleven_multilingual_v2`, student's cloned voice `sazmak2`), Playwright + Microsoft Edge (1280×720 live WebGL recording), `ffmpeg` (`H.264/AAC`).
- **Security:** Stored `ELEVENLABS_API_KEY` strictly in gitignored `.env` (verified never tracked by Git).
- **Output:** `docs/SteppeGuard_Demo_Video.mp4` (`2:48`, `22.39 MB`, synchronized 6-scene live walkthrough).
- **Transparency:** Added ElevenLabs TTS disclosure to `docs/AI_USAGE_DECLARATION.md` and rebuilt `docs/AI_Usage_Declaration.docx`.
