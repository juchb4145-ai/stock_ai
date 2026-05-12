"""키움 opt20006 으로 KOSPI/KOSDAQ 일봉을 받아 매크로 컨텍스트 JSON 으로 저장.

장 종료 후 별도로 실행하는 nightly job. main.py 에 일절 의존하지 않으며,
``review.market_context`` 가 본 모듈 없이 JSON 만 읽어 동작한다.

사용법:
    python fetch_market_context.py                      # 오늘
    python fetch_market_context.py 2026-04-30            # 특정 날짜
    python fetch_market_context.py --force               # 캐시 무시 재수집

저장:
    data/reviews/market_context_YYYY-MM-DD.json

키움 opt20006 (업종일봉조회요청):
    - 입력: 업종코드(001=KOSPI, 101=KOSDAQ), 기준일자(YYYYMMDD)
    - 응답: 일자별 일봉 OHLC 시계열 (최신 → 과거 순서)
    - 응답 필드: 일자(YYYYMMDD), 현재가(=종가), 시가, 고가, 저가, 거래량
    - 한 번 호출에 ~600일 반환. 우리는 최근 2 영업일만 사용한다(전일 종가 대비
      등락률 계산용).

매크로 구성:
    - kospi_close                : 당일 종가
    - kospi_close_return         : 당일 종가 / 전일 종가 - 1
    - kospi_intraday_high_return : 당일 고가 / 당일 시가 - 1 (일중 최대 상승률)
    - KOSDAQ 도 동일 3개 필드

오류 처리:
    - KOSPI/KOSDAQ 중 한쪽 호출 실패 시 해당 필드만 None 으로 두고 다른쪽은 살린다.
    - 두 쪽 다 실패하면 exit code 1, 부분 성공은 0.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Dict, List, Optional

from review.market_context import (
    REVIEWS_DIR_DEFAULT,
    MarketContext,
    context_path,
    save_market_context,
)


# 업종 코드 (키움 매뉴얼: KRX 종합지수)
INDEX_CODES: Dict[str, str] = {
    "kospi": "001",
    "kosdaq": "101",
}

TR_TIMEOUT_MS = 7000
TR_INTERVAL_SECONDS = 0.35
SCREEN_NO = "0371"
RQ_NAME = "opt20006_daily"

# QApplication 강한 참조 — fetch_minute_bars.py 와 동일한 사유.
_QAPP_REF = None


def _yyyymmdd(date: str) -> str:
    return date.replace("-", "")


def _output_path(reviews_dir: str, target_date: str) -> str:
    return context_path(target_date, reviews_dir)


def needs_fetch(path: str, force: bool) -> bool:
    if force:
        return True
    if not os.path.exists(path):
        return True
    try:
        return os.path.getsize(path) <= 2  # 빈 파일/거의 빈 파일이면 재수집
    except OSError:
        return True


# ---------------------------------------------------------------------------
# 키움 호출 (PyQt 의존)
# ---------------------------------------------------------------------------


class _KiwoomIndexFetcher:
    """opt20006 일봉을 받아 ``[{'date','open','high','low','close','volume'}, ...]`` 반환.

    응답은 최신 → 과거 순. 우리가 항상 명시적으로 정렬해서 가장 최근 N 영업일만 사용.
    """

    def __init__(self):
        from PyQt5.QAxContainer import QAxWidget   # noqa: WPS433
        from PyQt5.QtCore import QEventLoop

        self.widget = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login_loop = QEventLoop()
        self.tr_loop = QEventLoop()
        self.last_tr_at = 0.0
        self.rows: List[dict] = []
        self._cur_index = ""
        self.widget.OnEventConnect.connect(self._on_event_connect)
        self.widget.OnReceiveTrData.connect(self._on_receive_tr_data)

    def login(self) -> None:
        self.widget.dynamicCall("CommConnect()")
        self.login_loop.exec_()

    def _on_event_connect(self, err_code):
        if err_code != 0:
            print(f"[fetch_market_context] 로그인 실패: {err_code}", file=sys.stderr)
        self.login_loop.exit()

    def _wait_for_tr_slot(self) -> None:
        elapsed = time.time() - self.last_tr_at
        if elapsed < TR_INTERVAL_SECONDS:
            time.sleep(TR_INTERVAL_SECONDS - elapsed)
        self.last_tr_at = time.time()

    def fetch_daily(self, index_code: str, target_date: str) -> List[dict]:
        """업종 일봉을 받아 시간 오름차순 리스트로 반환. 응답이 비면 빈 리스트."""
        from PyQt5.QtCore import QTimer

        self.rows = []
        self._cur_index = index_code

        self.widget.dynamicCall("SetInputValue(QString, QString)", "업종코드", index_code)
        self.widget.dynamicCall("SetInputValue(QString, QString)", "기준일자", _yyyymmdd(target_date))
        self._wait_for_tr_slot()
        self.widget.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            RQ_NAME, "opt20006", 0, SCREEN_NO,
        )

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self.tr_loop.exit)
        timer.start(TR_TIMEOUT_MS)
        try:
            self.tr_loop.exec_()
        finally:
            timer.stop()

        self.rows.sort(key=lambda r: r["date"])
        return list(self.rows)

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next_, *_):
        if rqname != RQ_NAME:
            self.tr_loop.exit()
            return
        count = self.widget.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        new_rows: List[dict] = []
        for index in range(count):
            ts = self.widget.dynamicCall(
                "GetCommData(QString, QString, int, QString)", trcode, rqname, index, "일자",
            ).strip()
            if len(ts) != 8:
                continue
            try:
                dt_str = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"
            except IndexError:
                continue

            def _abs_float(name: str) -> float:
                raw = self.widget.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, index, name,
                ).strip()
                if not raw:
                    return 0.0
                try:
                    return abs(float(raw.replace(",", "").lstrip("+")))
                except (TypeError, ValueError):
                    return 0.0

            new_rows.append({
                "date": dt_str,
                "open": _abs_float("시가"),
                "high": _abs_float("고가"),
                "low":  _abs_float("저가"),
                "close": _abs_float("현재가"),
                "volume": _abs_float("거래량"),
            })
        self.rows = new_rows + self.rows
        self.tr_loop.exit()


# ---------------------------------------------------------------------------
# 매크로 변환
# ---------------------------------------------------------------------------


def _compute_returns_for_target(
    daily_rows: List[dict],
    target_date: str,
) -> Dict[str, Optional[float]]:
    """일봉 행 리스트에서 target_date 기준의 close/close_return/intraday_high_return 산출.

    Args:
        daily_rows: 시간 오름차순 일봉 (각 항목: ``{date, open, high, low, close, volume}``).
        target_date: ``YYYY-MM-DD``.

    Returns:
        ``{close, close_return, intraday_high_return}`` — 없으면 None.
    """
    out: Dict[str, Optional[float]] = {
        "close": None,
        "close_return": None,
        "intraday_high_return": None,
    }
    if not daily_rows:
        return out

    # target_date 행 찾기 — 정확 일치 우선, 없으면 가장 최근(<=target).
    target_row: Optional[dict] = None
    prev_row: Optional[dict] = None
    for i, row in enumerate(daily_rows):
        d = row.get("date", "")
        if d == target_date:
            target_row = row
            if i > 0:
                prev_row = daily_rows[i - 1]
            break
        if d < target_date:
            prev_row = row
        else:
            break

    if target_row is None:
        # target_date 행이 없으면 가장 최근 영업일을 target 으로 — 휴장일 fallback.
        eligible = [r for r in daily_rows if r.get("date", "") <= target_date]
        if not eligible:
            return out
        target_row = eligible[-1]
        prev_row = eligible[-2] if len(eligible) >= 2 else None

    today_close = float(target_row.get("close") or 0)
    today_open = float(target_row.get("open") or 0)
    today_high = float(target_row.get("high") or 0)
    if today_close > 0:
        out["close"] = today_close
    if prev_row is not None:
        prev_close = float(prev_row.get("close") or 0)
        if prev_close > 0 and today_close > 0:
            out["close_return"] = today_close / prev_close - 1
    if today_open > 0 and today_high > 0:
        out["intraday_high_return"] = today_high / today_open - 1

    return out


def _fetch_index(
    fetcher: "_KiwoomIndexFetcher",
    index_label: str,
    index_code: str,
    target_date: str,
) -> Dict[str, Optional[float]]:
    """단일 업종 fetch + 매크로 산출. 실패는 빈 dict."""
    try:
        rows = fetcher.fetch_daily(index_code, target_date)
    except Exception as exc:   # noqa: BLE001
        print(f"[fetch_market_context] {index_label} fetch 실패: {exc}", file=sys.stderr)
        return {"close": None, "close_return": None, "intraday_high_return": None}
    if not rows:
        print(f"[fetch_market_context] {index_label} 일봉 0건", file=sys.stderr)
        return {"close": None, "close_return": None, "intraday_high_return": None}
    return _compute_returns_for_target(rows, target_date)


# ---------------------------------------------------------------------------
# 외부 진입점
# ---------------------------------------------------------------------------


def fetch_market_context(
    target_date: str,
    reviews_dir: str = REVIEWS_DIR_DEFAULT,
    *,
    fetcher: Optional["_KiwoomIndexFetcher"] = None,
    force: bool = False,
) -> Optional[MarketContext]:
    """KOSPI/KOSDAQ 일봉을 받아 ``MarketContext`` 로 저장 후 반환.

    이미 캐시(JSON 파일) 가 있으면 재수집하지 않고 None 을 반환한다(force=True 면
    무시). KOSPI/KOSDAQ 중 한쪽 실패는 부분 결과로 저장한다.
    fetcher 를 주입하면 키움 호출을 mock 으로 대체 가능(테스트용).
    """
    out_path = _output_path(reviews_dir, target_date)
    if not needs_fetch(out_path, force):
        return None

    own_fetcher = False
    if fetcher is None:
        try:
            from PyQt5.QtWidgets import QApplication   # noqa: WPS433
        except ImportError:
            print("[fetch_market_context] PyQt5 가 설치되지 않았습니다.", file=sys.stderr)
            return None
        global _QAPP_REF
        if _QAPP_REF is None:
            _QAPP_REF = QApplication.instance() or QApplication(sys.argv)
        fetcher = _KiwoomIndexFetcher()
        fetcher.login()
        own_fetcher = True

    try:
        kospi = _fetch_index(fetcher, "KOSPI", INDEX_CODES["kospi"], target_date)
        kosdaq = _fetch_index(fetcher, "KOSDAQ", INDEX_CODES["kosdaq"], target_date)
    finally:
        if own_fetcher:
            pass  # QAxWidget 는 별도 dispose 불필요

    # 두 쪽 다 실패면 저장 안 함.
    if (
        kospi["close"] is None and kospi["close_return"] is None
        and kosdaq["close"] is None and kosdaq["close_return"] is None
    ):
        print(
            f"[fetch_market_context] {target_date} KOSPI/KOSDAQ 둘 다 fetch 실패 -- JSON 미작성",
            file=sys.stderr,
        )
        return None

    ctx = MarketContext(
        date=target_date,
        kospi_close_return=kospi["close_return"],
        kosdaq_close_return=kosdaq["close_return"],
        kospi_intraday_high_return=kospi["intraday_high_return"],
        kosdaq_intraday_high_return=kosdaq["intraday_high_return"],
        kospi_close=kospi["close"],
        kosdaq_close=kosdaq["close"],
        source="kiwoom_opt20006",
    )
    save_market_context(ctx, reviews_dir=reviews_dir)
    return ctx


def _fmt_pct(value: Optional[float]) -> str:
    return f"{value:+.2%}" if value is not None else "n/a"


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python fetch_market_context.py",
        description="KOSPI/KOSDAQ 일봉 한 건씩 받아 매크로 컨텍스트 JSON 으로 저장.",
    )
    parser.add_argument(
        "target_date", nargs="?", default=time.strftime("%Y-%m-%d"),
        help="대상 영업일 YYYY-MM-DD (기본: 오늘).",
    )
    parser.add_argument(
        "--reviews-dir", default=REVIEWS_DIR_DEFAULT,
        help=f"매크로 JSON 저장 디렉토리 (기본: {REVIEWS_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="캐시(이미 존재하는 JSON) 를 무시하고 재수집.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    print(f"== fetch_market_context {args.target_date} ==")
    out_path = _output_path(args.reviews_dir, args.target_date)
    if not needs_fetch(out_path, args.force):
        print(f"  - cached: {out_path} (재수집은 --force)")
        return 0

    ctx = fetch_market_context(args.target_date, reviews_dir=args.reviews_dir, force=args.force)
    if ctx is None:
        print("  - 매크로 fetch 실패 (KOSPI/KOSDAQ 둘 다 응답 없음).")
        return 1

    print(f"  - 저장: {out_path}")
    print(f"  - KOSPI  종가 {_fmt_pct(ctx.kospi_close_return)}, "
          f"일중최고 {_fmt_pct(ctx.kospi_intraday_high_return)}")
    print(f"  - KOSDAQ 종가 {_fmt_pct(ctx.kosdaq_close_return)}, "
          f"일중최고 {_fmt_pct(ctx.kosdaq_intraday_high_return)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
