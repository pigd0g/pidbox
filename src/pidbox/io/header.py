from __future__ import annotations

from pathlib import Path
from typing import Dict, List


_START_MARKERS = ("Firmware version", "Firmware revision")


def _parse_header_lines(raw_text: str) -> List[str]:
    return raw_text.splitlines()


def _session_ranges(lines: List[str]) -> List[tuple[int, int]]:
    starts = [
        i for i, line in enumerate(lines) if any(marker in line for marker in _START_MARKERS)
    ]
    if not starts:
        return [(0, len(lines) - 1)]

    ranges = []
    for idx, start in enumerate(starts):
        next_start = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        end = next_start - 1
        ranges.append((start, end))
    return ranges


def parse_setup_info(log_path: Path, session_index: int) -> Dict[str, str]:
    raw = log_path.read_bytes().decode("latin-1", errors="replace")
    lines = _parse_header_lines(raw)
    ranges = _session_ranges(lines)

    index = min(max(session_index - 1, 0), len(ranges) - 1)
    start, end = ranges[index]

    setup: Dict[str, str] = {}
    for line in lines[start : end + 1]:
        line = line.strip().replace("\x00", "")
        if not line.startswith("H") or ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lstrip("H").strip()
        value = right.strip()
        if key:
            setup[key] = value
    return setup


def extract_pidf(setup_info: Dict[str, str]) -> Dict[str, Dict[str, float]]:
    def parse_csv(text: str) -> List[float]:
        parts = [p.strip() for p in text.split(",") if p.strip()]
        out = []
        for part in parts[:3]:
            try:
                out.append(float(part))
            except ValueError:
                out.append(0.0)
        while len(out) < 3:
            out.append(0.0)
        return out

    roll = parse_csv(setup_info.get("rollPID", "0,0,0"))
    pitch = parse_csv(setup_info.get("pitchPID", "0,0,0"))
    yaw = parse_csv(setup_info.get("yawPID", "0,0,0"))
    d_min = parse_csv(setup_info.get("d_min", "0,0,0"))
    ff_key = "feedforward_weight" if "feedforward_weight" in setup_info else "ff_weight"
    ff = parse_csv(setup_info.get(ff_key, "0,0,0"))

    return {
        "roll": {"P": roll[0], "I": roll[1], "D": roll[2], "d_min": d_min[0], "FF": ff[0]},
        "pitch": {"P": pitch[0], "I": pitch[1], "D": pitch[2], "d_min": d_min[1], "FF": ff[1]},
        "yaw": {"P": yaw[0], "I": yaw[1], "D": yaw[2], "d_min": d_min[2], "FF": ff[2]},
    }
