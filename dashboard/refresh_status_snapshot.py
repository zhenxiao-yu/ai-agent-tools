"""
Refresh Dashboard Status Snapshot
=================================
CLI entry point for one-shot or watch-mode snapshot refreshes.
"""
from __future__ import annotations

import argparse
import time

from dashboard.services import describe_service_status_snapshot, refresh_service_status_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh persisted dashboard service snapshots.")
    parser.add_argument("--include-optional", action="store_true", help="Include slower optional tool checks.")
    parser.add_argument("--include-model-details", action="store_true", help="Include local model and runtime details.")
    parser.add_argument("--watch", action="store_true", help="Keep refreshing in a loop.")
    parser.add_argument("--interval", type=int, default=90, help="Seconds between watch-mode refreshes.")
    return parser


def run_once(include_optional: bool, include_model_details: bool) -> None:
    status = refresh_service_status_snapshot(
        include_optional=include_optional,
        include_model_details=include_model_details,
    )
    print(describe_service_status_snapshot(status))
    print(
        "Signals:",
        f"ollama={'up' if status['ollama'] else 'down'}",
        f"proxy={'up' if status['proxy'] else 'down'}",
        f"github={'up' if status['github'] else 'down'}",
        f"errors={len(status.get('errors', []))}",
    )


def main() -> None:
    args = build_parser().parse_args()
    interval = max(15, args.interval)

    while True:
        run_once(args.include_optional, args.include_model_details)
        if not args.watch:
            return
        time.sleep(interval)


if __name__ == "__main__":
    main()
