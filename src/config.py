"""Central configuration for SteppeGuard AI.

All defaults are grounded in course materials (AIF1303 Weeks 1, 2, 5, 6, 8)
and refined following Stage 1 Peer Architecture Audit.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


FEATURE_NAMES: Tuple[str, ...] = (
    "temperature_c",       # Ambient temperature (°C), ~10..48
    "humidity_pct",        # Relative humidity (%), ~8..85
    "wind_kmh",            # Wind speed (km/h), ~2..65
    "dryness_index",       # Vegetation dryness (1 - NDVI proxy), 0.0..1.0
    "thermal_anomaly",     # Satellite thermal index, 0.0..1.0
)

TERRAIN_NAMES: Dict[int, str] = {
    0: "Steppe Plain",
    1: "Dry Shrub",
    2: "Rocky Ridge",
    3: "Impassable Barrier",
}

TERRAIN_BASE_COSTS: Dict[int, float] = {
    0: 1.0,   # Open steppe road/plain
    1: 1.35,  # Dry brushland
    2: 1.85,  # Uneven hill/ridge
}


@dataclass(frozen=True)
class Config:
    """Reproducible hyperparameters and domain constants."""

    seed: int = 42
    grid_size: int = 10

    # Topic 1: Classical ML (Week 8) & Bayes Sensor Bridge (Week 6)
    lr_learning_rate: float = 0.25
    lr_epochs: int = 600
    lr_l2_lambda: float = 1.0          # Active L2 regularization on weights (not bias)
    default_tau: float = 0.35          # Safety-first wildfire threshold (< 0.50)
    sensor_tpr: float = 0.90           # P(Watchtower Alert | Fire)
    sensor_fpr: float = 0.10           # P(Watchtower Alert | No Fire)

    # Topic 2: Risk-Aware A* Search (Week 2)
    risk_lambda: float = 3.5           # Penalty multiplier on ML fire probability
    terrain_costs: Dict[int, float] = field(default_factory=lambda: dict(TERRAIN_BASE_COSTS))

    # Topic 3: MDP Value Iteration (Week 5)
    gamma: float = 0.90                # Discount factor
    theta: float = 1e-6                # Convergence tolerance
    max_vi_iters: int = 500
