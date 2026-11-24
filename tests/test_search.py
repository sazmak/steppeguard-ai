"""Unit, property, and edge-case tests for Topic 2 (Risk-Aware A* vs UCS vs BFS)."""

import numpy as np
import pytest

from src.search import astar_search, bfs_search, compute_step_costs, ucs_search


def test_search_edge_cases():
    terrain = np.zeros((5, 5), dtype=np.int64)
    risk = np.full((5, 5), 0.2, dtype=np.float64)
    obstacles = np.zeros((5, 5), dtype=bool)
    costs = compute_step_costs(terrain, risk, obstacles, risk_lambda=3.5)

    # 1. start == goal
    for fn in (bfs_search, ucs_search, astar_search):
        res = fn(costs, risk, obstacles, (2, 2), (2, 2))
        assert res.found and res.steps == 0 and res.path == [(2, 2)]

    # 2. goal on obstacle
    obs_goal = obstacles.copy()
    obs_goal[4, 4] = True
    costs_g = compute_step_costs(terrain, risk, obs_goal, risk_lambda=3.5)
    for fn in (bfs_search, ucs_search, astar_search):
        res = fn(costs_g, risk, obs_goal, (0, 0), (4, 4))
        assert not res.found and res.path == []

    # 3. completely walled-off goal (no path)
    obs_wall = obstacles.copy()
    obs_wall[:, 2] = True
    costs_w = compute_step_costs(terrain, risk, obs_wall, risk_lambda=3.5)
    for fn in (bfs_search, ucs_search, astar_search):
        res = fn(costs_w, risk, obs_wall, (0, 0), (4, 4))
        assert not res.found and res.path == []


def test_astar_optimality_and_efficiency_on_100_random_maps():
    """Audit #1 property test: on 100 random maps, A* cost == UCS cost <= BFS cost,
    and A* expands <= UCS nodes (identical tie-breaking)."""
    rng = np.random.default_rng(123)
    solved_count = 0

    for _ in range(100):
        R = C = 8
        terrain = rng.integers(0, 3, size=(R, C))
        risk = rng.uniform(0.0, 1.0, size=(R, C))
        obstacles = rng.random((R, C)) < 0.16
        obstacles[0, 0] = False
        obstacles[R - 1, C - 1] = False

        costs = compute_step_costs(terrain, risk, obstacles, risk_lambda=3.5)
        r_bfs = bfs_search(costs, risk, obstacles, (0, 0), (R - 1, C - 1))
        r_ucs = ucs_search(costs, risk, obstacles, (0, 0), (R - 1, C - 1))
        r_ast = astar_search(costs, risk, obstacles, (0, 0), (R - 1, C - 1))

        assert r_bfs.found == r_ucs.found == r_ast.found
        if r_ast.found:
            solved_count += 1
            assert np.isclose(r_ast.total_cost, r_ucs.total_cost, atol=1e-9)
            assert r_ast.total_cost <= r_bfs.total_cost + 1e-9
            assert r_ast.expanded_count <= r_ucs.expanded_count

    assert solved_count >= 75


def test_astar_detours_around_fire_corridor_unlike_bfs():
    """Verify A* meaningfully reduces fire exposure compared to unweighted BFS."""
    terrain = np.zeros((7, 7), dtype=np.int64)
    obstacles = np.zeros((7, 7), dtype=bool)
    risk = np.full((7, 7), 0.05, dtype=np.float64)
    # Place intense fire across the top two rows along the direct BFS path
    risk[0:2, 2:5] = 0.95

    costs = compute_step_costs(terrain, risk, obstacles, risk_lambda=3.5)
    r_bfs = bfs_search(costs, risk, obstacles, (0, 0), (0, 6))
    r_ast = astar_search(costs, risk, obstacles, (0, 0), (0, 6))

    assert r_bfs.found and r_ast.found
    assert r_ast.total_exposure < r_bfs.total_exposure
    assert r_ast.total_cost < r_bfs.total_cost


def test_heuristic_strict_admissibility_property():
    """Verify h(start) = c_min * Manhattan(start, goal) <= true optimal cost h*(start) on 50 random grids."""
    rng = np.random.default_rng(77)
    for _ in range(50):
        terrain = rng.integers(0, 3, size=(7, 7))
        risk = rng.uniform(0.0, 1.0, size=(7, 7))
        obstacles = rng.random((7, 7)) < 0.12
        obstacles[0, 0] = False
        obstacles[6, 6] = False
        costs = compute_step_costs(terrain, risk, obstacles, risk_lambda=3.5)
        res = astar_search(costs, risk, obstacles, (0, 0), (6, 6))
        if res.found:
            h_start = res.c_min_used * (6 + 6)
            assert 0.0 <= h_start <= res.total_cost + 1e-9
