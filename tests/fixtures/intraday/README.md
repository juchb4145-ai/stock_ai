# review/intraday 테스트 fixture

`fetch_minute_bars.py` 가 떨어뜨리는 형식과 동일한 1분봉 CSV.

## 디렉토리 구조

```
tests/fixtures/intraday/
└── YYYYMMDD/
    └── <종목코드>.csv      # 컬럼: datetime,open,high,low,close,volume
```

## 정적 fixture

- `20260430/050890.csv` (쏠리드, 09:00~09:14 15분간)

진입 시각 09:06:50 / 진입가 16,761 기준으로 의도된 메트릭:

| 메트릭                         | 기대값 |
|--------------------------------|--------|
| `return_1m`                    | (16850 - 16761) / 16761 ≈ +0.531% |
| `return_3m`                    | (17050 - 16761) / 16761 ≈ +1.724% |
| `max_profit_3m`                | (17080 - 16761) / 16761 ≈ +1.903% |
| `max_drawdown_3m`              | (16690 - 16761) / 16761 ≈ -0.424% |
| `entry_after_peak_sec`         | 50 (09:06 분봉 = session_high)    |
| `entry_near_session_high`      | 1 (16761 / 16820 ≈ 0.9965 ≥ 0.99) |
| `prior_3m_return_pct`          | (16761 - 16600) / 16600 ≈ +0.970% |
| `breakout_candle_body_pct`     | |16780 - 16700| / (16820 - 16690) = 0.6154 |
| `upper_wick_pct`               | (16820 - 16780) / (16820 - 16690) = 0.3077 |

다른 종목 fixture 가 없으면 `review.intraday.attach_intraday_metrics` 가 자동으로
fallback("fallback_5m_approx") 으로 떨어진다 — fallback 동작도 같은 fixture 셋트로
테스트 가능.
