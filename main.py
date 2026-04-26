from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import time

from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import numpy as np
import pickle

CONDITION_NAME = "단테떡상이"  # 비워두면 저장된 조건식 중 첫 번째 조건식을 사용합니다.
CONDITION_SCREEN_NO = "0150"
REALTIME_SCREEN_NO = "0160"
ORDER_SCREEN_NO = "0001"
BUY_QUANTITY = 1
MIN_EXPECTED_RETURN = 0.01
STOP_LOSS_RATE = -0.03
CONDITION_PROCESS_INTERVAL_MS = 2000
CONDITION_COOLDOWN_SECONDS = 60

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
    "42": "매도호가1",
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
    "153": "매수 거래원",
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

def get_fid(fid_name):
    keys = [key for key, value in FID_CODES.items() if value == fid_name]
    return keys[0]


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
        self.holding_codes = set()
        self.pending_order_codes = set()
        self.bought_codes = set()
        self.order_prices = {}
        self.realtime_registered_codes = set()
        self.condition_timer = QTimer()
        self.condition_timer.timeout.connect(self.process_next_condition_stock)

    
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
        print(screen_no, rqname, trcode, msg)
    
    def _on_receive_chejan(self, gubun, cnt, fid_list):
        print(gubun, cnt, fid_list)

        for fid in fid_list.split(';'):
            if not fid:
                continue
            code = self.dynamicCall("GetChejanData(int)", "9001")[1:]
            data = self.dynamicCall("GetChejanData(int)", fid).lstrip("+").lstrip("-")
            if data.isdigit():
                data = int(data)
            name = FID_CODES.get(fid, fid)
            print('{}: {}'.format(name, data))
            if fid == "913":
                code = self.normalize_code(code)
                if data == "체결":
                    self.pending_order_codes.discard(code)
                elif data in ("접수", "확인"):
                    self.pending_order_codes.add(code)

    def _on_receive_condition_ver(self, ret, msg):
        print("조건식 로드 결과:", ret, msg)
        self.conditions = self.get_condition_name_list()
        if self.condition_event_loop is not None:
            self.condition_event_loop.exit()

    def _on_receive_tr_condition(self, screen_no, code_list, condition_name, condition_index, next):
        codes = [code for code in code_list.split(';') if code]
        print("[조건검색 초기조회] {}({}) {}건".format(condition_name, condition_index, len(codes)))
        for code in codes:
            self.enqueue_condition_stock(code, condition_name, "I")

    def _on_receive_real_condition(self, code, event_type, condition_name, condition_index):
        if event_type == "I":
            print("[조건편입] {} {}({})".format(code, condition_name, condition_index))
            self.enqueue_condition_stock(code, condition_name, event_type)
        elif event_type == "D":
            print("[조건이탈] {} {}({})".format(code, condition_name, condition_index))

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, v1, v2, v3, v4):
        print(screen_no, rqname, trcode, record_name, next)
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
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입금액")
                available_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매매가능수량")

                code = code.strip()[1:]
                code_name = code_name.strip()
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)
                current_price = int(current_price)

                total_purchase_price = int(total_purchase_price)
                available_quantity = int(available_quantity)

                box.append([code, code_name, quantity, purchase_price, return_rate, current_price, total_purchase_price, available_quantity])
            self.tr_data = box


        self.tr_event_loop.exit()
        time.sleep(1)    
        
    def _login_slot(self, err_code):
        if err_code == 0:
            print("Connected to Kiwoom")
        else:
            print("Failed to connect to Kiwoom")
        self.login_event_loop.exit()

    def _comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_number(self):
        account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCLIST")
        account_number = account_list.split(';')[0]
        print("나의 계죄번호 : ", account_number)
        return account_number

    def get_code_list_stock_market(self, market_type):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]
        return code_list

    def get_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def load_conditions(self):
        self.condition_event_loop = QEventLoop()
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
        print("저장된 조건식 목록:", conditions)
        return conditions

    def select_condition(self, condition_name=CONDITION_NAME):
        if not self.conditions:
            self.load_conditions()

        if not self.conditions:
            print("저장된 조건식이 없습니다. 영웅문에서 조건식을 먼저 저장해주세요.")
            return None

        if condition_name:
            condition_index = self.conditions.get(condition_name)
            if condition_index is None:
                print("'{}' 조건식을 찾을 수 없습니다.".format(condition_name))
                return None
            self.selected_condition = (condition_name, condition_index)
        else:
            first_name = next(iter(self.conditions))
            self.selected_condition = (first_name, self.conditions[first_name])
            print("CONDITION_NAME이 비어 있어 첫 번째 조건식을 사용합니다:", first_name)

        return self.selected_condition

    def start_realtime_condition(self, condition_name=CONDITION_NAME):
        selected = self.select_condition(condition_name)
        if selected is None:
            return False

        name, index = selected
        result = self.dynamicCall(
            "SendCondition(QString, QString, int, int)",
            CONDITION_SCREEN_NO,
            name,
            index,
            1,
        )
        print("실시간 조건검색 시작:", name, index, "결과:", result)
        if result == 1:
            self.condition_timer.start(CONDITION_PROCESS_INTERVAL_MS)
            return True
        return False

    def enqueue_condition_stock(self, code, condition_name="", event_type="I"):
        now = time.time()
        last_at = self.last_signal_at.get(code, 0)
        if now - last_at < CONDITION_COOLDOWN_SECONDS:
            return
        if code in self.pending_condition_codes:
            return

        self.last_signal_at[code] = now
        self.pending_condition_codes.append(code)
        print("[조건검색 대기열] {} {} {} 대기 {}건".format(code, condition_name, event_type, len(self.pending_condition_codes)))
    
    def get_price(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081", "opt10081", 0, "0020")
        self.tr_event_loop.exec_()
        time.sleep(1)

        total = self.tr_data

        while self.isnext:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081", "opt10081", 2, "0020")
            self.tr_event_loop.exec_()
            total += self.tr_data
            time.sleep(1)
        
        df = pd.DataFrame(total, columns=['date', 'open', 'high', 'low', 'close', 'volume']).set_index('date')
        df = df.drop_duplicates()
        df = df.sort_index()
        return df

    def get_deposit(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00001", "opw00001", 0, "0002")
        self.tr_event_loop.exec_()
        return self.tr_data

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_gubun, order_no = ""):
        order_result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", [rqname, screen_no, self.account_number, order_type, code, order_quantity, order_price, order_gubun, order_no])
        return order_result
    
    def get_order(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075", "opt10075", 0, "0002")
        self.tr_event_loop.exec_()
        return self.tr_data

    def get_balance(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018", "opw00018", 0, "0002")
        self.tr_event_loop.exec_()
        return self.tr_data

    def _on_receive_real_data(self, s_code, real_type, real_data):
        if real_type == "장시작시간":
            pass
        elif real_type == "주식체결":
            signed_at = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("체결시간"))
            close = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("현재가"))
            close = abs(int(close))

            high = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("고가"))
            high = abs(int(high))

            open = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("시가"))
            open = abs(int(open))

            low = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("저가"))
            low = abs(int(low))

            top_priority_ask = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("(최우선)매도호가"))
            top_priority_ask = abs(int(top_priority_ask))

            top_priority_bid = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("(최우선)매수호가"))
            top_priority_bid = abs(int(top_priority_bid))

            accum_volume = self.dynamicCall("GetCommRealData(QString, QString)", s_code, get_fid("누적거래량"))
            accum_volume = abs(int(accum_volume))

            self.universe_realtime_transaction_info.append([s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume])
            self.check_sell_signal(s_code, close)
    
    def set_real_reg(self, str_screen_no, str_code_list, str_fid_list, str_opt_type):
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", str_screen_no, str_code_list, str_fid_list, str_opt_type)
        time.sleep(1)

    def process_next_condition_stock(self):
        if self.processing_condition or not self.pending_condition_codes:
            return

        code = self.pending_condition_codes.pop(0)
        self.processing_condition = True
        try:
            self.handle_condition_stock(code)
        except Exception as e:
            print("[조건검색 처리 오류] {} {}".format(code, e))
        finally:
            self.processing_condition = False

    def normalize_code(self, code):
        return code.strip().lstrip("A")

    def save_best(self):
        with open('best.dat', 'wb') as f:
            pickle.dump(self.best, f)

    def load_best(self):
        try:
            with open('best.dat', 'rb') as f:
                self.best = pickle.load(f)
        except FileNotFoundError:
            self.best = {}
        except Exception as e:
            print("best.dat 로드 실패:", e)
            self.best = {}

    def update_account_status(self):
        self.holding_codes = set()
        self.pending_order_codes = set()

        try:
            for balance in self.get_balance():
                code = self.normalize_code(balance[0])
                self.holding_codes.add(code)
                self.order_prices[code] = balance[3]
        except Exception as e:
            print("잔고 조회 실패:", e)

        try:
            for order in self.get_order():
                code = self.normalize_code(order[0])
                left_quantity = order[8]
                if left_quantity > 0:
                    self.pending_order_codes.add(code)
        except Exception as e:
            print("미체결 조회 실패:", e)

    def should_skip_buy(self, code):
        if code in self.holding_codes:
            print("[매수 제외] {} 이미 보유 중".format(code))
            return True
        if code in self.pending_order_codes:
            print("[매수 제외] {} 미체결 주문 존재".format(code))
            return True
        if code in self.bought_codes:
            print("[매수 제외] {} 오늘 이미 매수 주문 처리".format(code))
            return True
        return False

    def handle_condition_stock(self, code):
        code = self.normalize_code(code)
        self.update_account_status()
        if self.should_skip_buy(code):
            return

        prediction = self.predict_stock(code)
        if prediction is None:
            return

        expected_return = prediction["expected_return"]
        if expected_return < MIN_EXPECTED_RETURN:
            print("[매수 보류] {} 기대수익률 {:.2%} < 기준 {:.2%}".format(code, expected_return, MIN_EXPECTED_RETURN))
            return

        self.place_buy_order(code, prediction)

    def place_buy_order(self, code, prediction):
        current_price = prediction["current_price"]
        deposit = self.get_deposit()
        needed_cash = current_price * BUY_QUANTITY
        if deposit < needed_cash:
            print("[매수 보류] {} 예수금 부족: 필요 {}, 가능 {}".format(code, needed_cash, deposit))
            return

        result = self.send_order("buy", ORDER_SCREEN_NO, 1, code, BUY_QUANTITY, 0, "03")
        if result == 0:
            self.best[code] = prediction["predict_price"]
            self.order_prices[code] = current_price
            self.pending_order_codes.add(code)
            self.bought_codes.add(code)
            self.save_best()
            self.register_realtime_stock(code)
            print("[매수 주문] {} 현재가 {} 예측가 {} 기대수익률 {:.2%}".format(
                prediction["name"],
                current_price,
                prediction["predict_price"],
                prediction["expected_return"],
            ))
        else:
            print("[매수 실패] {} SendOrder 결과 {}".format(code, result))

    def register_realtime_stock(self, code):
        code = self.normalize_code(code)
        if code in self.realtime_registered_codes:
            return

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
        opt_type = "0" if not self.realtime_registered_codes else "1"
        self.set_real_reg(REALTIME_SCREEN_NO, code, fids, opt_type)
        self.realtime_registered_codes.add(code)

    def check_sell_signal(self, code, current_price):
        code = self.normalize_code(code)
        target_price = self.best.get(code)
        if target_price is None:
            return

        entry_price = self.order_prices.get(code)
        if current_price >= target_price:
            self.place_sell_order(code, target_price, "00", "목표가 도달")
        elif entry_price and current_price <= int(entry_price * (1 + STOP_LOSS_RATE)):
            self.place_sell_order(code, 0, "03", "손절가 도달")

    def place_sell_order(self, code, order_price, order_gubun, reason):
        self.update_account_status()

        sell_quantity = 0
        for balance in self.get_balance():
            balance_code = self.normalize_code(balance[0])
            if balance_code == code:
                sell_quantity = balance[7]
                break

        if sell_quantity <= 0:
            print("[매도 보류] {} 매매가능수량 없음".format(code))
            return

        result = self.send_order("sell", ORDER_SCREEN_NO, 2, code, sell_quantity, order_price, order_gubun)
        if result == 0:
            self.pending_order_codes.add(code)
            self.best.pop(code, None)
            self.save_best()
            print("[매도 주문] {} {} 수량 {} 가격 {} 구분 {}".format(code, reason, sell_quantity, order_price, order_gubun))
        else:
            print("[매도 실패] {} SendOrder 결과 {}".format(code, result))

    def predict_stock(self, code):

        # 종목코드를 가져와서 해당 종목의 모든 주식 가격 데이터 가져와서 데이터 프레임으로 만들기
        df = self.get_price(code)
        if len(df) < 2:
            print("[예측 실패] {} 학습 데이터 부족".format(code))
            return None

        data = []
        target = []

        # 특정일의 주식 가격은 data, 특정일 다음날의 종가 가격은 target에 할당
        for i in range(len(df) - 1):
            a = list(df.iloc[i])
            b = df.iloc[i + 1, 3]
            data.append(a)
            target.append(b)
        
        data = np.array(data)
        target = np.array(target)

        # 랜덤 포레스트 머신러닝 모델 활용
        rf = RandomForestRegressor(oob_score=True, random_state=1234)
        # 모델 학습
        rf.fit(data, target)

        # 현재 날짜의 주식 가격을 today_price 변수에 할당
        today_price = list(df.iloc[-1])

        # 현재 날짜의 가격을 통해 다음날 종가 예측
        predict_price = round(int(rf.predict([today_price])[0]), -2)
        current_price = int(df.iloc[-1]['close'])
        expected_return = (predict_price - current_price) / current_price
        name = self.get_code_name(code)
        print("[예측] {} 현재가 {} 예측가 {} 기대수익률 {:.2%}".format(name, current_price, predict_price, expected_return))
        return {
            "code": code,
            "name": name,
            "current_price": current_price,
            "predict_price": predict_price,
            "expected_return": expected_return,
        }

app = QApplication(sys.argv)
kiwoom = Kiwoom()

my_deposit = kiwoom.get_deposit()
print("남은 예수금 : ", my_deposit)

kiwoom.load_best()
kiwoom.update_account_status()
print("현재가지고 있는 종목: {}".format(kiwoom.get_balance()))
print("미체결 종목: {}".format(kiwoom.pending_order_codes))

for code in list(kiwoom.best.keys()):
    if code in kiwoom.holding_codes:
        kiwoom.register_realtime_stock(code)

if not kiwoom.start_realtime_condition(CONDITION_NAME):
    print("실시간 조건검색을 시작하지 못했습니다. 조건식 설정을 확인해주세요.")

app.exec_()