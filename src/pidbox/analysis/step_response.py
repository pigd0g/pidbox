from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from statsmodels.nonparametric.smoothers_lowess import lowess


def smooth_gyro(gyro: np.ndarray, smooth_factor: int) -> np.ndarray:
    smooth_windows = [1, 20, 40, 60]
    idx = min(max(smooth_factor, 1), 4) - 1
    window = smooth_windows[idx]
    if window <= 1 or len(gyro) < 5:
        return gyro.copy()
    frac = min(max(window / len(gyro), 0.001), 1.0)
    t = np.arange(len(gyro))
    return lowess(gyro, t, frac=frac, return_sorted=False)


def get_subsample_factor(signal_length: int, lograte_khz: float) -> int:
    duration_sec = signal_length / max(lograte_khz * 1000.0, 1.0)
    if duration_sec <= 20:
        return 10
    if duration_sec <= 60:
        return 7
    return 3


def deconvolve_step_response(sp: np.ndarray, gy: np.ndarray, wnd: int) -> np.ndarray:
    n = len(sp)
    nfft = 2 ** int(np.ceil(np.log2(n + wnd)))
    sp_f = np.fft.rfft(sp, n=nfft)
    gy_f = np.fft.rfft(gy, n=nfft)

    denom = (np.abs(sp_f) ** 2)
    regularizer = (1e-6 * np.max(denom)) if np.max(denom) > 0 else 1e-9
    h_f = gy_f * np.conj(sp_f) / (denom + regularizer)

    impulse = np.fft.irfft(h_f, n=nfft)[:wnd]
    step = np.cumsum(impulse)
    scale = np.max(np.abs(step))
    if scale > 0:
        step = step / scale
    return step


def compute_step_response_axis(
    sp: np.ndarray,
    gy: np.ndarray,
    lograte_khz: float,
    smooth_factor: int = 2,
    y_correction: bool = False,
    min_input: float = 20.0,
) -> Tuple[Optional[np.ndarray], np.ndarray, int]:
    subsample = get_subsample_factor(len(sp), lograte_khz)
    sp_ds = sp[::subsample]
    gy_ds = gy[::subsample]

    lograte_ds = max(lograte_khz / subsample, 0.001)
    gy_smoothed = smooth_gyro(gy_ds, smooth_factor)

    segment_length = max(1, int(lograte_ds * 2000))
    wnd = max(1, int(lograte_ds * 1000 * 0.5))

    n_segments = len(sp_ds) // segment_length
    traces = []
    for segment_idx in range(n_segments):
        start = segment_idx * segment_length
        end = start + segment_length
        sp_seg = sp_ds[start:end]
        gy_seg = gy_smoothed[start:end]
        if np.max(np.abs(sp_seg)) < min_input:
            continue
        traces.append(deconvolve_step_response(sp_seg, gy_seg, wnd))

    t_ms = np.arange(wnd, dtype=float) / lograte_ds
    if not traces:
        return None, t_ms, subsample

    stacked = np.vstack(traces)
    mean_trace = np.nanmean(stacked, axis=0)

    if y_correction and len(mean_trace):
        mean_trace = mean_trace - mean_trace[0]

    return mean_trace, t_ms, subsample
