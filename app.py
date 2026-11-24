"""SteppeGuard AI — FastAPI Server & REST API.

Serves:
- GET  /api/health      : Server & model health check
- GET  /api/presets     : Available Kazakhstan steppe scenario presets
- POST /api/run         : Full integrated ML -> A*/BFS/UCS -> MDP pipeline
- POST /api/sensor      : Live Week 6 Bayesian Watchtower Sensor Update + re-plan
- GET  /api/benchmarks  : Precomputed 30-seed benchmark summary
- GET  /                : Interactive 3D Web UI (mounted once static/index.html is built)
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from src.data import PRESET_METADATA
from src.pipeline import SteppeGuardEngine

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
RESULTS_DIR = BASE_DIR / "results"

app = FastAPI(
    title="SteppeGuard AI — Wildfire Risk Intelligence & Decision System",
    version="1.0.0",
)

engine = SteppeGuardEngine()


def _check_finite(val: Optional[float], name: str) -> Optional[float]:
    if val is not None and not math.isfinite(val):
        raise ValueError(f"{name} must be a finite number.")
    return val


class SensorEvent(BaseModel):
    row: int = Field(ge=0, le=9)
    col: int = Field(ge=0, le=9)
    alert: bool = True


class RunRequest(BaseModel):
    preset_id: str = "abai_high_wind"
    seed: int = Field(default=42, ge=0, le=100000)
    risk_lambda: float = Field(default=3.5, ge=0.0, le=12.0)
    gamma: float = Field(default=0.90, gt=0.05, lt=0.999)
    tau: Optional[float] = Field(default=None, ge=0.05, le=0.95)
    wind_override: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    dryness_boost: float = Field(default=0.0, ge=-0.4, le=0.4)
    resource_level: Optional[Literal["High", "Low"]] = None
    model_choice: Literal["logistic_regression", "gaussian_nb"] = "logistic_regression"
    sensor_events: List[SensorEvent] = Field(default_factory=list)
    extra_obstacles: List[Tuple[int, int]] = Field(default_factory=list)
    inspect_cell: Optional[Tuple[int, int]] = None

    @field_validator("risk_lambda", "gamma", "tau", "wind_override", "dryness_boost")
    @classmethod
    def validate_finite(cls, v: Optional[float], info: Any) -> Optional[float]:
        return _check_finite(v, info.field_name)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "project": "SteppeGuard AI",
        "selected_tau": engine.val_tau,
        "test_f1_lr": engine.ml_evaluation["logistic_regression"]["f1"],
        "test_f1_gnb": engine.ml_evaluation["gaussian_nb"]["f1"],
    }


@app.get("/api/presets")
def get_presets() -> Dict[str, Any]:
    return {
        "presets": [
            {"id": pid, **meta}
            for pid, meta in PRESET_METADATA.items()
        ]
    }


@app.post("/api/run")
def run_simulation(req: RunRequest) -> Dict[str, Any]:
    if req.preset_id not in PRESET_METADATA:
        raise HTTPException(status_code=400, detail=f"Unknown preset_id: {req.preset_id}")
    return engine.run_pipeline(
        preset_id=req.preset_id,
        seed=req.seed,
        risk_lambda=req.risk_lambda,
        gamma=req.gamma,
        tau=req.tau,
        wind_override=req.wind_override,
        dryness_boost=req.dryness_boost,
        resource_level=req.resource_level,
        model_choice=req.model_choice,
        sensor_events=[ev.model_dump() for ev in req.sensor_events],
        extra_obstacles=req.extra_obstacles,
        inspect_cell=req.inspect_cell,
    )


@app.post("/api/sensor")
def trigger_sensor(req: RunRequest) -> Dict[str, Any]:
    """Explicit endpoint for live Bayesian watchtower sensor updates + A*/MDP re-plan."""
    if not req.sensor_events:
        raise HTTPException(status_code=400, detail="At least one sensor_event is required.")
    return run_simulation(req)


@app.get("/api/benchmarks")
def get_benchmarks() -> JSONResponse:
    summary_path = RESULTS_DIR / "benchmark_summary.json"
    if not summary_path.exists():
        return JSONResponse(
            status_code=404,
            content={"detail": "Benchmark summary not generated yet. Run scripts/benchmark.py."},
        )
    return JSONResponse(content=json.loads(summary_path.read_text(encoding="utf-8")))


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index() -> Any:
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "SteppeGuard AI API is running. 3D frontend will be served at /static/index.html."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
