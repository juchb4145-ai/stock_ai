"""rule_candidates / rule_overrides JSON → 모듈 상수 자동 적용 (사람용 CLI 래퍼).

기본 모드는 dry_run — 어떤 경우에도 실제 setattr 가 일어나지 않는다.
--commit 플래그가 있을 때만 실제로 적용한다.

사용법:
    python apply_overrides.py 2026-04-30                    # dry_run
    python apply_overrides.py 2026-04-30 --commit            # 실제 적용
    python apply_overrides.py 2026-04-30 --max-changes 5
    python apply_overrides.py 2026-04-30 --source-dir tests/fixtures/reviews
    python apply_overrides.py 2026-04-30 --commit --no-fixture-test
    python apply_overrides.py 2026-04-30 --commit --fixture-tests test_classifier,test_intraday

안전장치 — fixture 테스트 hook(기본 활성):
    --commit 모드에서는 setattr 직후 ``test_classifier`` 회귀 테스트를 자동
    실행해 분류기가 망가지지 않았는지 검증한다. 실패 시 자동 rollback.
    이 기본 동작이 부담스러운 환경에서는 ``--no-fixture-test`` 로 끌 수 있다.

출력:
    data/reviews/applied_overrides_YYYYMMDD.json
    data/main.log 에 한 줄 요약 (root logger 가 부착된 경우)
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from typing import List, Optional

from review.overrides import (
    DEFAULT_MAX_DAILY_RULE_CHANGES,
    REVIEW_DIR_DEFAULT,
    load_and_apply_overrides,
)


DEFAULT_FIXTURE_TESTS = "test_classifier"


def _setup_stdout_logging() -> None:
    """단독 실행 시 stdout 으로도 [OVERRIDE] 로그가 보이게 한다."""
    logger = logging.getLogger("kiwoom")
    if any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                           datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _make_fixture_hook(test_modules: List[str]):
    """commit 후 분류기 회귀를 검증하는 fixture_hook.

    test_modules 의 unittest 모듈을 모두 통과해야 True 반환.
    하나라도 실패하면 False 반환 → review.overrides.commit_overrides 가 자동
    rollback 한다.
    """
    def _hook() -> bool:
        cmd = [sys.executable, "-m", "unittest", "-v", *test_modules]
        try:
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=120,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            print(f"[fixture-hook] 실행 실패 → rollback 트리거: {exc}", file=sys.stderr)
            return False
        if result.returncode != 0:
            print("[fixture-hook] 실패 → rollback 트리거", file=sys.stderr)
            print(result.stdout[-2000:], file=sys.stderr)
            print(result.stderr[-2000:], file=sys.stderr)
            return False
        return True
    return _hook


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python apply_overrides.py",
        description=(
            "룰 후보 → 모듈 상수 적용. 기본은 dry_run (실제 변경 없음). "
            "--commit 플래그로만 실제 setattr."
        ),
    )
    parser.add_argument("date", help="대상 날짜 YYYY-MM-DD")
    parser.add_argument(
        "--commit", action="store_true",
        help="실제 setattr 수행. 없으면 dry_run.",
    )
    parser.add_argument(
        "--source-dir", default=REVIEW_DIR_DEFAULT,
        help=f"후보 JSON 디렉토리 (기본 {REVIEW_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--log-dir", default=REVIEW_DIR_DEFAULT,
        help=f"applied_overrides_*.json 저장 디렉토리 (기본 {REVIEW_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--max-changes", type=int, default=DEFAULT_MAX_DAILY_RULE_CHANGES,
        help=f"하루 최대 적용 개수 (기본 {DEFAULT_MAX_DAILY_RULE_CHANGES}).",
    )
    parser.add_argument(
        "--fixture-tests", default=DEFAULT_FIXTURE_TESTS,
        help=(
            "commit 후 자동 실행할 unittest 모듈 (콤마 구분, "
            f"기본 {DEFAULT_FIXTURE_TESTS}). 실패 시 자동 rollback."
        ),
    )
    parser.add_argument(
        "--no-fixture-test", action="store_true",
        help="--commit 모드에서 fixture 테스트 hook 을 비활성화(권장하지 않음).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    _setup_stdout_logging()

    mode = "commit" if args.commit else "dry_run"

    # commit 모드 + --no-fixture-test 가 없으면 자동으로 분류기 회귀 검증 hook 부착.
    fixture_hook = None
    if mode == "commit" and not args.no_fixture_test:
        modules = [m.strip() for m in args.fixture_tests.split(",") if m.strip()]
        if modules:
            fixture_hook = _make_fixture_hook(modules)
            print(f"[apply_overrides] fixture hook 활성: {','.join(modules)}")

    try:
        result = load_and_apply_overrides(
            date=args.date,
            mode=mode,
            source_dir=args.source_dir,
            log_dir=args.log_dir,
            max_daily_rule_changes=args.max_changes,
            fixture_hook=fixture_hook,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"== apply_overrides {args.date} ({mode}) ==")
    print(f"  source: {result['source_file']}")
    print(f"  audit:  {result['audit_log_path']}")
    print(f"  applied={result['applied_count']} skipped={result['skipped_count']} "
          f"total={len(result['entries'])}")
    if mode == "dry_run":
        print("  * dry_run 모드: 실제 모듈 상수는 변경되지 않았습니다.")
        print("  * 검토 후 적용하려면 후보 JSON 의 allow_auto_apply 를 true 로 편집한 뒤")
        print("    'python apply_overrides.py {date} --commit' 으로 다시 실행하세요.".format(date=args.date))
    elif args.no_fixture_test:
        print("  * 경고: --no-fixture-test 로 fixture 검증을 건너뛰었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
