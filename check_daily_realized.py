import csv
import os
import sys
import time
from collections import defaultdict

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtWidgets import QApplication


TRADE_LOG_CSV = os.path.join("data", "trade_log.csv")
TR_TIMEOUT_MS = 7000
TR_INTERVAL_SECONDS = 0.35


def parse_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return abs(int(str(value).strip().lstrip("+").lstrip("-")))
    except (TypeError, ValueError):
        return default


def parse_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).strip().replace(",", ""))
    except (TypeError, ValueError):
        return default


def normalize_code(code):
    return str(code or "").strip().lstrip("A")


def load_trade_log_rows():
    if not os.path.exists(TRADE_LOG_CSV):
        raise FileNotFoundError("거래 로그가 없습니다: {}".format(TRADE_LOG_CSV))
    with open(TRADE_LOG_CSV, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def latest_log_execution_summary(rows, today):
    summary = defaultdict(lambda: {
        "name": "",
        "buy_quantity": 0,
        "buy_avg": 0,
        "sell_quantity": 0,
        "sell_avg": 0,
        "log_profit_rate": None,
    })

    for row in rows:
        logged_at = row.get("logged_at", "")
        if not logged_at.startswith(today):
            continue
        code = normalize_code(row.get("code"))
        if not code:
            continue
        item = summary[code]
        if row.get("name"):
            item["name"] = row.get("name")
        if row.get("event") == "sell_order" and row.get("profit_rate") not in ("", None):
            item["log_profit_rate"] = parse_float(row.get("profit_rate"))
        if row.get("event") != "chejan" or row.get("order_status") != "체결":
            continue

        side = row.get("side", "")
        quantity = parse_int(row.get("executed_quantity"))
        avg_price = parse_int(row.get("executed_price"))
        if quantity <= 0 or avg_price <= 0:
            continue
        if side == "buy" and quantity >= item["buy_quantity"]:
            item["buy_quantity"] = quantity
            item["buy_avg"] = avg_price
        elif side == "sell" and quantity >= item["sell_quantity"]:
            item["sell_quantity"] = quantity
            item["sell_avg"] = avg_price

    return dict(summary)


class KiwoomDailyRealized(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.login_loop = QEventLoop()
        self.tr_loop = QEventLoop()
        self.account_number = ""
        self.last_tr_at = 0
        self.rows = []
        self.total_profit = 0

    def login(self):
        self.dynamicCall("CommConnect()")
        self.login_loop.exec_()
        accounts = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        self.account_number = accounts.split(";")[0].strip()
        if not self.account_number:
            raise RuntimeError("계좌번호를 확인하지 못했습니다.")
        print("계좌번호:", self.account_number)

    def _on_event_connect(self, err_code):
        if err_code != 0:
            print("로그인 실패:", err_code)
        self.login_loop.exit()

    def wait_for_tr_slot(self):
        elapsed = time.time() - self.last_tr_at
        if elapsed < TR_INTERVAL_SECONDS:
            time.sleep(TR_INTERVAL_SECONDS - elapsed)
        self.last_tr_at = time.time()

    def request_daily_realized(self, code=""):
        self.rows = []
        self.total_profit = 0
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", normalize_code(code))
        self.wait_for_tr_slot()
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10077", "opt10077", 0, "0360")

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self.tr_loop.exit)
        timer.start(TR_TIMEOUT_MS)
        try:
            self.tr_loop.exec_()
        finally:
            timer.stop()
        return self.rows

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, *_):
        if rqname != "opt10077":
            self.tr_loop.exit()
            return

        total_profit = self.dynamicCall(
            "GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "당일실현손익"
        ).strip()
        self.total_profit = parse_int(total_profit)

        count = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        result = []
        for index in range(count):
            row = {
                "code": normalize_code(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "종목코드"
                )),
                "name": self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "종목명"
                ).strip(),
                "quantity": parse_int(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "체결량"
                )),
                "buy_avg": parse_int(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "매입단가"
                )),
                "sell_avg": parse_int(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "체결가"
                )),
                "realized_profit": parse_int(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "당일매도손익"
                )),
                "realized_rate": parse_float(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "손익율"
                )),
                "fee": parse_int(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "당일매매수수료"
                )),
                "tax": parse_int(self.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "당일매매세금"
                )),
            }
            if row["code"] or row["name"]:
                result.append(row)
        self.rows = result
        self.tr_loop.exit()


def compare(today):
    trade_rows = load_trade_log_rows()
    log_summary = latest_log_execution_summary(trade_rows, today)
    codes = sorted(log_summary.keys())
    if not codes:
        print("{} trade_log.csv 매매 기록이 없습니다.".format(today))
        return

    app = QApplication(sys.argv)
    kiwoom = KiwoomDailyRealized()
    kiwoom.login()

    actual_by_code = {}
    for code in codes:
        rows = kiwoom.request_daily_realized(code)
        for row in rows:
            if row["code"]:
                actual_by_code[row["code"]] = row

    print("\n=== 당일실현손익(opt10077) vs trade_log 비교 ===")
    print("날짜:", today)
    print("코드,종목,로그수익률,로그매입가,로그매도가,키움매입가,키움매도가,키움손익률,손익금액,수수료,세금,차이")
    for code in codes:
        log = log_summary[code]
        actual = actual_by_code.get(code)
        if actual is None:
            print("{},{},로그만 존재,{},{},,,,,,,키움 실현손익 없음".format(
                code,
                log["name"],
                log["buy_avg"],
                log["sell_avg"],
            ))
            continue
        log_profit_rate = log["log_profit_rate"]
        log_profit_text = "" if log_profit_rate is None else "{:.4f}%".format(log_profit_rate * 100)
        diff = ""
        if log_profit_rate is not None:
            diff = "{:.4f}%p".format(actual["realized_rate"] - log_profit_rate * 100)
        print("{},{},{},{},{},{},{},{:.4f}%,{},{},{},{}".format(
            code,
            actual["name"] or log["name"],
            log_profit_text,
            log["buy_avg"],
            log["sell_avg"],
            actual["buy_avg"],
            actual["sell_avg"],
            actual["realized_rate"],
            actual["realized_profit"],
            actual["fee"],
            actual["tax"],
            diff,
        ))


if __name__ == "__main__":
    target_day = sys.argv[1] if len(sys.argv) > 1 else time.strftime("%Y-%m-%d")
    compare(target_day)
