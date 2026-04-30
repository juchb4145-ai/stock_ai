"""오늘 매매 결과 복기 → 내일 룰 추천 모듈.

엔트리포인트는 프로젝트 루트의 ``analyze_today.py``.

서브모듈:
  - loader     : trade_log + dante_entry_training 매칭, Trade 객체 생성
  - metrics    : Trade 단위 파생 메트릭(give_back, mfe_r, mae_r ...)
  - classifier : 진입 4종 / 청산 4종 자동 분류
  - rules      : 분류 통계 → 다음 거래일 룰 추천
  - report     : md/csv/json 리포트 출력
"""

from .loader import Trade, load_trades
from .metrics import attach_metrics
from .classifier import classify_trades
from .rules import RuleRecommendation, recommend_rules
from .report import write_reports

__all__ = [
    "Trade",
    "load_trades",
    "attach_metrics",
    "classify_trades",
    "RuleRecommendation",
    "recommend_rules",
    "write_reports",
]
