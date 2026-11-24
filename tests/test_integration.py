"""Integration & FastAPI endpoint tests for end-to-end SteppeGuard AI pipeline."""

from fastapi.testclient import TestClient

from app import app, engine


client = TestClient(app)


def test_all_three_presets_run_cleanly_and_differ():
    results = {}
    for pid in ("abai_high_wind", "kostanay_dry_steppe", "akmola_sensor_noise"):
        res = engine.run_pipeline(preset_id=pid, seed=42)
        assert res["search"]["astar"]["found"] is True
        assert res["search"]["summary"]["astar_equals_ucs_cost"] is True
        assert res["mdp"]["converged"] is True
        results[pid] = res

    # Abai must have higher corridor risk than Akmola
    assert results["abai_high_wind"]["ml"]["corridor_risk"] > results["akmola_sensor_noise"]["ml"]["corridor_risk"]
    # Risk-Aware A* must beat unweighted BFS on risk exposure in Abai
    assert (
        results["abai_high_wind"]["search"]["astar"]["total_exposure"]
        < results["abai_high_wind"]["search"]["bfs"]["total_exposure"]
    )
    # Audit #2 P1: All three presets produce genuinely distinct recommended MDP actions!
    actions = {pid: results[pid]["mdp"]["recommended_action"] for pid in results}
    assert actions["akmola_sensor_noise"] == "Direct Dispatch", actions
    assert actions["kostanay_dry_steppe"] == "Safe Detour", actions
    assert actions["abai_high_wind"] == "Aerial Retardant", actions


def test_gaussian_nb_mode_matches_math_inspector():
    res = client.post(
        "/api/run",
        json={"preset_id": "kostanay_dry_steppe", "model_choice": "gaussian_nb", "inspect_cell": [5, 5]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["math_inspector"]["ml_step"]["model"] == "Gaussian Naive Bayes"
    grid_prob = body["grid"][5][5]["base_risk"]
    insp_prob = body["math_inspector"]["ml_step"]["probability"]
    assert abs(grid_prob - insp_prob) < 1e-3


def test_blocked_map_and_sensor_endpoints():
    # Completely block column 4 with extra_obstacles -> route_found=False handled cleanly
    wall = [[r, 4] for r in range(10)]
    r_wall = client.post("/api/run", json={"preset_id": "akmola_sensor_noise", "extra_obstacles": wall})
    assert r_wall.status_code == 200
    body = r_wall.json()
    assert body["search"]["astar"]["found"] is False
    assert body["mdp"]["converged"] is True

    # /api/sensor requires at least 1 event
    r_empty = client.post("/api/sensor", json={"preset_id": "akmola_sensor_noise", "sensor_events": []})
    assert r_empty.status_code == 400

    # Clear reading (alert=False) lowers probability
    r_base = client.post("/api/run", json={"preset_id": "abai_high_wind"}).json()
    prior = r_base["grid"][5][5]["risk"]
    r_clear = client.post(
        "/api/sensor",
        json={"preset_id": "abai_high_wind", "sensor_events": [{"row": 5, "col": 5, "alert": False}]},
    )
    assert r_clear.status_code == 200
    assert r_clear.json()["grid"][5][5]["risk"] < prior

    # /api/benchmarks serves 30-seed summary
    r_bm = client.get("/api/benchmarks")
    assert r_bm.status_code == 200
    assert r_bm.json()["n_seeds"] == 30


def test_live_bayes_sensor_updates_risk_and_replans():
    base = engine.run_pipeline(preset_id="akmola_sensor_noise", seed=42)
    # Pick a cell on the initial A* path and trigger a Watchtower Smoke Alert
    path = base["search"]["astar"]["path"]
    target_r, target_c = path[len(path) // 2]
    prior = base["grid"][target_r][target_c]["risk"]

    updated = engine.run_pipeline(
        preset_id="akmola_sensor_noise",
        seed=42,
        sensor_events=[{"row": target_r, "col": target_c, "alert": True}],
    )
    posterior = updated["grid"][target_r][target_c]["risk"]
    assert posterior > prior
    assert len(updated["ml"]["bayes_sensor_updates"]) == 1


def test_fastapi_endpoints_and_input_validation():
    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    r_presets = client.get("/api/presets")
    assert r_presets.status_code == 200
    assert len(r_presets.json()["presets"]) == 3

    r_run = client.post("/api/run", json={"preset_id": "kostanay_dry_steppe", "seed": 42})
    assert r_run.status_code == 200
    body = r_run.json()
    assert "grid" in body and "search" in body and "mdp" in body and "math_inspector" in body

    # Out-of-range gamma rejected cleanly with HTTP 422
    r_bad = client.post("/api/run", json={"preset_id": "abai_high_wind", "gamma": 1.5})
    assert r_bad.status_code == 422

    # Unknown preset rejected cleanly with HTTP 400
    r_unknown = client.post("/api/run", json={"preset_id": "nonexistent_map"})
    assert r_unknown.status_code == 400
