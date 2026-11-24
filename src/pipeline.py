"""End-to-end SteppeGuard AI Pipeline: ML -> (Bayes) -> Risk-Aware A* -> MDP.

Strictly chains all three course algorithms so every module feeds the next:
1. Classical ML (Week 8) predicts fire probabilities P(Fire | x) for every sector.
   Optional live Watchtower Sensor Alert applies exact Bayesian belief updating (Week 6).
2. Risk-Aware A* (Week 2) uses P(Fire | x) as dynamic terrain hazard cost and is
   benchmarked head-to-head against BFS and UCS.
3. MDP Value Iteration (Week 5) ingests corridor fire risk, wind, BFS direct exposure,
   and A* safe exposure to compute the optimal sequential policy pi*(s).
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.config import Config, FEATURE_NAMES, TERRAIN_NAMES
from src.data import PRESET_METADATA, SectorMap, make_dataset, make_preset_map
from src.mdp import build_mdp, gamma_sensitivity, value_iteration
from src.ml_model import (
    GaussianNBScratch,
    LogisticRegressionScratch,
    StandardScaler,
    bayes_sensor_update,
    evaluate_predictions,
    explain_cell_gnb,
    explain_cell_ml,
    predict_grid,
    select_threshold_on_val,
)
from src.search import astar_search, bfs_search, compute_step_costs, ucs_search


def risk_to_state_index(
    corridor_risk: float,
    tau: float,
    resource_level: str,
) -> Tuple[int, str]:
    """Map continuous corridor/hotspot fire probability into discrete MDP state index.

    Thresholds are explicitly anchored to the validation-selected ML threshold tau:
    - Low Risk:    corridor_risk < tau
    - Medium Risk: tau <= corridor_risk < min(0.85, tau + 0.30)
    - High Risk:   corridor_risk >= min(0.85, tau + 0.30)
    """
    high_cut = min(0.85, float(tau) + 0.30)
    if corridor_risk < tau:
        risk_idx, risk_label = 0, "Low"
    elif corridor_risk < high_cut:
        risk_idx, risk_label = 1, "Medium"
    else:
        risk_idx, risk_label = 2, "High"

    res_low = 1 if resource_level.lower().startswith("l") else 0
    return risk_idx * 2 + res_low, risk_label


class SteppeGuardEngine:
    """Stateful, reproducible engine caching the trained ML models on startup."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.dataset = make_dataset(seed=self.config.seed, n_scenes=30, cells_per_scene=100)

        # Fit StandardScaler strictly on X_train (zero leakage!)
        self.scaler = StandardScaler().fit(self.dataset["X_train"])
        X_tr = self.scaler.transform(self.dataset["X_train"])
        X_va = self.scaler.transform(self.dataset["X_val"])
        X_te = self.scaler.transform(self.dataset["X_test"])

        # Train primary Logistic Regression & Gaussian Naive Bayes baseline
        self.lr_model = LogisticRegressionScratch(
            learning_rate=self.config.lr_learning_rate,
            epochs=self.config.lr_epochs,
            l2_lambda=self.config.lr_l2_lambda,
        ).fit(X_tr, self.dataset["y_train"])

        self.gnb_model = GaussianNBScratch().fit(X_tr, self.dataset["y_train"])

        # Select safety-first threshold tau strictly on validation split for BOTH models
        lr_val_probs = self.lr_model.predict_proba(X_va)
        gnb_val_probs = self.gnb_model.predict_proba(X_va)
        self.val_tau, self.lr_val_metrics = select_threshold_on_val(
            self.dataset["y_val"], lr_val_probs, fn_cost=2.0, fp_cost=1.0
        )
        self.val_tau_gnb, self.gnb_val_metrics = select_threshold_on_val(
            self.dataset["y_val"], gnb_val_probs, fn_cost=2.0, fp_cost=1.0
        )

        # Evaluate both models honestly on held-out test split
        lr_test_probs = self.lr_model.predict_proba(X_te)
        gnb_test_probs = self.gnb_model.predict_proba(X_te)

        self.ml_evaluation: Dict[str, Any] = {
            "split_sizes": {
                "train": int(len(self.dataset["y_train"])),
                "val": int(len(self.dataset["y_val"])),
                "test": int(len(self.dataset["y_test"])),
            },
            "selected_tau": self.val_tau,
            "selected_tau_gnb": self.val_tau_gnb,
            "logistic_regression": evaluate_predictions(self.dataset["y_test"], lr_test_probs, tau=self.val_tau),
            "logistic_regression_default_050": evaluate_predictions(self.dataset["y_test"], lr_test_probs, tau=0.50),
            "gaussian_nb": evaluate_predictions(self.dataset["y_test"], gnb_test_probs, tau=self.val_tau_gnb),
            "feature_weights": {
                name: round(float(w), 4)
                for name, w in zip(FEATURE_NAMES, self.lr_model.weights_)
            },
            "bias": round(float(self.lr_model.bias_), 4),
            "loss_curve": [round(float(v), 5) for v in self.lr_model.loss_history_[::10]],
        }

    def run_pipeline(
        self,
        preset_id: str = "abai_high_wind",
        seed: Optional[int] = None,
        risk_lambda: Optional[float] = None,
        gamma: Optional[float] = None,
        tau: Optional[float] = None,
        wind_override: Optional[float] = None,
        dryness_boost: float = 0.0,
        resource_level: Optional[str] = None,
        model_choice: str = "logistic_regression",
        sensor_events: Optional[List[Dict[str, Any]]] = None,
        extra_obstacles: Optional[List[Tuple[int, int]]] = None,
        inspect_cell: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Run the full integrated AI/ML -> A* -> MDP pipeline and return JSON-safe results."""
        use_seed = self.config.seed if seed is None else int(seed)
        use_lambda = self.config.risk_lambda if risk_lambda is None else float(risk_lambda)
        use_gamma = self.config.gamma if gamma is None else float(gamma)
        default_tau = self.val_tau_gnb if model_choice == "gaussian_nb" else self.val_tau
        use_tau = default_tau if tau is None else float(tau)

        smap: SectorMap = make_preset_map(
            preset_id=preset_id,
            seed=use_seed,
            grid_size=self.config.grid_size,
            wind_override=wind_override,
            dryness_boost=float(dryness_boost),
        )

        # Apply optional interactive obstacle overrides (never blocking start/goal)
        if extra_obstacles:
            for r, c in extra_obstacles:
                if 0 <= r < smap.rows and 0 <= c < smap.cols and (r, c) not in (smap.start, smap.goal):
                    smap.obstacles[r, c] = True
                    smap.terrain[r, c] = 3

        # --- TOPIC 1: Classical ML Fire Probability Prediction ---
        active_model = self.gnb_model if model_choice == "gaussian_nb" else self.lr_model
        base_risk_grid = predict_grid(active_model, self.scaler, smap.features)
        risk_grid = base_risk_grid.copy()

        # Optional Week 6 Bayesian Watchtower Sensor Update(s)
        bayes_logs: List[Dict[str, Any]] = []
        if sensor_events:
            for ev in sensor_events:
                er, ec = int(ev["row"]), int(ev["col"])
                alert = bool(ev.get("alert", True))
                if 0 <= er < smap.rows and 0 <= ec < smap.cols and not smap.obstacles[er, ec]:
                    upd = bayes_sensor_update(
                        prior=float(risk_grid[er, ec]),
                        alert=alert,
                        tpr=self.config.sensor_tpr,
                        fpr=self.config.sensor_fpr,
                    )
                    upd["row"] = er
                    upd["col"] = ec
                    risk_grid[er, ec] = upd["posterior"]
                    bayes_logs.append(upd)

        # --- TOPIC 2: Risk-Aware A* vs UCS vs BFS ---
        step_costs = compute_step_costs(
            terrain=smap.terrain,
            risk_grid=risk_grid,
            obstacles=smap.obstacles,
            risk_lambda=use_lambda,
            terrain_costs=self.config.terrain_costs,
        )
        res_bfs = bfs_search(step_costs, risk_grid, smap.obstacles, smap.start, smap.goal)
        res_ucs = ucs_search(step_costs, risk_grid, smap.obstacles, smap.start, smap.goal)
        res_astar = astar_search(step_costs, risk_grid, smap.obstacles, smap.start, smap.goal)

        # --- TOPIC 3: MDP Value Iteration coupled to ML risk + BFS/A* exposure ---
        # Operational corridor risk = mean ML fire risk along the direct BFS corridor
        # (measuring severity of the fire front lying directly between Base and Settlement).
        if res_bfs.found and len(res_bfs.path) > 1:
            corridor_risk = float(np.mean([risk_grid[r, c] for r, c in res_bfs.path[1:]]))
        else:
            free_risks = risk_grid[~smap.obstacles]
            top_k = max(1, min(10, free_risks.size))
            corridor_risk = float(np.mean(np.sort(free_risks)[-top_k:]))

        use_res = resource_level or smap.initial_resource
        active_state_idx, active_risk_label = risk_to_state_index(corridor_risk, use_tau, use_res)

        mdp = build_mdp(
            wind_level=smap.wind_level,
            e_direct=res_bfs.total_exposure if res_bfs.found else 9.0,
            e_safe=res_astar.total_exposure if res_astar.found else 9.0,
            route_found=res_astar.found,
            bfs_steps=max(1, res_bfs.steps),
            astar_steps=max(1, res_astar.steps),
        )
        vi_res = value_iteration(mdp, gamma=use_gamma, theta=self.config.theta, max_iters=self.config.max_vi_iters)
        sensitivity = gamma_sensitivity(mdp, gammas=(0.50, 0.80, 0.90, 0.95), theta=self.config.theta)

        # Pick an informative cell to inspect in the Math Inspector (default: hottest cell on BFS path)
        if inspect_cell is not None:
            ir, ic = int(inspect_cell[0]), int(inspect_cell[1])
        elif res_bfs.found and len(res_bfs.path) > 2:
            ir, ic = max(res_bfs.path[1:-1], key=lambda rc: float(risk_grid[rc[0], rc[1]]))
        else:
            ir, ic = (smap.rows // 2, smap.cols // 2)

        ir = int(np.clip(ir, 0, smap.rows - 1))
        ic = int(np.clip(ic, 0, smap.cols - 1))
        if model_choice == "gaussian_nb":
            cell_ml_explain = explain_cell_gnb(self.gnb_model, self.scaler, smap.features[ir, ic], use_tau)
        else:
            cell_ml_explain = explain_cell_ml(self.lr_model, self.scaler, smap.features[ir, ic], use_tau)
        astar_node_info = res_astar.node_trace.get((ir, ic))

        # Assemble clean grid payload for 3D Three.js + 2D Fallback frontend
        cells_payload: List[List[Dict[str, Any]]] = []
        for r in range(smap.rows):
            row_list = []
            for c in range(smap.cols):
                t_id = int(smap.terrain[r, c])
                row_list.append(
                    {
                        "row": r,
                        "col": c,
                        "terrain_id": t_id,
                        "terrain_name": TERRAIN_NAMES[t_id],
                        "obstacle": bool(smap.obstacles[r, c]),
                        "elevation": round(float(smap.elevation[r, c]), 3),
                        "base_risk": round(float(base_risk_grid[r, c]), 4),
                        "risk": round(float(risk_grid[r, c]), 4),
                        "alert": bool(risk_grid[r, c] >= use_tau),
                        "step_cost": None if smap.obstacles[r, c] else round(float(step_costs[r, c]), 3),
                        "features": {
                            name: round(float(smap.features[r, c, idx]), 3)
                            for idx, name in enumerate(FEATURE_NAMES)
                        },
                        "astar_node": res_astar.node_trace.get((r, c)),
                    }
                )
            cells_payload.append(row_list)

        exposure_reduction_pct = 0.0
        if res_bfs.found and res_astar.found and res_bfs.total_exposure > 1e-6:
            exposure_reduction_pct = round(
                100.0 * (res_bfs.total_exposure - res_astar.total_exposure) / res_bfs.total_exposure, 1
            )

        return {
            "meta": {
                "preset_id": smap.preset_id,
                "title": smap.title,
                "region": smap.region,
                "description": smap.description,
                "seed": use_seed,
                "rows": smap.rows,
                "cols": smap.cols,
                "start": list(smap.start),
                "goal": list(smap.goal),
                "wind_level": round(float(smap.wind_level), 3),
                "resource_level": use_res,
                "risk_lambda": round(use_lambda, 2),
                "tau": round(use_tau, 3),
                "gamma": round(use_gamma, 3),
                "model_choice": model_choice,
                "synthetic_data_notice": (
                    "Synthetic domain-inspired simulation telemetry (AIF1303). "
                    "Human-in-the-Loop Decision Support per RK AI Law No. 230-VIII ZRK."
                ),
            },
            "grid": cells_payload,
            "ml": {
                "evaluation": self.ml_evaluation,
                "corridor_risk": round(corridor_risk, 4),
                "corridor_risk_band": active_risk_label,
                "bayes_sensor_updates": bayes_logs,
            },
            "search": {
                "astar": res_astar.to_dict(),
                "ucs": res_ucs.to_dict(),
                "bfs": res_bfs.to_dict(),
                "summary": {
                    "exposure_reduction_vs_bfs_pct": exposure_reduction_pct,
                    "nodes_saved_vs_ucs": int(res_ucs.expanded_count - res_astar.expanded_count),
                    "astar_equals_ucs_cost": bool(
                        res_astar.found
                        and res_ucs.found
                        and abs(res_astar.total_cost - res_ucs.total_cost) < 1e-6
                    ),
                },
            },
            "mdp": {
                **vi_res.to_dict(mdp, active_state_idx),
                "gamma_sensitivity": sensitivity,
            },
            "math_inspector": {
                "inspected_cell": [ir, ic],
                "ml_step": cell_ml_explain,
                "search_step": {
                    "cell": [ir, ic],
                    "terrain_cost": None if smap.obstacles[ir, ic] else round(
                        float(self.config.terrain_costs.get(int(smap.terrain[ir, ic]), 1.0)), 2
                    ),
                    "ml_risk": round(float(risk_grid[ir, ic]), 4),
                    "risk_lambda": round(use_lambda, 2),
                    "step_cost": None if smap.obstacles[ir, ic] else round(float(step_costs[ir, ic]), 4),
                    "astar_trace": astar_node_info,
                    "formula": (
                        "Obstacle (impassable)"
                        if smap.obstacles[ir, ic]
                        else f"c({ir},{ic}) = {self.config.terrain_costs.get(int(smap.terrain[ir, ic]), 1.0):.2f} "
                             f"+ {use_lambda:.1f} × {risk_grid[ir, ic]:.3f} = {step_costs[ir, ic]:.3f}"
                    ),
                },
                "mdp_step": {
                    "active_state": mdp.state_names[active_state_idx],
                    "recommended_action": vi_res.policy_names[active_state_idx],
                    "v_star": round(float(vi_res.V[active_state_idx]), 3),
                    "formula": (
                        f"V*(s) = max_a Q*(s, a) = Q*({mdp.short_names[active_state_idx]}, "
                        f"{vi_res.policy_names[active_state_idx]}) = {vi_res.V[active_state_idx]:.2f}"
                    ),
                },
            },
        }
