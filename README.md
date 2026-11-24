# SteppeGuard AI — Wildfire Risk Intelligence & Response Decision System

> **Live 3D Demo:** [https://steppeguard-ai.vercel.app](https://steppeguard-ai.vercel.app)  
> **GitHub Repository:** [https://github.com/sazmak/steppeguard-ai](https://github.com/sazmak/steppeguard-ai)  
> **Course:** AIF1303 — AI Fundamentals (QAIRU, Astana, 2026–2027)  
> **Program:** 6B06101 *AI and ML*  
> **Author:** Oral Sanzhar (Stream 1, Practice 4 — Solo Project)  
> **Demo Mode:** Live HTTPS Deployment + 100% Offline Local 3D WebGL (Three.js) & 2D Fallback

![SteppeGuard AI 3D Live Demo](results/fig4_3d_live_demo.png)

---

## 1. Problem Overview
Kazakhstan's steppe regions (Abai, Kostanay, Akmola) face fast-moving wildfires driven by dry vegetation and strong winds. Emergency dispatchers must answer three tightly coupled questions simultaneously:
1. **Where is wildfire risk highest?** *(Classical Machine Learning + Bayesian Sensor Update)*
2. **What is the safest and most efficient route to the target settlement?** *(Risk-Aware A\* Search)*
3. **What operational action maximizes long-term safety under uncertain wind?** *(MDP Value Iteration)*

**SteppeGuard AI** integrates three distinct AI Fundamentals topics into one live, reproducible pipeline:

```text
Steppe Telemetry (5 features)
   ──► [Topic 1: Classical ML — Logistic Regression vs Gaussian NB (Week 8)]
       (+ Live Watchtower Smoke Sensor Bayesian Update — Week 6)
   ──► [Topic 2: Informed Search — Risk-Aware A* vs UCS vs BFS (Week 2)]
   ──► [Topic 3: Sequential Decisions — MDP Value Iteration (Week 5)]
   ──► Human-in-the-Loop Dispatcher Gate (Kazakhstan AI Law No. 230-VIII ZRK)
```

> **Transparency Notice (Syllabus Section 8 & `MiniAI_FPTopics.docx`):** All weather/satellite telemetry maps, transition probabilities, and rewards are **synthetic, domain-inspired simulation data** designed for reproducible classroom evaluation. They are not real Ministry of Emergency Situations operational records.

---

## 2. Quick Start (Runs 100% Offline)

```bash
# 1. Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1

# 2. Install runtime dependencies (or requirements-dev.txt for tests/benchmarks/docs)
pip install -r requirements-dev.txt

# 3. Run full automated test suite (19 unit, property & API tests)
pytest -v

# 4. (Optional) Regenerate 30-seed benchmarks and figures in results/
python scripts/benchmark.py

# 5. Launch the 3D Interactive Web Application
python app.py
# Open http://127.0.0.1:8000 in any modern browser (zero internet required!)
```

---

## 3. Sample Input & Output

**Example API / Pipeline Run (`preset_id="abai_high_wind"`, `seed=42`, `λ=3.5`, `γ=0.90`):**

- **Input Sector `(5, 4)` Telemetry:** `Temp = 40.9°C`, `Humidity = 17%`, `Wind = 35 km/h`, `Dryness = 0.75`, `Thermal = 0.85`
- **Topic 1 (Logistic Regression):**
  - `z = w^T x_std + b = +8.21` → `P(Fire | x) = σ(z) ≈ 99.97%` (`ALERT` at seed-42 validation-selected `τ = 0.225`; 30-seed mean `τ = 0.353 ± 0.05`)
- **Topic 2 (Risk-Aware A\* vs UCS vs BFS — single seed=42 run):**
  - **A\*:** `44` expanded nodes | Optimal Cost `18.06` | Fire Risk Exposure **`0.06`**
  - **UCS:** `82` expanded nodes | Optimal Cost `18.06` | Fire Risk Exposure `0.06`
  - **BFS:** `71` expanded nodes | Cost `37.48` | Fire Risk Exposure **`7.44`** *(Single-run: A\* cuts fire exposure by **99.2%** and expands **46.3% fewer nodes** than UCS; across 30 seeds: **-98.3%** exposure and **-48.7%** nodes!)*
- **Topic 3 (MDP Value Iteration — 17 sweeps to `θ = 10⁻⁶`):**
  - Active State: `High Risk | High Resources` → Optimal Policy: **`Aerial Retardant`** (`V*(s) = 23.90`)
  - Switching Resources to `Low` flips policy to **`Evacuate / Hold`** (aircraft resource gating).
  - Switching presets gives three distinct actions: **Akmola → `Direct Dispatch`**, **Kostanay → `Safe Detour`**, **Abai → `Aerial Retardant`**.

---

## 4. Quantitative Benchmark Summary (30 Independent Seeds)

| Module | Metric | Result (Mean ± Std) | Key Takeaway |
|---|---|---:|---|
| **Topic 1: LogReg (Val-tuned τ)** | Recall / F1 / Brier | `86.8% ± 4.8%` / `80.6% ± 3.1%` / `0.085` | Recall jumps from ~78% (`τ=0.50`) to ~87%; Brier `0.085` vs `~0.22` baseline |
| **Topic 1: Gaussian NB (Baseline)** | Recall / F1 / Brier | `87.3% ± 4.8%` / `79.9% ± 3.3%` / `0.088` | Comparable F1 within 1 std; LogReg exposes direct interpretable weights |
| **Topic 2: Abai High Wind** | A\* vs UCS Nodes | `41.5 ± 5.0` vs `80.8 ± 2.5` | **-48.7% nodes expanded** at **identical optimal cost (`17.96`)** |
| **Topic 2: Abai High Wind** | A\* vs BFS Exposure | `0.12 ± 0.06` vs `7.20 ± 0.17` | **-98.3% cumulative wildfire exposure** vs unweighted BFS |
| **Topic 3: MDP Value Iteration** | Sweeps / γ-Flip | `17 sweeps` (`θ=10⁻⁶`) | `Med/HighRes` flips `Aerial Retardant` (`γ=0.50`) → `Safe Detour` (`γ≥0.80`) |

---

## 5. Repository Structure

```text
steppeguard-ai/
├── app.py                              # FastAPI server & REST API (/api/run, /api/sensor, /api/benchmarks)
├── requirements.txt                    # Exact Python dependencies
├── src/
│   ├── config.py                       # Reproducible hyperparameters & terrain constants
│   ├── data.py                         # Synthetic scene-grouped dataset & 3 Kazakhstan presets
│   ├── ml_model.py                     # Pure-NumPy StandardScaler, Logistic Regression, Gaussian NB & Bayes
│   ├── search.py                       # Risk-Aware A*, UCS, and BFS with admissible Manhattan heuristic
│   ├── mdp.py                          # 8-state 5-action MDP & Bellman Value Iteration + γ-sensitivity
│   └── pipeline.py                     # End-to-end ML -> Bayes -> A* -> MDP orchestration
├── static/
│   ├── index.html                      # 3-tab Tactical Command Center UI
│   ├── styles.css                      # Offline dark glassmorphism styling
│   ├── app.js                          # Three.js 3D terrain engine + 2D Canvas fallback
│   └── vendor/three.min.js             # Local Three.js bundle (zero CDN / 100% offline)
├── tests/                              # 19 automated unit, property, counterfactual & API tests
├── scripts/
│   ├── benchmark.py                    # 30-seed statistical evaluation & matplotlib figures
│   └── build_docs.py                   # Automated generator for .docx reports & 7-slide .pptx
├── results/                            # Benchmark JSON, matplotlib plots & 3D screenshot
├── docs/                               # Technical Report, 7-Slide Deck, AI Declaration, Contribution Statement
└── context/                            # Governance rules, course formulas, Claude audits, worklog & defense guide
```

---

## 6. Deliverables Index
- **Working 3D Application:** `python app.py` → `http://127.0.0.1:8000`
- **Technical Report:** [`docs/TECHNICAL_REPORT.md`](docs/TECHNICAL_REPORT.md) & [`docs/SteppeGuard_Technical_Report.docx`](docs/SteppeGuard_Technical_Report.docx)
- **Presentation (7 Slides):** [`docs/SteppeGuard_Presentation.pptx`](docs/SteppeGuard_Presentation.pptx)
- **AI Usage Declaration:** [`docs/AI_USAGE_DECLARATION.md`](docs/AI_USAGE_DECLARATION.md) & [`docs/AI_Usage_Declaration.docx`](docs/AI_Usage_Declaration.docx)
- **Contribution Statement:** [`docs/TEAM_CONTRIBUTION_STATEMENT.md`](docs/TEAM_CONTRIBUTION_STATEMENT.md) & [`docs/Team_Contribution_Statement.docx`](docs/Team_Contribution_Statement.docx)
- **Development Logs & Peer Audits:** [`context/WORKLOG.md`](context/WORKLOG.md), [`context/PROMPT_LOG.md`](context/PROMPT_LOG.md), [`context/AUDIT_1_ARCHITECTURE.md`](context/AUDIT_1_ARCHITECTURE.md), [`context/AUDIT_2_BACKEND.md`](context/AUDIT_2_BACKEND.md), [`context/AUDIT_3_FRONTEND.md`](context/AUDIT_3_FRONTEND.md)
