from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate Bukit Jalil National Stadium events into static calendar files."
    )
    parser.add_argument(
        "--source-config",
        type=Path,
        default=Path("data/sources.json"),
        help="Path to source registry JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("public"),
        help="Output directory for events.ics/events.json/sources.json/health.json.",
    )
    parser.add_argument(
        "--manual-events",
        type=Path,
        default=Path("data/manual_events.json"),
        help="Path to confirmed seed events JSON.",
    )
    args = parser.parse_args(argv)
    return run_pipeline(args.source_config, args.output, manual_events_path=args.manual_events)
