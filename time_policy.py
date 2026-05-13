from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone, tzinfo
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from trade_config import TRADE_CONFIG, TradeConfig


logger = logging.getLogger(__name__)

ALLOW_ENTRY = "ALLOW_ENTRY"
ALLOW_MANAGE_ONLY = "ALLOW_MANAGE_ONLY"
ALLOW_CANDIDATE_CAPTURE = "ALLOW_CANDIDATE_CAPTURE"
BLOCK_PRE_OPEN = "BLOCK_PRE_OPEN"
BLOCK_OPENING_STABILIZATION = "BLOCK_OPENING_STABILIZATION"
BLOCK_AFTER_ENTRY_CUTOFF = "BLOCK_AFTER_ENTRY_CUTOFF"
BLOCK_AFTER_CANDIDATE_CUTOFF = "BLOCK_AFTER_CANDIDATE_CUTOFF"
BLOCK_CLOSING_AUCTION = "BLOCK_CLOSING_AUCTION"
BLOCK_AFTER_MARKET = "BLOCK_AFTER_MARKET"
BLOCK_NON_TRADING_DAY = "BLOCK_NON_TRADING_DAY"
FORCE_EXIT_WINDOW = "FORCE_EXIT_WINDOW"
TIME_POLICY_DISABLED = "TIME_POLICY_DISABLED"

SESSION_DISABLED = "disabled"
SESSION_NON_TRADING_DAY = "non_trading_day"
SESSION_PRE_OPEN = "pre_open"
SESSION_REGULAR = "regular_market"
SESSION_CLOSING_AUCTION = "closing_auction"
SESSION_AFTER_MARKET = "after_market"


@dataclass(frozen=True)
class TimeDecision:
    allowed: bool
    action: str
    reason_code: str
    current_time: str
    session: str
    next_allowed_time: Optional[str]
    config_version: str
    time_decision_id: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "allowed": bool(self.allowed),
            "action": self.action,
            "reason_code": self.reason_code,
            "current_time": self.current_time,
            "session": self.session,
            "next_allowed_time": self.next_allowed_time,
            "config_version": self.config_version,
            "time_decision_id": self.time_decision_id,
        }


class KrxExchangeCalendar:
    """Small exchange-calendar facade for KRX regular-session policies.

    The calendar is deliberately data driven: weekends are closed by default,
    and weekday holidays or ad-hoc closures can be supplied by config instead
    of scattering date checks across strategy code.
    """

    def __init__(
        self,
        *,
        timezone: tzinfo,
        regular_open: dt_time,
        regular_close: dt_time,
        closing_auction_start: dt_time,
        closing_auction_end: dt_time,
        holidays: Iterable[date] = (),
    ) -> None:
        self.timezone = timezone
        self.regular_open = regular_open
        self.regular_close = regular_close
        self.closing_auction_start = closing_auction_start
        self.closing_auction_end = closing_auction_end
        self.holidays = set(holidays)

    def is_trading_day(self, day: date) -> bool:
        return day.weekday() < 5 and day not in self.holidays

    def session_for(self, local_dt: datetime) -> str:
        day = local_dt.date()
        clock = local_dt.time().replace(tzinfo=None)
        if not self.is_trading_day(day):
            return SESSION_NON_TRADING_DAY
        if clock < self.regular_open:
            return SESSION_PRE_OPEN
        if self.closing_auction_start <= clock < self.closing_auction_end:
            return SESSION_CLOSING_AUCTION
        if self.regular_open <= clock < self.regular_close:
            return SESSION_REGULAR
        return SESSION_AFTER_MARKET

    def next_trading_day(self, after_day: date) -> date:
        day = after_day + timedelta(days=1)
        for _ in range(370):
            if self.is_trading_day(day):
                return day
            day += timedelta(days=1)
        raise RuntimeError("no trading day found within one year")


class TimePolicy:
    def __init__(
        self,
        config: TradeConfig = TRADE_CONFIG,
        *,
        calendar: Optional[KrxExchangeCalendar] = None,
    ) -> None:
        self.config = config
        self.timezone = load_timezone(config.trading_timezone or "Asia/Seoul")
        self.config_version = str(config.time_policy_config_version or "krx_regular_v1")
        self.regular_open = parse_clock(config.krx_regular_open)
        self.regular_close = parse_clock(config.krx_regular_close)
        self.candidate_capture_start = parse_clock(config.candidate_capture_start)
        self.candidate_capture_end = parse_clock(config.candidate_capture_end)
        self.entry_windows = parse_windows(config.entry_windows)
        self.no_new_entry_after = parse_clock(config.no_new_entry_after)
        self.force_exit_start = parse_clock(config.force_exit_start)
        self.force_exit_deadline = parse_clock(config.force_exit_deadline)
        self.closing_auction_start = parse_clock(config.closing_auction_start)
        self.closing_auction_end = parse_clock(config.closing_auction_end)
        self.calendar = calendar or KrxExchangeCalendar(
            timezone=self.timezone,
            regular_open=self.regular_open,
            regular_close=self.regular_close,
            closing_auction_start=self.closing_auction_start,
            closing_auction_end=self.closing_auction_end,
            holidays=parse_dates(config.krx_holidays),
        )

    def current_hhmmss(self) -> int:
        return int(datetime.now(self.timezone).strftime("%H%M%S"))

    def datetime_from_hhmmss(
        self,
        hhmmss: int,
        *,
        base_date: Optional[date] = None,
    ) -> datetime:
        raw = str(int(hhmmss)).zfill(6)
        clock = dt_time(int(raw[0:2]), int(raw[2:4]), int(raw[4:6]))
        day = base_date or datetime.now(self.timezone).date()
        return datetime.combine(day, clock, tzinfo=self.timezone)

    def evaluate_candidate_capture(
        self,
        *,
        now: Optional[object] = None,
        log: bool = False,
        context: Optional[Dict[str, object]] = None,
    ) -> TimeDecision:
        if not bool(self.config.time_policy_enabled):
            decision = self._decision(True, ALLOW_CANDIDATE_CAPTURE, TIME_POLICY_DISABLED, now)
            self._maybe_log(decision, log, context)
            return decision

        local_dt = self._coerce_datetime(now)
        session = self.calendar.session_for(local_dt)
        clock = local_dt.time().replace(tzinfo=None)
        if session == SESSION_NON_TRADING_DAY:
            decision = self._decision(
                False,
                BLOCK_NON_TRADING_DAY,
                BLOCK_NON_TRADING_DAY,
                local_dt,
                session=session,
                next_allowed_time=self._next_candidate_start(local_dt),
            )
        elif clock < self.candidate_capture_start:
            decision = self._decision(
                False,
                BLOCK_PRE_OPEN,
                BLOCK_PRE_OPEN,
                local_dt,
                session=SESSION_PRE_OPEN,
                next_allowed_time=self._combine_iso(local_dt.date(), self.candidate_capture_start),
            )
        elif clock <= self.candidate_capture_end and clock < self.regular_close:
            decision = self._decision(
                True,
                ALLOW_CANDIDATE_CAPTURE,
                ALLOW_CANDIDATE_CAPTURE,
                local_dt,
                session=session,
            )
        elif session == SESSION_CLOSING_AUCTION:
            decision = self._decision(
                False,
                BLOCK_CLOSING_AUCTION,
                BLOCK_CLOSING_AUCTION,
                local_dt,
                session=session,
                next_allowed_time=self._next_candidate_start(local_dt),
            )
        elif clock >= self.regular_close:
            decision = self._decision(
                False,
                BLOCK_AFTER_MARKET,
                BLOCK_AFTER_MARKET,
                local_dt,
                session=SESSION_AFTER_MARKET,
                next_allowed_time=self._next_candidate_start(local_dt),
            )
        else:
            decision = self._decision(
                False,
                BLOCK_AFTER_CANDIDATE_CUTOFF,
                BLOCK_AFTER_CANDIDATE_CUTOFF,
                local_dt,
                session=session,
                next_allowed_time=self._next_candidate_start(local_dt),
            )
        self._maybe_log(decision, log, context)
        return decision

    def evaluate_entry(
        self,
        *,
        now: Optional[object] = None,
        log: bool = False,
        context: Optional[Dict[str, object]] = None,
    ) -> TimeDecision:
        if not bool(self.config.time_policy_enabled):
            decision = self._decision(True, ALLOW_ENTRY, TIME_POLICY_DISABLED, now)
            self._maybe_log(decision, log, context)
            return decision

        local_dt = self._coerce_datetime(now)
        session = self.calendar.session_for(local_dt)
        clock = local_dt.time().replace(tzinfo=None)
        if session == SESSION_NON_TRADING_DAY:
            decision = self._decision(
                False,
                BLOCK_NON_TRADING_DAY,
                BLOCK_NON_TRADING_DAY,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt),
            )
        elif session == SESSION_PRE_OPEN:
            decision = self._decision(
                False,
                BLOCK_PRE_OPEN,
                BLOCK_PRE_OPEN,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt, include_today=True),
            )
        elif session == SESSION_CLOSING_AUCTION:
            decision = self._decision(
                False,
                BLOCK_CLOSING_AUCTION,
                BLOCK_CLOSING_AUCTION,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt),
            )
        elif session == SESSION_AFTER_MARKET:
            reason = ALLOW_ENTRY if bool(self.config.allow_after_hours_entry) else BLOCK_AFTER_MARKET
            decision = self._decision(
                bool(self.config.allow_after_hours_entry),
                reason,
                reason,
                local_dt,
                session=session,
                next_allowed_time=None if bool(self.config.allow_after_hours_entry) else self._next_entry_start(local_dt),
            )
        elif self.force_exit_start <= clock <= self.force_exit_deadline:
            decision = self._decision(
                False,
                FORCE_EXIT_WINDOW,
                FORCE_EXIT_WINDOW,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt),
            )
        elif self.entry_windows and clock < self.entry_windows[0][0]:
            decision = self._decision(
                False,
                BLOCK_OPENING_STABILIZATION,
                BLOCK_OPENING_STABILIZATION,
                local_dt,
                session=session,
                next_allowed_time=self._combine_iso(local_dt.date(), self.entry_windows[0][0]),
            )
        elif clock >= self.no_new_entry_after:
            decision = self._decision(
                False,
                BLOCK_AFTER_ENTRY_CUTOFF,
                BLOCK_AFTER_ENTRY_CUTOFF,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt),
            )
        elif self._in_windows(clock, self.entry_windows):
            decision = self._decision(
                True,
                ALLOW_ENTRY,
                ALLOW_ENTRY,
                local_dt,
                session=session,
            )
        else:
            decision = self._decision(
                False,
                ALLOW_MANAGE_ONLY,
                ALLOW_MANAGE_ONLY,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt, include_today=True),
            )
        self._maybe_log(decision, log, context)
        if decision.action == FORCE_EXIT_WINDOW:
            self.log_decision(decision, event="force_exit_window_entered", context=context)
        return decision

    def evaluate_manage(
        self,
        *,
        now: Optional[object] = None,
        log: bool = False,
        context: Optional[Dict[str, object]] = None,
    ) -> TimeDecision:
        if not bool(self.config.time_policy_enabled):
            decision = self._decision(True, ALLOW_MANAGE_ONLY, TIME_POLICY_DISABLED, now)
            self._maybe_log(decision, log, context)
            return decision

        local_dt = self._coerce_datetime(now)
        session = self.calendar.session_for(local_dt)
        clock = local_dt.time().replace(tzinfo=None)
        if session == SESSION_NON_TRADING_DAY:
            decision = self._decision(
                False,
                BLOCK_NON_TRADING_DAY,
                BLOCK_NON_TRADING_DAY,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt),
            )
        elif session == SESSION_PRE_OPEN:
            decision = self._decision(
                False,
                BLOCK_PRE_OPEN,
                BLOCK_PRE_OPEN,
                local_dt,
                session=session,
                next_allowed_time=self._combine_iso(local_dt.date(), self.regular_open),
            )
        elif session == SESSION_AFTER_MARKET:
            decision = self._decision(
                False,
                BLOCK_AFTER_MARKET,
                BLOCK_AFTER_MARKET,
                local_dt,
                session=session,
                next_allowed_time=self._next_entry_start(local_dt),
            )
        elif self.force_exit_start <= clock <= self.force_exit_deadline:
            decision = self._decision(
                True,
                FORCE_EXIT_WINDOW,
                FORCE_EXIT_WINDOW,
                local_dt,
                session=session,
            )
        else:
            decision = self._decision(
                True,
                ALLOW_MANAGE_ONLY,
                ALLOW_MANAGE_ONLY,
                local_dt,
                session=session,
            )
        self._maybe_log(decision, log, context)
        if decision.action == FORCE_EXIT_WINDOW:
            self.log_decision(decision, event="force_exit_window_entered", context=context)
        return decision

    def evaluate_order(
        self,
        *,
        side: str,
        now: Optional[object] = None,
        log: bool = False,
        context: Optional[Dict[str, object]] = None,
    ) -> TimeDecision:
        normalized = str(side or "").lower()
        if normalized == "buy":
            return self.evaluate_entry(now=now, log=log, context=context)
        if normalized == "sell":
            return self.evaluate_manage(now=now, log=log, context=context)
        decision = self._decision(False, BLOCK_AFTER_MARKET, "BLOCK_UNKNOWN_ORDER_SIDE", now)
        self._maybe_log(decision, log, context)
        return decision

    def log_decision(
        self,
        decision: TimeDecision,
        *,
        event: str = "time_policy_decision",
        context: Optional[Dict[str, object]] = None,
    ) -> None:
        payload: Dict[str, object] = {"event": event}
        payload.update(decision.to_dict())
        if context:
            payload.update(context)
        logger.info(
            "[%s] %s",
            event,
            json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        )

    def _maybe_log(
        self,
        decision: TimeDecision,
        log: bool,
        context: Optional[Dict[str, object]],
    ) -> None:
        if log:
            self.log_decision(decision, context=context)

    def _decision(
        self,
        allowed: bool,
        action: str,
        reason_code: str,
        now: Optional[object],
        *,
        session: str = "",
        next_allowed_time: Optional[str] = None,
    ) -> TimeDecision:
        local_dt = self._coerce_datetime(now)
        session_value = (
            (session or self.calendar.session_for(local_dt))
            if bool(self.config.time_policy_enabled)
            else SESSION_DISABLED
        )
        return TimeDecision(
            allowed=bool(allowed),
            action=str(action),
            reason_code=str(reason_code),
            current_time=local_dt.isoformat(),
            session=session_value,
            next_allowed_time=next_allowed_time,
            config_version=self.config_version,
            time_decision_id=uuid.uuid4().hex,
        )

    def _coerce_datetime(self, now: Optional[object]) -> datetime:
        if now is None:
            return datetime.now(self.timezone)
        if isinstance(now, datetime):
            if now.tzinfo is None:
                return now.replace(tzinfo=self.timezone)
            return now.astimezone(self.timezone)
        if isinstance(now, (int, float)):
            return datetime.fromtimestamp(float(now), tz=self.timezone)
        raise TypeError("unsupported time value: {!r}".format(now))

    @staticmethod
    def _in_windows(clock: dt_time, windows: Sequence[Tuple[dt_time, dt_time]]) -> bool:
        return any(start <= clock <= end for start, end in windows)

    def _next_entry_start(self, local_dt: datetime, *, include_today: bool = False) -> str:
        first_start = self.entry_windows[0][0] if self.entry_windows else self.regular_open
        if include_today and self.calendar.is_trading_day(local_dt.date()):
            clock = local_dt.time().replace(tzinfo=None)
            for start, _end in self.entry_windows:
                if clock < start:
                    return self._combine_iso(local_dt.date(), start)
        next_day = self.calendar.next_trading_day(local_dt.date())
        return self._combine_iso(next_day, first_start)

    def _next_candidate_start(self, local_dt: datetime) -> str:
        if (
            self.calendar.is_trading_day(local_dt.date())
            and local_dt.time().replace(tzinfo=None) < self.candidate_capture_start
        ):
            return self._combine_iso(local_dt.date(), self.candidate_capture_start)
        next_day = self.calendar.next_trading_day(local_dt.date())
        return self._combine_iso(next_day, self.candidate_capture_start)

    def _combine_iso(self, day: date, clock: dt_time) -> str:
        return datetime.combine(day, clock, tzinfo=self.timezone).isoformat()


def parse_clock(value: object) -> dt_time:
    text = str(value or "").strip()
    if not text:
        raise ValueError("empty time value")
    if ":" in text:
        parts = [int(part) for part in text.split(":")]
    else:
        raw = text.zfill(6)
        parts = [int(raw[0:2]), int(raw[2:4]), int(raw[4:6])]
    while len(parts) < 3:
        parts.append(0)
    return dt_time(parts[0], parts[1], parts[2])


def parse_windows(value: object) -> List[Tuple[dt_time, dt_time]]:
    windows: List[Tuple[dt_time, dt_time]] = []
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        if "~" in text:
            start_text, end_text = text.split("~", 1)
        elif "-" in text:
            start_text, end_text = text.split("-", 1)
        else:
            raise ValueError("entry window must use start-end: {!r}".format(text))
        start = parse_clock(start_text)
        end = parse_clock(end_text)
        if end < start:
            raise ValueError("entry window end before start: {!r}".format(text))
        windows.append((start, end))
    return windows


def parse_dates(value: object) -> List[date]:
    dates: List[date] = []
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        dates.append(date.fromisoformat(text))
    return dates


def hhmmss_from_clock(value: object) -> int:
    return int(parse_clock(value).strftime("%H%M%S"))


def first_window_start_hhmmss(value: object, fallback: object) -> int:
    windows = parse_windows(value)
    if not windows:
        return hhmmss_from_clock(fallback)
    return int(windows[0][0].strftime("%H%M%S"))


def load_timezone(name: str) -> tzinfo:
    try:
        return ZoneInfo(name)
    except Exception:
        if name == "Asia/Seoul":
            return timezone(timedelta(hours=9), name)
        raise
