from __future__ import annotations

import unittest

import main


class ResolveSymbolMarketTests(unittest.TestCase):
    def test_resolve_symbol_market_uses_normalized_cache(self):
        class Dummy:
            normalize_code = main.Kiwoom.normalize_code
            resolve_symbol_market = main.Kiwoom.resolve_symbol_market

        kw = Dummy()
        kw.symbol_market_by_code = {
            "005930": "KOSPI",
            "035720": "KOSDAQ",
        }

        self.assertEqual(kw.resolve_symbol_market("A005930"), "KOSPI")
        self.assertEqual(kw.resolve_symbol_market("035720"), "KOSDAQ")
        self.assertEqual(kw.resolve_symbol_market("000000"), "unknown")


if __name__ == "__main__":
    unittest.main()
