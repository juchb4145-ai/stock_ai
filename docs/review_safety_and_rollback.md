# 자동매매 리뷰/룰 개선 — 안전장치와 롤백 가이드

본 문서는 자동 적용 기능이 *실거래에 어떤 안전장치를 두고 있는지*, 그리고 *문제가 생겼을 때 어떻게 되돌리는지* 를 정리합니다. 평소에는 거의 볼 일이 없지만, 한 번이라도 commit 후 이상 동작이 의심되면 바로 펼쳐 봐야 하는 참고서입니다.

전체 그림은 [review_system_overview.md](review_system_overview.md), 일상
사용은 [review_user_guide.md](review_user_guide.md) 를 보세요.

---

## 1. 적용기 6중 게이트 — 한 번에 보기

`commit_overrides()` 가 `setattr(module, attr, new_value)` 까지 가려면 모든 게이트를 통과해야 합니다.


| 순서  | 게이트                                    | 차단 시 사유                                |
| --- | -------------------------------------- | -------------------------------------- |
| 1   | 명시적 `--commit` 플래그                     | (CLI 차단; 사유 기록 안 됨)                    |
| 2   | `confidence == "high"`                 | `confidence_below_high`                |
| 3   | `allow_auto_apply == true`             | `not_approved`                         |
| 4   | `target` 이 TARGET_WHITELIST 안 + 타입이 숫자 | `validation_failed` 또는 `type_mismatch` |
| 5   | `new_value != old_value`               | `no_change`                            |
| 6   | 일일 변경 한도 이내                            | `exceeded_daily_limit`                 |
| 7   | (commit 후) fixture 테스트 통과              | `fixture_failed` (rollback 동반)         |


**6 + 7번 게이트는 commit 모드에서만** 작동합니다. dry_run 에서는 게이트 사유만 표시하고 차단은 안 합니다 (시뮬레이션 목적).

> **주의** — 어떤 게이트도 우회 가능한 옵션을 두지 않았습니다. 예외 상황도 코드 수정으로만 가능하며, 그 변경은 git diff 와 코드 리뷰에 남습니다.

---

## 2. TARGET_WHITELIST — 변경 가능한 모듈 상수 8개

`review/overrides.py` 상단에 정의된 8개만 변경 가능합니다.


| target                                    | hard min | hard max | 의미                     |
| ----------------------------------------- | -------- | -------- | ---------------------- |
| `entry_strategy.MAX_UPPER_WICK_RATIO`     | 0.10     | 0.80     | 5분봉 진행봉 윗꼬리 비율 상한      |
| `entry_strategy.OVERHEATED_OPEN_RETURN`   | 0.03     | 0.20     | 시가 대비 과열 차단 임계         |
| `entry_strategy.OVERHEATED_BB55_DISTANCE` | 0.01     | 0.10     | BB55 상단 대비 과열 거리       |
| `entry_strategy.DANTE_FIRST_ENTRY_RATIO`  | 0.00     | 0.50     | 1차 추격 비율 (0 이면 추격 비활성) |
| `exit_strategy.EXIT_BE_R`                 | 0.30     | 1.50     | BE 스탑 이동 R 배수          |
| `exit_strategy.EXIT_PARTIAL_R`            | 1.00     | 3.50     | 부분익절 R 배수              |
| `exit_strategy.EXIT_PARTIAL_RATIO`        | 0.20     | 0.80     | 부분익절 비율                |
| `exit_strategy.TRAIL_HIGHEST_GIVEBACK_R`  | 0.30     | 1.50     | 잔량 트레일링 give-back R    |


**hard min/max 는 절대 위반 불가**합니다. 룰이 이보다 낮은 값을 권장해도 `apply_override` 가 강제로 이 범위 안으로 클램프합니다.

> **주의** — 화이트리스트에 새 target 을 추가하려면 다음 3 곳을 동시에 수정해야 합니다 (의도된 마찰):
>
> 1. `TARGET_WHITELIST` 에 키 추가
> 2. `_TARGET_MODULES` 매핑에 모듈 객체 추가
> 3. 파일 상단에 명시적 `import` 추가
>
> 한 곳만 빼먹으면 PR-A 가 시작 시점에 에러를 내거나 그 target 을 영구히 무시합니다. 동적 import 는 일절 사용하지 않습니다.

---

## 3. eval / exec / 동적 import 를 금지한 이유

**이유 1 — 임의 코드 실행 차단**

만약 `proposed_overrides` 의 값이 `"max(0.20, MAX_UPPER_WICK_RATIO - 0.10)"` 같은 문자열이고 적용기가 이걸 `eval()` 한다면, 후보 JSON 파일을 조작한 누군가가 임의 코드를 실행시킬 수 있습니다. 본 시스템은 모든 후보를 구조화된 dict (`{"op": "decrement", "by": 0.10, ...}`) 로만 받고, op 는 화이트리스트 4개(`set / increment / decrement / multiply`) 안에서 분기로만 처리합니다.

**이유 2 — 동적 import 의 부작용 차단**

`importlib.import_module(target.split(".")[0])` 같은 코드는 target 모듈 이름이 곧 import 가능한 모든 Python 모듈로 통하므로, 화이트리스트 외 모듈도 import 시도가 발생합니다. 본 시스템은 적용 가능한 모듈을 파일 상단에 정적 import 한 뒤 `_TARGET_MODULES` 매핑에서만 lookup 합니다.

**이유 3 — 코드 감사 가능성**

`grep` 으로 `eval(`, `exec(`, `importlib.import_module`, `__import__(` 토큰을 검색하면 `review/overrides.py` 본문에 zero match 가 나와야 합니다. 이를 단위 테스트(`StaticImportPolicyTest`) 가 매 실행마다 자동 검증합니다 — 누군가 실수로 추가하면 즉시 테스트 실패.

---

## 4. min/max 범위 검증 — 두 단계 클램프

`apply_override(ov, current_value)` 의 내부 동작:

```
1. validate_override(ov)            # whitelist + op + 필수 필드 검증
2. raw_new_value = op 적용            # 예: current - by
3. new_value = clamp(raw_new_value, ov.min, ov.max)        # 룰 자체 min/max
4. new_value = clamp(new_value, hard_min, hard_max)        # whitelist 하드 캡
5. return new_value
```

따라서 룰의 `min` 과 hard cap 의 `min` 중 *큰 쪽*이, 그리고 `max` 중 *작은 쪽*이 적용됩니다 (교집합).

**예시 1** — 룰이 `{"op": "decrement", "by": 0.5, "min": 1.0}`, `exit_strategy.EXIT_PARTIAL_R` 의 hard cap 은 `min=1.0, max=3.5`. 현재 값 2.0:

```
raw = 2.0 - 0.5 = 1.5
clamp(1.5, rule_min=1.0, rule_max=None) = 1.5
clamp(1.5, hard_min=1.0, hard_max=3.5) = 1.5
new_value = 1.5
```

**예시 2** — 룰이 `{"op": "decrement", "by": 5.0}` (실수로 너무 큰 값).
현재 값 2.0:

```
raw = 2.0 - 5.0 = -3.0
clamp(-3.0, rule_min=None, rule_max=None) = -3.0
clamp(-3.0, hard_min=1.0, hard_max=3.5) = 1.0   # hard cap 이 보호
new_value = 1.0
```

hard cap 이 룰 실수까지 막아주는 안전망 역할을 합니다.

---

## 5. fixture 테스트 hook 와 자동 rollback

`commit_overrides(preview, mode="commit", fixture_hook=callable)` 를 호출할 때 `fixture_hook` 인자에 함수를 넘기면, 모든 `setattr` 가 끝난 직후 그 함수를 호출합니다. **함수가** `False` **를 반환하거나 예외를 던지면**:

1. `setattr` 한 모든 항목을 stack 역순으로 원복
2. 해당 entry 들의 `applied` 를 `false` 로 마킹
3. `skipped_reason` 을 `"fixture_failed"` 로 기록
4. main.log 에 rollback 로그 한 줄 출력

권장 hook 예시 — `test_classifier` 회귀 테스트 1초 안에 돌리기:

```python
import subprocess, sys

def run_classifier_fixture():
    return subprocess.run(
        [sys.executable, "-m", "unittest", "test_classifier"],
        check=False,
        capture_output=True,
    ).returncode == 0

load_and_apply_overrides(
    date="2026-04-30",
    mode="commit",
    fixture_hook=run_classifier_fixture,
)
```

이 hook 이 통과해야만 변경이 유지됩니다. 분류기가 망가지면 자동 rollback.

> **주의** — `fixture_hook` 는 `apply_overrides.py` CLI 에서는 기본값 `None` 입니다. CLI 단독 사용 시 fixture 검증을 활성화하려면
> `load_and_apply_overrides()` 를 직접 호출하는 별도 스크립트를 작성해야 합니다 (가급적 main.py 부팅 흐름에 부착하는 것을 권장).

---

## 6. commit 후 이상 발생 시 수동 롤백

자동 rollback 이 작동하지 않은 상태에서 (예: fixture_hook 미설정 + 커밋 직후 운영자가 직접 이상을 발견) 수동으로 되돌리는 절차입니다.

### 6.1 가장 확실한 방법 — Python 프로세스 재시작

본 시스템은 *현재 실행 중인 Python 프로세스의 모듈 상수만* 변경합니다.  
따라서 main.py 또는 적용기를 실행한 프로세스를 종료하고 새로 시작하면 모듈 상수는 코드 기본값으로 돌아갑니다.

```
1. main.py 가 실행 중이면 정상 종료 (장중이면 포지션 청산 후)
2. 프로세스 종료 확인
3. 다시 시작 — 이때 부팅 시 commit 호출이 다시 일어나지 않게
   해당 호출 코드를 일시 주석 처리
```

### 6.2 audit 로그로 역방향 override 만들기

`applied_overrides_YYYYMMDD.json` 의 entry 를 읽어 반대 방향 override 를 수동으로 작성한 뒤 같은 적용기로 commit 합니다.

예: 어제 `decrement by 0.3` 이 적용됐다면, 오늘 `increment by 0.3` 의 override 를 수동 후보 JSON 에 작성:

```json
{
  "candidates": [
    {
      "rule_id": "manual_rollback",
      "title": "수동 롤백",
      "confidence": "high",
      "consistent_across_windows": true,
      "n_largest_window": 100,
      "allow_auto_apply": true,
      "auto_apply": false,
      "proposed_overrides": [
        {
          "target": "exit_strategy.EXIT_BE_R",
          "op": "increment",
          "by": 0.3,
          "max": 1.0,
          "reason": "수동 롤백: 어제 decrement 0.3 취소"
        }
      ]
    }
  ]
}
```

이 JSON 을 `data/reviews/rule_candidates_YYYYMMDD.json` 으로 저장한 뒤 `apply_overrides.py YYYY-MM-DD --commit`. audit JSON 에 mode=commit, applied=true 가 기록됩니다.

> **주의** — 이 방법은 hard cap 안에서만 동작합니다. 만약 어제 commit 으로 hard cap 까지 끌어내려진 상태라면 increment 도 hard cap 위로는 못 올라갑니다. 그 경우 6.1 (프로세스 재시작) 만이 답입니다.

### 6.3 코드에서 직접 기본값으로 복구

가장 확실한 마지막 수단. `entry_strategy.py` / `exit_strategy.py` / `review/classifier.py` 의 해당 상수를 직접 코드에서 원래 값으로 다시 지정한 뒤, Python 프로세스를 재시작.

---

## 7. 적용된 룰을 확인하는 방법

운영 중 어느 시점에서 *지금 어떤 룰이 적용되어 있는가* 를 확인하는 두 가지 방법이 있습니다.

### 7.1 audit 로그 누적 확인

`data/reviews/applied_overrides_*.json` 을 날짜별로 읽어서 `mode=commit` 이고 `applied=true` 인 entry 를 누적하면 *지금까지 commit 된 변경 이력*을 얻을 수 있습니다.

```python
import glob, json, os

results = []
for path in sorted(glob.glob("data/reviews/applied_overrides_*.json")):
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if payload.get("mode") != "commit":
        continue
    for entry in payload.get("entries", []):
        if entry.get("applied"):
            results.append({
                "date": entry["date"],
                "target": entry["target"],
                "old_value": entry["old_value"],
                "new_value": entry["new_value"],
            })
for r in results:
    print(r)
```

### 7.2 모듈 상수 직접 출력

가장 확실. main.py 와 같은 Python 프로세스 안에서:

```python
import entry_strategy, exit_strategy
from review import classifier

print("MAX_UPPER_WICK_RATIO    =", entry_strategy.MAX_UPPER_WICK_RATIO)
print("OVERHEATED_OPEN_RETURN  =", entry_strategy.OVERHEATED_OPEN_RETURN)
print("DANTE_FIRST_ENTRY_RATIO =", entry_strategy.DANTE_FIRST_ENTRY_RATIO)
print("EXIT_BE_R               =", exit_strategy.EXIT_BE_R)
print("EXIT_PARTIAL_R          =", exit_strategy.EXIT_PARTIAL_R)
print("EXIT_PARTIAL_RATIO      =", exit_strategy.EXIT_PARTIAL_RATIO)
print("CLASSIFIER_VERSION      =", classifier.CLASSIFIER_VERSION)
```

main.py 에 `--print-rules` 같은 옵션을 추가해도 좋습니다 (별도 PR).

---

## 8. data/main.log 에서 확인할 로그 예시

### 8.1 dry_run 정상 동작

```
2026-04-30 12:57:07 [INFO] [OVERRIDE][DRY_RUN] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=high applied=false
2026-04-30 12:57:07 [INFO] [OVERRIDE][SUMMARY] date=2026-04-30 mode=dry_run applied=0 skipped=0 total=1 source=data\reviews\rule_candidates_20260430.json
```

핵심 표지: `applied=false` (dry_run 은 항상 false). `skipped=0` 이지만 `applied=0` 인 이유는 *적용 가능했지만 dry_run 이라 setattr 안 함*.

### 8.2 commit 정상 적용

```
2026-04-30 13:10:21 [INFO] [OVERRIDE][COMMIT] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=high applied=true
2026-04-30 13:10:21 [INFO] [OVERRIDE][SUMMARY] date=2026-04-30 mode=commit applied=1 skipped=0 total=1 source=data\reviews\rule_candidates_20260430.json
```

핵심 표지: `[COMMIT]` 태그 + `applied=true`.

### 8.3 commit 차단 (low confidence)

```
2026-04-30 13:10:21 [INFO] [OVERRIDE][COMMIT] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=low applied=false skipped=confidence_below_high
```

핵심 표지: `applied=false skipped=...`. 사유가 `confidence_below_high` 면 운영 의도대로 차단된 정상 상태.

### 8.4 fixture 실패 후 rollback

```
2026-04-30 13:10:21 [INFO] [OVERRIDE][COMMIT] target=exit_strategy.EXIT_BE_R old=1.0 new=0.7 confidence=high applied=true
2026-04-30 13:10:22 [ERROR] [OVERRIDE] fixture_hook 예외 - rollback: <에러 메시지>
2026-04-30 13:10:22 [INFO] [OVERRIDE][SUMMARY] date=2026-04-30 mode=commit applied=0 skipped=1 total=1 source=...
```

핵심 표지: 처음에는 `applied=true` 로 보이지만, 다음 줄에 `rollback` 로그가 있으면 실제로는 원복된 상태. summary 의 `applied=0` 이 결정적 신호.

---

## 9. 장애 상황별 대응법

### 9.1 intraday CSV 가 없습니다

**증상**: `daily_review_*.md` 에 "1분봉 정밀: 0건 / fallback: N건" 으로 모두 fallback.

**원인**: `fetch_minute_bars.py` 가 실행되지 않았거나, 키움 로그인 실패.

**대응**:

1. 키움 OpenAPI 가 정상 로그인되는 환경인지 확인 (`check_daily_realized.py` 가 실행되는지로 검증)
2. `python fetch_minute_bars.py YYYY-MM-DD` 다시 실행
3. `data/intraday/YYYYMMDD/` 디렉토리에 CSV 가 종목 수만큼 생기는지 확인

**주의**: 1분봉 없이도 `analyze_today.py` 는 정상 동작합니다 (fallback).
다만 D 피처(VWAP, 진입봉 윗꼬리 등)가 비어 있어 `late_chase` 분류 정확도가 떨어집니다. 가능하면 1분봉 캐시를 채운 뒤 재실행 권장.

### 9.2 rule_candidates 파일이 없습니다

**증상**:

```
FileNotFoundError: 2026-04-30 기준 적용 후보 파일이 없습니다.
(검색 경로: data\reviews\rule_candidates_20260430.json,
            data\reviews\rule_overrides_2026-04-30.json)
```

**원인**: `review.rolling` 또는 `analyze_today.py` 가 그 날짜로 실행되지 않았음.

**대응**: 둘 다 재실행.

```
python analyze_today.py 2026-04-30
python -m review.rolling 2026-04-30
```

`apply_overrides.py` 는 두 파일 모두 안 보이면 죽지만, 둘 중 하나만 있어도 동작합니다 (`rule_candidates_*` 우선, 없으면 `rule_overrides_*` 를 평탄화해서 사용).

### 9.3 validate_override 가 실패합니다

**증상**: audit JSON 의 `validation_status: "failed"`, `skipped_reason: "validation_failed"`.

**원인 후보**:

- `target` 이 화이트리스트 외 (예: 오타)
- `op` 가 `set/increment/decrement/multiply` 외
- `set` 인데 `value` 가 없음 / `increment` 인데 `by` 가 없음
- `min > max`

**대응**: `reason` 컬럼에 구체적 에러 메시지가 같이 들어갑니다 (예: `error=target 화이트리스트에 없음: typo.SOMETHING`). 후보 JSON 을 수정.

> **주의** — 자동 생성된 `rule_candidates_*.json` 에서 이 에러가 나오면 rolling.py 에 버그가 있는 것입니다 (사람이 편집한 JSON 이 아닌데 잘못된 target 이 들어감). 즉시 코드 점검.

### 9.4 fixture 테스트가 실패합니다

**증상**: audit JSON 의 `applied: false`, `skipped_reason: "fixture_failed"`. main.log 에 `rollback` 로그.

**원인**:

- 분류기 회귀 테스트(`test_classifier`) 자체가 깨짐 (코드 변경 후 테스트 업데이트 누락)
- commit 한 룰이 분류 결과를 바꿔서 기존 fixture 가 깨짐 (기대된 동작 — 룰 변경의 영향이 너무 큼)

**대응**:

1. `python -m unittest test_classifier -v` 로 어떤 테스트가 깨졌는지 확인
2. **테스트가 합리적이라면** — 룰 변경이 너무 공격적인 것. 후보 JSON 에서 해당 룰의 `by` 값을 더 보수적으로 바꿔 다시 commit (자동으로 rollback 되었으므로 모듈 상수는 이미 원래 값).
3. **테스트가 잘못되었다면** — 테스트 코드를 먼저 고친 뒤 재실행.

### 9.5 commit 후 분류 결과가 기대와 다릅니다

**증상**: commit 후 다음 거래일의 `daily_review_*.md` 에서 라벨 분포가 이상함 (예: 모든 거래가 갑자기 late_chase 로 분류됨).

**대응**:

1. `applied_overrides_YYYYMMDD.json` 에서 어제 commit 된 항목 확인
2. 가장 의심되는 target 을 §6.2 (역방향 override) 또는 §6.3 (코드 직접
  수정) 로 되돌림
3. 테스트 fixture 를 추가해 같은 실수가 다시 안 일어나게 함

이상 발견 후 *즉시* 자동매매를 중단하고 위 절차를 진행하는 것을 권장합니다.
다음 거래일까지 기다릴 필요 없습니다.

### 9.6 main.py 실행 시 override 가 적용되지 않습니다

**증상**: commit 까지 정상 완료된 것 같은데 main.py 가 새로 부팅하면 룰이 원래 값으로 돌아가 있음.

**원인**: 본 PR 의 코드는 main.py 부팅 시 자동 commit 호출을 *일부러* 넣지 않았습니다. commit 으로 변경된 모듈 상수는 *commit 을 실행한 Python 프로세스 안에서만* 유효하며, main.py 의 새 프로세스에서는 코드 기본값으로 시작됩니다.

**해결 두 가지**:

**(A)** main.py 부팅에 commit 호출 코드를 추가. 다음과 같은 형태:

```python
from datetime import datetime
from review.overrides import load_and_apply_overrides

def _apply_overnight_rules():
    target_date = datetime.now().strftime("%Y-%m-%d")
    try:
        load_and_apply_overrides(
            date=target_date, mode="commit",
            fixture_hook=lambda: subprocess.run(
                [sys.executable, "-m", "unittest", "test_classifier"],
                check=False,
            ).returncode == 0,
        )
    except FileNotFoundError:
        logger.info("[OVERRIDE] 적용할 후보 JSON 없음 - skip")

_apply_overnight_rules()
```

> **주의** — 이 방식이라면 매번 main.py 부팅 시 자동 commit 이 일어납니다.
> *커밋 자체* 가 아니라 *후보 JSON 의 allow_auto_apply 가 true 인 항목만 적용*되므로 안전한 흐름은 유지되지만, allow_auto_apply 가 사람이 매일 검토 후 편집하는 흐름이라는 점을 잊지 마세요.

**(B)** 코드에서 기본값을 직접 변경. 가장 확실하지만 git diff 가 늘어남.
중요한 변경(예: hard cap 자체 조정) 일 때만 권장.

### 9.7 portfolio_state.json 이 손상되었습니다

**증상**: main.py 부팅 시 `data/main.log` 에 다음 로그.

```
[ERROR] portfolio_state 손상 -- data/portfolio_state.json.corrupt 로 보존 후 빈 상태 시작: ...
```

**원인**: 디스크 가득참 / 비정상 종료 시 atomic write 가 깨진 경우 / 손으로 편집했다가 JSON 형식이 어긋난 경우.

**대응 자동 동작**:

1. 손상된 파일은 `data/portfolio_state.json.corrupt` 로 자동 보존됨 (분석용)
2. 빈 상태로 부팅 진행 — 거래 자체는 막히지 않음
3. 잔고 TR 응답으로 휘발성 필드(`quantity` / `entry_price`) 만 다시 채워짐

**사람이 해야 할 일**:

1. `data/portfolio_state.json.corrupt` 가 있다면 이전 거래일 데이터인지 확인
2. 같은 거래일이라면 — 보유 종목의 `entry_stage` / `stop_price` / `partial_taken` / `breakout_grade` 가 default 로 리셋되었음을 인지하고, 필요하면 다음 절차로 수동 복원
3. 다른 거래일이라면 — 그냥 백업 폴더로 옮기고 무시

**수동 복원 (같은 거래일에 의미 있음)**:

`.corrupt` 파일에서 보유 중인 종목 entry 만 골라 새 `portfolio_state.json` 으로 작성. 형식은 [review_system_overview.md](review_system_overview.md) §5.0.3 참조. 또는 main.py 를 종료 → 키움 영웅문에서 **수동 매도 후 다시 시작** 이 가장 안전.

> **주의** — 손상된 portfolio_state 와 *전략 사이드의 정합성 깨짐* 을 그대로 두면, BE 스탑이 풀려 -1R 보호가 사라지거나 1차에 25% 만 산 상태로 멈출 수 있습니다. 의심스러우면 즉시 자동매매를 중단하고 영웅문에서 수동으로 종목 정리 후 재시작 권장.

### 9.8 trading_day 가 어제로 남아 있습니다

**증상**: main.py 가 자정 이후에도 종료되지 않고 새 거래일에 처음 매수 시점에서 어제 매수 카운터가 남아 있음.

**원인**: `reset_daily_state` 가 trading_day 비교로만 일별 초기화를 트리거하는데, 자정을 넘긴 *프로세스 자체* 의 trading_day 갱신이 condition 큐 처리 후에야 일어남. 정상 동작이지만 첫 거래 직전 1~2초 race window 가 있을 수 있음.

**대응**: 자정~장 시작 (09:05) 사이에 main.py 를 한 번 재시작하는 것이 가장 깔끔. 그러면 부팅 시점에 `load_portfolio_state` 가 어제 trading_day 를 보고 자동으로 어제 portfolio 를 폐기 → 클린 상태로 새 거래일 시작.

---

## 10. 안전성 점검 체크리스트

분기에 한 번 정도 다음을 확인하면 시스템이 안전 상태인지 검증할 수 있습니다.

**코드 감사**

- `review/overrides.py` 본문에 `eval(`, `exec(`, `importlib.import_module`, `__import__(` 가 zero match (`StaticImportPolicyTest` 가 매번 검증)
- `TARGET_WHITELIST` 에 새 키가 추가됐다면 `_TARGET_MODULES` 매핑 + 파일 상단 import 도 동시 추가됐는지
- hard cap 값이 합리적 범위인지 (예: `EXIT_BE_R` 의 max 가 1.5 를 넘지 않는지)

**테스트 회귀**

- `python -m unittest test_overrides_apply` 24건 통과
- `python -m unittest test_overrides` 18건 통과
- `python -m unittest test_classifier` 18건 통과
- `python -m unittest test_intraday test_rolling` 모두 통과
- `python -m unittest test_portfolio_persistence test_save_portfolio_skip` (장중 크래시 복원) 통과
- `python -m unittest test_shadow_training test_market_context test_fetch_market_context` (표본 수집 인프라) 통과

**audit 누적**

- `data/reviews/applied_overrides_*.json` 의 모든 commit entry 가 합리적인지 (값 변동폭, 사유)
- 같은 target 에 commit 이 N 일 연속 있으면 누적 영향 검토 (예: 매일 decrement 0.3 → 1주일이면 -2.1)

**운영 가드**

- main.py 부팅 시 자동 commit 코드가 *의도된 형태*로 들어가 있는지
- fixture_hook 가 `test_classifier` 를 1초 안에 돌리는 형태인지
- `allow_auto_apply` 를 *기본 false* 로 두는 정책이 깨지지 않았는지
- `data/portfolio_state.json` 가 매일 새 trading_day 로 갱신되는지 (오래된 trading_day 가 며칠째 같으면 main.py 가 자정 이후 한 번도 재시작되지 않음을 의미)

이 체크리스트 모든 항목을 통과한다면 시스템이 안전 상태에 있습니다. 한 항목이라도 의심되면 [review_user_guide.md](review_user_guide.md) §8 의
"commit 하면 안 되는 상황" 도 같이 점검하세요.

---

## 11. 장중 크래시 복원 (portfolio_state.json)

main.py 가 장중에 죽고 재시작되어도 전략 상태가 보존되도록, 매 체결/매도 큐 변경/매도 평가 사이클마다 `data/portfolio_state.json` 에 atomic write 합니다.

### 11.1 보호되는 필드

잔고 TR 응답으로 회복 *불가능* 한 8개 전략 필드:


| 필드 | 잃으면 일어나는 일 |
| --- | -------------- |
| `entry_stage` | 1차에 25%만 사놓고 2차 본진입이 영원히 발사 안 됨 |
| `planned_quantity` | 2차 매수 수량 계산이 깨짐 |
| `stop_price` | BE 스탑이 풀려 -1R 보호가 사라짐 (가장 위험) |
| `partial_taken` | +2R 도달 시 또 부분익절 시도 (이중 체결) |
| `breakout_high` | 추적 고점이 0부터 다시 → 눌림 판정 오작동 |
| `breakout_grade` | A/B 등급 식별자 손실 → 분할매수 분기 오작동 |
| `pullback_window_deadline` | 2차 본진입 윈도우 영원히 만료 안 됨 → 1주 락 |
| `pending_sell_intent` | 큐에 있던 매도 의도 사라짐 → 매도 재시도 중단 |


### 11.2 부팅 시 복원 동작

```
1. load_best()                # best.dat (target_price 등)
2. load_portfolio_state()     # data/portfolio_state.json 읽어서 self.portfolio 복원
   ├─ saved_trading_day == today → portfolio + sell intent + bought_today 카운터 복원
   └─ saved_trading_day != today → 어제 상태 폐기, 잔고 TR 만으로 다시 시작
3. reset_daily_state()        # trading_day 일치 시 no-op (위에서 미리 세팅)
4. update_account_status()    # 잔고/미체결 TR 호출 → quantity / pending_buy/sell 만 덮어씀
                              #   _sync_position_from_dicts 가 휘발성 필드만 갱신
                              #   전략 필드(entry_stage 등) 는 디스크 본 그대로 보존
```

**핵심 — 잔고 TR 호출이 *나중* 에 일어나서 휘발성 필드만 덮어쓰고, 디스크 본의 전략 필드는 그대로 살아남습니다.**

### 11.3 저장 트리거

- `_on_receive_chejan` 끝 — 모든 매수/매도 체결 결과 동기화
- `place_buy_order` 발주 직후 — `planned_quantity` / `pullback_window_deadline` 보존
- `queue_sell_intent` — 큐에 들어갈 때마다
- `check_open_positions` 끝 — BE 스탑 이동 / partial_taken / breakout_high 갱신 동기화 (1.5초 주기)
- `_discard_position` — 청산 직후 stale 상태 제거

보유 0 상태에서는 1.5초 주기 호출에서도 IO 를 스킵해 무의미한 fsync 누적을 방지합니다.

### 11.4 손상된 JSON 동작

`json.JSONDecodeError` / `OSError` 발생 시:

1. 원본을 `data/portfolio_state.json.corrupt` 로 보존 (분석용)
2. main.log 에 ERROR 한 줄 — `portfolio_state 손상 -- ... 빈 상태 시작`
3. 빈 PortfolioState 로 부팅 진행 — *부팅 자체는 차단되지 않음*
4. 잔고 TR 응답이 휘발성 필드를 채움 → 보유 종목은 수량/평단까지 복원
5. **전략 필드(`entry_stage` 등) 는 default 로 리셋** — 운영자가 인지하고 필요 시 매도 후 재시작

손으로 편집하다 망가뜨려도 자동 거래는 멈추지 않지만, 그 시점부터 전략 보호가 약해진다는 점을 인지하세요.

### 11.5 type-cast 강건성

JSON 의 잘못된 타입(예: `"entry_stage": "two"`) 도 `from_persisted_dict` 가 캐스트 실패 시 *해당 필드만* default 로 두고 진행합니다. 다른 필드 복원은 영향받지 않습니다 — 손상 한 곳이 전체 복원을 막지 않게.

```python
# 캐스트 카테고리 (portfolio.py 상단)
_PERSISTED_INT_FIELDS   = {"target_price", "highest_price",
                           "entry_stage", "planned_quantity",
                           "stop_price", "breakout_high"}
_PERSISTED_FLOAT_FIELDS = {"target_return", "entry_time",
                           "entry1_time", "entry2_time",
                           "r_unit_pct", "pullback_window_deadline"}
_PERSISTED_BOOL_FIELDS  = {"bought_today", "partial_taken"}
_PERSISTED_STR_FIELDS   = {"name", "breakout_grade"}
```

캐스트 실패 시 `data/main.log` 에 `WARNING from_persisted_dict: <code>.<field> 값 무시(...)` 한 줄이 남습니다. 이 경고가 매일 보이면 어디선가 잘못된 타입을 디스크에 쓰고 있다는 신호 — 즉시 코드 점검.