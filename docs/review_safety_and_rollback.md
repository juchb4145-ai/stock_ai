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

**audit 누적**

- `data/reviews/applied_overrides_*.json` 의 모든 commit entry 가 합리적인지 (값 변동폭, 사유)
- 같은 target 에 commit 이 N 일 연속 있으면 누적 영향 검토 (예: 매일 decrement 0.3 → 1주일이면 -2.1)

**운영 가드**

- main.py 부팅 시 자동 commit 코드가 *의도된 형태*로 들어가 있는지
- fixture_hook 가 `test_classifier` 를 1초 안에 돌리는 형태인지
- `allow_auto_apply` 를 *기본 false* 로 두는 정책이 깨지지 않았는지

이 체크리스트 모든 항목을 통과한다면 시스템이 안전 상태에 있습니다. 한 항목이라도 의심되면 [review_user_guide.md](review_user_guide.md) §8 의
"commit 하면 안 되는 상황" 도 같이 점검하세요.