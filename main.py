from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import json
import os
import sys
import time
import urllib.error
import urllib.request

import pandas as pd
import pickle

import scoring
import entry_strategy
import exit_strategy
from bars import FiveMinIndicatorCache, MinuteBarAggregator
from condition_capture_logger import CONDITION_CAPTURE_CSV, ConditionCaptureLogger
from market_state import KOSDAQ_CODE, KOSPI_CODE, MarketStateCache
from portfolio import LoadedPortfolioState, Position, PortfolioState
from logging_setup import setup_logging
from fid_codes import FID_CODES, FID_NAME_TO_CODE, get_fid
from quant_condition_strategy import QuantConditionStrategy, QuantStrategyConfig
from training_recorder import (
    TrainingRecorderMixin,
    # 모듈 상수 re-export — 외부 테스트가 main.X 로 직접 접근하므로 호환 유지
    TRAINING_DATA_DIR,
    TRADE_LOG_CSV,
    DANTE_TRAINING_DATA_ENABLED,
    DANTE_TRAINING_CSV,
    DANTE_TRAINING_LABEL_HORIZONS,
    DANTE_TRAINING_FINAL_HORIZON_SECONDS,
    DANTE_TRAINING_SAMPLE_COOLDOWN_SECONDS,
    DANTE_TRAINING_FIELDS,
    DANTE_SHADOW_TRAINING_DATA_ENABLED,
    DANTE_SHADOW_TRAINING_CSV,
    DANTE_SHADOW_SAMPLE_COOLDOWN_SECONDS,
    DANTE_SHADOW_TRAINING_FIELDS,
    TRADE_LOG_CONDITION_FORMULA,
    TRADE_LOG_CONDITION_RULES,
    TRADE_LOG_RULE_VERSION,
    TRADE_LOG_STRATEGY_NAME,
    TRADE_LOG_FIELDS,
)


logger = setup_logging()

# ===== 퀀트조건식 눌림 전략 =====
# 영웅문에 저장된 조건식 이름과 정확히 일치해야 한다. 조건식 자체의 A/J/N/P/S/T
# 필터는 영웅문 조건검색이 담당하고, 이 프로그램은 편입 후 실시간으로 포착가 대비
# -1.5% 눌림 + 체결강도 100% 이상만 진입 트리거로 확인한다.
CONDITION_NAME = "단테떡상이"
CONDITION_SCREEN_NO = "0150"
REALTIME_SCREEN_NO = "0160"
# KOSPI/KOSDAQ 업종지수 실시간용 별도 스크린(종목 실시간과 충돌 방지).
INDEX_REALTIME_SCREEN_NO = "0170"
ORDER_SCREEN_NO = "0001"
# 조건식 편입 종목 전체를 AI 후보평가 대상으로 올리고, 퀀트조건식 룰은 feature/가드레일로 사용한다.
AI_SERVER_ENABLED = True
AI_SERVER_URL = "http://127.0.0.1:8000"
AI_SERVER_TIMEOUT_SECONDS = 0.35
# 학습 트랙(단테 + shadow) 의 enable 플래그/CSV 경로/필드 정의는
# training_recorder 모듈로 이전했다. 같은 이름의 모듈 상수를 main 에서 re-export
# 하므로 기존 ``from main import DANTE_TRAINING_CSV`` 같은 사용처는 그대로 동작한다.

# === 장중 크래시 복원용 portfolio 상태 디스크 영속화 ===
# Position 의 전략 필드(entry_stage / planned_quantity / stop_price / partial_taken /
# breakout_high / breakout_grade / pullback_window_deadline 등) 는 메모리에만 있다.
# 장중에 프로세스가 죽으면 잔고 TR 응답으로 quantity/entry_price 만 회복되고 위 필드들은
# 모두 0/false 로 초기화된다. 그러면 BE 스탑이 풀려 -1R 보호가 사라지고, 1차에 25%만
# 사놓고 2차 본진입이 영원히 발사 안 되는 등 운영 사고가 난다.
# 이를 막기 위해 매 chejan 이벤트, 매도 의도 큐 변경, 매도 평가 종료 시점마다 atomic
# write 한다. 부팅 시 잔고 TR 보다 먼저 로드해 두면, _sync_position_from_dicts 가
# 잔고 정보로 휘발성 필드만 덮어쓰고 전략 필드는 그대로 보존된다.
PORTFOLIO_STATE_PATH = os.path.join(TRAINING_DATA_DIR, "portfolio_state.json")
BUY_CASH_BUFFER_RATE = 0.98
BUY_PRICE_MARGIN_RATE = 1.005
RISK_PER_TRADE_RATE = 0.005
MAX_PORTFOLIO_RISK_RATE = 0.02
MIN_ORDER_CASH = 50_000
SAFE_PULLBACK_MIN_DROP_PCT = 0.015
SAFE_PULLBACK_MAX_DROP_PCT = 0.030
SAFE_PULLBACK_REBOUND_CONFIRM_PCT = 0.003
SAFE_PULLBACK_RUNAWAY_PCT = 0.030
SAFE_PULLBACK_VOLUME_RATIO_MAX = 0.30
SAFE_PULLBACK_CASH_RATE = 0.10
SAFE_PULLBACK_FIRST_ENTRY_RATIO = 0.50
SAFE_PULLBACK_MAX_POSITIONS = 3
SAFE_PULLBACK_STOP_LOSS_PCT = 0.015
SAFE_PULLBACK_TAKE_PROFIT_PCT = 0.020
SAFE_PULLBACK_TARGET_NEAR_PCT = 0.003
SAFE_PULLBACK_ASK_BID_RATIO_MIN = 2.0
SAFE_PULLBACK_BIG_BUY_MULT = 3.0
SAFE_PULLBACK_BIG_BUY_MIN_QTY = 1_000
SAFE_PULLBACK_SECOND_WINDOW_SECONDS = 10 * 60
SAFE_PULLBACK_SECOND_MIN_REBOUND_PCT = 0.003
SAFE_PULLBACK_SECOND_MAX_CHASE_PCT = 0.012
QUANT_ENTRY_PULLBACK_PCT = SAFE_PULLBACK_MIN_DROP_PCT
QUANT_ENTRY_CHEJAN_STRENGTH_MIN = 100.0
QUANT_TAKE_PROFIT_PCT = SAFE_PULLBACK_TAKE_PROFIT_PCT
QUANT_STOP_LOSS_PCT = SAFE_PULLBACK_STOP_LOSS_PCT
QUANT_PLAN_SOURCE = "quant_condition_pullback"
QUANT_GRADE = "QUANT"
QUANT_STRATEGY_CONFIG = QuantStrategyConfig(
    condition_name=CONDITION_NAME,
    entry_pullback_pct=QUANT_ENTRY_PULLBACK_PCT,
    max_pullback_pct=SAFE_PULLBACK_MAX_DROP_PCT,
    rebound_confirm_pct=SAFE_PULLBACK_REBOUND_CONFIRM_PCT,
    min_chejan_strength=QUANT_ENTRY_CHEJAN_STRENGTH_MIN,
    take_profit_pct=QUANT_TAKE_PROFIT_PCT,
    stop_loss_pct=QUANT_STOP_LOSS_PCT,
    max_positions=SAFE_PULLBACK_MAX_POSITIONS,
    plan_source=QUANT_PLAN_SOURCE,
    grade=QUANT_GRADE,
)
ENTRY_PLAN_EXPIRY_SECONDS = 45
# 매수 미체결 만료 점검 주기 (ms). 45초 expiry 와 ±2~5초 정밀도면 충분.
BUY_ORDER_EXPIRY_CHECK_INTERVAL_MS = 5000
# SendOrder 직후에는 키움 미체결 TR에 주문이 몇 초 늦게 반영될 수 있다. 이 시간을 넘겼는데
# 계좌 미체결에도 없으면 로컬 pending으로만 남은 유령 주문으로 보고 슬롯을 해제한다.
LOCAL_PENDING_ORDER_GRACE_SECONDS = 10
ENTRY_PLAN_MAX_ENTRY_PREMIUM_PCT = 0.001
ENTRY_PLAN_MIN_RISK_PCT = 0.004
ENTRY_PLAN_MAX_RISK_PCT = 0.022
ENTRY_PLAN_MIN_RR = 1.8
ENTRY_PLAN_TARGET_R = 2.0
# === fib retracement 기반 patient limit (윗자리 추격 방지) ===
# 풀백 저점에서 위로 N 비율 되돌린 자리에 patient 지정가를 둔다. 0.40 이면
# "풀백 깊이의 40% 만 회복한 지점" — 즉 직전 고점에서 -60% 자리. 풀백이 깊을수록
# 절대 가격 자리도 더 낮게 잡혀 종목 변동성에 자동 적응.
ENTRY_PLAN_FIB_RATIO = 0.40
# 풀백 저점 대비 회복(retracement) 가 N 이상이면 윗자리 추격으로 보고 plan 거절.
# 0.60 = 풀백 저점에서 60% 이상 회복한 지점 = fib_anchor 보다 위 → 매수 금지.
ENTRY_PLAN_MAX_RETRACEMENT = 0.60
# 풀백 자체가 N 미만이면 (= 사실상 풀백 미발생) anchor 가 의미 없어 plan 거절.
# breakout_high 직후 직진 상승 케이스를 거른다.
ENTRY_PLAN_MIN_PULLBACK_DEPTH = 0.003
# fib 분석에 사용할 1분봉 lookback 수.
ENTRY_PLAN_PULLBACK_LOOKBACK = 15
# 손절가는 오래된 장중 저점보다 최근 눌림 구조를 우선한다.
ENTRY_PLAN_STOP_LOOKBACK = 8
VOLUME_SPEED_COOLDOWN_TRIGGER = 3
VOLUME_SPEED_COOLDOWN_SECONDS = 5 * 60
MODEL_ASSIST_ONLY = True
AI_CANDIDATE_PROMOTION_ENABLED = False
AI_CANDIDATE_MIN_SCORE = 0.62
AI_CANDIDATE_WATCH_ENABLED = False
AI_CANDIDATE_WATCH_SECONDS = 20 * 60
AI_CANDIDATE_WATCH_RECHECK_INTERVAL_SECONDS = 30
AI_CANDIDATE_WATCH_MAX_CODES = 30
RISK_TOO_WIDE_WATCH_ENABLED = True
RISK_TOO_WIDE_WATCH_SECONDS = 20 * 60
RISK_TOO_WIDE_RECHECK_INTERVAL_SECONDS = 30
RISK_TOO_WIDE_MAX_CODES = 30
RISK_TOO_WIDE_MIN_MODEL_SCORE = 0.70
PULLBACK_RECOVERY_WATCH_REASON_CODES = {
    entry_strategy.GATE_STAGE2_PULLBACK_DEEP,
    entry_strategy.GATE_BGRADE_PULLBACK_DEEP,
    entry_strategy.GATE_STAGE2_VWAP_LOST,
    entry_strategy.GATE_BGRADE_VWAP_LOST,
}
MIN_EXPECTED_RETURN = 0.006
# 비용 반영 순기대수익률 기준(매수/목표가/로그에 사용)
ESTIMATED_BUY_FEE_RATE = 0.00015
ESTIMATED_SELL_FEE_RATE = 0.00015
ESTIMATED_SELL_TAX_RATE = 0.0018
ESTIMATED_SLIPPAGE_RATE = 0.0015
ESTIMATED_ROUND_TRIP_COST_RATE = (
    ESTIMATED_BUY_FEE_RATE
    + ESTIMATED_SELL_FEE_RATE
    + ESTIMATED_SELL_TAX_RATE
    + ESTIMATED_SLIPPAGE_RATE
)
MIN_NET_EXPECTED_RETURN = 0.006
DYNAMIC_MIN_NET_RETURN_PERCENTILE = 0.5
DYNAMIC_MIN_NET_RETURN_CEILING = 0.015
# 매수 가능 시간(장 마감 직전 강제 청산 시점은 OPENING_FORCE_EXIT 동일).
TIME_FILTER_MORNING_START = 90000
TIME_FILTER_MORNING_END = 100000
TIME_FILTER_MIDDAY_END = 140000
TIME_FILTER_CLOSING_END = 152000
TIME_FILTER_CLOSING_MIN_TURNOVER = 10_000_000_000
TIME_FILTER_CLOSING_TOP_RANK = 10
OPENING_BUY_START = TIME_FILTER_MORNING_START
OPENING_BUY_END = TIME_FILTER_CLOSING_END
OPENING_FORCE_EXIT = TIME_FILTER_CLOSING_END
# 실시간 틱 버퍼 크기 / 최소 틱 수 (단테 1차 게이트가 사용)
OPENING_MIN_TICKS = entry_strategy.DANTE_MIN_TICKS
OPENING_TICK_LIMIT = 40
# 호가 스프레드 상한
OPENING_MAX_SPREAD_RATE = entry_strategy.MAX_SPREAD_RATE
# 손절/시간 손절 등은 exit_strategy 모듈로 이전했다. 호환을 위해 alias 만 남긴다.
OPENING_STOP_LOSS_RATE = -exit_strategy.R_UNIT_PCT  # -1R
OPENING_MAX_HOLD_SECONDS = exit_strategy.EXIT_TIME_LIMIT_SECONDS                         
# 동시 종목 수는 리스크 예산 기반 sizing 의 안전 상한이다. 실제 진입 가능 여부는
# RISK_PER_TRADE_RATE / MAX_PORTFOLIO_RISK_RATE 가 결정한다.
MAX_CONCURRENT_POSITIONS = SAFE_PULLBACK_MAX_POSITIONS
MAX_DAILY_BUY_COUNT = 20
CONDITION_PROCESS_INTERVAL_MS = 1000
CONDITION_COOLDOWN_SECONDS = 60
WAIT_LOG_COOLDOWN_SECONDS = 30
REALTIME_TICK_WAIT_TIMEOUT_SECONDS = 60
MAX_DAILY_CANDLE_COUNT = 120
TR_REQUEST_INTERVAL_SECONDS = 0.35
ORDER_REQUEST_INTERVAL_SECONDS = 0.25
ACCOUNT_CACHE_SECONDS = 20
DEPOSIT_CACHE_SECONDS = 10
REALTIME_CODES_PER_SCREEN = 100
POSITION_CHECK_INTERVAL_MS = 10000
SELL_CHECK_INTERVAL_MS = 1500
SELL_INTENT_RETRY_SECONDS = 2.0
SELL_SKIP_LOG_COOLDOWN_SECONDS = 30
TR_RESPONSE_TIMEOUT_MS = 5000
AI_SERVER_FAILURE_THRESHOLD = 3
AI_SERVER_COOLDOWN_SECONDS = 30
# 학습/거래 로그 필드 정의(TRADE_LOG_FIELDS)
# 는 training_recorder.py 로 이전. 본 파일 상단 import 에서 re-export 한다.


class Kiwoom(TrainingRecorderMixin, QAxWidget):
    def __init__(self):
        super().__init__()
        self._make_kiwoom_instance()
        self._set_signal_slots()
        self._comm_connect()
        self.account_number = self.get_account_number()
        self.tr_event_loop = QEventLoop()
        self.universe_realtime_transaction_info = []
        self.best = {}
        self.condition_event_loop = None
        self.conditions = {}
        self.selected_condition = None
        self.pending_condition_codes = []
        self.processing_condition = False
        self.last_signal_at = {}
        self.last_wait_log_at = {}
        self.volume_speed_wait_counts = {}
        self.volume_speed_cooldown_until = {}
        self.no_tick_codes = set()
        self.holding_codes = set()
        self.pending_order_codes = set()
        self.bought_codes = set()
        self.order_prices = {}
        self.target_returns = {}
        self.position_quantities = {}
        self.available_quantities = {}
        self.entry_times = {}
        self.highest_prices = {}
        self.realtime_registered_codes = set()
        self.realtime_code_screens = {}
        self.realtime_ticks = {}
        self.orderbook_snapshots = {}
        self.condition_registered_at = {}
        self.quant_strategy = QuantConditionStrategy(QUANT_STRATEGY_CONFIG)
        self.condition_capture_logger = ConditionCaptureLogger(CONDITION_CAPTURE_CSV)
        # 단테 학습 트랙(Phase A) 의 sample_id → 진행 정보. 5/10/20분 horizon 라벨링 후 CSV flush.
        self.pending_dante_samples = {}
        self.last_dante_sample_at = {}
        # shadow 학습 트랙: 게이트가 거른(wait/blocked) 표본을 같은 25분 horizon 으로 사후 라벨링.
        # ready 표본과 같은 풀에 들어가지 않도록 별도 dict + 별도 CSV 로 분리.
        self.pending_dante_shadow_samples = {}
        self.last_dante_shadow_sample_at = {}
        self.monitoring_dict = {}
        self.dante_a_watchlist = {}
        self.dante_reentry_watchlist = {}
        self.ai_candidate_watchlist = {}
        self.risk_too_wide_watchlist = {}
        self.order_context = {}
        self.last_tr_request_at = 0
        self.last_order_request_at = 0
        self._tr_busy = False
        self._selling_codes = set()
        self.pending_sell_order_codes = set()
        self.pending_sell_intents = {}
        self.last_sell_skip_log_at = {}
        self.cached_deposit = None
        self.deposit_updated_at = 0
        self.cached_balance = []
        self.cached_orders = []
        self.account_updated_at = 0
        self.trading_day = ""
        # 점진적 dataclass 마이그레이션용 새 컨테이너. 현재는 기존 dict들과 병행 운영된다.
        # Phase 3: write 경로에서 parallel write, 추후 read 경로도 portfolio 기반으로 전환.
        self.portfolio = PortfolioState()
        # 단테 추세전략용 1분봉 집계기 + 5분봉 BB/Envelope 캐시.
        # 1분봉은 실시간 틱(append_realtime_tick) 에서, 5분봉은 opt10080 TR 응답에서 push 된다.
        self.minute_aggregator = MinuteBarAggregator(max_bars=60)
        self.five_min_cache = FiveMinIndicatorCache()
        # 매크로 dry-run 게이트용 KOSPI/KOSDAQ 실시간 지수 캐시.
        # 미수신 시 entry_strategy 가 neutral fallback 으로 안전 처리한다.
        self.market_state = MarketStateCache()
        self.index_realtime_registered = False
        self.ai_server_failure_count = 0
        self.ai_server_cooldown_until = 0.0
        self.condition_timer = QTimer()
        self.condition_timer.timeout.connect(self.process_next_condition_stock)
        self.position_check_timer = QTimer()
        self.position_check_timer.timeout.connect(self.check_open_positions)
        self.sell_check_timer = QTimer()
        self.sell_check_timer.timeout.connect(self.check_pending_sells)
        # 매수 미체결 만료 점검 — fib_anchor 자리에 둔 patient 지정가가 expiry_seconds
        # 안에 안 잡히면 자동 취소해 슬롯을 해제한다.
        self.buy_expiry_timer = QTimer()
        self.buy_expiry_timer.timeout.connect(self.cancel_stale_buy_orders)

    
    def _make_kiwoom_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1')


    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._login_slot)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveMsg.connect(self._on_receive_msg)
        self.OnReceiveChejanData.connect(self._on_receive_chejan)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveConditionVer.connect(self._on_receive_condition_ver)
        self.OnReceiveTrCondition.connect(self._on_receive_tr_condition)
        self.OnReceiveRealCondition.connect(self._on_receive_real_condition)
    
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        logger.debug("[메시지] %s %s %s %s", screen_no, rqname, trcode, msg)

    def get_chejan_value(self, fid, default=""):
        value = self.dynamicCall("GetChejanData(int)", fid).strip()
        value = value.lstrip("+")
        return value if value != "" else default

    def parse_int(self, value, default=0):
        try:
            if value is None or value == "":
                return default
            return abs(int(str(value).strip().lstrip("+").lstrip("-")))
        except (TypeError, ValueError):
            return default

    def parse_float(self, value, default=0.0):
        try:
            if value is None or value == "":
                return default
            return float(str(value).strip().replace("%", ""))
        except (TypeError, ValueError):
            return default
    
    def _on_receive_chejan(self, gubun, cnt, fid_list):
        logger.debug("[체결잔고] gubun=%s cnt=%s fid_list=%s", gubun, cnt, fid_list)
        raw_code = self.get_chejan_value("9001")
        code = self.normalize_code(raw_code)

        for fid in fid_list.split(';'):
            if not fid:
                continue
            data = self.dynamicCall("GetChejanData(int)", fid).lstrip("+").lstrip("-")
            if data.isdigit():
                data = int(data)
            name = FID_CODES.get(fid, fid)
            logger.debug('%s: %s', name, data)

        order_status = self.get_chejan_value("913")
        order_no = self.get_chejan_value("9203")
        order_type = self.get_chejan_value("905")
        left_quantity = self.get_chejan_value("902")
        order_price = self.get_chejan_value("901")
        order_quantity = self.get_chejan_value("900")
        executed_price = self.get_chejan_value("910")
        executed_quantity = self.get_chejan_value("911")
        current_price = self.get_chejan_value("10")
        context = self.order_context.get(code, {})
        left_quantity_int = self.parse_int(left_quantity)
        chejan_side = context.get("side", "")
        if "매도" in order_type:
            chejan_side = "sell"
        elif "매수" in order_type:
            chejan_side = "buy"
        order_terminated = False
        if order_status in ("접수", "확인"):
            self.pending_order_codes.add(code)
            if chejan_side == "sell":
                self.pending_sell_order_codes.add(code)
            # 매수 접수 시점에만 채워두면 cancel_stale_buy_orders 가 만료된 주문에
            # 같은 order_no 로 취소 요청을 보낼 수 있다(키움 SendOrder 는 즉시
            # 주문번호를 주지 않음 — chejan "접수" 이벤트가 유일한 출처).
            if chejan_side == "buy" and code and order_no:
                ctx = self.order_context.get(code)
                if isinstance(ctx, dict) and not ctx.get("order_no"):
                    ctx["order_no"] = order_no
        elif order_status == "체결":
            if left_quantity_int > 0:
                self.pending_order_codes.add(code)
                if chejan_side == "sell":
                    self.pending_sell_order_codes.add(code)
            else:
                self.pending_order_codes.discard(code)
                if chejan_side == "sell":
                    self.pending_sell_order_codes.discard(code)
                order_terminated = True
        elif "거부" in order_status or "취소" in order_status:
            self.pending_order_codes.discard(code)
            if chejan_side == "sell":
                self.pending_sell_order_codes.discard(code)
            order_terminated = True
            # 매수 거부/취소: 보유 quantity==0 이면 portfolio 에서 완전 제거,
            # 부분체결 후 잔량 취소면 pending_buy=False 만 풀어 보유 종목으로 전환.
            # 이 정리가 빠지면 should_skip_buy 의 is_pending() 가 계속 True 라
            # 같은 종목 재진입(다음 사이클의 fib anchor 자리)이 영구 차단된다.
            if chejan_side == "buy" and code:
                position = self.portfolio.get(code)
                if position is not None:
                    if position.quantity == 0 and not position.is_holding():
                        self._discard_position(code, save=False, persist=False)
                    else:
                        position.pending_buy = False
                # A-watch 도 정리 — 다음 사이클에 새 fib_anchor 로 재평가 가능하게.
                self.dante_a_watchlist.pop(code, None)
        self.append_trade_log(
            "chejan",
            code=code,
            name=context.get("name", self.get_code_name(code) if code else ""),
            side=chejan_side,
            order_type=order_type,
            order_status=order_status,
            order_no=order_no,
            quantity=order_quantity,
            order_price=order_price,
            current_price=current_price,
            executed_price=executed_price,
            executed_quantity=executed_quantity,
            entry_price=context.get("entry_price", self.order_prices.get(code, "")),
            target_price=context.get("target_price", self.best.get(code, "")),
            score=context.get("score", ""),
            expected_return=context.get("expected_return", ""),
            model_name=context.get("model_name", ""),
            model_score=context.get("model_score", ""),
            model_action=context.get("model_action", ""),
            model_target=context.get("model_target", ""),
            model_threshold=context.get("model_threshold", ""),
            reason=context.get("reason", ""),
            hold_seconds=context.get("hold_seconds", ""),
            profit_rate=context.get("profit_rate", ""),
            message="gubun {}".format(gubun),
        )

        gubun_str = str(gubun)
        if order_status == "체결" and code and gubun_str == "0":
            side = chejan_side
            executed_quantity_int = self.parse_int(executed_quantity)
            executed_price_int = self.parse_int(executed_price)
            if side == "buy" and executed_quantity_int > 0:
                previous_quantity = self.parse_int(self.position_quantities.get(code, 0))
                previous_entry_price = self.parse_int(self.order_prices.get(code, 0))
                entry_price = executed_price_int or previous_entry_price or self.parse_int(current_price)
                total_quantity = previous_quantity + executed_quantity_int
                if previous_quantity > 0 and previous_entry_price > 0 and executed_price_int > 0 and total_quantity > 0:
                    weighted_sum = previous_entry_price * previous_quantity + executed_price_int * executed_quantity_int
                    entry_price = round(weighted_sum / total_quantity)

                self.holding_codes.add(code)
                self.position_quantities[code] = total_quantity
                if entry_price:
                    self.order_prices[code] = entry_price
                    self.highest_prices[code] = max(self.highest_prices.get(code, entry_price), entry_price)
                self.entry_times.setdefault(code, time.time())

                # Portfolio dataclass 마이그레이션: 매수 체결 시점에 Position을 동기 갱신.
                position = self.portfolio.get_or_create(code, name=context.get("name", "") or self.get_code_name(code))
                position.quantity = total_quantity
                if entry_price:
                    position.entry_price = entry_price
                    position.update_highest(entry_price)
                if not position.entry_time:
                    position.entry_time = time.time()
                position.bought_today = True
                position.pending_buy = left_quantity_int > 0
                if isinstance(context, dict):
                    position.order_context = dict(context)
                    planned_stop = self.parse_int(context.get("stop_price", 0))
                    planned_target = self.parse_int(context.get("take_profit_price", 0))
                    if planned_stop > 0:
                        position.stop_price = planned_stop
                    if planned_target > 0:
                        position.target_price = planned_target
                        self.best[code] = planned_target

                # === 단테 분할매수 상태 갱신 ===
                stage_executed = int(context.get("stage", 1) or 1) if isinstance(context, dict) else 1
                planned_from_ctx = self.parse_int(context.get("planned_quantity", 0)) if isinstance(context, dict) else 0
                grade_from_ctx = (
                    str(context.get("grade", "") or "") if isinstance(context, dict) else ""
                )
                if planned_from_ctx > 0 and position.planned_quantity <= 0:
                    position.planned_quantity = planned_from_ctx
                if grade_from_ctx and not position.breakout_grade:
                    position.breakout_grade = grade_from_ctx
                # 부분체결 중에는 stage 를 올리지 않는다(잔여 0이 되어야 단계 완료).
                if left_quantity_int <= 0:
                    if stage_executed >= 2:
                        position.entry_stage = 2
                        position.entry2_time = time.time()
                        # B급 일괄 체결 — entry1_time 도 함께 채워야 시간손절 anchor 가 잡힌다.
                        if not position.entry1_time:
                            position.entry1_time = position.entry2_time
                    elif position.entry_stage < 1:
                        position.entry_stage = 1
                        position.entry1_time = time.time()
                        position.pullback_window_deadline = (
                            position.entry1_time + entry_strategy.PULLBACK_WINDOW_MAX_SECONDS
                        )
                # 1차 체결 시점에 R-multiple 트레일링 초기 셋업.
                if position.entry_stage >= 1:
                    if position.r_unit_pct <= 0:
                        position.r_unit_pct = exit_strategy.R_UNIT_PCT
                    # 평단(체결가 기반) 대비 -1R 로 stop 초기화. 가중평균이 변하면 다시 잡는다.
                    initial_stop = int(position.entry_price * (1 - position.r_unit_pct))
                    if position.stop_price <= 0:
                        position.stop_price = initial_stop
                    if position.breakout_high <= 0:
                        position.breakout_high = position.entry_price

                self.register_realtime_stock(code)
                if left_quantity_int <= 0:
                    self.pending_order_codes.discard(code)
                self.account_updated_at = 0
                self.deposit_updated_at = 0
                self.process_pending_sell_intents([code])

                # 1차 체결 직후 즉시 2차 평가가 돌도록 condition 큐에 다시 등록.
                if left_quantity_int <= 0 and position.entry_stage == 1:
                    self.requeue_condition_stock(code)
            elif side == "sell" and executed_quantity_int > 0:
                remaining_quantity = max(self.position_quantities.get(code, 0) - executed_quantity_int, 0)
                self.position_quantities[code] = remaining_quantity
                if remaining_quantity <= 0 and left_quantity_int <= 0:
                    position = self.portfolio.get(code)
                    self.maybe_start_reentry_watch(
                        code,
                        position,
                        exit_price=executed_price_int or self.parse_int(current_price),
                        reason=context.get("reason", "") if isinstance(context, dict) else "",
                    )
                    # _discard_position이 portfolio에서도 제거하므로 별도 동기화 불필요.
                    self._discard_position(code)
                else:
                    # Portfolio dataclass 마이그레이션: 부분 체결 시 수량/대기 플래그만 갱신.
                    position = self.portfolio.get(code)
                    if position is not None:
                        position.quantity = remaining_quantity
                        position.pending_sell = left_quantity_int > 0
                if left_quantity_int <= 0:
                    self.pending_sell_order_codes.discard(code)
                self.account_updated_at = 0
                self.deposit_updated_at = 0

        elif gubun_str == "1" and code:
            held_quantity = self.parse_int(self.get_chejan_value("930"))
            average_price = self.parse_int(self.get_chejan_value("931"))
            available_quantity = self.parse_int(self.get_chejan_value("933"))
            if held_quantity > 0:
                self.holding_codes.add(code)
                self.position_quantities[code] = held_quantity
                self.available_quantities[code] = available_quantity
                if average_price > 0:
                    self.order_prices[code] = average_price
                    target_return = self.target_returns.get(code)
                    if isinstance(target_return, (int, float)) and target_return > 0:
                        target_price = self.compute_target_price(average_price, target_return)
                        if target_price > 0:
                            self.best[code] = target_price
                            self.save_best()
                # Portfolio dataclass 마이그레이션: 잔고 변경 통보 시 Position도 동기화.
                self._sync_position_from_dicts(code)
            else:
                self._discard_position(code)
            self.account_updated_at = 0
            self.deposit_updated_at = 0
            self.process_pending_sell_intents([code])

        # 주문이 종료된 시점(체결 완료 또는 거부/취소)에서만 order_context를 정리한다.
        # 부분체결 중에는 컨텍스트가 필요하므로 유지한다.
        if order_terminated and code:
            self.order_context.pop(code, None)
            position = self.portfolio.get(code)
            if position is not None:
                position.order_context = {}

        # chejan 은 모든 매수/매도 체결의 진입점이라, 여기서 한 번만 disk 동기화하면
        # entry_stage/planned_quantity/stop_price 변경이 빠짐없이 반영된다.
        self.save_portfolio_state()

    def _on_receive_condition_ver(self, ret, msg):
        logger.info("조건식 로드 결과: ret=%s msg=%s", ret, msg)
        self.conditions = self.get_condition_name_list()
        if self.condition_event_loop is not None:
            self.condition_event_loop.exit()

    def _on_receive_tr_condition(self, screen_no, code_list, condition_name, condition_index, next):
        codes = [code for code in code_list.split(';') if code]
        logger.info("[조건검색 초기조회] {}({}) {}건".format(condition_name, condition_index, len(codes)))
        for code in codes:
            self.register_condition_detected_stock(
                code,
                condition_name,
                "I",
                condition_index=condition_index,
                screen_no=screen_no,
            )

    def _on_receive_real_condition(self, code, event_type, condition_name, condition_index):
        if event_type == "I":
            logger.info("[조건편입] {} {}({})".format(code, condition_name, condition_index))
            self.register_condition_detected_stock(
                code,
                condition_name,
                event_type,
                condition_index=condition_index,
                screen_no=CONDITION_SCREEN_NO,
            )
        elif event_type == "D":
            logger.info("[조건이탈] {} {}({})".format(code, condition_name, condition_index))

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, v1, v2, v3, v4):
        logger.debug("[TR응답] %s %s %s %s next=%s", screen_no, rqname, trcode, record_name, next)
        cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

        if next == '2':
            self.isnext = True
        else:
            self.isnext = False

        if rqname == "opt10081":
            total = []
            for i in range(cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()
                open = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip())
                high = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip())
                low = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip())
                close = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip())
                volume = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip())
                total.append([date, open, high, low, close, volume])
            self.tr_data = total
        elif rqname == "opt10080":
            # 분봉 TR. 응답 순서는 최신→과거이므로 OHLCV 튜플로 뒤집어 둔다.
            # 마지막 항목이 진행봉(0봉전), 그 직전이 1봉전 완성봉.
            bars = []
            for i in range(cnt):
                close_str = self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가"
                ).strip()
                if not close_str:
                    continue
                close_int = abs(int(close_str.lstrip("+").lstrip("-")))
                if close_int <= 0:
                    continue
                open_str = self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가"
                ).strip()
                high_str = self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가"
                ).strip()
                low_str = self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가"
                ).strip()
                vol_str = self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량"
                ).strip()
                open_int = abs(int(open_str.lstrip("+").lstrip("-"))) if open_str else close_int
                high_int = abs(int(high_str.lstrip("+").lstrip("-"))) if high_str else close_int
                low_int = abs(int(low_str.lstrip("+").lstrip("-"))) if low_str else close_int
                vol_int = abs(int(vol_str.lstrip("+").lstrip("-"))) if vol_str else 0
                bars.append((open_int, high_int, low_int, close_int, vol_int))
            bars.reverse()
            self.tr_data = bars
        elif rqname == "opw00001":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "주문가능금액")
            self.tr_data = int(deposit)
        elif rqname == "opt10075":
            box = []
            for i in range(cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명")
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문가격")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문구분")
                left_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "미체결수량")
                executed_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결량")
                ordered_at = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시간")
                fee = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "당일매매수수료")
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "당일매매세금")

                code = code.strip()
                code_name = code_name.strip()
                order_number = str(int(order_number.strip()))
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                current_price = int(current_price.strip().lstrip("+").lstrip("-"))
                order_type = order_type.strip().lstrip("+").lstrip("-")
                left_quantity = int(left_quantity.strip())
                executed_quantity = int(executed_quantity.strip())
                ordered_at = ordered_at.strip()
                fee = int(fee)
                tax = int(tax)

                box.append([code, code_name, order_number, order_status, order_quantity, order_price, current_price, order_type, left_quantity, executed_quantity, ordered_at, fee, tax])
            
            self.tr_data = box
        elif rqname == "opw00018":
            box = []
            for i in range(cnt):
                raw_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목코드")
                if not raw_code or not raw_code.strip():
                    raw_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입금액")
                available_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매매가능수량")

                code = raw_code.strip()
                if code.startswith("A") or code.startswith("a"):
                    code = code[1:]
                code_name = code_name.strip()
                if not code:
                    logger.warning("[잔고 파싱 경고] 종목코드 비어있음, 원본='{}', 종목명='{}'".format(raw_code, code_name))
                    continue
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)
                current_price = int(current_price)

                total_purchase_price = int(total_purchase_price)
                available_quantity = int(available_quantity)

                box.append([code, code_name, quantity, purchase_price, return_rate, current_price, total_purchase_price, available_quantity])
            self.tr_data = box


        self.tr_event_loop.exit()

        
    def _login_slot(self, err_code):
        if err_code == 0:
            logger.info("Connected to Kiwoom")
        else:
            logger.error("Failed to connect to Kiwoom")
        self.login_event_loop.exit()

    def _comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_number(self):
        account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCLIST")
        account_number = account_list.split(';')[0]
        logger.info("나의 계좌번호 : %s", account_number)
        return account_number

    def get_code_list_stock_market(self, market_type):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]
        return code_list

    def get_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def wait_for_tr_slot(self):
        elapsed = time.time() - self.last_tr_request_at
        if elapsed < TR_REQUEST_INTERVAL_SECONDS:
            time.sleep(TR_REQUEST_INTERVAL_SECONDS - elapsed)
        self.last_tr_request_at = time.time()

    def wait_for_order_slot(self):
        elapsed = time.time() - self.last_order_request_at
        if elapsed < ORDER_REQUEST_INTERVAL_SECONDS:
            time.sleep(ORDER_REQUEST_INTERVAL_SECONDS - elapsed)
        self.last_order_request_at = time.time()

    def request_tr(self, rqname, trcode, next, screen_no):
        self.wait_for_tr_slot()
        return self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)

    def _wait_tr_event(self, timeout_ms=TR_RESPONSE_TIMEOUT_MS):
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self.tr_event_loop.exit)
        timer.start(timeout_ms)
        try:
            self.tr_event_loop.exec_()
        finally:
            timer.stop()

    def _is_valid_tr_rows(self, data, expected_len):
        if not isinstance(data, list):
            return False
        for row in data:
            if not isinstance(row, list) or len(row) != expected_len:
                return False
        return True

    def load_conditions(self):
        self.condition_event_loop = QEventLoop()
        self.wait_for_tr_slot()
        self.dynamicCall("GetConditionLoad()")
        self.condition_event_loop.exec_()
        return self.conditions

    def get_condition_name_list(self):
        condition_text = self.dynamicCall("GetConditionNameList()")
        conditions = {}
        for item in condition_text.split(';'):
            if not item:
                continue
            index, name = item.split('^')
            conditions[name] = int(index)
        logger.info("저장된 조건식 목록: %s", conditions)
        return conditions

    def select_condition(self, condition_name=CONDITION_NAME):
        if not self.conditions:
            self.load_conditions()

        if not self.conditions:
            logger.warning("저장된 조건식이 없습니다. 영웅문에서 조건식을 먼저 저장해주세요.")
            return None

        if condition_name:
            condition_index = self.conditions.get(condition_name)
            if condition_index is None:
                logger.warning("'{}' 조건식을 찾을 수 없습니다.".format(condition_name))
                return None
            self.selected_condition = (condition_name, condition_index)
        else:
            first_name = next(iter(self.conditions))
            self.selected_condition = (first_name, self.conditions[first_name])
            logger.info("CONDITION_NAME이 비어 있어 첫 번째 조건식을 사용합니다: %s", first_name)

        return self.selected_condition

    def start_realtime_condition(self, condition_name=CONDITION_NAME):
        selected = self.select_condition(condition_name)
        if selected is None:
            return False

        name, index = selected
        self.wait_for_tr_slot()
        result = self.dynamicCall(
            "SendCondition(QString, QString, int, int)",
            CONDITION_SCREEN_NO,
            name,
            index,
            1,
        )
        logger.info("실시간 조건검색 시작: %s(%s) 결과: %s", name, index, result)
        if result == 1:
            self.condition_timer.start(CONDITION_PROCESS_INTERVAL_MS)
            return True
        return False

    def register_condition_detected_stock(
        self,
        code,
        condition_name="",
        event_type="I",
        *,
        condition_index="",
        screen_no="",
    ):
        """조건식 포착 직후 실시간 등록과 감시 큐 등록을 한 번에 수행한다."""
        code = self.normalize_code(code)
        if not code:
            return
        watch = self.ensure_monitoring_stock(code)
        watch["condition_name"] = condition_name or CONDITION_NAME
        watch["condition_event_type"] = event_type
        watch["condition_index"] = condition_index
        watch["condition_formula"] = TRADE_LOG_CONDITION_FORMULA
        try:
            self.condition_capture_logger.append_detection(
                code=code,
                name=self.get_code_name(code),
                condition_name=condition_name or CONDITION_NAME,
                condition_index=condition_index,
                event_type=event_type,
                screen_no=screen_no or CONDITION_SCREEN_NO,
            )
        except Exception as exc:
            logger.warning("[조건검색 포착 로그 실패] %s %s", code, exc)
        if code not in self.realtime_registered_codes:
            self.register_realtime_stock(code)
            self.condition_registered_at[code] = time.time()
            logger.info(
                "[조건편입 실시간등록] %s %s event=%s screen=%s - 첫 실시간 체결가를 포착가로 사용",
                code,
                condition_name or CONDITION_NAME,
                event_type,
                self.realtime_code_screens.get(code, ""),
            )
        else:
            self.condition_registered_at.setdefault(code, time.time())
        self.enqueue_condition_stock(code, condition_name, event_type)

    def enqueue_condition_stock(self, code, condition_name="", event_type="I"):
        code = self.normalize_code(code)
        if not code:
            return
        now = time.time()
        last_at = self.last_signal_at.get(code, 0)
        if now - last_at < CONDITION_COOLDOWN_SECONDS:
            return
        if code in self.pending_condition_codes:
            return

        self.last_signal_at[code] = now
        self.pending_condition_codes.append(code)
        logger.info("[조건검색 대기열] {} {} {} 대기 {}건".format(code, condition_name, event_type, len(self.pending_condition_codes)))
    
    def get_price(self, code):
        if self._tr_busy:
            logger.warning("[TR 보류] opt10081 다른 TR 진행중")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume']).set_index('date')
        self._tr_busy = True
        try:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.request_tr("opt10081", "opt10081", 0, "0020")
            self._wait_tr_event()

            total = self.tr_data

            while self.isnext and len(total) < MAX_DAILY_CANDLE_COUNT:
                self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
                self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
                self.request_tr("opt10081", "opt10081", 2, "0020")
                self._wait_tr_event()
                total += self.tr_data

            if len(total) > MAX_DAILY_CANDLE_COUNT:
                total = total[:MAX_DAILY_CANDLE_COUNT]

            df = pd.DataFrame(total, columns=['date', 'open', 'high', 'low', 'close', 'volume']).set_index('date')
            df = df.drop_duplicates()
            df = df.sort_index()
            return df
        finally:
            self._tr_busy = False

    def get_5min_chart(self, code, count=80):
        """opt10080 5분봉 OHLCV 튜플 리스트(과거→최신).

        각 항목 = (open, high, low, close, volume). 마지막 항목이 진행봉(0봉전).
        데이터 없거나 TR 분주 시 빈 리스트.
        """
        if self._tr_busy:
            return []
        self._tr_busy = True
        try:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "틱범위", "5")
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.tr_data = []
            self.request_tr("opt10080", "opt10080", 0, "0021")
            self._wait_tr_event()
            data = self.tr_data if isinstance(self.tr_data, list) else []
            if count > 0 and len(data) > count:
                data = data[-count:]
            return data
        finally:
            self._tr_busy = False

    def refresh_five_min_indicators(self, code, refresh_seconds=60.0):
        """opt10080 응답으로 5분봉 BB/Envelope/OHLC 캐시를 갱신한다.

        TR 빈도 제한(초 5회) 안에서 동작하도록 needs_refresh 로 주기를 제한한다.
        TR 가 분주(_tr_busy)하면 다음 호출에서 다시 시도한다.
        진행봉 close 는 실시간 마지막 틱으로 덮어써 stale 을 보정한다.
        """
        code = self.normalize_code(code)
        if not code:
            return
        if not self.five_min_cache.needs_refresh(code, refresh_seconds=refresh_seconds):
            return
        if self._tr_busy:
            return
        try:
            bars = self.get_5min_chart(code, count=80)
        except Exception as exc:
            logger.warning("[5분봉 조회 실패] %s %s", code, exc)
            return
        if not bars:
            return

        # 진행봉 close 를 실시간 마지막 틱으로 덮어쓰기 (TR 응답이 60초 stale 이어도 진행봉만큼은 최신).
        ticks = self.realtime_ticks.get(code, [])
        if ticks:
            last_close = self.parse_int(ticks[-1].get("close", 0))
            if last_close > 0 and bars:
                o, h, l, _c, v = bars[-1]
                if not o:
                    o = last_close
                new_h = max(h or last_close, last_close)
                new_l = min(l or last_close, last_close) if l else last_close
                bars[-1] = (o, new_h, new_l, last_close, v)

        self.five_min_cache.update_bars(code, bars)
        self.five_min_cache.mark_refreshed(code)

    def get_deposit(self, force=False):
        now = time.time()
        if not force and self.cached_deposit is not None and now - self.deposit_updated_at < DEPOSIT_CACHE_SECONDS:
            return self.cached_deposit
        if self._tr_busy:
            return self.cached_deposit if self.cached_deposit is not None else 0

        self._tr_busy = True
        try:
            self.tr_data = None
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
            self.request_tr("opw00001", "opw00001", 0, "0002")
            self._wait_tr_event()
            if isinstance(self.tr_data, int):
                self.cached_deposit = self.tr_data
                self.deposit_updated_at = time.time()
        finally:
            self._tr_busy = False
        return self.cached_deposit if self.cached_deposit is not None else 0

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_gubun, order_no = ""):
        self.wait_for_order_slot()
        order_result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", [rqname, screen_no, self.account_number, order_type, code, order_quantity, order_price, order_gubun, order_no])
        self.account_updated_at = 0
        self.deposit_updated_at = 0
        return order_result
    
    def get_order(self, force=False):
        now = time.time()
        if not force and now - self.account_updated_at < ACCOUNT_CACHE_SECONDS:
            return self.cached_orders
        if self._tr_busy:
            return self.cached_orders

        self._tr_busy = True
        try:
            self.tr_data = None
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
            self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
            self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")
            self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
            self.request_tr("opt10075", "opt10075", 0, "0002")
            self._wait_tr_event()
            if self._is_valid_tr_rows(self.tr_data, expected_len=13):
                self.cached_orders = self.tr_data
        finally:
            self._tr_busy = False
        return self.cached_orders

    def get_balance(self, force=False):
        now = time.time()
        if not force and now - self.account_updated_at < ACCOUNT_CACHE_SECONDS:
            return self.cached_balance
        if self._tr_busy:
            return self.cached_balance

        self._tr_busy = True
        try:
            self.tr_data = None
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
            self.request_tr("opw00018", "opw00018", 0, "0002")
            self._wait_tr_event()
            if self._is_valid_tr_rows(self.tr_data, expected_len=8):
                self.cached_balance = self.tr_data
        finally:
            self._tr_busy = False
        return self.cached_balance

    def get_real_int(self, code, fid_name):
        value = self.dynamicCall("GetCommRealData(QString, QString)", code, get_fid(fid_name)).strip()
        if not value:
            return 0
        try:
            return abs(int(value))
        except ValueError:
            # 업종지수(KOSPI/KOSDAQ) 등 일부 실시간 FID 는 '+6788.38' 같이 부호+소수 형태로 들어온다.
            try:
                return abs(int(float(value)))
            except (ValueError, TypeError):
                return 0

    def append_realtime_tick(self, code, signed_at, close, high, open, low, ask, bid, accum_volume, chejan_strength=0.0):
        code = self.normalize_code(code)
        if code in self.no_tick_codes:
            self.no_tick_codes.discard(code)
            self.requeue_condition_stock(code)
        received_at = time.time()
        ticks = self.realtime_ticks.setdefault(code, [])
        prev_accum_volume = self.parse_int(ticks[-1].get("accum_volume", 0)) if ticks else 0
        volume_delta = max(self.parse_int(accum_volume) - prev_accum_volume, 0) if prev_accum_volume > 0 else 0
        tick = {
            "received_at": received_at,
            "signed_at": signed_at,
            "close": close,
            "high": high,
            "open": open,
            "low": low,
            "ask": ask,
            "bid": bid,
            "accum_volume": accum_volume,
            "volume_delta": volume_delta,
            "chejan_strength": chejan_strength,
        }
        ticks.append(tick)
        if len(ticks) > OPENING_TICK_LIMIT:
            del ticks[:-OPENING_TICK_LIMIT]

        # 1분봉 집계기에도 동일 틱을 push 한다. open 이 변수 그림자 문제로 read-only 인 점을 명확히 처리.
        self.minute_aggregator.push(
            code,
            received_at=received_at,
            close=close,
            high=high,
            low=low,
            open_=open,
            accum_volume=accum_volume,
        )

        # 1차 진입 후 갱신되는 고점을 Position 에 기록한다(2차 눌림 판정 기준).
        position = self.portfolio.get(code)
        if position is not None and position.entry_stage >= 1 and close > 0:
            position.update_breakout_high(int(close))
            position.update_highest(int(close))
        watch = self.dante_a_watchlist.get(code)
        if watch is not None and close > 0:
            watch["breakout_high"] = max(self.parse_int(watch.get("breakout_high", 0)), int(close))
        self.update_monitoring_tick(code, tick)
        self.update_reentry_watch(code, close)

        self.update_dante_training_labels(code, close, received_at)
        self.update_dante_shadow_training_labels(code, close, received_at)

    def _on_receive_real_data(self, s_code, real_type, real_data):
        if real_type == "장시작시간":
            pass
        elif real_type == "업종지수":
            # KOSPI(001)/KOSDAQ(101) 실시간 지수 — market_state.MarketStateCache 갱신.
            # 등록 안 된 업종 코드는 cache 가 자동으로 무시한다.
            price = self.get_real_int(s_code, "현재가")
            if price > 0:
                self.market_state.update(str(s_code), float(price), time.time())
        elif real_type == "주식호가잔량":
            self.update_orderbook_snapshot(s_code)
        elif real_type == "주식체결":
            signed_at = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("체결시간"))
            close = self.get_real_int(s_code, "현재가")
            high = self.get_real_int(s_code, "고가")
            open = self.get_real_int(s_code, "시가")
            low = self.get_real_int(s_code, "저가")
            top_priority_ask = self.get_real_int(s_code, "(최우선)매도호가")
            top_priority_bid = self.get_real_int(s_code, "(최우선)매수호가")
            accum_volume = self.get_real_int(s_code, "누적거래량")
            chejan_strength_str = self.dynamicCall(
                "GetCommRealData(QString, QString)", s_code, get_fid("체결강도")
            ).strip()
            chejan_strength = self.parse_float(chejan_strength_str, 0.0)

            self.universe_realtime_transaction_info.append([s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume])
            self.append_realtime_tick(
                s_code, signed_at, close, high, open, low,
                top_priority_ask, top_priority_bid, accum_volume,
                chejan_strength=chejan_strength,
            )
    
    def set_real_reg(self, str_screen_no, str_code_list, str_fid_list, str_opt_type):
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", str_screen_no, str_code_list, str_fid_list, str_opt_type)

    def process_next_condition_stock(self):
        self.reset_daily_state()
        if self.processing_condition or not self.pending_condition_codes:
            return

        code = self.pending_condition_codes.pop(0)
        self.processing_condition = True
        try:
            self.handle_condition_stock(code)
        except Exception as e:
            logger.error("[조건검색 처리 오류] {} {}".format(code, e))
        finally:
            self.processing_condition = False

    def reset_daily_state(self):
        today = time.strftime("%Y-%m-%d")
        if self.trading_day == today:
            return
        self.trading_day = today
        self.bought_codes.clear()
        self.last_signal_at.clear()
        self.no_tick_codes.clear()
        self.last_wait_log_at.clear()
        self.volume_speed_wait_counts.clear()
        self.volume_speed_cooldown_until.clear()
        self.last_sell_skip_log_at.clear()
        self.pending_sell_intents.clear()
        self.pending_sell_order_codes.clear()
        self.condition_registered_at.clear()
        self.last_dante_sample_at.clear()
        # 전날 미라벨링된 단테 샘플은 표본 신뢰도가 낮으므로 폐기한다.
        self.pending_dante_samples.clear()
        self.last_dante_shadow_sample_at.clear()
        self.pending_dante_shadow_samples.clear()
        self.monitoring_dict.clear()
        self.dante_a_watchlist.clear()
        self.dante_reentry_watchlist.clear()
        self.risk_too_wide_watchlist.clear()
        logger.info("[일일초기화] {} 매수 후보/대기 상태 초기화".format(today))

    def normalize_code(self, code):
        return code.strip().lstrip("A")

    def _sync_position_from_dicts(self, code):
        """기존 dict 상태로부터 portfolio Position을 재구성/갱신한다.

        아직 portfolio 마이그레이션이 끝나지 않은 write 경로(예: update_account_status에서
        잔고 TR 응답으로 dict를 갱신하는 부분) 직후에 호출해, portfolio가 항상 dict와
        동일한 종목 상태를 갖도록 한다. 모든 read 경로가 portfolio 기반으로 옮겨가면
        이 헬퍼는 필요 없어진다.
        """
        code = self.normalize_code(code)
        if not code:
            return None
        position = self.portfolio.get_or_create(code, name=self.get_code_name(code) or "")
        position.quantity = self.parse_int(self.position_quantities.get(code, 0))
        position.available_quantity = self.parse_int(self.available_quantities.get(code, 0))
        position.entry_price = self.parse_int(self.order_prices.get(code, 0))
        position.target_price = self.parse_int(self.best.get(code, 0))
        target_return = self.target_returns.get(code, 0.0)
        position.target_return = float(target_return) if isinstance(target_return, (int, float)) else 0.0
        entry_time = self.entry_times.get(code, 0.0)
        position.entry_time = float(entry_time) if isinstance(entry_time, (int, float)) else 0.0
        position.highest_price = self.parse_int(self.highest_prices.get(code, 0))
        position.bought_today = code in self.bought_codes
        position.pending_buy = code in self.pending_order_codes and code not in self.pending_sell_order_codes
        position.pending_sell = code in self.pending_sell_order_codes
        position.pending_sell_intent = self.pending_sell_intents.get(code)
        order_context = self.order_context.get(code, {})
        position.order_context = order_context if isinstance(order_context, dict) else {}
        return position

    def _discard_position(self, code, *, save=True, drop_pending_sell=True, persist=True):
        # 종목 청산 시 흩어진 상태 dict/set을 한 번에 정리한다. 한 군데라도 빠지면 정합성이 깨지므로 항상 이 헬퍼를 사용한다.
        code = self.normalize_code(code)
        if not code:
            return
        self.holding_codes.discard(code)
        self.best.pop(code, None)
        self.entry_times.pop(code, None)
        self.order_prices.pop(code, None)
        self.target_returns.pop(code, None)
        self.highest_prices.pop(code, None)
        self.position_quantities.pop(code, None)
        self.available_quantities.pop(code, None)
        self.pending_sell_intents.pop(code, None)
        if drop_pending_sell:
            self.pending_sell_order_codes.discard(code)
        self.order_context.pop(code, None)
        # Portfolio dataclass 마이그레이션: 기존 dict 정리와 동시에 portfolio에서도 제거.
        self.portfolio.remove(code)
        # 단테 전략 캐시도 함께 정리(메모리/오랜 보유 방지).
        self.minute_aggregator.discard(code)
        self.five_min_cache.discard(code)
        if save:
            self.save_best()
        # 청산이 일어난 시점은 portfolio_state.json 도 동기화. 안 하면 다음 부팅 시
        # 이미 청산된 종목이 살아있는 것처럼 복원된다(잔고 TR 로 결국 정정되긴 하나 한 사이클
        # 동안 잘못된 should_skip_buy 결과가 나올 수 있음).
        if persist:
            self.save_portfolio_state()

    def maybe_start_reentry_watch(self, code, position=None, *, exit_price=0, reason=""):
        code = self.normalize_code(code)
        if not code or position is None:
            return
        entry_price = self.parse_int(getattr(position, "entry_price", 0))
        exit_price = self.parse_int(exit_price)
        if entry_price <= 0 or exit_price <= 0:
            return
        gross_profit = exit_price / entry_price - 1
        if gross_profit < exit_strategy.EXIT_BE_R * exit_strategy.R_UNIT_PCT:
            return
        breakout_high = max(
            self.parse_int(getattr(position, "breakout_high", 0)),
            self.parse_int(getattr(position, "highest_price", 0)),
            exit_price,
        )
        now = time.time()
        self.dante_reentry_watchlist[code] = {
            "started_at": now,
            "deadline": now + entry_strategy.REENTRY_WATCH_WINDOW_SECONDS,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "breakout_high": breakout_high,
            "pullback_low": exit_price,
            "reason": reason,
        }
        self.register_realtime_stock(code)
        self.requeue_condition_stock(code)
        logger.info(
            "[re-entry watch start] %s entry=%s exit=%s high=%s profit=%.2f%%",
            code,
            entry_price,
            exit_price,
            breakout_high,
            gross_profit * 100,
        )

    def update_reentry_watch(self, code, close):
        code = self.normalize_code(code)
        watch = self.dante_reentry_watchlist.get(code)
        if watch is None or close <= 0:
            return
        price = int(close)
        watch["breakout_high"] = max(self.parse_int(watch.get("breakout_high", 0)), price)
        low = self.parse_int(watch.get("pullback_low", 0))
        watch["pullback_low"] = price if low <= 0 else min(low, price)

    def save_best(self):
        # 쓰기 도중 종료되어도 best.dat이 깨지지 않도록 임시 파일 → rename 으로 교체
        tmp_path = 'best.dat.tmp'
        try:
            with open(tmp_path, 'wb') as f:
                pickle.dump(self.best, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, 'best.dat')
        except Exception as e:
            logger.error("best.dat 저장 실패: %s", e)
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    def load_best(self):
        try:
            with open('best.dat', 'rb') as f:
                self.best = pickle.load(f)
        except FileNotFoundError:
            self.best = {}
        except Exception as e:
            logger.error("best.dat 로드 실패: %s", e)
            self.best = {}

    def save_portfolio_state(self):
        """장중 크래시 복원용 portfolio JSON 영속화. atomic write 로 부분 쓰기를 방어.

        매 체결/매도 큐 변경/매도 평가 종료 시점마다 호출된다. IO 실패는 main 루프를
        멈추지 않고 로그만 남긴다(거래 자체가 막혀선 안 되므로 best-effort).

        보유/주문 종목이 0 일 때는 디스크 IO 를 스킵한다 -- check_open_positions 의
        1.5초 주기에서 의미 없는 fsync 가 누적되는 것을 방지한다. 잔존 portfolio_state.json
        파일은 그대로 남되, 다음 부팅 시 trading_day 비교로 어차피 폐기되므로 안전.
        """
        if len(self.portfolio) == 0:
            return
        try:
            self.portfolio.save(
                PORTFOLIO_STATE_PATH,
                metadata={
                    "trading_day": self.trading_day,
                    "saved_at": time.time(),
                    "saved_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
        except Exception as exc:
            logger.warning("portfolio_state 저장 실패: %s", exc)

    def load_portfolio_state(self):
        """부팅 시 portfolio JSON 복원. 잔고 TR 호출 전에 실행해야 한다.

        디스크에 저장된 trading_day 가 오늘과 같으면 self.trading_day 도 미리 복원해
        뒤이은 ``reset_daily_state`` 가 cleanup 으로 동작하지 않도록 한다(같은 거래일
        내 재시작 → 어제 매도 의도/매수 한도 카운터 보존). 다른 날이면 metadata 만 읽고
        position 자체는 잔고 TR 로 다시 검증된다.
        """
        loaded: LoadedPortfolioState = PortfolioState.load(PORTFOLIO_STATE_PATH)
        saved_trading_day = str(loaded.metadata.get("trading_day") or "")
        today = time.strftime("%Y-%m-%d")
        # 같은 거래일 내 재시작이 아니면 strategy 상태도 미신뢰 — 잔고 TR 만으로 다시 시작.
        if saved_trading_day and saved_trading_day != today:
            logger.info(
                "[portfolio_state] saved_trading_day=%s != today=%s -- 어제 상태 폐기, "
                "잔고 TR 로 재구성합니다.",
                saved_trading_day, today,
            )
            return

        if len(loaded.state) == 0:
            return

        self.portfolio = loaded.state
        if saved_trading_day:
            self.trading_day = saved_trading_day

        # 흩어진 dict 들도 portfolio 의 최근 값과 일치하도록 채워넣는다.
        # (update_account_status 가 잔고 TR 응답으로 다시 갱신하지만, 그 사이의 매도 의도/
        # 매수 한도 카운터 같은 휘발성이 아닌 메타는 _sync_position_from_dicts 가
        # 의존하기 때문에 미리 dict 에 깔아두어야 잔고 TR 동기화 후에도 보존된다.)
        for code, position in self.portfolio.items():
            if position.bought_today:
                self.bought_codes.add(code)
            if position.entry_time:
                self.entry_times[code] = position.entry_time
            if position.highest_price:
                self.highest_prices[code] = position.highest_price
            if position.target_price:
                self.best.setdefault(code, position.target_price)
            if position.target_return:
                self.target_returns[code] = position.target_return
            if position.pending_sell_intent:
                self.pending_sell_intents[code] = dict(position.pending_sell_intent)
            if position.order_context:
                self.order_context[code] = dict(position.order_context)

        logger.info(
            "[portfolio_state] %d 종목 복원 (saved=%s) -- entry_stage/stop_price/"
            "planned_quantity 등 전략 상태 보존",
            len(self.portfolio),
            loaded.metadata.get("saved_time", "?"),
        )

    def update_account_status(self, force=False):
        now = time.time()
        if not force and now - self.account_updated_at < ACCOUNT_CACHE_SECONDS:
            return

        holding_codes = set()
        new_pending = set()
        balance_ok = False
        order_ok = False

        try:
            for balance in self.get_balance(force=True):
                code = self.normalize_code(balance[0])
                if not code:
                    continue
                holding_codes.add(code)
                self.position_quantities[code] = self.parse_int(balance[2])
                self.order_prices[code] = self.parse_int(balance[3])
            # chejan으로 이미 보유 처리된 종목이 잔고 TR에 아직 반영되지 않은 경우(방금 체결)
            # 합집합으로 병합해 잠깐 사라지는 현상을 방지한다.
            self.holding_codes = holding_codes | self.holding_codes
            balance_ok = True
        except Exception as e:
            logger.error("잔고 조회 실패: %s", e)

        try:
            for order in self.get_order(force=True):
                code = self.normalize_code(order[0])
                left_quantity = order[8]
                if left_quantity > 0:
                    new_pending.add(code)
            # 방금 보낸 주문이 TR 응답에 아직 반영되지 않은 경우만 짧게 보존한다.
            # 유예시간 이후에도 계좌 미체결에 없으면 로컬 유령 주문이므로 슬롯을 해제한다.
            previous_pending = set(self.pending_order_codes)
            keep_local_pending = set()
            stale_local_pending = []
            for code in previous_pending - new_pending:
                ctx = self.order_context.get(code, {})
                side = ctx.get("side", "") if isinstance(ctx, dict) else ""
                placed_at = float(ctx.get("placed_at", 0) or 0) if isinstance(ctx, dict) else 0.0
                is_recent = placed_at > 0 and now - placed_at < LOCAL_PENDING_ORDER_GRACE_SECONDS
                if is_recent:
                    keep_local_pending.add(code)
                    continue
                if side == "buy" and code not in holding_codes:
                    stale_local_pending.append(code)
            self.pending_order_codes = new_pending | keep_local_pending
            for code in stale_local_pending:
                logger.warning(
                    "[미체결 정리] %s 계좌 미체결 없음 -- 로컬 매수 pending 해제",
                    code,
                )
                self.pending_order_codes.discard(code)
                self.bought_codes.discard(code)
                self._discard_position(code, save=False, persist=False)
            if stale_local_pending:
                self.save_best()
                self.save_portfolio_state()
            order_ok = True
        except Exception as e:
            logger.error("미체결 조회 실패: %s", e)

        if balance_ok:
            for code in list(self.position_quantities.keys()):
                if code not in self.holding_codes and code not in self.pending_order_codes:
                    self.position_quantities.pop(code, None)
                    self.available_quantities.pop(code, None)

        if balance_ok and order_ok:
            self.account_updated_at = time.time()

        # Portfolio dataclass 마이그레이션: dict 갱신 직후 portfolio도 동기화한다.
        # dict에서 사라진 종목은 portfolio에서도 제거되고, 살아 있는 종목은 최신 정보로 갱신된다.
        if balance_ok or order_ok:
            tracked_codes = self.holding_codes | self.pending_order_codes
            for code in tracked_codes:
                self._sync_position_from_dicts(code)
            for stale_code in list(self.portfolio.codes() - tracked_codes - set(self.best.keys())):
                self.portfolio.remove(stale_code)

    def should_skip_buy(self, code, *, stage=1, grade=""):
        """매수를 건너뛰어야 하는지 판단.

        stage:
          1 = A급 0봉 돌파 감시 시작(매수 없음)
          2 = 본진입 — A급/B급 첫 눌림 100% 본진입
        grade:
          "A" 또는 "B". B급 stage=2 는 신규 종목에서 한 번에 매수하므로 Position 미존재가 정상.
        """
        position = self.portfolio.get(code)
        if stage == 2:
            # B급 일괄 매수: position 미존재가 정상.
            if grade in ("A", "B", "AI", "SAFE") and (position is None or position.entry_stage == 0):
                if position is not None and position.is_holding():
                    logger.info("[매수 제외] {} 이미 보유 중".format(code))
                    return True
                if position is not None and position.entry_stage >= 2:
                    logger.info("[B급 매수 제외] {} 이미 본진입 완료".format(code))
                    return True
                if position is not None and position.pending_sell:
                    logger.info("[B급 매수 제외] {} 매도 진행 중".format(code))
                    return True
                # 신규 종목으로 취급 — 동시보유/일일한도 게이트는 stage=1 분기와 동일하게 적용.
                position_count = (
                    len(self.portfolio.holding_codes())
                    + len(self.portfolio.pending_order_codes())
                )
                if position_count >= MAX_CONCURRENT_POSITIONS:
                    logger.info("[B급 매수 제외] 최대 보유/주문 종목 수 도달: {}".format(MAX_CONCURRENT_POSITIONS))
                    return True
                if len(self.portfolio.bought_today_codes()) >= MAX_DAILY_BUY_COUNT:
                    logger.info("[B급 매수 제외] 일일 매수 횟수 한도 도달: {}".format(MAX_DAILY_BUY_COUNT))
                    return True
                return False
            # A급 본진입: 1차 보유/미체결 상태가 정상.
            if position is None:
                logger.info("[2차 매수 제외] {} 1차 Position 없음".format(code))
                return True
            if position.entry_stage >= 2:
                logger.info("[2차 매수 제외] {} 본진입 완료".format(code))
                return True
            if position.pending_sell:
                logger.info("[2차 매수 제외] {} 매도 진행 중".format(code))
                return True
            return False

        if position is not None:
            if position.is_holding() or position.entry_stage >= 1:
                logger.info("[매수 제외] {} 이미 보유 중".format(code))
                return True
            if position.is_pending():
                logger.info("[매수 제외] {} 미체결 주문 존재".format(code))
                return True
            if position.bought_today:
                logger.info("[매수 제외] {} 오늘 이미 매수 주문 처리".format(code))
                return True
        position_count = len(self.portfolio.holding_codes()) + len(self.portfolio.pending_order_codes())
        if position_count >= MAX_CONCURRENT_POSITIONS:
            logger.info("[매수 제외] 최대 보유/주문 종목 수 도달: {}".format(MAX_CONCURRENT_POSITIONS))
            return True
        if len(self.portfolio.bought_today_codes()) >= MAX_DAILY_BUY_COUNT:
            logger.info("[매수 제외] 일일 매수 횟수 한도 도달: {}".format(MAX_DAILY_BUY_COUNT))
            return True
        return False

    def current_hhmmss(self):
        return int(time.strftime("%H%M%S"))

    def is_opening_buy_time(self):
        now = self.current_hhmmss()
        return OPENING_BUY_START <= now <= OPENING_BUY_END

    def realtime_daily_turnover(self, code, *, current_price=0, accum_volume=0):
        code = self.normalize_code(code)
        price = self.parse_int(current_price)
        volume = self.parse_int(accum_volume)
        if (price <= 0 or volume <= 0) and code in self.realtime_ticks:
            ticks = self.realtime_ticks.get(code, [])
            if ticks:
                last = ticks[-1]
                price = price if price > 0 else self.parse_int(last.get("close", 0))
                volume = volume if volume > 0 else self.parse_int(last.get("accum_volume", 0))
        if price <= 0 or volume <= 0:
            return 0
        return price * volume

    def realtime_turnover_rank(self, code, *, current_turnover=0):
        code = self.normalize_code(code)
        turnovers = {}
        for tracked_code, ticks in self.realtime_ticks.items():
            if not ticks:
                continue
            last = ticks[-1]
            turnover = self.realtime_daily_turnover(
                tracked_code,
                current_price=last.get("close", 0),
                accum_volume=last.get("accum_volume", 0),
            )
            if turnover > 0:
                turnovers[self.normalize_code(tracked_code)] = turnover
        if current_turnover > 0:
            turnovers[code] = max(self.parse_int(current_turnover), turnovers.get(code, 0))
        if not turnovers or code not in turnovers:
            return 0, len(turnovers)
        rank = 1 + sum(1 for turnover in turnovers.values() if turnover > turnovers[code])
        return rank, len(turnovers)

    def evaluate_time_filter(self, code, *, current_price=0, accum_volume=0):
        now = self.current_hhmmss()
        if now < TIME_FILTER_MORNING_START:
            return {
                "ok": False,
                "status": "wait",
                "reason": "TimeFilter: 매수 시작 전",
                "phase": "preopen",
            }
        if now >= TIME_FILTER_CLOSING_END:
            return {
                "ok": False,
                "status": "blocked",
                "reason": "TimeFilter: 15:20 이후 신규 매수 금지",
                "phase": "closed",
            }

        daily_turnover = self.realtime_daily_turnover(
            code,
            current_price=current_price,
            accum_volume=accum_volume,
        )
        if now < TIME_FILTER_MORNING_END:
            return {
                "ok": True,
                "phase": "morning",
                "weight": 1.2,
                "reason": "TimeFilter morning: 조건식 거래대금 필터 신뢰, 적극 매매 구간",
                "daily_turnover": daily_turnover,
            }

        if now < TIME_FILTER_MIDDAY_END:
            return {
                "ok": False,
                "status": "blocked",
                "reason": "TimeFilter midday: 10:00~14:00 횡보장 구간 신규 매수 금지",
                "phase": "midday",
                "daily_turnover": daily_turnover,
            }

        rank, ranked_count = self.realtime_turnover_rank(code, current_turnover=daily_turnover)
        if daily_turnover < TIME_FILTER_CLOSING_MIN_TURNOVER:
            return {
                "ok": False,
                "status": "wait",
                "reason": "TimeFilter closing: 누적 거래대금 {:.1f}억 < {:.1f}억".format(
                    daily_turnover / 100_000_000,
                    TIME_FILTER_CLOSING_MIN_TURNOVER / 100_000_000,
                ),
                "phase": "closing",
                "daily_turnover": daily_turnover,
                "turnover_rank": rank,
                "ranked_count": ranked_count,
            }
        if rank <= 0 or rank > TIME_FILTER_CLOSING_TOP_RANK:
            return {
                "ok": False,
                "status": "blocked",
                "reason": "TimeFilter closing: 거래대금 순위 {}/{} > Top{}".format(
                    rank,
                    ranked_count,
                    TIME_FILTER_CLOSING_TOP_RANK,
                ),
                "phase": "closing",
                "daily_turnover": daily_turnover,
                "turnover_rank": rank,
                "ranked_count": ranked_count,
            }
        return {
            "ok": True,
            "phase": "closing",
            "weight": 0.8,
            "reason": "TimeFilter closing: 거래대금 Top{} 종목".format(rank),
            "daily_turnover": daily_turnover,
            "turnover_rank": rank,
            "ranked_count": ranked_count,
        }

    def clamp(self, value, low=0.0, high=1.0):
        return max(low, min(high, value))

    def gross_to_net_return(self, gross_return):
        gross_return = self.parse_float(gross_return, 0.0)
        return gross_return - ESTIMATED_ROUND_TRIP_COST_RATE

    def net_to_gross_return(self, net_return):
        net_return = self.parse_float(net_return, 0.0)
        return net_return + ESTIMATED_ROUND_TRIP_COST_RATE

    def compute_target_price_for_net_return(self, entry_price, net_target_return):
        gross_target_return = self.net_to_gross_return(net_target_return)
        return self.compute_target_price(entry_price, gross_target_return)

    def estimate_net_target_return(self, entry_price, target_price):
        gross_target_return = self.estimate_target_return(entry_price, target_price)
        return self.gross_to_net_return(gross_target_return)

    def compute_target_price(self, entry_price, target_return):
        entry_price = self.parse_int(entry_price)
        if entry_price <= 0:
            return 0
        raw = entry_price * (1 + target_return)
        rounded = scoring.round_up_to_tick(raw)
        # 진입가와 같거나 더 낮아지는 경우(매우 작은/음수 target_return)는 최소 1틱 위로 올린다.
        if rounded <= entry_price:
            rounded = entry_price + scoring.tick_size(entry_price)
        return rounded

    def estimate_target_return(self, entry_price, target_price):
        entry_price = self.parse_int(entry_price)
        target_price = self.parse_int(target_price)
        if entry_price <= 0 or target_price <= 0:
            return 0.0
        return target_price / entry_price - 1

    def has_consecutive_down_ticks(self, code, required_count=3):
        code = self.normalize_code(code)
        ticks = self.realtime_ticks.get(code, [])
        if len(ticks) < required_count + 1:
            return False
        recent = ticks[-(required_count + 1):]
        down_count = 0
        for prev, cur in zip(recent, recent[1:]):
            if cur["close"] < prev["close"]:
                down_count += 1
        return down_count >= required_count

    def should_log_sell_skip(self, code):
        now = time.time()
        last_at = self.last_sell_skip_log_at.get(code, 0)
        if now - last_at < SELL_SKIP_LOG_COOLDOWN_SECONDS:
            return False
        self.last_sell_skip_log_at[code] = now
        return True

    def queue_sell_intent(self, code, reason, order_price=0, order_gubun="03"):
        code = self.normalize_code(code)
        if not code:
            return
        existing = self.pending_sell_intents.get(code, {})
        intent = {
            "reason": reason,
            "order_price": order_price,
            "order_gubun": order_gubun,
            "queued_at": existing.get("queued_at", time.time()),
            "last_try_at": existing.get("last_try_at", 0),
        }
        self.pending_sell_intents[code] = intent
        # Position 의 pending_sell_intent 도 같이 갱신해 portfolio_state.json 에 보존되게 한다.
        # 크래시 후 재시작해도 큐가 사라지지 않아 매도 재시도가 자동으로 재개된다.
        position = self.portfolio.get(code)
        if position is not None:
            position.pending_sell_intent = dict(intent)
            self.save_portfolio_state()

    def process_pending_sell_intents(self, target_codes=None):
        if target_codes is None:
            codes = list(self.pending_sell_intents.keys())
        else:
            codes = [self.normalize_code(code) for code in target_codes]
        if not codes:
            return
        now = time.time()
        for code in codes:
            intent = self.pending_sell_intents.get(code)
            if intent is None:
                continue
            if code in self.pending_sell_order_codes or code in self.pending_order_codes:
                continue
            last_try = intent.get("last_try_at", 0)
            if now - last_try < SELL_INTENT_RETRY_SECONDS:
                continue
            _, available_quantity = self._lookup_balance_quantity(code)
            if self.parse_int(available_quantity) <= 0:
                continue
            intent["last_try_at"] = now
            self.place_sell_order(
                code,
                intent.get("order_price", 0),
                intent.get("order_gubun", "03"),
                intent.get("reason", "매도 의도 재시도"),
            )

    def requeue_condition_stock(self, code):
        code = self.normalize_code(code)
        if code in self.no_tick_codes:
            return
        if code not in self.pending_condition_codes:
            self.pending_condition_codes.append(code)

    def ensure_monitoring_stock(self, code, *, capture_price=0):
        code = self.normalize_code(code)
        watch = self.monitoring_dict.get(code)
        if watch is None:
            now = time.time()
            capture = self.parse_int(capture_price)
            watch = {
                "capture_price": capture,
                "status": "WATCHING",
                "detected_at": now,
                "ready_at": 0.0,
                "target_price": scoring.round_down_to_tick(
                    capture * (1 - SAFE_PULLBACK_MIN_DROP_PCT)
                ) if capture > 0 else 0,
                "capture_accum_volume": 0,
                "ready_accum_volume": 0,
                "breakout_volume": 0,
                "big_buy_seen": False,
                "big_buy_qty": 0,
                "last_price": 0,
                "last_reason": "",
                "condition_name": CONDITION_NAME,
                "condition_formula": TRADE_LOG_CONDITION_FORMULA,
                "rule_version": TRADE_LOG_RULE_VERSION,
            }
            self.monitoring_dict[code] = watch
            logger.info(
                "[퀀트조건식 감시 등록] %s capture=%s target=%s status=WATCHING",
                code,
                watch["capture_price"],
                watch["target_price"],
            )
        elif capture_price and self.parse_int(watch.get("capture_price", 0)) <= 0:
            watch["capture_price"] = self.parse_int(capture_price)
            watch["target_price"] = scoring.round_down_to_tick(
                self.parse_int(capture_price) * (1 - SAFE_PULLBACK_MIN_DROP_PCT)
            )
            logger.info("[포착가 저장] %s capture=%s", code, watch["capture_price"])
        return watch

    def clear_monitoring_stock(self, code, reason=""):
        code = self.normalize_code(code)
        watch = self.monitoring_dict.pop(code, None)
        if watch is not None:
            logger.info("[감시 해제] %s %s", code, reason)

    def monitoring_volume_5m(self, code):
        bars = self.minute_aggregator.all_bars(code)
        if not bars:
            return 0
        return sum(max(self.parse_int(getattr(bar, "volume", 0)), 0) for bar in bars[-5:])

    def update_orderbook_snapshot(self, code):
        code = self.normalize_code(code)
        ask_total = self.get_real_int(code, "매도호가 총잔량")
        bid_total = self.get_real_int(code, "매수호가 총잔량")
        if ask_total <= 0:
            ask_total = sum(self.get_real_int(code, "매도호가 수량{}".format(i)) for i in range(1, 11))
        if bid_total <= 0:
            bid_total = sum(self.get_real_int(code, "매수호가 수량{}".format(i)) for i in range(1, 11))
        if ask_total <= 0 and bid_total <= 0:
            return self.orderbook_snapshots.get(code, {})
        snapshot = {
            "ask_total": ask_total,
            "bid_total": bid_total,
            "ask_bid_ratio": (ask_total / bid_total) if bid_total > 0 else 0.0,
            "updated_at": time.time(),
        }
        self.orderbook_snapshots[code] = snapshot
        return snapshot

    def orderbook_wall_confirmed(self, code):
        snapshot = self.update_orderbook_snapshot(code)
        ask_total = self.parse_int(snapshot.get("ask_total", 0))
        bid_total = self.parse_int(snapshot.get("bid_total", 0))
        if ask_total <= 0 or bid_total <= 0:
            return False, "호가 총잔량 대기"
        ratio = ask_total / bid_total
        if ratio <= SAFE_PULLBACK_ASK_BID_RATIO_MIN:
            return False, "매도잔량/매수잔량 {:.2f} <= {:.1f}".format(
                ratio, SAFE_PULLBACK_ASK_BID_RATIO_MIN
            )
        return True, "매도잔량 우위 {:.2f}배".format(ratio)

    def is_big_buyer_tick(self, code, tick):
        volume_delta = self.parse_int(tick.get("volume_delta", 0))
        if volume_delta < SAFE_PULLBACK_BIG_BUY_MIN_QTY:
            return False
        if self.parse_float(tick.get("chejan_strength", 0.0), 0.0) < 100.0:
            return False
        ticks = self.realtime_ticks.get(code, [])
        if len(ticks) >= 2 and self.parse_int(tick.get("close", 0)) < self.parse_int(ticks[-2].get("close", 0)):
            return False
        recent = [
            self.parse_int(t.get("volume_delta", 0))
            for t in ticks[-10:-1]
            if self.parse_int(t.get("volume_delta", 0)) > 0
        ]
        avg_delta = (sum(recent) / len(recent)) if recent else SAFE_PULLBACK_BIG_BUY_MIN_QTY
        return volume_delta >= max(SAFE_PULLBACK_BIG_BUY_MIN_QTY, avg_delta * SAFE_PULLBACK_BIG_BUY_MULT)

    def recent_big_buyer_confirmed(self, code, *, lookback=5):
        ticks = self.realtime_ticks.get(code, [])
        if not ticks:
            return False, "빅바이어 체결 대기"
        recent = ticks[-lookback:]
        best = 0
        for tick in recent:
            volume_delta = self.parse_int(tick.get("volume_delta", 0))
            best = max(best, volume_delta)
            if self.is_big_buyer_tick(code, tick):
                return True, "빅바이어 재확인 {}주".format(volume_delta)
        return False, "빅바이어 부족 max={}주".format(best)

    def second_entry_orderbook_confirmed(self, code):
        snapshot = self.update_orderbook_snapshot(code)
        ask_total = self.parse_int(snapshot.get("ask_total", 0))
        bid_total = self.parse_int(snapshot.get("bid_total", 0))
        if ask_total <= 0 or bid_total <= 0:
            return False, "호가 총잔량 대기"
        ratio = ask_total / bid_total
        if ratio > SAFE_PULLBACK_ASK_BID_RATIO_MIN:
            return True, "매도벽 유지 {:.2f}배".format(ratio)
        if bid_total >= ask_total:
            return True, "매도벽 흡수 bid/ask {:.2f}".format(bid_total / ask_total if ask_total > 0 else 0)
        return False, "호가 흡수 미확인 ask/bid {:.2f}".format(ratio)

    def update_monitoring_tick(self, code, tick):
        code = self.normalize_code(code)
        watch = self.monitoring_dict.get(code)
        if watch is None:
            return
        close = self.parse_int(tick.get("close", 0))
        if close <= 0:
            return
        accum_volume = self.parse_int(tick.get("accum_volume", 0))
        watch["last_price"] = close
        if self.parse_int(watch.get("capture_price", 0)) <= 0:
            watch["capture_price"] = close
            watch["target_price"] = self.quant_strategy.trigger_price(close)
            watch["capture_accum_volume"] = accum_volume
            watch["breakout_volume"] = max(self.monitoring_volume_5m(code), 0)
            try:
                self.condition_capture_logger.append_capture_price(
                    code=code,
                    name=self.get_code_name(code),
                    condition_name=watch.get("condition_name", CONDITION_NAME),
                    condition_index=watch.get("condition_index", ""),
                    event_type=watch.get("condition_event_type", ""),
                    screen_no=self.realtime_code_screens.get(code, REALTIME_SCREEN_NO),
                    capture_price=close,
                    entry_trigger_price=watch["target_price"],
                    chejan_strength=self.parse_float(tick.get("chejan_strength", 0.0), 0.0),
                    accum_volume=accum_volume,
                )
            except Exception as exc:
                logger.warning("[조건검색 포착가 로그 실패] %s %s", code, exc)
            logger.info(
                "[퀀트조건식 포착가 저장] %s capture=%s entry_trigger=%s(-%.2f%%) strength_min=%.0f",
                code,
                close,
                watch["target_price"],
                QUANT_ENTRY_PULLBACK_PCT * 100,
                QUANT_ENTRY_CHEJAN_STRENGTH_MIN,
            )
            return

        capture_price = self.parse_int(watch.get("capture_price", 0))
        if capture_price <= 0:
            return
        pullback = (capture_price - close) / capture_price
        if watch.get("status") == "WATCHING" and pullback < SAFE_PULLBACK_MIN_DROP_PCT:
            volume_5m = self.monitoring_volume_5m(code)
            accum_delta = max(accum_volume - self.parse_int(watch.get("capture_accum_volume", 0)), 0)
            watch["breakout_volume"] = max(
                self.parse_int(watch.get("breakout_volume", 0)),
                volume_5m,
                accum_delta,
            )
        if self.is_big_buyer_tick(code, tick):
            volume_delta = self.parse_int(tick.get("volume_delta", 0))
            watch["big_buy_seen"] = True
            watch["big_buy_qty"] = max(self.parse_int(watch.get("big_buy_qty", 0)), volume_delta)

    def market_filter_pauses_buy(self):
        snapshot = self.market_state.snapshot()
        slope_1m = getattr(snapshot, "market_slope_1m", None)
        slope_3m = getattr(snapshot, "market_slope_3m", None)
        regime = getattr(snapshot, "market_regime", "") or ""
        if regime in ("weak", "risk_off"):
            return True, "지수 하락 regime={}".format(regime)
        if slope_1m is not None and slope_1m < 0:
            return True, "지수 1분봉 하락 slope={:.2%}".format(slope_1m)
        if slope_3m is not None and slope_3m < 0:
            return True, "지수 3분 추세 하락 slope={:.2%}".format(slope_3m)
        return False, ""

    def support_confirmed_for_safe_pullback(self, code):
        ind = self.five_min_cache.get(code)
        if ind is not None:
            cur_open = getattr(ind, "cur_open", None)
            cur_close = getattr(ind, "last_close", None)
            if cur_open and cur_close and cur_close > cur_open:
                return True, "5분봉 양봉"
            cur_low = getattr(ind, "cur_low", None)
            prev_low = getattr(ind, "prev_low", None)
            prev_close = getattr(ind, "prev_close", None)
            if cur_low and prev_low and cur_close and prev_close and cur_low >= prev_low and cur_close >= prev_close:
                return True, "5분봉 하락세 둔화"

        bars = self.minute_aggregator.all_bars(code)
        if len(bars) >= 3:
            recent = bars[-3:]
            if recent[-1].close >= recent[-2].close and recent[-1].low >= min(b.low for b in recent[:-1]):
                return True, "1분봉 저점 방어"
        return False, "지지 확인 전"

    def active_position_count(self):
        return len(self.portfolio.holding_codes()) + len(self.portfolio.pending_order_codes())

    def score_safe_pullback_trade(self, code):
        code = self.normalize_code(code)
        watch = self.ensure_monitoring_stock(code)
        ticks = self.realtime_ticks.get(code, [])
        if not ticks:
            return {"status": "wait", "stage": 2, "reason": "실시간 첫 틱 대기", "reason_code": "SAFE_WAIT_TICK"}

        tick = ticks[-1]
        current_price = self.parse_int(tick.get("close", 0))
        if current_price <= 0:
            return {"status": "wait", "stage": 2, "reason": "현재가 없음", "reason_code": "SAFE_NO_PRICE"}

        time_filter = self.evaluate_time_filter(
            code,
            current_price=current_price,
            accum_volume=tick.get("accum_volume", 0),
        )
        if not time_filter.get("ok"):
            return {
                "status": time_filter.get("status", "blocked"),
                "stage": 2,
                "code": code,
                "name": self.get_code_name(code),
                "current_price": current_price,
                "ratio": 0.0,
                "reason": time_filter.get("reason", "TimeFilter block"),
                "reason_code": "TIME_FILTER",
                "time_filter_phase": time_filter.get("phase", ""),
                "time_filter_weight": time_filter.get("weight", 0.0),
                "daily_turnover": time_filter.get("daily_turnover", 0),
                "turnover_rank": time_filter.get("turnover_rank", 0),
                "ranked_count": time_filter.get("ranked_count", 0),
            }

        self.update_monitoring_tick(code, tick)
        capture_price = self.parse_int(watch.get("capture_price", 0))
        if capture_price <= 0:
            return {"status": "wait", "stage": 2, "reason": "포착가 저장 대기", "reason_code": "SAFE_NO_CAPTURE"}

        name = self.get_code_name(code)
        chejan_strength = self.parse_float(tick.get("chejan_strength", 0.0), 0.0)
        target_price = self.parse_int(watch.get("target_price", 0))
        if target_price <= 0:
            target_price = self.quant_strategy.trigger_price(capture_price)
            watch["target_price"] = target_price
        recent_low_price = self.parse_int(watch.get("recent_low_price", capture_price))
        if recent_low_price <= 0:
            recent_low_price = capture_price
        recent_low_price = min(recent_low_price, current_price)
        watch["recent_low_price"] = recent_low_price
        market_snapshot = self.market_state.snapshot()
        market_regime = getattr(market_snapshot, "market_regime", "") or "neutral"

        entry_decision = self.quant_strategy.evaluate_entry(
            capture_price=capture_price,
            current_price=current_price,
            chejan_strength=chejan_strength,
            active_positions=self.active_position_count(),
            recent_low_price=recent_low_price,
            market_state=market_regime,
        )
        if entry_decision.status != "ready":
            watch["status"] = "WATCHING"
            return entry_decision.to_prediction(
                code=code,
                name=name,
                config=QUANT_STRATEGY_CONFIG,
            )

        if watch.get("status") != "READY":
            watch["status"] = "READY"
            watch["ready_at"] = time.time()
            watch["ready_accum_volume"] = self.parse_int(tick.get("accum_volume", 0))
            logger.info(
                "[퀀트조건식 매수 준비] %s capture=%s current=%s pullback=%.2f%% strength=%.1f",
                code,
                capture_price,
                current_price,
                entry_decision.pullback_pct * 100,
                chejan_strength,
            )

        return entry_decision.to_prediction(
            code=code,
            name=name,
            config=QUANT_STRATEGY_CONFIG,
            extra={
                "safe_target_price": target_price,
                "daily_turnover": time_filter.get("daily_turnover", 0),
                "turnover_rank": time_filter.get("turnover_rank", 0),
                "ranked_count": time_filter.get("ranked_count", 0),
                "time_filter_phase": time_filter.get("phase", ""),
                "time_filter_weight": time_filter.get("weight", 1.0),
            },
        )

    def score_safe_pullback_second_entry(self, code, position):
        code = self.normalize_code(code)
        ticks = self.realtime_ticks.get(code, [])
        if not ticks:
            return {"status": "wait", "stage": 2, "reason": "SAFE 2차 실시간 틱 대기", "reason_code": "SAFE_SECOND_WAIT_TICK"}

        current_price = self.parse_int(ticks[-1].get("close", 0))
        if current_price <= 0:
            return {"status": "wait", "stage": 2, "reason": "SAFE 2차 현재가 없음", "reason_code": "SAFE_SECOND_NO_PRICE"}

        time_filter = self.evaluate_time_filter(
            code,
            current_price=current_price,
            accum_volume=ticks[-1].get("accum_volume", 0),
        )
        if not time_filter.get("ok"):
            return {
                "status": time_filter.get("status", "blocked"),
                "stage": 2,
                "code": code,
                "name": getattr(position, "name", "") or self.get_code_name(code),
                "current_price": current_price,
                "ratio": 0.0,
                "reason": time_filter.get("reason", "TimeFilter block"),
                "reason_code": "TIME_FILTER",
                "time_filter_phase": time_filter.get("phase", ""),
                "time_filter_weight": time_filter.get("weight", 0.0),
                "daily_turnover": time_filter.get("daily_turnover", 0),
                "turnover_rank": time_filter.get("turnover_rank", 0),
                "ranked_count": time_filter.get("ranked_count", 0),
            }

        planned_quantity = self.parse_int(getattr(position, "planned_quantity", 0))
        held_quantity = self.parse_int(getattr(position, "quantity", 0))
        remaining = max(planned_quantity - held_quantity, 0)
        if planned_quantity <= 0 or remaining <= 0:
            return {
                "status": "blocked",
                "stage": 2,
                "reason": "SAFE 2차 잔여수량 없음 planned={} held={}".format(planned_quantity, held_quantity),
                "reason_code": "SAFE_SECOND_NO_REMAINING",
            }

        now_ts = time.time()
        entry1_time = float(getattr(position, "entry1_time", 0.0) or getattr(position, "entry_time", 0.0) or now_ts)
        if now_ts - entry1_time > SAFE_PULLBACK_SECOND_WINDOW_SECONDS:
            return {
                "status": "blocked",
                "stage": 2,
                "reason": "SAFE 2차 윈도우 만료 {:.0f}s".format(now_ts - entry1_time),
                "reason_code": "SAFE_SECOND_WINDOW_EXPIRED",
            }

        base_price = self.parse_int(getattr(position, "entry_price", 0))
        if base_price <= 0 and isinstance(getattr(position, "order_context", None), dict):
            base_price = self.parse_int(position.order_context.get("entry_limit_price", 0))
        if base_price <= 0:
            return {"status": "wait", "stage": 2, "reason": "SAFE 2차 기준가 없음", "reason_code": "SAFE_SECOND_NO_BASE"}

        rebound_pct = current_price / base_price - 1
        if rebound_pct < SAFE_PULLBACK_SECOND_MIN_REBOUND_PCT:
            return {
                "status": "wait",
                "stage": 2,
                "reason": "SAFE 2차 반등 부족 {:.2%} < {:.2%}".format(
                    rebound_pct, SAFE_PULLBACK_SECOND_MIN_REBOUND_PCT
                ),
                "reason_code": "SAFE_SECOND_REBOUND_WAIT",
            }
        if rebound_pct > SAFE_PULLBACK_SECOND_MAX_CHASE_PCT:
            return {
                "status": "wait",
                "stage": 2,
                "reason": "SAFE 2차 추격 방지 {:.2%} > {:.2%}".format(
                    rebound_pct, SAFE_PULLBACK_SECOND_MAX_CHASE_PCT
                ),
                "reason_code": "SAFE_SECOND_CHASE_WAIT",
            }

        self.refresh_five_min_indicators(code)
        support_ok, support_reason = self.support_confirmed_for_safe_pullback(code)
        if not support_ok:
            return {"status": "wait", "stage": 2, "reason": "SAFE 2차 {}".format(support_reason), "reason_code": "SAFE_SECOND_SUPPORT_WAIT"}

        orderbook_ok, orderbook_reason = self.second_entry_orderbook_confirmed(code)
        if not orderbook_ok:
            return {"status": "wait", "stage": 2, "reason": "SAFE 2차 {}".format(orderbook_reason), "reason_code": "SAFE_SECOND_ORDERBOOK_WAIT"}

        big_ok, big_reason = self.recent_big_buyer_confirmed(code)
        if not big_ok:
            return {"status": "wait", "stage": 2, "reason": "SAFE 2차 {}".format(big_reason), "reason_code": "SAFE_SECOND_BIG_BUY_WAIT"}

        paused, market_reason = self.market_filter_pauses_buy()
        if paused:
            return {"status": "wait", "stage": 2, "reason": market_reason, "reason_code": "SAFE_SECOND_MARKET_PAUSE"}

        entry_limit_price = scoring.round_down_to_tick(current_price)
        stop_price = scoring.round_down_to_tick(entry_limit_price * (1 - SAFE_PULLBACK_STOP_LOSS_PCT))
        take_profit_price = scoring.round_up_to_tick(entry_limit_price * (1 + SAFE_PULLBACK_TAKE_PROFIT_PCT))
        return {
            "status": "ready",
            "code": code,
            "name": getattr(position, "name", "") or self.get_code_name(code),
            "current_price": current_price,
            "ratio": 1.0,
            "stage": 2,
            "score": 1.0,
            "grade": "SAFE",
            "reason": "SAFE 2차: {} + {} + {}, rebound {:.2%}".format(
                support_reason, orderbook_reason, big_reason, rebound_pct
            ),
            "reason_code": "SAFE_SECOND_READY",
            "entry_limit_price": entry_limit_price,
            "stop_price": stop_price,
            "take_profit_price": take_profit_price,
            "order_gubun": "00",
            "plan_source": "safe_pullback",
            "entry_plan_reason": "SAFE 2차 지지/흡수 확인 지정가 매수",
            "chejan_strength": self.parse_float(ticks[-1].get("chejan_strength", 0.0), 0.0),
            "volume_speed": 0.0,
            "spread_rate": 0.0,
            "daily_turnover": time_filter.get("daily_turnover", 0),
            "turnover_rank": time_filter.get("turnover_rank", 0),
            "ranked_count": time_filter.get("ranked_count", 0),
            "time_filter_phase": time_filter.get("phase", ""),
            "time_filter_weight": time_filter.get("weight", 1.0),
        }

    def should_print_wait_log(self, code):
        now = time.time()
        last_at = self.last_wait_log_at.get(code, 0)
        if now - last_at < WAIT_LOG_COOLDOWN_SECONDS:
            return False
        self.last_wait_log_at[code] = now
        return True

    def is_volume_speed_cooling_down(self, code):
        until = float(self.volume_speed_cooldown_until.get(code, 0) or 0)
        if until <= 0:
            return False
        if time.time() >= until:
            self.volume_speed_cooldown_until.pop(code, None)
            self.volume_speed_wait_counts.pop(code, None)
            return False
        return True

    def record_volume_speed_wait(self, code, volume_speed, turnover_speed_per_min=0.0):
        count = self.volume_speed_wait_counts.get(code, 0) + 1
        self.volume_speed_wait_counts[code] = count
        if count < VOLUME_SPEED_COOLDOWN_TRIGGER:
            return False
        cooldown_until = time.time() + VOLUME_SPEED_COOLDOWN_SECONDS
        self.volume_speed_cooldown_until[code] = cooldown_until
        self.volume_speed_wait_counts[code] = 0
        logger.info(
            "[거래대금속도 쿨다운] %s %.1f백만원/분 < %.1f백만원/분 (%.0f주/초) %d회 반복 -- %d초 대기",
            code,
            turnover_speed_per_min / 1_000_000,
            entry_strategy.MIN_TURNOVER_SPEED_PER_MIN / 1_000_000,
            volume_speed,
            VOLUME_SPEED_COOLDOWN_TRIGGER,
            VOLUME_SPEED_COOLDOWN_SECONDS,
        )
        return True

    def call_ai_server(self, endpoint, payload):
        if not AI_SERVER_ENABLED:
            return None
        now = time.time()
        if now < self.ai_server_cooldown_until:
            return None
        try:
            body = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                AI_SERVER_URL + endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=AI_SERVER_TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    logger.warning("[AI서버 fallback] {} HTTP {}".format(endpoint, response.status))
                    self._record_ai_server_failure()
                    return None
                result = json.loads(response.read().decode("utf-8"))
                self.ai_server_failure_count = 0
                return result
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            logger.warning("[AI서버 fallback] {} {}".format(endpoint, e))
            self._record_ai_server_failure()
            return None

    def _record_ai_server_failure(self):
        self.ai_server_failure_count += 1
        if self.ai_server_failure_count >= AI_SERVER_FAILURE_THRESHOLD:
            self.ai_server_cooldown_until = time.time() + AI_SERVER_COOLDOWN_SECONDS
            logger.warning("[AI서버 일시 차단] {}회 연속 실패, {}초 동안 fallback 사용".format(
                self.ai_server_failure_count, AI_SERVER_COOLDOWN_SECONDS))
            self.ai_server_failure_count = 0

    def serialize_ticks(self, ticks):
        return [
            {
                "received_at": tick["received_at"],
                "signed_at": tick["signed_at"],
                "close": tick["close"],
                "high": tick["high"],
                "open": tick["open"],
                "low": tick["low"],
                "ask": tick["ask"],
                "bid": tick["bid"],
                "accum_volume": tick["accum_volume"],
            }
            for tick in ticks
        ]

    def attach_dante_ai_shadow(self, code, name, current_price, ctx, decision, *, stage, breakout_high=0):
        """Call the Dante AI server in shadow mode and attach score metadata."""
        decision.model_score = ""
        decision.model_action = "ai_disabled" if not AI_SERVER_ENABLED else "shadow_unavailable"
        decision.model_target = ""
        decision.model_threshold = ""
        decision.model_name = "DanteRule"

        five_min = ctx.five_min_ind
        env_upper = five_min.env_upper_13_25 if five_min is not None else None
        bb_upper = five_min.bb_upper_55_2 if five_min is not None else None
        closes_count = five_min.closes_count if five_min is not None else 0
        obs_elapsed = ctx.now_ts - (ctx.condition_registered_at or ctx.now_ts)
        features = scoring.build_dante_entry_features(
            current_price=current_price,
            chejan_strength=ctx.chejan_strength,
            volume_speed=ctx.volume_speed,
            spread_rate=ctx.spread_rate,
            obs_elapsed_sec=obs_elapsed,
            env_upper_13=env_upper,
            bb_upper_55=bb_upper,
            five_min_closes_count=closes_count,
            breakout_high=breakout_high,
            minute_bars=ctx.minute_bars,
            chejan_strength_history=ctx.chejan_strength_history,
            is_breakout_zero_bar=ctx.is_breakout_zero_bar,
            is_breakout_prev_bar=ctx.is_breakout_prev_bar,
            upper_wick_ratio=ctx.upper_wick_ratio_zero_bar,
            open_return=ctx.open_return,
            atr_5m_pct=ctx.atr_5m_pct,
            intraday_vwap=ctx.intraday_vwap,
            pullback_low_after_high=ctx.pullback_low_after_high,
        )
        payload = {
            "code": code,
            "name": name,
            "current_price": current_price,
            "rule": {
                "status": decision.status,
                "ratio": decision.ratio,
                "stage": stage,
                "grade": getattr(decision, "grade", "") or "",
                "reason": decision.reason,
                "reason_code": getattr(decision, "reason_code", "") or "",
            },
            "features": features,
            "market_regime": getattr(decision, "market_regime", "") or "",
            "market_gate_action": getattr(decision, "market_gate_action", "") or "",
            "market_gate_reason": getattr(decision, "market_gate_reason", "") or "",
            "enforce_model": False,
        }
        response = self.call_ai_server("/predict-dante-entry", payload)
        if not isinstance(response, dict):
            return features

        decision.model_score = response.get("model_score", "")
        decision.model_action = response.get("model_action", "")
        decision.model_target = response.get("model_target", "")
        decision.model_threshold = response.get("model_threshold", "")
        decision.model_name = response.get("model_name", "DanteLightGBM")
        return features

    def recent_pullback_low(self, code, fallback_price=0, lookback=5):
        bars = self.minute_aggregator.all_bars(code)
        lows = [
            self.parse_int(getattr(bar, "low", 0))
            for bar in bars[-lookback:]
            if self.parse_int(getattr(bar, "low", 0)) > 0
        ]
        return min(lows) if lows else self.parse_int(fallback_price)

    def recent_structural_pullback_low(self, code, fallback_price=0, lookback=8):
        """최근 1분봉에서 눌림 후 회복 구조가 확인된 저점을 손절 기준으로 사용한다."""
        bars = self.minute_aggregator.all_bars(code)
        recent = list(bars[-lookback:]) if bars else []
        fallback = self.parse_int(fallback_price)
        valid_lows = [
            self.parse_int(getattr(bar, "low", 0))
            for bar in recent
            if self.parse_int(getattr(bar, "low", 0)) > 0
        ]
        if not valid_lows:
            return fallback

        # 음봉 뒤 양봉 전환이 있으면 그 전환 구간의 저점을 우선한다.
        for idx in range(len(recent) - 1, 0, -1):
            prev = recent[idx - 1]
            cur = recent[idx]
            prev_open = self.parse_int(getattr(prev, "open", 0))
            prev_close = self.parse_int(getattr(prev, "close", 0))
            cur_open = self.parse_int(getattr(cur, "open", 0))
            cur_close = self.parse_int(getattr(cur, "close", 0))
            prev_low = self.parse_int(getattr(prev, "low", 0))
            cur_low = self.parse_int(getattr(cur, "low", 0))
            if (
                prev_open > 0
                and prev_close > 0
                and cur_open > 0
                and cur_close > 0
                and prev_low > 0
                and cur_low > 0
                and prev_close < prev_open
                and cur_close > cur_open
            ):
                return min(prev_low, cur_low)

        # 전환 패턴이 명확하지 않으면 최근 저점 중 현재가가 회복한 마지막 저점을 사용한다.
        for bar in reversed(recent):
            low = self.parse_int(getattr(bar, "low", 0))
            close = self.parse_int(getattr(bar, "close", 0))
            if low > 0 and fallback > low and (close > low or fallback >= close):
                return low

        return min(valid_lows)

    def build_rule_entry_plan(self, prediction):
        """fib retracement 기반 patient 지정가 계획.

        - breakout_high(=hint) 와 breakout_high 이후 최저 low 를 잡고,
          fib_anchor = low + (high - low) * ENTRY_PLAN_FIB_RATIO 자리에 발주.
        - 풀백 자체가 너무 얕거나(MIN_PULLBACK_DEPTH 미만) 풀백 저점에서 60%
          이상 회복(MAX_RETRACEMENT 초과) 한 윗자리는 plan 비어 있음으로 거절 →
          호출측 validate_entry_plan 가 "가격계획 데이터 부족" 으로 매수 보류.
        - fib 자료가 없을 때만 기존 보수적 fallback (bid+1tick / ask / current_price)
          를 쓰지만 stop 은 여전히 풀백 저점 - 1tick (또는 -1R) 으로 잡는다.
        """
        code = prediction.get("code", "")
        current_price = self.parse_int(prediction.get("current_price", 0))
        if current_price <= 0:
            return {}
        bid = self.parse_int(prediction.get("bid", 0))
        ask = self.parse_int(prediction.get("ask", 0))
        unit = scoring.tick_size(current_price)
        breakout_high_hint = self.parse_int(prediction.get("breakout_high", 0))

        bars = self.minute_aggregator.all_bars(code) if code else []
        anchor_high, anchor_low, anchor_valid = entry_strategy.compute_pullback_anchor(
            bars,
            breakout_high_hint=breakout_high_hint,
            lookback=ENTRY_PLAN_PULLBACK_LOOKBACK,
        )

        pullback_depth = 0.0
        retracement = 0.0
        plan_source = "rule_fallback"
        fib_anchor = 0
        if anchor_valid and anchor_high > 0 and anchor_low > 0 and anchor_low < anchor_high:
            pullback_depth = (anchor_high - anchor_low) / anchor_high
            if pullback_depth < ENTRY_PLAN_MIN_PULLBACK_DEPTH:
                # 풀백 자체가 -0.3% 미만 — anchor 가 사실상 high 와 같음. 매수 거절.
                return {}
            span = anchor_high - anchor_low
            retracement = (current_price - anchor_low) / span if span > 0 else 0.0
            if retracement > ENTRY_PLAN_MAX_RETRACEMENT:
                # 풀백 저점에서 60% 이상 회복 — 윗자리 추격 자리. 매수 거절.
                return {}
            fib_anchor = int(anchor_low + span * ENTRY_PLAN_FIB_RATIO)
            entry_limit = min(current_price, fib_anchor)
            plan_source = "rule_fib_retracement"
        else:
            # fib 분석 불가 — breakout_high/low 추적 부족(편입 직후 등). 보수 fallback.
            if bid > 0:
                entry_limit = min(current_price, bid + unit)
            elif ask > 0:
                entry_limit = min(current_price, ask)
            else:
                entry_limit = current_price
        entry_limit = scoring.round_down_to_tick(entry_limit)

        recent_low = self.parse_int(prediction.get("recent_low", 0))
        if anchor_valid and anchor_low > 0:
            # fib anchor 는 넓게 보되, 손절 기준은 최근 눌림 저점을 우선해 오래된 저점으로
            # 손절폭이 과도하게 벌어지는 케이스를 줄인다.
            stop_anchor = max(anchor_low, recent_low) if recent_low > 0 else anchor_low
        else:
            stop_anchor = recent_low if recent_low > 0 else int(entry_limit * (1 - exit_strategy.R_UNIT_PCT))
        if stop_anchor >= entry_limit:
            stop_anchor = int(entry_limit * (1 - exit_strategy.R_UNIT_PCT))
        structure_stop = scoring.round_down_to_tick(stop_anchor - unit)
        max_risk_stop = scoring.round_up_to_tick(entry_limit * (1 - ENTRY_PLAN_MAX_RISK_PCT))
        min_risk_stop = scoring.round_down_to_tick(entry_limit * (1 - ENTRY_PLAN_MIN_RISK_PCT))
        stop_price = max(structure_stop, max_risk_stop)
        stop_price = min(stop_price, min_risk_stop)
        if stop_price <= 0 or stop_price >= entry_limit:
            stop_price = scoring.round_down_to_tick(entry_limit * (1 - exit_strategy.R_UNIT_PCT))

        risk_per_share = max(entry_limit - stop_price, unit)
        take_profit = scoring.round_up_to_tick(entry_limit + risk_per_share * ENTRY_PLAN_TARGET_R)
        risk_pct = risk_per_share / entry_limit if entry_limit > 0 else 0.0
        rr = (take_profit - entry_limit) / risk_per_share if risk_per_share > 0 else 0.0
        return {
            "entry_limit_price": entry_limit,
            "stop_price": stop_price,
            "take_profit_price": take_profit,
            "risk_reward": rr,
            "max_risk_pct": risk_pct,
            "expiry_seconds": ENTRY_PLAN_EXPIRY_SECONDS,
            "plan_source": plan_source,
            "fib_anchor": fib_anchor,
            "pullback_high": anchor_high,
            "pullback_low": anchor_low,
            "pullback_depth": pullback_depth,
            "retracement": retracement,
        }

    def request_dante_entry_plan(self, code, prediction):
        rule_plan = self.build_rule_entry_plan(prediction)
        payload = {
            "code": code,
            "name": prediction.get("name", ""),
            "current_price": self.parse_int(prediction.get("current_price", 0)),
            "ask": self.parse_int(prediction.get("ask", 0)),
            "bid": self.parse_int(prediction.get("bid", 0)),
            "breakout_high": self.parse_int(prediction.get("breakout_high", 0)),
            "recent_low": self.parse_int(prediction.get("recent_low", 0)),
            "rule": {
                "status": prediction.get("status", "wait"),
                "ratio": float(prediction.get("ratio", 0.0) or 0.0),
                "stage": int(prediction.get("stage", 1) or 1),
                "grade": prediction.get("grade", ""),
                "reason": prediction.get("reason", ""),
                "reason_code": prediction.get("reason_code", ""),
            },
            "features": prediction.get("dante_features", {}),
            "market_regime": prediction.get("market_regime", ""),
            "market_gate_action": prediction.get("market_gate_action", ""),
            "market_gate_reason": prediction.get("market_gate_reason", ""),
            "enforce_model": False,
        }
        response = self.call_ai_server("/predict-dante-entry-plan", payload)
        if isinstance(response, dict):
            plan = dict(rule_plan)
            for key in (
                "entry_limit_price",
                "stop_price",
                "take_profit_price",
                "risk_reward",
                "max_risk_pct",
                "expiry_seconds",
                "plan_source",
                "model_name",
                "model_score",
                "model_action",
                "model_target",
                "model_threshold",
            ):
                if key in response:
                    plan[key] = response.get(key)

            # AI 응답이 entry_limit 을 fib_anchor 위로 끌어올렸으면 rule plan 의
            # fib_anchor 로 cap. 윗자리 추격 방지를 클라 측에서 단일 가드로 강제.
            rule_fib_anchor = self.parse_int(rule_plan.get("fib_anchor", 0))
            ai_entry = self.parse_int(plan.get("entry_limit_price", 0))
            if rule_fib_anchor > 0 and ai_entry > rule_fib_anchor:
                plan["entry_limit_price"] = rule_fib_anchor
                existing_source = plan.get("plan_source", "") or ""
                plan["plan_source"] = (
                    "{}+fib_capped".format(existing_source) if existing_source else "fib_capped"
                )
            entry_limit = self.parse_int(plan.get("entry_limit_price", 0))
            stop_price = self.parse_int(plan.get("stop_price", 0))
            if entry_limit > 0 and stop_price > 0:
                unit = scoring.tick_size(entry_limit)
                max_risk_stop = scoring.round_up_to_tick(entry_limit * (1 - ENTRY_PLAN_MAX_RISK_PCT))
                min_risk_stop = scoring.round_down_to_tick(entry_limit * (1 - ENTRY_PLAN_MIN_RISK_PCT))
                capped_stop = max(stop_price, max_risk_stop)
                capped_stop = min(capped_stop, min_risk_stop)
                if capped_stop != stop_price and 0 < capped_stop < entry_limit:
                    target_r = ENTRY_PLAN_TARGET_R
                    risk_per_share = max(entry_limit - capped_stop, unit)
                    plan["stop_price"] = capped_stop
                    plan["take_profit_price"] = scoring.round_up_to_tick(entry_limit + risk_per_share * target_r)
                    plan["risk_reward"] = round(
                        (plan["take_profit_price"] - entry_limit) / risk_per_share,
                        3,
                    )
                    plan["max_risk_pct"] = round(risk_per_share / entry_limit, 5)
                    existing_source = plan.get("plan_source", "") or ""
                    plan["plan_source"] = (
                        "{}+risk_capped".format(existing_source) if existing_source else "risk_capped"
                    )
            return plan
        return rule_plan

    def validate_entry_plan(self, prediction, plan):
        current_price = self.parse_int(prediction.get("current_price", 0))
        entry_limit = self.parse_int(plan.get("entry_limit_price", 0))
        stop_price = self.parse_int(plan.get("stop_price", 0))
        take_profit = self.parse_int(plan.get("take_profit_price", 0))
        if current_price <= 0 or entry_limit <= 0 or stop_price <= 0 or take_profit <= 0:
            return False, "가격계획 데이터 부족"
        if entry_limit > current_price * (1 + ENTRY_PLAN_MAX_ENTRY_PREMIUM_PCT):
            return False, "지정가가 현재가 대비 과도하게 높음"
        if stop_price >= entry_limit:
            return False, "손절가가 매수가 이상"
        if take_profit <= entry_limit:
            return False, "익절가가 매수가 이하"
        risk_pct = (entry_limit - stop_price) / entry_limit
        if risk_pct < ENTRY_PLAN_MIN_RISK_PCT:
            return False, "손절폭 과소 {:.2%}".format(risk_pct)
        if risk_pct > ENTRY_PLAN_MAX_RISK_PCT:
            return False, "손절폭 과대 {:.2%}".format(risk_pct)
        rr = (take_profit - entry_limit) / (entry_limit - stop_price)
        if rr < ENTRY_PLAN_MIN_RR:
            return False, "손익비 부족 {:.2f}R".format(rr)
        return True, "지정가 계획 OK entry={} stop={} target={} risk={:.2%} rr={:.2f}".format(
            entry_limit, stop_price, take_profit, risk_pct, rr
        )

    def is_risk_too_wide_plan_rejection(self, plan_reason):
        return str(plan_reason or "").startswith("손절폭 과대")

    def _plan_risk_pct(self, plan):
        entry_limit = self.parse_int(plan.get("entry_limit_price", 0))
        stop_price = self.parse_int(plan.get("stop_price", 0))
        if entry_limit <= 0 or stop_price <= 0 or stop_price >= entry_limit:
            return 0.0
        return (entry_limit - stop_price) / entry_limit

    def cleanup_risk_too_wide_watchlist(self, now_ts=None):
        now_ts = now_ts or time.time()
        for code, watch in list(self.risk_too_wide_watchlist.items()):
            if now_ts > float(watch.get("deadline", 0) or 0):
                self.risk_too_wide_watchlist.pop(code, None)

    def qualifies_risk_too_wide_watch(self, prediction, plan, plan_reason):
        if not RISK_TOO_WIDE_WATCH_ENABLED:
            return False
        if not self.is_risk_too_wide_plan_rejection(plan_reason):
            return False
        if prediction.get("market_gate_action", "") == entry_strategy.MARKET_ACTION_BLOCK_ALL:
            return False
        model_score = self.parse_float(plan.get("model_score", prediction.get("model_score", 0.0)), 0.0)
        if not MODEL_ASSIST_ONLY and model_score >= RISK_TOO_WIDE_MIN_MODEL_SCORE:
            return True
        reason_code = str(prediction.get("reason_code", "") or "")
        ready_codes = {
            entry_strategy.READY_AGRADE_FIRST,
            entry_strategy.READY_AGRADE_SECOND,
            entry_strategy.READY_BGRADE_PULLBACK,
            entry_strategy.READY_REENTRY_PULLBACK,
        }
        return reason_code in ready_codes

    def start_risk_too_wide_watch(self, code, prediction, plan, plan_reason):
        code = self.normalize_code(code)
        if not self.qualifies_risk_too_wide_watch(prediction, plan, plan_reason):
            return False
        self.cleanup_risk_too_wide_watchlist()
        if code not in self.risk_too_wide_watchlist and len(self.risk_too_wide_watchlist) >= RISK_TOO_WIDE_MAX_CODES:
            logger.info(
                "[손절폭 재감시 제외] %s watchlist 한도 도달 %s",
                code,
                RISK_TOO_WIDE_MAX_CODES,
            )
            return False

        now_ts = time.time()
        risk_pct = self._plan_risk_pct(plan)
        prev = self.risk_too_wide_watchlist.get(code, {})
        best_risk_pct = self.parse_float(prev.get("best_risk_pct", risk_pct), risk_pct)
        if risk_pct > 0:
            best_risk_pct = min(best_risk_pct, risk_pct) if best_risk_pct > 0 else risk_pct
        watch = {
            "code": code,
            "name": prediction.get("name", ""),
            "started_at": float(prev.get("started_at", now_ts) or now_ts),
            "deadline": float(prev.get("deadline", now_ts + RISK_TOO_WIDE_WATCH_SECONDS) or now_ts + RISK_TOO_WIDE_WATCH_SECONDS),
            "last_recheck_at": now_ts,
            "model_score": plan.get("model_score", prediction.get("model_score", "")),
            "model_name": plan.get("model_name", prediction.get("model_name", "")),
            "reason_code": prediction.get("reason_code", ""),
            "entry_limit_price": self.parse_int(plan.get("entry_limit_price", 0)),
            "stop_price": self.parse_int(plan.get("stop_price", 0)),
            "risk_pct": risk_pct,
            "best_risk_pct": best_risk_pct,
            "plan_reason": plan_reason,
        }
        self.risk_too_wide_watchlist[code] = watch
        self.requeue_condition_stock(code)
        logger.info(
            "[손절폭 재감시 등록] %s risk=%.2f%% best=%.2f%% model=%s deadline=%.0fs",
            code,
            risk_pct * 100,
            best_risk_pct * 100,
            watch.get("model_score", ""),
            max(watch["deadline"] - now_ts, 0),
        )
        return True

    def should_continue_risk_too_wide_watch(self, code):
        code = self.normalize_code(code)
        watch = self.risk_too_wide_watchlist.get(code)
        if watch is None:
            return True
        position = self.portfolio.get(code)
        if position is not None and (position.is_holding() or position.is_pending() or position.bought_today):
            self.risk_too_wide_watchlist.pop(code, None)
            logger.info("[손절폭 재감시 종료] %s 이미 보유/미체결/매수 처리", code)
            return False
        now_ts = time.time()
        if self.current_hhmmss() >= OPENING_BUY_END:
            self.risk_too_wide_watchlist.pop(code, None)
            logger.info("[손절폭 재감시 종료] %s 매수 가능 시간 종료", code)
            return False
        if now_ts > float(watch.get("deadline", 0) or 0):
            self.risk_too_wide_watchlist.pop(code, None)
            logger.info(
                "[손절폭 재감시 만료] %s best_risk=%.2f%%",
                code,
                self.parse_float(watch.get("best_risk_pct", 0.0), 0.0) * 100,
            )
            return False
        last_recheck = float(watch.get("last_recheck_at", 0) or 0)
        if now_ts - last_recheck < RISK_TOO_WIDE_RECHECK_INTERVAL_SECONDS:
            self.requeue_condition_stock(code)
            return False
        watch["last_recheck_at"] = now_ts
        return True

    def estimate_position_plan_risk(self, position):
        """현재 포지션/미체결이 계획상 감수하는 원화 리스크를 계산한다."""
        if position is None:
            return 0
        entry_price = self.parse_int(getattr(position, "entry_price", 0))
        stop_price = self.parse_int(getattr(position, "stop_price", 0))
        if entry_price <= 0 or stop_price <= 0 or stop_price >= entry_price:
            return 0

        quantity = self.parse_int(getattr(position, "quantity", 0))
        planned_quantity = self.parse_int(getattr(position, "planned_quantity", 0))
        if getattr(position, "partial_taken", False) and quantity > 0:
            risk_quantity = quantity
        elif (
            (getattr(position, "entry_stage", 0) < 2 or getattr(position, "pending_buy", False))
            and planned_quantity > 0
        ):
            risk_quantity = planned_quantity
        elif quantity > 0:
            risk_quantity = quantity
        else:
            risk_quantity = planned_quantity

        if risk_quantity <= 0:
            return 0
        return max(entry_price - stop_price, 0) * risk_quantity

    def current_open_position_risk(self, *, exclude_code=""):
        """보유/미체결 포지션의 계획 리스크 합계."""
        total = 0
        if not hasattr(self.portfolio, "items"):
            return total
        for code, position in self.portfolio.items():
            if exclude_code and code == exclude_code:
                continue
            if not (
                position.is_holding()
                or position.is_pending()
                or self.parse_int(getattr(position, "planned_quantity", 0)) > 0
            ):
                continue
            total += self.estimate_position_plan_risk(position)
        return total

    def build_position_size_plan(self, *, code, deposit, entry_limit_price, stop_price):
        """총 리스크 예산과 현금 한도를 동시에 만족하는 계획 수량을 계산한다."""
        entry_limit_price = self.parse_int(entry_limit_price)
        stop_price = self.parse_int(stop_price)
        deposit = self.parse_int(deposit)
        risk_per_share = entry_limit_price - stop_price
        if deposit <= 0 or entry_limit_price <= 0 or risk_per_share <= 0:
            return {
                "planned_quantity": 0,
                "reason": "sizing_input_invalid",
                "risk_per_share": max(risk_per_share, 0),
            }

        used_portfolio_risk = self.current_open_position_risk(exclude_code=code)
        portfolio_risk_budget = int(deposit * MAX_PORTFOLIO_RISK_RATE)
        remaining_portfolio_risk = max(portfolio_risk_budget - used_portfolio_risk, 0)
        per_trade_risk_budget = int(deposit * RISK_PER_TRADE_RATE)
        risk_budget = min(per_trade_risk_budget, remaining_portfolio_risk)

        risk_quantity = risk_budget // risk_per_share if risk_per_share > 0 else 0
        cash_budget = int(deposit * BUY_CASH_BUFFER_RATE)
        cash_quantity = cash_budget // entry_limit_price if entry_limit_price > 0 else 0
        planned_quantity = int(min(risk_quantity, cash_quantity))
        order_cash = planned_quantity * entry_limit_price

        if planned_quantity <= 0:
            reason = "portfolio_risk_exhausted" if remaining_portfolio_risk <= 0 else "risk_or_cash_quantity_zero"
        elif order_cash < MIN_ORDER_CASH:
            planned_quantity = 0
            reason = "below_min_order_cash"
        elif risk_quantity <= cash_quantity:
            reason = "risk_capped"
        else:
            reason = "cash_capped"

        return {
            "planned_quantity": planned_quantity,
            "reason": reason,
            "risk_per_share": risk_per_share,
            "risk_budget": risk_budget,
            "per_trade_risk_budget": per_trade_risk_budget,
            "portfolio_risk_budget": portfolio_risk_budget,
            "used_portfolio_risk": used_portfolio_risk,
            "remaining_portfolio_risk": remaining_portfolio_risk,
            "risk_quantity": int(risk_quantity),
            "cash_quantity": int(cash_quantity),
            "cash_budget": cash_budget,
            "order_cash": order_cash,
        }

    def format_position_size_plan(self, sizing_plan):
        if not isinstance(sizing_plan, dict):
            return ""
        return (
            "sizing={reason}, risk/share={risk_per_share}, risk_budget={risk_budget}, "
            "used_risk={used_portfolio_risk}/{portfolio_risk_budget}, "
            "qty risk/cash={risk_quantity}/{cash_quantity}, min_cash={min_cash}"
        ).format(
            reason=sizing_plan.get("reason", ""),
            risk_per_share=sizing_plan.get("risk_per_share", 0),
            risk_budget=sizing_plan.get("risk_budget", 0),
            used_portfolio_risk=sizing_plan.get("used_portfolio_risk", 0),
            portfolio_risk_budget=sizing_plan.get("portfolio_risk_budget", 0),
            risk_quantity=sizing_plan.get("risk_quantity", 0),
            cash_quantity=sizing_plan.get("cash_quantity", 0),
            min_cash=MIN_ORDER_CASH,
        )

    def dante_hard_blocks_ai_candidate(self, prediction):
        reason_code = str(prediction.get("reason_code", "") or "")
        market_gate_action = prediction.get("market_gate_action", "")
        if market_gate_action == entry_strategy.MARKET_ACTION_BLOCK_ALL:
            return True, "market risk_off"
        # Tier A 데이터 위생 — 틱·관찰시간·5분봉 캐시가 부족하면 피처 품질을 보장할 수 없으므로
        # AI 점수로 승격하지 않음(모델이 학습 시 못 본 분포/노이즈 입력 방지).
        hard_codes = {
            entry_strategy.GATE_TICKS_INSUFFICIENT,
            entry_strategy.GATE_OBSERVATION_SHORT,
            entry_strategy.GATE_FIVEMIN_CACHE,
            entry_strategy.GATE_ALREADY_ENTERED,
            entry_strategy.GATE_PRICE_DATA,
            entry_strategy.GATE_STAGE2_PRICE_DATA,
            entry_strategy.GATE_SPREAD,
            entry_strategy.GATE_STAGE2_SPREAD,
            entry_strategy.GATE_OVERHEAT_OPEN,
            entry_strategy.GATE_OVERHEAT_BB55,
            entry_strategy.GATE_STAGE2_DRAWDOWN,
            entry_strategy.GATE_BGRADE_DRAWDOWN,
        }
        if reason_code in hard_codes:
            return True, reason_code
        return False, ""

    def should_watch_pullback_recovery(self, prediction):
        status = str(prediction.get("status", "") or "")
        if status not in ("wait", "blocked"):
            return False
        if prediction.get("market_gate_action", "") == entry_strategy.MARKET_ACTION_BLOCK_ALL:
            return False
        reason_code = str(prediction.get("reason_code", "") or "")
        return reason_code in PULLBACK_RECOVERY_WATCH_REASON_CODES

    def dante_allows_ai_candidate_watch(self, prediction):
        """AI가 바로 매수하지 않고 재평가 감시로만 올릴 수 있는 회복형 게이트."""
        if not AI_CANDIDATE_WATCH_ENABLED:
            return False, "watch_disabled"
        status = str(prediction.get("status", "") or "")
        if status not in ("wait", "blocked"):
            return False, "status_not_watchable"
        hard_blocked, block_reason = self.dante_hard_blocks_ai_candidate(prediction)
        if hard_blocked:
            return False, block_reason
        reason_code = str(prediction.get("reason_code", "") or "")
        watchable_codes = {
            entry_strategy.GATE_VOLUME_SPEED,
            entry_strategy.GATE_CHEJAN_SOFT,
            entry_strategy.GATE_CHEJAN_HARD_NO_TREND,
            entry_strategy.GATE_STAGE2_CHEJAN,
            entry_strategy.GATE_STAGE2_VOLUME,
            entry_strategy.GATE_STAGE2_PULLBACK_SHALLOW,
            entry_strategy.GATE_STAGE2_PULLBACK_DEEP,
            entry_strategy.GATE_STAGE2_VWAP_LOST,
            entry_strategy.GATE_BGRADE_PULLBACK_SHALLOW,
            entry_strategy.GATE_BGRADE_PULLBACK_DEEP,
            entry_strategy.GATE_BGRADE_VWAP_LOST,
            entry_strategy.GATE_BGRADE_NO_REVERSAL,
            entry_strategy.GATE_STAGE2_NO_REVERSAL,
            entry_strategy.GATE_NO_BREAKOUT,
        }
        if reason_code not in watchable_codes:
            return False, "reason_not_watchable:{}".format(reason_code)
        return True, ""

    def cleanup_ai_candidate_watchlist(self, now_ts=None):
        now_ts = now_ts or time.time()
        for code, watch in list(self.ai_candidate_watchlist.items()):
            if now_ts > float(watch.get("deadline", 0) or 0):
                self.ai_candidate_watchlist.pop(code, None)

    def start_ai_candidate_watch(self, code, prediction, required_score):
        code = self.normalize_code(code)
        self.cleanup_ai_candidate_watchlist()
        if code not in self.ai_candidate_watchlist and len(self.ai_candidate_watchlist) >= AI_CANDIDATE_WATCH_MAX_CODES:
            logger.info(
                "[AI 후보 감시 제외] %s watchlist 한도 도달 %s",
                code,
                AI_CANDIDATE_WATCH_MAX_CODES,
            )
            return False

        now_ts = time.time()
        prev = self.ai_candidate_watchlist.get(code, {})
        model_score = self.parse_float(prediction.get("model_score", 0.0), 0.0)
        best_score = self.parse_float(prev.get("best_model_score", model_score), model_score)
        best_score = max(best_score, model_score)
        watch = {
            "code": code,
            "name": prediction.get("name", ""),
            "started_at": float(prev.get("started_at", now_ts) or now_ts),
            "deadline": float(prev.get("deadline", now_ts + AI_CANDIDATE_WATCH_SECONDS) or now_ts + AI_CANDIDATE_WATCH_SECONDS),
            "last_recheck_at": now_ts,
            "model_score": model_score,
            "best_model_score": best_score,
            "required_score": float(required_score),
            "model_threshold": prediction.get("model_threshold", ""),
            "model_target": prediction.get("model_target", ""),
            "reason_code": prediction.get("reason_code", ""),
            "rule_status": prediction.get("status", ""),
            "rule_reason": prediction.get("reason", ""),
        }
        self.ai_candidate_watchlist[code] = watch
        self.requeue_condition_stock(code)
        logger.info(
            "[AI 후보 감시 등록] %s score=%.3f required=%.3f status=%s reason=%s",
            code,
            model_score,
            required_score,
            watch["rule_status"],
            watch["reason_code"],
        )
        return True

    def should_continue_ai_candidate_watch(self, code):
        code = self.normalize_code(code)
        watch = self.ai_candidate_watchlist.get(code)
        if watch is None:
            return True
        position = self.portfolio.get(code)
        if position is not None and (position.is_holding() or position.is_pending() or position.bought_today):
            self.ai_candidate_watchlist.pop(code, None)
            logger.info("[AI 후보 감시 종료] %s 이미 보유/미체결/매수 처리", code)
            return False
        now_ts = time.time()
        if self.current_hhmmss() >= OPENING_BUY_END:
            self.ai_candidate_watchlist.pop(code, None)
            logger.info("[AI 후보 감시 종료] %s 매수 가능 시간 종료", code)
            return False
        if now_ts > float(watch.get("deadline", 0) or 0):
            self.ai_candidate_watchlist.pop(code, None)
            logger.info(
                "[AI 후보 감시 만료] %s best_score=%.3f reason=%s",
                code,
                self.parse_float(watch.get("best_model_score", 0.0), 0.0),
                watch.get("reason_code", ""),
            )
            return False
        last_recheck = float(watch.get("last_recheck_at", 0) or 0)
        if now_ts - last_recheck < AI_CANDIDATE_WATCH_RECHECK_INTERVAL_SECONDS:
            self.requeue_condition_stock(code)
            return False
        watch["last_recheck_at"] = now_ts
        return True

    def maybe_promote_ai_candidate(self, prediction):
        if MODEL_ASSIST_ONLY or not AI_CANDIDATE_PROMOTION_ENABLED:
            return prediction
        code = self.normalize_code(prediction.get("code", ""))
        if prediction.get("status") == "ready":
            if code in self.ai_candidate_watchlist:
                watch = self.ai_candidate_watchlist.pop(code, {})
                prediction["ai_watch_started_at"] = watch.get("started_at", "")
                prediction["ai_watch_best_model_score"] = watch.get("best_model_score", "")
                prediction["reason"] = "{} | AI 감시 후 룰 ready".format(prediction.get("reason", "")).strip()
                logger.info(
                    "[AI 후보 감시 통과] %s best_score=%.3f now_ready=%s",
                    code,
                    self.parse_float(watch.get("best_model_score", 0.0), 0.0),
                    prediction.get("reason_code", ""),
                )
            return prediction
        hard_blocked, block_reason = self.dante_hard_blocks_ai_candidate(prediction)
        if hard_blocked:
            if code in self.ai_candidate_watchlist:
                self.ai_candidate_watchlist.pop(code, None)
            prediction["ai_candidate_block_reason"] = block_reason
            return prediction
        model_action = str(prediction.get("model_action", "") or "")
        if model_action != "shadow_allow":
            return prediction
        model_score = self.parse_float(prediction.get("model_score", 0.0), 0.0)
        model_threshold = self.parse_float(prediction.get("model_threshold", 0.0), 0.0)
        required_score = max(AI_CANDIDATE_MIN_SCORE, model_threshold)
        if model_score < required_score:
            return prediction

        watchable, watch_reason = self.dante_allows_ai_candidate_watch(prediction)
        if not watchable:
            prediction["ai_candidate_block_reason"] = watch_reason
            return prediction

        self.start_ai_candidate_watch(code, prediction, required_score)
        prediction["ai_watch_status"] = "watching"
        prediction["rule_status"] = prediction.get("status", "")
        prediction["rule_reason"] = prediction.get("reason", "")
        prediction["status"] = "wait"
        prediction["ratio"] = 0.0
        prediction["reason"] = "AI 후보 감시 score {:.3f} >= {:.3f} | 룰 재확인 대기: {} {}".format(
            model_score,
            required_score,
            prediction.get("rule_status", ""),
            prediction.get("rule_reason", ""),
        )
        return prediction

    def score_opening_trade(self, code):
        """단테조건식 편입 종목에 대해 A급 감시 또는 첫 눌림 본진입 가능 여부 평가."""
        code = self.normalize_code(code)
        now = self.current_hhmmss()
        if now < OPENING_BUY_START:
            return {"status": "wait", "reason": "매수 시작 전"}
        if now > OPENING_BUY_END:
            return {"status": "blocked", "reason": "매수 시간 종료"}
        if self.is_volume_speed_cooling_down(code):
            remain = int(self.volume_speed_cooldown_until.get(code, 0) - time.time())
            return {
                "status": "blocked",
                "reason": "거래속도(거래대금) 반복 부족 쿨다운 {}초 남음".format(max(remain, 0)),
                "reason_code": entry_strategy.GATE_VOLUME_SPEED,
            }

        ticks = self.realtime_ticks.get(code, [])
        if not ticks:
            return {"status": "wait", "reason": "실시간 틱 미수신"}

        first = ticks[0]
        last = ticks[-1]
        current_price = last["close"]
        open_price = last["open"]
        ask = last["ask"]
        bid = last["bid"]
        chejan_strength = float(last.get("chejan_strength", 0.0))

        if current_price <= 0 or ask <= 0 or bid <= 0:
            return {"status": "wait", "reason": "실시간 가격 데이터 부족"}

        spread_rate = (ask - bid) / current_price if current_price > 0 else 0.0
        elapsed_secs = max(last["received_at"] - first["received_at"], 1.0)
        volume_delta = max(last["accum_volume"] - first["accum_volume"], 0)
        volume_speed = volume_delta / elapsed_secs
        turnover_speed_per_min = volume_speed * current_price * 60
        time_filter = self.evaluate_time_filter(
            code,
            current_price=current_price,
            accum_volume=last.get("accum_volume", 0),
        )
        if not time_filter.get("ok"):
            return {
                "status": time_filter.get("status", "blocked"),
                "code": code,
                "name": self.get_code_name(code),
                "current_price": current_price,
                "ratio": 0.0,
                "stage": 1,
                "score": 0.0,
                "reason": time_filter.get("reason", "TimeFilter block"),
                "reason_code": "TIME_FILTER",
                "time_filter_phase": time_filter.get("phase", ""),
                "time_filter_weight": time_filter.get("weight", 0.0),
                "daily_turnover": time_filter.get("daily_turnover", 0),
                "turnover_rank": time_filter.get("turnover_rank", 0),
                "ranked_count": time_filter.get("ranked_count", 0),
                "volume_speed": volume_speed,
                "turnover_speed_per_min": turnover_speed_per_min,
                "chejan_strength": chejan_strength,
            }

        highs = [tick["high"] for tick in ticks if tick["high"] > 0]
        lows = [tick["low"] for tick in ticks if tick["low"] > 0]
        high = max(highs) if highs else current_price
        low = min(lows) if lows else current_price

        # 5분봉 추세 필터(필요 시) 갱신. TR 분주 시 자동으로 다음 사이클로 미뤄진다.
        self.refresh_five_min_indicators(code)

        position = self.portfolio.get(code)
        name = self.get_code_name(code)
        five_min_ind = self.five_min_cache.get(code)

        # 새 게이트 입력값 추출 (체결강도 추세/돌파 등급/윗꼬리/과열).
        chejan_history = [
            float(t.get("chejan_strength", 0.0))
            for t in ticks[-entry_strategy.CHEJAN_STRENGTH_TREND_LOOKBACK:]
        ]
        is_breakout_zero = bool(five_min_ind.is_breakout_zero_bar()) if five_min_ind else False
        is_breakout_prev = bool(five_min_ind.is_breakout_prev_bar()) if five_min_ind else False
        upper_wick = float(five_min_ind.upper_wick_ratio_zero_bar()) if five_min_ind else 0.0
        if five_min_ind and five_min_ind.bb_upper_55_2 and five_min_ind.bb_upper_55_2 > 0:
            px_over_bb55 = current_price / five_min_ind.bb_upper_55_2 - 1
        else:
            px_over_bb55 = 0.0
        open_return = (current_price / open_price - 1) if open_price > 0 else 0.0

        # === ATR / VWAP 보강 (W1: 동적 풀백 밴드 + 고점추매 차단) ===
        # atr_pct 가 None 이면 0.0 으로 떨어뜨려 entry_strategy 가 정적 fallback 사용.
        atr_5m_pct = float(getattr(five_min_ind, "atr_pct", None) or 0.0) if five_min_ind else 0.0
        intraday_vwap = float(self.minute_aggregator.intraday_vwap(code) or 0.0)
        # 풀백 저점은 minute_aggregator 의 1분봉 lookback 에서 직접 추출(고점→저점 시퀀스 보장).
        pullback_low_after_high = int(self.minute_aggregator.pullback_low_after_high(code) or 0)

        # 매크로 dry-run 게이트 — 이번 PR 은 status/ratio 변경 없이 메타만 부여.
        market_snapshot = self.market_state.snapshot()

        ctx = entry_strategy.EntryContext(
            code=code,
            name=name,
            current_price=current_price,
            open_price=open_price,
            high=high,
            low=low,
            ask=ask,
            bid=bid,
            chejan_strength=chejan_strength,
            volume_speed=volume_speed,
            spread_rate=spread_rate,
            minute_bars=self.minute_aggregator.all_bars(code),
            five_min_ind=five_min_ind,
            condition_registered_at=self.condition_registered_at.get(code, time.time()),
            now_ts=time.time(),
            tick_count=len(ticks),
            position=position,
            chejan_strength_history=chejan_history,
            is_breakout_zero_bar=is_breakout_zero,
            is_breakout_prev_bar=is_breakout_prev,
            upper_wick_ratio_zero_bar=upper_wick,
            px_over_bb55_pct=px_over_bb55,
            open_return=open_return,
            market_state=market_snapshot,
            atr_5m_pct=atr_5m_pct,
            intraday_vwap=intraday_vwap,
            pullback_low_after_high=pullback_low_after_high,
        )

        reentry_watch = self.dante_reentry_watchlist.get(code)
        watch = self.dante_a_watchlist.get(code)
        if reentry_watch is not None and (position is None or position.entry_stage == 0):
            decision = entry_strategy.evaluate_reentry_after_exit(ctx, reentry_watch)
            stage = 2
            if decision.status == "blocked":
                self.dante_reentry_watchlist.pop(code, None)
        elif watch is not None and (position is None or position.entry_stage == 0):
            decision = entry_strategy.evaluate_a_grade_watch_entry(
                ctx,
                breakout_high=self.parse_int(watch.get("breakout_high", 0)),
                watch_started_at=float(watch.get("started_at", 0) or 0),
                pullback_window_deadline=float(watch.get("deadline", 0) or 0),
            )
            stage = 2
        elif position is not None and position.entry_stage == 1:
            decision = entry_strategy.evaluate_second_entry(ctx)
            stage = 2
        else:
            decision = entry_strategy.evaluate_first_entry(ctx)
            stage = decision.stage if decision.stage in (1, 2) else 1

        if decision.reason_code == entry_strategy.GATE_VOLUME_SPEED:
            if self.record_volume_speed_wait(code, volume_speed, turnover_speed_per_min):
                return {
                    "status": "blocked",
                    "stage": stage,
                    "reason": "거래속도(거래대금) 반복 부족 {:.1f}백만원/분 < {:.1f}백만원/분".format(
                        turnover_speed_per_min / 1_000_000,
                        entry_strategy.MIN_TURNOVER_SPEED_PER_MIN / 1_000_000,
                    ),
                    "reason_code": entry_strategy.GATE_VOLUME_SPEED,
                }
        else:
            self.volume_speed_wait_counts.pop(code, None)

        if decision.reason_code == entry_strategy.WATCH_AGRADE_BREAKOUT:
            watch = self.dante_a_watchlist.get(code)
            if watch is None:
                watch = {
                    "started_at": ctx.now_ts,
                    "deadline": ctx.now_ts + entry_strategy.PULLBACK_WINDOW_MAX_SECONDS,
                    "breakout_high": current_price,
                }
                self.dante_a_watchlist[code] = watch
                logger.info("[A급 감시 시작] %s %s 현재가 %s", code, name, current_price)
            else:
                watch["breakout_high"] = max(self.parse_int(watch.get("breakout_high", 0)), current_price)
            self.requeue_condition_stock(code)
        elif (
            decision.status == "blocked"
            and code in self.dante_a_watchlist
            and decision.reason_code not in PULLBACK_RECOVERY_WATCH_REASON_CODES
        ):
            self.dante_a_watchlist.pop(code, None)

        if reentry_watch is not None:
            ai_breakout_high = self.parse_int(reentry_watch.get("breakout_high", 0))
        elif watch is not None:
            ai_breakout_high = self.parse_int(watch.get("breakout_high", 0))
        elif position is not None:
            ai_breakout_high = self.parse_int(getattr(position, "breakout_high", 0))
        else:
            ai_breakout_high = 0
        if hasattr(self, "attach_dante_ai_shadow"):
            dante_features = self.attach_dante_ai_shadow(
                code,
                name,
                current_price,
                ctx,
                decision,
                stage=stage,
                breakout_high=ai_breakout_high,
            )
        else:
            dante_features = {}

        # Phase A 학습 트랙 — ready 시점의 모든 입력을 즉시 캡처해 사후 라벨링 큐에 등록한다.
        # 매수 발주/체결 결과와 무관하게 게이트가 'ready' 라고 판단한 표본을 모두 누적한다.
        if decision.status == "ready":
            try:
                self.register_dante_training_sample(
                    code=code,
                    name=name,
                    ctx=ctx,
                    decision=decision,
                    current_price=current_price,
                )
            except Exception as exc:
                logger.warning("[단테 학습데이터] sample 등록 실패 {} {}".format(code, exc))
        else:
            # Shadow 트랙 — 게이트가 wait/blocked 으로 거른 표본도 false-negative 측정용으로
            # 캡처. 의미 있는 데이터(틱/관찰시간/캐시 충분) 기준은 register 내부에서 다시 검사.
            try:
                self.register_dante_shadow_sample(
                    code=code,
                    name=name,
                    ctx=ctx,
                    decision=decision,
                    current_price=current_price,
                )
            except Exception as exc:
                logger.warning("[단테 shadow] sample 등록 실패 {} {}".format(code, exc))

        prediction = {
            "status": decision.status,
            "code": code,
            "name": name,
            "current_price": current_price,
            "ratio": decision.ratio,
            "stage": stage,
            "score": decision.ratio,
            "spread_rate": spread_rate,
            "chejan_strength": chejan_strength,
            "volume_speed": volume_speed,
            "turnover_speed_per_min": turnover_speed_per_min,
            "daily_turnover": time_filter.get("daily_turnover", 0),
            "turnover_rank": time_filter.get("turnover_rank", 0),
            "ranked_count": time_filter.get("ranked_count", 0),
            "time_filter_phase": time_filter.get("phase", ""),
            "time_filter_weight": time_filter.get("weight", 1.0),
            "reason": decision.reason,
            "reason_code": getattr(decision, "reason_code", "") or "",
            "grade": getattr(decision, "grade", "") or "",
            "is_breakout_zero_bar": is_breakout_zero,
            "is_breakout_prev_bar": is_breakout_prev,
            "upper_wick_ratio": upper_wick,
            "px_over_bb55_pct": px_over_bb55,
            "open_return": open_return,
            "chejan_strength_history": chejan_history,
            "ask": ask,
            "bid": bid,
            "breakout_high": ai_breakout_high,
            "recent_low": (
                self.recent_structural_pullback_low(
                    code,
                    current_price,
                    lookback=ENTRY_PLAN_STOP_LOOKBACK,
                )
                if hasattr(self, "recent_structural_pullback_low")
                else current_price
            ),
            "dante_features": dante_features,
            "model_name": getattr(decision, "model_name", "DanteRule") or "DanteRule",
            "model_score": getattr(decision, "model_score", "") or "",
            "model_action": getattr(decision, "model_action", "") or "",
            "model_target": getattr(decision, "model_target", "") or "",
            "model_threshold": getattr(decision, "model_threshold", "") or "",
            # 매크로 dry-run 메타 — place_buy_order 등 trade_log 호출처에서 그대로 사용.
            "market_regime": getattr(decision, "market_regime", "") or "",
            "market_gate_action": getattr(decision, "market_gate_action", "") or "",
            "market_gate_reason": getattr(decision, "market_gate_reason", "") or "",
        }
        if hasattr(self, "maybe_promote_ai_candidate"):
            return self.maybe_promote_ai_candidate(prediction)
        return prediction

    def handle_condition_stock(self, code):
        code = self.normalize_code(code)
        if code in self.no_tick_codes:
            return
        if hasattr(self, "ensure_monitoring_stock"):
            self.ensure_monitoring_stock(code)
        if code not in self.realtime_registered_codes:
            self.register_realtime_stock(code)
            self.condition_registered_at[code] = time.time()
            self.requeue_condition_stock(code)
            logger.info("[조건편입 관찰] {} 실시간 등록 - 퀀트조건식 눌림/체결강도 대기".format(code))
            return
        if not self.should_continue_risk_too_wide_watch(code):
            return
        if hasattr(self, "should_continue_ai_candidate_watch") and not self.should_continue_ai_candidate_watch(code):
            return

        prediction = self.predict_stock(code)
        if prediction is None:
            return

        status = prediction.get("status")
        stage = int(prediction.get("stage", 1) or 1)

        if status == "wait":
            ticks = self.realtime_ticks.get(code, [])
            registered_at = self.condition_registered_at.get(code, time.time())
            if len(ticks) == 0 and time.time() - registered_at >= REALTIME_TICK_WAIT_TIMEOUT_SECONDS:
                self.no_tick_codes.add(code)
                logger.info("[매수 제외] {} 실시간 틱 수신 없음 {}초".format(code, REALTIME_TICK_WAIT_TIMEOUT_SECONDS))
                return
            self.requeue_condition_stock(code)
            if self.should_print_wait_log(code):
                logger.info("[{}차 매수 대기] {} {}".format(stage, code, prediction.get("reason", "")))
            return
        if status == "blocked":
            if hasattr(self, "should_watch_pullback_recovery") and self.should_watch_pullback_recovery(prediction):
                self.requeue_condition_stock(code)
                if self.should_print_wait_log(code):
                    logger.info("[{}차 매수 대기] {} 회복 감시: {}".format(stage, code, prediction.get("reason", "")))
                return
            if hasattr(self, "ai_candidate_watchlist"):
                self.ai_candidate_watchlist.pop(code, None)
            self.risk_too_wide_watchlist.pop(code, None)
            logger.info("[{}차 매수 제외] {} {}".format(stage, code, prediction.get("reason", "")))
            return

        market_gate_action = prediction.get("market_gate_action", "")
        if market_gate_action == entry_strategy.MARKET_ACTION_BLOCK_ALL:
            self.risk_too_wide_watchlist.pop(code, None)
            logger.info("[매수 제외] %s market gate block_all: %s", code, prediction.get("market_gate_reason", ""))
            return
        if (
            market_gate_action == entry_strategy.MARKET_ACTION_BLOCK_CHASE_ONLY
            and prediction.get("reason_code") == entry_strategy.READY_AGRADE_FIRST
        ):
            logger.info("[매수 제외] %s weak market chase block", code)
            return

        self.update_account_status()
        grade = str(prediction.get("grade", "") or "")
        if self.should_skip_buy(code, stage=stage, grade=grade):
            return

        ratio = float(prediction.get("ratio", 0.0))
        if ratio <= 0:
            return

        if prediction.get("plan_source") in ("safe_pullback", QUANT_PLAN_SOURCE):
            plan = {
                "entry_limit_price": prediction.get("entry_limit_price", 0),
                "stop_price": prediction.get("stop_price", 0),
                "take_profit_price": prediction.get("take_profit_price", 0),
                "plan_source": prediction.get("plan_source", ""),
                "order_gubun": prediction.get("order_gubun", "00"),
            }
            plan_ok = True
            plan_reason = prediction.get("entry_plan_reason", "퀀트조건식 눌림 지정가 매수")
        else:
            plan = self.request_dante_entry_plan(code, prediction)
            plan_ok, plan_reason = self.validate_entry_plan(prediction, plan)
        if not plan_ok:
            watch_started = self.start_risk_too_wide_watch(code, prediction, plan, plan_reason)
            if code in self.risk_too_wide_watchlist and not watch_started and not self.is_risk_too_wide_plan_rejection(plan_reason):
                self.risk_too_wide_watchlist.pop(code, None)
            logger.info("[매수 제외] %s AI 지정가 계획 거절: %s", code, plan_reason)
            self.append_trade_log(
                "buy_skip",
                code=code,
                name=prediction.get("name", ""),
                side="buy",
                quantity=0,
                current_price=prediction.get("current_price", ""),
                score=prediction.get("score", ""),
                model_name=plan.get("model_name", prediction.get("model_name", "DanteRule")),
                model_score=plan.get("model_score", prediction.get("model_score", "")),
                model_action=plan.get("model_action", prediction.get("model_action", "")),
                model_target=plan.get("model_target", prediction.get("model_target", "")),
                model_threshold=plan.get("model_threshold", prediction.get("model_threshold", "")),
                reason="AI 지정가 계획 거절",
                message=plan_reason,
                market_regime=prediction.get("market_regime", ""),
                market_gate_action=prediction.get("market_gate_action", ""),
                market_gate_reason=prediction.get("market_gate_reason", ""),
            )
            return
        if code in self.risk_too_wide_watchlist:
            watch = self.risk_too_wide_watchlist.pop(code, {})
            logger.info(
                "[손절폭 재감시 통과] %s best_risk=%.2f%% -> %s",
                code,
                self.parse_float(watch.get("best_risk_pct", 0.0), 0.0) * 100,
                plan_reason,
            )
        prediction.update(plan)
        prediction["entry_plan_reason"] = plan_reason

        self.place_buy_order(code, prediction, ratio=ratio, stage=stage)

    def place_buy_order(self, code, prediction, *, ratio, stage):
        """단테 분할매수 발주.

        stage == 1:
          - A급은 이제 매수하지 않고 감시만 하므로 이 경로는 구형 호환용이다.
        stage == 2 (본진입):
          - 단테 룰 후보 + AI/룰 가격계획이 통과한 지정가로 주문.
        """
        code = self.normalize_code(code)
        current_price = self.parse_int(prediction.get("current_price", 0))
        if current_price <= 0:
            logger.info("[매수 보류] {} 현재가 0".format(code))
            return
        entry_limit_price = self.parse_int(prediction.get("entry_limit_price", 0))
        stop_price = self.parse_int(prediction.get("stop_price", 0))
        take_profit_price = self.parse_int(prediction.get("take_profit_price", 0))
        order_gubun = str(prediction.get("order_gubun", "00") or "00")
        if entry_limit_price <= 0 or stop_price <= 0 or take_profit_price <= 0:
            logger.info("[매수 보류] {} 지정가/손절/익절 계획 부족".format(code))
            return

        deposit = self.get_deposit(force=True)
        position = self.portfolio.get(code)

        unit_cost = max(current_price if order_gubun == "03" else entry_limit_price, 1)

        grade = str(prediction.get("grade", "") or "")
        safe_pullback_entry = prediction.get("plan_source") in ("safe_pullback", QUANT_PLAN_SOURCE) or grade in ("SAFE", QUANT_GRADE)
        pullback_lump_sum = (
            stage == 2
            and (position is None or position.entry_stage == 0)
            and grade in ("A", "B", "AI", "SAFE", QUANT_GRADE)
        )
        sizing_plan = {}

        if stage == 1:
            sizing_plan = self.build_position_size_plan(
                code=code,
                deposit=deposit,
                entry_limit_price=entry_limit_price,
                stop_price=stop_price,
            )
            planned_quantity = self.parse_int(sizing_plan.get("planned_quantity", 0))
            if safe_pullback_entry:
                cash_budget = int(deposit * SAFE_PULLBACK_CASH_RATE * BUY_CASH_BUFFER_RATE)
                planned_quantity = int(cash_budget // unit_cost) if unit_cost > 0 else 0
                sizing_plan = {
                    "planned_quantity": planned_quantity,
                    "reason": "safe_pullback_10pct_cash",
                    "risk_per_share": max(entry_limit_price - stop_price, 0),
                    "risk_budget": cash_budget,
                    "per_trade_risk_budget": cash_budget,
                    "portfolio_risk_budget": cash_budget,
                    "used_portfolio_risk": self.current_open_position_risk(exclude_code=code),
                    "remaining_portfolio_risk": cash_budget,
                    "risk_quantity": planned_quantity,
                    "cash_quantity": planned_quantity,
                    "cash_budget": cash_budget,
                    "order_cash": planned_quantity * unit_cost,
                }
            if planned_quantity <= 0:
                sizing_message = self.format_position_size_plan(sizing_plan)
                logger.info(
                    "[매수 보류] {} 리스크/현금 예산 부족: 단가 {}, 가능 예수금 {}, {}".format(
                        code, unit_cost, deposit, sizing_message
                    )
                )
                self.append_trade_log(
                    "buy_skip",
                    code=code,
                    name=prediction.get("name", ""),
                    side="buy",
                    quantity=0,
                    current_price=current_price,
                    score=prediction.get("score", ""),
                    model_name=prediction.get("model_name", ""),
                    model_score=prediction.get("model_score", ""),
                    model_action=prediction.get("model_action", ""),
                    model_target=prediction.get("model_target", ""),
                    model_threshold=prediction.get("model_threshold", ""),
                    reason="리스크 예산 부족",
                    message="단테 1차 stage 보류, {}".format(sizing_message),
                    market_regime=prediction.get("market_regime", ""),
                    market_gate_action=prediction.get("market_gate_action", ""),
                    market_gate_reason=prediction.get("market_gate_reason", ""),
                )
                return
            order_quantity = max(int(planned_quantity * ratio), 1)
            # 잔여 분(2차분)이 1주 이상 남도록 캡 — 1차에서 전량 다 사버리면 본진입이 무의미.
            order_quantity = min(order_quantity, max(planned_quantity - 1, 1))
        elif pullback_lump_sum:
            # B급(1봉전 돌파만) — 1차/2차 분리 없이 첫 눌림에서 한 번에 본진입(ratio=1.0).
            sizing_plan = self.build_position_size_plan(
                code=code,
                deposit=deposit,
                entry_limit_price=entry_limit_price,
                stop_price=stop_price,
            )
            planned_quantity = self.parse_int(sizing_plan.get("planned_quantity", 0))
            if safe_pullback_entry:
                cash_budget = int(deposit * SAFE_PULLBACK_CASH_RATE * BUY_CASH_BUFFER_RATE)
                planned_quantity = int(cash_budget // unit_cost) if unit_cost > 0 else 0
                sizing_plan = {
                    "planned_quantity": planned_quantity,
                    "reason": "safe_pullback_10pct_cash",
                    "risk_per_share": max(entry_limit_price - stop_price, 0),
                    "risk_budget": cash_budget,
                    "per_trade_risk_budget": cash_budget,
                    "portfolio_risk_budget": cash_budget,
                    "used_portfolio_risk": self.current_open_position_risk(exclude_code=code),
                    "remaining_portfolio_risk": cash_budget,
                    "risk_quantity": planned_quantity,
                    "cash_quantity": planned_quantity,
                    "cash_budget": cash_budget,
                    "order_cash": planned_quantity * unit_cost,
                }
            if planned_quantity <= 0:
                sizing_message = self.format_position_size_plan(sizing_plan)
                logger.info(
                    "[B급 매수 보류] {} 리스크/현금 예산 부족: 단가 {}, 가능 {}, {}".format(
                        code, unit_cost, deposit, sizing_message
                    )
                )
                self.append_trade_log(
                    "buy_skip",
                    code=code,
                    name=prediction.get("name", ""),
                    side="buy",
                    quantity=0,
                    current_price=current_price,
                    score=prediction.get("score", ""),
                    model_name=prediction.get("model_name", "DanteRule"),
                    model_score=prediction.get("model_score", ""),
                    model_action=prediction.get("model_action", ""),
                    model_target=prediction.get("model_target", ""),
                    model_threshold=prediction.get("model_threshold", ""),
                    reason="리스크 예산 부족",
                    message=sizing_message,
                    market_regime=prediction.get("market_regime", ""),
                    market_gate_action=prediction.get("market_gate_action", ""),
                    market_gate_reason=prediction.get("market_gate_reason", ""),
                )
                return
            order_quantity = planned_quantity  # ratio==1.0 이므로 전량
            if safe_pullback_entry:
                order_quantity = max(int(planned_quantity * ratio), 1)
                order_quantity = min(order_quantity, planned_quantity)
            if prediction.get("reason_code") == entry_strategy.READY_REENTRY_PULLBACK:
                order_quantity = max(int(planned_quantity * ratio), 1)
                order_quantity = min(order_quantity, planned_quantity)
        else:
            if position is None:
                logger.info("[2차 매수 보류] {} Position 없음".format(code))
                return
            already_filled = position.quantity
            remaining = max(position.planned_quantity - already_filled, 0)
            if remaining <= 0:
                logger.info(
                    "[2차 매수 보류] {} 잔여 수량 없음 (planned {}, 보유 {})".format(
                        code, position.planned_quantity, already_filled
                    )
                )
                return
            # 본진입 잔여 수량 그대로 매수
            order_quantity = remaining
            planned_quantity = position.planned_quantity

        # 예수금 한 번 더 안전 체크(지정가 기준).
        needed_cash = unit_cost * order_quantity
        if needed_cash < MIN_ORDER_CASH:
            sizing_message = self.format_position_size_plan(sizing_plan)
            logger.info(
                "[{}차 매수 보류] {} 최소 주문금액 미달(needed {}, min {}, {})".format(
                    stage, code, needed_cash, MIN_ORDER_CASH, sizing_message
                )
            )
            self.append_trade_log(
                "buy_skip",
                code=code,
                name=prediction.get("name", ""),
                side="buy",
                quantity=0,
                current_price=current_price,
                score=prediction.get("score", ""),
                model_name=prediction.get("model_name", "DanteRule"),
                model_score=prediction.get("model_score", ""),
                model_action=prediction.get("model_action", ""),
                model_target=prediction.get("model_target", ""),
                model_threshold=prediction.get("model_threshold", ""),
                reason="최소 주문금액 미달",
                message="needed {}, min {}, {}".format(needed_cash, MIN_ORDER_CASH, sizing_message),
                market_regime=prediction.get("market_regime", ""),
                market_gate_action=prediction.get("market_gate_action", ""),
                market_gate_reason=prediction.get("market_gate_reason", ""),
            )
            return
        if needed_cash > deposit:
            adjusted = deposit // unit_cost if unit_cost > 0 else 0
            if adjusted <= 0:
                logger.info(
                    "[{}차 매수 보류] {} 예수금 부족(needed {}, deposit {})".format(
                        stage, code, needed_cash, deposit
                    )
                )
                return
            order_quantity = adjusted
            needed_cash = unit_cost * order_quantity
            if needed_cash < MIN_ORDER_CASH:
                logger.info(
                    "[{}차 매수 보류] {} 예수금 조정 후 최소 주문금액 미달(needed {}, min {})".format(
                        stage, code, needed_cash, MIN_ORDER_CASH
                    )
                )
                return

        send_order_price = 0 if order_gubun == "03" else entry_limit_price
        result = self.send_order("buy", ORDER_SCREEN_NO, 1, code, order_quantity, send_order_price, order_gubun)
        if prediction.get("plan_source") == QUANT_PLAN_SOURCE or grade == QUANT_GRADE:
            reason_label = "퀀트조건식 눌림 매수"
        elif pullback_lump_sum and grade == "A":
            reason_label = "Dante A-watch pullback entry"
        elif safe_pullback_entry:
            reason_label = "Safe pullback limit entry"
        elif grade == "AI":
            reason_label = "AI 후보 지정가 매수"
        elif grade == "B":
            reason_label = "단테 B급 일괄 매수"
        else:
            reason_label = "단테 {}차 매수 (A급)".format(stage)
        self.order_context[code] = {
            "side": "buy",
            "name": prediction.get("name", ""),
            "stage": stage,
            "ratio": ratio,
            "grade": grade,
            "planned_quantity": planned_quantity,
            "score": prediction.get("score", 0.0),
            "spread_rate": prediction.get("spread_rate", 0.0),
            "chejan_strength": prediction.get("chejan_strength", 0.0),
            "volume_speed": prediction.get("volume_speed", 0.0),
            "model_name": prediction.get("model_name", "DanteRule"),
            "model_score": prediction.get("model_score", ""),
            "model_action": prediction.get("model_action", ""),
            "model_target": prediction.get("model_target", ""),
            "model_threshold": prediction.get("model_threshold", ""),
            "capture_price": prediction.get("capture_price", ""),
            "safe_target_price": prediction.get("safe_target_price", ""),
            "entry_limit_price": entry_limit_price,
            "order_gubun": order_gubun,
            "stop_price": stop_price,
            "take_profit_price": take_profit_price,
            "risk_reward": prediction.get("risk_reward", ""),
            "max_risk_pct": prediction.get("max_risk_pct", ""),
            "position_sizing": sizing_plan.get("reason", ""),
            "risk_per_share": sizing_plan.get("risk_per_share", ""),
            "risk_budget": sizing_plan.get("risk_budget", ""),
            "used_portfolio_risk": sizing_plan.get("used_portfolio_risk", ""),
            "portfolio_risk_budget": sizing_plan.get("portfolio_risk_budget", ""),
            "expiry_seconds": prediction.get("expiry_seconds", ENTRY_PLAN_EXPIRY_SECONDS),
            "plan_source": prediction.get("plan_source", ""),
            "reason": "{} ({})".format(reason_label, prediction.get("reason", "")),
            # cancel_stale_buy_orders 가 만료 점검에 사용. order_no 는 chejan "접수"
            # 이벤트가 도착할 때 채워진다(키움이 send_order 응답으로 즉시 주는 게 아님).
            "placed_at": time.time(),
            "order_no": "",
        }
        self.append_trade_log(
            "buy_order",
            code=code,
            name=prediction.get("name", ""),
            side="buy",
            order_type="시장가" if order_gubun == "03" else "지정가",
            order_result=result,
            quantity=order_quantity,
            order_price=send_order_price,
            current_price=current_price,
            entry_price=entry_limit_price,
            target_price=take_profit_price,
            score=prediction.get("score", 0.0),
            model_name=prediction.get("model_name", "DanteRule"),
            model_score=prediction.get("model_score", ""),
            model_action=prediction.get("model_action", ""),
            model_target=prediction.get("model_target", ""),
            model_threshold=prediction.get("model_threshold", ""),
            reason_code=prediction.get("reason_code", ""),
            reason=reason_label,
            plan_source=prediction.get("plan_source", ""),
            capture_price=prediction.get("capture_price", ""),
            pullback_pct=prediction.get("pullback_pct", ""),
            chejan_strength=prediction.get("chejan_strength", ""),
            message="{}, planned {}, ratio {:.2f}, limit {}, stop {}, target {}, {}, {}".format(
                reason_label,
                planned_quantity,
                ratio,
                entry_limit_price,
                stop_price,
                take_profit_price,
                self.format_position_size_plan(sizing_plan),
                prediction.get("entry_plan_reason", prediction.get("reason", "")),
            ),
            market_regime=prediction.get("market_regime", ""),
            market_gate_action=prediction.get("market_gate_action", ""),
            market_gate_reason=prediction.get("market_gate_reason", ""),
        )
        if result == 0:
            self.order_prices[code] = entry_limit_price
            self.entry_times[code] = time.time()
            self.highest_prices[code] = current_price
            self.pending_order_codes.add(code)
            self.bought_codes.add(code)
            self.best[code] = take_profit_price
            self.target_returns[code] = self.estimate_net_target_return(entry_limit_price, take_profit_price)
            self.save_best()
            if prediction.get("reason_code") == entry_strategy.READY_REENTRY_PULLBACK:
                self.dante_reentry_watchlist.pop(code, None)
            if safe_pullback_entry:
                self.clear_monitoring_stock(code, "매수 주문 접수")
            if pullback_lump_sum and grade == "A":
                self.dante_a_watchlist.pop(code, None)

            # Position 채움. 1차 발주 시점에 planned_quantity / pullback_window_deadline 셋업.
            position = self.portfolio.get_or_create(code, name=prediction.get("name", ""))
            position.entry_price = entry_limit_price
            position.stop_price = stop_price
            position.target_price = take_profit_price
            position.target_return = self.estimate_net_target_return(entry_limit_price, take_profit_price)
            position.entry_time = position.entry_time or time.time()
            position.update_highest(current_price)
            position.pending_buy = True
            position.bought_today = True
            position.order_context = dict(self.order_context.get(code, {}))
            if grade and not position.breakout_grade:
                position.breakout_grade = grade
            if stage == 1:
                position.planned_quantity = planned_quantity
                position.r_unit_pct = exit_strategy.R_UNIT_PCT
                # 윈도우는 1차 체결 시 정확히 잡지만, 발주 시점에도 미리 한 번 세팅.
                position.pullback_window_deadline = time.time() + entry_strategy.PULLBACK_WINDOW_MAX_SECONDS
                position.entry1_time = position.entry1_time or time.time()
            elif pullback_lump_sum:
                # B급은 1차+2차를 한 번에 매수했으므로 분할 윈도우 없음, planned == 전량.
                position.planned_quantity = planned_quantity
                position.r_unit_pct = exit_strategy.R_UNIT_PCT
                position.entry1_time = position.entry1_time or time.time()
                position.entry2_time = position.entry2_time or time.time()
                position.pullback_window_deadline = 0.0
            else:
                position.entry2_time = position.entry2_time or time.time()

            self.register_realtime_stock(code)
            # 발주 직후 portfolio_state 디스크 동기화 — planned_quantity / pullback 윈도우 등
            # 1차 발주 단계에서만 세팅되는 필드들을 보존해야 다음 부팅 시 2차 본진입 평가가 가능.
            self.save_portfolio_state()
            logger.info(
                "[{} 매수 주문] {} 수량 {}/{} 현재가 {} 단가 {} 등급={} 사유 {}".format(
                    reason_label,
                    prediction.get("name", ""),
                    order_quantity,
                    planned_quantity,
                    entry_limit_price,
                    unit_cost,
                    grade or "?",
                    prediction.get("reason", ""),
                )
            )
        else:
            logger.error(
                "[{} 매수 실패] {} SendOrder 결과 {}".format(
                    reason_label,
                    code,
                    result,
                )
            )

    def cancel_stale_buy_orders(self):
        """매수 patient 지정가 중 expiry_seconds 가 지난 미체결을 SendOrder 로 취소한다.

        취소가 발사되면 키움이 chejan "취소" 이벤트를 보내고, _on_receive_chejan 의
        해당 분기가 pending_order_codes / order_context / portfolio.pending_buy 를
        정리한다. 이 메서드는 발주만 보낸다. 같은 종목에 두 번 취소가 발사되지 않도록
        ctx 에 ``cancel_requested_at`` 마킹 후 다음 호출에서 스킵한다.
        """
        now = time.time()
        for code in list(self.pending_order_codes):
            # 매도 미체결은 기존 큐가 따로 처리한다.
            if code in self.pending_sell_order_codes:
                continue
            ctx = self.order_context.get(code)
            if not isinstance(ctx, dict):
                continue
            if ctx.get("side") != "buy":
                continue
            order_no = str(ctx.get("order_no", "") or "")
            placed_at = float(ctx.get("placed_at", 0) or 0)
            expiry = float(ctx.get("expiry_seconds", ENTRY_PLAN_EXPIRY_SECONDS) or ENTRY_PLAN_EXPIRY_SECONDS)
            if not order_no or placed_at <= 0 or expiry <= 0:
                continue
            elapsed = now - placed_at
            if elapsed < expiry:
                continue
            # 이미 한 번 취소를 발사한 주문은 재발사 금지(키움 chejan 응답 지연 대비).
            cancel_requested_at = float(ctx.get("cancel_requested_at", 0) or 0)
            if cancel_requested_at > 0 and now - cancel_requested_at < 10.0:
                continue

            result = self.send_order(
                "buy_cancel",
                ORDER_SCREEN_NO,
                3,
                code,
                0,
                0,
                "00",
                order_no,
            )
            ctx["cancel_requested_at"] = now
            logger.info(
                "[매수 미체결 취소] %s order_no=%s elapsed=%.0fs expiry=%.0fs result=%s",
                code, order_no, elapsed, expiry, result,
            )
            try:
                self.append_trade_log(
                    "buy_cancel",
                    code=code,
                    name=ctx.get("name", ""),
                    side="buy",
                    order_no=order_no,
                    order_result=result,
                    order_price=ctx.get("entry_limit_price", ""),
                    entry_price=ctx.get("entry_limit_price", ""),
                    target_price=ctx.get("take_profit_price", ""),
                    score=ctx.get("score", ""),
                    model_name=ctx.get("model_name", ""),
                    model_score=ctx.get("model_score", ""),
                    model_action=ctx.get("model_action", ""),
                    model_target=ctx.get("model_target", ""),
                    model_threshold=ctx.get("model_threshold", ""),
                    reason="buy_order_expired",
                    message="elapsed {:.0f}s > expiry {:.0f}s".format(elapsed, expiry),
                )
            except Exception as exc:  # 로그 실패는 동작 영향 없게 swallow.
                logger.warning("[매수 미체결 취소] trade_log 기록 실패 %s %s", code, exc)

    def register_realtime_stock(self, code):
        code = self.normalize_code(code)
        if code in self.realtime_registered_codes:
            return

        screen_no = self.get_realtime_screen_no()
        fids = ";".join([
            get_fid("체결시간"),
            get_fid("현재가"),
            get_fid("고가"),
            get_fid("시가"),
            get_fid("저가"),
            get_fid("(최우선)매도호가"),
            get_fid("(최우선)매수호가"),
            get_fid("누적거래량"),
            get_fid("체결강도"),  # 퀀트조건식 눌림 매수 게이트와 청산 약화 판정에 사용
            "121",  # 매도호가 총잔량
            "125",  # 매수호가 총잔량
        ])
        opt_type = "0" if screen_no not in self.realtime_code_screens.values() else "1"
        self.set_real_reg(screen_no, code, fids, opt_type)
        self.realtime_registered_codes.add(code)
        self.realtime_code_screens[code] = screen_no
        logger.info("[실시간 등록] %s screen=%s fids=%s", code, screen_no, fids)

    def register_realtime_indices(self):
        """KOSPI(001)/KOSDAQ(101) 업종지수 실시간 등록 — 1회만 호출.

        종목용 실시간과 다른 스크린(INDEX_REALTIME_SCREEN_NO)을 쓰고, 콜백에서는
        ``_on_receive_real_data`` 의 ``"업종지수"`` 분기가 ``self.market_state.update()``
        로 흘려준다. 키움 OpenAPI 의 SetRealReg 는 종목코드 자리에 업종코드(001/101)를
        받는다. 등록 실패/지연 시 cache 가 비고 → ``regime=unknown`` → entry_strategy 가
        neutral 로 fallback 하므로 행동 변화가 없다.
        """
        if self.index_realtime_registered:
            return
        codes = ";".join([KOSPI_CODE, KOSDAQ_CODE])
        fids = ";".join([
            get_fid("현재가"),
            get_fid("시가"),
            get_fid("고가"),
            get_fid("저가"),
            get_fid("체결시간"),
        ])
        # opt_type "0" = 새 등록(스크린이 종목과 분리되어 있으므로 안전).
        self.set_real_reg(INDEX_REALTIME_SCREEN_NO, codes, fids, "0")
        self.index_realtime_registered = True
        logger.info("[매크로] KOSPI/KOSDAQ 업종지수 실시간 등록 (screen %s)", INDEX_REALTIME_SCREEN_NO)

    def get_realtime_screen_no(self):
        screen_offset = len(self.realtime_registered_codes) // REALTIME_CODES_PER_SCREEN
        return str(int(REALTIME_SCREEN_NO) + screen_offset).zfill(4)

    def score_exit_timing(self, code, current_price):
        """단테 R-multiple 하이브리드 청산 평가."""
        code = self.normalize_code(code)
        position = self.portfolio.get(code)
        entry_price = position.entry_price if position is not None and position.entry_price > 0 else 0
        if not entry_price:
            entry_price = self.parse_int(self.order_prices.get(code, 0))
        if not entry_price:
            for balance in self.cached_balance:
                if self.normalize_code(balance[0]) == code:
                    fallback = self.parse_int(balance[3])
                    if fallback > 0:
                        entry_price = fallback
                        self.order_prices[code] = fallback
                    break
        if entry_price and (position is None or position.entry_price != entry_price):
            if position is None:
                position = self.portfolio.get_or_create(code)
            position.entry_price = entry_price

        if self.current_hhmmss() >= OPENING_FORCE_EXIT:
            return {
                "action": "sell",
                "qty_ratio": 1.0,
                "reason": "장 마감 직전 강제 청산({})".format(OPENING_FORCE_EXIT),
            }
        if not entry_price or position is None:
            return {"action": "hold", "qty_ratio": 0.0, "reason": "진입가/Position 정보 부족"}

        order_context = getattr(position, "order_context", {}) or {}
        is_quant_position = (
            getattr(position, "breakout_grade", "") == QUANT_GRADE
            or order_context.get("plan_source") == QUANT_PLAN_SOURCE
        )
        if is_quant_position:
            quant_exit = self.quant_strategy.evaluate_exit(
                entry_price=entry_price,
                current_price=current_price,
            )
            if quant_exit.action == "sell":
                return {
                    "action": quant_exit.action,
                    "qty_ratio": quant_exit.qty_ratio,
                    "reason": quant_exit.reason,
                    "mark_partial_taken": False,
                }

        # Position 누락 필드 보정.
        now_ts = time.time()
        if not position.entry_time:
            position.entry_time = now_ts
        if not position.entry1_time:
            position.entry1_time = position.entry_time
        if position.r_unit_pct <= 0:
            position.r_unit_pct = exit_strategy.R_UNIT_PCT
        if position.stop_price <= 0 and position.entry_price > 0:
            position.stop_price = int(position.entry_price * (1 - position.r_unit_pct))
        if position.breakout_high <= 0:
            position.breakout_high = position.entry_price
        if current_price > 0:
            position.update_highest(current_price)
            position.update_breakout_high(current_price)
            self.highest_prices[code] = position.highest_price

        # 5분봉 캐시 갱신(보유 종목은 항상 갱신 시도).
        self.refresh_five_min_indicators(code)

        ticks = self.realtime_ticks.get(code, [])
        chejan_strength = float(ticks[-1].get("chejan_strength", 0.0)) if ticks else 0.0

        ctx = exit_strategy.ExitContext(
            position=position,
            current_price=current_price,
            chejan_strength=chejan_strength,
            minute_bars=self.minute_aggregator.all_bars(code),
            five_min_ind=self.five_min_cache.get(code),
            now_ts=now_ts,
        )
        decision = exit_strategy.evaluate_exit(ctx)

        # BE 스탑 이동 플래그를 즉시 반영.
        if decision.update_stop_to_be and position.entry_price > 0:
            new_stop = position.entry_price
            if new_stop > position.stop_price:
                position.stop_price = new_stop
                logger.info(
                    "[BE 스탑 이동] {} stop {} → {} (현재가 {})".format(
                        code, position.stop_price, new_stop, current_price
                    )
                )

        return {
            "action": decision.action,
            "qty_ratio": decision.qty_ratio,
            "reason": decision.reason,
            "mark_partial_taken": decision.mark_partial_taken,
        }

    def check_sell_signal(self, code, current_price):
        code = self.normalize_code(code)
        position = self.portfolio.get(code)
        # 매도 미체결이 진행 중인 종목은 새 매도 판단을 보류.
        if (position is not None and position.pending_sell) or code in self.pending_sell_order_codes:
            return
        # 보유도 추적도 안 하는 종목이면 매도 신호 자체가 의미 없음
        if (position is None or not position.is_holding()) and code not in self.holding_codes and code not in self.best:
            return

        exit_decision = self.score_exit_timing(code, current_price)
        action = exit_decision.get("action", "hold")

        if action == "sell":
            self.place_sell_order(code, 0, "03", exit_decision.get("reason", "매도 신호"))
            return

        if action == "partial_sell":
            qty_ratio = float(exit_decision.get("qty_ratio", 0.5))
            if position is None or position.quantity <= 0:
                return
            partial_quantity = max(int(position.quantity * qty_ratio), 1)
            partial_quantity = min(partial_quantity, position.quantity - 1)
            if partial_quantity <= 0:
                return
            # 부분 익절 발사 직전에 partial_taken 마킹 → 동일 종목에서 partial 이 두 번 발사되지 않게.
            if exit_decision.get("mark_partial_taken"):
                position.partial_taken = True
            self.place_sell_order(
                code, 0, "03", exit_decision.get("reason", "부분 익절"),
                desired_quantity=partial_quantity,
            )

    def get_balance_current_price(self, code):
        for balance in self.cached_balance:
            if self.normalize_code(balance[0]) == code:
                return balance[5]
        return 0

    def _lookup_balance_quantity(self, code):
        code = self.normalize_code(code)
        chejan_quantity = self.parse_int(self.position_quantities.get(code, 0))
        chejan_available = self.parse_int(self.available_quantities.get(code, 0))
        for balance in self.cached_balance:
            if self.normalize_code(balance[0]) == code:
                balance_quantity = self.parse_int(balance[2])
                balance_available = self.parse_int(balance[7])
                merged_quantity = max(chejan_quantity, balance_quantity)
                merged_available = chejan_available if chejan_available > 0 else balance_available
                return merged_quantity, merged_available
        return chejan_quantity, chejan_available

    def check_open_positions(self):
        self.update_account_status(force=True)
        self._cleanup_stale_best()
        self.process_pending_sell_intents()
        codes_to_check = self.portfolio.codes() | set(self.best.keys()) | set(self.holding_codes)
        codes_to_check = {c for c in codes_to_check if c}
        for code in codes_to_check:
            self.register_realtime_stock(code)
            last_tick = self.realtime_ticks.get(code, [{}])[-1]
            current_price = last_tick.get("close") or self.get_balance_current_price(code)
            if current_price:
                self.check_sell_signal(code, current_price)
        # 매도 평가에서 BE 스탑 이동/partial_taken/breakout_high 갱신이 일어나므로,
        # 한 사이클이 끝나면 portfolio_state 를 디스크에 동기화한다.
        self.save_portfolio_state()

        # [임시] Portfolio dataclass 마이그레이션 1단계 검증.
        # read 경로를 portfolio 기반으로 옮기기 전에 dict와 portfolio가 같은 정보를 갖는지 확인한다.
        # 1일 운용 후 [정합성] warning이 한 건도 없으면 안전하게 다음 단계 진행 가능.
        # read 경로 변환이 끝나면 이 호출과 _assert_portfolio_consistent 메서드를 함께 제거.
        try:
            self._assert_portfolio_consistent()
        except Exception as e:
            logger.warning("[정합성 검증 오류] %s", e)

    def _assert_portfolio_consistent(self):
        """portfolio Position과 기존 dict/set의 정보가 일치하는지 점검한다(임시).

        값이 다르면 [정합성] warning을 남긴다. 운용 도중 한 건이라도 발견되면
        write 경로 어디선가 한쪽만 갱신되고 있다는 뜻이므로 다음 단계로 넘어가면 안 된다.
        """
        # 1) dict 기준 종목들이 portfolio에 모두 존재하고 값이 같은지 확인
        tracked_codes = (
            set(self.holding_codes)
            | set(self.pending_order_codes)
            | set(self.best.keys())
        )
        for code in tracked_codes:
            if not code:
                continue
            position = self.portfolio.get(code)
            if position is None:
                logger.warning("[정합성] %s portfolio Position 누락 (holding=%s pending=%s best=%s)",
                               code,
                               code in self.holding_codes,
                               code in self.pending_order_codes,
                               code in self.best)
                continue

            dict_quantity = self.parse_int(self.position_quantities.get(code, 0))
            if position.quantity != dict_quantity:
                logger.warning("[정합성] %s quantity 불일치 portfolio=%s dict=%s",
                               code, position.quantity, dict_quantity)

            dict_available = self.parse_int(self.available_quantities.get(code, 0))
            if position.available_quantity != dict_available:
                logger.warning("[정합성] %s available_quantity 불일치 portfolio=%s dict=%s",
                               code, position.available_quantity, dict_available)

            dict_entry = self.parse_int(self.order_prices.get(code, 0))
            if position.entry_price != dict_entry:
                logger.warning("[정합성] %s entry_price 불일치 portfolio=%s dict=%s",
                               code, position.entry_price, dict_entry)

            dict_target = self.parse_int(self.best.get(code, 0))
            if position.target_price != dict_target:
                logger.warning("[정합성] %s target_price 불일치 portfolio=%s dict=%s",
                               code, position.target_price, dict_target)

            dict_highest = self.parse_int(self.highest_prices.get(code, 0))
            if position.highest_price != dict_highest:
                logger.warning("[정합성] %s highest_price 불일치 portfolio=%s dict=%s",
                               code, position.highest_price, dict_highest)

            dict_target_return = self.target_returns.get(code, 0.0)
            if isinstance(dict_target_return, (int, float)):
                if abs(position.target_return - float(dict_target_return)) > 1e-9:
                    logger.warning("[정합성] %s target_return 불일치 portfolio=%s dict=%s",
                                   code, position.target_return, dict_target_return)

            dict_pending_buy = code in self.pending_order_codes and code not in self.pending_sell_order_codes
            if position.pending_buy != dict_pending_buy:
                logger.warning("[정합성] %s pending_buy 불일치 portfolio=%s dict=%s",
                               code, position.pending_buy, dict_pending_buy)

            dict_pending_sell = code in self.pending_sell_order_codes
            if position.pending_sell != dict_pending_sell:
                logger.warning("[정합성] %s pending_sell 불일치 portfolio=%s dict=%s",
                               code, position.pending_sell, dict_pending_sell)

            dict_bought_today = code in self.bought_codes
            if position.bought_today != dict_bought_today:
                logger.warning("[정합성] %s bought_today 불일치 portfolio=%s dict=%s",
                               code, position.bought_today, dict_bought_today)

        # 2) portfolio에는 있지만 어느 dict에도 없는 유령 Position 검출
        portfolio_only = self.portfolio.codes() - tracked_codes
        for code in portfolio_only:
            position = self.portfolio.get(code)
            logger.warning("[정합성] %s portfolio 유령 (qty=%s entry=%s pending_buy=%s pending_sell=%s)",
                           code, position.quantity, position.entry_price,
                           position.pending_buy, position.pending_sell)

    def check_pending_sells(self):
        # 실시간 슬롯에서 매 틱마다 동기 HTTP를 부르지 않도록, 일정 주기로 모아서 매도 판단을 수행한다.
        # 매도 의도 큐도 함께 재시도해 매매가능수량이 늦게 갱신되는 케이스를 빠르게 회수한다.
        try:
            self.process_pending_sell_intents()
        except Exception as e:
            logger.error("[매도 의도 처리 오류] {}".format(e))

        # portfolio 기반 조회. 보유/추적 종목 모두 포함.
        codes_to_check = self.portfolio.codes() | set(self.best.keys()) | set(self.holding_codes)
        for code in codes_to_check:
            if not code:
                continue
            position = self.portfolio.get(code)
            if (position is not None and position.is_pending()) or code in self.pending_order_codes:
                continue
            ticks = self.realtime_ticks.get(code, [])
            if not ticks:
                continue
            current_price = ticks[-1].get("close")
            if not current_price:
                continue
            try:
                self.check_sell_signal(code, current_price)
            except Exception as e:
                logger.error("[매도 판단 오류] {} {}".format(code, e))

    def _cleanup_stale_best(self):
        stale = [
            code for code in list(self.best.keys())
            if code
            and code not in self.holding_codes
            and code not in self.pending_order_codes
            and self.parse_int(self.position_quantities.get(code, 0)) <= 0
        ]
        if not stale:
            return
        for code in stale:
            self._discard_position(code, save=False)
        self.save_best()
        logger.info("[best 정리] 보유/미체결 없음 종목 제거: {}".format(stale))

    def place_sell_order(self, code, order_price, order_gubun, reason, *, desired_quantity=None):
        """매도 주문 발주.

        desired_quantity:
          - None: 전량(매매가능수량 전체) 매도
          - int > 0: 해당 수량만 매도 (부분 익절). 가용 수량보다 크면 가용으로 캡.
        """
        code = self.normalize_code(code)
        if code in self._selling_codes:
            logger.warning("[매도 중복 차단] {} 진행 중인 매도 있음".format(code))
            return
        if code in self.pending_sell_order_codes:
            logger.warning("[매도 중복 차단] {} 미체결 매도 주문 존재".format(code))
            return
        self._selling_codes.add(code)
        try:
            self._do_place_sell_order(code, order_price, order_gubun, reason, desired_quantity=desired_quantity)
        finally:
            self._selling_codes.discard(code)

    def _do_place_sell_order(self, code, order_price, order_gubun, reason, *, desired_quantity=None):
        chejan_quantity = self.parse_int(self.position_quantities.get(code, 0))
        balance_quantity, available_quantity = self._lookup_balance_quantity(code)
        balance_quantity = self.parse_int(balance_quantity)
        available_quantity = self.parse_int(available_quantity)

        if chejan_quantity <= 0 and balance_quantity <= 0:
            self.update_account_status(force=True)
            balance_quantity, available_quantity = self._lookup_balance_quantity(code)
            balance_quantity = self.parse_int(balance_quantity)
            available_quantity = self.parse_int(available_quantity)

        held_quantity = max(chejan_quantity, balance_quantity)
        sell_quantity = available_quantity
        if desired_quantity is not None and desired_quantity > 0:
            sell_quantity = min(int(desired_quantity), available_quantity)

        # 매매가능수량이 아직 갱신되지 않은 경우, 메인 스레드를 블로킹하지 않도록 sleep 없이
        # 매도 의도만 큐에 등록하고 sell_check_timer / process_pending_sell_intents가 재시도하게 둔다.
        if sell_quantity <= 0:
            stale = (
                chejan_quantity <= 0
                and balance_quantity <= 0
                and available_quantity <= 0
                and code not in self.pending_order_codes
            )
            if self.should_log_sell_skip(code):
                logger.info("[매도 보류] {} 매매가능수량 없음 (chejan {}, 잔고 {}, 가능 {}){}".format(
                    code, chejan_quantity, balance_quantity, available_quantity,
                    " - best 정리" if stale else ""))
                self.append_trade_log(
                    "sell_skip",
                    code=code,
                    name=self.get_code_name(code),
                    side="sell",
                    quantity=sell_quantity,
                    order_price=order_price,
                    entry_price=self.order_prices.get(code, ""),
                    target_price=self.best.get(code, ""),
                    reason=reason,
                    message="매매가능수량 없음 chejan={} 잔고={} 가능={}".format(
                        chejan_quantity, balance_quantity, available_quantity),
                )
            if stale:
                self._discard_position(code)
            elif held_quantity > 0:
                self.queue_sell_intent(code, reason, order_price, order_gubun)
            return

        entry_price = self.order_prices.get(code)
        hold_seconds = ""
        profit_rate = ""
        if code in self.entry_times:
            hold_seconds = time.time() - self.entry_times[code]
        if entry_price:
            last_price = self.realtime_ticks.get(code, [{}])[-1].get("close", order_price)
            if last_price:
                gross_profit_rate = last_price / entry_price - 1
                profit_rate = self.gross_to_net_return(gross_profit_rate)
        result = self.send_order("sell", ORDER_SCREEN_NO, 2, code, sell_quantity, order_price, order_gubun)
        self.order_context[code] = {
            "side": "sell",
            "name": self.get_code_name(code),
            "reason": reason,
            "entry_price": entry_price or "",
            "target_price": self.best.get(code, ""),
            "hold_seconds": hold_seconds,
            "profit_rate": profit_rate,
        }
        self.append_trade_log(
            "sell_order",
            code=code,
            name=self.get_code_name(code),
            side="sell",
            order_type="시장가" if order_gubun == "03" else "지정가",
            order_result=result,
            quantity=sell_quantity,
            order_price=order_price,
            entry_price=entry_price or "",
            target_price=self.best.get(code, ""),
            reason=reason,
            hold_seconds=hold_seconds,
            profit_rate=profit_rate,
        )
        if result == 0:
            self.pending_order_codes.add(code)
            self.pending_sell_order_codes.add(code)
            self.pending_sell_intents.pop(code, None)
            logger.info("[매도 주문] {} {} 수량 {} 가격 {} 구분 {}".format(code, reason, sell_quantity, order_price, order_gubun))
        else:
            logger.error("[매도 실패] {} SendOrder 결과 {}".format(code, result))
            self.queue_sell_intent(code, reason, order_price, order_gubun)

    def predict_stock(self, code):
        code = self.normalize_code(code)
        position = self.portfolio.get(code)
        if (
            position is not None
            and getattr(position, "breakout_grade", "") == "SAFE"
            and getattr(position, "entry_stage", 0) == 1
        ):
            return self.score_safe_pullback_second_entry(code, position)
        if code in self.monitoring_dict:
            return self.score_safe_pullback_trade(code)
        return self.score_opening_trade(code)


def _log_quant_condition_startup_banner():
    """퀀트조건식 운용 파라미터를 시작 시 로그에 한 번 출력한다."""
    logger.info("=" * 78)
    logger.info(
        "[%s] rule=%s | 조건식='%s' | 수식=%s",
        TRADE_LOG_STRATEGY_NAME,
        TRADE_LOG_RULE_VERSION,
        CONDITION_NAME,
        TRADE_LOG_CONDITION_FORMULA,
    )
    logger.info("[조건식 상세] %s", TRADE_LOG_CONDITION_RULES)
    logger.info(
        "[매수룰] 조건편입 즉시 SetRealReg -> 첫 실시간 체결가를 포착가로 저장 -> 현재가가 포착가 대비 -%.2f%% 이상 눌리고 체결강도 %.0f 이상이면 지정가 매수",
        QUANT_ENTRY_PULLBACK_PCT * 100,
        QUANT_ENTRY_CHEJAN_STRENGTH_MIN,
    )
    logger.info(
        "[매도룰] 매수가 대비 +%.2f%% 전량 익절 / -%.2f%% 전량 손절",
        QUANT_TAKE_PROFIT_PCT * 100,
        QUANT_STOP_LOSS_PCT * 100,
    )
    logger.info("[안전장치] 동시보유 %d, 일일매수상한 %d, 강제청산 %d, 주문간격 %.2fs(초당 5회 이하), AI서버=%s, 조건식학습=%s(%s), shadow=%s(%s)",
                MAX_CONCURRENT_POSITIONS,
                MAX_DAILY_BUY_COUNT,
                OPENING_FORCE_EXIT,
                ORDER_REQUEST_INTERVAL_SECONDS,
                "ON" if AI_SERVER_ENABLED else "OFF",
                "ON" if DANTE_TRAINING_DATA_ENABLED else "OFF",
                DANTE_TRAINING_CSV,
                "ON" if DANTE_SHADOW_TRAINING_DATA_ENABLED else "OFF",
                DANTE_SHADOW_TRAINING_CSV)
    logger.info("=" * 78)


def main():
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()

    _log_quant_condition_startup_banner()

    my_deposit = kiwoom.get_deposit()
    logger.info("남은 예수금 : %s", my_deposit)

    kiwoom.load_best()
    # portfolio_state 는 잔고 TR 호출 전에 미리 로드. 같은 거래일 내 재시작이면
    # entry_stage / planned_quantity / stop_price 등 전략 필드를 보존하고, 잔고 TR 응답이
    # quantity / entry_price 등 휘발성 필드만 덮어쓰게 한다.
    kiwoom.load_portfolio_state()
    kiwoom.reset_daily_state()
    kiwoom.update_account_status()
    logger.info("현재가지고 있는 종목: {}".format(kiwoom.get_balance()))
    logger.info("미체결 종목: {}".format(kiwoom.pending_order_codes))

    kiwoom._cleanup_stale_best()
    startup_codes = set(kiwoom.best.keys()) | set(kiwoom.holding_codes)
    for code in startup_codes:
        if code:
            kiwoom.register_realtime_stock(code)

    kiwoom.check_open_positions()
    kiwoom.position_check_timer.start(POSITION_CHECK_INTERVAL_MS)
    kiwoom.sell_check_timer.start(SELL_CHECK_INTERVAL_MS)
    kiwoom.buy_expiry_timer.start(BUY_ORDER_EXPIRY_CHECK_INTERVAL_MS)

    # 매크로 dry-run 게이트용 KOSPI/KOSDAQ 실시간 지수 — 조건검색 시작 전에 1회 등록.
    kiwoom.register_realtime_indices()

    if not kiwoom.start_realtime_condition(CONDITION_NAME):
        logger.error("실시간 조건검색을 시작하지 못했습니다. 조건식 설정을 확인해주세요.")

    app.exec_()


if __name__ == "__main__":
    main()
