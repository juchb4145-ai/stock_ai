# review/rolling 테스트 fixture

`review.rolling` 의 단위 테스트와 사람용 sanity check 에 쓰는 정적 데이터.

## 일자별 구성 (2026-04-21 ~ 2026-04-25, 영업일 5일)

각 일자마다 5건씩, 동일한 패턴을 반복:

| # | entry_class      | exit_class  | r_multiple | mfe_r | mae_r | be_violation |
|---|------------------|-------------|------------|-------|-------|--------------|
| 1 | breakout_chase   | bad_stop    | -0.5       | +1.5  | -1.0  | 1            |
| 2 | breakout_chase   | bad_stop    | -0.7       | +2.0  | -1.0  | 1            |
| 3 | breakout_chase   | good_stop   | -1.0       | +0.3  | -1.0  | 0            |
| 4 | breakout_chase   | clean_exit  | +1.0       | +1.5  | -0.3  | 0            |
| 5 | first_pullback   | late_take   | +1.0       | +3.0  | -0.5  | 0            |

## 의도된 룰 후보 (5/10/20d 모두 동일 fixture 만 있는 경우)

총 거래 25건 / 패배 15건 / 승리 10건.

- `break_even_cut`        : be_violation 10건 / loser 15건 = 66.7% → **trigger**
- `take_profit_faster`    : late_take 5건 / winner 10건 = 50.0% → **trigger**
- `block_fake_breakout`   : fake_breakout 0건 → not triggered
- `wait_for_pullback`     : A 평균 R 음수, B 평균 R 양수, 차이 ≥ 0.5R → **trigger**
- `apply_trailing`        : fast_take 0건 → not triggered

5/10/20d 모두 같은 fixture(=동일 5일치) 라 `consistent_across_windows=True`.
윈도우 전체 거래수 25 → confidence 후보는 medium (≥20, <40).

## 파일 목록

- `trade_review_2026-04-21.csv` ~ `trade_review_2026-04-25.csv` — 거래 단위
- `rule_overrides_2026-04-24.json`, `rule_overrides_2026-04-25.json` — 보조 evidence
