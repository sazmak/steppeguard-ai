# Stage 1 Architecture Audit — Claude Sonnet Peer Review & Resolution

- **Auditor:** Claude Code CLI (`--model sonnet`, Pro subscription)
- **Date:** 2026-11-25 00:29 (UTC+5)
- **Files Audited:** `context/RULES.md`, `context/PROJECT_OVERVIEW.md`, `context/COURSE_REFERENCES.md`

## Key Findings & Design Upgrades Adopted

| Area | Claude Audit Finding | Action Taken in Architecture |
|---|---|---|
| **A\* Heuristic Strength** | With $\lambda = 8$, step costs reach ~9 while $h$ assumes 1.0, weakening A\* vs UCS contrast | Lowered default $\lambda = 3.5$, set $c_{\min} = \min_{v \text{ free}} c(v)$ from the live map (still strictly admissible & consistent), designed fire-corridor presets where BFS enters fire and A\* detours |
| **MDP Dead Action** | `Sensor Re-scan` is degenerate in a fully observed MDP | Renamed to **`Monitor`** (low-cost hold where fire may stochastically escalate or subside) |
| **MDP Dominance & Coupling** | `Aerial Retardant` could dominate everywhere; ML→A\*→MDP link needed tightening | Gated `Aerial Retardant` to consume `High → Low` resources (unavailable/heavily penalized at `Low`), parameterized `Direct Dispatch` using BFS exposure $E_{\text{direct}}$ and `Safe Detour` using A\* exposure $E_{\text{safe}}$, tuned rewards so $\ge 4$ distinct actions appear and $\gamma = 0.5$ flips at least one state's optimal action |
| **ML Hygiene** | Prevent leakage, numerical instability, and fake 100% accuracy | Added 3-way scene-grouped `train/val/test` split (select $\tau$ on `val`), stable sigmoid, L2 on weights only (not bias), `std >= 1e-8`, log-space GNB with variance floor, label noise + `dryness × wind` interaction term, Brier score & *"approximately calibrated"* wording |
| **Live Bayes Sensor** | Sensor must be conditionally independent of thermal-IR feature; re-plan A\* after update | Modeled sensor as an independent **Watchtower Visual/Smoke Alert** (TPR=0.90, FPR=0.10); live Bayes update immediately re-runs A\* and MDP |
| **Testing & Benchmarks** | Single map looks cherry-picked; test edge cases explicitly | Added `scripts/benchmark.py` (30 seeds, mean ± std, JSON + PNG plots) and full edge-case `pytest` suite (including 100-map A\*==UCS optimality property test) |
| **Kazakhstan AI Law Citation** | Verify Law No. 230-VIII ZRK citation from course files | Verified directly in `AI_Legal_Framework.pptx` Slides 2, 4, and 22 (*Adilet — Law of the Republic of Kazakhstan "On Artificial Intelligence", No. 230-VIII ZRK, 17 Nov 2025*) |
