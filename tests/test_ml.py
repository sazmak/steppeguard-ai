"""Unit & edge-case tests for Topic 1 (Classical ML + Bayesian Sensor Update)."""

import numpy as np
import pytest

from src.data import make_dataset
from src.ml_model import (
    GaussianNBScratch,
    LogisticRegressionScratch,
    StandardScaler,
    bayes_sensor_update,
    evaluate_predictions,
    select_threshold_on_val,
    stable_sigmoid,
)


def test_stable_sigmoid_extreme_values():
    z = np.array([-1000.0, -2.0, 0.0, 2.0, 1000.0])
    p = stable_sigmoid(z)
    assert np.all(np.isfinite(p))
    assert np.isclose(p[2], 0.5)
    assert p[0] >= 0.0 and p[-1] <= 1.0
    assert np.isclose(p[3], 1.0 / (1.0 + np.exp(-2.0)), atol=1e-6)


def test_scaler_zero_variance_and_nan_rejection():
    X = np.array([[5.0, 1.0], [5.0, 2.0], [5.0, 3.0]])
    scaler = StandardScaler().fit(X)
    Xt = scaler.transform(X)
    assert np.all(np.isfinite(Xt))
    assert np.allclose(Xt[:, 0], 0.0)

    X_nan = np.array([[1.0, np.nan], [2.0, 3.0]])
    with pytest.raises(ValueError):
        StandardScaler().fit(X_nan)


def test_ml_models_realistic_performance_and_no_leakage():
    ds = make_dataset(seed=42, n_scenes=30, cells_per_scene=100)
    scaler = StandardScaler().fit(ds["X_train"])
    X_tr = scaler.transform(ds["X_train"])
    X_va = scaler.transform(ds["X_val"])
    X_te = scaler.transform(ds["X_test"])

    lr = LogisticRegressionScratch(learning_rate=0.25, epochs=600, l2_lambda=0.05).fit(X_tr, ds["y_train"])
    gnb = GaussianNBScratch().fit(X_tr, ds["y_train"])

    assert lr.loss_history_[-1] < lr.loss_history_[0]

    tau_val, _ = select_threshold_on_val(ds["y_val"], lr.predict_proba(X_va))
    assert 0.15 <= tau_val <= 0.55

    m_lr = evaluate_predictions(ds["y_test"], lr.predict_proba(X_te), tau=tau_val)
    m_gnb = evaluate_predictions(ds["y_test"], gnb.predict_proba(X_te), tau=tau_val)

    # Realistic non-trivial performance (not broken, and not fake 100%)
    assert 0.75 <= m_lr["f1"] <= 0.96
    assert 0.70 <= m_gnb["f1"] <= 0.96
    assert m_lr["brier_score"] < 0.16
    assert m_lr["recall"] >= 0.80


def test_all_same_class_edge_case():
    X = np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]])
    y_all_zero = np.zeros(3, dtype=np.int64)
    y_all_one = np.ones(3, dtype=np.int64)

    lr0 = LogisticRegressionScratch().fit(X, y_all_zero)
    gnb0 = GaussianNBScratch().fit(X, y_all_zero)
    assert np.all(lr0.predict_proba(X) < 0.1)
    assert np.allclose(gnb0.predict_proba(X), 0.0)

    lr1 = LogisticRegressionScratch().fit(X, y_all_one)
    gnb1 = GaussianNBScratch().fit(X, y_all_one)
    assert np.all(lr1.predict_proba(X) > 0.9)
    assert np.allclose(gnb1.predict_proba(X), 1.0)


def test_bayes_sensor_update_exact_lecture_example():
    # Exact Lecture 6 Page 58 numerical verification:
    # Prior=0.02, TPR=0.90, FPR=0.10 => Posterior = 0.1552
    res = bayes_sensor_update(prior=0.02, alert=True, tpr=0.90, fpr=0.10)
    assert np.isclose(res["posterior"], 0.1552, atol=1e-4)

    # Clear reading lowers belief
    res_clear = bayes_sensor_update(prior=0.50, alert=False, tpr=0.90, fpr=0.10)
    assert res_clear["posterior"] < 0.50
    assert np.isclose(res_clear["posterior"], 0.10, atol=1e-4)
