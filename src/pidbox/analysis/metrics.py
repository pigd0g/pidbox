from __future__ import annotations

from typing import Dict

import numpy as np


def analyze_step_response(step_response: np.ndarray, t_ms: np.ndarray) -> Dict[str, float]:
    if step_response.size == 0:
        return {
            "steady_state_value": float("nan"),
            "overshoot_pct": float("nan"),
            "rise_time_ms": float("nan"),
            "settling_time_ms": float("nan"),
            "peak_value": float("nan"),
        }

    finite = np.isfinite(step_response)
    if not np.any(finite):
        return {
            "steady_state_value": float("nan"),
            "overshoot_pct": float("nan"),
            "rise_time_ms": float("nan"),
            "settling_time_ms": float("nan"),
            "peak_value": float("nan"),
        }

    tail_window = min(50, len(step_response))
    steady_state = float(np.nanmean(step_response[-tail_window:]))

    peak = float(np.nanmax(step_response))
    overshoot_pct = max(0.0, (peak - 1.0) * 100.0) if np.isfinite(peak) else float("nan")

    rise_candidates = np.where(np.isfinite(step_response) & (step_response >= 0.63))[0]
    rise_time_ms = float(t_ms[rise_candidates[0]]) if len(rise_candidates) else float("nan")

    within_band = np.isfinite(step_response) & (np.abs(step_response - 1.0) <= 0.05)
    if np.any(within_band):
        first_settle = 0
        for i in range(len(within_band)):
            if np.all(within_band[i:]):
                first_settle = i
                break
        settling_time_ms = float(t_ms[first_settle])
    else:
        settling_time_ms = float("nan")

    return {
        "steady_state_value": steady_state,
        "overshoot_pct": float(overshoot_pct),
        "rise_time_ms": rise_time_ms,
        "settling_time_ms": settling_time_ms,
        "peak_value": peak,
    }
