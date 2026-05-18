# 2026-05-18 Post-Market Condition Review (live)

## Daily Summary
- total detected: 688
- traded: 0
- non-traded: 688
- TRADED_WIN: 0
- TRADED_LOSS: 0
- MISSED_OPPORTUNITY: 192
- GOOD_REJECT: 226
- DATA_QUALITY_BLOCK: 0
- TIME_POLICY_BLOCK: 251
- ORDER_GUARD_BLOCK: 0
- win rate: missing
- realized pnl: missing
- mode: live
- generated_at: 2026-05-18 17:24:27

## Daily Buy Gate Funnel
| metric | value |
|---|---:|
| raw_detected | 688 |
| unique_detected_symbols | 94 |
| registered_candidates | 74 |
| analysis_only_candidates | 268 |
| momentum_evaluated | 437 |
| final_decision_emitted | 437 |
| baseline_buy_allowed | 0 |
| relaxed_pullback_signal_rows | 356 |
| order_attempted | 0 |
| order_filled | 0 |
| policy_row_count | 688 |

## Market/Sector/Theme Gates
| field | value | row_count | unique_symbol_count | missed_count | avg_mfe_pct |
|---|---|---:|---:|---:|---:|
| gate_payload | missing | 0 | 0 | 0 | missing |

- no structured market/sector/theme gate fields found in matched 2026-05-15 logs.

## Reason Counts by Unique Symbol
| reason | row_count | unique_symbol_count | avg_mfe_pct | missed_count |
|---|---:|---:|---:|---:|
| TIME_POLICY_ANALYSIS_ONLY | 251 | 43 | +2.95% | 11 |
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 126 | 32 | +3.93% | 30 |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 114 | 10 | +9.95% | 79 |
| FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 73 | 12 | +3.60% | 19 |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 58 | 8 | +5.22% | 38 |
| FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | 19 | 2 | +16.02% | 19 |
| FINAL_MOMENTUM_REJECT_SPREAD | 19 | 4 | +7.58% | 7 |
| FINAL_MOMENTUM_WAIT_LEADER_SCORE | 16 | 3 | +12.43% | 7 |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 12 | 2 | +14.88% | 12 |

## Trade Results
- no traded candidates

## Exit Type Performance
- no traded candidates

## Non-Traded Review
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 036930 | 주성엔지니어링 | 2026-05-18 09:00:19 | 153300 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 4.96% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -2.02% | BAD_BLOCK_CHASE |
| 036930 | 주성엔지니어링 | 2026-05-18 09:00:19 | 153300 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 4.96% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -2.02% | BAD_BLOCK_CHASE |
| 088350 | 한화생명 | 2026-05-18 09:00:33 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 088350 | 한화생명 | 2026-05-18 09:00:36 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 001450 | 현대해상 | 2026-05-18 09:00:37 | 35300 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 5.59%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +11.90% | -1.70% | MISSED_OPPORTUNITY |
| 001450 | 현대해상 | 2026-05-18 09:00:37 | 35300 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 5.59%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +11.90% | -1.70% | MISSED_OPPORTUNITY |
| 088350 | 한화생명 | 2026-05-18 09:00:38 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 088350 | 한화생명 | 2026-05-18 09:00:51 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 490470 | 세미파이브 | 2026-05-18 09:01:21 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 490470 | 세미파이브 | 2026-05-18 09:01:21 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 490470 | 세미파이브 | 2026-05-18 09:01:24 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 490470 | 세미파이브 | 2026-05-18 09:01:25 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 332570 | PS일렉트로닉스 | 2026-05-18 09:01:28 | 12470 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.65% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +9.62% | -5.61% | MISSED_OPPORTUNITY |
| 490470 | 세미파이브 | 2026-05-18 09:01:28 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 490470 | 세미파이브 | 2026-05-18 09:01:31 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 178320 | 서진시스템 | 2026-05-18 09:01:31 | 71500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.32... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +5.45% | -4.90% | MISSED_OPPORTUNITY |
| 178320 | 서진시스템 | 2026-05-18 09:01:32 | 71500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.32... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +5.45% | -4.90% | MISSED_OPPORTUNITY |
| 490470 | 세미파이브 | 2026-05-18 09:01:32 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 036930 | 주성엔지니어링 | 2026-05-18 09:01:33 | 153300 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 4.96% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -1.89% | BAD_BLOCK_CHASE |
| 490470 | 세미파이브 | 2026-05-18 09:01:34 | 37250 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +6.58% | -6.04% | MISSED_OPPORTUNITY |
| 178320 | 서진시스템 | 2026-05-18 09:01:45 | 71500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.32... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +5.45% | -4.90% | MISSED_OPPORTUNITY |
| 178320 | 서진시스템 | 2026-05-18 09:01:45 | 71500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.32... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +5.45% | -4.90% | MISSED_OPPORTUNITY |
| 178320 | 서진시스템 | 2026-05-18 09:02:01 | 71500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.32... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +5.45% | -4.90% | MISSED_OPPORTUNITY |
| 178320 | 서진시스템 | 2026-05-18 09:02:01 | 71500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.32... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +5.45% | -4.90% | MISSED_OPPORTUNITY |
| 038500 | 삼표시멘트 | 2026-05-18 09:02:10 | 14060 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.45... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +6.69% | -4.91% | MISSED_OPPORTUNITY |
| 038500 | 삼표시멘트 | 2026-05-18 09:02:12 | 14060 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 10.45... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +6.69% | -4.91% | MISSED_OPPORTUNITY |
| 253840 | 수젠텍 | 2026-05-18 09:02:13 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:02:13 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 066430 | 아이로보틱스 | 2026-05-18 09:02:30 | 3445 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 94.9 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +16.11% | -14.37% | MISSED_OPPORTUNITY |
| 100790 | 미래에셋벤처투자 | 2026-05-18 09:02:32 | 60600 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +11.88% | -5.28% | MISSED_OPPORTUNITY |

## Missed Opportunities
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 412350 | 레이저쎌 | 2026-05-18 10:08:53 | 11565 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 29.3 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +26.59% | -1.51% | MISSED_OPPORTUNITY |
| 412350 | 레이저쎌 | 2026-05-18 10:08:53 | 11565 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 29.3 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +26.59% | -1.51% | MISSED_OPPORTUNITY |
| 412350 | 레이저쎌 | 2026-05-18 10:08:58 | 11565 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 29.3 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +26.59% | -1.51% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:36:45 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | -2.21% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:36:46 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | -2.21% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:42:50 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:14 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:19 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:28 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:28 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:32 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:45 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:46 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 380550 | 뉴로핏 | 2026-05-18 13:43:52 | 16730 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +24.93% | +3.77% | MISSED_OPPORTUNITY |
| 274090 | 켄코아에어로스페이스 | 2026-05-18 09:13:16 | 20900 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 46.0 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +24.16% | -4.31% | MISSED_OPPORTUNITY |

## Good Rejects
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 088350 | 한화생명 | 2026-05-18 09:00:33 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 088350 | 한화생명 | 2026-05-18 09:00:36 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 088350 | 한화생명 | 2026-05-18 09:00:38 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 088350 | 한화생명 | 2026-05-18 09:00:51 | 5550 | WAIT | Momentum decision is not BUY: WAIT_PULLBACK leader score wait 60.7 < 65.0 | FINAL_MOMENTUM_WAIT_LEADER_SCORE | +4.68% | -8.83% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:02:13 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:02:13 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:02:47 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:02:50 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:03:14 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:03:41 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:03:49 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:04:04 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 253840 | 수젠텍 | 2026-05-18 09:04:07 | 7260 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.81 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +1.24% | -11.43% | GOOD_REJECT |
| 204270 | 제이앤티씨 | 2026-05-18 09:05:18 | 21150 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.39 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +3.07% | -7.47% | GOOD_REJECT |
| 204270 | 제이앤티씨 | 2026-05-18 09:05:19 | 21150 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.39 < 1.20 bucket=bas... | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +3.07% | -7.47% | GOOD_REJECT |

## Block Chase Review
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 036930 | 주성엔지니어링 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -2.02% | +18.85% |
| 036930 | 주성엔지니어링 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -2.02% | +18.85% |
| 036930 | 주성엔지니어링 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -1.89% | +18.85% |
| 036930 | 주성엔지니어링 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -0.39% | +18.85% |
| 036930 | 주성엔지니어링 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -0.39% | +18.85% |
| 036930 | 주성엔지니어링 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -0.39% | +18.85% |
| 036930 | 주성엔지니어링 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +18.85% | -0.39% | +18.85% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -4.79% | +0.00% |
| 037460 | 삼지전자 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +14.36% | -1.60% | +0.00% |

## Data Quality Blocks
| symbol | name | category | reason_code | MFE | MAE | close return | data_quality |
|---|---|---|---|---:|---:|---:|---|
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |

| data_quality | count | avg_mfe_pct | n_mfe | missing_mfe |
|---|---:|---:|---:|---:|
| MISSING_DECISION_TRACE | 251 | +2.95% | 107 | 144 |
| MISSING_SPREAD_RATE | 251 | +2.95% | 107 | 144 |
| MISSING_TRADE_STRENGTH | 251 | +2.95% | 107 | 144 |
| partial_data | 251 | +2.95% | 107 | 144 |
| MISSING_CAPTURE_PRICE | 144 | missing | 0 | 144 |
| MISSING_MFE_MAE | 144 | missing | 0 | 144 |
| MISSING_UPPER_WICK_RATIO | 1 | +0.00% | 1 | 0 |

## Missing Decision Trace Detail
| symbol | name | detected_at | candidate_id | role | reason_code | time_policy | source | stage | data_quality |
|---|---|---|---|---|---|---|---|---|---|
| 044380 | 주연테크 | 2026-05-18 09:07:50 | 38400ff3447f41d6bd97ac89295568cc | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_UPP... |
| 019180 | 티에이치엔 | 2026-05-18 10:32:36 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 007610 | 선도전기 | 2026-05-18 10:32:52 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 019180 | 티에이치엔 | 2026-05-18 10:33:15 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 019180 | 티에이치엔 | 2026-05-18 10:33:27 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 007610 | 선도전기 | 2026-05-18 10:33:38 | ce9f9bb47acc48c1b18f79925e28f1a3 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 019180 | 티에이치엔 | 2026-05-18 10:34:06 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 007610 | 선도전기 | 2026-05-18 10:36:04 | ce9f9bb47acc48c1b18f79925e28f1a3 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 007610 | 선도전기 | 2026-05-18 10:36:05 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 007610 | 선도전기 | 2026-05-18 10:39:23 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 007610 | 선도전기 | 2026-05-18 10:39:24 | ce9f9bb47acc48c1b18f79925e28f1a3 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:48:12 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 017900 | 광전자 | 2026-05-18 10:48:53 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:48:54 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:48:59 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:02 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:07 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:08 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 093370 | 후성 | 2026-05-18 10:49:09 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 017900 | 광전자 | 2026-05-18 10:49:11 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:14 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:16 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:18 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:20 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:22 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:49:41 | 913ac5f79e674634b7305d1830a68342 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 017900 | 광전자 | 2026-05-18 10:52:41 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 361390 | 제노코 | 2026-05-18 10:54:02 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 458650 | 성우 | 2026-05-18 10:57:00 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 017510 | 세명전기 | 2026-05-18 10:58:31 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 458650 | 성우 | 2026-05-18 10:59:21 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 217730 | 강스템바이오텍 | 2026-05-18 11:09:49 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 082920 | 비츠로셀 | 2026-05-18 11:13:40 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 403870 | HPSP | 2026-05-18 11:13:42 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | missing | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 403870 | HPSP | 2026-05-18 11:13:42 | 285f1cca5490432caf156d7bd90904dd | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 082920 | 비츠로셀 | 2026-05-18 11:13:46 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 082920 | 비츠로셀 | 2026-05-18 11:13:56 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 082920 | 비츠로셀 | 2026-05-18 11:14:00 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 082920 | 비츠로셀 | 2026-05-18 11:14:01 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 217730 | 강스템바이오텍 | 2026-05-18 11:14:59 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 014620 | 성광벤드 | 2026-05-18 11:16:46 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 394420 | 리센스메디컬 | 2026-05-18 11:19:39 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 004590 | 한국가구 | 2026-05-18 11:20:35 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | condition_detected | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 000370 | 한화손해보험 | 2026-05-18 11:21:55 |  | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_MANAGE_ONLY | missing | analysis_only | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 000370 | 한화손해보험 | 2026-05-18 11:21:55 | f24082df100e4f2fb785b0b432f1f78b | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 000370 | 한화손해보험 | 2026-05-18 11:21:59 | f24082df100e4f2fb785b0b432f1f78b | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 000370 | 한화손해보험 | 2026-05-18 11:22:15 | f24082df100e4f2fb785b0b432f1f78b | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 000370 | 한화손해보험 | 2026-05-18 11:22:18 | f24082df100e4f2fb785b0b432f1f78b | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 000370 | 한화손해보험 | 2026-05-18 11:22:30 | f24082df100e4f2fb785b0b432f1f78b | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 000370 | 한화손해보험 | 2026-05-18 11:22:57 | f24082df100e4f2fb785b0b432f1f78b | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | condition_detected | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |

## Data Quality High MFE
- none

## Time Policy Blocks
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 055490 | 테이팩스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.35% | -5.64% | +3.79% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |
| 295310 | 에이치브이엠 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.70% | -1.48% | +3.30% |

## OrderGuard Blocks
- none

## Reason Code Ranking
| reason_code | count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae | missing_mfe | missing_mae | missed_opportunity_count | missed_opportunity_rate | good_reject_count | good_reject_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TIME_POLICY_ANALYSIS_ONLY | 251 | +2.95% | -3.22% | 107 | 107 | 144 | 144 | 11 | 4.38% | 0 | 0.00% |
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 126 | +3.93% | -3.02% | 126 | 126 | 0 | 0 | 30 | 23.81% | 96 | 76.19% |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 114 | +9.95% | -12.53% | 114 | 114 | 0 | 0 | 79 | 69.30% | 35 | 30.70% |
| FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 73 | +3.60% | -4.80% | 73 | 73 | 0 | 0 | 19 | 26.03% | 54 | 73.97% |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 58 | +5.22% | -4.43% | 58 | 58 | 0 | 0 | 38 | 65.52% | 20 | 34.48% |
| FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | 19 | +16.02% | -3.25% | 19 | 19 | 0 | 0 | 19 | 100.00% | 0 | 0.00% |
| FINAL_MOMENTUM_REJECT_SPREAD | 19 | +7.58% | -8.97% | 19 | 19 | 0 | 0 | 7 | 36.84% | 12 | 63.16% |
| FINAL_MOMENTUM_WAIT_LEADER_SCORE | 16 | +12.43% | -3.96% | 16 | 16 | 0 | 0 | 7 | 43.75% | 9 | 56.25% |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 12 | +14.88% | -13.75% | 12 | 12 | 0 | 0 | 12 | 100.00% | 0 | 0.00% |

## Relaxed Pullback Dry Run
| policy | candidate_rows | unique_symbols | pullback_signal_rows | non_traded_signal_rows | top_signal_block_reason |
|---|---:|---:|---:|---:|---|
| pullback >= 0.5% | 688 | 47 | 356 | 356 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback >= 0.8% | 688 | 36 | 261 | 261 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback >= 1.0% | 688 | 35 | 254 | 254 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback >= 1.5% | 688 | 27 | 220 | 220 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |

- pullback_signal_rows only means the relaxed pullback threshold passed; it is not a full buy-gate allowed count.

## Would Buy Comparison
| policy | row_count | unique_symbol_count | traded_count | top_reason |
|---|---:|---:|---:|---|
| baseline | 0 | 0 | 0 | missing |
| pullback_0p5_signal | 356 | 47 | 0 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_0p8_signal | 261 | 36 | 0 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_1p0_signal | 254 | 35 | 0 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_1p5_signal | 220 | 27 | 0 | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW |
| breakout_small_trace | 0 | 0 | 0 | missing |
| pullback_reclaim_vwap | 0 | 0 | 0 | missing |

- pullback_*_signal is a relaxed pullback signal count, not a full buy-gate pass count.

## Weak Volume Ratio MFE
- weak_volume_ratio_good_reject_count: 54
- weak_volume_ratio_missed_opportunity_count: 19

| symbol | name | reason | MFE | MAE | volume_ratio | trade_strength |
|---|---|---|---:|---:|---:|---:|
| 211270 | AP위성 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +18.08% | -0.94% | 0.6360 | 135.0100 |
| 211270 | AP위성 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +18.08% | +1.68% | 0.6360 | 135.0100 |
| 211270 | AP위성 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +18.08% | +1.68% | 0.6360 | 135.0100 |
| 474170 | 루미르 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +10.18% | -2.02% | 0.2138 | 116.9600 |
| 474170 | 루미르 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +10.18% | +3.11% | 0.2138 | 116.9600 |
| 474170 | 루미르 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +10.18% | +3.50% | 0.2138 | 116.9600 |
| 100790 | 미래에셋벤처투자 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +7.62% | -1.11% | 0.0496 | 116.0600 |
| 100790 | 미래에셋벤처투자 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +7.62% | -1.11% | 0.0496 | 116.0600 |
| 100790 | 미래에셋벤처투자 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +7.62% | -0.95% | 0.0496 | 116.0600 |
| 403870 | HPSP | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +6.20% | -3.29% | 0.1035 | 115.9100 |
| 403870 | HPSP | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +6.20% | -2.52% | 0.1035 | 115.9100 |
| 403870 | HPSP | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +6.20% | -2.52% | 0.1035 | 115.9100 |
| 019210 | 와이지-원 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.57% | -1.11% | 0.0577 | 106.8600 |
| 019210 | 와이지-원 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.57% | -1.11% | 0.0577 | 106.8600 |
| 019210 | 와이지-원 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.57% | -1.11% | 0.0577 | 106.8600 |
| 019210 | 와이지-원 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.57% | -1.11% | 0.0577 | 106.8600 |
| 417840 | 저스템 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.04% | -3.92% | 0.2502 | 100.1000 |
| 417840 | 저스템 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.04% | -2.08% | 0.2502 | 100.1000 |
| 417840 | 저스템 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +5.04% | -2.08% | 0.2502 | 100.1000 |
| 204270 | 제이앤티씨 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +3.07% | -7.47% | 0.3942 | 120.8100 |

## Reconciliation
- post_market raw detected rows: 688
- post_market unique symbols: 94
- post_market unique candidate_ids: 92
- baseline full-gate buy/order rows: 0
- relaxed pullback 0.5% signal rows: 356
- entry_gate_dry_run groups condition captures by symbol and then expands policy rows, while post_market keeps raw condition detections. Compare unique_symbol_count with raw_detected before tuning.
- previous relaxed pullback would_buy_count meant pullback-threshold signal only. It is now reported as signal rows to avoid implying that VWAP, volume, time policy, and order guard also passed.

## Time Bucket Analysis
| time_bucket | capture_count | strategy_candidate_count | paper_only_count | traded_count | non_traded_count | missed_opportunity_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09:00~09:30 | 240 | 0 | 0 | 0 | 240 | 153 | 86 | +8.68% | -9.86% | 240 | 240 |
| 09:30~10:30 | 72 | 0 | 0 | 0 | 72 | 25 | 47 | +5.13% | -3.16% | 72 | 72 |
| 10:30~13:00 | 199 | 0 | 0 | 0 | 199 | 11 | 2 | +2.71% | -3.35% | 84 | 84 |
| 13:00~14:20 | 124 | 0 | 0 | 0 | 124 | 33 | 91 | +4.56% | -2.51% | 124 | 124 |
| 14:20 이후 | 53 | 0 | 0 | 0 | 53 | 0 | 0 | +3.82% | -1.40% | 24 | 24 |

## Paper Strategy Performance
No paper-only strategy candidates.

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