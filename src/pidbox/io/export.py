from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd

from pidbox.models import SessionResult


def create_output_dir(input_path: Path, base_output_dir: Path | None = None) -> Path:
    root = base_output_dir or input_path.parent / "analysis"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / f"{timestamp}_{input_path.stem}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_flat_frames(sessions: Iterable[SessionResult]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    points: List[dict] = []
    metrics: List[dict] = []

    for session in sessions:
        for axis in ("roll", "pitch", "yaw"):
            axis_data = session.axes[axis]
            for t_ms, value in zip(axis_data.t_ms, axis_data.step_response):
                points.append(
                    {
                        "session": session.session_index,
                        "axis": axis,
                        "t_ms": t_ms,
                        "step_response": value,
                        "log_rate_khz": session.log_rate_khz,
                        "source_csv": str(session.csv_path),
                    }
                )

            metric_row = {"session": session.session_index, "axis": axis}
            metric_row.update(axis_data.metrics)
            metrics.append(metric_row)

    return pd.DataFrame(points), pd.DataFrame(metrics)


def export_flat_files(
    sessions: Iterable[SessionResult],
    output_dir: Path,
    export_csv: bool,
    export_parquet: bool,
) -> Tuple[Path | None, Path | None, Path]:
    points_df, metrics_df = build_flat_frames(sessions)

    csv_path = None
    parquet_path = None
    metrics_path = output_dir / "step_response_metrics.csv"

    if export_csv:
        csv_path = output_dir / "step_response_points.csv"
        points_df.to_csv(csv_path, index=False)

    if export_parquet:
        parquet_path = output_dir / "step_response_points.parquet"
        points_df.to_parquet(parquet_path, index=False)

    metrics_df.to_csv(metrics_path, index=False)
    return csv_path, parquet_path, metrics_path


def export_metadata_json(input_path: Path, output_dir: Path, decoder: str, sessions: Iterable[SessionResult]) -> Path:
    metadata_path = output_dir / "metadata.json"
    payload = {
        "input": str(input_path),
        "decoder": decoder,
        "generated_at": datetime.now().isoformat(),
        "sessions": [
            {
                "session_index": s.session_index,
                "csv_path": str(s.csv_path),
                "log_rate_khz": s.log_rate_khz,
                "sample_count": s.sample_count,
                "pidf": s.pidf,
            }
            for s in sessions
        ],
    }
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return metadata_path
