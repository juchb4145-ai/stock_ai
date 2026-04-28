from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import csv
import json
import logging
import logging.handlers
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

import pandas as pd
import pickle

import scoring


def _setup_logging():
    # 환경변수 KIWOOM_LOG_LEVEL=DEBUG 등으로 임시 디버그 가능. 기본은 INFO.
    log_dir = "data"
    os.makedirs(log_dir, exist_ok=True)
    root = logging.getLogger()
    if root.handlers:
        return logging.getLogger("kiwoom")
    level_name = os.environ.get("KIWOOM_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    root.addHandler(stream_handler)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "main.log"),
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    return logging.getLogger("kiwoom")


logger = _setup_logging()

CONDITION_NAME = "단테떡상이"  # 비워두면 저장된 조건식 중 첫 번째 조건식을 사용합니다.
CONDITION_SCREEN_NO = "0150"
REALTIME_SCREEN_NO = "0160"
ORDER_SCREEN_NO = "0001"
AI_SERVER_ENABLED = True
AI_SERVER_URL = "http://127.0.0.1:8000"
AI_SERVER_TIMEOUT_SECONDS = 0.35
TRAINING_DATA_ENABLED = True
TRAINING_DATA_DIR = "data"
TRAINING_ENTRY_CSV = os.path.join(TRAINING_DATA_DIR, "entry_training.csv")
TRADE_LOG_CSV = os.path.join(TRAINING_DATA_DIR, "trade_log.csv")
TRAINING_SAMPLE_COOLDOWN_SECONDS = 30
TRAINING_LABEL_HORIZONS = (300, 600, 1200)
BUY_CASH_BUFFER_RATE = 0.98
BUY_PRICE_MARGIN_RATE = 1.005
MIN_EXPECTED_RETURN = 0.006
OPENING_BUY_START = 90300
# 9:03~15:20
OPENING_BUY_END = 152000
OPENING_FORCE_EXIT = 152000

OPENING_MIN_TICKS = 5
OPENING_TICK_LIMIT = 40
OPENING_MIN_SCORE = 0.68
OPENING_TAKE_PROFIT_RATE = 0.012
OPENING_STOP_LOSS_RATE = -0.008
OPENING_STOP_LOSS_GRACE_SECONDS = 45
OPENING_STOP_LOSS_FORCE_RATE = -0.012
OPENING_STOP_LOSS_CONFIRM_TICKS = 3
OPENING_MAX_HOLD_SECONDS = 20 * 60
OPENING_MIN_HOLD_SECONDS = 5 * 60
OPENING_MAX_SPREAD_RATE = 0.006
ENTRY_OVERHEAT_BOX_POSITION = 0.95
ENTRY_OVERHEAT_DIRECTION_MAX = 0.25
EXIT_MIN_PROFIT_RATE = 0.007
EXIT_STRONG_PROFIT_RATE = 0.018
EXIT_TRAILING_DROP_RATE = 0.0035
EXIT_HOLD_SCORE_MIN = 0.45
EXIT_STALL_SECONDS = 7 * 60
MAX_CONCURRENT_POSITIONS = 3
MAX_DAILY_BUY_COUNT = 5
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
ENTRY_FEATURE_NAMES = [
    "price_momentum",
    "open_return",
    "box_position",
    "direction_score",
    "volume_speed",
    "spread_rate",
]
TRAINING_ENTRY_FIELDS = [
    "sample_id",
    "captured_at",
    "captured_time",
    "code",
    "name",
    "entry_price",
    "score",
    "expected_return",
    "target_price",
    "model_name",
    "status",
    "reason",
] + ENTRY_FEATURE_NAMES + [
    "return_5m",
    "return_10m",
    "return_20m",
    "success_10m",
]
TRADE_LOG_FIELDS = [
    "logged_at",
    "event",
    "code",
    "name",
    "side",
    "order_type",
    "order_status",
    "order_no",
    "order_result",
    "quantity",
    "order_price",
    "current_price",
    "executed_price",
    "executed_quantity",
    "entry_price",
    "target_price",
    "score",
    "expected_return",
    "model_name",
    "reason",
    "hold_seconds",
    "profit_rate",
    "message",
]

FID_CODES = {
    "10": "현재가",
    "11": "전일 대비",
    "12": "등락율",
    "13": "누적거래량",
    "14": "누적거래대금",
    "15": "거래량",
    "16": "시가",
    "17": "고가",
    "18": "저가",
    "20": "체결시간",
    "21": "호가시간",
    "23": "예상체결가",
    "24": "예상체결 수량",
    "25": "전일대비기호",
    "26": "전일거래량 대비(계약,주)",
    "27": "(최우선)매도호가",
    "28": "(최우선)매수호가",
    "29": "거래대금 증감",
    "30": "전일거래량 대비(비율)",
    "31": "거래회전율",
    "32": "거래비용",
    "41": "매도호가1",
    "42": "매도호가2",
    "43": "매도호가3",
    "44": "매도호가4",
    "45": "매도호가5",
    "46": "매도호가6",
    "47": "매도호가7",
    "48": "매도호가8",
    "49": "매도호가9",
    "50": "매도호가10",
    "51": "매수호가1",
    "52": "매수호가2",
    "53": "매수호가3",
    "54": "매수호가4",
    "55": "매수호가5",
    "56": "매수호가6",
    "57": "매수호가7",
    "58": "매수호가8",
    "59": "매수호가9",
    "60": "매수호가10",
    "61": "매도호가 수량1",
    "62": "매도호가 수량2",
    "63": "매도호가 수량3",
    "64": "매도호가 수량4",
    "65": "매도호가 수량5",
    "66": "매도호가 수량6",
    "67": "매도호가 수량7",
    "68": "매도호가 수량8",
    "69": "매도호가 수량9",
    "70": "매도호가 수량10",
    "71": "매수호가 수량1",
    "72": "매수호가 수량2",
    "73": "매수호가 수량3",
    "74": "매수호가 수량4",
    "75": "매수호가 수량5",
    "76": "매수호가 수량6",
    "77": "매수호가 수량7",
    "78": "매수호가 수량8",
    "79": "매수호가 수량9",
    "80": "매수호가 수량10",
    "81": "매도호가 직전대비1",
    "82": "매도호가 직전대비2",
    "83": "매도호가 직전대비3",
    "84": "매도호가 직전대비4",
    "85": "매도호가 직전대비5",
    "86": "매도호가 직전대비6",
    "87": "매도호가 직전대비7",
    "88": "매도호가 직전대비8",
    "89": "매도호가 직전대비9",
    "90": "매도호가 직전대비10",
    "91": "매수호가 직전대비1",
    "92": "매수호가 직전대비2",
    "93": "매수호가 직전대비3",
    "94": "매수호가 직전대비4",
    "95": "매수호가 직전대비5",
    "96": "매수호가 직전대비6",
    "97": "매수호가 직전대비7",
    "98": "매수호가 직전대비8",
    "99": "매수호가 직전대비9",
    "100": "매수호가 직전대비10",
    "101": "매도호가 건수1",
    "102": "매도호가 건수2",
    "103": "매도호가 건수3",
    "104": "매도호가 건수4",
    "105": "매도호가 건수5",
    "111": "매수호가 건수1",
    "112": "매수호가 건수2",
    "113": "매수호가 건수3",
    "114": "매수호가 건수4",
    "115": "매수호가 건수5",
    "121": "매도호가 총잔량",
    "122": "매도호가 총잔량 직전대비",
    "123": "매도호가 총 건수",
    "125": "매수호가 총잔량",
    "126": "매수호가 총잔량 직전대비",
    "127": "매수호가 총 건수",
    "128": "순매수잔량(총매수잔량-총매도잔량)",
    "129": "매수비율",
    "131": "시간외 매도호가 총잔량",
    "132": "시간외 매도호가 총잔량 직전대비",
    "135": "시간외 매수호가 총잔량",
    "136": "시간외 매수호가 총잔량 직전대비",
    "137": "호가 순잔량",
    "138": "순매도잔량(총매도잔량-총매수잔량)",
    "139": "매도비율",
    "141": "매도 거래원1",
    "142": "매도 거래원2",
    "143": "매도 거래원3",
    "144": "매도 거래원4",
    "145": "매도 거래원5",
    "146": "매도 거래원 코드1",
    "147": "매도 거래원 코드2",
    "148": "매도 거래원 코드3",
    "149": "매도 거래원 코드4",
    "150": "매도 거래원 코드5",
    "151": "매수 거래원1",
    "152": "매수 거래원2",
    "153": "매수 거래원3",
    "154": "매수 거래원4",
    "155": "매수 거래원5",
    "156": "매수 거래원 코드1",
    "157": "매수 거래원 코드2",
    "158": "매수 거래원 코드3",
    "159": "매수 거래원 코드4",
    "160": "매수 거래원 코드5",
    "161": "매도 거래원 수량1",
    "162": "매도 거래원 수량2",
    "163": "매도 거래원 수량3",
    "164": "매도 거래원 수량4",
    "165": "매도 거래원 수량5",
    "166": "매도 거래원별 증감1",
    "167": "매도 거래원별 증감2",
    "168": "매도 거래원별 증감3",
    "169": "매도 거래원별 증감4",
    "170": "매도 거래원별 증감5",
    "171": "매수 거래원 수량1",
    "172": "매수 거래원 수량2",
    "173": "매수 거래원 수량3",
    "174": "매수 거래원 수량4",
    "175": "매수 거래원 수량5",
    "176": "매수 거래원별 증감1",
    "177": "매수 거래원별 증감2",
    "178": "매수 거래원별 증감3",
    "179": "매수 거래원별 증감4",
    "180": "매수 거래원별 증감5",
    "181": "미결제 약정 전일대비",
    "182": "이론가",
    "183": "시장베이시스",
    "184": "이론베이시스",
    "185": "괴리도",
    "186": "괴리율",
    "187": "내재가치",
    "188": "시간가치",
    "189": "내재변동성(I.V.)",
    "190": "델타",
    "191": "감마",
    "192": "베가",
    "193": "세타",
    "194": "로",
    "195": "미결제약정",
    "196": "미결제 증감",
    "197": "KOSPI200",
    "200": "예상체결가 전일종가 대비",
    "201": "예상체결가 전일종가 대비 등락율",
    "214": "장시작 예상잔여시간",
    "215": "장운영구분",  # (0:장시작전, 2:장종료전, 3:장시작, 4,8:장종료, 9:장마감)
    "216": "투자자별 ticker",
    "219": "선물 최근 월물지수",
    "228": "체결강도",
    "238": "예상체결가 전일종가 대비기호",
    "246": "시초 미결제 약정수량",
    "247": "최고 미결제 약정수량",
    "248": "최저 미결제 약정수량",
    "251": "상한종목수",
    "252": "상승종목수",
    "253": "보합종목수",
    "254": "하한종목수",
    "255": "하락종목수",
    "256": "거래형성 종목수",
    "257": "거래형성 비율",
    "261": "외국계 매도추정합",
    "262": "외국계 매도추정합 변동",
    "263": "외국계 매수추정합",
    "264": "외국계 매수추정합 변동",
    "267": "외국계 순매수추정합",
    "268": "외국계 순매수 변동",
    "271": "매도 거래원 색깔1",
    "272": "매도 거래원 색깔2",
    "273": "매도 거래원 색깔3",
    "274": "매도 거래원 색깔4",
    "275": "매도 거래원 색깔5",
    "281": "매수 거래원 색깔1",
    "282": "매수 거래원 색깔2",
    "283": "매수 거래원 색깔3",
    "284": "매수 거래원 색깔4",
    "285": "매수 거래원 색깔5",
    "290": "장구분",
    "291": "예상체결가",
    "292": "예상체결량",
    "293": "예상체결가 전일대비기호",
    "294": "예상체결가 전일대비",
    "295": "예상체결가 전일대비등락율",
    "299": "전일거래량대비예상체결률",
    "302": "종목명",
    "307": "기준가",
    "311": "시가총액(억)",
    "337": "거래소구분 (1, KOSPI, 2:KOSDAQ, 3:OTCCBB, 4:KOSPI200선물, 5:KOSPI200옵션, 6:개별주식옵션, 7:채권)",
    "391": "기준가대비 시고등락율",
    "392": "기준가대비 고가등락율",
    "393": "기준가대비 저가등락율",
    "397": "주식옵션거래단위",
    "621": "LP매도호가 수량1",
    "622": "LP매도호가 수량2",
    "623": "LP매도호가 수량3",
    "624": "LP매도호가 수량4",
    "625": "LP매도호가 수량5",
    "626": "LP매도호가 수량6",
    "627": "LP매도호가 수량7",
    "628": "LP매도호가 수량8",
    "629": "LP매도호가 수량9",
    "630": "LP매도호가 수량10",
    "631": "LP매수호가 수량1",
    "632": "LP매수호가 수량2",
    "633": "LP매수호가 수량3",
    "634": "LP매수호가 수량4",
    "635": "LP매수호가 수량5",
    "636": "LP매수호가 수량6",
    "637": "LP매수호가 수량7",
    "638": "LP매수호가 수량8",
    "639": "LP매수호가 수량9",
    "640": "LP매수호가 수량10",
    "691": "K,O 접근도 (ELW조기종료발생 기준가격, 지수)",
    "900": "주문수량",
    "901": "주문가격",
    "902": "미체결수량",
    "903": "체결누계금액",
    "904": "원주문번호",
    "905": "주문구분",
    "906": "매매구분",
    "907": "매도수구분",
    "908": "주문시간",
    "909": "체결번호",
    "910": "체결가",
    "911": "체결량",
    "912": "주문업무분류",  # (JJ:주식주문, FJ:선물옵션, JG:주식잔고, FG:선물옵션잔고)
    "913": "주문상태",  # (10:원주문, 11:정정주문, 12:취소주문, 20:주문확인, 21:정정확인, 22:취소확인, 90-92:주문거부)
    "914": "단위체결가",
    "915": "단위체결량",
    "916": "대출일",
    "917": "신용구분",
    "918": "만기일",
    "930": "보유수량",
    "931": "매입단가",
    "932": "총매입가",
    "933": "주문가능수량",
    "938": "당일매매 수수료",
    "939": "당일매매세금",
    "945": "당일순매수량",
    "946": "매도/매수구분",
    "950": "당일 총 매도 손익",
    "951": "예수금",
    "957": "신용금액",
    "958": "신용이자",
    "959": "담보대출수량",
    "990": "당일실현손익(유가)",
    "991": "당일실현손익률(유가)",
    "992": "당일실현손익(신용)",
    "993": "당일실현손익률(신용)",
    "8019": "손익율",
    "9001": "종목코드",
    "9201": "계좌번호",
    "9203": "주문번호",
    "9205": "관리자사번"
}

FID_NAME_TO_CODE = {value: key for key, value in FID_CODES.items()}


def get_fid(fid_name):
    try:
        return FID_NAME_TO_CODE[fid_name]
    except KeyError:
        raise KeyError("알 수 없는 FID 이름: {}".format(fid_name))


class Kiwoom(QAxWidget):
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
                target_return = context.get("target_return")
                if not isinstance(target_return, (int, float)):
                    target_return = self.estimate_target_return(entry_price, context.get("target_price", ""))
                if target_return > 0:
                    self.target_returns[code] = target_return
                    target_price = self.compute_target_price(entry_price, target_return)
                else:
                    target_price = self.parse_int(context.get("target_price", ""))
                if target_price:
                    self.best[code] = target_price
                    self.save_best()
                self.register_realtime_stock(code)
                if left_quantity_int <= 0:
                    self.pending_order_codes.discard(code)
                self.account_updated_at = 0
                self.deposit_updated_at = 0
                self.process_pending_sell_intents([code])
            elif side == "sell" and executed_quantity_int > 0:
                remaining_quantity = max(self.position_quantities.get(code, 0) - executed_quantity_int, 0)
                self.position_quantities[code] = remaining_quantity
                if remaining_quantity <= 0 and left_quantity_int <= 0:
                    self._discard_position(code)
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
            else:
                self._discard_position(code)
            self.account_updated_at = 0
            self.deposit_updated_at = 0
            self.process_pending_sell_intents([code])

        # 주문이 종료된 시점(체결 완료 또는 거부/취소)에서만 order_context를 정리한다.
        # 부분체결 중에는 컨텍스트가 필요하므로 유지한다.
        if order_terminated and code:
            self.order_context.pop(code, None)

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

    def append_realtime_tick(self, code, signed_at, close, high, open, low, ask, bid, accum_volume):
        code = self.normalize_code(code)
        if code in self.no_tick_codes:
            self.no_tick_codes.discard(code)
            self.requeue_condition_stock(code)
        tick = {
            "received_at": time.time(),
            "signed_at": signed_at,
            "close": close,
            "high": high,
            "open": open,
            "low": low,
            "ask": ask,
            "bid": bid,
            "accum_volume": accum_volume,
        }
        ticks = self.realtime_ticks.setdefault(code, [])
        ticks.append(tick)
        if len(ticks) > OPENING_TICK_LIMIT:
            del ticks[:-OPENING_TICK_LIMIT]
        self.update_training_labels(code, close, tick["received_at"])

    def _on_receive_real_data(self, s_code, real_type, real_data):
        if real_type == "장시작시간":
            pass
        elif real_type == "주식체결":
            signed_at = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("체결시간"))
            close = self.get_real_int(s_code, "현재가")
            high = self.get_real_int(s_code, "고가")
            open = self.get_real_int(s_code, "시가")
            low = self.get_real_int(s_code, "저가")
            top_priority_ask = self.get_real_int(s_code, "(최우선)매도호가")
            top_priority_bid = self.get_real_int(s_code, "(최우선)매수호가")
            accum_volume = self.get_real_int(s_code, "누적거래량")

            self.universe_realtime_transaction_info.append([s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume])
            self.append_realtime_tick(s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume)
    
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
        logger.info("[일일초기화] {} 매수 후보/대기 상태 초기화".format(today))

    def normalize_code(self, code):
        return code.strip().lstrip("A")

    def _discard_position(self, code, *, save=True, drop_pending_sell=True):
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
        if save:
            self.save_best()

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

    def should_skip_buy(self, code):
        if code in self.holding_codes:
            logger.info("[매수 제외] {} 이미 보유 중".format(code))
            return True
        if code in self.pending_order_codes:
            logger.info("[매수 제외] {} 미체결 주문 존재".format(code))
            return True
        if code in self.bought_codes:
            logger.info("[매수 제외] {} 오늘 이미 매수 주문 처리".format(code))
            return True
        if len(self.holding_codes) + len(self.pending_order_codes) >= MAX_CONCURRENT_POSITIONS:
            logger.info("[매수 제외] 최대 보유/주문 종목 수 도달: {}".format(MAX_CONCURRENT_POSITIONS))
            return True
        if len(self.bought_codes) >= MAX_DAILY_BUY_COUNT:
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

    def compute_target_price(self, entry_price, target_return):
        entry_price = self.parse_int(entry_price)
        if entry_price <= 0:
            return 0
        return round(int(entry_price * (1 + target_return)), -1)

    def estimate_target_return(self, entry_price, target_price):
        entry_price = self.parse_int(entry_price)
        target_price = self.parse_int(target_price)
        if entry_price <= 0 or target_price <= 0:
            return 0.0
        return target_price / entry_price - 1

    def has_consecutive_down_ticks(self, code, required_count=OPENING_STOP_LOSS_CONFIRM_TICKS):
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
        self.pending_sell_intents[code] = {
            "reason": reason,
            "order_price": order_price,
            "order_gubun": order_gubun,
            "queued_at": existing.get("queued_at", time.time()),
            "last_try_at": existing.get("last_try_at", 0),
        }

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

    def ensure_training_data_file(self):
        if not TRAINING_DATA_ENABLED:
            return
        os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
        if os.path.exists(TRAINING_ENTRY_CSV):
            return
        with open(TRAINING_ENTRY_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRAINING_ENTRY_FIELDS)
            writer.writeheader()

    def append_training_row(self, row):
        if not TRAINING_DATA_ENABLED:
            return
        self.ensure_training_data_file()
        with open(TRAINING_ENTRY_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRAINING_ENTRY_FIELDS)
            writer.writerow(row)

    def ensure_trade_log_file(self):
        os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
        if os.path.exists(TRADE_LOG_CSV):
            return
        with open(TRADE_LOG_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRADE_LOG_FIELDS)
            writer.writeheader()

    def append_trade_log(self, event, **kwargs):
        self.ensure_trade_log_file()
        row = {field: "" for field in TRADE_LOG_FIELDS}
        row["logged_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        row["event"] = event
        for key, value in kwargs.items():
            if key in row:
                row[key] = value
        with open(TRADE_LOG_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=TRADE_LOG_FIELDS)
            writer.writerow(row)

    def register_training_sample(self, code, name, entry_price, features, prediction):
        if not TRAINING_DATA_ENABLED:
            return
        now = time.time()
        last_at = self.last_training_sample_at.get(code, 0)
        if now - last_at < TRAINING_SAMPLE_COOLDOWN_SECONDS:
            return

        sample_id = uuid.uuid4().hex
        row = {
            "sample_id": sample_id,
            "captured_at": now,
            "captured_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "code": code,
            "name": name,
            "entry_price": entry_price,
            "score": prediction.get("score", 0),
            "expected_return": prediction.get("expected_return", 0),
            "target_price": prediction.get("target_price", entry_price),
            "model_name": prediction.get("model_name", ""),
            "status": prediction.get("status", ""),
            "reason": prediction.get("reason", ""),
        }
        for feature_name in ENTRY_FEATURE_NAMES:
            row[feature_name] = features.get(feature_name, 0)
        for horizon in TRAINING_LABEL_HORIZONS:
            row["return_{}m".format(horizon // 60)] = ""
        row["success_10m"] = ""

        self.pending_training_samples[sample_id] = {
            "code": code,
            "captured_at": now,
            "entry_price": entry_price,
            "row": row,
            "labeled_horizons": set(),
        }
        self.last_training_sample_at[code] = now
        logger.info("[학습데이터 후보] {} {} 기준가 {} sample {}".format(name, code, entry_price, sample_id[:8]))

    def update_training_labels(self, code, current_price, received_at):
        if not TRAINING_DATA_ENABLED:
            return
        code = self.normalize_code(code)
        completed = []
        for sample_id, sample in list(self.pending_training_samples.items()):
            if sample["code"] != code:
                continue
            elapsed = received_at - sample["captured_at"]
            for horizon in TRAINING_LABEL_HORIZONS:
                if horizon in sample["labeled_horizons"] or elapsed < horizon:
                    continue
                return_rate = current_price / sample["entry_price"] - 1
                sample["row"]["return_{}m".format(horizon // 60)] = return_rate
                sample["labeled_horizons"].add(horizon)
            if len(sample["labeled_horizons"]) == len(TRAINING_LABEL_HORIZONS):
                return_10m = sample["row"].get("return_10m", 0)
                sample["row"]["success_10m"] = 1 if return_10m >= MIN_EXPECTED_RETURN else 0
                self.append_training_row(sample["row"])
                completed.append(sample_id)
                logger.info("[학습데이터 저장] {} sample {} 10분수익률 {:.2%}".format(code, sample_id[:8], return_10m))

        for sample_id in completed:
            self.pending_training_samples.pop(sample_id, None)

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
        code = self.normalize_code(code)
        now = self.current_hhmmss()
        if now < OPENING_BUY_START:
            return {
                "status": "wait",
                "reason": "장초반 매수 시작 전",
            }
        if now > OPENING_BUY_END:
            return {
                "status": "blocked",
                "reason": "장초반 매수 시간 아님",
            }

        ticks = self.realtime_ticks.get(code, [])
        if len(ticks) < OPENING_MIN_TICKS:
            return {
                "status": "wait",
                "reason": "실시간 틱 부족 {}/{}".format(len(ticks), OPENING_MIN_TICKS),
            }

        first = ticks[0]
        last = ticks[-1]
        current_price = last["close"]
        open_price = last["open"]
        highs = [tick["high"] for tick in ticks if tick["high"] > 0]
        lows = [tick["low"] for tick in ticks if tick["low"] > 0]
        if not highs or not lows:
            return {
                "status": "wait",
                "reason": "고가/저가 데이터 부족",
            }
        high = max(highs)
        low = min(lows)
        ask = last["ask"]
        bid = last["bid"]
        if current_price <= 0 or open_price <= 0 or high <= low or ask <= 0 or bid <= 0:
            return {
                "status": "wait",
                "reason": "실시간 가격 데이터 부족",
            }

        features = scoring.build_entry_features(
            ticks=ticks,
            current_price=current_price,
            open_price=open_price,
            high=high,
            low=low,
            ask=ask,
            bid=bid,
        )
        if features is None:
            return {
                "status": "wait",
                "reason": "실시간 가격 데이터 부족",
            }
        spread_rate = features["spread_rate"]
        price_momentum = features["price_momentum"]
        open_return = features["open_return"]
        box_position = features["box_position"]
        direction_score = features["direction_score"]
        if box_position >= ENTRY_OVERHEAT_BOX_POSITION and direction_score <= ENTRY_OVERHEAT_DIRECTION_MAX:
            return {
                "status": "wait",
                "reason": "상단 과열 구간 추격 진입 대기(box {:.2f}, direction {:.2f})".format(
                    box_position, direction_score
                ),
            }

        server_prediction = self.call_ai_server("/predict-entry", {
            "code": code,
            "name": self.get_code_name(code),
            "current_price": current_price,
            "open_price": open_price,
            "high": high,
            "low": low,
            "ask": ask,
            "bid": bid,
            "ticks": self.serialize_ticks(ticks),
        })
        if server_prediction is not None:
            server_prediction["code"] = code
            server_prediction["name"] = self.get_code_name(code)
            server_prediction["current_price"] = current_price
            logger.info("[AI서버 매수판단] {} 현재가 {} 점수 {:.2f} 기대수익률 {:.2%} 모델 {} 사유 {}".format(
                server_prediction["name"],
                current_price,
                server_prediction.get("score", 0),
                server_prediction.get("expected_return", 0),
                server_prediction.get("model_name", "unknown"),
                server_prediction.get("reason", ""),
            ))
            self.register_training_sample(code, server_prediction["name"], current_price, features, server_prediction)
            return server_prediction

        if spread_rate < 0 or spread_rate > OPENING_MAX_SPREAD_RATE:
            return {
                "status": "blocked",
                "reason": "호가 스프레드 과다 {:.2%}".format(spread_rate),
            }

        score = scoring.compute_entry_score(features, OPENING_MAX_SPREAD_RATE)
        expected_return = scoring.expected_return_from_score(score)
        target_price = scoring.compute_target_price(current_price, expected_return, OPENING_TAKE_PROFIT_RATE)
        name = self.get_code_name(code)
        logger.info("[장초반점수] {} 현재가 {} 점수 {:.2f} 기대수익률 {:.2%} 모멘텀 {:.2%} 시가대비 {:.2%} 스프레드 {:.2%}".format(
            name,
            current_price,
            score,
            expected_return,
            price_momentum,
            open_return,
            spread_rate,
        ))
        prediction = {
            "status": "ready",
            "code": code,
            "name": name,
            "current_price": current_price,
            "target_price": target_price,
            "expected_return": expected_return,
            "score": score,
            "model_name": "OpeningRealtimeScore",
        }
        self.register_training_sample(code, name, current_price, features, prediction)
        return prediction

    def handle_condition_stock(self, code):
        code = self.normalize_code(code)
        if code in self.no_tick_codes:
            return
        if code not in self.realtime_registered_codes:
            self.register_realtime_stock(code)
            self.condition_registered_at[code] = time.time()
            self.requeue_condition_stock(code)
            logger.info("[조건검색 관찰] {} 실시간 등록 후 장초반 점수 대기".format(code))
            return

        prediction = self.predict_stock(code)
        if prediction is None:
            return

        if prediction.get("status") == "wait":
            ticks = self.realtime_ticks.get(code, [])
            registered_at = self.condition_registered_at.get(code, time.time())
            if len(ticks) == 0 and time.time() - registered_at >= REALTIME_TICK_WAIT_TIMEOUT_SECONDS:
                self.no_tick_codes.add(code)
                logger.info("[매수 제외] {} 실시간 틱 수신 없음 {}초".format(code, REALTIME_TICK_WAIT_TIMEOUT_SECONDS))
                return
            self.requeue_condition_stock(code)
            if self.should_print_wait_log(code):
                logger.info("[매수 대기] {} {}".format(code, prediction["reason"]))
            return
        if prediction.get("status") == "blocked":
            logger.info("[매수 제외] {} {}".format(code, prediction["reason"]))
            return

        self.update_account_status()
        if self.should_skip_buy(code):
            return

        expected_return = prediction["expected_return"]
        if expected_return < MIN_EXPECTED_RETURN:
            logger.info("[매수 보류] {} 기대수익률 {:.2%} < 기준 {:.2%}".format(code, expected_return, MIN_EXPECTED_RETURN))
            return
        if prediction["score"] < OPENING_MIN_SCORE:
            logger.info("[매수 보류] {} 장초반점수 {:.2f} < 기준 {:.2f}".format(code, prediction["score"], OPENING_MIN_SCORE))
            return

        self.place_buy_order(code, prediction)

    def place_buy_order(self, code, prediction):
        current_price = prediction["current_price"]
        deposit = self.get_deposit(force=True)
        position_count = len(self.holding_codes) + len(self.pending_order_codes)
        remaining_slots = max(MAX_CONCURRENT_POSITIONS - position_count, 1)
        order_budget = int(deposit * BUY_CASH_BUFFER_RATE / remaining_slots)

        ticks = self.realtime_ticks.get(code, [])
        last_ask = ticks[-1].get("ask", 0) if ticks else 0
        reference_price = max(current_price, last_ask) if last_ask > 0 else current_price
        unit_cost = max(int(reference_price * BUY_PRICE_MARGIN_RATE), 1)
        order_quantity = order_budget // unit_cost if unit_cost > 0 else 0
        needed_cash = current_price * order_quantity
        if order_quantity <= 0:
            logger.info("[매수 보류] {} 예수금 부족: 종목당 예산 {}, 단가 {}, 가능 예수금 {}".format(code, order_budget, unit_cost, deposit))
            self.append_trade_log(
                "buy_skip",
                code=code,
                name=prediction.get("name", ""),
                side="buy",
                quantity=0,
                current_price=current_price,
                target_price=prediction.get("target_price", ""),
                score=prediction.get("score", ""),
                expected_return=prediction.get("expected_return", ""),
                model_name=prediction.get("model_name", ""),
                reason="예수금 부족",
                message="종목당 예산 {}, 단가 {}, 가능 {}".format(order_budget, unit_cost, deposit),
            )
            return

        result = self.send_order("buy", ORDER_SCREEN_NO, 1, code, order_quantity, 0, "03")
        target_price = self.parse_int(prediction.get("target_price", 0))
        target_return = self.estimate_target_return(current_price, target_price)
        self.order_context[code] = {
            "side": "buy",
            "name": prediction.get("name", ""),
            "score": prediction.get("score", ""),
            "expected_return": prediction.get("expected_return", ""),
            "model_name": prediction.get("model_name", ""),
            "target_price": prediction.get("target_price", ""),
            "target_return": target_return,
            "reason": "매수 조건 통과",
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
            target_price=prediction.get("target_price", ""),
            score=prediction.get("score", ""),
            expected_return=prediction.get("expected_return", ""),
            model_name=prediction.get("model_name", ""),
            reason="매수 조건 통과",
        )
        if result == 0:
            self.best[code] = prediction["target_price"]
            if target_return > 0:
                self.target_returns[code] = target_return
            self.order_prices[code] = current_price
            self.entry_times[code] = time.time()
            self.highest_prices[code] = current_price
            self.pending_order_codes.add(code)
            self.bought_codes.add(code)
            self.save_best()
            self.register_realtime_stock(code)
            logger.info("[매수 주문] {} 수량 {} 현재가 {} 주문예산 {} 목표가 {} 기대수익률 {:.2%} 장초반점수 {:.2f} 모델 {}".format(
                prediction["name"],
                order_quantity,
                current_price,
                needed_cash,
                prediction["target_price"],
                prediction["expected_return"],
                prediction["score"],
                prediction["model_name"],
            ))
        else:
            logger.error("[매수 실패] {} SendOrder 결과 {}".format(code, result))

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
        ])
        opt_type = "0" if screen_no not in self.realtime_code_screens.values() else "1"
        self.set_real_reg(screen_no, code, fids, opt_type)
        self.realtime_registered_codes.add(code)
        self.realtime_code_screens[code] = screen_no

    def get_realtime_screen_no(self):
        screen_offset = len(self.realtime_registered_codes) // REALTIME_CODES_PER_SCREEN
        return str(int(REALTIME_SCREEN_NO) + screen_offset).zfill(4)

    def score_exit_timing(self, code, current_price):
        code = self.normalize_code(code)
        entry_price = self.order_prices.get(code)
        if not isinstance(entry_price, (int, float)):
            entry_price = self.parse_int(entry_price)
            if entry_price > 0:
                self.order_prices[code] = entry_price
            else:
                entry_price = None
        if not entry_price:
            for balance in self.cached_balance:
                if self.normalize_code(balance[0]) == code:
                    fallback = self.parse_int(balance[3])
                    if fallback > 0:
                        entry_price = fallback
                        self.order_prices[code] = fallback
                    break
        entry_time = self.entry_times.get(code)

        if self.current_hhmmss() >= OPENING_FORCE_EXIT:
            return {
                "action": "sell",
                "score": 0.0,
                "reason": "장초반 전략 종료 시간 도달",
            }
        if not entry_price:
            return {
                "action": "hold",
                "score": 0.0,
                "reason": "진입가 정보 부족",
            }

        now = time.time()
        if not entry_time:
            self.entry_times[code] = now
            entry_time = now
        hold_seconds = now - entry_time
        profit_rate = current_price / entry_price - 1
        highest_price = max(self.highest_prices.get(code, current_price), current_price)
        self.highest_prices[code] = highest_price
        trailing_drop = current_price / highest_price - 1 if highest_price > 0 else 0

        if profit_rate <= OPENING_STOP_LOSS_RATE:
            in_grace = hold_seconds < OPENING_STOP_LOSS_GRACE_SECONDS
            hard_break = profit_rate <= OPENING_STOP_LOSS_FORCE_RATE
            confirmed_downtrend = self.has_consecutive_down_ticks(code, OPENING_STOP_LOSS_CONFIRM_TICKS)
            if in_grace and not hard_break and not confirmed_downtrend:
                return {
                    "action": "hold",
                    "score": 0.0,
                    "reason": "손절 유예(보유 {:.0f}초, 수익률 {:.2%})".format(hold_seconds, profit_rate),
                }
            return {
                "action": "sell",
                "score": 0.0,
                "reason": "장초반 손절가 도달",
            }
        if hold_seconds >= OPENING_MAX_HOLD_SECONDS:
            return {
                "action": "sell",
                "score": 0.0,
                "reason": "장초반 최대 보유시간 도달",
            }

        server_decision = self.call_ai_server("/predict-exit", {
            "code": code,
            "entry_price": entry_price,
            "current_price": current_price,
            "highest_price": highest_price,
            "hold_seconds": hold_seconds,
            "ticks": self.serialize_ticks(self.realtime_ticks.get(code, [])),
        })
        if server_decision is not None:
            logger.info("[AI서버 익절판단] {} action {} 점수 {:.2f} 모델 {} 사유 {}".format(
                code,
                server_decision.get("action", "hold"),
                server_decision.get("score", 0),
                server_decision.get("model_name", "unknown"),
                server_decision.get("reason", ""),
            ))
            return server_decision

        ticks = self.realtime_ticks.get(code, [])
        hold_score = scoring.compute_exit_hold_score(
            ticks=ticks,
            current_price=current_price,
            profit_rate=profit_rate,
            trailing_drop=trailing_drop,
            hold_seconds=hold_seconds,
            opening_max_spread_rate=OPENING_MAX_SPREAD_RATE,
            exit_min_profit_rate=EXIT_MIN_PROFIT_RATE,
            exit_strong_profit_rate=EXIT_STRONG_PROFIT_RATE,
            exit_trailing_drop_rate=EXIT_TRAILING_DROP_RATE,
            exit_stall_seconds=EXIT_STALL_SECONDS,
            opening_max_hold_seconds=OPENING_MAX_HOLD_SECONDS,
        )

        if profit_rate >= EXIT_STRONG_PROFIT_RATE:
            return {
                "action": "sell",
                "score": hold_score,
                "reason": "강한 수익 구간 도달 {:.2%}".format(profit_rate),
            }
        if profit_rate >= EXIT_MIN_PROFIT_RATE and trailing_drop <= -EXIT_TRAILING_DROP_RATE:
            return {
                "action": "sell",
                "score": hold_score,
                "reason": "고점 대비 밀림 {:.2%}".format(trailing_drop),
            }
        if profit_rate >= EXIT_MIN_PROFIT_RATE and hold_seconds >= EXIT_STALL_SECONDS and hold_score < EXIT_HOLD_SCORE_MIN:
            return {
                "action": "sell",
                "score": hold_score,
                "reason": "상승 지속 점수 약화 {:.2f}".format(hold_score),
            }

        return {
            "action": "hold",
            "score": hold_score,
            "reason": "상승 지속 점수 {:.2f}".format(hold_score),
        }

    def check_sell_signal(self, code, current_price):
        code = self.normalize_code(code)
        if code in self.pending_order_codes:
            return
        if code not in self.holding_codes and code not in self.best:
            return

        target_price = self.best.get(code)
        exit_decision = self.score_exit_timing(code, current_price)
        if exit_decision["action"] == "sell":
            self.place_sell_order(code, 0, "03", exit_decision["reason"])
            return
        if target_price is not None and current_price >= target_price and exit_decision["score"] < 0.65:
            self.place_sell_order(code, 0, "03", "목표가 도달 후 보유 점수 약화 {:.2f}".format(exit_decision["score"]))
        elif target_price is not None and current_price >= target_price:
            logger.info("[익절 보류] {} 목표가 도달, 보유 지속 점수 {:.2f}".format(code, exit_decision["score"]))

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
        codes_to_check = set(self.best.keys()) | set(self.holding_codes)
        codes_to_check = {c for c in codes_to_check if c}
        for code in codes_to_check:
            self.register_realtime_stock(code)
            last_tick = self.realtime_ticks.get(code, [{}])[-1]
            current_price = last_tick.get("close") or self.get_balance_current_price(code)
            if current_price:
                self.check_sell_signal(code, current_price)

    def check_pending_sells(self):
        # 실시간 슬롯에서 매 틱마다 동기 HTTP를 부르지 않도록, 일정 주기로 모아서 매도 판단을 수행한다.
        # 매도 의도 큐도 함께 재시도해 매매가능수량이 늦게 갱신되는 케이스를 빠르게 회수한다.
        try:
            self.process_pending_sell_intents()
        except Exception as e:
            logger.error("[매도 의도 처리 오류] {}".format(e))

        codes_to_check = set(self.best.keys()) | set(self.holding_codes)
        for code in codes_to_check:
            if not code:
                continue
            if code in self.pending_order_codes:
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

    def place_sell_order(self, code, order_price, order_gubun, reason):
        code = self.normalize_code(code)
        if code in self._selling_codes:
            logger.warning("[매도 중복 차단] {} 진행 중인 매도 있음".format(code))
            return
        if code in self.pending_sell_order_codes:
            logger.warning("[매도 중복 차단] {} 미체결 매도 주문 존재".format(code))
            return
        self._selling_codes.add(code)
        try:
            self._do_place_sell_order(code, order_price, order_gubun, reason)
        finally:
            self._selling_codes.discard(code)

    def _do_place_sell_order(self, code, order_price, order_gubun, reason):
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
                profit_rate = last_price / entry_price - 1
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


def main():
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()

    my_deposit = kiwoom.get_deposit()
    logger.info("남은 예수금 : %s", my_deposit)

    kiwoom.load_best()
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

    if not kiwoom.start_realtime_condition(CONDITION_NAME):
        logger.error("실시간 조건검색을 시작하지 못했습니다. 조건식 설정을 확인해주세요.")

    app.exec_()


if __name__ == "__main__":
    main()