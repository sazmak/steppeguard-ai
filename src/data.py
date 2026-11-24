"""Synthetic domain-grounded Kazakhstan steppe telemetry & scenario presets.

IMPORTANT ACADEMIC INTEGRITY NOTE (Syllabus Section 8 & MiniAI_FPTopics.docx):
All weather/satellite telemetry, terrain grids, and wildfire labels generated
here are synthetic, domain-inspired simulation data created for educational
demonstration and reproducible experimentation. They are NOT real Ministry of
Emergency Situations (MChS) operational data.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class SectorMap:
    """A 2D grid representing a Kazakhstan steppe operational region."""

    preset_id: str
    title: str
    region: str
    description: str
    seed: int
    rows: int
    cols: int
    features: np.ndarray       # shape (R, C, 5)
    terrain: np.ndarray        # shape (R, C), values in {0, 1, 2, 3}
    obstacles: np.ndarray      # shape (R, C), bool (True where impassable)
    elevation: np.ndarray      # shape (R, C), float in [0.0, 1.0] for 3D rendering
    start: Tuple[int, int]     # Base / Fire Station
    goal: Tuple[int, int]      # Target Settlement / Hotspot
    wind_level: float          # Normalized regional wind severity in [0.0, 1.0]
    initial_resource: str      # "High" or "Low"


PRESET_METADATA: Dict[str, Dict[str, str]] = {
    "abai_high_wind": {
        "title": "Abai High-Wind Fire Corridor",
        "region": "Abai Region (East Kazakhstan Steppe)",
        "description": (
            "Severe hot wind creates a high-risk wildfire belt across the direct "
            "corridor. BFS cuts blindly into danger, while Risk-Aware A* detours "
            "safely and MDP recommends Aerial Retardant (or Evacuation if low on resources)."
        ),
    },
    "kostanay_dry_steppe": {
        "title": "Kostanay Dry Steppe Belt",
        "region": "Kostanay Region (Northern Steppe)",
        "description": (
            "Moderate wind and dry brush create a medium-risk central zone. "
            "A* balances distance and hazard, and MDP selects Safe Detour as the optimal policy."
        ),
    },
    "akmola_sensor_noise": {
        "title": "Akmola Watchtower Sensor Alert",
        "region": "Akmola Region (Near Astana)",
        "description": (
            "Calm conditions with ambiguous warm sectors. Ideal for testing live "
            "Bayesian sensor updates: triggering a Watchtower Smoke Alert dynamically "
            "raises fire probability, reroutes A*, and shifts the MDP recommendation."
        ),
    },
}


def _true_fire_logit(X: np.ndarray) -> np.ndarray:
    """Underlying domain-inspired physical wildfire log-odds with nonlinear interaction.

    Features: [temperature_c, humidity_pct, wind_kmh, dryness_index, thermal_anomaly].
    Includes a realistic (low_humidity * high_wind) interaction term and dry-fuel
    amplification so Logistic Regression and Gaussian Naive Bayes exhibit realistic,
    non-trivial differences rather than an artificial 100% accuracy.
    """
    temp = (X[:, 0] - 28.0) / 8.0
    hum = (X[:, 1] - 42.0) / 18.0
    wind = (X[:, 2] - 26.0) / 14.0
    dry = (X[:, 3] - 0.50) / 0.22
    therm = (X[:, 4] - 0.35) / 0.24

    # Interaction: dry air (negative hum) combined with strong wind sharply increases fire odds
    low_hum_high_wind = np.maximum(0.0, -hum) * np.maximum(0.0, wind)

    logits = (
        -1.75
        + 1.65 * temp
        - 1.85 * hum
        + 1.35 * wind
        + 1.75 * dry
        + 2.35 * therm
        + 1.15 * low_hum_high_wind
    )
    return logits


def _sample_scene_features(rng: np.random.Generator, n_cells: int) -> np.ndarray:
    """Generate realistic correlated steppe telemetry for one synthetic scene."""
    # Each scene has its own regional weather regime (prevents i.i.d. oversimplification)
    regime_shift = rng.normal(0.0, 0.55)

    temp = np.clip(rng.normal(27.0 + 5.5 * regime_shift, 6.0, size=n_cells), 8.0, 48.0)
    humidity = np.clip(rng.normal(44.0 - 12.0 * regime_shift, 14.0, size=n_cells), 6.0, 88.0)
    wind = np.clip(rng.normal(24.0 + 7.5 * regime_shift, 11.5, size=n_cells), 2.0, 65.0)
    dryness = np.clip(rng.normal(0.48 + 0.14 * regime_shift, 0.20, size=n_cells), 0.05, 0.98)
    thermal = np.clip(
        0.18 + 0.28 * dryness + 0.006 * (temp - 20.0) + rng.normal(0.0, 0.20, size=n_cells),
        0.02,
        0.99,
    )
    return np.column_stack([temp, humidity, wind, dryness, thermal])


def make_dataset(
    seed: int = 42,
    n_scenes: int = 30,
    cells_per_scene: int = 100,
    label_noise: float = 0.02,
) -> Dict[str, np.ndarray]:
    """Generate a reproducible scene-grouped 3-way dataset (train / val / test).

    Splitting by independent scenes (60% train / 20% val / 20% test) eliminates
    spatial data leakage (Course Lecture 8, Slide 64). Labels include stochastic
    Bernoulli sampling from the physical odds plus small label noise so model
    evaluation reflects realistic uncertainty (~25-35% wildfire prevalence).
    """
    rng = np.random.default_rng(seed)

    scenes_X: List[np.ndarray] = []
    scenes_y: List[np.ndarray] = []

    for _ in range(n_scenes):
        X_s = _sample_scene_features(rng, cells_per_scene)
        logits = _true_fire_logit(X_s)
        probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -30.0, 30.0)))
        y_s = (rng.random(cells_per_scene) < probs).astype(np.int64)

        # Realistic reporting/label noise
        if label_noise > 0.0:
            flip_mask = rng.random(cells_per_scene) < label_noise
            y_s = np.where(flip_mask, 1 - y_s, y_s)

        scenes_X.append(X_s)
        scenes_y.append(y_s)

    n_train = max(1, int(round(0.60 * n_scenes)))
    n_val = max(1, int(round(0.20 * n_scenes)))

    X_train = np.vstack(scenes_X[:n_train])
    y_train = np.concatenate(scenes_y[:n_train])
    X_val = np.vstack(scenes_X[n_train : n_train + n_val])
    y_val = np.concatenate(scenes_y[n_train : n_train + n_val])
    X_test = np.vstack(scenes_X[n_train + n_val :])
    y_test = np.concatenate(scenes_y[n_train + n_val :])

    return {
        "X_train": X_train,
        "y_train": y_train,
        "X_val": X_val,
        "y_val": y_val,
        "X_test": X_test,
        "y_test": y_test,
    }


def make_preset_map(
    preset_id: str = "abai_high_wind",
    seed: int = 42,
    grid_size: int = 10,
    wind_override: float | None = None,
    dryness_boost: float = 0.0,
) -> SectorMap:
    """Create a deterministic, visually distinct 10x10 Kazakhstan steppe map."""
    if preset_id not in PRESET_METADATA:
        raise ValueError(f"Unknown preset '{preset_id}'. Valid: {list(PRESET_METADATA)}")

    rng = np.random.default_rng(seed)
    R = C = grid_size
    features = np.zeros((R, C, 5), dtype=np.float64)
    terrain = np.zeros((R, C), dtype=np.int64)
    obstacles = np.zeros((R, C), dtype=bool)
    elevation = np.zeros((R, C), dtype=np.float64)

    # West Fire Station -> East Target Settlement across the central steppe corridor
    start = (R // 2, 0)
    goal = (R // 2, C - 1)

    if preset_id == "abai_high_wind":
        base_temp, base_hum, base_wind, base_dry, base_therm = 21.0, 56.0, 22.0, 0.34, 0.14
        wind_level = 0.85
        initial_resource = "High"
        # Intense wildfire front squarely blocking the central BFS straight-line corridor (row 4-6, cols 3-6)
        hotspots = [(5, 3, 1.45, 1.15), (5, 5, 1.55, 1.20), (4, 4, 1.45, 1.10), (5, 6, 1.35, 1.05)]
        obstacle_cells = [(2, 4), (2, 5), (8, 3), (8, 6)]
    elif preset_id == "kostanay_dry_steppe":
        base_temp, base_hum, base_wind, base_dry, base_therm = 20.5, 57.0, 19.0, 0.33, 0.14
        wind_level = 0.52
        initial_resource = "High"
        hotspots = [(5, 4, 1.45, 0.85), (5, 5, 1.45, 0.88), (4, 5, 1.35, 0.72)]
        obstacle_cells = [(1, 4), (2, 4), (8, 5), (7, 7)]
    else:  # akmola_sensor_noise
        base_temp, base_hum, base_wind, base_dry, base_therm = 18.5, 64.0, 13.0, 0.26, 0.11
        wind_level = 0.22
        initial_resource = "High"
        hotspots = [(5, 4, 1.30, 0.48), (4, 6, 1.25, 0.42)]
        obstacle_cells = [(2, 6), (3, 6), (7, 3)]

    if wind_override is not None:
        wind_level = float(np.clip(wind_override, 0.0, 1.0))
        base_wind = 8.0 + 52.0 * wind_level

    for r in range(R):
        for c in range(C):
            # Smooth synthetic steppe topography for 3D elevation & terrain types
            ridge = 0.32 * np.sin(r * 0.55 + 0.4) * np.cos(c * 0.55) + 0.35
            elev = float(np.clip(ridge + rng.normal(0.0, 0.06), 0.05, 0.85))
            elevation[r, c] = elev

            # Compute radial proximity to regional fire hotspots
            heat_intensity = 0.0
            for hr, hc, radius, strength in hotspots:
                dist = np.hypot(r - hr, c - hc)
                heat_intensity += strength * float(np.exp(-(dist ** 2) / (2.0 * (radius ** 2))))
            heat_intensity = float(np.clip(heat_intensity, 0.0, 1.35))

            temp = np.clip(base_temp + 14.0 * heat_intensity + rng.normal(0.0, 1.4), 8.0, 48.0)
            hum = np.clip(base_hum - 26.0 * heat_intensity + rng.normal(0.0, 2.5), 6.0, 88.0)
            wind = np.clip(base_wind + 10.0 * heat_intensity + rng.normal(0.0, 2.0), 2.0, 65.0)
            dry = np.clip(base_dry + 0.34 * heat_intensity + dryness_boost + rng.normal(0.0, 0.04), 0.05, 0.98)
            therm = np.clip(base_therm + 0.62 * heat_intensity + rng.normal(0.0, 0.04), 0.02, 0.99)

            features[r, c] = [temp, hum, wind, dry, therm]

            if elev > 0.62:
                terrain[r, c] = 2  # Rocky Ridge
            elif dry > 0.56:
                terrain[r, c] = 1  # Dry Shrub
            else:
                terrain[r, c] = 0  # Steppe Plain

    # Apply impassable natural barriers (ravines / lakes), keeping start & goal clear
    for r, c in obstacle_cells:
        if 0 <= r < R and 0 <= c < C and (r, c) not in (start, goal):
            obstacles[r, c] = True
            terrain[r, c] = 3
            elevation[r, c] = 0.96

    # Keep base station (start) safe and plain
    terrain[start] = 0
    obstacles[start] = False
    features[start] = [19.0, 62.0, max(8.0, base_wind * 0.5), 0.25, 0.08]

    meta = PRESET_METADATA[preset_id]
    return SectorMap(
        preset_id=preset_id,
        title=meta["title"],
        region=meta["region"],
        description=meta["description"],
        seed=seed,
        rows=R,
        cols=C,
        features=features,
        terrain=terrain,
        obstacles=obstacles,
        elevation=elevation,
        start=start,
        goal=goal,
        wind_level=wind_level,
        initial_resource=initial_resource,
    )
