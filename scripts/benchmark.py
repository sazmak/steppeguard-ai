"""Reproducible 30-seed Benchmark & Publication-Quality Figure Generator.

Evaluates all three course topics quantitatively (Addressing Audit #1 & Rubric 15 pts):
1. Classical ML (30 seeds): Logistic Regression vs Gaussian Naive Bayes
   (Accuracy, Precision, Recall, F1, Brier Score — mean +/- std) + Confusion Matrix.
2. Heuristic Search (30 seeds across presets): Risk-Aware A* vs UCS vs BFS
   (Expanded Nodes, Weighted Cost, Fire Risk Exposure — mean +/- std).
3. MDP Value Iteration: Bellman convergence curve (delta_k vs iteration) and
   discount-factor gamma sensitivity policy comparison.

Outputs saved to results/benchmark_summary.json and results/*.png.
"""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import Config, FEATURE_NAMES
from src.data import PRESET_METADATA, make_dataset, make_preset_map
from src.mdp import build_mdp, gamma_sensitivity, value_iteration
from src.ml_model import (
    GaussianNBScratch,
    LogisticRegressionScratch,
    StandardScaler,
    evaluate_predictions,
    predict_grid,
    select_threshold_on_val,
)
from src.search import astar_search, bfs_search, compute_step_costs, ucs_search

RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _mean_std(vals: List[float]) -> Dict[str, float]:
    arr = np.asarray(vals, dtype=np.float64)
    return {
        "mean": round(float(arr.mean()), 4),
        "std": round(float(arr.std(ddof=1)) if len(arr) > 1 else 0.0, 4),
    }


def run_benchmarks(n_seeds: int = 30) -> Dict[str, Any]:
    cfg = Config()
    seeds = list(range(100, 100 + n_seeds))

    lr_metrics_all: Dict[str, List[float]] = {k: [] for k in ("accuracy", "precision", "recall", "f1", "brier_score")}
    lr_def_all: Dict[str, List[float]] = {k: [] for k in ("accuracy", "precision", "recall", "f1", "brier_score")}
    gnb_metrics_all: Dict[str, List[float]] = {k: [] for k in ("accuracy", "precision", "recall", "f1", "brier_score")}
    taus: List[float] = []

    search_stats: Dict[str, Dict[str, Dict[str, List[float]]]] = {
        pid: {
            algo: {"expanded": [], "cost": [], "exposure": [], "steps": []}
            for algo in ("astar", "ucs", "bfs")
        }
        for pid in PRESET_METADATA
    }

    # Reference model (seed=42) for Confusion Matrix & Feature Weights plots
    ref_ds = make_dataset(seed=cfg.seed, n_scenes=30, cells_per_scene=100)
    ref_scaler = StandardScaler().fit(ref_ds["X_train"])
    ref_lr = LogisticRegressionScratch(cfg.lr_learning_rate, cfg.lr_epochs, cfg.lr_l2_lambda).fit(
        ref_scaler.transform(ref_ds["X_train"]), ref_ds["y_train"]
    )
    ref_tau, _ = select_threshold_on_val(
        ref_ds["y_val"], ref_lr.predict_proba(ref_scaler.transform(ref_ds["X_val"]))
    )
    ref_test_eval = evaluate_predictions(
        ref_ds["y_test"], ref_lr.predict_proba(ref_scaler.transform(ref_ds["X_test"])), tau=ref_tau
    )

    for s in seeds:
        ds = make_dataset(seed=s, n_scenes=30, cells_per_scene=100)
        scaler = StandardScaler().fit(ds["X_train"])
        X_tr = scaler.transform(ds["X_train"])
        X_va = scaler.transform(ds["X_val"])
        X_te = scaler.transform(ds["X_test"])

        lr = LogisticRegressionScratch(cfg.lr_learning_rate, cfg.lr_epochs, cfg.lr_l2_lambda).fit(X_tr, ds["y_train"])
        gnb = GaussianNBScratch().fit(X_tr, ds["y_train"])

        tau_val, _ = select_threshold_on_val(ds["y_val"], lr.predict_proba(X_va))
        taus.append(tau_val)

        m_lr = evaluate_predictions(ds["y_test"], lr.predict_proba(X_te), tau=tau_val)
        m_lr_def = evaluate_predictions(ds["y_test"], lr.predict_proba(X_te), tau=0.50)
        m_gnb = evaluate_predictions(ds["y_test"], gnb.predict_proba(X_te), tau=tau_val)

        for k in lr_metrics_all:
            lr_metrics_all[k].append(m_lr[k])
            lr_def_all[k].append(m_lr_def[k])
            gnb_metrics_all[k].append(m_gnb[k])

        for pid in PRESET_METADATA:
            smap = make_preset_map(preset_id=pid, seed=s, grid_size=cfg.grid_size)
            rgrid = predict_grid(lr, scaler, smap.features)
            cgrid = compute_step_costs(smap.terrain, rgrid, smap.obstacles, risk_lambda=cfg.risk_lambda)

            for name, fn in (("astar", astar_search), ("ucs", ucs_search), ("bfs", bfs_search)):
                res = fn(cgrid, rgrid, smap.obstacles, smap.start, smap.goal)
                if res.found:
                    search_stats[pid][name]["expanded"].append(float(res.expanded_count))
                    search_stats[pid][name]["cost"].append(float(res.total_cost))
                    search_stats[pid][name]["exposure"].append(float(res.total_exposure))
                    search_stats[pid][name]["steps"].append(float(res.steps))

    # MDP Convergence & Gamma Sensitivity on Kostanay Dry Steppe (seed=42)
    k_map = make_preset_map("kostanay_dry_steppe", seed=cfg.seed, grid_size=cfg.grid_size)
    k_risk = predict_grid(ref_lr, ref_scaler, k_map.features)
    k_cost = compute_step_costs(k_map.terrain, k_risk, k_map.obstacles, risk_lambda=cfg.risk_lambda)
    k_bfs = bfs_search(k_cost, k_risk, k_map.obstacles, k_map.start, k_map.goal)
    k_astar = astar_search(k_cost, k_risk, k_map.obstacles, k_map.start, k_map.goal)
    k_mdp = build_mdp(
        k_map.wind_level,
        k_bfs.total_exposure,
        k_astar.total_exposure,
        bfs_steps=max(1, k_bfs.steps),
        astar_steps=max(1, k_astar.steps),
    )
    k_vi = value_iteration(k_mdp, gamma=cfg.gamma, theta=cfg.theta)
    k_sens = gamma_sensitivity(k_mdp, gammas=(0.50, 0.80, 0.90, 0.95), theta=cfg.theta)

    summary: Dict[str, Any] = {
        "n_seeds": n_seeds,
        "ml": {
            "val_tau": _mean_std(taus),
            "logistic_regression_tuned": {k: _mean_std(v) for k, v in lr_metrics_all.items()},
            "logistic_regression_tau_050": {k: _mean_std(v) for k, v in lr_def_all.items()},
            "gaussian_nb_tuned": {k: _mean_std(v) for k, v in gnb_metrics_all.items()},
            "reference_seed_42_confusion_matrix": ref_test_eval["confusion_matrix"],
            "reference_seed_42_reliability": ref_test_eval["reliability_bins"],
            "reference_feature_weights": {
                n: round(float(w), 4) for n, w in zip(FEATURE_NAMES, ref_lr.weights_)
            },
        },
        "search": {
            pid: {
                algo: {metric: _mean_std(vals) for metric, vals in mdict.items()}
                for algo, mdict in adict.items()
            }
            for pid, adict in search_stats.items()
        },
        "mdp": {
            "scenario": "kostanay_dry_steppe (seed=42)",
            "gamma": cfg.gamma,
            "iterations": k_vi.iterations,
            "converged": k_vi.converged,
            "deltas": [round(float(d), 6) for d in k_vi.deltas],
            "gamma_sensitivity": k_sens,
        },
    }

    (RESULTS_DIR / "benchmark_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    _generate_plots(summary, ref_lr)
    return summary


def _generate_plots(summary: Dict[str, Any], ref_lr: LogisticRegressionScratch) -> None:
    plt.rcParams.update({
        "figure.facecolor": "#0f172a",
        "axes.facecolor": "#1e293b",
        "axes.edgecolor": "#475569",
        "axes.labelcolor": "#e2e8f0",
        "xtick.color": "#cbd5e1",
        "ytick.color": "#cbd5e1",
        "text.color": "#f8fafc",
        "grid.color": "#334155",
        "font.size": 10,
    })

    # 1. ML Model Comparison (30-seed mean +/- std) + Confusion Matrix
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=180)
    metrics = ["accuracy", "precision", "recall", "f1"]
    labels = ["Accuracy", "Precision", "Recall", "F1-Score"]
    x = np.arange(len(metrics))
    w = 0.25

    lr_m = [summary["ml"]["logistic_regression_tuned"][m]["mean"] for m in metrics]
    lr_s = [summary["ml"]["logistic_regression_tuned"][m]["std"] for m in metrics]
    lrd_m = [summary["ml"]["logistic_regression_tau_050"][m]["mean"] for m in metrics]
    lrd_s = [summary["ml"]["logistic_regression_tau_050"][m]["std"] for m in metrics]
    gnb_m = [summary["ml"]["gaussian_nb_tuned"][m]["mean"] for m in metrics]
    gnb_s = [summary["ml"]["gaussian_nb_tuned"][m]["std"] for m in metrics]

    ax1.bar(x - w, lr_m, w, yerr=lr_s, capsize=3, label="LogReg (Val-Tuned τ)", color="#38bdf8")
    ax1.bar(x, lrd_m, w, yerr=lrd_s, capsize=3, label="LogReg (Default τ=0.50)", color="#818cf8")
    ax1.bar(x + w, gnb_m, w, yerr=gnb_s, capsize=3, label="Gaussian NB (Tuned τ)", color="#fb923c")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylim(0.50, 1.02)
    ax1.set_ylabel("Score (30-Seed Mean ± Std)")
    ax1.set_title("Topic 1: Classical ML Comparison (30 Seeds)")
    ax1.grid(axis="y", alpha=0.4)
    ax1.legend(facecolor="#0f172a", edgecolor="#475569", fontsize=8.5)

    cm = summary["ml"]["reference_seed_42_confusion_matrix"]
    mat = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    im = ax2.imshow(mat, cmap="Blues", vmin=0, vmax=max(1, int(mat.max())))
    ax2.set_xticks([0, 1])
    ax2.set_yticks([0, 1])
    ax2.set_xticklabels(["Pred Safe (0)", "Pred Fire (1)"])
    ax2.set_yticklabels(["Actual Safe (0)", "Actual Fire (1)"])
    ax2.set_title("Logistic Regression Confusion Matrix (Test Split)")
    for i in range(2):
        for j in range(2):
            # High values -> dark blue background -> white text; low values -> light blue -> dark text
            txt_col = "#f8fafc" if mat[i, j] > mat.max() * 0.45 else "#0f172a"
            ax2.text(j, i, f"{mat[i, j]}", ha="center", va="center", fontsize=15, fontweight="bold", color=txt_col)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig1_ml_evaluation.png", bbox_inches="tight")
    plt.close(fig)

    # 2. Search Comparison: Expanded Nodes & Risk Exposure across 3 Presets (30 seeds)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=180)
    presets = list(PRESET_METADATA.keys())
    plabels = ["Abai\nHigh Wind", "Kostanay\nDry Steppe", "Akmola\nSensor Noise"]
    x = np.arange(len(presets))
    w = 0.25

    for idx, (algo, lbl, col) in enumerate([
        ("astar", "Risk-Aware A*", "#22c55e"),
        ("ucs", "UCS (h=0)", "#38bdf8"),
        ("bfs", "BFS (Unweighted)", "#f43f5e"),
    ]):
        offset = (idx - 1) * w
        exp_m = [summary["search"][p][algo]["expanded"]["mean"] for p in presets]
        exp_s = [summary["search"][p][algo]["expanded"]["std"] for p in presets]
        risk_m = [summary["search"][p][algo]["exposure"]["mean"] for p in presets]
        risk_s = [summary["search"][p][algo]["exposure"]["std"] for p in presets]

        ax1.bar(x + offset, exp_m, w, yerr=exp_s, capsize=3, label=lbl, color=col)
        ax2.bar(x + offset, risk_m, w, yerr=risk_s, capsize=3, label=lbl, color=col)

    ax1.set_xticks(x); ax1.set_xticklabels(plabels)
    ax1.set_ylabel("Expanded Nodes (Lower = Faster)")
    ax1.set_title("Topic 2: Nodes Expanded — A* vs UCS vs BFS")
    ax1.grid(axis="y", alpha=0.4); ax1.legend(facecolor="#0f172a", edgecolor="#475569", fontsize=8.5)

    ax2.set_xticks(x); ax2.set_xticklabels(plabels)
    ax2.set_ylabel("Cumulative Fire Risk Exposure (Lower = Safer)")
    ax2.set_title("Topic 2: Route Fire Exposure — A* vs UCS vs BFS")
    ax2.grid(axis="y", alpha=0.4); ax2.legend(facecolor="#0f172a", edgecolor="#475569", fontsize=8.5)

    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig2_search_benchmark.png", bbox_inches="tight")
    plt.close(fig)

    # 3. MDP Value Iteration Convergence + Discount Factor Sensitivity
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=180)
    deltas = summary["mdp"]["deltas"]
    ax1.semilogy(range(1, len(deltas) + 1), deltas, color="#38bdf8", linewidth=2.2, marker="o", markersize=3)
    ax1.axhline(1e-6, color="#f43f5e", linestyle="--", linewidth=1.2, label="Tolerance θ = 1e-6")
    ax1.set_xlabel("Value Iteration Sweep (k)")
    ax1.set_ylabel("Max Bellman Residual Δ_k (log scale)")
    ax1.set_title(f"Topic 3: Bellman Value Iteration Convergence ({len(deltas)} sweeps)")
    ax1.grid(True, alpha=0.35); ax1.legend(facecolor="#0f172a", edgecolor="#475569")

    sens = summary["mdp"]["gamma_sensitivity"]
    gammas = [row["gamma"] for row in sens]
    for state_key, col in [
        ("Low / HighRes", "#22c55e"),
        ("Med / HighRes", "#facc15"),
        ("High / HighRes", "#fb923c"),
        ("High / LowRes", "#f43f5e"),
    ]:
        vals = [row["values"][state_key] for row in sens]
        ax2.plot(gammas, vals, marker="o", linewidth=2.2, label=state_key, color=col)
    ax2.set_xlabel("Discount Factor γ")
    ax2.set_ylabel("Optimal State Value V*(s)")
    ax2.set_title("Topic 3: Optimal Value V*(s) vs Discount Factor γ")
    ax2.grid(True, alpha=0.35); ax2.legend(loc="center left", facecolor="#0f172a", edgecolor="#475569", fontsize=8.5)

    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig3_mdp_convergence.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    res = run_benchmarks(n_seeds=30)
    print(json.dumps({
        "ml_lr_tuned": res["ml"]["logistic_regression_tuned"],
        "ml_gnb_tuned": res["ml"]["gaussian_nb_tuned"],
        "abai_search": res["search"]["abai_high_wind"],
        "mdp_iters": res["mdp"]["iterations"],
        "mdp_gamma_sensitivity": [
            {"gamma": r["gamma"], "Med/HighRes": r["policies"]["Med / HighRes"], "High/HighRes": r["policies"]["High / HighRes"], "High/LowRes": r["policies"]["High / LowRes"]}
            for r in res["mdp"]["gamma_sensitivity"]
        ],
    }, indent=2))
