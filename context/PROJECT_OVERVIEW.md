# SteppeGuard AI — Project Overview & Rubric Alignment

## 1. Identity
- **Project Name:** **SteppeGuard AI** — Wildfire Risk Intelligence & Response Decision System
- **Course:** AIF1303 — AI Fundamentals (QAIRU, Astana, 2026–2027)
- **Track:** 6B06101 *AI and ML*
- **Author:** Solo Student Project (100% individual ownership)
- **Language of Deliverables:** English (Defense prep guide in Russian + English)

## 2. Real-World Problem
Kazakhstan's steppe regions (e.g., Abai, Kostanay, Akmola) face rapidly spreading wildfires driven by dry vegetation and high winds. Emergency dispatchers must simultaneously:
1. Predict **where fire risk is highest** from noisy weather & satellite telemetry,
2. Plan a **fast yet safe response route** avoiding high-risk fire corridors, and
3. Decide **which sequential operational action** to take under uncertain wind/fire spread (*Direct Dispatch, Safe Detour, Aerial Retardant, Sensor Re-scan, Hold/Evacuate*).

## 3. Integrated Three-Algorithm Pipeline (3 Distinct Course Topics)
```
Steppe Sector Telemetry (Temp, Humidity, Wind, NDVI, Thermal IR)
        │
        ▼
[1] Classical Machine Learning (Week 8 — RO4)
    • Logistic Regression (primary) + Gaussian Naive Bayes (baseline), implemented cleanly in NumPy
    • Outputs calibrated fire probability map P(Fire | x) + ML metrics (Accuracy, Precision, Recall, F1, Confusion Matrix)
    • Optional live Bayesian sensor update (Week 6 bridge) when operator triggers a smoke sensor reading
        │
        ▼  (passes live fire-risk probability grid)
[2] Informed Heuristic Search (Week 2 — RO2)
    • Risk-Aware A* Search: f(n) = g(n) + h(n), where step cost incorporates terrain + ML fire probability
    • Head-to-head benchmark vs BFS and UCS (expanded nodes, path length, total risk exposure)
        │
        ▼  (passes sector risk + route exposure + resource level)
[3] Sequential Decision Making (Week 5 — RO3)
    • Markov Decision Process (MDP) solved via Value Iteration (Bellman Optimality Equation)
    • Computes optimal state values V*(s), action values Q*(s, a), and optimal policy π*(s)
    • Supports live sensitivity check across discount factor γ and wind stochasticity
```

## 4. Responsible AI & Legal Framing (Week 10 — AI Legal Framework)
- Aligned with **Kazakhstan Law No. 230-VIII ZRK (adopted 17 Nov 2025)** from `AI_Legal_Framework.pptx`:
  - **Risk Tier:** High-impact emergency support domain → requires transparency and auditability.
  - **Autonomy Tier:** Low/Human-in-the-Loop — SteppeGuard AI recommends routes and policies with full mathematical explanations; a human dispatcher always confirms the final decision.
  - **Data Governance:** Uses explicitly labeled synthetic simulation telemetry (zero personal data).

## 5. Rubric Mapping (100 Points Total)
| Criterion | Max | How SteppeGuard AI Earns Full Marks |
|---|---:|---|
| Correct Implementation of Three AI Topics | 30 | Pure, transparent Python/NumPy implementations of ML (LogReg + GNB), Risk-Aware A* (+ BFS/UCS), and MDP Value Iteration, chained end-to-end |
| Functionality and Stability | 20 | Deterministic local FastAPI server + offline-bundled 3D Three.js Web UI (+ 2D fallback) + 3 one-click presets |
| Testing and Results | 15 | Full `pytest` unit/integration/edge-case suite + ML Confusion Matrix/F1 + A* vs BFS vs UCS table + Bellman convergence curve |
| UI / UX | 10 | Interactive 3D animated steppe terrain with heatmap pillars, animated response unit, click-to-inspect math breakdown (`Input → Calculation → Output`) |
| Code Quality, GitHub & Documentation | 10 | Modular `src/`, `tests/`, `docs/`, `context/`, clear `README.md`, clean git history |
| Originality & Practical Value | 5 | Kazakhstan-relevant wildfire AI/ML decision support platform with 3D simulation & KZ AI Law framing |
| Project Defense & Individual Understanding | 10 | Clear 1st-year-friendly analogies, live walkthrough script, bilingual Q&A prep guide |

## 6. Required Deliverables Checklist (7 Items)
- [ ] 1. Working Application & Live/Local 3D Demo (`app.py` + Three.js frontend)
- [ ] 2. GitHub Repository (clean commits, `.gitignore`, `README.md`)
- [ ] 3. Technical Report (`docs/TECHNICAL_REPORT.md` + formatted `.docx`/`.pdf`)
- [ ] 4. 5–7 Slide Presentation (`docs/SteppeGuard_Presentation.pptx`)
- [ ] 5. 2–3 Minute Demo Video (recording script + student screen recording)
- [ ] 6. AI Usage Declaration (`docs/AI_USAGE_DECLARATION.md` + `.docx`, exact Syllabus Appendix table)
- [ ] 7. Team Contribution Statement (`docs/TEAM_CONTRIBUTION_STATEMENT.md`, Solo 100%)
