from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from orangebox import Parser


def decode_blackbox(log_path: Path, project_root: Path, decoder: str = "orangebox") -> Tuple[str, List[Path]]:
    """
    Decode a Blackbox log into per-session CSV files using the orangebox parser.

    The ``project_root`` and ``decoder`` parameters are retained for backward compatibility
    with previous signatures; decoder selection is ignored because orangebox is the only
    supported backend.
    """
    parser = Parser.load(str(log_path))
    session_count = parser.reader.log_count

    if session_count < 1:
        raise RuntimeError("Decode failed. No sessions found in log file.")

    csv_paths: List[Path] = []
    for session_index in range(1, session_count + 1):
        parser.set_log_index(session_index)
        frames = list(parser.frames())
        if not frames:
            continue

        data = [frame.data for frame in frames]
        df = pd.DataFrame(data, columns=parser.field_names)

        csv_path = log_path.with_name(f"{log_path.stem}_{session_index:03d}.csv")
        df.to_csv(csv_path, index=False)
        csv_paths.append(csv_path)

    if not csv_paths:
        raise RuntimeError("Decode failed. No frames decoded via orangebox.")

    return "orangebox", csv_paths


def get_session_number(csv_path: Path) -> int:
    match = re.search(r"[._](\d+)\.csv$", csv_path.name)
    return int(match.group(1)) if match else 1
