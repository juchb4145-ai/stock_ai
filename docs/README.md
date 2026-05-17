# 자동매매/리뷰 시스템 문서 인덱스

이 문서는 현재 레포의 운영 문서 인덱스입니다. 예전 단순 조건식 매매 설명이 아니라, 현재 코드 기준의 장중 매매 파이프라인과 장 마감 후 PostMarketReview 흐름을 기준으로 정리합니다.

## 현재 기준 요약

현재 시스템은 키움증권 OpenAPI 기반의 조건검색 포착 종목을 장중에 평가하고, 장 마감 후에는 포착 종목 전체를 read-only로 복기하는 구조입니다.

장중 핵심 흐름:

```text
조건검색 포착
-> CandidateRegistry 등록/갱신
-> 실시간/분봉/체결강도 기반 데이터 수집
-> MomentumBreakoutStrategy 판단
-> Legacy/Dante filter 확인
-> FinalEntryDecision 생성
-> TimePolicy 확인
-> OrderGuard 확인
-> paper/live 주문 경로 또는 비매매
-> structured log / trade_log 기록
```

장 마감 후 핵심 흐름:

```text
condition_captures.csv
+ main.log*
+ trade_log.csv
+ intraday/YYYYMMDD/*.csv
-> tools.post_market_review
-> reports/post_market/YYYYMMDD_<mode>_condition_review.csv
-> reports/post_market/YYYYMMDD_<mode>_condition_review.json
-> reports/post_market/YYYYMMDD_<mode>_summary.md
```

PostMarketReview는 실제 주문 API를 호출하지 않는 read-only 분석 도구입니다.

## 주요 문서

| 문서 | 용도 |
|---|---|
| [POST_MARKET_REVIEW_GUIDE.md](POST_MARKET_REVIEW_GUIDE.md) | PostMarketReview 설계, 구현, 운영, 테스트 기준 문서 |
| [../reports/post_market/README.md](../reports/post_market/README.md) | 장 마감 후 운영자가 바로 보는 PostMarketReview 빠른 runbook |
| [review_system_overview.md](review_system_overview.md) | 기존 일간 리뷰/룰 후보 시스템의 전체 구조 |
| [review_user_guide.md](review_user_guide.md) | 기존 일간 리뷰 운영 절차 |
| [review_safety_and_rollback.md](review_safety_and_rollback.md) | 룰 변경, rollback, 안전장치 문서 |

`review_system_overview.md`, `review_user_guide.md`, `review_safety_and_rollback.md`는 기존 daily review/rolling rule 계열 문서입니다. 조건검색 포착 종목 전체 복기는 `POST_MARKET_REVIEW_GUIDE.md`와 `reports/post_market/README.md`를 우선 기준으로 봅니다.

## 주요 코드 구성

| 파일 | 현재 역할 |
|---|---|
| [../main.py](../main.py) | 키움 OpenAPI 이벤트 루프, 조건검색 포착, 실시간 등록, 전략 판단, 주문 경로 진입점 |
| [../candidate_registry.py](../candidate_registry.py) | 조건 포착 후보 생명주기 관리. TTL 내 refresh와 TTL 이후 재포착을 `candidate_id`로 구분 |
| [../condition_capture_logger.py](../condition_capture_logger.py) | `data/condition_captures.csv` 기록. `candidate_id`, `strategy_name`, `signal_source` 포함 |
| [../momentum_breakout_strategy.py](../momentum_breakout_strategy.py) | 모멘텀 2차 판단. BUY/WAIT/BLOCK/REJECT와 reason_code 생성 |
| [../final_entry_decision.py](../final_entry_decision.py) | Momentum + Legacy/Dante 판단을 합쳐 최종 진입 판단과 `decision_trace` 생성 |
| [../time_policy.py](../time_policy.py) | 장중 시간 정책. 진입 가능 시간, 컷오프, 종가 관리 구간 판단 |
| [../order_guard.py](../order_guard.py) | 주문 전 안전 게이트. 일일 매수 제한, 손실 제한, 중복 포지션, 재진입 제한 등 확인 |
| [../training_recorder.py](../training_recorder.py) | `data/trade_log.csv`와 학습/리뷰용 CSV 기록 |
| [../fetch_minute_bars.py](../fetch_minute_bars.py) | 장 마감 후 1분봉 캐시 수집. `--source condition/all`로 조건 포착 전체 종목 수집 가능 |
| [../review/post_market.py](../review/post_market.py) | PostMarketReview 핵심 로직. 후보/판단/체결/분봉 join, 분류, CSV/JSON/Markdown 생성 |
| [../tools/post_market_review.py](../tools/post_market_review.py) | PostMarketReview CLI 진입점 |
| [../review/structured_log.py](../review/structured_log.py) | `data/main.log*` 구조화 로그 파서. `main.log.1` 같은 회전 로그도 후보로 읽음 |
| [../trade_config.py](../trade_config.py) | 전략명, 신호 출처, dry_run/live 설정, 리스크/전략 파라미터 |

## 장중 데이터와 로그

| 경로 | 내용 |
|---|---|
| `data/condition_captures.csv` | 조건검색 포착 이벤트와 최초 capture price. `candidate_id`, `strategy_name`, `condition_name`, `signal_source` 포함 |
| `data/main.log*` | `[momentum_entry_decision]`, `[final_entry_decision]`, `[entry_decision_trace]`, CandidateRegistry lifecycle 로그 |
| `data/trade_log.csv` | paper `would_order`, live `chejan`, 진입/청산 가격과 시간, `candidate_id` |
| `data/intraday/YYYYMMDD/*.csv` | 종목별 1분봉 캐시. MFE/MAE, time_to_high, return_after_Nm 계산에 사용 |
| `reports/post_market/` | PostMarketReview CSV/JSON/Markdown 출력 |

## 장 마감 후 운영 순서

1. 조건 포착 종목 전체의 1분봉을 수집합니다.

```powershell
python fetch_minute_bars.py 2026-05-13 --source condition
```

2. paper/live를 분리해서 PostMarketReview를 실행합니다.

```powershell
python -m tools.post_market_review --date 2026-05-13 --mode paper
python -m tools.post_market_review --date 2026-05-13 --mode live
python -m tools.post_market_review --date 2026-05-13 --mode all --output reports/post_market
```

3. `reports/post_market/YYYYMMDD_<mode>_summary.md`를 먼저 봅니다.
4. `MISSED_OPPORTUNITY`, `GOOD_REJECT`, `DATA_QUALITY_BLOCK`, `TIME_POLICY_BLOCK`, `ORDER_GUARD_BLOCK`, `TRADED_LOSS`를 순서대로 확인합니다.
5. config 변경 후보만 기록하고 즉시 자동 변경하지 않습니다.

## PostMarketReview 출력

mode suffix를 사용해 paper/live 결과를 섞지 않습니다.

| mode | CSV | JSON | Markdown |
|---|---|---|---|
| `paper` | `YYYYMMDD_paper_condition_review.csv` | `YYYYMMDD_paper_condition_review.json` | `YYYYMMDD_paper_summary.md` |
| `live` | `YYYYMMDD_live_condition_review.csv` | `YYYYMMDD_live_condition_review.json` | `YYYYMMDD_live_summary.md` |
| `all` | paper/live 파일을 각각 생성 | paper/live JSON을 각각 생성 | paper/live Markdown을 각각 생성 |

핵심 컬럼:

| 컬럼 | 의미 |
|---|---|
| `candidate_id` | 조건 포착 후보와 판단/체결 로그를 연결하는 ID |
| `strategy_name` | 전략명. 과거 로그에 없으면 `signal_source` fallback 가능 |
| `entry_time`, `exit_time` | paper/live 진입/청산 체결 시간 |
| `decision_trace` | Momentum, Legacy/Dante, TimePolicy, OrderGuard 판단 trace |
| `join_quality` | `exact_candidate_id`, `fallback_symbol_time`, `fallback_symbol_only`, `partial_match`, `missing_join` |
| `data_quality` | `ok`, `partial_data`, `missing_minute_bars`, `missing_decision_trace` 등 |
| `review_category` | `TRADED_WIN`, `TRADED_LOSS`, `MISSED_OPPORTUNITY`, `GOOD_REJECT`, `DATA_QUALITY_BLOCK` 등 |
| `mfe_pct`, `mae_pct` | 포착 이후 최대 유리/불리 변동률 |

중요 원칙:

> missing 값은 0이 아닙니다. missing MFE/MAE는 평균 계산에서 제외하고, `n_mfe`, `n_mae`, `missing_mfe`, `missing_mae`로 표본 수를 함께 표시합니다.

## Markdown 요약 섹션

PostMarketReview summary는 다음 섹션을 기준으로 봅니다.

| 섹션 | 확인할 내용 |
|---|---|
| `Daily Summary` | 총 포착/매매/비매매 수와 주요 카테고리 개수 |
| `Trade Results` | 실제 매매한 종목의 진입/청산/수익률 |
| `Non-Traded Review` | 포착됐지만 매매하지 않은 전체 종목 |
| `Missed Opportunities` | 안 샀지만 이후 크게 오른 종목 |
| `Good Rejects` | 안 사서 잘한 종목 |
| `Block Chase Review` | 추격매수 차단이 유효했는지 |
| `Data Quality Blocks` | 데이터 missing/invalid 차단과 이후 흐름 |
| `Time Policy Blocks` | 시간 필터 차단과 이후 흐름 |
| `OrderGuard Blocks` | OrderGuard 차단과 이후 흐름 |
| `Reason Code Ranking` | reason별 count, 평균 MFE/MAE, n/missing 수 |
| `Time Bucket Analysis` | 포착 시간대별 성과 |
| `Parameter Tuning Hints` | 사람이 검토할 튜닝 힌트 |
| `Next Action Checklist` | 장 마감 후 확인할 체크리스트 |

## 안전 원칙

PostMarketReview와 관련 CLI는 read-only 분석 경로입니다.

- `send_order` 호출 금지
- `dynamicCall("SendOrder")` 호출 금지
- `submit_order_guarded` 호출 금지
- `place_buy_order` 호출 금지
- `main.Kiwoom` 인스턴스 생성 금지
- 분석 결과가 자동으로 config를 바꾸면 안 됨
- paper/live 결과는 분리해서 계산
- 데이터가 없으면 추측하지 말고 missing으로 기록

실제 주문 경로는 장중 `main.py` 내부에서 TimePolicy와 OrderGuard를 거친 뒤에만 사용됩니다. 문서/리뷰 도구는 그 경로를 호출하지 않습니다.

## 테스트

주요 테스트 명령:

```powershell
python -m unittest test_post_market_review.py
python -m unittest test_condition_capture_logger.py test_candidate_registry.py test_fetch_minute_bars.py test_post_market_review.py
python -m py_compile review\post_market.py review\structured_log.py tools\post_market_review.py
```

회전 로그 테스트:

- sanitized fixture: `tests/fixtures/post_market/main.log.1`
- 로컬 integration: `data/main.log.1`이 있으면 실행, 없으면 skip
- 실제 운영 로그 원문은 fixture로 커밋하지 않습니다.

## 이전 문서와의 관계

이 문서는 현재 기준의 인덱스입니다. 기존 daily review/rolling rule 문서는 아직 참고할 수 있지만, 조건검색 포착 종목 전체 복기와 PostMarketReview 운영은 다음 두 문서를 우선 기준으로 삼습니다.

- [POST_MARKET_REVIEW_GUIDE.md](POST_MARKET_REVIEW_GUIDE.md)
- [../reports/post_market/README.md](../reports/post_market/README.md)
## Sector/Theme Map Preflight

Before enabling or reviewing the sector/theme dry-run gates, validate that
`data/sector_map.csv` and `data/theme_map.csv` are not missing or header-only:

```powershell
.\venv64\Scripts\python.exe tools\bootstrap_sector_theme_maps.py --validate-only --fail-on-empty
```

Bootstrap local Kiwoom/exported data into the production maps:

```powershell
.\venv64\Scripts\python.exe tools\bootstrap_sector_theme_maps.py `
  --sector-source path\to\sector_source.csv `
  --theme-source path\to\theme_source.json `
  --fail-on-empty
```

See [SECTOR_THEME_MAPS.md](SECTOR_THEME_MAPS.md) for the CSV/JSON formats and
startup fail-fast policy.
