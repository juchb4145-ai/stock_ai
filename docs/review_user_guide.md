# 자동매매 리뷰/룰 개선 — 운영자 사용 가이드

본 문서는 **장 종료 후 매일 따라 하는 절차**를 정리합니다. 명령어 그대로 복사해 쓰면 되도록 작성했습니다. 시스템 전반의 그림은  
[review_system_overview.md](review_system_overview.md) , 안전장치 상세는[review_safety_and_rollback.md](review_safety_and_rollback.md) 를 보세요.

---

## 1. 매일 실행할 7단계 (요약)


| 단계  | 명령어                                                                 | 모드      | 변경 발생?             |
| --- | ------------------------------------------------------------------- | ------- | ------------------ |
| 1   | `python fetch_market_context.py 2026-04-30`                         | 매크로 수집  | data/reviews 만 갱신  |
| 2   | `python fetch_minute_bars.py 2026-04-30`                            | 캐시 수집   | data/intraday 만 갱신 |
| 3   | `.\.venv\Scripts\python.exe .\analyze_today.py 2026-04-30`          | 일별 리뷰   | data/reviews 만 갱신  |
| 4   | `.\.venv\Scripts\python.exe -m review.rolling 2026-04-30`           | 누적 통계   | data/reviews 만 갱신  |
| 5   | `.\.venv\Scripts\python.exe apply_overrides.py 2026-04-30`          | dry_run | 없음 (감사 로그만)        |
| 6   | (사람이) `data/reviews/rule_candidates_20260430.json` 편집               | 검토/승인   | JSON 1줄 수정         |
| 7   | `.\.venv\Scripts\python.exe apply_overrides.py 2026-04-30 --commit` | commit  | **모듈 상수 변경**       |


**날짜 형식 주의**: 파일명에 따라 `YYYY-MM-DD` 또는 `YYYYMMDD` 가 섞여 있어 보일 수 있으나, 명령어 인자로는 항상 `YYYY-MM-DD` (하이픈) 입니다.

**1, 2단계 환경**: `fetch_market_context` 와 `fetch_minute_bars` 는 키움 OpenAPI 가 동작하는 32-bit Python 환경에서 실행되어야 합니다 (main.py 와 동일).

---

## 2. 단계별 상세

### 단계 1 — 시장 매크로 수집

```
python fetch_market_context.py 2026-04-30
```

옵션:


| 옵션              | 의미                                          | 예                                |
| --------------- | ------------------------------------------- | -------------------------------- |
| `--reviews-dir` | 매크로 JSON 저장 디렉토리 (기본 `data/reviews`)         | `--reviews-dir custom/path`      |
| `--force`       | 캐시(이미 존재하는 JSON) 무시하고 재수집                   | `--force`                        |


성공 출력 예시:

```
== fetch_market_context 2026-04-30 ==
  - 저장: data/reviews/market_context_2026-04-30.json
  - KOSPI  종가 +0.78%, 일중최고 +1.25%
  - KOSDAQ 종가 +1.14%, 일중최고 +1.81%
```

> **주의** — 키움 OpenAPI 로그인이 필요한 32-bit Python 환경에서만 자동 fetch 됩니다.
> 운영 환경에서 자동 fetch 가 어려운 경우, `data/reviews/market_context_YYYY-MM-DD.json` 을 수동으로 작성해도 분석 파이프라인이 동일하게 동작합니다 (`source: "manual"` 같이 표시). 파일이 아예 없으면 매크로 컬럼은 빈 값 / `market_strength="unknown"` 으로 graceful fallback.

### 단계 2 — 1분봉 수집

```
python fetch_minute_bars.py 2026-04-30
```

옵션:


| 옵션               | 의미                         | 예                                        |
| ---------------- | -------------------------- | ---------------------------------------- |
| `--codes`        | trade_log 가 아니라 지정한 종목만 수집 | `--codes 050890,038460`                  |
| `--force`        | 캐시(이미 받은 csv) 무시하고 재수집     | `--force`                                |
| `--intraday-dir` | 저장 디렉토리 변경                 | `--intraday-dir tests/fixtures/intraday` |


> **주의** — 키움증권 OpenAPI 가 로그인 가능한 PyQt 환경에서만 동작합니다.
> 로그인 실패 시 stderr 에 `[fetch_minute_bars] 로그인 실패` 가 찍히고 모든 종목이 `failed` 로 분류됩니다. 그래도 다음 단계는 정상 진행되며 5분봉 fallback 으로 자동 동작합니다.

성공 출력 예시:

```
== fetch_minute_bars 2026-04-30 (codes=4) ==
  - fetched: 4
      · 050890: 380 rows -> data\intraday\20260430\050890.csv
      · 038460: 360 rows -> data\intraday\20260430\038460.csv
      · 082800: 380 rows -> data\intraday\20260430\082800.csv
      · 307180: 372 rows -> data\intraday\20260430\307180.csv
  - cached:  0
  - failed:  0
```

### 단계 3 — 일별 리뷰 생성

```
python analyze_today.py 2026-04-30
```

옵션:


| 옵션               | 의미                             |
| ---------------- | ------------------------------ |
| `--intraday-dir` | 1분봉 캐시 위치 (기본 `data/intraday`) |
| `--reviews-dir`  | 매크로/리뷰 디렉토리 (기본 `data/reviews`) |
| `--no-intraday`  | 1분봉 단계 건너뛰기 (디버그용)             |


성공 출력 예시:

```
== 2026-04-30 매매 복기 ==
  - 거래 4건 (청산 완료 4건)
  - 1분봉 정밀: 3건 / fallback: 1건 / missing: 0건
  - 시장 컨텍스트: strong (KOSPI +0.78% / KOSDAQ +1.14%, source=kiwoom_opt20006)
  - 추천 룰 1건
  - csv:  data\reviews\trade_review_2026-04-30.csv
  - md:   data\reviews\daily_review_2026-04-30.md
  - json: data\reviews\rule_overrides_2026-04-30.json
```

매크로 JSON 이 없으면 "시장 컨텍스트: 데이터 없음 (market_context_*.json 미작성)" 으로 표시되고 trade_review 의 매크로 컬럼은 빈 값으로 남습니다. 분석 자체는 계속 진행됩니다.

이 단계 후에는 `data/reviews/daily_review_2026-04-30.md` 를 직접 열어 **사람이 먼저 한 번 읽어 보는 것이 권장**됩니다. 그날 매매가 정상이었는지, 분류가 합리적인지 1분만 보면 확인할 수 있습니다.

### 단계 4 — 누적 통계 생성

```
python -m review.rolling 2026-04-30
```

옵션:


| 옵션                  | 의미                                        |
| ------------------- | ----------------------------------------- |
| `--windows 5,10,20` | 윈도우 변경 (기본 `5,10,20`)                     |
| `--reviews-dir`     | trade_review_*.csv 위치 (기본 `data/reviews`) |
| `--no-write`        | JSON 출력 없이 stdout 요약만                     |


성공 출력 예시:

```
== rolling summary as_of 2026-04-30 ==
  [5d] dates=5건 trades=25 avg_r=-0.04R win=40% pf=0.91 confidence=medium
  [10d] dates=10건 trades=58 avg_r=-0.02R win=43% pf=0.95 confidence=high
  [20d] dates=20건 trades=110 avg_r=-0.01R win=44% pf=0.97 confidence=high
  - 룰 후보 3건 (모두 auto_apply=false):
      · break_even_cut    | windows=[5, 10, 20] | confidence=high   | n=42 | consistent=True
      · take_profit_faster| windows=[10, 20]    | confidence=medium | n=15 | consistent=False
      · wait_for_pullback | windows=[10, 20]    | confidence=medium | n=22 | consistent=False
  - summary:    data\reviews\rolling_summary_20260430.json
  - candidates: data\reviews\rule_candidates_20260430.json
```

`rolling_summary_*.json` 의 각 윈도우는 `n_total` (전체 거래 수) 와 `n_candidate` (v2 분류기 거래 수 — confidence 결정에 사용) 두 가지를 둡니다. v1 fallback 비율을 보려면 `by_classifier_version` 키 확인.

### 단계 5 — dry_run 으로 검토

```
python apply_overrides.py 2026-04-30
```

`--commit` 플래그가 **없으므로** 실제 모듈 상수는 어떤 경우에도 변경되지 않습니다. 적용 *예정* 만 계산해서 audit JSON 으로 떨어집니다.

성공 출력 예시:

```
2026-04-30 12:57:07 [INFO] [OVERRIDE][DRY_RUN] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=high applied=false
2026-04-30 12:57:07 [INFO] [OVERRIDE][SUMMARY] date=2026-04-30 mode=dry_run applied=0 skipped=0 total=1 source=data\reviews\rule_candidates_20260430.json
== apply_overrides 2026-04-30 (dry_run) ==
  source: data\reviews\rule_candidates_20260430.json
  audit:  data\reviews\applied_overrides_20260430.json
  applied=0 skipped=0 total=1
  * dry_run 모드: 실제 모듈 상수는 변경되지 않았습니다.
  * 검토 후 적용하려면 후보 JSON 의 allow_auto_apply 를 true 로 편집한 뒤
    'python apply_overrides.py 2026-04-30 --commit' 으로 다시 실행하세요.
```

### 단계 6 — JSON 편집해서 승인

`data/reviews/rule_candidates_20260430.json` 을 텍스트 에디터로 엽니다.
적용하고 싶은 후보의 `allow_auto_apply` 만 `false` → `true` 로 변경합니다.

**변경 전** (rolling.py 가 만든 그대로):

```json
{
  "rule_id": "break_even_cut",
  "confidence": "high",
  "consistent_across_windows": true,
  "allow_auto_apply": false,
  "auto_apply": false,
  "proposed_overrides": [...]
}
```

**변경 후** (사람이 승인):

```json
{
  "rule_id": "break_even_cut",
  "confidence": "high",
  "consistent_across_windows": true,
  "allow_auto_apply": true,
  "auto_apply": false,
  "proposed_overrides": [...]
}
```

> **주의** — `auto_apply` 와 `allow_auto_apply` 는 다릅니다.
>
> - `auto_apply` 는 rolling 모듈이 *결과로 자동 적용했는지* 의 기록입니다.
> rolling 모듈은 자동 적용을 절대 안 하므로 항상 `false`. 건드리지 마세요.
> - `allow_auto_apply` 는 *PR-A 가 commit 단계에서 시도해도 좋은가* 의 정책입니다. 사람이 직접 `true` 로 편집해야만 적용 후보가 됩니다.

### 단계 7 — commit 으로 실제 적용

```
python apply_overrides.py 2026-04-30 --commit
```

성공 시 출력 예시:

```
2026-04-30 13:10:21 [INFO] [OVERRIDE][COMMIT] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=high applied=true
2026-04-30 13:10:21 [INFO] [OVERRIDE][SUMMARY] date=2026-04-30 mode=commit applied=1 skipped=0 total=1 source=data\reviews\rule_candidates_20260430.json
== apply_overrides 2026-04-30 (commit) ==
  source: data\reviews\rule_candidates_20260430.json
  audit:  data\reviews\applied_overrides_20260430.json
  applied=1 skipped=0 total=1
```

차단 시 출력 예시 (예: confidence 가 high 가 아닌데 commit 시도한 경우):

```
2026-04-30 13:10:21 [INFO] [OVERRIDE][COMMIT] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=medium applied=false skipped=confidence_below_high
```

> **주의** — commit 이 끝나면 **현재 실행 중인 Python 프로세스의 모듈 상수만** 변경됩니다. 이미 실행 중인 main.py 는 영향받지 않으며, 다음 부팅 시 main.py 가 같은 commit 시퀀스를 호출해야 그 룰이 거래 시점에 반영됩니다.  
> 본 PR 에서는 main.py 자동 호출 코드는 일부러 추가하지 않았습니다.

---

## 3. dry_run 과 commit 의 차이


| 항목                  | dry_run (기본)     | commit (`--commit`) |
| ------------------- | ---------------- | ------------------- |
| 모듈 상수 변경            | 안 함              | 함                   |
| audit JSON 출력       | 함 (mode=dry_run) | 함 (mode=commit)     |
| main.log 한 줄 요약     | 함                | 함                   |
| confidence 검사       | 검사하되 차단은 안 함     | high 만 적용, 그 외 skip |
| allow_auto_apply 검사 | 검사하되 차단은 안 함     | true 만 적용, 그 외 skip |
| 일일 한도 검사            | 검사하되 차단은 안 함     | 한도 초과분 skip         |
| fixture 테스트 hook    | 호출 안 함           | 호출 함 (있으면)          |


**결론적으로 dry_run 은 시뮬레이션이고, commit 은 실제 적용입니다.** dry_run 결과의 `new_value` 컬럼이 그대로 commit 시 적용될 값입니다.

---

## 4. confidence 의 의미 (low / medium / high)

`rolling.py` 가 후보를 만들 때 다음 기준으로 confidence 를 매깁니다.


| confidence | 표본 수 (`n_candidate` = v2 거래) | 일관성                  | commit 적용 가능?                                      |
| ---------- | --------------------------- | -------------------- | -------------------------------------------------- |
| `low`      | 20건 미만                      | 무관                   | **불가능** (`skipped_reason="confidence_below_high"`) |
| `medium`   | 20 ~ 39건                    | 무관                   | 불가능                                                |
| `high`     | 40건 이상                      | 5/10/20 모든 윈도우에서 트리거 | 가능                                                 |


40건 이상이어도 5/10/20 중 일부에서만 트리거되면 자동으로 `medium` 으로 강등되니, "충분한 표본 + 일관된 패턴" 이 high 의 두 조건입니다.

> **주의** — `n_total` 이 아니라 `n_candidate` 기준입니다. v1 fallback 거래(1분봉 D 피처가 없어 분류 임계가 다른 거래) 는 후보 평가에서 제외되므로, v1 비율이 높은 날은 `n_total = 50` 인데 `n_candidate = 18` → low confidence 로 떨어질 수 있습니다. 이 경우 `fetch_minute_bars.py` 가 1분봉을 잘 받아왔는지 확인하세요.

---

## 5. allow_auto_apply 의 의미

`true` 로 설정해야만 commit 단계에서 *적용 시도*가 됩니다. 그래도 실제로 적용되려면 다음 4가지가 모두 충족돼야 합니다.

1. `confidence == "high"`
2. `allow_auto_apply == true`
3. 변경 후보 수가 일일 한도(`max_daily_rule_changes`, 기본 3) 이내
4. `validation_status == "ok"` (whitelist, 타입, min/max 모두 통과)

이 중 하나라도 어기면 `applied=false` + 적절한 `skipped_reason` 이 audit 에 기록되고, 모듈 상수는 변경되지 않습니다.

---

## 6. 진입/청산 라벨 의미

### 6.1 진입 라벨 (`entry_class`)


| 라벨               | 정상/문제  | 정의                                            |
| ---------------- | ------ | --------------------------------------------- |
| `breakout_chase` | 정상     | A급(0봉 돌파) 1차 추격. 거래량/체결강도/스프레드 모두 통과한 정상 진입   |
| `first_pullback` | 정상     | B급(1봉 돌파만) 또는 2차 본진입(눌림 후). 가장 안전한 진입 패턴      |
| `late_chase`     | **문제** | 고점 근처 추격성 진입. 10개 점수 조건 중 3개 이상 충족 시 분류       |
| `fake_breakout`  | **문제** | 진입 후 한 번도 +0.5R 못 가고 -1R 영역 진입한 거래. 무조건 우선 분류 |


late_chase 의 점수 조건 10가지(reason 문자열):


| reason                   | 충족 조건                      |
| ------------------------ | -------------------------- |
| `near_session_high`      | 진입가가 당일 고점의 99% 이상         |
| `prior_3m_overshot`      | 직전 3분 상승률 ≥ 3%             |
| `prior_5m_overshot`      | 직전 5분 상승률 ≥ 5%             |
| `above_vwap`             | VWAP 대비 진입가 ≥ +2%          |
| `shallow_drop_from_high` | 고점 대비 진입가 -0.8% 이내 (거의 고점) |
| `no_pullback`            | 직전 고점 대비 눌림 ≤ 1%           |
| `late_after_peak`        | 고점 형성 후 60초 이상 지나서 진입      |
| `long_observation`       | 조건 편입 후 180초 이상 경과         |
| `long_upper_wick`        | 진입봉 윗꼬리 비율 ≥ 35%           |
| `weak_body`              | 진입봉 몸통 비율 ≤ 45%            |


**강한 패턴 우선** — `near_session_high` + `prior_3m_overshot` + `no_pullback` 3가지가 동시에 충족되면 점수 무관하게 즉시 late_chase.

**돌파 보호 패턴** — `volume_ratio_1m ≥ 2.0` + `breakout_candle_body_pct ≥ 0.55`

- `upper_wick_pct ≤ 0.25` 셋 모두 동시 충족 시 점수가 높아도 breakout_chase 로 보호 (`breakout_chase_protected = true`).

### 6.2 청산 라벨 (`exit_class`)


| 라벨           | 정상/문제  | 정의                                          |
| ------------ | ------ | ------------------------------------------- |
| `clean_exit` | 정상     | 위 4 분류 외 정상 청산 (예: BE 위 +0.5R 익절, 시간 손절 등)  |
| `good_stop`  | 정상     | 손절 후 추가 하락 — 잘 끊은 손절                        |
| `bad_stop`   | **문제** | +1R 도달 후 손절 OR 손절 후 +1R 이상 반등               |
| `fast_take`  | **문제** | over_run ≥ 1R 이고 give-back ≤ 0.3R — 더 갔어야 함 |
| `late_take`  | **문제** | give-back ≥ 0.7R — 최고가 한참 반납하고 청산           |


청산 라벨 3대 지표:

- **MFE (Maximum Favorable Excursion)** — 진입 후 25분 내 최대 미실현 이익. R 배수로 환산 → `mfe_r`.
- **MAE (Maximum Adverse Excursion)** — 같은 구간 최대 미실현 손실 → `mae_r`.
- **give-back** — `MFE - 실제 청산 수익` (R 배수). 클수록 최고가 대비 많이 반납.

---

## 7. applied_overrides_YYYYMMDD.json 읽는 법

**감사 로그 한 entry 예시:**

```json
{
  "date": "2026-04-30",
  "mode": "commit",
  "source_file": "data\\reviews\\rule_candidates_20260430.json",
  "target": "exit_strategy.EXIT_BE_R",
  "old_value": 1.0,
  "new_value": 0.7,
  "op": "decrement",
  "confidence": "high",
  "reason": "+1R 도달 후 손절 비율 30% 이상 반복",
  "validation_status": "ok",
  "skipped_reason": "",
  "applied": true,
  "rule_hash": "f69c63e12978",
  "classifier_version_before": "v2",
  "classifier_version_after": "v2"
}
```

읽는 순서:

1. `**mode**` 부터 본다. `dry_run` 이면 아래 모든 값은 *예상*. `commit`이면 *실제 결과*.
2. `**applied`** 가 `true` 면 `target` 의 모듈 상수가 `old_value` 에서 `new_value` 로 실제 변경됨. `false` 면 변경 안 됨.
3. `**skipped_reason*`* 이 비어 있지 않으면 그 사유로 차단됨. 사유별 의미는[review_system_overview.md](review_system_overview.md) §5.6 참조.
4. `**rule_hash**` 가 같으면 동일 룰. 여러 날의 같은 후보를 추적할 때 사용.
5. `classifier_version_*` 가 다르면 분류기 버전이 commit 사이에 바뀐 것. 보통 `v2` 로 동일.

---

## 8. commit 하면 안 되는 상황 — 체크리스트

다음 중 하나라도 해당하면 commit 하지 마세요. 다음 거래일에 손실 확대 가능성이 큽니다.

- **장중**입니다. (commit 은 반드시 장 종료 후 ~ 다음 장 시작 전 사이)
- **trade_log.csv 에 그날 거래가 비정상적으로 적습니다** (예: 평소 5건 이상인데 1건). 표본 부족으로 잘못된 룰을 강화할 위험.
- **분류 결과가 직관과 너무 다릅니다.** 예: 명백한 가짜돌파인데 breakout_chase 로 분류, 또는 정상 거래가 late_chase 로 분류. 우선  
`daily_review_*.md` 와 `late_chase_reasons` 컬럼을 확인.
- **rule_candidates JSON 의** `confidence` **가 모두** `low` **또는** `medium`입니다. high 가 아니면 commit 해도 어차피 적용 안 됩니다 (시간  
낭비).
- **proposed_overrides 의** `target` **이 평소 보던 것과 다릅니다.** 예: `entry_strategy.SOMETHING_NEW` 가 보이면 코드 변경이 있는 것이니
먼저 코드 리뷰.
- `**new_value` 가 `old_value` 와 너무 다릅니다.** 보통 `decrement by 0.3` 정도가 권장 — 그 이상의 변동폭이라면 임계값 점검.
- **단일 거래 1건** 으로 트리거된 후보입니다. (rolling.py 가 보통 N>=2일 때만 트리거하지만, 직접 편집한 JSON 이라면 가능)
- **commit 직전 fixture 테스트(`test_classifier`) 가 실패**합니다.
commit 시 자동 rollback 되긴 하지만 실패 원인을 먼저 잡아야 합니다.

---

## 9. 자주 묻는 질문

**Q1. 같은 날 commit 을 두 번 하면 어떻게 되나요?**  
A. 첫 번째 commit 의 결과가 그대로 적용된 모듈 상수 위에서, 두 번째 commit이 다시 평가됩니다. 두 번째에서는 이미 적용된 룰의 `new_value` 가 `current_value` 가 되므로 (decrement by 0.3 같은 op 가 누적됨), 의도치 않은 중복 적용 가능성이 있습니다. 같은 날 commit 은 한 번만 실행하는 것을 권장.

**Q2. 어제 commit 을 했는데 오늘도 같은 룰이 후보로 다시 올라옵니다.**
A. rolling.py 는 *현재 모듈 상수* 와 무관하게 누적 통계만 보고 후보를 만듭니다. 같은 패턴이 계속 반복되면 같은 후보가 계속 올라옵니다. 단,  
`apply_override` 의 클램프 로직이 모듈 상수를 화이트리스트의 hard min 아래로는 절대 안 떨어뜨리므로 무한 감소는 발생하지 않습니다.

**Q3. dry_run 도 안 돌렸는데 모듈 상수가 바뀐 것 같습니다.**  
A. main.py 가 부팅 시 자동으로 commit 하는 코드가 있는지 확인하세요. 본 PR 까지의 코드에는 main.py 자동 commit 호출이 **일부러 들어있지 않습니다**. 누군가가 추가했다면 그 코드를 검토.

**Q4.** `data/reviews/applied_overrides_20260430.json` **이 사라졌어요.**  
A. 같은 날 dry_run / commit 을 다시 실행하면 그 파일은 마지막 실행 결과로 덮어쓰여집니다. 이전 실행 결과가 필요하면 별도 백업이 필요합니다. 향후 `history/` 디렉토리에 누적하는 옵션을 추가할 수도 있습니다.

---

## 10. 매일 운영 체크리스트

다음 항목을 매일 순서대로 체크하면 안전합니다.

**장 종료 직후**

- `data/trade_log.csv` 마지막 줄이 오늘 날짜인지 확인
- `data/dante_entry_training.csv` 의 마지막 sample 들이 오늘 진입 후보인지 확인 (라벨링은 25분 후)
- `data/dante_shadow_training.csv` 도 함께 누적되는지 (게이트 거른 표본; false-negative 측정용)
- `data/portfolio_state.json` 에 보유 종목이 정상 반영돼 있는지 (장중 크래시 후 재부팅 시 자동 복원의 진실 소스)
- `python fetch_market_context.py YYYY-MM-DD` 실행
- `data/reviews/market_context_YYYY-MM-DD.json` 작성 확인 (KOSPI/KOSDAQ 등락률 출력)
- `python fetch_minute_bars.py YYYY-MM-DD` 실행
- `data/intraday/YYYYMMDD/` 안에 매수한 종목 수만큼 CSV 가 있는지 확인
- 누락 종목이 있으면 `--codes` 로 단일 종목 재시도

**리뷰 단계**

- `python analyze_today.py YYYY-MM-DD` 실행
- `data/reviews/daily_review_YYYY-MM-DD.md` 직접 열어 1분 훑어보기
- 분류 결과가 직관과 일치하는지 (특히 `late_chase`, `fake_breakout`)
- 1분봉 정밀 메트릭 적용률이 50% 이상인지
- 출력의 "시장 컨텍스트" 라인이 `unknown` 이 아닌지 (unknown 이면 매크로 fetch 실패)

**누적 통계**

- `python -m review.rolling YYYY-MM-DD` 실행
- `data/reviews/rolling_summary_YYYYMMDD.json` 의 `n_candidate` / `confidence` 확인
- `by_classifier_version` 의 v1 비율이 비정상적으로 높지 않은지 (v1 비율 30%+ 이면 1분봉 캐시 점검)
- `data/reviews/rule_candidates_YYYYMMDD.json` 에 high 후보가 있는지

**dry_run 검토**

- `python apply_overrides.py YYYY-MM-DD` (dry_run)
- `data/reviews/applied_overrides_YYYYMMDD.json` 의 각 entry 확인
- `validation_status == "ok"` 인지
- `new_value` 가 합리적 범위인지 (보통 ±15% 이내 변동)
- `skipped_reason` 의 사유가 이해되는지

**commit 결정**

- §8 의 "commit 하면 안 되는 상황" 체크리스트를 모두 통과
- 적용할 후보의 `allow_auto_apply` 를 JSON 에서 `true` 로 변경
- `python apply_overrides.py YYYY-MM-DD --commit` 실행
- audit JSON 의 `mode == "commit"`, `applied == true` 확인
- `data/main.log` 마지막 부분에 `[OVERRIDE][COMMIT]` 한 줄이 있는지

이 체크리스트를 매일 같은 순서로 실행하면 잘못된 적용 위험이 거의 0 에 수렴합니다.