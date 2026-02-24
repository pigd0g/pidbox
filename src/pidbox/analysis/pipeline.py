from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np

from pidbox.analysis.metrics import analyze_step_response
from pidbox.analysis.plotting import plot_overlay_step_response, plot_session_step_response
from pidbox.analysis.step_response import compute_step_response_axis
from pidbox.io.csv_loader import compute_log_rate_khz, load_axis_signals, load_blackbox_csv, load_time_us
from pidbox.io.decode import decode_blackbox, get_session_number
from pidbox.io.export import create_output_dir, export_flat_files, export_metadata_json
from pidbox.io.header import extract_pidf, parse_setup_info
from pidbox.models import AXES, AnalysisConfig, AnalysisResult, AxisStepResponse, SessionResult


def analyze_blackbox(
    input_path: Path,
    project_root: Path,
    output_dir: Path | None,
    config: AnalysisConfig,
) -> AnalysisResult:
    if not input_path.exists():
        raise FileNotFoundError(f"Input log not found: {input_path}")

    decoder_used, csv_paths = decode_blackbox(input_path, project_root, decoder=config.decoder)
    if not csv_paths:
        raise RuntimeError("Decoder produced no session CSV files")

    result_output_dir = create_output_dir(input_path, output_dir)

    sessions: List[SessionResult] = []
    for csv_path in csv_paths:
        df = load_blackbox_csv(csv_path)
        if len(df) < 3:
            continue

        session_index = get_session_number(csv_path)
        setup_info = parse_setup_info(input_path, session_index)
        pidf = extract_pidf(setup_info)

        time_us = load_time_us(df)
        log_rate_khz = compute_log_rate_khz(time_us)
        axis_signals = load_axis_signals(df)

        axis_results = {}
        for axis_name in AXES:
            sp = axis_signals[axis_name]["setpoint"]
            gy = axis_signals[axis_name]["gyro"]
            step_response, t_ms, _ = compute_step_response_axis(
                sp,
                gy,
                log_rate_khz,
                smooth_factor=config.smooth_factor,
                y_correction=config.y_correction and axis_name == "yaw",
                min_input=config.min_input,
            )
            if step_response is None:
                step_response = np.full_like(t_ms, np.nan, dtype=float)
            metrics = analyze_step_response(step_response, t_ms)
            axis_results[axis_name] = AxisStepResponse(
                axis=axis_name,
                t_ms=t_ms.tolist(),
                step_response=step_response.tolist(),
                metrics=metrics,
            )

        session = SessionResult(
            session_index=session_index,
            csv_path=csv_path,
            log_rate_khz=log_rate_khz,
            pidf=pidf,
            axes=axis_results,
            sample_count=len(df),
        )
        sessions.append(session)

    if not sessions:
        raise RuntimeError("No valid decoded sessions available for analysis")

    sessions.sort(key=lambda s: s.session_index)

    per_session_png = []
    for session in sessions:
        out = result_output_dir / f"step_response_session_{session.session_index:03d}.png"
        per_session_png.append(plot_session_step_response(session, out))

    overlay_png = plot_overlay_step_response(sessions, result_output_dir / "step_response_overlay.png")
    flat_csv, flat_parquet, metrics_csv = export_flat_files(
        sessions,
        result_output_dir,
        export_csv=config.export_csv,
        export_parquet=config.export_parquet,
    )
    metadata_json = export_metadata_json(input_path, result_output_dir, decoder_used, sessions)

    return AnalysisResult(
        input_path=input_path,
        output_dir=result_output_dir,
        decoder_used=decoder_used,
        sessions=sessions,
        overlay_png=overlay_png,
        per_session_png=per_session_png,
        flat_csv=flat_csv,
        flat_parquet=flat_parquet,
        metrics_csv=metrics_csv,
        metadata_json=metadata_json,
    )
