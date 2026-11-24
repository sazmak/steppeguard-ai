"""Topic 1: Classical Machine Learning (Week 8) + Bayesian Sensor Update (Week 6).

Pure NumPy implementations — zero black-box ML wrappers — directly mirroring
course lectures:
- Lecture 8 (Slides 41-46, 60-64): StandardScaler, Logistic Regression with
  sigmoid, decision threshold tau, Accuracy/Precision/Recall/F1, Brier Score.
- Syllabus Week 8: Gaussian Naive Bayes baseline for model comparison.
- Lecture 6 (Pages 55-60): Exact Bayesian posterior update for a noisy sensor.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import numpy as np

from src.config import FEATURE_NAMES


def stable_sigmoid(z: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid: sigma(z) = 1 / (1 + exp(-z))."""
    z = np.asarray(z, dtype=np.float64)
    return np.where(
        z >= 0.0,
        1.0 / (1.0 + np.exp(-np.clip(z, -500.0, 500.0))),
        np.exp(np.clip(z, -500.0, 500.0)) / (1.0 + np.exp(np.clip(z, -500.0, 500.0))),
    )


def _validate_array(X: np.ndarray, name: str = "X") -> np.ndarray:
    arr = np.asarray(X, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] == 0:
        raise ValueError(f"{name} must be a non-empty 2D array, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr


class StandardScaler:
    """Z-score standardization: z = (x - mean) / std, fit ONLY on training data."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "StandardScaler":
        arr = _validate_array(X, "X")
        self.mean_ = arr.mean(axis=0)
        # Guard against zero-variance features (Audit #1 edge case)
        self.std_ = np.maximum(arr.std(axis=0), 1e-8)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.mean_ is None or self.std_ is None:
            raise RuntimeError("StandardScaler must be fit before calling transform.")
        arr = _validate_array(X, "X")
        return (arr - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


class LogisticRegressionScratch:
    """Binary Logistic Regression trained via batch gradient descent with L2 regularization.

    Course formula (Lecture 8, Slides 42-43):
        P(y = 1 | x) = sigma(w^T x + b)
    Note: L2 penalty is applied to weights w ONLY (never to bias b).
    """

    def __init__(
        self,
        learning_rate: float = 0.25,
        epochs: int = 600,
        l2_lambda: float = 0.05,
    ) -> None:
        self.learning_rate = float(learning_rate)
        self.epochs = int(epochs)
        self.l2_lambda = float(l2_lambda)
        self.weights_: np.ndarray | None = None
        self.bias_: float = 0.0
        self.loss_history_: List[float] = []

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressionScratch":
        X_arr = _validate_array(X, "X")
        y_arr = np.asarray(y, dtype=np.float64).ravel()
        if X_arr.shape[0] != y_arr.shape[0]:
            raise ValueError("X and y must have the same number of samples.")
        if not np.all(np.isfinite(y_arr)):
            raise ValueError("y contains NaN or infinite values.")

        n_samples, n_features = X_arr.shape
        self.weights_ = np.zeros(n_features, dtype=np.float64)
        self.bias_ = 0.0
        self.loss_history_ = []

        # Handle degenerate all-same-class edge case cleanly
        unique_classes = np.unique(y_arr)
        if unique_classes.size == 1:
            self.bias_ = 4.0 if unique_classes[0] == 1.0 else -4.0
            self.loss_history_.append(0.0)
            return self

        eps = 1e-12
        for _ in range(self.epochs):
            z = X_arr @ self.weights_ + self.bias_
            p = stable_sigmoid(z)
            p_clipped = np.clip(p, eps, 1.0 - eps)

            # Binary cross-entropy + L2 penalty on weights only
            bce = -np.mean(y_arr * np.log(p_clipped) + (1.0 - y_arr) * np.log(1.0 - p_clipped))
            reg = 0.5 * self.l2_lambda * float(np.sum(self.weights_ ** 2)) / n_samples
            self.loss_history_.append(float(bce + reg))

            err = p - y_arr
            grad_w = (X_arr.T @ err) / n_samples + (self.l2_lambda / n_samples) * self.weights_
            grad_b = float(np.mean(err))

            self.weights_ -= self.learning_rate * grad_w
            self.bias_ -= self.learning_rate * grad_b

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.weights_ is None:
            raise RuntimeError("LogisticRegressionScratch must be fit before predict_proba.")
        X_arr = _validate_array(X, "X")
        return stable_sigmoid(X_arr @ self.weights_ + self.bias_)

    def predict(self, X: np.ndarray, tau: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= tau).astype(np.int64)


class GaussianNBScratch:
    """Gaussian Naive Bayes classifier computed in log-space for numerical stability.

    Uses a variance floor (1e-9 * max variance) and log-sum-exp normalization.
    """

    def __init__(self, var_smoothing: float = 1e-9) -> None:
        self.var_smoothing = float(var_smoothing)
        self.classes_: np.ndarray | None = None
        self.log_priors_: Dict[int, float] = {}
        self.means_: Dict[int, np.ndarray] = {}
        self.vars_: Dict[int, np.ndarray] = {}

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GaussianNBScratch":
        X_arr = _validate_array(X, "X")
        y_arr = np.asarray(y, dtype=np.int64).ravel()
        if X_arr.shape[0] != y_arr.shape[0]:
            raise ValueError("X and y must have the same number of samples.")

        self.classes_ = np.unique(y_arr)
        max_var = float(np.max(np.var(X_arr, axis=0)))
        var_floor = max(self.var_smoothing * max_var, 1e-9)

        self.log_priors_.clear()
        self.means_.clear()
        self.vars_.clear()

        for c in self.classes_:
            Xc = X_arr[y_arr == c]
            self.log_priors_[int(c)] = float(np.log(len(Xc) / len(y_arr)))
            self.means_[int(c)] = Xc.mean(axis=0)
            self.vars_[int(c)] = Xc.var(axis=0) + var_floor
        return self

    def _log_likelihood(self, X: np.ndarray, c: int) -> np.ndarray:
        mean = self.means_[c]
        var = self.vars_[c]
        return -0.5 * np.sum(np.log(2.0 * np.pi * var) + ((X - mean) ** 2) / var, axis=1)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.classes_ is None:
            raise RuntimeError("GaussianNBScratch must be fit before predict_proba.")
        X_arr = _validate_array(X, "X")

        # Handle degenerate single-class edge case
        if len(self.classes_) == 1:
            return np.full(X_arr.shape[0], 1.0 if self.classes_[0] == 1 else 0.0, dtype=np.float64)

        log_j0 = self.log_priors_[0] + self._log_likelihood(X_arr, 0)
        log_j1 = self.log_priors_[1] + self._log_likelihood(X_arr, 1)

        # Log-sum-exp trick for stable posterior probability P(y=1 | x)
        max_log = np.maximum(log_j0, log_j1)
        log_denom = max_log + np.log(np.exp(log_j0 - max_log) + np.exp(log_j1 - max_log))
        return np.exp(log_j1 - log_denom)

    def predict(self, X: np.ndarray, tau: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= tau).astype(np.int64)


def evaluate_predictions(y_true: np.ndarray, probs: np.ndarray, tau: float = 0.5) -> Dict[str, Any]:
    """Compute Lecture 8 classification metrics, confusion matrix, and Brier score."""
    y = np.asarray(y_true, dtype=np.int64).ravel()
    p = np.asarray(probs, dtype=np.float64).ravel()
    preds = (p >= tau).astype(np.int64)

    tp = int(np.sum((y == 1) & (preds == 1)))
    tn = int(np.sum((y == 0) & (preds == 0)))
    fp = int(np.sum((y == 0) & (preds == 1)))
    fn = int(np.sum((y == 1) & (preds == 0)))
    total = max(1, len(y))

    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    brier = float(np.mean((p - y) ** 2))

    # 5-bin reliability table to honestly inspect approximate probability calibration
    bins = np.linspace(0.0, 1.0, 6)
    reliability: List[Dict[str, Any]] = []
    for i in range(5):
        lo, hi = float(bins[i]), float(bins[i + 1])
        mask = (p >= lo) & (p <= hi if i == 4 else p < hi)
        cnt = int(np.sum(mask))
        reliability.append(
            {
                "bin": f"{lo:.1f}-{hi:.1f}",
                "count": cnt,
                "mean_pred": round(float(p[mask].mean()), 4) if cnt > 0 else None,
                "empirical_rate": round(float(y[mask].mean()), 4) if cnt > 0 else None,
            }
        )

    prevalence = float(y.mean())
    brier_baseline = prevalence * (1.0 - prevalence)

    return {
        "tau": round(float(tau), 3),
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "brier_score": round(brier, 4),
        "brier_baseline": round(float(brier_baseline), 4),
        "prevalence": round(prevalence, 4),
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "reliability_bins": reliability,
    }


def select_threshold_on_val(
    y_val: np.ndarray,
    probs_val: np.ndarray,
    fn_cost: float = 2.0,
    fp_cost: float = 1.0,
) -> Tuple[float, Dict[str, Any]]:
    """Select decision threshold tau on validation split (Lecture 8, Slides 22 & 45).

    Because missing a real wildfire (FN) is far costlier than a false alarm (FP),
    we search tau in [0.15, 0.75] minimizing expected decision cost:
        Cost(tau) = fn_cost * FN + fp_cost * FP
    """
    best_tau = 0.50
    best_cost = float("inf")
    best_metrics: Dict[str, Any] = {}

    for tau in np.linspace(0.15, 0.75, 25):
        m = evaluate_predictions(y_val, probs_val, tau=float(tau))
        cm = m["confusion_matrix"]
        cost = fn_cost * cm["fn"] + fp_cost * cm["fp"]
        if cost < best_cost:
            best_cost = cost
            best_tau = float(tau)
            best_metrics = m

    return round(best_tau, 3), best_metrics


def bayes_sensor_update(
    prior: float,
    alert: bool,
    tpr: float = 0.90,
    fpr: float = 0.10,
) -> Dict[str, Any]:
    """Exact Bayesian belief update for an independent Watchtower Smoke Sensor (Week 6).

    Assumption: The watchtower visual/smoke sensor is conditionally independent
    of the 5 regional weather/thermal features given the true fire state, with
    fixed sensitivity P(Alert | Fire) = tpr and false alarm P(Alert | NoFire) = fpr.
    """
    p = float(np.clip(prior, 1e-6, 1.0 - 1e-6))
    if alert:
        like_fire = float(tpr)
        like_safe = float(fpr)
        obs_label = "Smoke Alert (E = True)"
    else:
        like_fire = 1.0 - float(tpr)
        like_safe = 1.0 - float(fpr)
        obs_label = "Clear Watchtower Scan (E = False)"

    num = like_fire * p
    denom = num + like_safe * (1.0 - p)
    posterior = num / denom

    return {
        "observation": obs_label,
        "alert": bool(alert),
        "prior": round(p, 4),
        "p_e_given_fire": round(like_fire, 4),
        "p_e_given_no_fire": round(like_safe, 4),
        "evidence_total": round(denom, 4),
        "posterior": round(float(posterior), 4),
        "delta": round(float(posterior - p), 4),
        "formula": (
            f"P(Fire|E) = ({like_fire:.2f} × {p:.3f}) / "
            f"[({like_fire:.2f} × {p:.3f}) + ({like_safe:.2f} × {1-p:.3f})] = {posterior:.4f}"
        ),
        "explanation": (
            f"The watchtower observation '{obs_label}' updated fire belief from "
            f"{p*100:.1f}% to {posterior*100:.1f}% via Bayes' theorem."
        ),
    }


def predict_grid(
    model: LogisticRegressionScratch | GaussianNBScratch,
    scaler: StandardScaler,
    features_3d: np.ndarray,
) -> np.ndarray:
    """Predict fire probability map P(Fire | x) for every (r, c) cell on a grid."""
    rows, cols, n_feat = features_3d.shape
    flat_X = features_3d.reshape(-1, n_feat)
    flat_probs = model.predict_proba(scaler.transform(flat_X))
    return flat_probs.reshape(rows, cols)


def explain_cell_ml(
    model: LogisticRegressionScratch,
    scaler: StandardScaler,
    cell_features: np.ndarray,
    tau: float,
) -> Dict[str, Any]:
    """Produce a 1st-year-friendly step-by-step calculation for a single grid sector."""
    x_raw = np.asarray(cell_features, dtype=np.float64).reshape(1, -1)
    x_std = scaler.transform(x_raw)[0]
    w = model.weights_
    assert w is not None
    contributions = w * x_std
    z = float(np.dot(w, x_std) + model.bias_)
    prob = float(stable_sigmoid(np.array([z]))[0])

    terms = []
    for name, raw_val, z_val, weight, contrib in zip(
        FEATURE_NAMES, x_raw[0], x_std, w, contributions
    ):
        terms.append(
            {
                "feature": name,
                "raw_value": round(float(raw_val), 3),
                "standardized": round(float(z_val), 3),
                "weight": round(float(weight), 3),
                "contribution": round(float(contrib), 3),
            }
        )

    neg_z_str = f"{-z:.3f}" if z < 0 else f"-{z:.3f}"
    return {
        "model": "Logistic Regression",
        "terms": terms,
        "bias": round(float(model.bias_), 4),
        "linear_score_z": round(z, 4),
        "probability": round(prob, 4),
        "threshold_tau": round(float(tau), 3),
        "predicted_alert": bool(prob >= tau),
        "formula": f"z = w^T x_std + b = {z:.3f}  →  P(Fire|x) = 1 / (1 + e^({neg_z_str})) = {prob:.4f}",
        "explanation": (
            f"Standardized features produce score z = {z:.2f}, mapped by the sigmoid "
            f"to a {prob*100:.1f}% fire probability ({'ALERT' if prob >= tau else 'Below threshold'} at τ = {tau:.2f})."
        ),
    }


def explain_cell_gnb(
    model: GaussianNBScratch,
    scaler: StandardScaler,
    cell_features: np.ndarray,
    tau: float,
) -> Dict[str, Any]:
    """Produce a step-by-step Gaussian Naive Bayes log-odds breakdown for one sector."""
    x_raw = np.asarray(cell_features, dtype=np.float64).reshape(1, -1)
    x_std = scaler.transform(x_raw)[0]
    prob = float(model.predict_proba(x_std.reshape(1, -1))[0])

    terms = []
    log_odds = model.log_priors_[1] - model.log_priors_[0]
    for idx, name in enumerate(FEATURE_NAMES):
        v0, m0 = float(model.vars_[0][idx]), float(model.means_[0][idx])
        v1, m1 = float(model.vars_[1][idx]), float(model.means_[1][idx])
        ll0 = -0.5 * (np.log(2.0 * np.pi * v0) + ((x_std[idx] - m0) ** 2) / v0)
        ll1 = -0.5 * (np.log(2.0 * np.pi * v1) + ((x_std[idx] - m1) ** 2) / v1)
        llr = float(ll1 - ll0)
        log_odds += llr
        terms.append(
            {
                "feature": name,
                "raw_value": round(float(x_raw[0, idx]), 3),
                "standardized": round(float(x_std[idx]), 3),
                "weight": round(llr, 3),       # log-likelihood ratio for this feature
                "contribution": round(llr, 3),
            }
        )

    return {
        "model": "Gaussian Naive Bayes",
        "terms": terms,
        "bias": round(float(model.log_priors_[1] - model.log_priors_[0]), 4),
        "linear_score_z": round(float(log_odds), 4),
        "probability": round(prob, 4),
        "threshold_tau": round(float(tau), 3),
        "predicted_alert": bool(prob >= tau),
        "formula": f"log-odds = log P(1)/P(0) + Σ log[N(x_j|1)/N(x_j|0)] = {log_odds:.3f}  →  P(Fire|x) = {prob:.4f}",
        "explanation": (
            f"Gaussian Naive Bayes sums per-feature log-likelihood ratios to log-odds {log_odds:.2f}, "
            f"yielding a {prob*100:.1f}% fire probability ({'ALERT' if prob >= tau else 'Below threshold'} at τ = {tau:.2f})."
        ),
    }
