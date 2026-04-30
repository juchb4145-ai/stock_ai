"""오늘(또는 지정일) 매매 결과 → 복기 리포트 + 다음 거래일 룰 추천.

사용법:
    python analyze_today.py                          # trade_log 의 마지막 날짜 자동
    python analyze_today.py 2026-04-30                # 특정 날짜 지정
    python analyze_today.py 2026-04-30 --intraday-dir tests/fixtures/intraday

출력:
    data/reviews/trade_review_YYYY-MM-DD.csv     거래 단위 상세
    data/reviews/daily_review_YYYY-MM-DD.md      사람용 요약
    data/reviews/rule_overrides_YYYY-MM-DD.json  내일 부팅 시 적용할 룰 오버라이드

분봉 정밀 메트릭:
    fetch_minute_bars.py 가 미리 받아둔 data/intraday/YYYYMMDD/<code>.csv 가
    있으면 review.intraday 가 1분봉 기반 정밀 메트릭 + D 피처를 채운다.
    없는 종목은 5분봉 라벨로 fallback 하고, 두 라벨 다 없으면 missing 리스트에
    기록되어 리포트에 노출된다.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from review import (
    attach_metrics,
    classify_trades,
    load_trades,
    recommend_rules,
    write_reports,
)
from review.intraday import INTRADAY_DIR_DEFAULT, attach_intraday_metrics
from review.loader import latest_trade_date


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python analyze_today.py")
    parser.add_argument("target_date", nargs="?", default=None,
                        help="대상 날짜 YYYY-MM-DD (생략시 trade_log 마지막 날짜).")
    parser.add_argument("--intraday-dir", default=INTRADAY_DIR_DEFAULT,
                        help=f"1분봉 캐시 디렉토리 (기본 {INTRADAY_DIR_DEFAULT}).")
    parser.add_argument("--no-intraday", action="store_true",
                        help="1분봉 정밀 메트릭 단계를 건너뛴다(테스트/디버그용).")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    target_date = args.target_date or latest_trade_date()
    if not target_date:
        print("trade_log.csv 가 없거나 비어 있습니다.")
        return 1

    trades = load_trades(target_date)
    if not trades:
        print(f"{target_date} 의 매매 기록이 없습니다.")
        return 0

    attach_metrics(trades)

    # 분봉 정밀 메트릭/D 피처 부착(있는 종목만, 없으면 fallback).
    intraday_summary = {"with_intraday": [], "fallback": [], "missing": []}
    if not args.no_intraday:
        # P1 #12: intraday 단계 실패 시 모든 거래를 missing 리스트에 채워 운영자가
        # 즉시 인지할 수 있게 한다. 또한 catch 범위를 의도된 예외로 좁혀 코딩 실수가
        # 묻히지 않게 한다(KeyError/AttributeError 같은 진짜 버그는 raise).
        try:
            intraday_summary = attach_intraday_metrics(
                trades, target_date=target_date, intraday_dir=args.intraday_dir,
            )
        except (FileNotFoundError, OSError, ValueError) as exc:
            print(f"[warn] intraday 단계 실패 — 모든 거래 missing 처리: {exc}",
                  file=sys.stderr)
            intraday_summary = {
                "with_intraday": [],
                "fallback": [],
                "missing": [t.code for t in trades],
            }

    classify_trades(trades)
    recs = recommend_rules(trades)
    paths = write_reports(trades, recs, target_date,
                          intraday_summary=intraday_summary)

    closed = [t for t in trades if t.is_closed]
    print(f"== {target_date} 매매 복기 ==")
    print(f"  - 거래 {len(trades)}건 (청산 완료 {len(closed)}건)")
    print(f"  - 1분봉 정밀: {len(intraday_summary['with_intraday'])}건 / "
          f"fallback: {len(intraday_summary['fallback'])}건 / "
          f"missing: {len(intraday_summary['missing'])}건")
    if intraday_summary["missing"]:
        print(f"      missing codes: {','.join(intraday_summary['missing'])}")
    print(f"  - 추천 룰 {len(recs)}건")
    for path_kind, path in paths.items():
        print(f"  - {path_kind}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
