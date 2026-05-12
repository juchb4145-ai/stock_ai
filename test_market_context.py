"""review/market_context.py 테스트.

매크로 JSON 의 round-trip, attach 단계의 graceful fallback, classify 임계 동작을 검증.

실행:
    python -m unittest test_market_context -v
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from review.market_context import (
    MARKET_CONTEXT_FEATURE_KEYS,
    MARKET_CONTEXT_LABEL_KEY,
    MARKET_CONTEXT_SCHEMA,
    MarketContext,
    attach_market_context,
    classify_market_strength,
    context_path,
    load_market_context,
    save_market_context,
)


class _Trade:
    """attach_market_context 가 쓰는 features dict 만 가진 stub."""
    def __init__(self, code: str = "000000") -> None:
        self.code = code
        self.features: dict = {}


class MarketContextSerializationTests(unittest.TestCase):
    def test_round_trip_full_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = MarketContext(
                date="2026-04-30",
                kospi_close_return=0.0078,
                kosdaq_close_return=0.0114,
                kospi_intraday_high_return=0.0125,
                kosdaq_intraday_high_return=0.0181,
                kospi_close=2_650.5,
                kosdaq_close=870.3,
                source="kiwoom_opt20006",
            )
            path = save_market_context(ctx, reviews_dir=tmp)
            self.assertEqual(path, context_path("2026-04-30", tmp))
            self.assertTrue(os.path.exists(path))

            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
            self.assertEqual(payload["schema"], MARKET_CONTEXT_SCHEMA)
            self.assertEqual(payload["date"], "2026-04-30")
            self.assertNotEqual(payload["generated_at"], "")

            loaded = load_market_context("2026-04-30", reviews_dir=tmp)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.kospi_close_return, 0.0078)
            self.assertEqual(loaded.source, "kiwoom_opt20006")

    def test_load_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(load_market_context("2026-04-30", reviews_dir=tmp))

    def test_load_corrupt_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = context_path("2026-04-30", tmp)
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not json")
            self.assertIsNone(load_market_context("2026-04-30", reviews_dir=tmp))

    def test_partial_fields_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = MarketContext(date="2026-04-30", kospi_close_return=0.012)
            save_market_context(ctx, reviews_dir=tmp)
            loaded = load_market_context("2026-04-30", reviews_dir=tmp)
            self.assertEqual(loaded.kospi_close_return, 0.012)
            self.assertIsNone(loaded.kosdaq_close_return)
            self.assertIsNone(loaded.kospi_intraday_high_return)


class ClassifyMarketStrengthTests(unittest.TestCase):
    def test_unknown_when_none(self):
        self.assertEqual(classify_market_strength(None), "unknown")

    def test_unknown_when_kospi_missing(self):
        ctx = MarketContext(date="2026-04-30", kospi_close_return=None)
        self.assertEqual(classify_market_strength(ctx), "unknown")

    def test_strong_at_threshold(self):
        ctx = MarketContext(date="2026-04-30", kospi_close_return=0.005)
        self.assertEqual(classify_market_strength(ctx), "strong")

    def test_strong_above(self):
        ctx = MarketContext(date="2026-04-30", kospi_close_return=0.012)
        self.assertEqual(classify_market_strength(ctx), "strong")

    def test_weak_at_threshold(self):
        ctx = MarketContext(date="2026-04-30", kospi_close_return=-0.005)
        self.assertEqual(classify_market_strength(ctx), "weak")

    def test_weak_below(self):
        ctx = MarketContext(date="2026-04-30", kospi_close_return=-0.018)
        self.assertEqual(classify_market_strength(ctx), "weak")

    def test_neutral_inside_band(self):
        ctx = MarketContext(date="2026-04-30", kospi_close_return=0.001)
        self.assertEqual(classify_market_strength(ctx), "neutral")


class AttachMarketContextTests(unittest.TestCase):
    def test_attach_with_full_data(self):
        ctx = MarketContext(
            date="2026-04-30",
            kospi_close_return=0.012,
            kosdaq_close_return=0.018,
            kospi_intraday_high_return=0.015,
            kosdaq_intraday_high_return=0.022,
        )
        trades = [_Trade("A"), _Trade("B")]
        result = attach_market_context(trades, "2026-04-30", context=ctx)
        self.assertIs(result, ctx)
        for trade in trades:
            self.assertEqual(trade.features["market_kospi_close_return"], 0.012)
            self.assertEqual(trade.features["market_kosdaq_close_return"], 0.018)
            self.assertEqual(trade.features["market_kospi_intraday_high_return"], 0.015)
            self.assertEqual(trade.features["market_kosdaq_intraday_high_return"], 0.022)
            self.assertEqual(trade.features[MARKET_CONTEXT_LABEL_KEY], "strong")

    def test_attach_without_data_marks_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            trades = [_Trade("A")]
            result = attach_market_context(trades, "2026-04-30", reviews_dir=tmp)
            self.assertIsNone(result)
            for key in MARKET_CONTEXT_FEATURE_KEYS:
                self.assertIsNone(trades[0].features[key])
            self.assertEqual(trades[0].features[MARKET_CONTEXT_LABEL_KEY], "unknown")

    def test_attach_skips_trade_without_features_attr(self):
        trades = [object()]  # features 속성 없음
        # 예외 없이 통과해야 함 — graceful skip
        attach_market_context(trades, "2026-04-30",
                              context=MarketContext(date="2026-04-30"))


if __name__ == "__main__":
    unittest.main()
