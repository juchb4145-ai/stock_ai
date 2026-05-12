"""fetch_market_context.py 단위 테스트 (키움 호출 mock).

키움 OpenAPI 의존을 피하기 위해 _KiwoomIndexFetcher 를 mock 으로 주입한다.
일봉 응답 → 매크로(close_return, intraday_high_return) 변환 로직과 부분 실패
처리, target_date 가 휴장일일 때의 fallback 을 검증한다.

실행:
    python -m unittest test_fetch_market_context -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from typing import Dict, List

from fetch_market_context import (
    INDEX_CODES,
    _compute_returns_for_target,
    fetch_market_context,
    needs_fetch,
)
from review.market_context import MARKET_CONTEXT_SCHEMA, load_market_context


class _StubFetcher:
    """키움 fetcher 를 대체하는 mock. ``responses[index_code]`` 로 일봉 응답을 미리 주입."""

    def __init__(self, responses: Dict[str, List[dict]], fail_for: List[str] = None) -> None:
        self.responses = responses
        self.fail_for = fail_for or []
        self.calls: List[tuple] = []

    def fetch_daily(self, index_code: str, target_date: str) -> List[dict]:
        self.calls.append((index_code, target_date))
        if index_code in self.fail_for:
            raise RuntimeError(f"simulated failure for {index_code}")
        return list(self.responses.get(index_code, []))


def _make_daily(date: str, *, open_: float, high: float, low: float, close: float) -> dict:
    return {"date": date, "open": open_, "high": high, "low": low, "close": close, "volume": 100_000}


class ComputeReturnsTests(unittest.TestCase):
    def test_full_returns(self):
        rows = [
            _make_daily("2026-04-29", open_=2_600, high=2_620, low=2_590, close=2_610),
            _make_daily("2026-04-30", open_=2_610, high=2_650, low=2_605, close=2_640),
        ]
        out = _compute_returns_for_target(rows, "2026-04-30")
        self.assertEqual(out["close"], 2_640)
        self.assertAlmostEqual(out["close_return"], 2_640 / 2_610 - 1)
        self.assertAlmostEqual(out["intraday_high_return"], 2_650 / 2_610 - 1)

    def test_close_return_none_without_prev(self):
        rows = [
            _make_daily("2026-04-30", open_=2_610, high=2_650, low=2_605, close=2_640),
        ]
        out = _compute_returns_for_target(rows, "2026-04-30")
        self.assertEqual(out["close"], 2_640)
        self.assertIsNone(out["close_return"])
        self.assertIsNotNone(out["intraday_high_return"])

    def test_intraday_high_none_when_open_zero(self):
        rows = [
            _make_daily("2026-04-29", open_=2_600, high=2_620, low=2_590, close=2_610),
            _make_daily("2026-04-30", open_=0, high=2_650, low=2_605, close=2_640),
        ]
        out = _compute_returns_for_target(rows, "2026-04-30")
        self.assertIsNone(out["intraday_high_return"])
        self.assertIsNotNone(out["close_return"])

    def test_holiday_fallback_uses_most_recent_business_day(self):
        # target=2026-05-02 (휴장일) — 가장 최근 영업일 2026-05-01 을 target 으로 사용.
        rows = [
            _make_daily("2026-04-30", open_=2_600, high=2_620, low=2_590, close=2_610),
            _make_daily("2026-05-01", open_=2_610, high=2_650, low=2_605, close=2_640),
        ]
        out = _compute_returns_for_target(rows, "2026-05-02")
        self.assertEqual(out["close"], 2_640)
        self.assertAlmostEqual(out["close_return"], 2_640 / 2_610 - 1)

    def test_empty_rows(self):
        out = _compute_returns_for_target([], "2026-04-30")
        self.assertEqual(out, {"close": None, "close_return": None, "intraday_high_return": None})


class NeedsFetchTests(unittest.TestCase):
    def test_force_always_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.json")
            self.assertTrue(needs_fetch(path, force=True))

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(needs_fetch(os.path.join(tmp, "x.json"), force=False))

    def test_existing_file_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write('{"a":1}')
            self.assertFalse(needs_fetch(path, force=False))


class FetchMarketContextTests(unittest.TestCase):
    def test_full_success_writes_json(self):
        rows_kospi = [
            _make_daily("2026-04-29", open_=2_600, high=2_620, low=2_590, close=2_610),
            _make_daily("2026-04-30", open_=2_610, high=2_650, low=2_605, close=2_640),
        ]
        rows_kosdaq = [
            _make_daily("2026-04-29", open_=850, high=860, low=848, close=855),
            _make_daily("2026-04-30", open_=855, high=875, low=852, close=870),
        ]
        fetcher = _StubFetcher({
            INDEX_CODES["kospi"]: rows_kospi,
            INDEX_CODES["kosdaq"]: rows_kosdaq,
        })
        with tempfile.TemporaryDirectory() as tmp:
            ctx = fetch_market_context("2026-04-30", reviews_dir=tmp, fetcher=fetcher)

        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.date, "2026-04-30")
        self.assertEqual(ctx.kospi_close, 2_640)
        self.assertEqual(ctx.kosdaq_close, 870)
        self.assertAlmostEqual(ctx.kospi_close_return, 2_640 / 2_610 - 1)
        self.assertAlmostEqual(ctx.kosdaq_close_return, 870 / 855 - 1)
        self.assertEqual(ctx.source, "kiwoom_opt20006")

        # 두 업종 모두 fetcher 호출 확인
        called_codes = {c[0] for c in fetcher.calls}
        self.assertEqual(called_codes, {INDEX_CODES["kospi"], INDEX_CODES["kosdaq"]})

    def test_partial_failure_writes_with_none(self):
        rows_kospi = [
            _make_daily("2026-04-29", open_=2_600, high=2_620, low=2_590, close=2_610),
            _make_daily("2026-04-30", open_=2_610, high=2_650, low=2_605, close=2_640),
        ]
        fetcher = _StubFetcher(
            responses={INDEX_CODES["kospi"]: rows_kospi},
            fail_for=[INDEX_CODES["kosdaq"]],
        )
        with tempfile.TemporaryDirectory() as tmp:
            ctx = fetch_market_context("2026-04-30", reviews_dir=tmp, fetcher=fetcher)

        self.assertIsNotNone(ctx)
        self.assertIsNotNone(ctx.kospi_close_return)
        self.assertIsNone(ctx.kosdaq_close_return)
        self.assertIsNone(ctx.kosdaq_intraday_high_return)

    def test_full_failure_returns_none(self):
        fetcher = _StubFetcher(
            responses={},
            fail_for=[INDEX_CODES["kospi"], INDEX_CODES["kosdaq"]],
        )
        with tempfile.TemporaryDirectory() as tmp:
            ctx = fetch_market_context("2026-04-30", reviews_dir=tmp, fetcher=fetcher)
            self.assertIsNone(ctx)
            # 실패 시 JSON 도 작성되지 않아야 함
            from review.market_context import context_path
            self.assertFalse(os.path.exists(context_path("2026-04-30", tmp)))

    def test_cached_skipped_unless_force(self):
        rows_kospi = [
            _make_daily("2026-04-29", open_=2_600, high=2_620, low=2_590, close=2_610),
            _make_daily("2026-04-30", open_=2_610, high=2_650, low=2_605, close=2_640),
        ]
        rows_kosdaq = [
            _make_daily("2026-04-29", open_=850, high=860, low=848, close=855),
            _make_daily("2026-04-30", open_=855, high=875, low=852, close=870),
        ]
        fetcher = _StubFetcher({
            INDEX_CODES["kospi"]: rows_kospi,
            INDEX_CODES["kosdaq"]: rows_kosdaq,
        })
        with tempfile.TemporaryDirectory() as tmp:
            # 첫 호출: 작성됨
            ctx1 = fetch_market_context("2026-04-30", reviews_dir=tmp, fetcher=fetcher)
            self.assertIsNotNone(ctx1)
            calls_before = len(fetcher.calls)

            # 두번째 호출: cached → fetcher 호출 안 일어나고 None 반환
            ctx2 = fetch_market_context("2026-04-30", reviews_dir=tmp, fetcher=fetcher)
            self.assertIsNone(ctx2)
            self.assertEqual(len(fetcher.calls), calls_before)

            # force=True → 다시 호출
            ctx3 = fetch_market_context("2026-04-30", reviews_dir=tmp, fetcher=fetcher, force=True)
            self.assertIsNotNone(ctx3)
            self.assertGreater(len(fetcher.calls), calls_before)

    def test_saved_json_round_trip(self):
        rows_kospi = [
            _make_daily("2026-04-29", open_=2_600, high=2_620, low=2_590, close=2_610),
            _make_daily("2026-04-30", open_=2_610, high=2_650, low=2_605, close=2_640),
        ]
        rows_kosdaq = [
            _make_daily("2026-04-29", open_=850, high=860, low=848, close=855),
            _make_daily("2026-04-30", open_=855, high=875, low=852, close=870),
        ]
        fetcher = _StubFetcher({
            INDEX_CODES["kospi"]: rows_kospi,
            INDEX_CODES["kosdaq"]: rows_kosdaq,
        })
        with tempfile.TemporaryDirectory() as tmp:
            fetch_market_context("2026-04-30", reviews_dir=tmp, fetcher=fetcher)
            loaded = load_market_context("2026-04-30", reviews_dir=tmp)

        self.assertIsNotNone(loaded)
        self.assertAlmostEqual(loaded.kospi_close_return, 2_640 / 2_610 - 1)
        self.assertAlmostEqual(loaded.kosdaq_close_return, 870 / 855 - 1)
        self.assertEqual(loaded.source, "kiwoom_opt20006")


if __name__ == "__main__":
    unittest.main()
