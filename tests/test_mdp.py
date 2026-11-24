"""Unit & policy-structure tests for Topic 3 (MDP Value Iteration)."""

import numpy as np
import pytest

from src.mdp import ACTION_NAMES, TERMINAL_STATES, build_mdp, gamma_sensitivity, value_iteration


def test_mdp_transition_rows_sum_to_one_and_terminals_absorbing():
    mdp = build_mdp(wind_level=0.55, e_direct=4.2, e_safe=1.5)
    n_actions, n_states, _ = mdp.P.shape

    assert np.all(mdp.P >= 0.0)
    for a in range(n_actions):
        for s in range(n_states):
            assert np.isclose(mdp.P[a, s].sum(), 1.0, atol=1e-9)
        for t in TERMINAL_STATES:
            assert np.isclose(mdp.P[a, t, t], 1.0)
            assert np.isclose(mdp.R[a, t, t], 0.0)


def test_value_iteration_convergence_and_non_degenerate_policy():
    """Verify Bellman convergence, zero terminal V, and >= 3 distinct actions across states."""
    mdp = build_mdp(wind_level=0.55, e_direct=4.2, e_safe=1.4)
    vi = value_iteration(mdp, gamma=0.90, theta=1e-6)

    assert vi.converged
    assert vi.iterations < 200
    assert vi.V[6] == 0.0 and vi.V[7] == 0.0

    # Active states (0..5) must produce a rich, non-degenerate policy
    active_policies = set(vi.policy_names[:6])
    assert len(active_policies) >= 3, f"Degenerate policy: {vi.policy_names[:6]}"

    # Resource gating: Aerial Retardant must be chosen at High/HighRes and NEVER at High/LowRes
    assert vi.policy_names[4] == "Aerial Retardant"
    assert vi.policy_names[5] == "Evacuate / Hold"
    assert vi.policy_names[2] == "Safe Detour"


def test_gamma_sensitivity_flips_at_least_one_action():
    """Audit #1 requirement: changing discount factor gamma must flip >= 1 state's action."""
    mdp = build_mdp(wind_level=0.52, e_direct=3.6, e_safe=1.3)
    sens = gamma_sensitivity(mdp, gammas=(0.50, 0.90))
    pol_low_gamma = sens[0]["policies"]
    pol_high_gamma = sens[1]["policies"]

    diffs = [s for s in pol_low_gamma if pol_low_gamma[s] != pol_high_gamma[s]]
    assert len(diffs) >= 1, (
        f"Expected at least one policy flip between gamma=0.50 and 0.90.\n"
        f"gamma=0.50: {pol_low_gamma}\ngamma=0.90: {pol_high_gamma}"
    )


def test_invalid_gamma_rejected():
    mdp = build_mdp(wind_level=0.5, e_direct=2.0, e_safe=1.0)
    with pytest.raises(ValueError):
        value_iteration(mdp, gamma=1.0)
    with pytest.raises(ValueError):
        value_iteration(mdp, gamma=0.0)


def test_counterfactual_exposure_coupling_flips_policy():
    """Audit #2 P1 counterfactual test: increasing BFS e_direct from low to high
    measurably drops Q(Direct Dispatch) and flips the Low/HighRes policy to Safe Detour."""
    mdp_clean = build_mdp(wind_level=0.20, e_direct=0.3, e_safe=0.3, bfs_steps=9, astar_steps=9)
    mdp_fire = build_mdp(wind_level=0.20, e_direct=7.5, e_safe=0.3, bfs_steps=9, astar_steps=13)

    vi_clean = value_iteration(mdp_clean, gamma=0.90)
    vi_fire = value_iteration(mdp_fire, gamma=0.90)

    # Action 1 = Direct Dispatch
    assert vi_fire.Q[0, 1] < vi_clean.Q[0, 1] - 10.0
    assert vi_clean.policy_names[0] == "Direct Dispatch"
    assert vi_fire.policy_names[0] == "Safe Detour"
