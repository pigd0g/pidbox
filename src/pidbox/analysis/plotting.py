from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt

from pidbox.models import SessionResult


COLORS = {"roll": "tab:blue", "pitch": "tab:orange", "yaw": "tab:green"}


def plot_session_step_response(session: SessionResult, output_path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    for ax, axis_name in zip(axes, ("roll", "pitch", "yaw")):
        axis_data = session.axes[axis_name]
        gains = session.pidf.get(axis_name, {})
        ax.plot(axis_data.t_ms, axis_data.step_response, color=COLORS[axis_name], linewidth=1.8)
        ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.8)
        ax.axhline(0.0, color="black", linewidth=0.6)
        ax.set_xlim(0, 500)
        ax.set_ylim(-0.2, 1.75)
        ax.set_xlabel("Time (ms)")
        ax.set_title(
            f"{axis_name.capitalize()} P={gains.get('P', 0):.0f} I={gains.get('I', 0):.0f} D={gains.get('D', 0):.0f} FF={gains.get('FF', 0):.0f}"
        )
        ax.grid(alpha=0.3)

    axes[0].set_ylabel("Normalized Response")
    fig.suptitle(f"Step Response — Session {session.session_index:03d}")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_overlay_step_response(sessions: Iterable[SessionResult], output_path: Path) -> Path:
    session_list = list(sessions)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    for ax, axis_name in zip(axes, ("roll", "pitch", "yaw")):
        for session in session_list:
            axis_data = session.axes[axis_name]
            ax.plot(axis_data.t_ms, axis_data.step_response, linewidth=1.1, label=f"S{session.session_index:03d}")
        ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.8)
        ax.set_xlim(0, 500)
        ax.set_ylim(-0.2, 1.75)
        ax.set_xlabel("Time (ms)")
        ax.set_title(axis_name.capitalize())
        ax.grid(alpha=0.3)

    axes[0].set_ylabel("Normalized Response")
    if session_list:
        axes[-1].legend(fontsize=8)
    fig.suptitle("Step Response Overlay")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
