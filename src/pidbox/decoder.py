"""Wrapper around the blackbox_decode executables."""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional


# Locate the bundled executables relative to this file
_PACKAGE_DIR = Path(__file__).parent
_PROJECT_ROOT = _PACKAGE_DIR.parent.parent
_BLACKBOX_DIR = _PROJECT_ROOT / "blackbox-decode"

_EXE_BETAFLIGHT = _BLACKBOX_DIR / "blackbox_decode.exe"
_EXE_INAV = _BLACKBOX_DIR / "blackbox_decode_INAV.exe"


def _get_executable(inav: bool = False) -> Path:
    """Return the path to the appropriate blackbox_decode executable."""
    exe = _EXE_INAV if inav else _EXE_BETAFLIGHT
    if not exe.exists():
        raise FileNotFoundError(f"Executable not found: {exe}")
    return exe


def _build_command(
    exe: Path,
    log_file: str,
    index: Optional[int] = None,
    limits: bool = False,
    stdout: bool = False,
    debug: bool = False,
    raw: bool = False,
    merge_gps: bool = False,
    prefix: Optional[str] = None,
    unit_amperage: Optional[str] = None,
    unit_altitude: Optional[str] = None,
    unit_velocity: Optional[str] = None,
    unit_rotation: Optional[str] = None,
    unit_frame_time: Optional[str] = None,
    unit_acceleration: Optional[str] = None,
    unit_gps_speed: Optional[str] = None,
    unit_magnetometer: Optional[str] = None,
    declination: Optional[float] = None,
    declination_dec: Optional[float] = None,
    simulate_current_meter: Optional[str] = None,
) -> List[str]:
    """Build the command line argument list for the decoder."""
    cmd: List[str] = []

    # On non-Windows systems, invoke through Wine
    if platform.system() != "Windows":
        wine = shutil.which("wine")
        if wine is None:
            raise RuntimeError(
                "Wine is required to run blackbox_decode on non-Windows systems "
                "but was not found in PATH."
            )
        cmd.append(wine)

    cmd.append(str(exe))

    if index is not None:
        cmd.extend(["--index", str(index)])
    if limits:
        cmd.append("--limits")
    if stdout:
        cmd.append("--stdout")
    if debug:
        cmd.append("--debug")
    if raw:
        cmd.append("--raw")
    if merge_gps:
        cmd.append("--merge-gps")
    if prefix is not None:
        cmd.extend(["--prefix", prefix])
    if simulate_current_meter is not None:
        cmd.extend(["--simulate-current-meter", simulate_current_meter])
    if unit_amperage is not None:
        cmd.extend(["--unit-amperage", unit_amperage])
    if unit_altitude is not None:
        cmd.extend(["--unit-altitude", unit_altitude])
    if unit_velocity is not None:
        cmd.extend(["--unit-velocity", unit_velocity])
    if unit_rotation is not None:
        cmd.extend(["--unit-rotation", unit_rotation])
    if unit_frame_time is not None:
        cmd.extend(["--unit-frame-time", unit_frame_time])
    if unit_acceleration is not None:
        cmd.extend(["--unit-acceleration", unit_acceleration])
    if unit_gps_speed is not None:
        cmd.extend(["--unit-gps-speed", unit_gps_speed])
    if unit_magnetometer is not None:
        cmd.extend(["--unit-magnetometer", unit_magnetometer])
    if declination is not None:
        cmd.extend(["--declination", str(declination)])
    if declination_dec is not None:
        cmd.extend(["--declination-dec", str(declination_dec)])

    cmd.append(log_file)
    return cmd


class BlackboxDecoder:
    """Decode Betaflight/INAV blackbox log files using the bundled executables.

    Parameters
    ----------
    inav:
        When ``True`` the INAV variant of the decoder is used.  Defaults to
        ``False`` (Betaflight).
    """

    def __init__(self, inav: bool = False) -> None:
        self.inav = inav
        self._exe = _get_executable(inav=inav)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def decode(
        self,
        log_file: str,
        *,
        index: Optional[int] = None,
        limits: bool = False,
        stdout: bool = False,
        debug: bool = False,
        raw: bool = False,
        merge_gps: bool = False,
        prefix: Optional[str] = None,
        unit_amperage: Optional[str] = None,
        unit_altitude: Optional[str] = None,
        unit_velocity: Optional[str] = None,
        unit_rotation: Optional[str] = None,
        unit_frame_time: Optional[str] = None,
        unit_acceleration: Optional[str] = None,
        unit_gps_speed: Optional[str] = None,
        unit_magnetometer: Optional[str] = None,
        declination: Optional[float] = None,
        declination_dec: Optional[float] = None,
        simulate_current_meter: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Decode a blackbox log file.

        Parameters
        ----------
        log_file:
            Path to the ``.BBL`` / ``.bfl`` log file to decode.
        index:
            Decode only the flight log at this 1-based index.
        limits:
            Print the limits and units of each field then exit.
        stdout:
            Write decoded CSV data to stdout instead of a file.
        debug:
            Show extra debugging information.
        raw:
            Do not apply field corrections such as calibration.
        merge_gps:
            Merge GPS data into the main CSV output.
        prefix:
            Override the output filename prefix.
        simulate_current_meter:
            Simulate the onboard current meter (``<shunt>/<offset>`` string).
        unit_amperage:
            Unit for amperage: ``milliamps`` or ``amps``.
        unit_altitude:
            Unit for altitude: ``feet`` or ``meters``.
        unit_velocity:
            Unit for velocity: ``kmh``, ``ms``, or ``mph``.
        unit_rotation:
            Unit for rotation: ``degrees`` or ``radians``.
        unit_frame_time:
            Unit for frame time: ``us``, ``ms``, or ``s``.
        unit_acceleration:
            Unit for acceleration: ``mss`` or ``gs``.
        unit_gps_speed:
            Unit for GPS speed: ``mps``, ``kph``, or ``mph``.
        unit_magnetometer:
            Unit for magnetometer: ``raw`` or ``gauss``.
        declination:
            Magnetic declination angle (degrees) for true-north GPS heading.
        declination_dec:
            Declination as a decimal degree value (e.g. ``-6.3``).

        Returns
        -------
        subprocess.CompletedProcess
            The result of the decoder subprocess including ``returncode``,
            ``stdout``, and ``stderr``.

        Raises
        ------
        FileNotFoundError
            If ``log_file`` does not exist.
        RuntimeError
            If the decoder exits with a non-zero return code.
        """
        if not os.path.isfile(log_file):
            raise FileNotFoundError(f"Log file not found: {log_file}")

        cmd = _build_command(
            self._exe,
            log_file,
            index=index,
            limits=limits,
            stdout=stdout,
            debug=debug,
            raw=raw,
            merge_gps=merge_gps,
            prefix=prefix,
            unit_amperage=unit_amperage,
            unit_altitude=unit_altitude,
            unit_velocity=unit_velocity,
            unit_rotation=unit_rotation,
            unit_frame_time=unit_frame_time,
            unit_acceleration=unit_acceleration,
            unit_gps_speed=unit_gps_speed,
            unit_magnetometer=unit_magnetometer,
            declination=declination,
            declination_dec=declination_dec,
            simulate_current_meter=simulate_current_meter,
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"blackbox_decode failed (exit {result.returncode}):\n{result.stderr}"
            )
        return result
