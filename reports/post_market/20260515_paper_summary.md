# 2026-05-15 Post-Market Condition Review (paper)

## Daily Summary
- total detected: 770
- traded: 0
- non-traded: 770
- TRADED_WIN: 0
- TRADED_LOSS: 0
- MISSED_OPPORTUNITY: 192
- GOOD_REJECT: 371
- DATA_QUALITY_BLOCK: 0
- TIME_POLICY_BLOCK: 184
- ORDER_GUARD_BLOCK: 0
- win rate: missing
- realized pnl: missing
- mode: paper
- generated_at: 2026-05-15 16:20:55

## Daily Buy Gate Funnel
| metric | value |
|---|---:|
| raw_detected | 770 |
| unique_detected_symbols | 146 |
| registered_candidates | 116 |
| analysis_only_candidates | 204 |
| momentum_evaluated | 577 |
| final_decision_emitted | 577 |
| baseline_buy_allowed | 0 |
| relaxed_pullback_signal_rows | 260 |
| order_attempted | 0 |
| order_filled | 0 |
| policy_row_count | 770 |

## Reason Counts by Unique Symbol
| reason | row_count | unique_symbol_count | avg_mfe_pct | missed_count |
|---|---:|---:|---:|---:|
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 284 | 64 | +3.49% | 70 |
| TIME_POLICY_ANALYSIS_ONLY | 184 | 38 | +4.63% | 9 |
| FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 117 | 18 | +5.63% | 72 |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 45 | 9 | +3.46% | 8 |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 30 | 6 | +0.44% | 0 |
| FINAL_MOMENTUM_WAIT_RECLAIM_VWAP | 26 | 1 | +7.38% | 26 |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 25 | 5 | +3.01% | 6 |
| FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | 23 | 6 | +11.92% | 23 |
| FINAL_MOMENTUM_WAIT_LEADER_SCORE | 19 | 2 | +0.95% | 1 |
| missing | 9 | 1 | +8.97% | 9 |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_TOP | 4 | 2 | +0.83% | 0 |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 4 | 1 | +1.19% | 0 |

## Trade Results
- no traded candidates

## Exit Type Performance
- no traded candidates

## Non-Traded Review
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 006800 | 미래에셋증권 | 2026-05-15 09:00:07 | 75600 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE upper wick pressure 36% > 30% | FINAL_MOMENTUM_BLOCK_UPPER_WICK | +2.38% | -10.58% | GOOD_REJECT |
| 006800 | 미래에셋증권 | 2026-05-15 09:00:07 | 75600 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE upper wick pressure 36% > 30% | FINAL_MOMENTUM_BLOCK_UPPER_WICK | +2.38% | -10.58% | GOOD_REJECT |
| 027360 | 아주IB투자 | 2026-05-15 09:00:08 | 16610 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 69.1 < 70.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +2.35% | -16.32% | GOOD_REJECT |
| 027360 | 아주IB투자 | 2026-05-15 09:00:08 | 16610 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 69.1 < 70.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +2.35% | -16.32% | GOOD_REJECT |
| 319400 | 현대무벡스 | 2026-05-15 09:00:10 | 44050 | WAIT | Momentum decision is not BUY: WAIT_RECLAIM_VWAP below VWAP but flow is strong... | FINAL_MOMENTUM_WAIT_RECLAIM_VWAP | +7.38% | -9.99% | MISSED_OPPORTUNITY |
| 100790 | 미래에셋벤처투자 | 2026-05-15 09:00:11 | 61800 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 86.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +2.59% | -14.40% | GOOD_REJECT |
| 100790 | 미래에셋벤처투자 | 2026-05-15 09:00:11 | 61800 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 86.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +2.59% | -14.40% | GOOD_REJECT |
| 018880 | 한온시스템 | 2026-05-15 09:00:22 | 5130 | missing | missing | missing | +8.97% | -3.51% | MISSED_OPPORTUNITY |
| 034220 | LG디스플레이 | 2026-05-15 09:00:25 | 15980 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.64 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.13% | -14.08% | MISSED_OPPORTUNITY |
| 034220 | LG디스플레이 | 2026-05-15 09:00:25 | 15980 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.64 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.13% | -14.08% | MISSED_OPPORTUNITY |
| 090360 | 로보스타 | 2026-05-15 09:00:35 | 89900 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 55.6 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +8.90% | -5.34% | MISSED_OPPORTUNITY |
| 036930 | 주성엔지니어링 | 2026-05-15 09:00:35 | 182100 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 60.7 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.77% | -25.26% | GOOD_REJECT |
| 036930 | 주성엔지니어링 | 2026-05-15 09:00:36 | 182100 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 60.7 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.77% | -25.26% | GOOD_REJECT |
| 332570 | PS일렉트로닉스 | 2026-05-15 09:00:36 | 13720 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 7.43% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | BAD_BLOCK_CHASE |
| 332570 | PS일렉트로닉스 | 2026-05-15 09:00:36 | 13720 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 7.43% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | BAD_BLOCK_CHASE |
| 001200 | 유진투자증권 | 2026-05-15 09:00:36 | 6600 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 9.62%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +4.85% | -12.58% | GOOD_REJECT |
| 001740 | SK네트웍스 | 2026-05-15 09:00:37 | 8390 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 57.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +18.00% | -11.80% | MISSED_OPPORTUNITY |
| 018880 | 한온시스템 | 2026-05-15 09:00:37 | 5130 | missing | missing | missing | +8.97% | -3.51% | MISSED_OPPORTUNITY |
| 332570 | PS일렉트로닉스 | 2026-05-15 09:00:38 | 13720 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 7.43% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | BAD_BLOCK_CHASE |
| 018880 | 한온시스템 | 2026-05-15 09:00:38 | 5130 | missing | missing | missing | +8.97% | -3.51% | MISSED_OPPORTUNITY |
| 332570 | PS일렉트로닉스 | 2026-05-15 09:00:38 | 13720 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 7.43% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | BAD_BLOCK_CHASE |
| 090710 | 휴림로봇 | 2026-05-15 09:00:43 | 13000 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 6.38% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +13.00% | -2.85% | BAD_BLOCK_CHASE |
| 018880 | 한온시스템 | 2026-05-15 09:00:44 | 5130 | missing | missing | missing | +8.97% | -3.51% | MISSED_OPPORTUNITY |
| 234340 | 헥토파이낸셜 | 2026-05-15 09:00:45 | 38550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 54.0 < 70.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +0.26% | -20.10% | GOOD_REJECT |
| 234340 | 헥토파이낸셜 | 2026-05-15 09:00:45 | 34750 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 54.0 < 70.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +11.22% | -11.37% | MISSED_OPPORTUNITY |
| 196170 | 알테오젠 | 2026-05-15 09:00:46 | 401500 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 84.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.87% | -10.09% | GOOD_REJECT |
| 018880 | 한온시스템 | 2026-05-15 09:00:46 | 5130 | missing | missing | missing | +8.97% | -3.51% | MISSED_OPPORTUNITY |
| 196170 | 알테오젠 | 2026-05-15 09:00:46 | 401500 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 84.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.87% | -10.09% | GOOD_REJECT |
| 018880 | 한온시스템 | 2026-05-15 09:00:48 | 5130 | missing | missing | missing | +8.97% | -3.51% | MISSED_OPPORTUNITY |
| 001510 | SK증권 | 2026-05-15 09:00:53 | 4670 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 55.9 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +1.71% | -13.06% | GOOD_REJECT |

## Missed Opportunities
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 454910 | 두산로보틱스 | 2026-05-15 09:01:16 | 111800 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 11.54% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +24.15% | -1.52% | BAD_BLOCK_CHASE |
| 454910 | 두산로보틱스 | 2026-05-15 09:06:03 | 111800 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 11.54% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +24.15% | +2.24% | BAD_BLOCK_CHASE |
| 037460 | 삼지전자 | 2026-05-15 11:27:47 | 40800 | missing | Analysis-only condition capture by TimePolicy ALLOW_CANDIDATE_CAPTURE | TIME_POLICY_ANALYSIS_ONLY | +21.69% | -6.37% | TIME_POLICY_BLOCK |
| 396300 | 세아메카닉스 | 2026-05-15 09:26:57 | 6080 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 53.8 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +20.72% | -3.45% | MISSED_OPPORTUNITY |
| 033240 | 자화전자 | 2026-05-15 09:20:36 | 50300 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 12.13% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +19.28% | -0.40% | BAD_BLOCK_CHASE |
| 001740 | SK네트웍스 | 2026-05-15 09:00:37 | 8390 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 57.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +18.00% | -11.80% | MISSED_OPPORTUNITY |
| 001740 | SK네트웍스 | 2026-05-15 09:01:06 | 8390 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 57.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +18.00% | -11.80% | MISSED_OPPORTUNITY |
| 001740 | SK네트웍스 | 2026-05-15 09:03:26 | 8390 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 57.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +18.00% | -11.80% | MISSED_OPPORTUNITY |
| 001740 | SK네트웍스 | 2026-05-15 09:03:45 | 8390 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 57.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +18.00% | -11.80% | MISSED_OPPORTUNITY |
| 001740 | SK네트웍스 | 2026-05-15 09:03:49 | 8390 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 57.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +18.00% | -11.80% | MISSED_OPPORTUNITY |
| 138360 | 앤로보틱스 | 2026-05-15 09:02:12 | 4235 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 58.0 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +17.59% | -10.98% | MISSED_OPPORTUNITY |
| 138360 | 앤로보틱스 | 2026-05-15 09:02:12 | 4235 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 58.0 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +17.59% | -10.98% | MISSED_OPPORTUNITY |
| 138360 | 앤로보틱스 | 2026-05-15 09:06:37 | 4235 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 58.0 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +17.59% | -10.98% | MISSED_OPPORTUNITY |
| 138360 | 앤로보틱스 | 2026-05-15 09:07:05 | 4235 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 58.0 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +17.59% | -10.98% | MISSED_OPPORTUNITY |
| 215100 | 로보로보 | 2026-05-15 09:05:52 | 7560 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 58.8 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +13.76% | -7.14% | MISSED_OPPORTUNITY |

## Good Rejects
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 006800 | 미래에셋증권 | 2026-05-15 09:00:07 | 75600 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE upper wick pressure 36% > 30% | FINAL_MOMENTUM_BLOCK_UPPER_WICK | +2.38% | -10.58% | GOOD_REJECT |
| 006800 | 미래에셋증권 | 2026-05-15 09:00:07 | 75600 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE upper wick pressure 36% > 30% | FINAL_MOMENTUM_BLOCK_UPPER_WICK | +2.38% | -10.58% | GOOD_REJECT |
| 027360 | 아주IB투자 | 2026-05-15 09:00:08 | 16610 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 69.1 < 70.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +2.35% | -16.32% | GOOD_REJECT |
| 027360 | 아주IB투자 | 2026-05-15 09:00:08 | 16610 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 69.1 < 70.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +2.35% | -16.32% | GOOD_REJECT |
| 100790 | 미래에셋벤처투자 | 2026-05-15 09:00:11 | 61800 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 86.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +2.59% | -14.40% | GOOD_REJECT |
| 100790 | 미래에셋벤처투자 | 2026-05-15 09:00:11 | 61800 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 86.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +2.59% | -14.40% | GOOD_REJECT |
| 036930 | 주성엔지니어링 | 2026-05-15 09:00:35 | 182100 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 60.7 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.77% | -25.26% | GOOD_REJECT |
| 036930 | 주성엔지니어링 | 2026-05-15 09:00:36 | 182100 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 60.7 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.77% | -25.26% | GOOD_REJECT |
| 001200 | 유진투자증권 | 2026-05-15 09:00:36 | 6600 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 9.62%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +4.85% | -12.58% | GOOD_REJECT |
| 234340 | 헥토파이낸셜 | 2026-05-15 09:00:45 | 38550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 54.0 < 70.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +0.26% | -20.10% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-15 09:00:46 | 401500 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 84.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.87% | -10.09% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-15 09:00:46 | 401500 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 84.8 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +0.87% | -10.09% | GOOD_REJECT |
| 001510 | SK증권 | 2026-05-15 09:00:53 | 4670 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 55.9 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +1.71% | -13.06% | GOOD_REJECT |
| 096770 | SK이노베이션 | 2026-05-15 09:01:20 | 132400 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +3.02% | -7.70% | GOOD_REJECT |
| 096770 | SK이노베이션 | 2026-05-15 09:01:20 | 132400 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +3.02% | -7.70% | GOOD_REJECT |

## Block Chase Review
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 454910 | 두산로보틱스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +24.15% | -1.52% | +13.95% |
| 454910 | 두산로보틱스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +24.15% | +2.24% | +13.95% |
| 033240 | 자화전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +19.28% | -0.40% | +10.74% |
| 090710 | 휴림로봇 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +13.00% | -2.85% | +0.92% |
| 090710 | 휴림로봇 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +13.00% | -2.85% | +0.92% |
| 090710 | 휴림로봇 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +13.00% | -2.85% | +0.92% |
| 090710 | 휴림로봇 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +13.00% | -2.85% | +0.92% |
| 090710 | 휴림로봇 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +13.00% | -2.85% | +0.92% |
| 090710 | 휴림로봇 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +13.00% | -2.85% | +0.92% |
| 018260 | 삼성에스디에스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +11.87% | -2.11% | -0.26% |
| 018260 | 삼성에스디에스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +11.87% | -2.11% | -0.26% |
| 018260 | 삼성에스디에스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +11.87% | -2.11% | -0.26% |
| 018260 | 삼성에스디에스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +11.87% | -2.11% | -0.26% |
| 018260 | 삼성에스디에스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +11.87% | -2.11% | -0.26% |
| 018260 | 삼성에스디에스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +11.87% | -2.11% | -0.26% |
| 332570 | PS일렉트로닉스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | -10.50% |
| 332570 | PS일렉트로닉스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | -10.50% |
| 332570 | PS일렉트로닉스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | -10.50% |
| 332570 | PS일렉트로닉스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | -10.50% |
| 332570 | PS일렉트로닉스 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +7.73% | -13.63% | -10.50% |

## Data Quality Blocks
| symbol | name | category | reason_code | MFE | MAE | close return | data_quality |
|---|---|---|---|---:|---:|---:|---|
| 037460 | 삼지전자 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +21.69% | -6.37% | +21.69% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +12.54% | -6.36% | -3.80% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 260970 | 에스앤디 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +10.93% | -4.57% | +9.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 260970 | 에스앤디 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +10.60% | -0.33% | +9.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 005950 | 이수화학 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +9.40% | -11.50% | -8.67% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 077500 | 유니퀘스트 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +8.97% | -7.54% | -5.98% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 018880 | 한온시스템 | MISSED_OPPORTUNITY | missing | +8.97% | -3.51% | -1.56% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 214320 | 이노션 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.60% | -3.33% | -0.95% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 003350 | 한국화장품제조 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +6.31% | -1.94% | -0.10% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 003350 | 한국화장품제조 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +6.31% | -1.94% | -0.10% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |

| data_quality | count | avg_mfe_pct | n_mfe | missing_mfe |
|---|---:|---:|---:|---:|
| MISSING_DECISION_TRACE | 193 | +5.45% | 48 | 145 |
| MISSING_SPREAD_RATE | 193 | +5.45% | 48 | 145 |
| MISSING_TRADE_STRENGTH | 193 | +5.45% | 48 | 145 |
| partial_data | 193 | +5.45% | 48 | 145 |
| MISSING_CAPTURE_PRICE | 145 | missing | 0 | 145 |
| MISSING_MFE_MAE | 145 | missing | 0 | 145 |
| MISSING_VOLUME_RATIO | 7 | +7.71% | 7 | 0 |
| MISSING_UPPER_WICK_RATIO | 3 | +0.00% | 3 | 0 |

## Missing Decision Trace Detail
| symbol | name | detected_at | candidate_id | role | reason_code | time_policy | source | stage | data_quality |
|---|---|---|---|---|---|---|---|---|---|
| 018880 | 한온시스템 | 2026-05-15 09:00:22 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | 2026-05-15 09:00:37 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | 2026-05-15 09:00:38 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | 2026-05-15 09:00:44 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | 2026-05-15 09:00:46 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | 2026-05-15 09:00:48 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 066570 | LG전자 | 2026-05-15 09:02:19 | 5c88901a66064072940998b935b4144b | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 018880 | 한온시스템 | 2026-05-15 09:04:30 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 018880 | 한온시스템 | 2026-05-15 09:04:31 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 018880 | 한온시스템 | 2026-05-15 09:06:23 | e77b43cd724e49609fc497e8e8064b47 | trading | missing | ALLOW_CANDIDATE_CAPTURE | condition_detected | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 242040 | 나무기술 | 2026-05-15 10:34:10 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 242040 | 나무기술 | 2026-05-15 10:34:11 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 242040 | 나무기술 | 2026-05-15 10:34:15 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 242040 | 나무기술 | 2026-05-15 10:34:20 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 443060 | HD현대마린솔루션 | 2026-05-15 10:34:56 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 081660 | 미스토홀딩스 | 2026-05-15 10:37:57 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 052900 | KX하이텍 | 2026-05-15 10:39:40 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 052900 | KX하이텍 | 2026-05-15 10:39:41 | 78a31b485f82407bb2aac61102741fcc | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 052900 | KX하이텍 | 2026-05-15 10:44:21 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | missing | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 052900 | KX하이텍 | 2026-05-15 10:44:21 | 78a31b485f82407bb2aac61102741fcc | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 003350 | 한국화장품제조 | 2026-05-15 10:48:27 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 052900 | KX하이텍 | 2026-05-15 10:49:11 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | missing | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 052900 | KX하이텍 | 2026-05-15 10:49:11 | 78a31b485f82407bb2aac61102741fcc | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 052900 | KX하이텍 | 2026-05-15 10:52:29 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | missing | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 052900 | KX하이텍 | 2026-05-15 10:52:29 | 78a31b485f82407bb2aac61102741fcc | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 187870 | 디바이스 | 2026-05-15 10:52:37 | 29e2c4f20fd44ac9a294edec9edadb5e | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | missing | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 187870 | 디바이스 | 2026-05-15 10:52:37 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 187870 | 디바이스 | 2026-05-15 10:55:10 | 29e2c4f20fd44ac9a294edec9edadb5e | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | missing | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 187870 | 디바이스 | 2026-05-15 10:55:10 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 126600 | BGF에코머티리얼즈 | 2026-05-15 10:56:20 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:01:39 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 024060 | 흥구석유 | 2026-05-15 11:02:08 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003350 | 한국화장품제조 | 2026-05-15 11:02:37 | f9bb1b15b84c4ac28a5f840c241e3fcb | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | missing | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 003350 | 한국화장품제조 | 2026-05-15 11:02:37 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:03:17 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:03:19 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:03:34 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:04:10 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:04:12 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:04:13 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-15 11:04:22 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 007340 | DN오토모티브 | 2026-05-15 11:04:37 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 007340 | DN오토모티브 | 2026-05-15 11:04:47 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003350 | 한국화장품제조 | 2026-05-15 11:05:07 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | missing | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003350 | 한국화장품제조 | 2026-05-15 11:05:07 | f9bb1b15b84c4ac28a5f840c241e3fcb | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 003280 | 흥아해운 | 2026-05-15 11:06:06 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 024060 | 흥구석유 | 2026-05-15 11:09:26 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 024060 | 흥구석유 | 2026-05-15 11:09:28 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 024060 | 흥구석유 | 2026-05-15 11:09:31 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 024060 | 흥구석유 | 2026-05-15 11:13:15 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |

## Data Quality High MFE
- none

## Time Policy Blocks
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 037460 | 삼지전자 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +21.69% | -6.37% | +21.69% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +12.54% | -6.36% | -3.80% |
| 260970 | 에스앤디 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +10.93% | -4.57% | +9.30% |
| 260970 | 에스앤디 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +10.60% | -0.33% | +9.30% |
| 005950 | 이수화학 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +9.40% | -11.50% | -8.67% |
| 077500 | 유니퀘스트 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +8.97% | -7.54% | -5.98% |
| 214320 | 이노션 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.60% | -3.33% | -0.95% |
| 003350 | 한국화장품제조 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +6.31% | -1.94% | -0.10% |
| 003350 | 한국화장품제조 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +6.31% | -1.94% | -0.10% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 000240 | 한국앤컴퍼니 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.79% | -2.20% | +1.60% |
| 024060 | 흥구석유 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.02% | -3.03% | -0.20% |

## OrderGuard Blocks
- none

## Reason Code Ranking
| reason_code | count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae | missing_mfe | missing_mae | missed_opportunity_count | missed_opportunity_rate | good_reject_count | good_reject_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 284 | +3.49% | -9.11% | 284 | 284 | 0 | 0 | 70 | 24.65% | 214 | 75.35% |
| TIME_POLICY_ANALYSIS_ONLY | 184 | +4.63% | -5.53% | 39 | 39 | 145 | 145 | 9 | 4.89% | 0 | 0.00% |
| FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 117 | +5.63% | -8.19% | 117 | 117 | 0 | 0 | 72 | 61.54% | 45 | 38.46% |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 45 | +3.46% | -9.87% | 45 | 45 | 0 | 0 | 8 | 17.78% | 37 | 82.22% |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 30 | +0.44% | -12.95% | 30 | 30 | 0 | 0 | 0 | 0.00% | 30 | 100.00% |
| FINAL_MOMENTUM_WAIT_RECLAIM_VWAP | 26 | +7.38% | -9.99% | 26 | 26 | 0 | 0 | 26 | 100.00% | 0 | 0.00% |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 25 | +3.01% | -6.11% | 25 | 25 | 0 | 0 | 6 | 24.00% | 19 | 76.00% |
| FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | 23 | +11.92% | -5.52% | 23 | 23 | 0 | 0 | 23 | 100.00% | 0 | 0.00% |
| FINAL_MOMENTUM_WAIT_LEADER_SCORE | 19 | +0.95% | -16.25% | 19 | 19 | 0 | 0 | 1 | 5.26% | 18 | 94.74% |
| missing | 9 | +8.97% | -3.51% | 9 | 9 | 0 | 0 | 9 | 100.00% | 0 | 0.00% |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_TOP | 4 | +0.83% | -7.27% | 4 | 4 | 0 | 0 | 0 | 0.00% | 4 | 100.00% |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 4 | +1.19% | -10.58% | 4 | 4 | 0 | 0 | 0 | 0.00% | 4 | 100.00% |

## Relaxed Pullback Dry Run
| policy | candidate_rows | unique_symbols | pullback_signal_rows | non_traded_signal_rows | top_signal_block_reason |
|---|---:|---:|---:|---:|---|
| pullback >= 0.5% | 770 | 46 | 260 | 260 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 0.8% | 770 | 41 | 243 | 243 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 1.0% | 770 | 37 | 218 | 218 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 1.5% | 770 | 29 | 129 | 129 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |

- pullback_signal_rows only means the relaxed pullback threshold passed; it is not a full buy-gate allowed count.

## Would Buy Comparison
| policy | row_count | unique_symbol_count | traded_count | top_reason |
|---|---:|---:|---:|---|
| baseline | 0 | 0 | 0 | missing |
| pullback_0p5_signal | 260 | 46 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_0p8_signal | 243 | 41 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_1p0_signal | 218 | 37 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_1p5_signal | 129 | 29 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| breakout_small_trace | 0 | 0 | 0 | missing |
| pullback_reclaim_vwap | 26 | 1 | 0 | FINAL_MOMENTUM_WAIT_RECLAIM_VWAP |

- pullback_*_signal is a relaxed pullback signal count, not a full buy-gate pass count.

## Weak Volume Ratio MFE
- weak_volume_ratio_good_reject_count: 45
- weak_volume_ratio_missed_opportunity_count: 72

| symbol | name | reason | MFE | MAE | volume_ratio | trade_strength |
|---|---|---|---:|---:|---:|---:|
| 382800 | 지앤비에스 에코 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +12.28% | -3.32% | 0.5188 | 137.8400 |
| 382800 | 지앤비에스 에코 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +12.28% | -3.32% | 0.5188 | 137.8400 |
| 382800 | 지앤비에스 에코 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +12.28% | -3.32% | 0.5188 | 137.8400 |
| 382800 | 지앤비에스 에코 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +12.28% | -3.32% | 0.5188 | 137.8400 |
| 382800 | 지앤비에스 에코 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +12.28% | -3.32% | 0.5188 | 137.8400 |
| 382800 | 지앤비에스 에코 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +12.28% | -3.32% | 0.5188 | 137.8400 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -15.40% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -11.32% | 0.1140 | 108.2600 |
| 261780 | 차백신연구소 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.44% | -11.32% | 0.1140 | 108.2600 |

## Reconciliation
- post_market raw detected rows: 770
- post_market unique symbols: 146
- post_market unique candidate_ids: 133
- baseline full-gate buy/order rows: 0
- relaxed pullback 0.5% signal rows: 260
- entry_gate_dry_run groups condition captures by symbol and then expands policy rows, while post_market keeps raw condition detections. Compare unique_symbol_count with raw_detected before tuning.
- previous relaxed pullback would_buy_count meant pullback-threshold signal only. It is now reported as signal rows to avoid implying that VWAP, volume, time policy, and order guard also passed.

## Time Bucket Analysis
| time_bucket | capture_count | traded_count | non_traded_count | missed_opportunity_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09:00~09:30 | 448 | 0 | 448 | 179 | 268 | +4.61% | -10.07% | 448 | 448 |
| 09:30~10:30 | 80 | 0 | 80 | 21 | 59 | +3.06% | -8.33% | 80 | 80 |
| 10:30~13:00 | 157 | 0 | 157 | 7 | 0 | +4.78% | -5.72% | 33 | 33 |
| 13:00~14:20 | 59 | 0 | 59 | 15 | 44 | +2.65% | -2.79% | 59 | 59 |
| 14:20 이후 | 26 | 0 | 26 | 2 | 0 | +4.53% | -2.90% | 5 | 5 |

## Parameter Tuning Hints
- BLOCK_CHASE has repeated upside misses. Review chase distance and wick thresholds manually.
- TimePolicy blocked rows later moved strongly. Review entry windows manually, especially recurring time buckets.

## Next Action Checklist
- [ ] Review top 5 MISSED_OPPORTUNITY rows.
- [ ] Check high-MFE DATA_QUALITY_BLOCK rows before tuning strategy parameters.
- [ ] Verify whether BLOCK_CHASE actually prevented weak follow-through.
- [ ] Review TIME_POLICY_BLOCK rows that rallied after the block.
- [ ] Inspect TRADED_LOSS reason_code clustering.
- [ ] Record config candidates only; do not change config immediately.

---
Generated from files only. This review does not connect to live trading.