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
[장 종료 후]                                      [다음 거래일 시작 전]
       |                                                    |
       v                                                    v
+-----------------+   +------------------+   +------------------+
|  매매 로그 수집 |-->|  1분봉 보강      |-->|  거래별 리뷰     |
|  (trade_log)    |   |  (fetch_minute_  |   |  (analyze_today) |
|                 |   |   bars.py)       |   |                  |
+-----------------+   +------------------+   +------------------+
                                                       |
                                                       v
                                           +-----------------------+
                                           |  rolling 누적 통계    |
                                           |  (review.rolling)     |
                                           +-----------------------+
                                                       |
                                                       v
                                           +-----------------------+
                                           |  rule_candidates 생성 |
                                           |  (review.rolling)     |
                                           +-----------------------+
                                                       |
                                                       v
                                           +-----------------------+
                                           |  dry_run 으로 검토    |
                                           |  (apply_overrides.py) |
                                           +-----------------------+
                                                       |
                                                       v
                                           +-----------------------+
                                           |  사람이 JSON 편집     |
                                           |  (allow_auto_apply)   |
                                           +-----------------------+
                                                       |
                                                       v
                                           +-----------------------+
                                           |  --commit 으로 적용   |
                                           |  (apply_overrides.py) |
                                           +-----------------------+
```

각 단계는 모두 **독립적으로 실행 가능한 별도 스크립트**입니다. 단계 사이는 파일(CSV, JSON)로만 연결되어 있어서 어떤 단계든 다시 돌리거나 수동으로 파일을 편집해 결과를 바꿀 수 있습니다.

---

## 3. 단계별 상세 흐름

### 단계 1 — 오늘 매매 로그 수집

이 단계는 자동매매 시스템(main.py)이 장중에 자동으로 수행합니다. 별도 실행 불필요.


| 항목    | 값                                      |
| ----- | -------------------------------------- |
| 입력    | 키움증권 실시간 체결 이벤트                        |
| 출력    | `data/trade_log.csv` (모든 매수/매도 이벤트 기록) |
| 실행 주체 | main.py (장중 자동)                        |


### 단계 2 — intraday 1분봉 보강

장 종료 후 별도 실행. 오늘 매매한 종목들의 1분봉 데이터를 키움 opt10080 TR 로 받아 캐시합니다. 이 데이터가 있어야 다음 단계의 리뷰에서 정밀한 진입 시점 분석(VWAP 대비 가격, 진입 전 3분 상승률, 진입봉 윗꼬리 등)을 할 수 있습니다.


| 항목    | 값                                                 |
| ----- | ------------------------------------------------- |
| 실행 명령 | `python fetch_minute_bars.py [YYYY-MM-DD]`        |
| 입력    | `data/trade_log.csv` (오늘 매매한 종목 코드 추출)            |
| 출력    | `data/intraday/YYYYMMDD/<종목코드>.csv` (종목별 1개 파일)   |
| 실패 시  | 해당 종목만 건너뛰고 다음 종목 진행 — 다음 단계는 5분봉 라벨로 자동 fallback |


### 단계 3 — 거래별 리뷰 생성

오늘 거래를 종목별로 묶고, 각 거래에 진입 분류(`entry_class`)와 청산 분류(`exit_class`), 그리고 사후 메트릭(MFE/MAE, give-back, over-run 등) 을 부여합니다.


| 항목    | 값                                                                                                                                    |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 실행 명령 | `python analyze_today.py [YYYY-MM-DD]`                                                                                               |
| 입력    | `data/trade_log.csv`, `data/dante_entry_training.csv`, `data/intraday/YYYYMMDD/*.csv`                                                |
| 출력    | `data/reviews/trade_review_YYYY-MM-DD.csv`, `data/reviews/daily_review_YYYY-MM-DD.md`, `data/reviews/rule_overrides_YYYY-MM-DD.json` |


### 단계 4 — rolling 누적 통계 생성

5/10/20 영업일 누적 통계를 만들어 *반복되는 패턴*을 찾습니다. 단일 일자로는 표본이 부족해서 단순한 우연을 룰 변경의 근거로 잡을 수 있는데, 누적 통계는 이걸 막아줍니다.


| 항목    | 값                                                                                          |
| ----- | ------------------------------------------------------------------------------------------ |
| 실행 명령 | `python -m review.rolling [YYYY-MM-DD]`                                                    |
| 입력    | `data/reviews/trade_review_*.csv` 여러 일자                                                    |
| 출력    | `data/reviews/rolling_summary_YYYYMMDD.json`, `data/reviews/rule_candidates_YYYYMMDD.json` |


### 단계 5 — rule_candidates 생성

단계 4 와 같은 명령(`review.rolling`) 으로 한 번에 만들어집니다. 누적 통계에서 트리거 조건이 충족된 룰만 골라 *후보*로 만듭니다. 이 시점에서는 어떤 룰도 자동 적용되지 않으며, 모든 후보의 `allow_auto_apply` 필드는 기본값 `false` 입니다.

### 단계 6 — dry_run 으로 적용 예정 룰 검토

`apply_overrides.py` 를 인자 없이 호출하면 dry_run 모드로 동작합니다.
**실제 모듈 상수는 절대 변경되지 않으며**, 적용 *예정* 내역만 감사 로그로 떨어뜨립니다.


| 항목    | 값                                                             |
| ----- | ------------------------------------------------------------- |
| 실행 명령 | `python apply_overrides.py [YYYY-MM-DD]` (--commit 없음)        |
| 입력    | `data/reviews/rule_candidates_YYYYMMDD.json`                  |
| 출력    | `data/reviews/applied_overrides_YYYYMMDD.json` (mode=dry_run) |


### 단계 7 — 사람이 확인 후 commit 적용

운영자가 단계 6 의 audit JSON 을 읽어보고, 적용해도 좋다고 판단한 후보의 `allow_auto_apply` 를 `true` 로 직접 편집합니다. 그 후 `--commit` 플래그로 다시 실행하면 실제 모듈 상수가 변경됩니다.


| 항목    | 값                                                                                    |
| ----- | ------------------------------------------------------------------------------------ |
| 실행 명령 | `python apply_overrides.py [YYYY-MM-DD] --commit`                                    |
| 안전장치  | `confidence=high` AND `allow_auto_apply=true` 인 후보만 적용                               |
| 출력    | `data/reviews/applied_overrides_YYYYMMDD.json` (mode=commit), `data/main.log` 한 줄 요약 |


---

## 4. 모듈 역할 정리


| 모듈/스크립트                | 역할                                    | 키움 API 호출    | 모듈 상수 변경         |
| ---------------------- | ------------------------------------- | ------------ | ---------------- |
| `analyze_today.py`     | 단일 일자 거래 묶음 + 분류 + 메트릭 + 일별 리뷰 산출     | 안 함          | 안 함              |
| `fetch_minute_bars.py` | 1분봉 캐시 수집 (별도 nightly job)            | 함 (opt10080) | 안 함              |
| `review/intraday.py`   | 캐시된 1분봉 CSV 로 정밀 메트릭/D 피처 계산          | 안 함          | 안 함              |
| `review/rolling.py`    | 5/10/20 영업일 누적 통계 + 룰 후보 산출           | 안 함          | 안 함              |
| `review/classifier.py` | 진입 4종 + 청산 4종 자동 분류 (v2 강화 로직)        | 안 함          | 안 함              |
| `review/overrides.py`  | 룰 후보 검증 + dry_run/commit 적용기 (단일 진입점) | 안 함          | **commit 시에만** 함 |
| `apply_overrides.py`   | `review/overrides.py` 의 사람용 CLI 래퍼    | 안 함          | 위와 동일            |


이 표에서 보듯, 모듈 상수를 실제로 변경하는 경로는 단 하나 (`review/overrides.py` 의 `commit_overrides`) 뿐입니다. 다른 모든 모듈은
파일을 읽고/쓰기만 합니다.

---

## 5. 생성되는 주요 파일

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

### 5.2 `data/reviews/trade_review_YYYY-MM-DD.csv` — 거래별 상세

거래 한 건당 한 행. 진입/청산 분류, R 배수, MFE/MAE, give-back, 1분봉 정밀메트릭, D 피처(고점 대비 진입 위치, VWAP 대비, 진입봉 몸통/윗꼬리 등), late_chase 디버그 필드까지 들어갑니다. 전체 50여 개 컬럼.

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
      "confidence": "medium",
      "overall": {"win_rate": 0.4, "avg_r": -0.04, "profit_factor": 0.91},
      "by_entry_class": {"breakout_chase": {...}, "first_pullback": {...}},
      "by_exit_class":  {"bad_stop": {...}, "late_take": {...}},
      "by_entry_exit":  {"breakout_chase|bad_stop": {...}}
    }
  ]
}
```

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
3. **confidence 게이트** — 누적 표본이 충분(40건+)하고 5/10/20 영업일 모두 같은 패턴을 보일 때만 `high` confidence 가 부여되며, commit 단계는 high 만 적용합니다.
4. **변경 한도** — 하루 최대 3건(기본). 초과분은 자동 skip.
5. **rollback 훅** — main.py 부팅 시 fixture 테스트(`test_classifier`) 를 같이 돌려, 실패하면 자동 rollback.
6. **whitelist** — `entry_strategy` / `exit_strategy` / `classifier` 의 8개 상수만 변경 가능. 그 외 모듈 상수는 절대 변경되지 않음.

상세는 [review_safety_and_rollback.md](review_safety_and_rollback.md) 참고.

---

## 8. 체크리스트 — 본 문서를 다 읽었으면 답할 수 있어야 함

- 자동매매 리뷰 시스템이 매일 풀어주는 두 가지 문제는?
- 단계 1 ~ 7 의 순서를 외울 수 있는가?
- 어떤 단계가 키움 API 를 호출하는가?
- 어떤 모듈만 모듈 상수를 변경할 수 있는가?
- dry_run 과 commit 의 결정적 차이는?
- `applied_overrides_YYYYMMDD.json` 의 entry 에 들어가는 15개 필드 중 `skipped_reason` 7가지 종류를 알고 있는가?
- `allow_auto_apply` 가 기본 false 인 이유는?
- `confidence=high` 외에 commit 적용을 막는 다른 게이트 1개를 댈 수 있는가? (정답: `allow_auto_apply=true`, 일일 한도, fixture 테스트, validation, no_change)

체크리스트의 모든 항목에 답할 수 없다면 [review_user_guide.md](review_user_guide.md) 를 함께 읽으면 됩니다.