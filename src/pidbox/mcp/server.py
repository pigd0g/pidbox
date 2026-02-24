from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from pidbox.analysis.pipeline import analyze_blackbox
from pidbox.io.export import build_flat_frames
from pidbox.models import AnalysisConfig


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _result_summary(result) -> Dict[str, Any]:
    return {
        "input": str(result.input_path),
        "output_dir": str(result.output_dir),
        "decoder_used": result.decoder_used,
        "session_count": len(result.sessions),
        "overlay_png": str(result.overlay_png) if result.overlay_png else None,
        "flat_csv": str(result.flat_csv) if result.flat_csv else None,
        "flat_parquet": str(result.flat_parquet) if result.flat_parquet else None,
        "metrics_csv": str(result.metrics_csv) if result.metrics_csv else None,
        "metadata_json": str(result.metadata_json) if result.metadata_json else None,
    }


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _json_safe_records(records: list[dict]) -> list[dict]:
    safe_records = []
    for row in records:
        safe_records.append({key: _json_safe_value(val) for key, val in row.items()})
    return safe_records


def _result_content(result, max_points_rows: int | None = None) -> Dict[str, Any]:
    points_df, metrics_df = build_flat_frames(result.sessions)
    total_points_rows = len(points_df)

    if max_points_rows is not None and max_points_rows >= 0:
        points_df = points_df.head(max_points_rows)

    points_records = _json_safe_records(points_df.to_dict(orient="records"))
    metrics_records = _json_safe_records(metrics_df.to_dict(orient="records"))

    metadata_content: Dict[str, Any] | None = None
    if result.metadata_json and result.metadata_json.exists():
        metadata_content = json.loads(result.metadata_json.read_text(encoding="utf-8"))

    return {
        "step_response_points": points_records,
        "step_response_metrics": metrics_records,
        "metadata": metadata_content,
        "points_row_count": len(points_records),
        "total_points_row_count": total_points_rows,
        "metrics_row_count": len(metrics_records),
        "points_truncated": bool(max_points_rows is not None and len(points_records) < total_points_rows),
    }


def build_server(project_root: Path | None = None) -> FastMCP:
    root = project_root or _default_project_root()
    app = FastMCP("pidbox")

    @app.tool()
    def analyze_log(
        input_path: str,
        smooth_factor: int = 2,
        min_input: float = 20.0,
        y_correction: bool = False,
        export_csv: bool = True,
        export_parquet: bool = True,
        decoder: str = "auto",
        max_points_rows: int | None = None,
    ) -> Dict[str, Any]:
        config = AnalysisConfig(
            smooth_factor=smooth_factor,
            y_correction=y_correction,
            min_input=min_input,
            export_csv=export_csv,
            export_parquet=export_parquet,
            decoder=decoder,
        )
        result = analyze_blackbox(Path(input_path).resolve(), root, None, config)
        payload = _result_summary(result)
        payload.update(_result_content(result, max_points_rows=max_points_rows))
        return payload

    @app.tool()
    def list_sessions(input_path: str, decoder: str = "auto") -> Dict[str, Any]:
        config = AnalysisConfig(decoder=decoder, export_csv=False, export_parquet=False)
        result = analyze_blackbox(Path(input_path).resolve(), root, None, config)
        return {
            "input": input_path,
            "output_dir": str(result.output_dir),
            "sessions": [
                {
                    "session_index": s.session_index,
                    "csv_path": str(s.csv_path),
                    "sample_count": s.sample_count,
                    "log_rate_khz": s.log_rate_khz,
                }
                for s in result.sessions
            ],
        }

    @app.tool()
    def get_axis_metrics(
        input_path: str,
        axis: str,
        decoder: str = "auto",
        smooth_factor: int = 2,
        min_input: float = 20.0,
    ) -> Dict[str, Any]:
        axis_name = axis.lower()
        if axis_name not in {"roll", "pitch", "yaw"}:
            raise ValueError("axis must be one of: roll, pitch, yaw")

        config = AnalysisConfig(
            decoder=decoder,
            smooth_factor=smooth_factor,
            min_input=min_input,
        )
        result = analyze_blackbox(Path(input_path).resolve(), root, None, config)

        return {
            "axis": axis_name,
            "sessions": [
                {
                    "session_index": s.session_index,
                    "metrics": s.axes[axis_name].metrics,
                }
                for s in result.sessions
            ],
            "metrics_csv": str(result.metrics_csv) if result.metrics_csv else None,
        }

    @app.tool()
    def get_output_paths(input_path: str, decoder: str = "auto") -> Dict[str, Any]:
        config = AnalysisConfig(decoder=decoder)
        result = analyze_blackbox(Path(input_path).resolve(), root, None, config)
        return _result_summary(result)

    return app


def run_stdio_server(project_root: Path | None = None) -> None:
    server = build_server(project_root=project_root)
    server.run(transport="stdio")
