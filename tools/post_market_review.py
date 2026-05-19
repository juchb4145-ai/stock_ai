from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from review.post_market import (
    MODE_CHOICES,
    MODE_LIVE,
    MODE_PAPER,
    POST_MARKET_OUTPUT_DEFAULT,
    run_post_market_review,
)


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.post_market_review",
        description="Build a read-only post-market review for condition-search candidates.",
    )
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")
    parser.add_argument("--mode", choices=MODE_CHOICES, default=MODE_PAPER)
    parser.add_argument("--output", default=str(POST_MARKET_OUTPUT_DEFAULT))
    parser.add_argument("--min-missed-opportunity-pct", type=float, default=0.05)
    parser.add_argument("--timeframe", choices=("1m", "5m"), default="1m")
    parser.add_argument("--include-non-traded", action="store_true", help="Accepted for compatibility; non-traded rows are always included.")
    parser.add_argument("--include-data-quality-blocks", action="store_true", help="Accepted for compatibility; data quality rows are always included.")
    parser.add_argument("--json", dest="write_json", action="store_true", default=True, help="Write JSON detail output. Enabled by default.")
    parser.add_argument("--no-json", dest="write_json", action="store_false", help="Skip JSON detail output.")
    parser.add_argument("--condition-captures", default="data/condition_captures.csv")
    parser.add_argument("--trade-log", default="data/trade_log.csv")
    parser.add_argument("--main-log", default="data/main.log")
    parser.add_argument("--intraday-dir", default="data/intraday")
    parser.add_argument("--sector-map", default="data/sector_map.csv")
    parser.add_argument("--theme-map", default="data/theme_map.csv")
    return parser.parse_args(argv)


def _validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"--date must be YYYY-MM-DD, got {value!r}") from exc
    return value


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    target_date = _validate_date(args.date)
    modes = [MODE_PAPER, MODE_LIVE] if args.mode == "all" else [args.mode]
    output_dir = Path(args.output)
    results = []
    for mode in modes:
        result = run_post_market_review(
            target_date=target_date,
            mode=mode,
            output_dir=output_dir,
            condition_capture_path=args.condition_captures,
            trade_log_path=args.trade_log,
            main_log_path=args.main_log,
            intraday_dir=args.intraday_dir,
            sector_map_path=args.sector_map,
            theme_map_path=args.theme_map,
            min_missed_opportunity_pct=args.min_missed_opportunity_pct,
            timeframe=args.timeframe,
            write_json=args.write_json,
        )
        results.append(result)

    for result in results:
        paths = result.paths
        traded = sum(1 for row in result.rows if row.traded)
        missed = sum(1 for row in result.rows if row.missed_opportunity)
        print(
            f"{result.mode}: detected={len(result.rows)} traded={traded} missed={missed}",
            file=sys.stderr,
        )
        if paths:
            print(f"  csv: {paths.csv}", file=sys.stderr)
            print(f"  md: {paths.markdown}", file=sys.stderr)
            if paths.json:
                print(f"  json: {paths.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
