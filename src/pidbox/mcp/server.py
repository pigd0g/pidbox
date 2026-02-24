from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from pidbox.analysis.pipeline import analyze_blackbox
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
        return _result_summary(result)

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
