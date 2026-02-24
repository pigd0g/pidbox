from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


REQUIRED_GYRO = ["gyroADC[0]", "gyroADC[1]", "gyroADC[2]"]


def _looks_like_header(line: str) -> bool:
    lowered = line.lower()
    if "," not in lowered:
        return False
    tokens = ("time", "gyroadc", "setpoint", "axisrate", "loopiteration")
    return any(token in lowered for token in tokens)


def load_blackbox_csv(csv_path: Path) -> pd.DataFrame:
    with csv_path.open("r", encoding="latin-1", errors="replace") as handle:
        line1 = handle.readline()
        line2 = handle.readline()

    if _looks_like_header(line1):
        df = pd.read_csv(csv_path, header=0, low_memory=False, skipinitialspace=True)
    elif _looks_like_header(line2):
        df = pd.read_csv(csv_path, skiprows=1, header=0, low_memory=False, skipinitialspace=True)
    else:
        header_row = pd.read_csv(csv_path, skiprows=1, nrows=0, skipinitialspace=True)
        df = pd.read_csv(csv_path, skiprows=2, header=None, low_memory=False, skipinitialspace=True)
        df.columns = list(header_row.columns)

    df.columns = [str(column).strip() for column in df.columns]
    return df


def _time_column(df: pd.DataFrame) -> str:
    candidates = ["time (us)", "time_us", "time"]
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"No time column found. Expected one of: {candidates}")


def compute_log_rate_khz(time_us: np.ndarray) -> float:
    elapsed = time_us - time_us[0]
    dt_us = float(np.median(np.diff(elapsed)))
    if dt_us <= 0:
        raise ValueError("Invalid time delta for log rate")
    return round((1_000_000.0 / dt_us) / 1000.0, 1)


def axis_column_map(df: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    for column in REQUIRED_GYRO:
        if column not in df.columns:
            raise KeyError(f"Missing required gyro column: {column}")

    if all(f"setpoint[{i}]" in df.columns for i in range(3)):
        setpoint_prefix = "setpoint"
    elif all(f"axisRate[{i}]" in df.columns for i in range(3)):
        setpoint_prefix = "axisRate"
    else:
        raise KeyError("Missing setpoint columns. Expected setpoint[0..2] or axisRate[0..2]")

    return {
        axis: {
            "setpoint": f"{setpoint_prefix}[{idx}]",
            "gyro": f"gyroADC[{idx}]",
            "axisP": f"axisP[{idx}]",
            "axisI": f"axisI[{idx}]",
            "axisD": f"axisD[{idx}]",
            "axisF": f"axisF[{idx}]",
        }
        for idx, axis in enumerate(("roll", "pitch", "yaw"))
    }


def load_axis_signals(df: pd.DataFrame) -> Dict[str, Dict[str, np.ndarray]]:
    mapping = axis_column_map(df)
    axis_data: Dict[str, Dict[str, np.ndarray]] = {}

    for axis, columns in mapping.items():
        signals = {}
        for name, col in columns.items():
            if col in df.columns:
                signals[name] = df[col].astype(float).to_numpy()
            else:
                signals[name] = np.zeros(len(df), dtype=float)

        signals["pid_error"] = signals["gyro"] - signals["setpoint"]
        signals["pid_sum"] = (
            signals.get("axisP", 0)
            + signals.get("axisI", 0)
            + signals.get("axisD", 0)
            + signals.get("axisF", 0)
        )
        axis_data[axis] = signals

    return axis_data


def load_time_us(df: pd.DataFrame) -> np.ndarray:
    return df[_time_column(df)].astype(float).to_numpy()
