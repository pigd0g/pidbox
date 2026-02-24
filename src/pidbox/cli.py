from __future__ import annotations

import argparse
from pathlib import Path

from pidbox.analysis.pipeline import analyze_blackbox
from pidbox.mcp.server import run_stdio_server
from pidbox.models import AnalysisConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pidbox", description="PID blackbox step response analysis")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Decode and analyze blackbox log")
    analyze.add_argument("input", type=Path, help="Path to .bbl/.bfl log")
    analyze.add_argument("--output-dir", type=Path, default=None, help="Override output root directory")
    analyze.add_argument("--smooth-factor", type=int, default=2, choices=[1, 2, 3, 4], help="LOWESS smoothing level")
    analyze.add_argument("--min-input", type=float, default=20.0, help="Minimum setpoint threshold (deg/s)")
    analyze.add_argument("--y-correction", action="store_true", help="Apply y-axis offset correction for yaw")
    analyze.add_argument(
        "--decoder",
        choices=["orangebox"],
        default="orangebox",
        help="Decoder backend (orangebox)",
    )
    analyze.add_argument("--no-csv", action="store_true", help="Disable CSV export")
    analyze.add_argument("--no-parquet", action="store_true", help="Disable Parquet export")

    mcp_cmd = sub.add_parser("mcp-server", help="Run stdio MCP server")
    mcp_cmd.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Project root containing blackbox-decode folder",
    )

    return parser


def run_analyze(args: argparse.Namespace) -> int:
    project_root = Path(__file__).resolve().parents[2]
    config = AnalysisConfig(
        smooth_factor=args.smooth_factor,
        y_correction=args.y_correction,
        min_input=args.min_input,
        decoder=args.decoder,
        export_csv=not args.no_csv,
        export_parquet=not args.no_parquet,
    )

    result = analyze_blackbox(args.input.resolve(), project_root, args.output_dir, config)

    print(f"Input: {result.input_path}")
    print(f"Decoder: {result.decoder_used}")
    print(f"Output: {result.output_dir}")
    print(f"Sessions analyzed: {len(result.sessions)}")
    if result.overlay_png:
        print(f"Overlay plot: {result.overlay_png}")
    if result.flat_csv:
        print(f"CSV points: {result.flat_csv}")
    if result.flat_parquet:
        print(f"Parquet points: {result.flat_parquet}")
    if result.metrics_csv:
        print(f"Metrics CSV: {result.metrics_csv}")
    if result.metadata_json:
        print(f"Metadata JSON: {result.metadata_json}")

    return 0


def run_mcp(args: argparse.Namespace) -> int:
    run_stdio_server(project_root=args.project_root.resolve())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return run_analyze(args)
    if args.command == "mcp-server":
        return run_mcp(args)

    parser.error(f"Unknown command: {args.command}")
    return 2
