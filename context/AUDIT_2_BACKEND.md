# Stage 2 Backend Code & Math Audit — Claude Sonnet Peer Review & Resolution

- **Auditor:** Claude Code CLI (`--model sonnet`, Pro subscription)
- **Date:** 2026-11-25 00:41 (UTC+5)
- **Verdict:** **0 P0 bugs** (all core ML, A\*, Bayes, and Bellman Value Iteration formulas verified mathematically correct); **3 P1 findings** fixed immediately prior to Pre-Visual Checkpoint.

## P1 Fixes Applied & Verified

| # | Claude Finding | Fix Applied | Verification |
|---|---|---|---|
| 1 | **Weak/Saturating Search→MDP Coupling:** `/5` normalization saturated `d_risk` and `Direct Dispatch` never won; comment on $\gamma$-flip was inaccurate | Normalized route exposure by **per-step mean risk** (`e_direct / bfs_steps`, `e_safe / astar_steps`), tuned `Direct Dispatch` so clean direct corridors prefer `Direct Dispatch` while high-exposure corridors flip to `Safe Detour`, corrected $\gamma$-flip documentation (`Med/HighRes`: `Aerial Retardant` at $\gamma=0.50$ → `Safe Detour` at $\gamma \ge 0.80$) | Added `test_counterfactual_exposure_coupling_flips_policy` and verified all 3 presets yield 3 distinct actions (`Direct Dispatch` / `Safe Detour` / `Aerial Retardant`) |
| 2 | **`gaussian_nb` Math Inspector mismatch:** Switching to GNB still ran LR's explainer and LR's $\tau$ | Added `explain_cell_gnb(...)` (per-feature log-likelihood ratios) and tuned GNB's own validation $\tau_{\text{gnb}}$ on `X_val` | Added `test_gaussian_nb_mode_matches_math_inspector` asserting grid risk == inspector risk |
| 3 | **Honest ML Reporting & Brier Baseline:** Avoid unproven "calibrated" label; frame $\tau$ gain as Recall boost (+8–9%); add Brier baseline | Added `brier_baseline = prev * (1 - prev)` (~0.22 vs model 0.085), removed overclaiming wording in `pipeline.py`, updated report framing so LR vs GNB comparison is statistically honest | Checked in `benchmark_summary.json` and `ml_model.py` |

## Additional P2 & Visual QA Improvements Applied
- Raised L2 regularization `lr_l2_lambda` from `0.05` to `1.0` so L2 regularization is active.
- Made `_set_transitions` compute probability-weighted rewards if duplicate next-states ever occur.
- Fixed text contrast in `results/fig1_ml_evaluation.png` Confusion Matrix (`cmap="Blues"` with adaptive white/dark text) and legend position in `results/fig3_mdp_convergence.png`.
- Expanded test suite to cover blocked maps (`found=False`), `alert=False`, `/api/sensor` 400 validation, `/api/benchmarks` 200, and 50-grid heuristic admissibility property testing.
