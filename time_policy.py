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
ALLOW_LATE_A_GRADE_ENTRY = "ALLOW_LATE_A_GRADE_ENTRY"
ALLOW_MANAGE_ONLY = "ALLOW_MANAGE_ONLY"
ALLOW_CANDIDATE_CAPTURE = "ALLOW_CANDIDATE_CAPTURE"
ALLOW_ANALYSIS_ONLY = "ALLOW_ANALYSIS_ONLY"
BLOCK_PRE_OPEN = "BLOCK_PRE_OPEN"
BLOCK_OPENING_STABILIZATION = "BLOCK_OPENING_STABILIZATION"
BLOCK_AFTER_ENTRY_CUTOFF = "BLOCK_AFTER_ENTRY_CUTOFF"
BLOCK_AFTER_CANDIDATE_CUTOFF = "BLOCK_AFTER_CANDIDATE_CUTOFF"
BLOCK_CLOSING_AUCTION = "BLOCK_CLOSING_AUCTION"
BLOCK_AFTER_MARKET = "BLOCK_AFTER_MARKET"
BLOCK_NON_TRADING_DAY = "BLOCK_NON_TRADING_DAY"
FORCE_EXIT_WINDOW = "FORCE_EXIT_WINDOW"
CLOSING_AUCTION_EMERGENCY_EXIT = "CLOSING_AUCTION_EMERGENCY_EXIT"
TIME_POLICY_DISABLED = "TIME_POLICY_DISABLED"
TOO_LATE_FOR_ENTRY_WINDOW = "TOO_LATE_FOR_ENTRY_WINDOW"

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
    entry_allowed: bool = False
    capture_allowed: bool = False
    manage_allowed: bool = False
    analysis_allowed: bool = False
    candidate_role: str = ""

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
            "entry_allowed": bool(self.entry_allowed),
            "capture_allowed": bool(self.capture_allowed),
            "manage_allowed": bool(self.manage_allowed),
            "analysis_allowed": bool(self.analysis_allowed),
            "candidate_role": self.candidate_role,
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
        self.midday_paper_windows = parse_windows(config.midday_paper_window)
        self.afternoon_entry_windows = parse_windows(config.afternoon_entry_window)
        self.closing_paper_windows = parse_windows(config.closing_paper_window)
        self.no_new_entry_after = parse_clock(config.no_new_entry_after)
        self.late_a_grade_entry_start = parse_clock(config.late_a_grade_entry_start)
        self.late_a_grade_entry_end = parse_clock(config.late_a_grade_entry_end)
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

    def evaluate_trading_candidate_capture(
        self,
        *,
        now: Optional[object] = None,
        min_observation_sec: Optional[float] = None,
        log: bool = False,
        context: Optional[Dict[str, object]] = None,
    ) -> TimeDecision:
        """Return whether a detection should enter the live trading candidate pool.

        Candidate capture is intentionally wider than buy entry. This method is
        the narrower live-trading gate: detections outside a usable entry window
        can still be logged as analysis samples without becoming orderable
        candidates.
        """
        local_dt = self._coerce_datetime(now)
        base_context = dict(context or {})
        capture_decision = self.evaluate_candidate_capture(
            now=local_dt,
            log=False,
            context=base_context,
        )
        if not capture_decision.capture_allowed:
            self._maybe_log(capture_decision, log, base_context)
            return capture_decision

        min_obs = (
            float(min_observation_sec)
            if min_observation_sec is not None
            else float(getattr(self.config, "min_candidate_age_seconds", 0) or 0)
        )
        trading_context = dict(base_context)
        trading_context.setdefault("candidate_role", "trading")
        trading_context.setdefault("min_observation_sec", min_obs)

        entry_decision = self.evaluate_entry(
            now=local_dt,
            log=False,
            context=trading_context,
        )
        deadline = self.entry_window_deadline(now=local_dt, context=trading_context)
        if entry_decision.allowed and self._observation_overruns_deadline(
            local_dt,
            min_obs,
            deadline,
        ):
            decision = self._decision(
                False,
                ALLOW_ANALYSIS_ONLY,
                TOO_LATE_FOR_ENTRY_WINDOW,
                local_dt,
                session=capture_decision.session,
                next_allowed_time=entry_decision.next_allowed_time,
                candidate_role="analysis_only",
                context=trading_context,
            )
            self._maybe_log(decision, log, trading_context)
            return decision

        if entry_decision.allowed:
            role = (
                "trading_late_a_grade"
                if entry_decision.action == ALLOW_LATE_A_GRADE_ENTRY
                else "trading"
            )
            decision = self._decision(
                True,
                entry_decision.action
                if entry_decision.action == ALLOW_LATE_A_GRADE_ENTRY
                else ALLOW_CANDIDATE_CAPTURE,
                entry_decision.action
                if entry_decision.action == ALLOW_LATE_A_GRADE_ENTRY
                else ALLOW_CANDIDATE_CAPTURE,
                local_dt,
                session=capture_decision.session,
                candidate_role=role,
                context=trading_context,
            )
            self._maybe_log(decision, log, trading_context)
            return decision

        if entry_decision.reason_code == BLOCK_OPENING_STABILIZATION:
            opening_deadline = self.entry_window_deadline(
                now=local_dt,
                context=trading_context,
                include_next=True,
            )
            if not self._observation_overruns_deadline(local_dt, min_obs, opening_deadline):
                decision = self._decision(
                    True,
                    ALLOW_CANDIDATE_CAPTURE,
                    ALLOW_CANDIDATE_CAPTURE,
                    local_dt,
                    session=capture_decision.session,
                    next_allowed_time=entry_decision.next_allowed_time,
                    candidate_role="trading",
                    context=trading_context,
                )
                self._maybe_log(decision, log, trading_context)
                return decision

        late_context = dict(trading_context)
        late_context["late_a_grade_candidate"] = True
        late_deadline = self.entry_window_deadline(now=local_dt, context=late_context)
        if (
            bool(getattr(self.config, "allow_late_a_grade_entry", False))
            and late_deadline is not None
            and not self._observation_overruns_deadline(
                local_dt,
                float(getattr(self.config, "min_candidate_age_a_grade_seconds", min_obs) or min_obs),
                late_deadline,
            )
        ):
            decision = self._decision(
                True,
                ALLOW_LATE_A_GRADE_ENTRY,
                ALLOW_LATE_A_GRADE_ENTRY,
                local_dt,
                session=capture_decision.session,
                candidate_role="trading_late_a_grade_watch",
                context=late_context,
            )
            self._maybe_log(decision, log, late_context)
            return decision

        decision = self._decision(
            False,
            ALLOW_ANALYSIS_ONLY,
            entry_decision.reason_code,
            local_dt,
            session=capture_decision.session,
            next_allowed_time=entry_decision.next_allowed_time,
            candidate_role="analysis_only",
            context=trading_context,
        )
        self._maybe_log(decision, log, trading_context)
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
        elif self._late_a_grade_entry_allowed(clock, context):
            decision = self._decision(
                True,
                ALLOW_LATE_A_GRADE_ENTRY,
                ALLOW_LATE_A_GRADE_ENTRY,
                local_dt,
                session=session,
                context=context,
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
        elif session == SESSION_CLOSING_AUCTION:
            allowed = bool(getattr(self.config, "allow_closing_auction_emergency_exit", True))
            decision = self._decision(
                allowed,
                CLOSING_AUCTION_EMERGENCY_EXIT if allowed else BLOCK_CLOSING_AUCTION,
                CLOSING_AUCTION_EMERGENCY_EXIT if allowed else BLOCK_CLOSING_AUCTION,
                local_dt,
                session=session,
                next_allowed_time=None if allowed else self._next_entry_start(local_dt),
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

    def permission_snapshot(
        self,
        *,
        now: Optional[object] = None,
        context: Optional[Dict[str, object]] = None,
    ) -> Dict[str, bool]:
        local_dt = self._coerce_datetime(now)
        if not bool(self.config.time_policy_enabled):
            return {
                "entry_allowed": True,
                "capture_allowed": True,
                "manage_allowed": True,
                "analysis_allowed": True,
            }
        session = self.calendar.session_for(local_dt)
        clock = local_dt.time().replace(tzinfo=None)
        capture_allowed = (
            session == SESSION_REGULAR
            and self.candidate_capture_start <= clock <= self.candidate_capture_end
            and clock < self.regular_close
        )
        entry_allowed = self._entry_allowed_for_clock(clock, session, context)
        manage_allowed = session not in {
            SESSION_NON_TRADING_DAY,
            SESSION_PRE_OPEN,
            SESSION_AFTER_MARKET,
        } and (
            session != SESSION_CLOSING_AUCTION
            or bool(getattr(self.config, "allow_closing_auction_emergency_exit", True))
        )
        return {
            "entry_allowed": bool(entry_allowed),
            "capture_allowed": bool(capture_allowed),
            "manage_allowed": bool(manage_allowed),
            "analysis_allowed": bool(capture_allowed),
        }

    def paper_strategy_type(
        self,
        *,
        now: Optional[object] = None,
    ) -> str:
        """Classify non-live evaluation windows for analysis/paper strategies."""
        local_dt = self._coerce_datetime(now)
        if self.calendar.session_for(local_dt) != SESSION_REGULAR:
            return ""
        clock = local_dt.time().replace(tzinfo=None)
        if self._in_windows(clock, self.midday_paper_windows):
            return "MIDDAY_VWAP_RECLAIM"
        if self._in_windows(clock, self.afternoon_entry_windows):
            return "AFTERNOON_SECOND_WAVE"
        if self._in_windows(clock, self.closing_paper_windows):
            return "CLOSING_STRENGTH"
        return ""

    def paper_strategy_allowed(
        self,
        *,
        now: Optional[object] = None,
    ) -> bool:
        return bool(self.paper_strategy_type(now=now))

    def entry_window_deadline(
        self,
        *,
        now: Optional[object] = None,
        context: Optional[Dict[str, object]] = None,
        include_next: bool = False,
    ) -> Optional[datetime]:
        local_dt = self._coerce_datetime(now)
        if not bool(self.config.time_policy_enabled):
            return datetime.combine(local_dt.date(), self.regular_close, tzinfo=self.timezone)
        session = self.calendar.session_for(local_dt)
        if session not in {SESSION_PRE_OPEN, SESSION_REGULAR}:
            return None
        clock = local_dt.time().replace(tzinfo=None)
        if self._late_a_grade_entry_allowed(clock, context):
            return datetime.combine(
                local_dt.date(),
                self.late_a_grade_entry_end,
                tzinfo=self.timezone,
            )
        for start, end in self.entry_windows:
            if start <= clock <= end or (include_next and clock < start):
                return datetime.combine(local_dt.date(), end, tzinfo=self.timezone)
        return None

    def _entry_allowed_for_clock(
        self,
        clock: dt_time,
        session: str,
        context: Optional[Dict[str, object]],
    ) -> bool:
        if session == SESSION_AFTER_MARKET:
            return bool(self.config.allow_after_hours_entry)
        if session != SESSION_REGULAR:
            return False
        if self.force_exit_start <= clock <= self.force_exit_deadline:
            return False
        if clock >= self.no_new_entry_after:
            return False
        return self._in_windows(clock, self.entry_windows) or self._late_a_grade_entry_allowed(
            clock,
            context,
        )

    def _late_a_grade_entry_allowed(
        self,
        clock: dt_time,
        context: Optional[Dict[str, object]],
    ) -> bool:
        if not bool(getattr(self.config, "allow_late_a_grade_entry", False)):
            return False
        if not (self.late_a_grade_entry_start <= clock <= self.late_a_grade_entry_end):
            return False
        ctx = context or {}
        grade = str(ctx.get("candidate_grade") or ctx.get("grade") or "").upper()
        entry_type = str(ctx.get("entry_type") or "").upper()
        return (
            bool(ctx.get("late_a_grade_candidate"))
            or grade == "A"
            or entry_type == "BREAKOUT_SMALL"
        )

    @staticmethod
    def _observation_overruns_deadline(
        local_dt: datetime,
        min_observation_sec: float,
        deadline: Optional[datetime],
    ) -> bool:
        if deadline is None:
            return True
        return local_dt + timedelta(seconds=max(float(min_observation_sec or 0), 0.0)) > deadline

    def _decision(
        self,
        allowed: bool,
        action: str,
        reason_code: str,
        now: Optional[object],
        *,
        session: str = "",
        next_allowed_time: Optional[str] = None,
        candidate_role: str = "",
        context: Optional[Dict[str, object]] = None,
    ) -> TimeDecision:
        local_dt = self._coerce_datetime(now)
        session_value = (
            (session or self.calendar.session_for(local_dt))
            if bool(self.config.time_policy_enabled)
            else SESSION_DISABLED
        )
        permissions = self.permission_snapshot(now=local_dt, context=context)
        return TimeDecision(
            allowed=bool(allowed),
            action=str(action),
            reason_code=str(reason_code),
            current_time=local_dt.isoformat(),
            session=session_value,
            next_allowed_time=next_allowed_time,
            config_version=self.config_version,
            time_decision_id=uuid.uuid4().hex,
            entry_allowed=permissions["entry_allowed"],
            capture_allowed=permissions["capture_allowed"],
            manage_allowed=permissions["manage_allowed"],
            analysis_allowed=permissions["analysis_allowed"],
            candidate_role=str(candidate_role or ""),
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
