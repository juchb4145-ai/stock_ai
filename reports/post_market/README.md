# PostMarketReview 운영 README

이 디렉터리는 장 마감 후 조건검색 포착 종목 전체를 복기하는 PostMarketReview 리포트 출력 위치입니다.

상세 설계와 필드 정의는 [../../docs/POST_MARKET_REVIEW_GUIDE.md](../../docs/POST_MARKET_REVIEW_GUIDE.md)를 참고하세요.

## 목적

PostMarketReview는 장 마감 후 read-only로 실행하는 분석 도구입니다.

- 조건식에 포착된 전체 종목을 복기합니다.
- 실제 매매한 종목과 매매하지 않은 종목을 분리해 봅니다.
- 왜 샀는지, 왜 안 샀는지, 안 산 뒤에는 어떻게 움직였는지 확인합니다.
- `missing` 값은 0이 아닙니다. missing MFE/MAE는 평균 계산에서 제외하고 `n_mfe`, `n_mae`, `missing_mfe`, `missing_mae`로 표본 수를 함께 봅니다.

## 실행 명령어

```powershell
python -m tools.post_market_review --date 2026-05-13 --mode paper
python -m tools.post_market_review --date 2026-05-13 --mode live
python -m tools.post_market_review --date 2026-05-13 --mode all --output reports/post_market
```

JSON은 기본 생성됩니다. JSON을 생략하려면 `--no-json`을 사용합니다.

```powershell
python -m tools.post_market_review --date 2026-05-13 --mode paper --no-json
```

## 장 마감 후 Runbook

1. 조건 포착 종목 전체 1분봉을 수집합니다.

```powershell
python fetch_minute_bars.py 2026-05-13 --source condition
```

2. paper/live를 분리해 PostMarketReview를 실행합니다.
3. `YYYYMMDD_<mode>_summary.md`를 먼저 확인합니다.
4. `MISSED_OPPORTUNITY` 상위 종목을 확인합니다.
5. `GOOD_REJECT`가 실제로 잘 막은 종목인지 확인합니다.
6. `DATA_QUALITY_BLOCK` 중 MFE가 높은 종목을 확인합니다.
7. `TIME_POLICY_BLOCK` 이후 급등한 종목이 반복되는지 확인합니다.
8. `ORDER_GUARD_BLOCK`이 과도한 제한이었는지 확인합니다.
9. `TRADED_LOSS`의 `reason_code`를 확인합니다.
10. config 변경 후보만 기록하고 즉시 자동 변경하지 않습니다.

## 출력 파일

mode suffix를 붙여 paper/live 결과를 섞지 않습니다.

| mode | CSV | JSON | Markdown |
|---|---|---|---|
| `paper` | `YYYYMMDD_paper_condition_review.csv` | `YYYYMMDD_paper_condition_review.json` | `YYYYMMDD_paper_summary.md` |
| `live` | `YYYYMMDD_live_condition_review.csv` | `YYYYMMDD_live_condition_review.json` | `YYYYMMDD_live_summary.md` |
| `all` | paper/live 파일을 각각 생성 | paper/live JSON을 각각 생성 | paper/live Markdown을 각각 생성 |

## 핵심 필드

| 필드 | 의미 |
|---|---|
| `candidate_id` | 조건 포착 후보와 판단/체결 로그를 연결하는 ID |
| `strategy_name` | 전략명. 과거 로그에 없으면 `signal_source` fallback 가능 |
| `condition_name` | 조건검색식 이름 |
| `detected_at` | 조건식 포착 시각 |
| `capture_price` | 포착 당시 기준 가격 |
| `entry_time` | paper/live buy fill 시간 |
| `exit_time` | paper/live sell fill 시간. 미청산이면 missing |
| `final_decision` | 최종 진입 판단 |
| `reason_code` | 차단/진입 사유 코드 |
| `decision_trace` | Momentum, Legacy, TimePolicy, OrderGuard 판단 trace |
| `join_quality` | `exact_candidate_id`, `fallback_symbol_time`, `fallback_symbol_only`, `partial_match`, `missing_join` |
| `data_quality` | `ok`, `partial_data`, `missing_minute_bars`, `missing_decision_trace` 등 |
| `review_category` | `TRADED_WIN`, `MISSED_OPPORTUNITY`, `GOOD_REJECT` 등 |
| `mfe_pct` | 포착 이후 최대 유리 변동률 |
| `mae_pct` | 포착 이후 최대 불리 변동률 |
| `n_mfe`, `n_mae` | reason 통계에서 평균 계산에 실제 사용된 표본 수 |
| `missing_mfe`, `missing_mae` | reason 통계에서 missing이라 제외된 표본 수 |

## Markdown 섹션

| 섹션 | 확인할 내용 |
|---|---|
| `Daily Summary` | 포착/매매/비매매 수와 주요 카테고리 개수 |
| `Trade Results` | 실제 매매 종목의 진입/청산/수익률 |
| `Non-Traded Review` | 포착됐지만 매매하지 않은 종목 전체 |
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

- PostMarketReview는 read-only 분석 도구입니다.
- 실제 주문 API를 호출하지 않습니다.
- `send_order` 호출 금지.
- `dynamicCall("SendOrder")` 호출 금지.
- `submit_order_guarded`, `place_buy_order` 호출 금지.
- 분석 결과가 자동으로 config를 바꾸면 안 됩니다.
- missing 값은 0이 아닙니다.
- missing MFE/MAE는 평균 계산에서 제외하고 n/missing count를 함께 표시합니다.

## 문제 해결

| 상황 | 확인할 것 |
|---|---|
| `data/main.log.1`이 없음 | 회전 로그가 없으면 현재 `data/main.log`만 사용합니다. 테스트는 skip될 수 있습니다. |
| 분봉 데이터가 없음 | 먼저 `fetch_minute_bars.py YYYY-MM-DD --source condition`을 실행합니다. 없으면 `missing_minute_bars`로 남깁니다. |
| `candidate_id`가 없는 과거 로그 | `symbol + detected_at` 근접 fallback join을 사용하고 `join_quality`에 표시합니다. |
| `strategy_name`이 없는 과거 로그 | `signal_source`를 fallback으로 사용할 수 있고 `data_quality`에 `strategy_name_fallback_used`가 남습니다. |
| 인코딩 문제 | 로그 파서는 UTF-8에서 깨지는 문자를 `errors=replace`로 안전 처리합니다. 원문 복구가 필요한 경우 운영 로그 인코딩을 별도로 확인합니다. |
