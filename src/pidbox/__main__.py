"""Command-line interface for pidbox blackbox decoding."""

import argparse
import sys

from .decoder import BlackboxDecoder


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pidbox",
        description="Decode Betaflight/INAV blackbox log files.",
    )
    parser.add_argument("log_file", help="Path to the blackbox log file (.BBL/.bfl)")
    parser.add_argument(
        "--inav",
        action="store_true",
        help="Use the INAV decoder instead of the Betaflight decoder",
    )
    parser.add_argument(
        "--index",
        type=int,
        metavar="<num>",
        help="Decode only the log with this 1-based index number",
    )
    parser.add_argument(
        "--limits",
        action="store_true",
        help="Print the limits and units of each field then exit",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write decoded CSV data to stdout instead of a file",
    )
    parser.add_argument("--debug", action="store_true", help="Show extra debug info")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Do not apply field corrections such as calibration",
    )
    parser.add_argument(
        "--merge-gps",
        action="store_true",
        dest="merge_gps",
        help="Merge GPS data into the main CSV output",
    )
    parser.add_argument("--prefix", metavar="<prefix>", help="Output filename prefix")
    parser.add_argument(
        "--simulate-current-meter",
        metavar="<sim>",
        dest="simulate_current_meter",
        help="Simulate the onboard current meter (<shunt>/<offset>)",
    )
    parser.add_argument(
        "--unit-amperage",
        choices=["milliamps", "amps"],
        metavar="<unit>",
        help="Unit for amperage: milliamps or amps (default: amps)",
    )
    parser.add_argument(
        "--unit-altitude",
        choices=["feet", "meters"],
        metavar="<unit>",
        help="Unit for altitude: feet or meters (default: meters)",
    )
    parser.add_argument(
        "--unit-velocity",
        choices=["kmh", "ms", "mph"],
        metavar="<unit>",
        help="Unit for velocity: kmh, ms, or mph (default: ms)",
    )
    parser.add_argument(
        "--unit-rotation",
        choices=["degrees", "radians"],
        metavar="<unit>",
        help="Unit for rotation: degrees or radians (default: degrees)",
    )
    parser.add_argument(
        "--unit-frame-time",
        choices=["us", "ms", "s"],
        metavar="<unit>",
        help="Unit for frame time: us, ms, or s (default: us)",
    )
    parser.add_argument(
        "--unit-acceleration",
        choices=["mss", "gs"],
        metavar="<unit>",
        help="Unit for acceleration: mss or gs (default: mss)",
    )
    parser.add_argument(
        "--unit-gps-speed",
        choices=["mps", "kph", "mph"],
        metavar="<unit>",
        help="Unit for GPS speed: mps, kph, or mph (default: mps)",
    )
    parser.add_argument(
        "--unit-magnetometer",
        choices=["raw", "gauss"],
        metavar="<unit>",
        help="Unit for magnetometer: raw or gauss (default: gauss)",
    )
    parser.add_argument(
        "--declination",
        type=float,
        metavar="<angle>",
        help="Magnetic declination angle (degrees) for true-north GPS heading",
    )
    parser.add_argument(
        "--declination-dec",
        type=float,
        metavar="<angle>",
        dest="declination_dec",
        help="Declination as a decimal degree value (e.g. -6.3)",
    )

    args = parser.parse_args()

    decoder = BlackboxDecoder(inav=args.inav)
    try:
        result = decoder.decode(
            args.log_file,
            index=args.index,
            limits=args.limits,
            stdout=args.stdout,
            debug=args.debug,
            raw=args.raw,
            merge_gps=args.merge_gps,
            prefix=args.prefix,
            simulate_current_meter=args.simulate_current_meter,
            unit_amperage=args.unit_amperage,
            unit_altitude=args.unit_altitude,
            unit_velocity=args.unit_velocity,
            unit_rotation=args.unit_rotation,
            unit_frame_time=args.unit_frame_time,
            unit_acceleration=args.unit_acceleration,
            unit_gps_speed=args.unit_gps_speed,
            unit_magnetometer=args.unit_magnetometer,
            declination=args.declination,
            declination_dec=args.declination_dec,
        )
        if result.stdout:
            print(result.stdout, end="")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

