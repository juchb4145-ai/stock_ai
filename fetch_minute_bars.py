"""오늘(또는 지정일) 매매한 종목의 1분봉을 키움 opt10080 으로 받아 캐시.

장 종료 후 별도로 실행하는 nightly job. main.py 에 일절 의존하지 않으며,
``review.intraday`` 는 본 모듈 없이 캐시 CSV 만 읽어 동작한다.

사용법:
    python fetch_minute_bars.py                      # 오늘
    python fetch_minute_bars.py 2026-04-30            # 특정 날짜
    python fetch_minute_bars.py 2026-04-30 --force    # 캐시 무시하고 재수집
    python fetch_minute_bars.py --codes 050890,038460 # 특정 코드만

저장:
    data/intraday/YYYYMMDD/<종목코드>.csv
    헤더: datetime,open,high,low,close,volume

키움 opt10080 (주식분봉차트조회요청):
    - 종목코드, 틱범위(=1: 1분), 수정주가구분(=1)
    - 응답 필드: 체결시간(YYYYMMDDHHMMSS), 시가/고가/저가/현재가, 거래량
    - 한 번 호출에 ~600개 봉 반환. 하루 분봉(390개)은 보통 1회로 충분.
      혹시 모자라면 prev_next 로 한 번 더 받는다.

오류 처리:
    - 종목별 호출 실패는 stderr 에 한 줄 로그만 남기고 다음 종목으로 진행.
    - 전체 실패가 아니라 부분 실패도 exit code 0 (review.intraday 가 fallback).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from collections import OrderedDict
from datetime import datetime
from typing import Iterable, List, Optional, Set


TRADE_LOG_DEFAULT = os.path.join("data", "trade_log.csv")
INTRADAY_DIR_DEFAULT = os.path.join("data", "intraday")

TR_TIMEOUT_MS = 7000
TR_INTERVAL_SECONDS = 0.35
SCREEN_NO = "0370"
RQ_NAME = "opt10080_min1"

# QApplication 인스턴스를 모듈 전역으로 유지한다.
# PyQt 는 QApplication 객체에 대한 강한 참조가 사라지면 즉시 정리하는 경우가
# 있어, QAxWidget 생성 시 "Must construct a QApplication before a QWidget"
# 경고가 뜬다. 함수 로컬 변수가 아니라 모듈 전역으로 잡아두면 fetch_for_codes
# 호출 사이에도 인스턴스가 살아있다.
_QAPP_REF = None


def _normalize_code(code: str) -> str:
    return str(code or "").strip().lstrip("A")


def collect_traded_codes(trade_log_path: str, target_date: str) -> List[str]:
    """trade_log.csv 에서 ``target_date`` 의 buy_order/chejan(체결) 종목코드 목록.

    중복 제거하되 입력 등장 순서를 유지한다.
    """
    if not os.path.exists(trade_log_path):
        raise FileNotFoundError(f"trade_log 가 없습니다: {trade_log_path}")
    seen: "OrderedDict[str, None]" = OrderedDict()
    with open(trade_log_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            logged_at = row.get("logged_at", "") or ""
            if not logged_at.startswith(target_date):
                continue
            event = row.get("event", "")
            if event not in ("buy_order", "chejan"):
                continue
            code = _normalize_code(row.get("code"))
            if not code:
                continue
            seen.setdefault(code, None)
    return list(seen.keys())


def _output_path(intraday_dir: str, target_date: str, code: str) -> str:
    yyyymmdd = target_date.replace("-", "")
    return os.path.join(intraday_dir, yyyymmdd, f"{_normalize_code(code)}.csv")


def needs_fetch(path: str, force: bool) -> bool:
    if force:
        return True
    if not os.path.exists(path):
        return True
    try:
        return os.path.getsize(path) <= len("datetime,open,high,low,close,volume\n") + 1
    except OSError:
        return True


# ---------------------------------------------------------------------------
# 키움 호출 (PyQt 의존)
# ---------------------------------------------------------------------------


class _KiwoomMinuteFetcher:
    """opt10080 분봉을 받아 (datetime, ohlcv) 행 리스트로 반환.

    PyQt5 / KHOPENAPI ActiveX 가 필요. 호출은 동기식 — 응답 콜백에서
    QEventLoop.exit() 로 깨운다(check_daily_realized.py 와 동일 패턴).
    """

    def __init__(self):
        from PyQt5.QAxContainer import QAxWidget   # noqa: WPS433  (런타임 import)
        from PyQt5.QtCore import QEventLoop

        self.widget = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login_loop = QEventLoop()
        self.tr_loop = QEventLoop()
        self.last_tr_at = 0.0
        self.rows: List[dict] = []
        self.has_next = False
        self._cur_code = ""
        self.widget.OnEventConnect.connect(self._on_event_connect)
        self.widget.OnReceiveTrData.connect(self._on_receive_tr_data)

    def login(self) -> None:
        self.widget.dynamicCall("CommConnect()")
        self.login_loop.exec_()

    def _on_event_connect(self, err_code):
        if err_code != 0:
            print(f"[fetch_minute_bars] 로그인 실패: {err_code}", file=sys.stderr)
        self.login_loop.exit()

    def _wait_for_tr_slot(self) -> None:
        elapsed = time.time() - self.last_tr_at
        if elapsed < TR_INTERVAL_SECONDS:
            time.sleep(TR_INTERVAL_SECONDS - elapsed)
        self.last_tr_at = time.time()

    def fetch(self, code: str, target_date: str, max_pages: int = 8) -> List[dict]:
        """code 의 1분봉을 받아 ``target_date`` 분만 시간 오름차순 리스트로 반환.

        키움 opt10080 응답의 페이지 순서(최신→과거 / 과거→최신) 가정에 의존하지
        않도록, 매 페이지 응답 후 self.rows 를 datetime 으로 명시적으로 정렬한
        뒤 self.rows[0](가장 과거) 의 날짜로 종료 조건을 평가한다.
        max_pages=8 — 페이지당 ~600봉 × 8 = 4800봉 (= 80시간) 으로 일반적 1분봉
        하루치 + 안전 마진을 충분히 커버한다.
        """
        self.rows = []
        self._cur_code = _normalize_code(code)

        from PyQt5.QtCore import QTimer

        prev_next = "0"
        for page in range(max_pages):
            self.widget.dynamicCall("SetInputValue(QString, QString)", "종목코드", self._cur_code)
            self.widget.dynamicCall("SetInputValue(QString, QString)", "틱범위", "1")
            self.widget.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self._wait_for_tr_slot()
            self.widget.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                RQ_NAME, "opt10080", int(prev_next), SCREEN_NO,
            )

            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(self.tr_loop.exit)
            timer.start(TR_TIMEOUT_MS)
            try:
                self.tr_loop.exec_()
            finally:
                timer.stop()

            # 페이지 응답 누적 후 명시적 정렬 — 키움 응답 순서 가정에 의존 안 함.
            self.rows.sort(key=lambda r: r["datetime"])

            if not self.has_next:
                break
            # 가장 과거(self.rows[0]) 가 target_date 이전이면 충분히 받았으니 종료.
            if self.rows and self.rows[0]["datetime"][:10] < target_date:
                break
            prev_next = "2"

        target_rows = [r for r in self.rows if r["datetime"][:10] == target_date]
        # 위에서 정렬했지만 안전을 위해 한 번 더.
        target_rows.sort(key=lambda r: r["datetime"])
        return target_rows

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next_, *_):
        if rqname != RQ_NAME:
            self.tr_loop.exit()
            return
        self.has_next = (str(next_).strip() == "2")
        count = self.widget.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        new_rows: List[dict] = []
        for index in range(count):
            ts = self.widget.dynamicCall(
                "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "체결시간",
            ).strip()
            if len(ts) != 14:
                continue
            try:
                dt_str = (
                    f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} "
                    f"{ts[8:10]}:{ts[10:12]}:{ts[12:14]}"
                )
            except IndexError:
                continue

            def _abs_int(name: str) -> int:
                raw = self.widget.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, name,
                ).strip()
                if not raw:
                    return 0
                try:
                    return abs(int(float(raw.replace(",", "").lstrip("+"))))
                except (TypeError, ValueError):
                    return 0

            new_rows.append({
                "datetime": dt_str,
                "open": _abs_int("시가"),
                "high": _abs_int("고가"),
                "low":  _abs_int("저가"),
                "close": _abs_int("현재가"),
                "volume": _abs_int("거래량"),
            })
        # 응답은 보통 최신 → 과거 순. 누적은 "전체 분봉" 을 갖되 정렬은 마지막에.
        # 페이지 호출이라 prepend 가 단순하다.
        self.rows = new_rows + self.rows
        self.tr_loop.exit()


# ---------------------------------------------------------------------------
# 저장
# ---------------------------------------------------------------------------


_CSV_HEADER = ["datetime", "open", "high", "low", "close", "volume"]


def write_intraday_csv(path: str, rows: Iterable[dict]) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    written = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_CSV_HEADER)
        for row in rows:
            writer.writerow([
                row["datetime"], row["open"], row["high"], row["low"],
                row["close"], row["volume"],
            ])
            written += 1
    return written


# ---------------------------------------------------------------------------
# 외부 진입점
# ---------------------------------------------------------------------------


def fetch_for_codes(
    codes: List[str],
    target_date: str,
    intraday_dir: str = INTRADAY_DIR_DEFAULT,
    force: bool = False,
    fetcher: Optional[_KiwoomMinuteFetcher] = None,
) -> dict:
    """주어진 codes 에 대해 분봉을 받아 캐시. 결과 통계 dict 반환.

    fetcher 를 주입하면 키움 호출을 mock 으로 대체 가능(테스트용).
    """
    stats = {"target_date": target_date, "fetched": [], "cached": [], "failed": []}
    if not codes:
        return stats

    own_fetcher = False
    if fetcher is None:
        try:
            from PyQt5.QtWidgets import QApplication   # noqa: WPS433
        except ImportError:
            print("[fetch_minute_bars] PyQt5 가 설치되지 않았습니다.", file=sys.stderr)
            stats["failed"] = list(codes)
            return stats
        global _QAPP_REF
        if _QAPP_REF is None:
            _QAPP_REF = QApplication.instance() or QApplication(sys.argv)
        fetcher = _KiwoomMinuteFetcher()
        fetcher.login()
        own_fetcher = True

    try:
        for code in codes:
            path = _output_path(intraday_dir, target_date, code)
            if not needs_fetch(path, force):
                stats["cached"].append(code)
                continue
            try:
                rows = fetcher.fetch(code, target_date)
            except Exception as exc:   # noqa: BLE001
                print(f"[fetch_minute_bars] {code} 호출 실패: {exc}", file=sys.stderr)
                stats["failed"].append(code)
                continue
            if not rows:
                print(f"[fetch_minute_bars] {code} 분봉 0건", file=sys.stderr)
                stats["failed"].append(code)
                continue
            n = write_intraday_csv(path, rows)
            stats["fetched"].append({"code": code, "rows": n, "path": path})
    finally:
        if own_fetcher:
            # QAxWidget 는 별도 dispose 불필요. QApplication 도 종료하지 않는다(공유 가능).
            pass
    return stats


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python fetch_minute_bars.py",
        description="trade_log 에 등장한 종목의 1분봉을 키움 opt10080 으로 캐시.",
    )
    parser.add_argument(
        "target_date", nargs="?", default=time.strftime("%Y-%m-%d"),
        help="대상 영업일 YYYY-MM-DD (기본: 오늘).",
    )
    parser.add_argument(
        "--codes", default=None,
        help="콤마로 구분된 종목코드. 지정하면 trade_log 가 아니라 이 리스트만 받는다.",
    )
    parser.add_argument(
        "--trade-log", default=TRADE_LOG_DEFAULT,
        help=f"trade_log.csv 경로 (기본: {TRADE_LOG_DEFAULT}).",
    )
    parser.add_argument(
        "--intraday-dir", default=INTRADAY_DIR_DEFAULT,
        help=f"저장 디렉토리 (기본: {INTRADAY_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="캐시(이미 존재하는 csv) 를 무시하고 재수집.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    if args.codes:
        codes = [_normalize_code(c) for c in args.codes.split(",") if c.strip()]
    else:
        try:
            codes = collect_traded_codes(args.trade_log, args.target_date)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if not codes:
        print(f"{args.target_date} 매매 기록이 없습니다.", file=sys.stderr)
        return 0

    print(f"== fetch_minute_bars {args.target_date} (codes={len(codes)}) ==")
    stats = fetch_for_codes(
        codes, args.target_date, intraday_dir=args.intraday_dir, force=args.force,
    )
    print(f"  - fetched: {len(stats['fetched'])}")
    for entry in stats["fetched"]:
        print(f"      · {entry['code']}: {entry['rows']} rows → {entry['path']}")
    print(f"  - cached:  {len(stats['cached'])}")
    print(f"  - failed:  {len(stats['failed'])}")
    if stats["failed"]:
        print(f"      · {','.join(stats['failed'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
