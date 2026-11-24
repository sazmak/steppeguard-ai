"""Topic 2: Informed Heuristic Search — Risk-Aware A* vs UCS vs BFS (Week 2).

Directly aligned with Lecture 2 (Pages 13-47) and Practical Work 2:
- BFS: FIFO queue, fewest steps, completely ignores terrain & fire-risk costs.
- UCS: Priority queue ordered by g(n), optimal risk-weighted cost, h(n) = 0.
- A*:  Priority queue ordered by f(n) = g(n) + h(n), where
       c(u -> v) = c_terrain(v) + lambda * P(Fire | x_v)
       h(n)      = c_min * (|r_n - r_goal| + |c_n - c_goal|)
  Because c_min = min_{free v} c(v) <= every step cost on the grid, h(n) is
  both admissible (0 <= h(n) <= h*(n)) and consistent, guaranteeing A* finds
  the exact same optimal cost as UCS while expanding <= UCS nodes.
"""

from collections import deque
from dataclasses import dataclass, field
import heapq
from typing import Any, Dict, List, Tuple
import numpy as np

from src.config import TERRAIN_BASE_COSTS

Coord = Tuple[int, int]
DIRECTIONS: Tuple[Coord, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))  # N, S, W, E


@dataclass
class SearchResult:
    """Structured output for BFS, UCS, and A* search."""

    algorithm: str
    found: bool
    path: List[Coord]
    steps: int
    total_cost: float
    total_exposure: float          # Sum of ML P(Fire) along path (feeds MDP!)
    max_cell_risk: float           # Highest single-cell P(Fire) entered along path
    expanded_count: int
    expanded_order: List[Coord]
    c_min_used: float
    node_trace: Dict[Coord, Dict[str, float]] = field(default_factory=dict)
    message: str = "OK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "found": self.found,
            "path": [[r, c] for r, c in self.path],
            "steps": self.steps,
            "total_cost": round(float(self.total_cost), 4),
            "total_exposure": round(float(self.total_exposure), 4),
            "max_cell_risk": round(float(self.max_cell_risk), 4),
            "expanded_count": self.expanded_count,
            "expanded_order": [[r, c] for r, c in self.expanded_order],
            "c_min_used": round(float(self.c_min_used), 4),
            "message": self.message,
        }


def compute_step_costs(
    terrain: np.ndarray,
    risk_grid: np.ndarray,
    obstacles: np.ndarray,
    risk_lambda: float = 3.5,
    terrain_costs: Dict[int, float] | None = None,
) -> np.ndarray:
    """Compute step entry cost c(v) = c_terrain(v) + lambda * P(Fire | x_v)."""
    if risk_lambda < 0.0:
        raise ValueError("risk_lambda must be non-negative.")
    t_map = terrain_costs or TERRAIN_BASE_COSTS
    rows, cols = terrain.shape
    costs = np.full((rows, cols), np.inf, dtype=np.float64)

    for r in range(rows):
        for c in range(cols):
            if obstacles[r, c]:
                continue
            base = float(t_map.get(int(terrain[r, c]), 1.0))
            risk = float(np.clip(risk_grid[r, c], 0.0, 1.0))
            costs[r, c] = base + float(risk_lambda) * risk
    return costs


def _validate_endpoints(
    rows: int,
    cols: int,
    obstacles: np.ndarray,
    start: Coord,
    goal: Coord,
    algorithm: str,
) -> SearchResult | None:
    sr, sc = start
    gr, gc = goal
    if not (0 <= sr < rows and 0 <= sc < cols) or not (0 <= gr < rows and 0 <= gc < cols):
        return SearchResult(
            algorithm=algorithm,
            found=False,
            path=[],
            steps=0,
            total_cost=float("inf"),
            total_exposure=0.0,
            max_cell_risk=0.0,
            expanded_count=0,
            expanded_order=[],
            c_min_used=1.0,
            message="Start or goal coordinates are out of grid bounds.",
        )
    if obstacles[sr, sc] or obstacles[gr, gc]:
        return SearchResult(
            algorithm=algorithm,
            found=False,
            path=[],
            steps=0,
            total_cost=float("inf"),
            total_exposure=0.0,
            max_cell_risk=0.0,
            expanded_count=0,
            expanded_order=[],
            c_min_used=1.0,
            message="Start or goal cell lies on an impassable obstacle.",
        )
    return None


def _reconstruct_path(came_from: Dict[Coord, Coord | None], goal: Coord) -> List[Coord]:
    path: List[Coord] = []
    cur: Coord | None = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path


def _summarize_path(
    path: List[Coord],
    cost_grid: np.ndarray,
    risk_grid: np.ndarray,
) -> Tuple[float, float, float]:
    if len(path) <= 1:
        r0, c0 = path[0]
        return 0.0, float(risk_grid[r0, c0]), float(risk_grid[r0, c0])
    # Step cost paid when entering each cell after start
    total_cost = float(sum(cost_grid[r, c] for r, c in path[1:]))
    risks = [float(risk_grid[r, c]) for r, c in path[1:]]
    return total_cost, float(sum(risks)), float(max(risks))


def bfs_search(
    cost_grid: np.ndarray,
    risk_grid: np.ndarray,
    obstacles: np.ndarray,
    start: Coord,
    goal: Coord,
) -> SearchResult:
    """Breadth-First Search (FIFO queue): fewest steps, ignores fire-risk weights."""
    rows, cols = obstacles.shape
    err = _validate_endpoints(rows, cols, obstacles, start, goal, "BFS")
    if err is not None:
        return err

    if start == goal:
        tc, exp, mr = _summarize_path([start], cost_grid, risk_grid)
        return SearchResult("BFS", True, [start], 0, tc, exp, mr, 1, [start], 0.0)

    queue: deque[Coord] = deque([start])
    came_from: Dict[Coord, Coord | None] = {start: None}
    expanded_order: List[Coord] = []

    while queue:
        cur = queue.popleft()
        expanded_order.append(cur)
        if cur == goal:
            path = _reconstruct_path(came_from, goal)
            tc, exp, mr = _summarize_path(path, cost_grid, risk_grid)
            return SearchResult(
                algorithm="BFS",
                found=True,
                path=path,
                steps=len(path) - 1,
                total_cost=tc,
                total_exposure=exp,
                max_cell_risk=mr,
                expanded_count=len(expanded_order),
                expanded_order=expanded_order,
                c_min_used=0.0,
            )

        r, c = cur
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)
            if 0 <= nr < rows and 0 <= nc < cols and not obstacles[nr, nc] and nxt not in came_from:
                came_from[nxt] = cur
                queue.append(nxt)

    return SearchResult(
        algorithm="BFS",
        found=False,
        path=[],
        steps=0,
        total_cost=float("inf"),
        total_exposure=0.0,
        max_cell_risk=0.0,
        expanded_count=len(expanded_order),
        expanded_order=expanded_order,
        c_min_used=0.0,
        message="No feasible path exists between start and goal.",
    )


def _best_first_weighted_search(
    cost_grid: np.ndarray,
    risk_grid: np.ndarray,
    obstacles: np.ndarray,
    start: Coord,
    goal: Coord,
    use_heuristic: bool,
) -> SearchResult:
    """Shared optimal priority-queue engine for UCS (h=0) and A* (h=c_min*Manhattan).

    Uses identical tie-breaking (f, g, r, c) so UCS and A* node-expansion counts
    are strictly comparable and reproducible.
    """
    algo_name = "A*" if use_heuristic else "UCS"
    rows, cols = obstacles.shape
    err = _validate_endpoints(rows, cols, obstacles, start, goal, algo_name)
    if err is not None:
        return err

    free_costs = cost_grid[~obstacles]
    c_min = float(np.min(free_costs)) if free_costs.size > 0 else 1.0
    if not use_heuristic:
        c_min = 0.0

    def heuristic(pos: Coord) -> float:
        if not use_heuristic:
            return 0.0
        return c_min * (abs(pos[0] - goal[0]) + abs(pos[1] - goal[1]))

    if start == goal:
        tc, exp, mr = _summarize_path([start], cost_grid, risk_grid)
        return SearchResult(
            algo_name,
            True,
            [start],
            0,
            tc,
            exp,
            mr,
            1,
            [start],
            c_min,
            node_trace={start: {"g": 0.0, "h": 0.0, "f": 0.0}},
        )

    h0 = heuristic(start)
    # Priority tuple: (f_score, g_score, row, col)
    pq: List[Tuple[float, float, int, int]] = [(h0, 0.0, start[0], start[1])]
    best_g: Dict[Coord, float] = {start: 0.0}
    came_from: Dict[Coord, Coord | None] = {start: None}
    closed: set[Coord] = set()
    expanded_order: List[Coord] = []
    node_trace: Dict[Coord, Dict[str, float]] = {
        start: {"g": 0.0, "h": round(h0, 4), "f": round(h0, 4)}
    }

    while pq:
        f_cur, g_cur, r, c = heapq.heappop(pq)
        cur = (r, c)
        if cur in closed:
            continue
        closed.add(cur)
        expanded_order.append(cur)

        if cur == goal:
            path = _reconstruct_path(came_from, goal)
            tc, exp, mr = _summarize_path(path, cost_grid, risk_grid)
            return SearchResult(
                algorithm=algo_name,
                found=True,
                path=path,
                steps=len(path) - 1,
                total_cost=tc,
                total_exposure=exp,
                max_cell_risk=mr,
                expanded_count=len(expanded_order),
                expanded_order=expanded_order,
                c_min_used=c_min,
                node_trace=node_trace,
            )

        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)
            if not (0 <= nr < rows and 0 <= nc < cols) or obstacles[nr, nc] or nxt in closed:
                continue

            tentative_g = g_cur + float(cost_grid[nr, nc])
            if tentative_g + 1e-12 < best_g.get(nxt, float("inf")):
                best_g[nxt] = tentative_g
                came_from[nxt] = cur
                h_nxt = heuristic(nxt)
                f_nxt = tentative_g + h_nxt
                node_trace[nxt] = {
                    "g": round(tentative_g, 4),
                    "h": round(h_nxt, 4),
                    "f": round(f_nxt, 4),
                }
                heapq.heappush(pq, (f_nxt, tentative_g, nr, nc))

    return SearchResult(
        algorithm=algo_name,
        found=False,
        path=[],
        steps=0,
        total_cost=float("inf"),
        total_exposure=0.0,
        max_cell_risk=0.0,
        expanded_count=len(expanded_order),
        expanded_order=expanded_order,
        c_min_used=c_min,
        node_trace=node_trace,
        message="No feasible path exists between start and goal.",
    )


def ucs_search(
    cost_grid: np.ndarray,
    risk_grid: np.ndarray,
    obstacles: np.ndarray,
    start: Coord,
    goal: Coord,
) -> SearchResult:
    """Uniform Cost Search (priority queue on g(n); equivalent to A* with h=0)."""
    return _best_first_weighted_search(cost_grid, risk_grid, obstacles, start, goal, use_heuristic=False)


def astar_search(
    cost_grid: np.ndarray,
    risk_grid: np.ndarray,
    obstacles: np.ndarray,
    start: Coord,
    goal: Coord,
) -> SearchResult:
    """Risk-Aware A* Search (f(n) = g(n) + c_min * Manhattan(n, goal))."""
    return _best_first_weighted_search(cost_grid, risk_grid, obstacles, start, goal, use_heuristic=True)
