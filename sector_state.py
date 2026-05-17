from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

from sector_theme_maps import MapValidation, validate_sector_map
from market_state import (
    IndexState,
    MarketSnapshot,
    classify_regime,
    REGIME_NEUTRAL,
    REGIME_RISK_OFF,
    REGIME_STRONG,
    REGIME_UNKNOWN,
    REGIME_WEAK,
)


logger = logging.getLogger("kiwoom")

SECTOR_ACTION_ALLOW = "dry_run_allow"
SECTOR_ACTION_BOOST = "dry_run_boost"
SECTOR_ACTION_BLOCK_CHASE_ONLY = "dry_run_block_chase_only"
SECTOR_ACTION_BLOCK_ALL = "dry_run_block_all"

SECTOR_FIELDS = [
    "sector_code",
    "sector_name",
    "sector_index_code",
    "sector_regime",
    "sector_pct",
    "sector_slope_1m",
    "sector_slope_3m",
    "sector_drawdown_from_high",
    "sector_relative_strength_vs_primary",
    "sector_gate_action",
    "sector_gate_reason",
    "turnover_rank_sector",
    "sector_ranked_count",
]


@dataclass
class SectorSnapshot:
    sector_code: str = ""
    sector_name: str = ""
    sector_index_code: str = ""
    sector_regime: str = REGIME_UNKNOWN
    sector_pct: Optional[float] = None
    sector_slope_1m: Optional[float] = None
    sector_slope_3m: Optional[float] = None
    sector_drawdown_from_high: Optional[float] = None
    sector_relative_strength_vs_primary: Optional[float] = None
    sector_gate_action: str = SECTOR_ACTION_ALLOW
    sector_gate_reason: str = ""
    sector_confidence: float = 0.0


@dataclass
class SectorContext:
    symbol: str = ""
    symbol_market: str = "unknown"
    primary_market_regime: str = REGIME_UNKNOWN
    primary_market_pct: Optional[float] = None
    sector_code: str = ""
    sector_name: str = ""
    sector_index_code: str = ""
    sector_regime: str = REGIME_UNKNOWN
    sector_pct: Optional[float] = None
    sector_slope_1m: Optional[float] = None
    sector_slope_3m: Optional[float] = None
    sector_drawdown_from_high: Optional[float] = None
    sector_relative_strength_vs_primary: Optional[float] = None
    sector_gate_action: str = SECTOR_ACTION_ALLOW
    sector_gate_reason: str = ""
    turnover_rank_sector: int = 0
    sector_ranked_count: int = 0

    def as_log_dict(self) -> Dict[str, object]:
        return as_log_dict(self)


class SectorStateCache:
    def __init__(self, map_path: str = "data/sector_map.csv") -> None:
        self.map_path = map_path
        self.symbol_sector: Dict[str, Dict[str, str]] = {}
        self.indices: Dict[str, IndexState] = {}
        self.index_to_sector_code: Dict[str, str] = {}
        self.map_validation: Optional[MapValidation] = None

    @staticmethod
    def normalize_code(code: str) -> str:
        return str(code or "").strip().lstrip("A").zfill(6)[-6:]

    def load_sector_maps(self) -> None:
        self.symbol_sector.clear()
        self.index_to_sector_code.clear()
        self.map_validation = validate_sector_map(self.map_path)
        if not self.map_validation.ok:
            logger.warning("[sector] %s - sector unknown fallback", self.map_validation.message())
            return
        if not os.path.exists(self.map_path):
            logger.info("[sector] sector_map.csv 없음 - sector unknown fallback")
            return
        with open(self.map_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                code = self.normalize_code(row.get("code", ""))
                sector_code = str(row.get("sector_code", "") or "").strip()
                if not code or not sector_code:
                    continue
                meta = {
                    "code": code,
                    "name": str(row.get("name", "") or "").strip(),
                    "market": str(row.get("market", "") or "unknown").strip() or "unknown",
                    "sector_code": sector_code,
                    "sector_name": str(row.get("sector_name", "") or "").strip(),
                    "sector_index_code": str(row.get("sector_index_code", "") or "").strip(),
                }
                self.symbol_sector[code] = meta
                if meta["sector_index_code"]:
                    self.index_to_sector_code[meta["sector_index_code"]] = sector_code

    def resolve_symbol_sector(self, code: str) -> Dict[str, str]:
        normalized = self.normalize_code(code)
        return dict(self.symbol_sector.get(normalized, {}))

    def register_sector_index_if_needed(self, sector_code: str) -> str:
        for meta in self.symbol_sector.values():
            if meta.get("sector_code") == sector_code:
                index_code = meta.get("sector_index_code", "")
                if index_code and index_code not in self.indices:
                    self.indices[index_code] = IndexState()
                    self.index_to_sector_code[index_code] = sector_code
                return index_code
        return ""

    def update(self, index_code: str, price: float, ts: float) -> None:
        index_code = str(index_code or "").strip()
        if not index_code:
            return
        if index_code not in self.indices:
            sector_code = self.index_to_sector_code.get(index_code, "")
            if not sector_code:
                return
            self.indices[index_code] = IndexState()
        self.indices[index_code].update(price, ts)

    def _snapshot_from_meta(self, meta: Dict[str, str]) -> SectorSnapshot:
        index_code = meta.get("sector_index_code", "")
        state = self.indices.get(index_code)
        if state is None:
            return self._with_gate(
                SectorSnapshot(
                    sector_code=meta.get("sector_code", ""),
                    sector_name=meta.get("sector_name", ""),
                    sector_index_code=index_code,
                    sector_regime=REGIME_UNKNOWN,
                )
            )
        snap = MarketSnapshot(
            market_pct=state.pct(),
            market_slope_1m=state.slope_1m(),
            market_slope_3m=state.slope_3m(),
            market_drawdown_from_high=state.drawdown_from_high(),
        )
        regime = classify_regime(snap)
        return self._with_gate(
            SectorSnapshot(
                sector_code=meta.get("sector_code", ""),
                sector_name=meta.get("sector_name", ""),
                sector_index_code=index_code,
                sector_regime=regime,
                sector_pct=snap.market_pct,
                sector_slope_1m=snap.market_slope_1m,
                sector_slope_3m=snap.market_slope_3m,
                sector_drawdown_from_high=snap.market_drawdown_from_high,
                sector_confidence=1.0 if snap.market_pct is not None else 0.0,
            )
        )

    def snapshot_sector(self, sector_code: str) -> SectorSnapshot:
        for meta in self.symbol_sector.values():
            if meta.get("sector_code") == str(sector_code or "").strip():
                return self._snapshot_from_meta(meta)
        return self._with_gate(SectorSnapshot(sector_code=str(sector_code or "").strip()))

    def snapshot_for_symbol(
        self,
        code: str,
        symbol_market: str = "",
        market_context=None,
    ) -> SectorContext:
        meta = self.resolve_symbol_sector(code)
        primary_pct = getattr(market_context, "primary_market_pct", None)
        primary_regime = getattr(market_context, "primary_market_regime", REGIME_UNKNOWN)
        if not meta:
            return SectorContext(
                symbol=self.normalize_code(code),
                symbol_market=symbol_market or "unknown",
                primary_market_regime=primary_regime,
                primary_market_pct=primary_pct,
                sector_gate_action=SECTOR_ACTION_ALLOW,
                sector_gate_reason="SECTOR_UNKNOWN_FALLBACK",
            )
        snap = self._snapshot_from_meta(meta)
        rel = None
        if snap.sector_pct is not None and primary_pct is not None:
            rel = snap.sector_pct - primary_pct
        reason = snap.sector_gate_reason
        if snap.sector_regime == REGIME_WEAK and rel is not None and rel > 0:
            reason = "{}_REL_STRENGTH_POSITIVE".format(reason or "SECTOR_WEAK")
        return SectorContext(
            symbol=self.normalize_code(code),
            symbol_market=symbol_market or meta.get("market", "unknown") or "unknown",
            primary_market_regime=primary_regime,
            primary_market_pct=primary_pct,
            sector_code=snap.sector_code,
            sector_name=snap.sector_name,
            sector_index_code=snap.sector_index_code,
            sector_regime=snap.sector_regime,
            sector_pct=snap.sector_pct,
            sector_slope_1m=snap.sector_slope_1m,
            sector_slope_3m=snap.sector_slope_3m,
            sector_drawdown_from_high=snap.sector_drawdown_from_high,
            sector_relative_strength_vs_primary=rel,
            sector_gate_action=snap.sector_gate_action,
            sector_gate_reason=reason,
        )

    @staticmethod
    def _with_gate(snapshot: SectorSnapshot) -> SectorSnapshot:
        regime = snapshot.sector_regime or REGIME_UNKNOWN
        if regime == REGIME_STRONG:
            snapshot.sector_gate_action = SECTOR_ACTION_BOOST
            snapshot.sector_gate_reason = "SECTOR_STRONG"
        elif regime == REGIME_NEUTRAL:
            snapshot.sector_gate_action = SECTOR_ACTION_ALLOW
            snapshot.sector_gate_reason = ""
        elif regime == REGIME_WEAK:
            snapshot.sector_gate_action = SECTOR_ACTION_BLOCK_CHASE_ONLY
            snapshot.sector_gate_reason = "SECTOR_WEAK_CHASE_RISK"
        elif regime == REGIME_RISK_OFF:
            snapshot.sector_gate_action = SECTOR_ACTION_BLOCK_ALL
            snapshot.sector_gate_reason = "SECTOR_RISK_OFF"
        else:
            snapshot.sector_regime = REGIME_UNKNOWN
            snapshot.sector_gate_action = SECTOR_ACTION_ALLOW
            snapshot.sector_gate_reason = "SECTOR_UNKNOWN_FALLBACK"
        return snapshot

    def as_log_dict(self, context: SectorContext) -> Dict[str, object]:
        return as_log_dict(context)


def as_log_dict(context: SectorContext) -> Dict[str, object]:
    if context is None:
        context = SectorContext()
    out = {}
    for field in SECTOR_FIELDS:
        value = getattr(context, field, "")
        out[field] = "" if value is None else value
    return out
