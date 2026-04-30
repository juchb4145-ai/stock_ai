"""Trade 객체에 파생 메트릭을 채운다.

용어:
  R         : 1R = exit_strategy.R_UNIT_PCT (기본 1.5%)
  realized  : 실제 청산 수익률 (sell_order.profit_rate 우선, 없으면 체결가 기반)
  MFE       : max favorable excursion = max_return_25m
  MAE       : max adverse  excursion = min_return_25m
  give_back : MFE - realized   (최고가 대비 반납폭)
  over_run  : return_20m - realized (익절일 때만; 익절 후 추가상승)
  bounce_after_stop : 손절일 때 MFE  (한 번이라도 +로 갔는지)
"""

from __future__ import annotations

from typing import Iterable

from exit_strategy import R_UNIT_PCT

from .loader import Trade


def _safe(value):
    return value if value is not None else float("nan")


def attach_metrics(trades: Iterable[Trade]) -> None:
    for trade in trades:
        m = trade.metrics
        realized = trade.final_return

        m["realized_return"] = _safe(realized)
        m["r_multiple"] = realized / R_UNIT_PCT if realized is not None else float("nan")

        mfe = trade.max_return_25m
        mae = trade.min_return_25m
        m["mfe"] = _safe(mfe)
        m["mae"] = _safe(mae)
        m["mfe_r"] = mfe / R_UNIT_PCT if mfe is not None else float("nan")
        m["mae_r"] = mae / R_UNIT_PCT if mae is not None else float("nan")

        m["return_5m"] = _safe(trade.return_5m)
        m["return_10m"] = _safe(trade.return_10m)
        m["return_20m"] = _safe(trade.return_20m)

        if realized is not None and mfe is not None:
            give_back = mfe - realized
        else:
            give_back = float("nan")
        m["give_back"] = give_back
        m["give_back_r"] = give_back / R_UNIT_PCT if give_back == give_back else float("nan")

        if realized is not None and realized > 0 and trade.return_20m is not None:
            over_run = trade.return_20m - realized
        else:
            over_run = float("nan")
        m["over_run"] = over_run
        m["over_run_r"] = over_run / R_UNIT_PCT if over_run == over_run else float("nan")

        if realized is not None and realized < 0 and mfe is not None:
            m["bounce_after_stop"] = mfe
            m["bounce_after_stop_r"] = mfe / R_UNIT_PCT
        else:
            m["bounce_after_stop"] = float("nan")
            m["bounce_after_stop_r"] = float("nan")

        m["dip_to_stop"] = _safe(mae)
        m["dip_to_stop_r"] = mae / R_UNIT_PCT if mae is not None else float("nan")

        # 보유시간(초)
        hold = trade.hold_seconds
        m["hold_seconds"] = hold if hold is not None else float("nan")

        # +1R 도달 후 손절(=본절컷 후보) 표시용
        if (
            realized is not None and realized < 0
            and trade.reached_1r is not None and trade.reached_1r >= 1
        ):
            m["be_violation"] = 1.0  # 한 번 +1R 갔다 손절로 끝남
        else:
            m["be_violation"] = 0.0
