# 자동매매 리뷰/룰 개선 기능 — 전체 개요

본 문서는 매일 매매 결과를 자동으로 분석해 다음 거래일의 매수/매도 룰을 보완하기 위한 기능 전체를 설명합니다. 운영자 관점에서 *"어떤 단계가 있고, 각 단계에서 어떤 파일이 만들어지고, 무엇을 보고 무엇을 결정해야 하는가"* 를 이해하기 위한 출발점입니다.

세부 사용 절차는 [review_user_guide.md](review_user_guide.md) , 안전장치와 롤백 정책은 [review_safety_and_rollback.md](review_safety_and_rollback.md) 를 참고하세요.

---

## 1. 왜 필요한가

자동매매를 운영하다 보면 매일 같은 패턴의 손실이 반복되는 경우가 자주 나옵니다. 예를 들어:

- 진입 직후 +1R 까지 잘 갔다가 손절선에 닿아 -1R 로 끝나는 거래(=본절컷 부재)가 반복됨
- 고점 근처에서 추격하는 진입(=late_chase)만 골라 손실로 끝남
- 익절은 제대로 했지만 더 갔어야 하는 자리에서 던져버림(=fast_take)

기존에는 사람이 매일 trade_log.csv 를 직접 살펴보고, 다음 날 룰을 손으로 바꿔야 했습니다. 이 작업은 다음 두 가지 위험을 가집니다.

1. **놓치기 쉬움** — 거래 수가 늘면 패턴을 한눈에 보기 어렵습니다.
2. **재현 불가** — 사람이 임의로 룰을 바꾸면 왜 바꿨는지가 코드에 남지 않습니다.

본 기능은 이 두 가지를 모두 해결합니다.

- 매일 자동으로 거래 결과를 *분류*하고(돌파매수, 첫 눌림매수, 추격매수, 가짜돌파, 빠른익절, 늦은익절, 좋은손절, 나쁜손절)
- 누적 통계로 다음 날 룰 후보를 *제안*하고 **사람이 검토한 뒤** 명시적으로 승인했을 때만 실제 룰을 변경합니다.

---

## 2. 전체 흐름 한눈에 보기

```
[장중 자동 (main.py)]                            [장 종료 후 nightly]
       |                                                    |
       v                                                    v
+-----------------------------+    +------------------------+
| 매매 로그 / 학습 표본 수집  |    | KOSPI/KOSDAQ 매크로    |
| - trade_log.csv             |    | (fetch_market_context) |
| - dante_entry_training.csv  |    +------------------------+
| - dante_shadow_training.csv |               |
| - portfolio_state.json      |               v
+-----------------------------+    +------------------------+
                                   |  1분봉 보강            |
                                   |  (fetch_minute_bars)   |
                                   +------------------------+
                                               |
                                               v
                                   +------------------------+
                                   |  거래별 리뷰           |
                                   |  (analyze_today)       |
                                   |  + 매크로 컬럼 join    |
                                   +------------------------+
                                               |
                                               v
                                   +------------------------+
                                   |  rolling 누적 통계     |
                                   |  v1/v2 분리 집계       |
                                   |  rule_candidates 산출  |
                                   |  (review.rolling)      |
                                   +------------------------+
                                               |
                                               v
                                   +------------------------+
                                   |  dry_run 으로 검토     |
                                   |  (apply_overrides.py)  |
                                   +------------------------+
                                               |
                                               v
                                   +------------------------+
                                   |  사람이 JSON 편집      |
                                   |  (allow_auto_apply)    |
                                   +------------------------+
                                               |
                                               v
                                   +------------------------+
                                   |  --commit 으로 적용    |
                                   |  (apply_overrides.py)  |
                                   +------------------------+
```

각 단계는 모두 **독립적으로 실행 가능한 별도 스크립트**입니다. 단계 사이는 파일(CSV, JSON)로만 연결되어 있어서 어떤 단계든 다시 돌리거나 수동으로 파일을 편집해 결과를 바꿀 수 있습니다.

### 2.1 장중 main.py 가 자동으로 만드는 산출물

운영자가 별도로 실행할 필요 없이, main.py 가 장중에 4가지 파일을 자동으로 갱신합니다.


| 파일 | 역할 |
| ---- | --- |
| `data/trade_log.csv` | 모든 매수/매도 이벤트 로그 (이전부터 있던 핵심 진실 소스) |
| `data/dante_entry_training.csv` | 게이트가 `ready` 라고 판단한 진입 후보 + 25분 후 사후 라벨 |
| `data/dante_shadow_training.csv` | 게이트가 `wait`/`blocked` 으로 거른 표본 + 동일 25분 후 라벨 (false-negative 측정용) |
| `data/portfolio_state.json` | 장중 크래시 복원용 Position 영속화. `entry_stage` / `stop_price` / `partial_taken` / `breakout_grade` / `pending_sell_intent` 등 잃으면 전략이 망가지는 8개 전략 필드를 매 체결/매도 큐 변경/매도 평가 사이클마다 atomic write |

---

## 3. 단계별 상세 흐름

### 단계 1 — 오늘 매매 로그 수집 (장중 자동)

이 단계는 자동매매 시스템(main.py)이 장중에 자동으로 수행합니다. 별도 실행 불필요.
산출물 4종은 §2.1 표 참조. 운영자가 신경 쓸 일은 없지만, `data/portfolio_state.json` 은 장중 크래시 후 main.py 를 다시 띄우면 자동으로 읽혀 전략 상태가 복원됩니다 — 잔고 TR 응답으로는 회복 불가능한 `entry_stage` / `stop_price` 같은 필드를 보호합니다.


| 항목    | 값                                      |
| ----- | -------------------------------------- |
| 입력    | 키움증권 실시간 체결 이벤트                        |
| 출력    | `data/trade_log.csv`, `data/dante_entry_training.csv`, `data/dante_shadow_training.csv`, `data/portfolio_state.json` |
| 실행 주체 | main.py (장중 자동)                        |


### 단계 2 — 시장 매크로 수집 (KOSPI/KOSDAQ 일봉)

장 종료 후 별도 실행. 그 날의 KOSPI/KOSDAQ 종가 등락률 + 일중 최대상승률을 키움 opt20006 TR 로 받아 매크로 JSON 으로 저장합니다. 분석 단계에서 매 거래에 join 되며, rolling 통계는 향후 강세장/약세장 분리 평가에 이 컬럼을 사용합니다.


| 항목    | 값                                                                              |
| ----- | ------------------------------------------------------------------------------ |
| 실행 명령 | `python fetch_market_context.py [YYYY-MM-DD]`                                  |
| 입력    | 없음 (KOSPI=001, KOSDAQ=101 코드는 모듈 상수)                                            |
| 출력    | `data/reviews/market_context_YYYY-MM-DD.json`                                  |
| 실패 시  | 한쪽 실패는 부분 결과로 저장(다른 쪽은 살림). 두 쪽 다 실패면 JSON 미작성 — analyze_today 가 자동 graceful fallback |


### 단계 3 — intraday 1분봉 보강

장 종료 후 별도 실행. 오늘 매매한 종목들의 1분봉 데이터를 키움 opt10080 TR 로 받아 캐시합니다. 이 데이터가 있어야 다음 단계의 리뷰에서 정밀한 진입 시점 분석(VWAP 대비 가격, 진입 전 3분 상승률, 진입봉 윗꼬리 등)을 할 수 있습니다.


| 항목    | 값                                                 |
| ----- | ------------------------------------------------- |
| 실행 명령 | `python fetch_minute_bars.py [YYYY-MM-DD]`        |
| 입력    | `data/trade_log.csv` (오늘 매매한 종목 코드 추출)            |
| 출력    | `data/intraday/YYYYMMDD/<종목코드>.csv` (종목별 1개 파일)   |
| 실패 시  | 해당 종목만 건너뛰고 다음 종목 진행 — 다음 단계는 5분봉 라벨로 자동 fallback |


### 단계 4 — 거래별 리뷰 생성

오늘 거래를 종목별로 묶고, 각 거래에 진입 분류(`entry_class`)와 청산 분류(`exit_class`), 사후 메트릭(MFE/MAE, give-back, over-run 등), 그리고 단계 2 의 매크로 컬럼(`market_strength` / `market_kospi_close_return` / ...)을 부여합니다.


| 항목    | 값                                                                                                                                                          |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 실행 명령 | `python analyze_today.py [YYYY-MM-DD]`                                                                                                                     |
| 입력    | `data/trade_log.csv`, `data/dante_entry_training.csv`, `data/intraday/YYYYMMDD/*.csv`, `data/reviews/market_context_YYYY-MM-DD.json` (없으면 매크로 컬럼만 비고 정상 진행) |
| 출력    | `data/reviews/trade_review_YYYY-MM-DD.csv`, `data/reviews/daily_review_YYYY-MM-DD.md`, `data/reviews/rule_overrides_YYYY-MM-DD.json`                       |


### 단계 5 — rolling 누적 통계 생성

5/10/20 영업일 누적 통계를 만들어 *반복되는 패턴*을 찾습니다. 단일 일자로는 표본이 부족해서 단순한 우연을 룰 변경의 근거로 잡을 수 있는데, 누적 통계는 이걸 막아줍니다.

**v1/v2 분류기 분리 집계** — `trade_review_*.csv` 의 `classifier_version` 컬럼 기준. 룰 후보 평가는 *v2 표본만* 으로 결정되어 v1 fallback 거래(1분봉 D 피처 부재로 임계가 다른 거래) 가 통계를 흐리지 않도록 합니다. 빈 값(legacy fixture) 은 v2 default 로 취급. v1 row 는 audit 가독성을 위해 `by_classifier_version` 통계에만 노출됩니다.

**confidence 게이트는 v2 row 수(=`n_candidate`) 기준** — 전체 row 수가 아니라 후보 평가에 실제 들어가는 v2 표본 수로 low/medium/high 가 결정됩니다. v1 fallback 비율이 높아 보여도 잘못 high 로 잡히지 않습니다.


| 항목    | 값                                                                                          |
| ----- | ------------------------------------------------------------------------------------------ |
| 실행 명령 | `python -m review.rolling [YYYY-MM-DD]`                                                    |
| 입력    | `data/reviews/trade_review_*.csv` 여러 일자                                                    |
| 출력    | `data/reviews/rolling_summary_YYYYMMDD.json` (`n_candidate` / `by_classifier_version` 노출), `data/reviews/rule_candidates_YYYYMMDD.json` |


### 단계 6 — rule_candidates 생성

단계 5 와 같은 명령(`review.rolling`) 으로 한 번에 만들어집니다. 누적 통계에서 트리거 조건이 충족된 룰만 골라 *후보*로 만듭니다. 이 시점에서는 어떤 룰도 자동 적용되지 않으며, 모든 후보의 `allow_auto_apply` 필드는 기본값 `false` 입니다.

### 단계 7 — dry_run 으로 적용 예정 룰 검토

`apply_overrides.py` 를 인자 없이 호출하면 dry_run 모드로 동작합니다.
**실제 모듈 상수는 절대 변경되지 않으며**, 적용 *예정* 내역만 감사 로그로 떨어뜨립니다.


| 항목    | 값                                                             |
| ----- | ------------------------------------------------------------- |
| 실행 명령 | `python apply_overrides.py [YYYY-MM-DD]` (--commit 없음)        |
| 입력    | `data/reviews/rule_candidates_YYYYMMDD.json`                  |
| 출력    | `data/reviews/applied_overrides_YYYYMMDD.json` (mode=dry_run) |


### 단계 8 — 사람이 확인 후 commit 적용

운영자가 단계 7 의 audit JSON 을 읽어보고, 적용해도 좋다고 판단한 후보의 `allow_auto_apply` 를 `true` 로 직접 편집합니다. 그 후 `--commit` 플래그로 다시 실행하면 실제 모듈 상수가 변경됩니다.


| 항목    | 값                                                                                    |
| ----- | ------------------------------------------------------------------------------------ |
| 실행 명령 | `python apply_overrides.py [YYYY-MM-DD] --commit`                                    |
| 안전장치  | `confidence=high` AND `allow_auto_apply=true` 인 후보만 적용                               |
| 출력    | `data/reviews/applied_overrides_YYYYMMDD.json` (mode=commit), `data/main.log` 한 줄 요약 |


---

## 4. 모듈 역할 정리


| 모듈/스크립트                  | 역할                                                       | 키움 API 호출    | 모듈 상수 변경         |
| ------------------------ | -------------------------------------------------------- | ------------ | ---------------- |
| `main.py`                | 장중 거래 + 학습 표본 수집 + portfolio_state 영속화                   | 함 (실시간/주문)   | 안 함              |
| `analyze_today.py`       | 단일 일자 거래 묶음 + 분류 + 메트릭 + 매크로 join + 일별 리뷰 산출             | 안 함          | 안 함              |
| `fetch_minute_bars.py`   | 1분봉 캐시 수집 (별도 nightly job)                               | 함 (opt10080) | 안 함              |
| `fetch_market_context.py`| KOSPI/KOSDAQ 일봉 매크로 수집 (별도 nightly job)                  | 함 (opt20006) | 안 함              |
| `review/intraday.py`     | 캐시된 1분봉 CSV 로 정밀 메트릭/D 피처 계산                             | 안 함          | 안 함              |
| `review/market_context.py`| 매크로 JSON 로드/저장 + 거래에 매크로 컬럼 join + strong/weak 분류         | 안 함          | 안 함              |
| `review/rolling.py`      | 5/10/20 영업일 누적 통계(v1/v2 분리) + 룰 후보 산출                    | 안 함          | 안 함              |
| `review/classifier.py`   | 진입 4종 + 청산 4종 자동 분류 (v2 강화 로직)                           | 안 함          | 안 함              |
| `review/overrides.py`    | 룰 후보 검증 + dry_run/commit 적용기 (단일 진입점)                    | 안 함          | **commit 시에만** 함 |
| `apply_overrides.py`     | `review/overrides.py` 의 사람용 CLI 래퍼                       | 안 함          | 위와 동일            |
| `portfolio.py`           | Position dataclass + 디스크 영속화(save/load)                  | 안 함          | 안 함              |


이 표에서 보듯, 모듈 상수를 실제로 변경하는 경로는 단 하나 (`review/overrides.py` 의 `commit_overrides`) 뿐입니다. 다른 모든 모듈은
파일을 읽고/쓰기만 합니다.

---

## 5. 생성되는 주요 파일

### 5.0 장중 자동 산출물

#### 5.0.1 `data/dante_entry_training.csv` — ready 진입 후보 학습 표본

게이트가 `ready` 라고 판단한 진입 후보 + 25분 후 사후 라벨(`reached_1r` / `reached_2r` / `hit_stop` / `time_exit`). 매수 발주/체결 결과와 무관하게 게이트 통과 시점에 즉시 캡처되며, 같은 종목은 60초 cooldown.

#### 5.0.2 `data/dante_shadow_training.csv` — wait/blocked 표본 (false-negative 측정)

게이트가 거른 후보를 같은 horizon 으로 사후 라벨링. 첫 컬럼 `decision_status` 가 `"wait"` / `"blocked"`. 데이터 부족(틱/관찰시간/5분봉 캐시) 으로 거른 표본은 의미가 없어 **자동 제외** 됩니다 — `wait/blocked` 사유가 *전략 임계 미달* 인 표본만 캡처. cooldown 90초.

분석 시 같은 분석 파이프라인(예: 정책 재현) 에 두 CSV 를 함께 입력하면 "거른 종목 vs 통과 종목" 의 도달률 비교가 가능합니다. 헤더는 `[decision_status] + DANTE_TRAINING_FIELDS` 로 호환.

#### 5.0.3 `data/portfolio_state.json` — 장중 크래시 복원 영속화

매 체결/매도 큐 변경/매도 평가 사이클마다 atomic write. 잃으면 전략이 망가지는 8개 필드(`entry_stage` / `planned_quantity` / `stop_price` / `partial_taken` / `breakout_high` / `breakout_grade` / `pullback_window_deadline` / `pending_sell_intent`) 를 보호.


| 필드 카테고리 | 동작                                                            |
| ------- | ------------------------------------------------------------- |
| 전략 필드   | 디스크 → 메모리 복원, 잔고 TR 응답이 *덮어쓰지 않음*                             |
| 휘발성 필드  | `quantity` / `available_quantity` / `entry_price` / `pending_buy` / `pending_sell` 은 디스크 본을 무시하고 잔고/미체결 TR 로 덮어씀 |
| trading_day | 메타데이터로 함께 저장. 부팅 시 today 와 다르면 어제 상태로 보고 자동 폐기(매도 의도 stale 가격 방지) |


손상된 JSON 은 `.corrupt` 접미사로 보존되고 부팅은 차단되지 않습니다(빈 상태로 시작 → 잔고 TR 로 재구성).

빈 portfolio(보유 0) 일 때는 1.5초 주기 매도 평가 사이클에서도 디스크 IO 를 스킵해 무의미한 fsync 누적을 방지합니다.

### 5.1 `data/intraday/YYYYMMDD/<code>.csv` — 1분봉 캐시


| 컬럼                                | 설명                    |
| --------------------------------- | --------------------- |
| `datetime`                        | `YYYY-MM-DD HH:MM:SS` |
| `open` / `high` / `low` / `close` | 분봉 OHLC (정수, 원)       |
| `volume`                          | 분봉 거래량                |


예시:

```
datetime,open,high,low,close,volume
2026-04-30 09:00:00,16400,16550,16380,16500,5000
2026-04-30 09:01:00,16500,16600,16470,16550,4500
```

### 5.1.1 `data/reviews/market_context_YYYY-MM-DD.json` — KOSPI/KOSDAQ 매크로

`fetch_market_context.py` 가 키움 opt20006 으로 만들거나, 운영자가 수동으로 JSON 한 줄 작성 가능. 분석 단계에서 매 거래에 join 됩니다.


| 필드                           | 의미                                       |
| ---------------------------- | ---------------------------------------- |
| `date`                       | `YYYY-MM-DD`                             |
| `kospi_close_return`         | KOSPI 종가 등락률 (전일 대비)                     |
| `kosdaq_close_return`        | KOSDAQ 종가 등락률                            |
| `kospi_intraday_high_return` | KOSPI 일중 시가 → 고가 최대 상승률                  |
| `kosdaq_intraday_high_return`| KOSDAQ 동일                                |
| `kospi_close` / `kosdaq_close` | 종가 (수치)                                |
| `source`                     | `kiwoom_opt20006` / `manual` 등           |
| `generated_at`               | ISO 시각                                   |


예시:

```json
{
  "schema": "market_context_v1",
  "date": "2026-04-30",
  "kospi_close_return": 0.0078,
  "kosdaq_close_return": 0.0114,
  "kospi_intraday_high_return": 0.0125,
  "kosdaq_intraday_high_return": 0.0181,
  "kospi_close": 2650.5,
  "kosdaq_close": 870.3,
  "source": "kiwoom_opt20006",
  "generated_at": "2026-04-30T16:05:00"
}
```

`review.market_context.classify_market_strength` 가 KOSPI 종가 등락률 ±0.5% 기준으로 `strong` / `weak` / `neutral` 3분류, 데이터 없으면 `unknown`.

### 5.2 `data/reviews/trade_review_YYYY-MM-DD.csv` — 거래별 상세

거래 한 건당 한 행. 진입/청산 분류, R 배수, MFE/MAE, give-back, 1분봉 정밀메트릭, D 피처(고점 대비 진입 위치, VWAP 대비, 진입봉 몸통/윗꼬리 등), late_chase 디버그 필드 + **매크로 컬럼 5종**(`market_strength` / `market_kospi_close_return` / `market_kosdaq_close_return` / `market_kospi_intraday_high_return` / `market_kosdaq_intraday_high_return`) 까지 들어갑니다. 전체 50여 개 컬럼.

매크로 JSON 이 없는 날은 `market_strength="unknown"` + 매크로 등락률 컬럼은 빈 값으로 graceful fallback.

### 5.3 `data/reviews/daily_review_YYYY-MM-DD.md` — 사람용 일별 요약

마크다운으로 작성된 그날의 매매 요약. 표 4개:

- **요약** — 거래 수, 평균 R, 승률, 진입/청산 분류 카운트
- **1분봉 데이터 소스** — 1분봉 정밀/fallback/missing 종목 수
- **손실 큰 거래 Top 3**
- **전체 거래 시간순**
- **다음 거래일 룰 추천** — 트리거된 룰만 표시

### 5.4 `data/reviews/rolling_summary_YYYYMMDD.json` — 누적 통계 원본

5/10/20 영업일 윈도우별 통계.

```json
{
  "as_of_date": "2026-04-30",
  "windows": [5, 10, 20],
  "stats": [
    {
      "window": 5,
      "dates": ["2026-04-26", "..."],
      "n_total": 25,
      "n_candidate": 23,
      "confidence": "medium",
      "overall": {"win_rate": 0.4, "avg_r": -0.04, "profit_factor": 0.91},
      "by_entry_class": {"breakout_chase": {...}, "first_pullback": {...}},
      "by_exit_class":  {"bad_stop": {...}, "late_take": {...}},
      "by_entry_exit":  {"breakout_chase|bad_stop": {...}},
      "by_classifier_version": {"v2": {"n": 23, ...}, "v1": {"n": 2, ...}}
    }
  ]
}
```


| 필드                      | 의미                                            |
| ----------------------- | --------------------------------------------- |
| `n_total`               | 윈도우 내 *전체* 거래 수 (분류기 버전 무관)                   |
| `n_candidate`           | *룰 후보 평가에 들어가는* v2 거래 수 — `confidence` 가 이 수치로 결정 |
| `by_classifier_version` | v1 / v2 별 분리 집계. v1 비율이 높은 날은 audit 추적용으로 활용 |


### 5.5 `data/reviews/rule_candidates_YYYYMMDD.json` — 룰 후보

누적 통계에서 트리거된 룰들. **모든 후보의** `allow_auto_apply` **는 기본** `false` — 사람이 직접 편집해야 commit 시 적용됩니다.

```json
{
  "as_of_date": "2026-04-30",
  "auto_apply_globally_disabled": true,
  "candidates": [
    {
      "rule_id": "break_even_cut",
      "title": "본절컷(BE 스탑 조기 이동)",
      "confidence": "medium",
      "n_largest_window": 10,
      "consistent_across_windows": true,
      "allow_auto_apply": false,
      "auto_apply": false,
      "evidence": {"5d": {...}, "10d": {...}, "20d": {...}},
      "proposed_overrides": [
        {
          "target": "exit_strategy.EXIT_BE_R",
          "op": "decrement",
          "by": 0.3,
          "min": 0.5,
          "reason": "+1R 도달 후 손절 비율 30% 이상 반복"
        }
      ]
    }
  ]
}
```

### 5.6 `data/reviews/applied_overrides_YYYYMMDD.json` — 감사 로그

`apply_overrides.py` 가 실행될 때마다 이 파일이 갱신됩니다(같은 날 여러 번 실행하면 마지막 실행 결과로 덮어씀).

각 entry 에는 다음 15개 필드가 모두 들어갑니다.


| 필드                          | 의미                                             |
| --------------------------- | ---------------------------------------------- |
| `date`                      | 대상 날짜                                          |
| `mode`                      | `dry_run` 또는 `commit`                          |
| `source_file`               | 후보 JSON 의 절대 경로                                |
| `target`                    | `module.NAME` 형식                               |
| `old_value`                 | 변경 전 모듈 상수 값                                   |
| `new_value`                 | 적용될 새 값(클램프 후)                                 |
| `op`                        | `set` / `increment` / `decrement` / `multiply` |
| `confidence`                | `low` / `medium` / `high`                      |
| `reason`                    | 사람용 설명                                         |
| `validation_status`         | `ok` / `failed`                                |
| `skipped_reason`            | 건너뛴 사유 (`""` 면 적용 가능)                          |
| `applied`                   | `true` / `false`                               |
| `rule_hash`                 | 동일 룰 식별용 안정 해시                                 |
| `classifier_version_before` | 적용 전 분류기 버전                                    |
| `classifier_version_after`  | 적용 후 분류기 버전                                    |


`skipped_reason` 종류:


| 값                       | 의미                                     |
| ----------------------- | -------------------------------------- |
| `""`                    | 건너뛰지 않음 (적용 가능)                        |
| `confidence_below_high` | confidence 가 high 가 아니라 commit 차단      |
| `not_approved`          | `allow_auto_apply` 가 false 라 commit 차단 |
| `validation_failed`     | 후보 형식이 잘못됨 (whitelist 외 target 등)      |
| `type_mismatch`         | 모듈 상수 타입이 숫자가 아님                       |
| `no_change`             | 새 값이 현재 값과 동일                          |
| `exceeded_daily_limit`  | 일일 변경 한도 초과                            |
| `fixture_failed`        | commit 후 fixture 테스트 실패 → 자동 rollback  |


### 5.7 `data/main.log` — 한 줄 요약 로그

`apply_overrides.py` 실행 시 자동으로 한 줄씩 추가됩니다. 형식:

```
2026-04-30 12:57:07 [INFO] [OVERRIDE][DRY_RUN] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=low applied=false
2026-04-30 12:57:07 [INFO] [OVERRIDE][SUMMARY] date=2026-04-30 mode=dry_run applied=0 skipped=0 total=1 source=data\reviews\rule_candidates_20260430.json
```

`[DRY_RUN]` 또는 `[COMMIT]` 태그로 모드가 즉시 식별됩니다. main.py 가 켜져 있을 때 같은 로그 파일에 기록됩니다.

---

## 6. 라벨 한눈에 보기

진입/청산 라벨의 의미는 [review_user_guide.md](review_user_guide.md) 의 "라벨 의미" 섹션에서 자세히 다룹니다. 여기서는 일람만:


| 진입 라벨            | 의미                               |
| ---------------- | -------------------------------- |
| `breakout_chase` | A급(0봉 돌파) 1차 추격 — 정상 진입          |
| `first_pullback` | B급(1봉 돌파+눌림) 또는 2차 본진입 — 눌림 후 진입 |
| `late_chase`     | 고점 추격성 진입 (PR-D 강화 로직)           |
| `fake_breakout`  | 진입 후 한 번도 못 오르고 손절 영역 진입         |



| 청산 라벨        | 의미                          |
| ------------ | --------------------------- |
| `good_stop`  | 손절 후 안 반등 — 잘 끊은 손절         |
| `bad_stop`   | +1R 갔다 손절 또는 손절 후 +1R 이상 반등 |
| `fast_take`  | 익절했지만 더 갔어야 함               |
| `late_take`  | 익절했지만 give-back 너무 큼        |
| `clean_exit` | 위 4 분류에 해당하지 않는 정상 청산       |


---

## 7. 자동 적용의 안전 원칙

1. **dry_run 이 기본값** — `--commit` 플래그가 명시되지 않으면 어떤 경우에도 모듈 상수가 변경되지 않습니다.
2. **승인이 두 단계** — 후보 JSON 의 `allow_auto_apply: true` (사람이 편집) + CLI `--commit` 플래그 (사람이 명시) 두 조건이 모두 만족돼야만 적용.
3. **confidence 게이트** — 누적 v2 표본이 충분(40건+)하고 5/10/20 영업일 모두 같은 패턴을 보일 때만 `high` confidence 가 부여되며, commit 단계는 high 만 적용합니다. *v1 fallback 거래가 confidence 를 부풀리지 못합니다.*
4. **변경 한도** — 하루 최대 3건(기본). 초과분은 자동 skip.
5. **rollback 훅** — main.py 부팅 시 fixture 테스트(`test_classifier`) 를 같이 돌려, 실패하면 자동 rollback.
6. **whitelist** — `entry_strategy` / `exit_strategy` / `classifier` 의 8개 상수만 변경 가능. 그 외 모듈 상수는 절대 변경되지 않음.
7. **장중 크래시 복원** — `data/portfolio_state.json` 영속화 덕에 main.py 가 죽고 재시작되어도 `entry_stage` / `stop_price` / `partial_taken` 같은 전략 필드가 보존됩니다. 잔고 TR 응답이 휘발성 필드만 덮어쓰고 전략 필드는 디스크 본을 따릅니다.

상세는 [review_safety_and_rollback.md](review_safety_and_rollback.md) 참고.

---

## 8. 체크리스트 — 본 문서를 다 읽었으면 답할 수 있어야 함

- 자동매매 리뷰 시스템이 매일 풀어주는 두 가지 문제는?
- 단계 1 ~ 8 의 순서를 외울 수 있는가? (장중 자동 / 매크로 / 1분봉 / 리뷰 / rolling / 후보 / dry_run / commit)
- 어떤 단계가 키움 API 를 호출하는가? (정답: 1단계 main.py, 2단계 fetch_market_context, 3단계 fetch_minute_bars)
- 어떤 모듈만 모듈 상수를 변경할 수 있는가?
- dry_run 과 commit 의 결정적 차이는?
- `applied_overrides_YYYYMMDD.json` 의 entry 에 들어가는 15개 필드 중 `skipped_reason` 7가지 종류를 알고 있는가?
- `allow_auto_apply` 가 기본 false 인 이유는?
- `confidence=high` 외에 commit 적용을 막는 다른 게이트 1개를 댈 수 있는가? (정답: `allow_auto_apply=true`, 일일 한도, fixture 테스트, validation, no_change)
- `dante_entry_training.csv` 와 `dante_shadow_training.csv` 가 각각 어떤 표본을 모으는지?
- 장중 main.py 가 죽고 재부팅되면 어떤 필드가 디스크에서 복원되고 어떤 필드는 잔고 TR 로 다시 채워지는지?
- rolling 의 `confidence` 가 v2 표본 수(`n_candidate`) 기준인 이유는?
- 매크로 JSON 이 없는 날에도 분석 파이프라인이 정상 동작하는 이유는? (정답: graceful fallback — `market_strength="unknown"` + 등락률 컬럼은 빈 값)

체크리스트의 모든 항목에 답할 수 없다면 [review_user_guide.md](review_user_guide.md) 를 함께 읽으면 됩니다.