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
from market_state import KOSDAQ_CODE, KOSPI_CODE, MarketStateCache
from portfolio import LoadedPortfolioState, Position, PortfolioState
from logging_setup import setup_logging
from fid_codes import FID_CODES, FID_NAME_TO_CODE, get_fid
from training_recorder import (
    TrainingRecorderMixin,
    # 모듈 상수 re-export — 외부 테스트가 main.X 로 직접 접근하므로 호환 유지
    TRAINING_DATA_ENABLED,
    TRAINING_DATA_DIR,
    TRAINING_ENTRY_CSV,
    TRADE_LOG_CSV,
    TRAINING_SAMPLE_COOLDOWN_SECONDS,
    TRAINING_LABEL_HORIZONS,
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
    ENTRY_FEATURE_NAMES,
    TRAINING_ENTRY_FIELDS,
    TRADE_LOG_FIELDS,
)


logger = setup_logging()

# ===== 단테조건식 추세전략 =====
# 영웅문에 저장된 조건식 이름과 정확히 일치해야 한다. 단테조건식.xls 의 본 조건은
# 5분봉 BB(45,2)/BB(55,2) 및 Envelope(13,2.5)/Envelope(22,2.5) 동시 상향돌파 +
# 일거래량 5만 + 체결강도 100% 게이트로 구성된다. 영웅문에서 저장된 실제 이름이
# 다르다면 이 한 줄만 수정한다.
CONDITION_NAME = "단테떡상이"
CONDITION_SCREEN_NO = "0150"
REALTIME_SCREEN_NO = "0160"
# KOSPI/KOSDAQ 업종지수 실시간용 별도 스크린(종목 실시간과 충돌 방지).
INDEX_REALTIME_SCREEN_NO = "0170"
ORDER_SCREEN_NO = "0001"
# 단테 룰 기반 전환 직후에는 AI 서버/구식 학습 트랙(entry_training.csv) 의 의사결정을
# 따르지 않는다. 새 전략 데이터가 충분히 쌓일 때까지 두 트랙 모두 비활성화한다.
AI_SERVER_ENABLED = False
AI_SERVER_URL = "http://127.0.0.1:8000"
AI_SERVER_TIMEOUT_SECONDS = 0.35
# 학습 트랙(구학습 + 단테 + shadow) 의 enable 플래그/CSV 경로/필드 정의는
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
OPENING_BUY_START = 90500
OPENING_BUY_END = 143000
OPENING_FORCE_EXIT = 151500
# 실시간 틱 버퍼 크기 / 최소 틱 수 (단테 1차 게이트가 사용)
OPENING_MIN_TICKS = entry_strategy.DANTE_MIN_TICKS
OPENING_TICK_LIMIT = 40
# 호가 스프레드 상한
OPENING_MAX_SPREAD_RATE = entry_strategy.MAX_SPREAD_RATE
# 손절/시간 손절 등은 exit_strategy 모듈로 이전했다. 호환을 위해 alias 만 남긴다.
OPENING_STOP_LOSS_RATE = -exit_strategy.R_UNIT_PCT  # -1R
OPENING_MAX_HOLD_SECONDS = exit_strategy.EXIT_TIME_LIMIT_SECONDS                         
# 단테 전략은 1차 추격(소량) + 2차 본진입(본물량) 분할매수 방식이라 동시 보유 종목을
# 보수적으로 1개로 시작한다. 검증 후 점진적으로 늘린다.
MAX_CONCURRENT_POSITIONS = 1
MAX_DAILY_BUY_COUNT = 20
CONDITION_PROCESS_INTERVAL_MS = 2000
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
# 학습/거래 로그 필드 정의(ENTRY_FEATURE_NAMES, TRAINING_ENTRY_FIELDS, TRADE_LOG_FIELDS)
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
        self.condition_registered_at = {}
        self.pending_training_samples = {}
        self.last_training_sample_at = {}
        # 단테 학습 트랙(Phase A) 의 sample_id → 진행 정보. 5/10/20분 horizon 라벨링 후 CSV flush.
        self.pending_dante_samples = {}
        self.last_dante_sample_at = {}
        # shadow 학습 트랙: 게이트가 거른(wait/blocked) 표본을 같은 25분 horizon 으로 사후 라벨링.
        # ready 표본과 같은 풀에 들어가지 않도록 별도 dict + 별도 CSV 로 분리.
        self.pending_dante_shadow_samples = {}
        self.last_dante_shadow_sample_at = {}
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
        # 학습 데이터(entry_training.csv) 기반 보정값.
        # 단테 룰 전환 직후에는 사용하지 않으므로 None 상태로 둔다.
        self.dynamic_min_net_return = None
        self.entry_calibration = self.load_entry_calibration()
        self.ai_server_failure_count = 0
        self.ai_server_cooldown_until = 0.0
        self.condition_timer = QTimer()
        self.condition_timer.timeout.connect(self.process_next_condition_stock)
        self.position_check_timer = QTimer()
        self.position_check_timer.timeout.connect(self.check_open_positions)
        self.sell_check_timer = QTimer()
        self.sell_check_timer.timeout.connect(self.check_pending_sells)

    
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
                    if position.stop_price <= 0 or position.stop_price < initial_stop:
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
            self.enqueue_condition_stock(code, condition_name, "I")

    def _on_receive_real_condition(self, code, event_type, condition_name, condition_index):
        if event_type == "I":
            logger.info("[조건편입] {} {}({})".format(code, condition_name, condition_index))
            self.enqueue_condition_stock(code, condition_name, event_type)
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
        return abs(int(value))

    def append_realtime_tick(self, code, signed_at, close, high, open, low, ask, bid, accum_volume, chejan_strength=0.0):
        code = self.normalize_code(code)
        if code in self.no_tick_codes:
            self.no_tick_codes.discard(code)
            self.requeue_condition_stock(code)
        received_at = time.time()
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
            "chejan_strength": chejan_strength,
        }
        ticks = self.realtime_ticks.setdefault(code, [])
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

        self.update_training_labels(code, close, received_at)
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
        self.last_sell_skip_log_at.clear()
        self.pending_sell_intents.clear()
        self.pending_sell_order_codes.clear()
        self.condition_registered_at.clear()
        self.last_training_sample_at.clear()
        self.last_dante_sample_at.clear()
        # 전날 미라벨링된 단테 샘플은 표본 신뢰도가 낮으므로 폐기한다.
        self.pending_dante_samples.clear()
        self.last_dante_shadow_sample_at.clear()
        self.pending_dante_shadow_samples.clear()
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
            # 방금 보낸 주문이 TR 응답에 아직 반영되지 않은 경우를 대비해 합집합으로 병합
            self.pending_order_codes = new_pending | self.pending_order_codes
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
          1 = 1차 추격 매수 (A급 0봉 돌파)
          2 = 본진입 — A급 75% 분할 본진입 또는 B급 100% 일괄 본진입
        grade:
          "A" 또는 "B". B급 stage=2 는 신규 종목에서 한 번에 매수하므로 Position 미존재가 정상.
        """
        position = self.portfolio.get(code)
        if stage == 2:
            # B급 일괄 매수: position 미존재가 정상.
            if grade == "B" and (position is None or position.entry_stage == 0):
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

    def clamp(self, value, low=0.0, high=1.0):
        return max(low, min(high, value))

    def load_entry_calibration(self, path=TRAINING_ENTRY_CSV, bins=10, min_per_bin=5, min_total=80):
        """학습 데이터에서 score→평균 return_10m 매핑(보정 테이블)을 만든다.

        - score를 bins개 구간으로 나눠 각 구간 평균 return_10m 을 계산한다.
        - 각 구간에 표본이 min_per_bin개 미만이거나 전체가 min_total 미만이면 None 반환.
        - return은 scoring.calibrated_return_from_score 가 사용하는 형식의 list of dict.
        """
        try:
            if not os.path.exists(path):
                return None
            df = pd.read_csv(path, encoding="utf-8-sig")
            if "score" not in df.columns or "return_10m" not in df.columns:
                return None
            df = df[["score", "return_10m"]].copy()
            df["score"] = pd.to_numeric(df["score"], errors="coerce")
            df["return_10m"] = pd.to_numeric(df["return_10m"], errors="coerce")
            df = df.dropna()
            if len(df) < min_total:
                logger.info("[entry calibration] 표본 부족(%d < %d) → fallback 사용", len(df), min_total)
                return None
            edges = [i / bins for i in range(bins + 1)]
            df["bin"] = pd.cut(df["score"], bins=edges, include_lowest=True, labels=False)
            grouped = df.groupby("bin")
            table = []
            for bin_idx, group in grouped:
                if len(group) < min_per_bin:
                    continue
                table.append({
                    "score": float((edges[int(bin_idx)] + edges[int(bin_idx) + 1]) / 2),
                    "return": float(group["return_10m"].mean()),
                    "count": int(len(group)),
                })
            if len(table) < 3:
                logger.info("[entry calibration] 유효 구간 부족(%d) → fallback 사용", len(table))
                return None
            table.sort(key=lambda row: row["score"])
            logger.info("[entry calibration] %d개 구간 로드: %s", len(table),
                        ["{:.2f}->{:+.2%}({})".format(r["score"], r["return"], r["count"]) for r in table])
            self.dynamic_min_net_return = self._compute_dynamic_min_net_return(df["return_10m"])
            return table
        except Exception as exc:
            logger.warning("[entry calibration] 로드 실패: %s", exc)
            return None

    def _compute_dynamic_min_net_return(self, returns):
        """학습 데이터의 return_10m 분포에서 P50 기반의 자동 임계값을 계산한다.

        - 표본이 너무 적으면 None 반환 → 정적 MIN_NET_EXPECTED_RETURN 사용.
        - gross P50 에서 왕복비용을 차감한 net 값을 [floor, ceiling] 범위로 클램프한다.
        """
        try:
            series = returns.dropna() if hasattr(returns, "dropna") else returns
            if len(series) < 80:
                return None
            gross_p = float(series.quantile(DYNAMIC_MIN_NET_RETURN_PERCENTILE))
            net = gross_p - ESTIMATED_ROUND_TRIP_COST_RATE
            tuned = max(MIN_NET_EXPECTED_RETURN, min(net, DYNAMIC_MIN_NET_RETURN_CEILING))
            logger.info(
                "[entry calibration] 동적 매수 임계값 적용: P%.0f gross=%+.2%%, 비용=%.2%%, net=%+.2%% → 임계 %.2%%",
                DYNAMIC_MIN_NET_RETURN_PERCENTILE * 100,
                gross_p,
                ESTIMATED_ROUND_TRIP_COST_RATE,
                net,
                tuned,
            )
            return tuned
        except Exception as exc:
            logger.warning("[entry calibration] 동적 임계값 계산 실패: %s", exc)
            return None

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

    def should_print_wait_log(self, code):
        now = time.time()
        last_at = self.last_wait_log_at.get(code, 0)
        if now - last_at < WAIT_LOG_COOLDOWN_SECONDS:
            return False
        self.last_wait_log_at[code] = now
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

    def score_opening_trade(self, code):
        """단테조건식 편입 종목에 대해 1차(추격) 또는 2차(눌림 본진입) 매수 가능 여부 평가."""
        code = self.normalize_code(code)
        now = self.current_hhmmss()
        if now < OPENING_BUY_START:
            return {"status": "wait", "reason": "매수 시작 전"}
        if now > OPENING_BUY_END:
            return {"status": "blocked", "reason": "매수 시간 종료"}

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
        )

        if position is not None and position.entry_stage == 1:
            decision = entry_strategy.evaluate_second_entry(ctx)
            stage = 2
        else:
            decision = entry_strategy.evaluate_first_entry(ctx)
            stage = decision.stage if decision.stage in (1, 2) else 1

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

        return {
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
            "reason": decision.reason,
            "grade": getattr(decision, "grade", "") or "",
            "is_breakout_zero_bar": is_breakout_zero,
            "is_breakout_prev_bar": is_breakout_prev,
            "upper_wick_ratio": upper_wick,
            "px_over_bb55_pct": px_over_bb55,
            "open_return": open_return,
            "chejan_strength_history": chejan_history,
            "model_name": "DanteRule",
            # 매크로 dry-run 메타 — place_buy_order 등 trade_log 호출처에서 그대로 사용.
            "market_regime": getattr(decision, "market_regime", "") or "",
            "market_gate_action": getattr(decision, "market_gate_action", "") or "",
            "market_gate_reason": getattr(decision, "market_gate_reason", "") or "",
        }

    def handle_condition_stock(self, code):
        code = self.normalize_code(code)
        if code in self.no_tick_codes:
            return
        if code not in self.realtime_registered_codes:
            self.register_realtime_stock(code)
            self.condition_registered_at[code] = time.time()
            self.requeue_condition_stock(code)
            logger.info("[조건편입 관찰] {} 실시간 등록 - 단테 1차 게이트 대기".format(code))
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
            logger.info("[{}차 매수 제외] {} {}".format(stage, code, prediction.get("reason", "")))
            return

        self.update_account_status()
        grade = str(prediction.get("grade", "") or "")
        if self.should_skip_buy(code, stage=stage, grade=grade):
            return

        ratio = float(prediction.get("ratio", 0.0))
        if ratio <= 0:
            return

        self.place_buy_order(code, prediction, ratio=ratio, stage=stage)

    def place_buy_order(self, code, prediction, *, ratio, stage):
        """단테 분할매수 발주.

        stage == 1 (1차 추격):
          - 종목당 총 예산을 기반으로 planned_quantity 산정.
          - order_quantity = planned_quantity * ratio (1차 비율) → 시장가 주문.
        stage == 2 (본진입):
          - position.planned_quantity 에서 이미 체결된 1차 수량을 뺀 잔여를 시장가 주문.
        """
        code = self.normalize_code(code)
        current_price = self.parse_int(prediction.get("current_price", 0))
        if current_price <= 0:
            logger.info("[매수 보류] {} 현재가 0".format(code))
            return

        deposit = self.get_deposit(force=True)
        position = self.portfolio.get(code)

        ticks = self.realtime_ticks.get(code, [])
        last_ask = ticks[-1].get("ask", 0) if ticks else 0
        reference_price = max(current_price, last_ask) if last_ask > 0 else current_price
        unit_cost = max(int(reference_price * BUY_PRICE_MARGIN_RATE), 1)

        grade = str(prediction.get("grade", "") or "")
        b_grade_lump_sum = (
            stage == 2
            and (position is None or position.entry_stage == 0)
            and grade == "B"
        )

        if stage == 1:
            position_count = len(self.portfolio.holding_codes()) + len(self.portfolio.pending_order_codes())
            remaining_slots = max(MAX_CONCURRENT_POSITIONS - position_count, 1)
            full_budget = int(deposit * BUY_CASH_BUFFER_RATE / remaining_slots)
            planned_quantity = full_budget // unit_cost if unit_cost > 0 else 0
            if planned_quantity <= 0:
                logger.info(
                    "[매수 보류] {} 예수금 부족: 종목당 예산 {}, 단가 {}, 가능 예수금 {}".format(
                        code, full_budget, unit_cost, deposit
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
                    reason="예수금 부족",
                    message="단테 1차 stage 보류, 종목당 예산 {}, 단가 {}, 가능 {}".format(
                        full_budget, unit_cost, deposit
                    ),
                    market_regime=prediction.get("market_regime", ""),
                    market_gate_action=prediction.get("market_gate_action", ""),
                    market_gate_reason=prediction.get("market_gate_reason", ""),
                )
                return
            order_quantity = max(int(planned_quantity * ratio), 1)
            # 잔여 분(2차분)이 1주 이상 남도록 캡 — 1차에서 전량 다 사버리면 본진입이 무의미.
            order_quantity = min(order_quantity, max(planned_quantity - 1, 1))
        elif b_grade_lump_sum:
            # B급(1봉전 돌파만) — 1차/2차 분리 없이 첫 눌림에서 한 번에 본진입(ratio=1.0).
            position_count = len(self.portfolio.holding_codes()) + len(self.portfolio.pending_order_codes())
            remaining_slots = max(MAX_CONCURRENT_POSITIONS - position_count, 1)
            full_budget = int(deposit * BUY_CASH_BUFFER_RATE / remaining_slots)
            planned_quantity = full_budget // unit_cost if unit_cost > 0 else 0
            if planned_quantity <= 0:
                logger.info(
                    "[B급 매수 보류] {} 예수금 부족: 종목당 예산 {}, 단가 {}, 가능 {}".format(
                        code, full_budget, unit_cost, deposit
                    )
                )
                return
            order_quantity = planned_quantity  # ratio==1.0 이므로 전량
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

        # 예수금 한 번 더 안전 체크(시장가 슬리피지 대비).
        needed_cash = unit_cost * order_quantity
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

        result = self.send_order("buy", ORDER_SCREEN_NO, 1, code, order_quantity, 0, "03")
        if grade == "B":
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
            "reason": "{} ({})".format(reason_label, prediction.get("reason", "")),
        }
        self.append_trade_log(
            "buy_order",
            code=code,
            name=prediction.get("name", ""),
            side="buy",
            order_type="시장가",
            order_result=result,
            quantity=order_quantity,
            order_price=0,
            current_price=current_price,
            entry_price=current_price,
            score=prediction.get("score", 0.0),
            model_name=prediction.get("model_name", "DanteRule"),
            reason=reason_label,
            message="{}, planned {}, ratio {:.2f}, 단가 {}, 사유 {}".format(
                reason_label, planned_quantity, ratio, unit_cost, prediction.get("reason", "")
            ),
            market_regime=prediction.get("market_regime", ""),
            market_gate_action=prediction.get("market_gate_action", ""),
            market_gate_reason=prediction.get("market_gate_reason", ""),
        )
        if result == 0:
            self.order_prices[code] = current_price
            self.entry_times[code] = time.time()
            self.highest_prices[code] = current_price
            self.pending_order_codes.add(code)
            self.bought_codes.add(code)

            # Position 채움. 1차 발주 시점에 planned_quantity / pullback_window_deadline 셋업.
            position = self.portfolio.get_or_create(code, name=prediction.get("name", ""))
            position.entry_price = current_price
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
            elif b_grade_lump_sum:
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
                    "B급 일괄" if b_grade_lump_sum else "{}차".format(stage),
                    prediction.get("name", ""),
                    order_quantity,
                    planned_quantity,
                    current_price,
                    unit_cost,
                    grade or "?",
                    prediction.get("reason", ""),
                )
            )
        else:
            logger.error(
                "[{} 매수 실패] {} SendOrder 결과 {}".format(
                    "B급 일괄" if b_grade_lump_sum else "{}차".format(stage),
                    code,
                    result,
                )
            )

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
            get_fid("체결강도"),  # 단테 1차/2차 게이트와 청산 약화 판정에 사용
        ])
        opt_type = "0" if screen_no not in self.realtime_code_screens.values() else "1"
        self.set_real_reg(screen_no, code, fids, opt_type)
        self.realtime_registered_codes.add(code)
        self.realtime_code_screens[code] = screen_no

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
        return self.score_opening_trade(code)


def _log_dante_startup_banner():
    """단테 전략 핵심 파라미터를 시작 시 로그에 한 번 출력한다.

    소프트 롤아웃 1일차에 운영자가 게이트/청산 임계값을 즉시 확인할 수 있도록 한다.
    """
    logger.info("=" * 78)
    logger.info("[단테 추세전략] A급(0봉 돌파) 1차 추격(%.0f%%)→눌림 본진입(%.0f%%) | B급(1봉 돌파) 첫 눌림 일괄(%.0f%%)",
                entry_strategy.DANTE_FIRST_ENTRY_RATIO * 100,
                entry_strategy.DANTE_SECOND_ENTRY_RATIO * 100,
                entry_strategy.DANTE_GRADE_B_RATIO * 100)
    logger.info("[게이트] 체결강도 Hard≥%.0f / Soft%.0f~%.0f(추세상승필요) / 거래속도≥%.0f주초 / 스프레드≤%.2f%% / 관찰%.0f초 / 최소틱%d",
                entry_strategy.MIN_CHEJAN_STRENGTH_HARD,
                entry_strategy.MIN_CHEJAN_STRENGTH_SOFT,
                entry_strategy.MIN_CHEJAN_STRENGTH_HARD,
                entry_strategy.MIN_VOLUME_SPEED,
                entry_strategy.MAX_SPREAD_RATE * 100,
                entry_strategy.DANTE_MIN_OBSERVATION_SECONDS,
                entry_strategy.DANTE_MIN_TICKS)
    logger.info("[가짜돌파/과열] 5분봉 윗꼬리≤%.0f%% / 시가대비≤+%.0f%% / BB55 거리≤+%.1f%%",
                entry_strategy.MAX_UPPER_WICK_RATIO * 100,
                entry_strategy.OVERHEATED_OPEN_RETURN * 100,
                entry_strategy.OVERHEATED_BB55_DISTANCE * 100)
    logger.info("[눌림] %.2f%% ~ %.2f%% (고점대비 -%.2f%% 초과 시 차단), 음봉%d~%d 후 양봉반전, 윈도우 %d초",
                entry_strategy.PULLBACK_MIN_PCT * 100,
                entry_strategy.PULLBACK_MAX_PCT * 100,
                entry_strategy.MAX_DRAWDOWN_FROM_HIGH * 100,
                entry_strategy.PULLBACK_NEG_BARS_MIN,
                entry_strategy.PULLBACK_NEG_BARS_MAX,
                entry_strategy.PULLBACK_WINDOW_MAX_SECONDS)
    logger.info("[청산] -1R(%.2f%%) 손절 → +1R BE → +2R %.0f%% 부분익절 → 잔량 추세이탈, 시간손절 %d초",
                exit_strategy.R_UNIT_PCT * 100,
                exit_strategy.EXIT_PARTIAL_RATIO * 100,
                exit_strategy.EXIT_TIME_LIMIT_SECONDS)
    logger.info("[안전장치] 동시보유 %d, 일일매수상한 %d, 강제청산 %d, AI서버=%s, 구학습=%s, 단테학습=%s(%s), shadow=%s(%s)",
                MAX_CONCURRENT_POSITIONS,
                MAX_DAILY_BUY_COUNT,
                OPENING_FORCE_EXIT,
                "ON" if AI_SERVER_ENABLED else "OFF",
                "ON" if TRAINING_DATA_ENABLED else "OFF",
                "ON" if DANTE_TRAINING_DATA_ENABLED else "OFF",
                DANTE_TRAINING_CSV,
                "ON" if DANTE_SHADOW_TRAINING_DATA_ENABLED else "OFF",
                DANTE_SHADOW_TRAINING_CSV)
    logger.info("[조건식] 영웅문 등록명='%s' (단테조건식.xls 의 다중 BB/Envelope 상향돌파 + 거래량 + 체결강도)",
                CONDITION_NAME)
    logger.info("=" * 78)


def main():
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()

    _log_dante_startup_banner()

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

    # 매크로 dry-run 게이트용 KOSPI/KOSDAQ 실시간 지수 — 조건검색 시작 전에 1회 등록.
    kiwoom.register_realtime_indices()

    if not kiwoom.start_realtime_condition(CONDITION_NAME):
        logger.error("실시간 조건검색을 시작하지 못했습니다. 조건식 설정을 확인해주세요.")

    app.exec_()


if __name__ == "__main__":
    main()