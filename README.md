# pidbox

Command-line and MCP tools for analyzing PID loop step responses from Betaflight/INAV Blackbox logs.

## Features

- Decodes `.bbl` / `.bfl` logs using the Python `orangebox` library (no external executables).
- Auto-detects and parses multiple sessions directly from the log file.
- Computes PTB-style step responses for roll, pitch, and yaw.
- Handles multiple sessions in a single Blackbox file and overlays them for comparison.
- Exports:
	- PNG plots (per session + overlay)
	- CSV points
	- Parquet points
	- CSV metrics + JSON metadata
- Provides a stdio MCP server using the same shared analysis pipeline as the CLI.

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pidbox --help
```

## CLI Usage

Analyze a Blackbox log:

```powershell
python -m pidbox analyze C:\path\to\flight.bbl
```

Optional flags:

```powershell
python -m pidbox analyze C:\path\to\flight.bbl `
	--smooth-factor 2 `
	--min-input 20 `
	--y-correction
```

Output folder format:

```text
analysis/YYYYMMDD_HHMMSS_<input_stem>/
```

Contains:

- `step_response_session_XXX.png`
- `step_response_overlay.png`
- `step_response_points.csv`
- `step_response_points.parquet`
- `step_response_metrics.csv`
- `metadata.json`

## MCP Server (stdio)

Start the MCP server:

```powershell
python -m pidbox mcp-server
```

Available MCP tools:

- `analyze_log`
- `list_sessions`
- `get_axis_metrics`
- `get_output_paths`
