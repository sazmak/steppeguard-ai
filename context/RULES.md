# SteppeGuard AI — Project Rules & Working Agreements

> **Status:** APPROVED & LOCKED v1.0 (All 17 rules confirmed by student on 2026-11-25 00:26)
> **Course:** AIF1303 — AI Fundamentals (QAIRU, Astana, Trimester 1, 2026–2027)
> **Program:** 6B06101 "AI and ML" (Solo Project)
> **Defense Deadline:** 2026-11-25, 14:00 (UTC+5)

---

## Core Rules (Defined by Student)

1. **Rich Visuals & 3D Animated Web Demo**
   - Build a genuinely visual, interactive **3D animated web application** (Three.js / WebGL terrain, animated wildfire risk heatmap, live agent/drone movement, explored nodes, interactive camera & controls) rather than a static HTML landing page or plain console script.
   - Include live, concrete examples that demonstrate every algorithm visually step by step (`Input → Calculation → Output → Explanation`).

2. **Dual-Model Peer Audit (Antigravity + Claude Code)**
   - Use Claude Code (`claude` CLI, Pro subscription) not merely as a code generator, but as an **independent peer reviewer and auditor** at every major stage and after major deliverables.
   - Cross-check architecture, formulas, edge cases, UI/UX quality, and rubric compliance between both models; log all audit findings and fixes.

3. **100% Strict Compliance with Course Documents & Rubric**
   - Every requirement from `Final Project.docx`, `MiniAI_FPTopics.docx`, Course Syllabus (`AIF1303`), and the 100-point assessment rubric must be satisfied completely and verified against a formal checklist.
   - All 7 required deliverables must be produced and verified before submission.

4. **First-Year Friendly Explanations with Clean Academic Style**
   - Do **not** overcomplicate into a dense PhD research paper.
   - Explain concepts clearly using intuitive analogies, concrete small-number walkthroughs, and plain language suitable for a 1st-year undergraduate — while maintaining polished, formal academic structure and precision in English.

5. **Full Step-by-Step Logging, Version Control & AI Declaration**
   - Record every step: what was done, how it was done, which tools/models were used, and how outputs were verified (`context/WORKLOG.md` + `context/PROMPT_LOG.md`).
   - Preserve the full development history locally and in GitHub commits.
   - Deliver a complete, honest **AI Usage Declaration** matching the exact table format in the Syllabus Appendix.

6. **Course-First Sourcing & Verified Citations**
   - Derive definitions, notation, formulas, and frameworks primarily from the course lecture slides and practical guides in `C:\Users\sazmak\Desktop\AIF FINAL\`.
   - Whenever any external fact, formula, library detail, or domain statistic is used, verify it explicitly and cite the exact source.

7. **High Craft & Visual Polish**
   - Aim for top-tier visual aesthetics across the 3D Web UI, evaluation charts, Technical Report, and 5–7 slide presentation.
   - Flag proactively if any additional design tool, library, or skill would meaningfully improve quality.

8. **Persistent Context & Rules Directory**
   - Maintain a dedicated `context/` folder containing the project description, course-sourced formulas, working rules, rubric checklist, worklog, and prompt log so both AI models and the student always share a single source of truth.

---

## Additional Rules (Approved & Locked)

9. **100% Offline Reliability for Live Demo (Zero-CDN-Failure Rule)**
   - Bundle Three.js and all frontend assets locally inside `static/vendor/` so the 3D web app works flawlessly on `localhost` even with zero classroom Wi-Fi.
   - Include a smooth **2D Canvas Fallback toggle** in case the presentation laptop/projector has weak WebGL performance.

10. **Strict Timeboxing & Protected Sleep Window**
    - Lock hard stage milestones so 3D polish never starves the Technical Report, Slides, Video, or GitHub repo.
    - Target finishing all code, UI, report, and slides by ~03:30–04:00 so the student gets 5.5–6 hours of sleep before final video recording, GitHub push, and defense rehearsal (10:00–13:30).

11. **Oral Defense Ownership ("Understand Every Line" Rule)**
    - Keep Python algorithm modules (`src/ml_model.py`, `src/search.py`, `src/mdp.py`, `src/pipeline.py`) clean, concise, well-commented, and free of unnecessary magic so the student can confidently explain every line and formula during the 3-minute Q&A.
    - Maintain a bilingual (RU + EN) Defense & Q&A Cheat Sheet in `context/DEFENSE_GUIDE.md`.

12. **Deterministic Reproducibility & Demo Presets**
    - Every synthetic dataset and simulation run uses an explicit, configurable `random_seed` (matching Syllabus criterion: *reproducibility*).
    - Provide 3 one-click scenario presets (*Abai High Wind*, *Kostanay Dry Steppe*, *Akmola Sensor Noise*) guaranteed to produce crisp, dramatic visual contrasts during the 3–5 minute Live Demo.

13. **Visual QA Before Sign-Off**
    - Never ship UI or slides unseen: inspect the running 3D web app visually in a live browser and render every slide of the `.pptx` deck to images to verify layout, contrast, readability, and zero overlapping text.

14. **Transparent Synthetic Data Labeling (Academic Integrity Rule)**
    - Per Syllabus Section 8 & `MiniAI_FPTopics.docx`, explicitly label all steppe telemetry maps, probabilities, and rewards as **synthetic, domain-inspired simulation assumptions** — never claim simulated data is real emergency-services data.

15. **Clean Repository Hygiene (Protect Course Files)**
    - Keep the project isolated in `steppeguard-ai/` with a strict `.gitignore` so copyrighted university lecture slides/PDFs, `.venv`, and temp caches are never committed to GitHub.

16. **Smart Claude Pro Quota Management**
    - Batch Claude Code calls into high-value, well-scoped architecture audits, implementation passes, and final rubric audits (pointing Claude directly to `context/` files) to avoid hitting the 5-hour Pro message cap.

17. **7-Deliverable Pre-Flight Gate**
    - Before marking the project complete, verify all 7 deliverables + exact defense timing (2 min problem + 3–5 min live demo + 2 min algorithms + 3 min Q&A) in a final sign-off audit.
