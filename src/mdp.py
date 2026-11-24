"""Topic 3: Sequential Decision Making — MDP & Value Iteration (Week 5).

Directly aligned with MDP_Reinforcement_Learning.pptx (Slides 4, 13-31, 69):
- "Search returns a path; an MDP solution is a policy pi(s)."
- Bellman Optimality Equation:
      Q*(s, a) = sum_{s'} P(s' | s, a) * [R(s, a, s') + gamma * V*(s')]
      V*(s)    = max_a Q*(s, a)
      pi*(s)   = argmax_a Q*(s, a)
- Tightly coupled with Topic 1 (ML risk level) and Topic 2 (BFS direct exposure
  E_direct vs Risk-Aware A* safe exposure E_safe).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple
import numpy as np


STATE_NAMES: Tuple[str, ...] = (
    "Low Risk | High Resources",     # 0
    "Low Risk | Low Resources",      # 1
    "Med Risk | High Resources",     # 2
    "Med Risk | Low Resources",      # 3
    "High Risk | High Resources",    # 4
    "High Risk | Low Resources",     # 5
    "Contained (Terminal)",          # 6
    "Escaped (Terminal)",            # 7
)

STATE_SHORT_NAMES: Tuple[str, ...] = (
    "Low / HighRes",
    "Low / LowRes",
    "Med / HighRes",
    "Med / LowRes",
    "High / HighRes",
    "High / LowRes",
    "Contained",
    "Escaped",
)

ACTION_NAMES: Tuple[str, ...] = (
    "Monitor",
    "Direct Dispatch",
    "Safe Detour",
    "Aerial Retardant",
    "Evacuate / Hold",
)

TERMINAL_STATES = (6, 7)
CONTAINED = 6
ESCAPED = 7


@dataclass
class MDPModel:
    """Explicit tabular MDP (S, A, P, R) with verified stochastic transition rows."""

    state_names: Tuple[str, ...]
    short_names: Tuple[str, ...]
    action_names: Tuple[str, ...]
    P: np.ndarray        # shape (n_actions, n_states, n_states), rows sum to 1.0
    R: np.ndarray        # shape (n_actions, n_states, n_states), transition reward R(s, a, s')
    wind_level: float
    e_direct: float
    e_safe: float


@dataclass
class VIResult:
    """Output of Bellman Value Iteration."""

    gamma: float
    theta: float
    iterations: int
    converged: bool
    V: np.ndarray              # shape (n_states,)
    Q: np.ndarray              # shape (n_states, n_actions)
    policy_indices: np.ndarray # shape (n_states,)
    policy_names: List[str]
    deltas: List[float]        # max |V_{k+1} - V_k| per sweep

    def to_dict(self, mdp: MDPModel, active_state: int) -> Dict[str, Any]:
        states_table = []
        for s in range(len(mdp.state_names)):
            is_term = s in TERMINAL_STATES
            q_map = {
                mdp.action_names[a]: round(float(self.Q[s, a]), 3)
                for a in range(len(mdp.action_names))
            }
            states_table.append(
                {
                    "index": s,
                    "state": mdp.state_names[s],
                    "short_name": mdp.short_names[s],
                    "is_terminal": is_term,
                    "is_active": s == active_state,
                    "v_star": round(float(self.V[s]), 3),
                    "best_action": "Terminal" if is_term else self.policy_names[s],
                    "q_values": q_map,
                }
            )

        # Worked Bellman breakdown for the active state (1st-year Math Inspector)
        best_a = int(self.policy_indices[active_state])
        transitions_breakdown = []
        for s_next in range(len(mdp.state_names)):
            prob = float(mdp.P[best_a, active_state, s_next])
            if prob > 1e-6:
                rew = float(mdp.R[best_a, active_state, s_next])
                v_next = float(self.V[s_next])
                contrib = prob * (rew + self.gamma * v_next)
                transitions_breakdown.append(
                    {
                        "next_state": mdp.short_names[s_next],
                        "prob": round(prob, 4),
                        "reward": round(rew, 2),
                        "v_next": round(v_next, 3),
                        "contribution": round(contrib, 3),
                    }
                )

        return {
            "gamma": round(float(self.gamma), 3),
            "theta": self.theta,
            "iterations": self.iterations,
            "converged": self.converged,
            "active_state_index": active_state,
            "active_state_name": mdp.state_names[active_state],
            "recommended_action": self.policy_names[active_state],
            "active_v_star": round(float(self.V[active_state]), 3),
            "deltas": [round(float(d), 6) for d in self.deltas],
            "states": states_table,
            "active_bellman_breakdown": transitions_breakdown,
            "coupling_inputs": {
                "wind_level": round(float(mdp.wind_level), 3),
                "e_direct_bfs": round(float(mdp.e_direct), 3),
                "e_safe_astar": round(float(mdp.e_safe), 3),
            },
        }


def _set_transitions(
    P: np.ndarray,
    R: np.ndarray,
    a: int,
    s: int,
    outcomes: Sequence[Tuple[int, float, float]],
) -> None:
    """Assign normalized transition probabilities and probability-weighted rewards R(s, a, s')."""
    total_p = sum(p for _, p, _ in outcomes)
    if total_p <= 0.0:
        raise ValueError(f"Transition probabilities for (s={s}, a={a}) sum to <= 0.")
    weighted_r: Dict[int, float] = {}
    prob_acc: Dict[int, float] = {}
    for s_next, prob, rew in outcomes:
        norm_p = prob / total_p
        prob_acc[s_next] = prob_acc.get(s_next, 0.0) + norm_p
        weighted_r[s_next] = weighted_r.get(s_next, 0.0) + norm_p * rew
    for s_next, p_val in prob_acc.items():
        P[a, s, s_next] = p_val
        R[a, s, s_next] = weighted_r[s_next] / p_val if p_val > 0.0 else 0.0


def build_mdp(
    wind_level: float,
    e_direct: float,
    e_safe: float,
    route_found: bool = True,
    bfs_steps: int = 9,
    astar_steps: int = 12,
) -> MDPModel:
    """Construct the SteppeGuard MDP parameterized by live ML/A* outputs.

    Parameters
    ----------
    wind_level : float in [0, 1]
        Regional wind severity (increases fire escalation probability).
    e_direct : float
        Cumulative ML fire probability along the direct (BFS) path.
    e_safe : float
        Cumulative ML fire probability along the Risk-Aware A* path.
    route_found : bool
        If False (all corridors blocked), ground actions fail and Aerial/Evacuate dominate.
    bfs_steps, astar_steps : int
        Path step counts used to compute non-saturating per-step mean route risk.
    """
    w = float(np.clip(wind_level, 0.0, 1.0))
    # Per-step mean fire risk in [0, 1] avoids saturation on long routes (Audit #2 P1 fix)
    d_risk = float(np.clip(e_direct / max(1, bfs_steps), 0.0, 1.0)) if route_found else 1.0
    s_risk = float(np.clip(e_safe / max(1, astar_steps), 0.0, 1.0)) if route_found else 1.0

    n_states = len(STATE_NAMES)
    n_actions = len(ACTION_NAMES)
    P = np.zeros((n_actions, n_states, n_states), dtype=np.float64)
    R = np.zeros((n_actions, n_states, n_states), dtype=np.float64)

    # Absorbing terminal states: self-loop with 0 future reward (V=0)
    for a in range(n_actions):
        for t_state in TERMINAL_STATES:
            P[a, t_state, t_state] = 1.0
            R[a, t_state, t_state] = 0.0

    # Reward constants (course Lecture 5, Slide 13: safety outweighs speed)
    R_CONTAIN = 100.0
    R_NATURAL_OUT = 68.0
    R_SAFE_EVAC = -16.0
    R_ESCAPED = -130.0

    # Action operating costs
    C_MON = -1.0
    C_DIRECT = -9.0
    C_DETOUR = -12.0
    C_AERIAL = -26.0
    C_EVAC = -14.0

    # Helper to build transitions for each of the 6 active states (risk_idx in 0..2, res_low in 0..1)
    for risk_idx in (0, 1, 2):       # 0=Low, 1=Med, 2=High
        for res_low in (0, 1):       # 0=HighRes, 1=LowRes
            s = risk_idx * 2 + res_low
            s_same = s
            s_up = min(2, risk_idx + 1) * 2 + res_low
            s_down = max(0, risk_idx - 1) * 2 + res_low
            s_lowres_down = max(0, risk_idx - 1) * 2 + 1
            s_lowres_same = risk_idx * 2 + 1

            # --- Action 0: Monitor (cheap observation; wind drives escalation) ---
            if risk_idx == 0:  # Low Risk
                p_out = float(np.clip(0.42 - 0.25 * w, 0.12, 0.45))
                p_esc = float(np.clip(0.10 + 0.34 * w, 0.08, 0.48))
                p_stay = max(0.05, 1.0 - p_out - p_esc)
                _set_transitions(P, R, 0, s, [
                    (CONTAINED, p_out, C_MON + R_NATURAL_OUT),
                    (s_same, p_stay, C_MON),
                    (s_up, p_esc, C_MON - 4.0),
                ])
            elif risk_idx == 1:  # Medium Risk
                p_esc = float(np.clip(0.38 + 0.38 * w, 0.30, 0.78))
                p_stay = max(0.10, 0.90 - p_esc)
                _set_transitions(P, R, 0, s, [
                    (s_down, 0.10, C_MON),
                    (s_same, p_stay, C_MON - 3.0),
                    (s_up, p_esc, C_MON - 10.0),
                ])
            else:  # High Risk: waiting risks catastrophic escape
                p_escape = float(np.clip(0.55 + 0.35 * w, 0.50, 0.92))
                _set_transitions(P, R, 0, s, [
                    (s_same, 1.0 - p_escape, C_MON - 12.0),
                    (ESCAPED, p_escape, C_MON + R_ESCAPED),
                ])

            # --- Action 1: Direct Dispatch (coupled to BFS path exposure d_risk!) ---
            if not route_found:
                _set_transitions(P, R, 1, s, [
                    (s_up if risk_idx < 2 else ESCAPED, 0.75, C_DIRECT - 25.0 + (R_ESCAPED if risk_idx == 2 else 0.0)),
                    (s_same, 0.25, C_DIRECT - 15.0),
                ])
            elif risk_idx == 0:  # Low Risk
                # Direct Dispatch is fast & optimal when BFS direct route is clean (low d_risk),
                # but loses to Safe Detour if direct route exposure d_risk spikes (strong coupling!).
                p_con = float(np.clip(0.84 - 0.55 * d_risk - 0.08 * w, 0.25, 0.86))
                p_esc = float(np.clip(0.04 + 0.42 * d_risk + 0.08 * w, 0.03, 0.55))
                p_stay = max(0.05, 1.0 - p_con - p_esc)
                extra_pen = -3.0 if res_low else 0.0
                _set_transitions(P, R, 1, s, [
                    (CONTAINED, p_con, C_DIRECT + extra_pen + R_CONTAIN),
                    (s_same, p_stay, C_DIRECT + extra_pen),
                    (s_up, p_esc, C_DIRECT + extra_pen - 16.0),
                ])
            elif risk_idx == 1:  # Medium Risk
                # Direct Dispatch is fast when direct path is clear, but high BFS exposure d_risk
                # sharply increases escalation risk, making Risk-Aware A* Safe Detour superior.
                # Note on gamma sensitivity: at myopic gamma=0.50, Aerial Retardant's immediate
                # containment beats Safe Detour's multi-step de-escalation; at farsighted gamma>=0.80,
                # Safe Detour wins by conserving aircraft resources and de-escalating Med -> Low.
                p_con = float(np.clip(0.68 - 0.42 * d_risk - 0.08 * w, 0.22, 0.70))
                p_esc = float(np.clip(0.14 + 0.42 * d_risk + 0.12 * w, 0.12, 0.65))
                p_stay = max(0.05, 1.0 - p_con - p_esc)
                _set_transitions(P, R, 1, s, [
                    (CONTAINED, p_con, C_DIRECT + R_CONTAIN),
                    (s_same, p_stay, C_DIRECT - 4.0),
                    (s_up, p_esc, C_DIRECT - 18.0),
                ])
            else:  # High Risk: sending ground crew straight into a fire front is very risky
                p_con = float(np.clip(0.28 - 0.15 * d_risk, 0.08, 0.30))
                p_escape = float(np.clip(0.40 + 0.28 * d_risk + 0.16 * w, 0.38, 0.85))
                p_stay = max(0.05, 1.0 - p_con - p_escape)
                _set_transitions(P, R, 1, s, [
                    (CONTAINED, p_con, C_DIRECT + R_CONTAIN),
                    (s_same, p_stay, C_DIRECT - 15.0),
                    (ESCAPED, p_escape, C_DIRECT + R_ESCAPED),
                ])

            # --- Action 2: Safe Detour (coupled to Risk-Aware A* exposure s_risk!) ---
            if not route_found:
                _set_transitions(P, R, 2, s, [
                    (s_up if risk_idx < 2 else ESCAPED, 0.70, C_DETOUR - 20.0 + (R_ESCAPED if risk_idx == 2 else 0.0)),
                    (s_same, 0.30, C_DETOUR - 12.0),
                ])
            elif risk_idx == 0:  # Low Risk: longer detour is slightly slower/costlier than Direct
                p_con = float(np.clip(0.68 - 0.08 * s_risk, 0.52, 0.72))
                p_stay = 1.0 - p_con
                _set_transitions(P, R, 2, s, [
                    (CONTAINED, p_con, C_DETOUR + R_CONTAIN),
                    (s_same, p_stay, C_DETOUR),
                ])
            elif risk_idx == 1:  # Medium Risk: A* detour safely flanks & de-escalates Med -> Low!
                p_con = float(np.clip(0.32 - 0.08 * s_risk, 0.18, 0.36))
                p_down = float(np.clip(0.56 - 0.14 * s_risk - 0.08 * w, 0.32, 0.62))
                p_stay = max(0.05, 1.0 - p_con - p_down)
                _set_transitions(P, R, 2, s, [
                    (CONTAINED, p_con, C_DETOUR + R_CONTAIN),
                    (s_down, p_down, C_DETOUR + 6.0),
                    (s_same, p_stay, C_DETOUR),
                ])
            else:  # High Risk: A* ground detour alone struggles against a major fire front
                p_down = float(np.clip(0.32 - 0.12 * s_risk - 0.10 * w, 0.10, 0.36))
                p_escape = float(np.clip(0.34 + 0.20 * s_risk + 0.22 * w, 0.30, 0.75))
                p_stay = max(0.05, 1.0 - p_down - p_escape)
                _set_transitions(P, R, 2, s, [
                    (s_down, p_down, C_DETOUR),
                    (s_same, p_stay, C_DETOUR - 10.0),
                    (ESCAPED, p_escape, C_DETOUR + R_ESCAPED),
                ])

            # --- Action 3: Aerial Retardant (resource-gated! Consumes High -> Low) ---
            if res_low == 1:
                # Gated when Low Resources: aircraft refueling / unavailable -> high cost, ineffective
                p_esc = float(np.clip(0.45 + 0.35 * w, 0.40, 0.85))
                target_bad = ESCAPED if risk_idx == 2 else s_up
                bad_rew = (R_ESCAPED if risk_idx == 2 else -20.0)
                _set_transitions(P, R, 3, s, [
                    (s_same, 1.0 - p_esc, -38.0),
                    (target_bad, p_esc, -38.0 + bad_rew),
                ])
            else:  # High Resources available
                if risk_idx == 0:
                    # Overkill at Low Risk: expensive and burns aircraft reserve
                    _set_transitions(P, R, 3, s, [
                        (CONTAINED, 0.82, C_AERIAL - 8.0 + R_CONTAIN),
                        (s_lowres_same, 0.18, C_AERIAL - 8.0),
                    ])
                elif risk_idx == 1:
                    # Effective at Medium Risk, but costly and depletes resources to Low
                    p_con = float(np.clip(0.68 - 0.10 * w, 0.50, 0.72))
                    p_down = max(0.15, 0.92 - p_con)
                    _set_transitions(P, R, 3, s, [
                        (CONTAINED, p_con, C_AERIAL + R_CONTAIN),
                        (s_lowres_down, p_down, C_AERIAL),
                        (s_lowres_same, 0.08, C_AERIAL - 4.0),
                    ])
                else:  # High Risk + High Resources: decisive aerial drop!
                    p_con = float(np.clip(0.64 - 0.12 * w, 0.45, 0.68))
                    p_down = float(np.clip(0.28, 0.20, 0.35))
                    p_esc = max(0.04, 1.0 - p_con - p_down)
                    _set_transitions(P, R, 3, s, [
                        (CONTAINED, p_con, C_AERIAL + R_CONTAIN),
                        (s_lowres_down, p_down, C_AERIAL + 8.0),
                        (ESCAPED, p_esc, C_AERIAL + R_ESCAPED),
                    ])

            # --- Action 4: Evacuate / Hold (life-safety fallback when High Risk + Low Res) ---
            if risk_idx < 2:
                # Premature evacuation at Low/Med risk incurs disruption penalty
                _set_transitions(P, R, 4, s, [
                    (CONTAINED, 0.85, C_EVAC - 14.0),
                    (s_same, 0.15, C_EVAC - 18.0),
                ])
            else:
                # At High Risk: orderly evacuation protects lives & avoids catastrophic -130 loss
                p_safe = float(np.clip(0.88 - 0.12 * w, 0.72, 0.90))
                _set_transitions(P, R, 4, s, [
                    (CONTAINED, p_safe, C_EVAC + R_SAFE_EVAC),
                    (ESCAPED, 1.0 - p_safe, C_EVAC + R_ESCAPED * 0.5),
                ])

    return MDPModel(
        state_names=STATE_NAMES,
        short_names=STATE_SHORT_NAMES,
        action_names=ACTION_NAMES,
        P=P,
        R=R,
        wind_level=w,
        e_direct=float(e_direct),
        e_safe=float(e_safe),
    )


def value_iteration(
    mdp: MDPModel,
    gamma: float = 0.90,
    theta: float = 1e-6,
    max_iters: int = 500,
) -> VIResult:
    """Solve MDP via Bellman Value Iteration (Lecture 5, Slides 26 & 29)."""
    if not (0.0 < gamma < 1.0):
        raise ValueError(f"Discount factor gamma must lie in (0, 1), got {gamma}.")

    n_actions, n_states, _ = mdp.P.shape
    V = np.zeros(n_states, dtype=np.float64)
    Q = np.zeros((n_states, n_actions), dtype=np.float64)
    deltas: List[float] = []
    converged = False

    for it in range(1, max_iters + 1):
        new_V = np.zeros(n_states, dtype=np.float64)
        for s in range(n_states):
            if s in TERMINAL_STATES:
                new_V[s] = 0.0
                Q[s, :] = 0.0
                continue
            for a in range(n_actions):
                # Q(s, a) = sum_{s'} P(s'|s,a) * [R(s,a,s') + gamma * V(s')]
                Q[s, a] = float(np.sum(mdp.P[a, s] * (mdp.R[a, s] + gamma * V)))
            new_V[s] = float(np.max(Q[s]))

        delta = float(np.max(np.abs(new_V - V)))
        deltas.append(delta)
        V = new_V
        if delta < theta:
            converged = True
            break

    # Final Q sweep using converged V*
    for s in range(n_states):
        if s in TERMINAL_STATES:
            Q[s, :] = 0.0
        else:
            for a in range(n_actions):
                Q[s, a] = float(np.sum(mdp.P[a, s] * (mdp.R[a, s] + gamma * V)))

    policy_indices = np.argmax(Q, axis=1)
    policy_names = [
        "Terminal" if s in TERMINAL_STATES else mdp.action_names[int(policy_indices[s])]
        for s in range(n_states)
    ]

    return VIResult(
        gamma=gamma,
        theta=theta,
        iterations=len(deltas),
        converged=converged,
        V=V,
        Q=Q,
        policy_indices=policy_indices,
        policy_names=policy_names,
        deltas=deltas,
    )


def gamma_sensitivity(
    mdp: MDPModel,
    gammas: Sequence[float] = (0.50, 0.80, 0.90, 0.95),
    theta: float = 1e-6,
) -> List[Dict[str, Any]]:
    """Run Value Iteration across discount factors gamma to observe policy shifts."""
    rows: List[Dict[str, Any]] = []
    for g in gammas:
        res = value_iteration(mdp, gamma=float(g), theta=theta)
        rows.append(
            {
                "gamma": round(float(g), 2),
                "iterations": res.iterations,
                "policies": {
                    mdp.short_names[s]: res.policy_names[s]
                    for s in range(len(mdp.state_names))
                    if s not in TERMINAL_STATES
                },
                "values": {
                    mdp.short_names[s]: round(float(res.V[s]), 2)
                    for s in range(len(mdp.state_names))
                    if s not in TERMINAL_STATES
                },
            }
        )
    return rows
