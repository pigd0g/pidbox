from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List, Tuple


def _candidate_decoder_paths(project_root: Path, decoder: str) -> List[Path]:
    decoder_dir = project_root / "blackbox-decode"
    auto = [
        decoder_dir / "blackbox_decode.exe",
        decoder_dir / "blackbox_decode_INAV.exe",
    ]
    if decoder == "auto":
        return auto
    if decoder == "betaflight":
        return [auto[0]]
    if decoder == "inav":
        return [auto[1]]
    return [Path(decoder)]


def _collect_csvs(log_path: Path) -> List[Path]:
    stem = log_path.stem
    pattern = re.compile(rf"^{re.escape(stem)}[._](\d+)\.csv$", flags=re.IGNORECASE)
    candidates = list(log_path.parent.glob(f"{stem}_*.csv")) + list(log_path.parent.glob(f"{stem}.*.csv"))
    unique = {candidate.resolve(): candidate for candidate in candidates}.values()
    return sorted([candidate for candidate in unique if pattern.match(candidate.name)])


def _cleanup_decode_artifacts(log_path: Path) -> None:
    stem = log_path.stem
    for ext in ("*.event", "*.gps.csv", "*.gps.gpx"):
        for sep in ("_", "."):
            for file_path in log_path.parent.glob(f"{stem}{sep}{ext}"):
                file_path.unlink(missing_ok=True)


def decode_blackbox(log_path: Path, project_root: Path, decoder: str = "auto") -> Tuple[str, List[Path]]:
    decoder_candidates = _candidate_decoder_paths(project_root, decoder)
    if not decoder_candidates:
        raise RuntimeError("No decoder candidates configured")

    decode_errors = []
    for decoder_path in decoder_candidates:
        if not decoder_path.exists():
            decode_errors.append(f"Missing decoder: {decoder_path}")
            continue

        cmd = [str(decoder_path), str(log_path.name)]
        cmdline = subprocess.list2cmdline(cmd)
        print(f"[pidbox] decode cwd: {log_path.parent}")
        print(f"[pidbox] decode cmd: {cmdline}")
        run = subprocess.run(
            cmd,
            cwd=str(log_path.parent),
            capture_output=True,
            text=True,
            check=False,
        )

        _cleanup_decode_artifacts(log_path)
        csv_files = _collect_csvs(log_path)

        if run.returncode == 0 and csv_files:
            return decoder_path.name, csv_files

        decode_errors.append(
            f"{decoder_path.name} failed rc={run.returncode}: {run.stderr.strip() or run.stdout.strip() or 'no output'}"
        )

    raise RuntimeError("Decode failed. " + " | ".join(decode_errors))


def get_session_number(csv_path: Path) -> int:
    match = re.search(r"[._](\d+)\.csv$", csv_path.name)
    return int(match.group(1)) if match else 1
