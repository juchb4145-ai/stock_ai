# 2026-05-14 Post-Market Condition Review (live)

## Daily Summary
- total detected: 1086
- traded: 0
- non-traded: 1086
- TRADED_WIN: 0
- TRADED_LOSS: 0
- MISSED_OPPORTUNITY: 224
- GOOD_REJECT: 399
- DATA_QUALITY_BLOCK: 61
- TIME_POLICY_BLOCK: 400
- ORDER_GUARD_BLOCK: 0
- win rate: missing
- realized pnl: missing
- mode: live
- generated_at: 2026-05-14 15:22:49

## Daily Buy Gate Funnel
| metric | value |
|---|---:|
| raw_detected | 1086 |
| unique_detected_symbols | 220 |
| registered_candidates | 194 |
| analysis_only_candidates | 273 |
| momentum_evaluated | 631 |
| final_decision_emitted | 631 |
| baseline_buy_allowed | 0 |
| relaxed_pullback_signal_rows | 137 |
| order_attempted | 0 |
| order_filled | 0 |
| policy_row_count | 1086 |

## Reason Counts by Unique Symbol
| reason | row_count | unique_symbol_count | avg_mfe_pct | missed_count |
|---|---:|---:|---:|---:|
| FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 307 | 75 | +6.70% | 135 |
| TIME_POLICY_ANALYSIS_ONLY | 273 | 64 | missing | 0 |
| FINAL_MOMENTUM_REJECT_VWAP_LOST | 211 | 46 | +1.98% | 17 |
| TIME_POLICY_PRE_MOMENTUM_BLOCK | 127 | 35 | +4.79% | 51 |
| FINAL_MOMENTUM_REJECT_SPREAD | 63 | 10 | +9.55% | 40 |
| missing | 55 | 17 | +5.43% | 22 |
| FINAL_MOMENTUM_WAIT_MIN_AGE | 19 | 4 | +3.83% | 5 |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 14 | 7 | +8.06% | 10 |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 8 | 7 | +0.65% | 0 |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 6 | 1 | +3.16% | 0 |
| FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | 2 | 1 | +15.12% | 2 |
| FINAL_MOMENTUM_MISSING_PRIOR_HIGH | 1 | 1 | +7.92% | 1 |

## Trade Results
- no traded candidates

## Non-Traded Review
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 000720 | 현대건설 | 2026-05-14 09:02:40 | 166500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 4.76%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +2.28% | -1.56% | GOOD_REJECT |
| 0011T0 | 채비 | 2026-05-14 09:02:40 | 17620 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 6.31%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +7.83% | -2.61% | MISSED_OPPORTUNITY |
| 001440 | 대한전선 | 2026-05-14 09:02:40 | 69600 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=69100 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +1.01% | -7.04% | GOOD_REJECT |
| 001510 | SK증권 | 2026-05-14 09:02:40 | 4590 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=4525 vwap=4550 | FINAL_MOMENTUM_REJECT_VWAP_LOST | +0.98% | -5.66% | GOOD_REJECT |
| 001740 | SK네트웍스 | 2026-05-14 09:02:40 | 6590 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 1.19 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +19.88% | -2.35% | MISSED_OPPORTUNITY |
| 005930 | 삼성전자 | 2026-05-14 09:02:40 | 287000 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=287000 vwap... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +4.36% | -1.48% | GOOD_REJECT |
| 009830 | 한화솔루션 | 2026-05-14 09:02:40 | 45425 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 6.19%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +6.44% | -0.72% | MISSED_OPPORTUNITY |
| 025560 | 미래산업 | 2026-05-14 09:02:40 | 23100 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.91 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +11.04% | -3.90% | MISSED_OPPORTUNITY |
| 027360 | 아주IB투자 | 2026-05-14 09:02:40 | 16990 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 1.08 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +6.89% | -6.77% | MISSED_OPPORTUNITY |
| 033790 | 피노 | 2026-05-14 09:02:40 | 15840 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.08 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +2.84% | -9.41% | GOOD_REJECT |
| 034220 | LG디스플레이 | 2026-05-14 09:02:40 | 14800 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=14800 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +5.88% | -1.49% | MISSED_OPPORTUNITY |
| 035420 | NAVER | 2026-05-14 09:02:40 | 210000 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 4.50%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +2.86% | -0.95% | GOOD_REJECT |
| 035720 | 카카오 | 2026-05-14 09:02:41 | 44100 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.41 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +3.51% | -0.57% | GOOD_REJECT |
| 050890 | 쏠리드 | 2026-05-14 09:02:41 | 17530 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=17440 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +1.14% | -9.47% | GOOD_REJECT |
| 064400 | LG씨엔에스 | 2026-05-14 09:02:41 | 76600 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 4.12%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +15.40% | -1.31% | MISSED_OPPORTUNITY |
| 066570 | LG전자 | 2026-05-14 09:02:41 | 210000 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=208500 vwap... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +6.90% | -4.29% | MISSED_OPPORTUNITY |
| 081150 | 티플랙스 | 2026-05-14 09:02:41 | 4555 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.06 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -5.16% | MISSED_OPPORTUNITY |
| 088350 | 한화생명 | 2026-05-14 09:02:41 | 5125 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE chase distance too high 4.00% > 4.00% | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +15.12% | -0.29% | BAD_BLOCK_CHASE |
| 090460 | 비에이치 | 2026-05-14 09:02:41 | 33050 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.36 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +16.49% | -1.66% | MISSED_OPPORTUNITY |
| 100790 | 미래에셋벤처투자 | 2026-05-14 09:02:41 | 63700 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.95 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +10.99% | -7.85% | MISSED_OPPORTUNITY |
| 138080 | 오이솔루션 | 2026-05-14 09:02:41 | 51100 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=50100 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +0.20% | -10.86% | GOOD_REJECT |
| 140670 | 알에스오토메이션 | 2026-05-14 09:02:41 | 17860 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.69% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +2.18% | -6.38% | GOOD_REJECT |
| 144960 | 뉴파워프라즈마 | 2026-05-14 09:02:41 | 11590 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=11620 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +4.57% | -5.00% | GOOD_REJECT |
| 147830 | 제룡산업 | 2026-05-14 09:02:41 | 12310 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 97.9 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +1.38% | -10.40% | GOOD_REJECT |
| 178320 | 서진시스템 | 2026-05-14 09:02:41 | 68500 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=68100 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +3.36% | -3.21% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-14 09:02:41 | 377000 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=375000 vwap... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +2.92% | -2.25% | GOOD_REJECT |
| 199820 | 제일일렉트릭 | 2026-05-14 09:02:41 | 17310 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=17240 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +0.58% | -10.17% | GOOD_REJECT |
| 402340 | SK스퀘어 | 2026-05-14 09:02:41 | 1204000 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=1194000 vwa... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +0.33% | -3.90% | GOOD_REJECT |
| 412350 | 레이저쎌 | 2026-05-14 09:02:41 | 10990 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.43 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.38% | -12.74% | MISSED_OPPORTUNITY |
| 417840 | 저스템 | 2026-05-14 09:02:41 | 18130 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.53 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +3.70% | -8.99% | GOOD_REJECT |

## Missed Opportunities
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 081150 | 티플랙스 | 2026-05-14 09:02:41 | 4555 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.06 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -5.16% | MISSED_OPPORTUNITY |
| 081150 | 티플랙스 | 2026-05-14 09:17:03 | 4555 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.06 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -0.66% | MISSED_OPPORTUNITY |
| 081150 | 티플랙스 | 2026-05-14 09:17:07 | 4555 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.06 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -0.66% | MISSED_OPPORTUNITY |
| 081150 | 티플랙스 | 2026-05-14 09:21:13 | 4555 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.06 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -0.55% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:40:55 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:04 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:10 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:11 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:12 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:34 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:36 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:38 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:43 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:45 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |
| 254490 | 미래반도체 | 2026-05-14 13:41:50 | 39600 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.62% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +20.83% | -2.90% | MISSED_OPPORTUNITY |

## Good Rejects
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 000720 | 현대건설 | 2026-05-14 09:02:40 | 166500 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 4.76%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +2.28% | -1.56% | GOOD_REJECT |
| 001440 | 대한전선 | 2026-05-14 09:02:40 | 69600 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=69100 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +1.01% | -7.04% | GOOD_REJECT |
| 001510 | SK증권 | 2026-05-14 09:02:40 | 4590 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=4525 vwap=4550 | FINAL_MOMENTUM_REJECT_VWAP_LOST | +0.98% | -5.66% | GOOD_REJECT |
| 005930 | 삼성전자 | 2026-05-14 09:02:40 | 287000 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=287000 vwap... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +4.36% | -1.48% | GOOD_REJECT |
| 033790 | 피노 | 2026-05-14 09:02:40 | 15840 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.08 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +2.84% | -9.41% | GOOD_REJECT |
| 035420 | NAVER | 2026-05-14 09:02:40 | 210000 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE signal candle range too large 4.50%... | FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | +2.86% | -0.95% | GOOD_REJECT |
| 035720 | 카카오 | 2026-05-14 09:02:41 | 44100 | BLOCKED | Momentum decision is not BUY: REJECT weak_volume_ratio 0.41 < 1.20 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +3.51% | -0.57% | GOOD_REJECT |
| 050890 | 쏠리드 | 2026-05-14 09:02:41 | 17530 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=17440 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +1.14% | -9.47% | GOOD_REJECT |
| 138080 | 오이솔루션 | 2026-05-14 09:02:41 | 51100 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=50100 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +0.20% | -10.86% | GOOD_REJECT |
| 140670 | 알에스오토메이션 | 2026-05-14 09:02:41 | 17860 | BLOCKED | Momentum decision is not BUY: REJECT spread too wide 0.69% > 0.60% | FINAL_MOMENTUM_REJECT_SPREAD | +2.18% | -6.38% | GOOD_REJECT |
| 144960 | 뉴파워프라즈마 | 2026-05-14 09:02:41 | 11590 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=11620 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +4.57% | -5.00% | GOOD_REJECT |
| 147830 | 제룡산업 | 2026-05-14 09:02:41 | 12310 | BLOCKED | Momentum decision is not BUY: REJECT trade strength weak 97.9 < 100.0 | FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | +1.38% | -10.40% | GOOD_REJECT |
| 178320 | 서진시스템 | 2026-05-14 09:02:41 | 68500 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=68100 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +3.36% | -3.21% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-14 09:02:41 | 377000 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=375000 vwap... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +2.92% | -2.25% | GOOD_REJECT |
| 199820 | 제일일렉트릭 | 2026-05-14 09:02:41 | 17310 | BLOCKED | Momentum decision is not BUY: REJECT VWAP recovery failed current=17240 vwap=... | FINAL_MOMENTUM_REJECT_VWAP_LOST | +0.58% | -10.17% | GOOD_REJECT |

## Block Chase Review
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 088350 | 한화생명 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +15.12% | -0.29% | +8.88% |
| 088350 | 한화생명 | BAD_BLOCK_CHASE | FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | +15.12% | +3.61% | +8.88% |

## Data Quality Blocks
| symbol | name | category | reason_code | MFE | MAE | close return | data_quality |
|---|---|---|---|---:|---:|---:|---|
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | -1.86% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | MISSED_OPPORTUNITY | missing | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | MISSED_OPPORTUNITY | missing | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | MISSED_OPPORTUNITY | missing | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | MISSED_OPPORTUNITY | missing | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | MISSED_OPPORTUNITY | missing | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | MISSED_OPPORTUNITY | missing | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | MISSED_OPPORTUNITY | missing | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | -1.19% | +5.59% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | -1.19% | +5.59% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | +0.90% | +5.59% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | +3.90% | +5.59% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 096530 | 씨젠 | DATA_QUALITY_BLOCK | FINAL_MOMENTUM_WAIT_MIN_AGE | +10.78% | -1.39% | +8.35% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |

| data_quality | count | avg_mfe_pct | n_mfe | missing_mfe |
|---|---:|---:|---:|---:|
| partial_data | 516 | +4.99% | 193 | 323 |
| MISSING_DECISION_TRACE | 455 | +4.98% | 182 | 273 |
| MISSING_SPREAD_RATE | 381 | +4.98% | 182 | 199 |
| MISSING_TRADE_STRENGTH | 381 | +4.98% | 182 | 199 |
| MISSING_MFE_MAE | 323 | missing | 0 | 323 |
| MISSING_CAPTURE_PRICE | 273 | missing | 0 | 273 |
| MISSING_MARKET_METRICS | 135 | +5.21% | 11 | 124 |
| market_data_unavailable | 11 | +5.21% | 11 | 0 |
| FINAL_MOMENTUM_MISSING_PRIOR_HIGH | 1 | +7.92% | 1 | 0 |
| MOMENTUM | 1 | +7.92% | 1 | 0 |

## Missing Decision Trace Detail
| symbol | name | detected_at | candidate_id | role | reason_code | time_policy | source | stage | data_quality |
|---|---|---|---|---|---|---|---|---|---|
| 128820 | 대성산업 | 2026-05-14 10:33:41 | adfc7b45cec642ebb94997f250e67a66 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 128820 | 대성산업 | 2026-05-14 10:39:06 | adfc7b45cec642ebb94997f250e67a66 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 294870 | IPARK현대산업개발 | 2026-05-14 10:40:51 | 33b8a60ce3e2470bae982b4bc86f9ea0 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 294870 | IPARK현대산업개발 | 2026-05-14 10:40:58 | 33b8a60ce3e2470bae982b4bc86f9ea0 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 294870 | IPARK현대산업개발 | 2026-05-14 10:41:03 | 33b8a60ce3e2470bae982b4bc86f9ea0 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 294870 | IPARK현대산업개발 | 2026-05-14 10:41:24 | 33b8a60ce3e2470bae982b4bc86f9ea0 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:41:48 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:41:49 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:42:04 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:42:08 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:42:16 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:42:27 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:43:30 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 061090 | 세나테크놀로지 | 2026-05-14 10:43:46 | 4eb332fc9ab441d3a6d13f0542e73ec7 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 090430 | 아모레퍼시픽 | 2026-05-14 10:46:02 | 5937ebce76e84c8b93bb83969e82ecdb |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:48:14 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:49:14 | c5522931d0cc476799014f7cd6c2c6ae |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:49:15 | c5522931d0cc476799014f7cd6c2c6ae |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:49:17 | c5522931d0cc476799014f7cd6c2c6ae |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:49:20 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:49:21 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:49:39 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:50:46 | c5522931d0cc476799014f7cd6c2c6ae |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:50:48 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:50:52 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:51:42 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:51:51 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:51:57 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:52:02 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:52:05 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:52:06 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:52:23 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 420570 | 제이투케이바이오 | 2026-05-14 10:52:35 | c5522931d0cc476799014f7cd6c2c6ae |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:52:48 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:52:49 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:52:51 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:52:53 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:53:03 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:53:04 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:53:07 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:53:12 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:53:13 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 086960 | MDS테크 | 2026-05-14 10:53:14 | 0bb80c9cbfdd4aab9e2a297ed7344420 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 380550 | 뉴로핏 | 2026-05-14 10:54:01 | 7d9a361d7e084a60a380c58a75eaa1f5 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 380550 | 뉴로핏 | 2026-05-14 10:56:41 | 7d9a361d7e084a60a380c58a75eaa1f5 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 064290 | 인텍플러스 | 2026-05-14 10:57:48 | 457f2b1d81b24bc79320a5c55f81036d |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 024060 | 흥구석유 | 2026-05-14 10:59:55 | 921d557b072e4823afd87d6fc1038542 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 950130 | 엑세스바이오 | 2026-05-14 11:06:34 | 15a541a0834c4784bd3d9855bbb3c450 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 950130 | 엑세스바이오 | 2026-05-14 11:07:07 | 15a541a0834c4784bd3d9855bbb3c450 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 950130 | 엑세스바이오 | 2026-05-14 11:07:46 | 15a541a0834c4784bd3d9855bbb3c450 |  | TIME_POLICY_PRE_MOMENTUM_BLOCK | ALLOW_MANAGE_ONLY | evaluate_time_filter | time_policy_pre_momentum | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |

## Data Quality High MFE
| symbol | name | detected_at | reason | MFE | MAE | data_quality |
|---|---|---|---|---:|---:|---|
| 096530 | 씨젠 | 2026-05-14 09:06:46 | FINAL_MOMENTUM_WAIT_MIN_AGE | +10.78% | -1.39% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 096530 | 씨젠 | 2026-05-14 09:13:14 | FINAL_MOMENTUM_WAIT_MIN_AGE | +10.78% | -0.17% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 096530 | 씨젠 | 2026-05-14 09:18:27 | FINAL_MOMENTUM_WAIT_MIN_AGE | +10.78% | +0.87% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 128820 | 대성산업 | 2026-05-14 09:06:02 | FINAL_MOMENTUM_MISSING_PRIOR_HIGH | +7.92% | -3.40% | FINAL_MOMENTUM_MISSING_PRIOR_HIGH;MISSING_MARKET_METRICS;MOMENTUM;market_data_unavailable;partial... |
| 001450 | 현대해상 | 2026-05-14 09:06:46 | FINAL_MOMENTUM_WAIT_MIN_AGE | +6.62% | -1.29% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 001450 | 현대해상 | 2026-05-14 09:11:24 | FINAL_MOMENTUM_WAIT_MIN_AGE | +6.62% | +1.29% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 475150 | SK이터닉스 | 2026-05-14 10:29:20 | FINAL_MOMENTUM_WAIT_MIN_AGE | +0.76% | -4.17% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 475150 | SK이터닉스 | 2026-05-14 10:29:22 | FINAL_MOMENTUM_WAIT_MIN_AGE | +0.76% | -4.17% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 475150 | SK이터닉스 | 2026-05-14 10:29:32 | FINAL_MOMENTUM_WAIT_MIN_AGE | +0.76% | -4.17% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 475150 | SK이터닉스 | 2026-05-14 10:29:46 | FINAL_MOMENTUM_WAIT_MIN_AGE | +0.76% | -4.17% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |
| 475150 | SK이터닉스 | 2026-05-14 10:29:48 | FINAL_MOMENTUM_WAIT_MIN_AGE | +0.76% | -4.17% | MISSING_MARKET_METRICS;market_data_unavailable;partial_data |

## Time Policy Blocks
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | -1.86% | +5.43% |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% |
| 086960 | MDS테크 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +16.29% | +2.43% | +5.43% |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | -1.19% | +5.59% |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | -1.19% | +5.59% |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | +0.90% | +5.59% |
| 380550 | 뉴로핏 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +13.78% | +3.90% | +5.59% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |
| 420570 | 제이투케이바이오 | TIME_POLICY_BLOCK | TIME_POLICY_PRE_MOMENTUM_BLOCK | +10.19% | -2.80% | -0.34% |

## OrderGuard Blocks
- none

## Reason Code Ranking
| reason_code | count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae | missing_mfe | missing_mae | missed_opportunity_count | missed_opportunity_rate | good_reject_count | good_reject_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 307 | +6.70% | -3.77% | 298 | 298 | 9 | 9 | 135 | 43.97% | 163 | 53.09% |
| TIME_POLICY_ANALYSIS_ONLY | 273 | missing | missing | 0 | 0 | 273 | 273 | 0 | 0.00% | 0 | 0.00% |
| FINAL_MOMENTUM_REJECT_VWAP_LOST | 211 | +1.98% | -4.64% | 172 | 172 | 39 | 39 | 17 | 8.06% | 155 | 73.46% |
| TIME_POLICY_PRE_MOMENTUM_BLOCK | 127 | +4.79% | -2.30% | 127 | 127 | 0 | 0 | 51 | 40.16% | 0 | 0.00% |
| FINAL_MOMENTUM_REJECT_SPREAD | 63 | +9.55% | -5.04% | 61 | 61 | 2 | 2 | 40 | 63.49% | 21 | 33.33% |
| missing | 55 | +5.43% | -1.45% | 55 | 55 | 0 | 0 | 22 | 40.00% | 33 | 60.00% |
| FINAL_MOMENTUM_WAIT_MIN_AGE | 19 | +3.83% | -1.69% | 19 | 19 | 0 | 0 | 5 | 26.32% | 9 | 47.37% |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 14 | +8.06% | -0.83% | 14 | 14 | 0 | 0 | 10 | 71.43% | 4 | 28.57% |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 8 | +0.65% | -5.76% | 8 | 8 | 0 | 0 | 0 | 0.00% | 8 | 100.00% |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 6 | +3.16% | -14.38% | 6 | 6 | 0 | 0 | 0 | 0.00% | 6 | 100.00% |
| FINAL_MOMENTUM_BLOCK_CHASE_DISTANCE | 2 | +15.12% | +1.66% | 2 | 2 | 0 | 0 | 2 | 100.00% | 0 | 0.00% |
| FINAL_MOMENTUM_MISSING_PRIOR_HIGH | 1 | +7.92% | -3.40% | 1 | 1 | 0 | 0 | 1 | 100.00% | 0 | 0.00% |

## Relaxed Pullback Dry Run
| policy | candidate_rows | unique_symbols | pullback_signal_rows | non_traded_signal_rows | top_signal_block_reason |
|---|---:|---:|---:|---:|---|
| pullback >= 0.5% | 1086 | 30 | 137 | 137 | FINAL_MOMENTUM_REJECT_VWAP_LOST |
| pullback >= 0.8% | 1086 | 17 | 70 | 70 | FINAL_MOMENTUM_REJECT_VWAP_LOST |
| pullback >= 1.0% | 1086 | 12 | 60 | 60 | FINAL_MOMENTUM_REJECT_VWAP_LOST |
| pullback >= 1.5% | 1086 | 7 | 30 | 30 | FINAL_MOMENTUM_REJECT_SPREAD |

- pullback_signal_rows only means the relaxed pullback threshold passed; it is not a full buy-gate allowed count.

## Would Buy Comparison
| policy | row_count | unique_symbol_count | traded_count | top_reason |
|---|---:|---:|---:|---|
| baseline | 0 | 0 | 0 | missing |
| pullback_0p5_signal | 137 | 30 | 0 | FINAL_MOMENTUM_REJECT_VWAP_LOST |
| pullback_0p8_signal | 70 | 17 | 0 | FINAL_MOMENTUM_REJECT_VWAP_LOST |
| pullback_1p0_signal | 60 | 12 | 0 | FINAL_MOMENTUM_REJECT_VWAP_LOST |
| pullback_1p5_signal | 30 | 7 | 0 | FINAL_MOMENTUM_REJECT_SPREAD |
| breakout_small_trace | 0 | 0 | 0 | missing |
| pullback_reclaim_vwap | 0 | 0 | 0 | missing |

- pullback_*_signal is a relaxed pullback signal count, not a full buy-gate pass count.

## Weak Volume Ratio MFE
- weak_volume_ratio_good_reject_count: 163
- weak_volume_ratio_missed_opportunity_count: 135

| symbol | name | reason | MFE | MAE | volume_ratio | trade_strength |
|---|---|---|---:|---:|---:|---:|
| 081150 | 티플랙스 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -5.16% | 0.0596 | 114.8800 |
| 081150 | 티플랙스 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -0.66% | 0.0596 | 114.8800 |
| 081150 | 티플랙스 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -0.66% | 0.0596 | 114.8800 |
| 081150 | 티플랙스 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +22.28% | -0.55% | 0.0596 | 114.8800 |
| 042520 | 한스바이오메드 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +20.55% | -2.31% | 0.2487 | 160.4300 |
| 042520 | 한스바이오메드 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +20.55% | -2.31% | 0.2487 | 160.4300 |
| 042520 | 한스바이오메드 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +20.55% | -2.31% | 0.2487 | 160.4300 |
| 042520 | 한스바이오메드 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +20.55% | +1.05% | 0.2487 | 160.4300 |
| 001740 | SK네트웍스 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +19.88% | -2.35% | 1.1935 | 173.9700 |
| 001740 | SK네트웍스 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +19.88% | +1.06% | 1.1935 | 173.9700 |
| 412350 | 레이저쎌 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.38% | -12.74% | 0.4341 | 101.9600 |
| 412350 | 레이저쎌 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.38% | -12.74% | 0.4341 | 101.9600 |
| 031330 | 에스에이엠티 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.10% | -1.77% | 0.0327 | 111.7700 |
| 031330 | 에스에이엠티 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.10% | -1.77% | 0.0327 | 111.7700 |
| 031330 | 에스에이엠티 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.10% | -1.77% | 0.0327 | 111.7700 |
| 031330 | 에스에이엠티 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.10% | -1.77% | 0.0327 | 111.7700 |
| 031330 | 에스에이엠티 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.10% | -1.77% | 0.0327 | 111.7700 |
| 382480 | 지아이텍 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.03% | -0.90% | 0.0244 | 132.1700 |
| 382480 | 지아이텍 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +17.03% | +1.08% | 0.0244 | 132.1700 |
| 090460 | 비에이치 | FINAL_MOMENTUM_WEAK_VOLUME_RATIO | +16.49% | -1.66% | 0.3579 | 335.3600 |

## Reconciliation
- post_market raw detected rows: 1086
- post_market unique symbols: 220
- post_market unique candidate_ids: 194
- baseline full-gate buy/order rows: 0
- relaxed pullback 0.5% signal rows: 137
- entry_gate_dry_run groups condition captures by symbol and then expands policy rows, while post_market keeps raw condition detections. Compare unique_symbol_count with raw_detected before tuning.
- previous relaxed pullback would_buy_count meant pullback-threshold signal only. It is now reported as signal rows to avoid implying that VWAP, volume, time policy, and order guard also passed.

## Time Bucket Analysis
| time_bucket | capture_count | traded_count | non_traded_count | missed_opportunity_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09:00~09:30 | 312 | 0 | 312 | 133 | 179 | +5.79% | -5.22% | 312 | 312 |
| 09:30~10:30 | 106 | 0 | 106 | 12 | 89 | +2.64% | -5.08% | 106 | 106 |
| 10:30~13:00 | 311 | 0 | 311 | 73 | 33 | +4.98% | -2.04% | 182 | 182 |
| 13:00~14:20 | 213 | 0 | 213 | 65 | 98 | +6.63% | -1.47% | 163 | 163 |
| 14:20 이후 | 144 | 0 | 144 | 0 | 0 | missing | missing | 0 | 0 |

## Parameter Tuning Hints
- DATA_QUALITY_BLOCK rows include high MFE. Check collection for missing volume/VWAP/candle cache before changing entry rules.
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