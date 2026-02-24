from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


AXES = ("roll", "pitch", "yaw")


@dataclass
class AnalysisConfig:
    smooth_factor: int = 2
    y_correction: bool = False
    min_input: float = 20.0
    decoder: str = "auto"
    export_csv: bool = True
    export_parquet: bool = True


@dataclass
class AxisStepResponse:
    axis: str
    t_ms: List[float]
    step_response: List[float]
    metrics: Dict[str, float]


@dataclass
class SessionResult:
    session_index: int
    csv_path: Path
    log_rate_khz: float
    pidf: Dict[str, Dict[str, float]]
    axes: Dict[str, AxisStepResponse]
    sample_count: int


@dataclass
class AnalysisResult:
    input_path: Path
    output_dir: Path
    decoder_used: str
    sessions: List[SessionResult]
    overlay_png: Optional[Path] = None
    per_session_png: List[Path] = field(default_factory=list)
    flat_csv: Optional[Path] = None
    flat_parquet: Optional[Path] = None
    metrics_csv: Optional[Path] = None
    metadata_json: Optional[Path] = None
