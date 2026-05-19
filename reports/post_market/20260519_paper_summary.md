# 2026-05-19 Post-Market Condition Review (paper)

## Daily Summary
- total detected: 749
- traded: 0
- non-traded: 749
- TRADED_WIN: 0
- TRADED_LOSS: 0
- MISSED_OPPORTUNITY: 42
- GOOD_REJECT: 184
- DATA_QUALITY_BLOCK: 81
- TIME_POLICY_BLOCK: 300
- ORDER_GUARD_BLOCK: 142
- win rate: missing
- realized pnl: missing
- mode: paper
- generated_at: 2026-05-19 20:56:59

## Data Source Status
| source | status | path | data_rows | valid_rows | invalid_rows | missing_columns |
|---|---|---|---:|---:|---:|---|
| sector_map | ok | data/sector_map.csv | 4277 | 4277 | 0 | ok |
| theme_map | ok | data/theme_map.csv | 909 | 909 | 0 | ok |

## Daily Buy Gate Funnel
| metric | value |
|---|---:|
| raw_detected | 749 |
| unique_detected_symbols | 120 |
| registered_candidates | 79 |
| analysis_only_candidates | 307 |
| momentum_evaluated | 224 |
| final_decision_emitted | 224 |
| baseline_buy_allowed | 58 |
| baseline_buy_allowed_unique_candidates | 8 |
| relaxed_pullback_signal_rows | 218 |
| order_attempted | 0 |
| order_filled | 0 |
| policy_row_count | 749 |

## Market/Sector/Theme Gates
| field | value | row_count | unique_symbol_count | missed_count | avg_mfe_pct |
|---|---|---:|---:|---:|---:|
| symbol_market | KOSDAQ | 289 | 49 | 152 | +7.82% |
| symbol_market | KOSPI | 168 | 27 | 11 | +2.52% |
| primary_index_code | 101 | 139 | 26 | 59 | +5.29% |
| primary_index_code | 001 | 84 | 17 | 3 | +1.96% |
| primary_market_regime | neutral | 85 | 18 | 2 | +2.70% |
| primary_market_regime | strong | 65 | 9 | 47 | +5.21% |
| primary_market_regime | risk_off | 41 | 8 | 12 | +6.62% |
| primary_market_regime | weak | 32 | 9 | 1 | +1.89% |
| primary_market_pct | 0.007469654528478031 | 33 | 8 | 15 | +4.15% |
| primary_market_pct | 0.00933706816059754 | 32 | 1 | 32 | +6.30% |
| primary_market_pct | 0.0018001800180018623 | 21 | 2 | 0 | +4.35% |
| primary_market_pct | 0.006535947712418277 | 13 | 1 | 0 | -0.05% |
| primary_market_pct | 0.004277041942604809 | 12 | 1 | 0 | +1.46% |
| primary_market_pct | -0.00990099009900991 | 10 | 2 | 0 | +2.20% |
| primary_market_pct | -0.019393939393939408 | 10 | 1 | 0 | -0.17% |
| primary_market_pct | -0.008619528619528638 | 9 | 2 | 0 | +0.82% |
| primary_market_pct | -0.018585858585858595 | 8 | 1 | 0 | +0.17% |
| primary_market_pct | -0.027902790279027867 | 8 | 1 | 8 | +25.91% |
| primary_market_pct | -0.022895622895622858 | 7 | 1 | 0 | +3.48% |
| primary_market_pct | 0.0009427609427610228 | 7 | 1 | 0 | +0.71% |
| primary_market_pct | -0.004500450045004545 | 6 | 3 | 0 | +1.81% |
| primary_market_pct | 0.00040404040404040664 | 6 | 1 | 0 | +1.90% |
| primary_market_pct | -0.0016161616161616266 | 5 | 1 | 0 | +1.64% |
| primary_market_pct | -0.00848484848484854 | 5 | 1 | 0 | +0.35% |
| primary_market_pct | -0.009427609427609451 | 4 | 1 | 0 | +1.91% |
| primary_market_pct | -0.02970297029702973 | 4 | 1 | 4 | +9.22% |
| primary_market_pct | 0.004552980132450424 | 3 | 1 | 0 | +3.47% |
| primary_market_pct | -0.0009337068160597539 | 2 | 1 | 0 | +2.02% |
| primary_market_pct | -0.0018001800180017513 | 2 | 1 | 0 | +4.63% |
| primary_market_pct | -0.003232323232323253 | 2 | 1 | 2 | +23.92% |
| primary_market_pct | -0.007946127946127923 | 2 | 1 | 0 | +2.15% |
| primary_market_pct | -0.022502250225022502 | 2 | 1 | 0 | +0.00% |
| primary_market_pct | -0.0002759381898455038 | 1 | 1 | 0 | +1.00% |
| primary_market_pct | -0.00592592592592589 | 1 | 1 | 0 | +0.54% |
| primary_market_pct | -0.012601260126012592 | 1 | 1 | 0 | +2.75% |
| primary_market_pct | -0.013333333333333308 | 1 | 1 | 1 | +16.93% |
| primary_market_pct | -0.03060306030603055 | 1 | 1 | 0 | +0.65% |
| primary_market_pct | 0.0023454746136866156 | 1 | 1 | 0 | +0.66% |
| primary_market_pct | 0.00466853408029877 | 1 | 1 | 0 | +2.91% |
| primary_market_slope_1m | 0.001789154968345752 | 12 | 1 | 0 | +1.46% |
| primary_market_slope_1m | -0.0004073872895166142 | 9 | 2 | 0 | +0.82% |
| primary_market_slope_1m | -0.0009250693802035359 | 8 | 1 | 8 | +25.91% |
| primary_market_slope_1m | -0.0004034969737727323 | 7 | 1 | 0 | +0.71% |
| primary_market_slope_1m | -0.0012389867841409163 | 7 | 1 | 0 | +3.48% |
| primary_market_slope_1m | 0.0018214936247722413 | 7 | 1 | 0 | +1.20% |
| primary_market_slope_1m | -0.000941492938802968 | 6 | 1 | 0 | +1.90% |
| primary_market_slope_1m | -0.000949925363007198 | 5 | 1 | 0 | +0.35% |
| primary_market_slope_1m | 0.000945179584120881 | 5 | 1 | 0 | +1.64% |
| primary_market_slope_1m | -0.000926784059314234 | 4 | 1 | 4 | +9.22% |
| primary_market_slope_1m | -0.0012221618685497315 | 4 | 1 | 0 | +1.91% |
| primary_market_slope_1m | 0.0008992805755396738 | 4 | 1 | 0 | +2.45% |
| primary_market_slope_1m | -0.0027198549410698547 | 3 | 1 | 0 | +4.53% |
| primary_market_slope_1m | -0.0009009009009008917 | 2 | 1 | 0 | +4.63% |
| primary_market_slope_1m | -0.0016264570344266538 | 2 | 1 | 0 | +2.15% |
| primary_market_slope_1m | -0.00013798813302057233 | 1 | 1 | 0 | +1.00% |
| primary_market_slope_1m | -0.000412768299394628 | 1 | 1 | 0 | +0.66% |
| primary_market_slope_1m | -0.0005457025920873049 | 1 | 1 | 1 | +16.93% |
| primary_market_slope_1m | -0.000676956404007556 | 1 | 1 | 0 | +0.54% |
| primary_market_slope_1m | -0.0009276437847866026 | 1 | 1 | 0 | +0.65% |
| primary_market_slope_1m | -0.0018198362147406888 | 1 | 1 | 0 | +2.75% |
| primary_market_slope_1m | 0.0018621973929235924 | 1 | 1 | 0 | +2.91% |
| primary_market_slope_3m | 0.002782931354359919 | 32 | 1 | 32 | +6.30% |
| primary_market_slope_3m | 0.0009276437847867136 | 21 | 7 | 3 | +3.27% |
| primary_market_slope_3m | -0.000926784059314234 | 17 | 2 | 4 | +2.13% |
| primary_market_slope_3m | 0.0008992805755396738 | 17 | 1 | 0 | +4.80% |
| primary_market_slope_3m | 0.003308063404548589 | 12 | 1 | 0 | +1.46% |
| primary_market_slope_3m | -0.0009604829857299269 | 10 | 1 | 0 | -0.17% |
| primary_market_slope_3m | -0.0016275600162756199 | 9 | 2 | 0 | +0.82% |
| primary_market_slope_3m | -0.0005486215882595236 | 8 | 1 | 0 | +0.17% |
| primary_market_slope_3m | -0.0036900369003689537 | 8 | 1 | 8 | +25.91% |
| primary_market_slope_3m | 0.0009099181073703999 | 7 | 1 | 0 | +1.20% |
| primary_market_slope_3m | 0.0011039050641645787 | 7 | 1 | 0 | +3.48% |
| primary_market_slope_3m | 0.0012124477973864956 | 7 | 1 | 0 | +0.71% |
| primary_market_slope_3m | -0.0018050541516245744 | 6 | 3 | 0 | +1.81% |
| primary_market_slope_3m | 0.0006735821096590655 | 6 | 1 | 0 | +1.90% |
| primary_market_slope_3m | -0.0008143322475570036 | 5 | 1 | 0 | +0.35% |
| primary_market_slope_3m | -0.0012126111560226693 | 5 | 1 | 0 | +1.64% |
| primary_market_slope_3m | -0.00244134002441343 | 4 | 1 | 0 | +1.91% |
| primary_market_slope_3m | 0.002702702702702675 | 4 | 1 | 0 | +2.45% |
| primary_market_slope_3m | -0.001814882032667886 | 3 | 1 | 0 | +4.53% |
| primary_market_slope_3m | 0.0009345794392523477 | 3 | 1 | 0 | +3.30% |
| primary_market_slope_3m | 0.003860471529022469 | 3 | 1 | 0 | +3.47% |
| primary_market_slope_3m | -0.0009009009009008917 | 2 | 1 | 0 | +4.63% |
| primary_market_slope_3m | -0.0009449244060475426 | 2 | 1 | 2 | +23.92% |
| primary_market_slope_3m | -0.0009494100094941116 | 2 | 1 | 0 | +2.15% |
| primary_market_slope_3m | -0.0018382352941176405 | 2 | 1 | 0 | +0.00% |
| primary_market_slope_3m | -0.00013762730525734845 | 1 | 1 | 0 | +0.66% |
| primary_market_slope_3m | -0.0018198362147406888 | 1 | 1 | 0 | +2.75% |
| primary_market_slope_3m | -0.001853568118628357 | 1 | 1 | 0 | +0.65% |
| primary_market_slope_3m | -0.0018931710615280872 | 1 | 1 | 0 | +0.54% |
| primary_market_slope_3m | -0.002858309514087387 | 1 | 1 | 1 | +16.93% |
| primary_market_slope_3m | 0.002795899347623587 | 1 | 1 | 0 | +2.91% |
| primary_market_slope_3m | 0.0029065743944636235 | 1 | 1 | 0 | +1.00% |
| primary_market_drawdown_from_high | -0.0018501387604070718 | 33 | 8 | 15 | +4.15% |
| primary_market_drawdown_from_high | -0.008021390374331583 | 21 | 2 | 0 | +4.35% |
| primary_market_drawdown_from_high | -0.0027752081406104967 | 13 | 1 | 0 | -0.05% |
| primary_market_drawdown_from_high | -0.008985704560925845 | 12 | 1 | 0 | +1.46% |
| primary_market_drawdown_from_high | -0.019607843137254943 | 10 | 2 | 0 | +2.20% |
| primary_market_drawdown_from_high | -0.02215954875100723 | 10 | 1 | 0 | -0.17% |
| primary_market_drawdown_from_high | -0.011415525114155223 | 9 | 2 | 0 | +0.82% |
| primary_market_drawdown_from_high | -0.021353746978243326 | 8 | 1 | 0 | +0.17% |
| primary_market_drawdown_from_high | -0.03743315508021394 | 8 | 1 | 8 | +25.91% |
| primary_market_drawdown_from_high | -0.0018802041364490707 | 7 | 1 | 0 | +0.71% |
| primary_market_drawdown_from_high | -0.025651356432984107 | 7 | 1 | 0 | +3.48% |
| primary_market_drawdown_from_high | -0.00241740531829171 | 6 | 1 | 0 | +1.90% |
| primary_market_drawdown_from_high | -0.014260249554367221 | 6 | 3 | 0 | +1.81% |
| primary_market_drawdown_from_high | -0.004431909750201468 | 5 | 1 | 0 | +1.64% |
| primary_market_drawdown_from_high | -0.011281224818694646 | 5 | 1 | 0 | +0.35% |
| primary_market_drawdown_from_high | -0.012221326886919126 | 4 | 1 | 0 | +1.91% |
| primary_market_drawdown_from_high | -0.039215686274509776 | 4 | 1 | 4 | +9.22% |
| primary_market_drawdown_from_high | -0.008333333333333304 | 3 | 1 | 0 | +3.30% |
| primary_market_drawdown_from_high | -0.00871341048332197 | 3 | 1 | 0 | +3.47% |
| primary_market_drawdown_from_high | -0.006043513295729275 | 2 | 1 | 2 | +23.92% |
| primary_market_drawdown_from_high | -0.0092592592592593 | 2 | 1 | 0 | +2.02% |
| primary_market_drawdown_from_high | -0.010744023636852007 | 2 | 1 | 0 | +2.15% |
| primary_market_drawdown_from_high | -0.01158645276292336 | 2 | 1 | 0 | +4.63% |
| primary_market_drawdown_from_high | -0.03208556149732622 | 2 | 1 | 0 | +0.00% |
| primary_market_drawdown_from_high | -0.0037037037037036535 | 1 | 1 | 0 | +2.91% |
| primary_market_drawdown_from_high | -0.008729519204942249 | 1 | 1 | 0 | +0.54% |
| primary_market_drawdown_from_high | -0.010891763104152519 | 1 | 1 | 0 | +0.66% |
| primary_market_drawdown_from_high | -0.013478556841388656 | 1 | 1 | 0 | +1.00% |
| primary_market_drawdown_from_high | -0.016116035455277955 | 1 | 1 | 1 | +16.93% |
| primary_market_drawdown_from_high | -0.022281639928698804 | 1 | 1 | 0 | +2.75% |
| primary_market_drawdown_from_high | -0.0401069518716578 | 1 | 1 | 0 | +0.65% |
| kospi_regime | neutral | 112 | 23 | 17 | +3.18% |
| kospi_regime | risk_off | 40 | 7 | 12 | +6.72% |
| kospi_regime | weak | 39 | 13 | 1 | +1.90% |
| kospi_regime | strong | 32 | 1 | 32 | +6.30% |
| kosdaq_regime | strong | 81 | 12 | 47 | +4.53% |
| kosdaq_regime | neutral | 70 | 16 | 2 | +2.88% |
| kosdaq_regime | risk_off | 60 | 13 | 13 | +5.09% |
| kosdaq_regime | weak | 12 | 3 | 0 | +2.19% |
| market_regime | neutral | 85 | 18 | 2 | +2.70% |
| market_regime | strong | 65 | 9 | 47 | +5.21% |
| market_regime | risk_off | 41 | 8 | 12 | +6.62% |
| market_regime | weak | 32 | 9 | 1 | +1.89% |
| sector_ranked_count | 0 | 142 | 14 | 118 | +10.47% |
| sector_regime | unknown | 223 | 43 | 62 | +4.04% |
| sector_gate_action | dry_run_allow | 223 | 43 | 62 | +4.04% |
| sector_gate_reason | SECTOR_UNKNOWN_FALLBACK | 223 | 43 | 62 | +4.04% |
| theme_member_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_active_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_rising_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_falling_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_top_turnover | 0 | 142 | 14 | 118 | +10.47% |
| theme_regime | unknown | 223 | 43 | 62 | +4.04% |
| theme_gate_action | dry_run_allow | 223 | 43 | 62 | +4.04% |
| theme_gate_reason | THEME_UNKNOWN_FALLBACK | 223 | 43 | 62 | +4.04% |

## Reason Counts by Unique Symbol
| reason | row_count | unique_symbol_count | avg_mfe_pct | missed_count |
|---|---:|---:|---:|---:|
| TIME_POLICY_ANALYSIS_ONLY | 297 | 63 | +3.11% | 13 |
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 140 | 32 | +2.61% | 17 |
| missing | 136 | 26 | +6.88% | 25 |
| max_position_size_exceeded | 90 | 9 | +11.11% | 73 |
| FINAL_PAPER_ONLY_STRATEGY | 37 | 3 | +6.07% | 32 |
| FINAL_BUY_READY | 20 | 4 | +14.27% | 13 |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 14 | 2 | -0.00% | 0 |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 6 | 1 | +1.90% | 0 |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 4 | 1 | +2.45% | 0 |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 2 | 1 | +2.15% | 0 |
| TIME_POLICY_PRE_MOMENTUM_BLOCK | 2 | 2 | missing | 0 |
| closing_strength_paper_only | 1 | 1 | +2715.00% | 1 |

## Recovery Watch
- recovery_watch_rows: 217
- recovery_watch_unique_candidates: 43
- recovery_watch_unique_symbols: 42
- recovery_watch_missed_count: 62
- recovery_watch_avg_mfe_pct: +4.10%

| reason | row_count | unique_symbol_count | missed_count | avg_mfe_pct |
|---|---:|---:|---:|---:|
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 201 | 38 | 61 | +4.10% |
| FINAL_MOMENTUM_REJECT_SPREAD | 60 | 5 | 45 | +4.93% |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 59 | 7 | 36 | +4.52% |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 48 | 6 | 32 | +5.38% |
| FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 44 | 9 | 13 | +6.47% |

| symbol | name | detected_at | reason_code | recovery_reason | delay_sec | MFE | MAE | category |
|---|---|---|---|---|---:|---:|---:|---|
| 439960 | 코스모로보틱스 | 2026-05-19 10:01:05 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | -1.17% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:13:49 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:13:53 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:00 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:01 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:20 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:21 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:30 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 005500 | 삼진제약 | 2026-05-19 09:07:59 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 60 | +23.92% | -1.20% | MISSED_OPPORTUNITY |
| 005500 | 삼진제약 | 2026-05-19 09:07:59 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 60 | +23.92% | -1.20% | MISSED_OPPORTUNITY |
| 005500 | 삼진제약 | 2026-05-19 09:47:29 | FINAL_BUY_READY | FINAL_MOMENTUM_REJECT_SPREAD;FINAL_MOMENTUM_WEAK_VOLUME_RATIO | 15 | +16.93% | -4.29% | ORDER_GUARD_BLOCK |
| 086960 | MDS테크 | 2026-05-19 10:12:50 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW;FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FI... | 15 | +9.22% | -3.07% | ORDER_GUARD_BLOCK |
| 086960 | MDS테크 | 2026-05-19 10:12:50 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW;FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FI... | 15 | +9.22% | -3.07% | ORDER_GUARD_BLOCK |
| 086960 | MDS테크 | 2026-05-19 10:15:33 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW;FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FI... | 15 | +9.22% | -3.07% | ORDER_GUARD_BLOCK |
| 086960 | MDS테크 | 2026-05-19 10:15:33 | FINAL_BUY_READY | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW;FINAL_MOMENTUM_BLOCK_WEAK_LEADER;FI... | 15 | +9.22% | -3.07% | ORDER_GUARD_BLOCK |
| 083500 | 에프엔에스테크 | 2026-05-19 14:18:57 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 60 | +6.64% | -1.18% | MISSED_OPPORTUNITY |
| 083500 | 에프엔에스테크 | 2026-05-19 14:19:00 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 60 | +6.64% | -0.95% | MISSED_OPPORTUNITY |
| 083500 | 에프엔에스테크 | 2026-05-19 14:19:10 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 60 | +6.64% | -0.95% | MISSED_OPPORTUNITY |
| 033160 | 엠케이전자 | 2026-05-19 13:52:09 | FINAL_PAPER_ONLY_STRATEGY | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW;FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_... | 10 | +6.30% | -2.75% | ORDER_GUARD_BLOCK |
| 033160 | 엠케이전자 | 2026-05-19 13:53:00 | FINAL_PAPER_ONLY_STRATEGY | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW;FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_... | 10 | +6.30% | -2.75% | ORDER_GUARD_BLOCK |

## Trade Results
- no traded candidates

## Exit Type Performance
- no traded candidates

## Non-Traded Review
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:24 | 191500 | missing | missing | missing | +4.07% | -12.01% | GOOD_REJECT |
| 006340 | 대원전선 | 2026-05-19 09:00:26 | 15390 | missing | missing | missing | +6.89% | -9.55% | MISSED_OPPORTUNITY |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:31 | 26800 | missing | missing | max_position_size_exceeded | +22.95% | -2.61% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:31 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 356680 | 엑스게이트 | 2026-05-19 09:00:33 | 16760 | missing | missing | missing | +15.93% | -4.18% | MISSED_OPPORTUNITY |
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:38 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | 38850 | missing | Analysis-only condition capture by TimePolicy ALLOW_CANDIDATE_CAPTURE | TIME_POLICY_ANALYSIS_ONLY | +2.06% | -2.83% | TIME_POLICY_BLOCK |
| 006340 | 대원전선 | 2026-05-19 09:00:40 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:00:42 | 2765 | missing | missing | missing | +7.41% | -11.03% | MISSED_OPPORTUNITY |
| 321370 | 센서뷰 | 2026-05-19 09:00:47 | 3940 | missing | missing | missing | +10.15% | -6.09% | MISSED_OPPORTUNITY |
| 006340 | 대원전선 | 2026-05-19 09:00:48 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 006340 | 대원전선 | 2026-05-19 09:00:49 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:00:51 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 178320 | 서진시스템 | 2026-05-19 09:00:52 | 73700 | missing | missing | missing | +0.41% | -6.24% | GOOD_REJECT |
| 003280 | 흥아해운 | 2026-05-19 09:00:54 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:00:57 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:08 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | 29850 | missing | Analysis-only condition capture by TimePolicy ALLOW_CANDIDATE_CAPTURE | TIME_POLICY_ANALYSIS_ONLY | +1.34% | -10.05% | TIME_POLICY_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:12 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:01:20 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:01:25 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:01:27 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:28 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:29 | missing | missing | missing | missing | missing | missing | DATA_QUALITY_BLOCK |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:31 | 4215 | missing | missing | missing | +20.52% | -13.29% | MISSED_OPPORTUNITY |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:33 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |

## Missed Opportunities
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 005930 | 삼성전자 | 2026-05-19 14:29:33 | 10000 | BUY | closing strength paper-only | closing_strength_paper_only | +2715.00% | +2655.00% | TIME_POLICY_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:01:05 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | -1.17% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:13:49 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:13:53 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:00 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:01 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:20 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:21 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 439960 | 코스모로보틱스 | 2026-05-19 10:14:30 | 38600 | BUY | Momentum BUY and pullback/strength filters passed | FINAL_BUY_READY | +25.91% | +3.24% | ORDER_GUARD_BLOCK |
| 005500 | 삼진제약 | 2026-05-19 09:07:59 | 20900 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 39.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +23.92% | -1.20% | MISSED_OPPORTUNITY |
| 005500 | 삼진제약 | 2026-05-19 09:07:59 | 20900 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 39.1 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +23.92% | -1.20% | MISSED_OPPORTUNITY |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:31 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:08 | 26750 | missing | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |

## Good Rejects
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:24 | 191500 | missing | missing | missing | +4.07% | -12.01% | GOOD_REJECT |
| 178320 | 서진시스템 | 2026-05-19 09:00:52 | 73700 | missing | missing | missing | +0.41% | -6.24% | GOOD_REJECT |
| 028050 | 삼성E&A | 2026-05-19 09:01:37 | 49900 | missing | missing | missing | +1.20% | -4.71% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-19 09:01:56 | 378000 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +2.65% | -5.95% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-19 09:01:57 | 378000 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +2.65% | -5.95% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:09 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:11 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 042660 | 한화오션 | 2026-05-19 09:02:17 | 118700 | missing | missing | missing | +0.42% | -6.49% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:17 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:21 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 007610 | 선도전기 | 2026-05-19 09:02:24 | 10410 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 43.9 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +1.54% | -13.54% | GOOD_REJECT |
| 007610 | 선도전기 | 2026-05-19 09:02:24 | 10410 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 43.9 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +1.54% | -13.54% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:37 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:38 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 036540 | SFA반도체 | 2026-05-19 09:02:39 | 8720 | missing | missing | missing | +0.80% | -12.61% | GOOD_REJECT |

## Block Chase Review
- none

## Data Quality Blocks
| symbol | name | category | reason_code | MFE | MAE | close return | data_quality |
|---|---|---|---|---:|---:|---:|---|
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOLUME_RATIO;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOLUME_RATIO;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOLUME_RATIO;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +22.95% | -2.61% | +6.16% | MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOLUME_RATIO;partial_data |
| 066430 | 아이로보틱스 | MISSED_OPPORTUNITY | missing | +20.52% | -13.29% | +1.90% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | MISSED_OPPORTUNITY | missing | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | MISSED_OPPORTUNITY | missing | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | MISSED_OPPORTUNITY | missing | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |

| data_quality | count | avg_mfe_pct | n_mfe | missing_mfe |
|---|---:|---:|---:|---:|
| MISSING_SPREAD_RATE | 525 | +7.43% | 215 | 310 |
| MISSING_TRADE_STRENGTH | 525 | +7.43% | 215 | 310 |
| partial_data | 525 | +7.43% | 215 | 310 |
| MISSING_DECISION_TRACE | 435 | +4.77% | 125 | 310 |
| MISSING_CAPTURE_PRICE | 310 | missing | 0 | 310 |
| MISSING_MFE_MAE | 310 | missing | 0 | 310 |
| MISSING_VOLUME_RATIO | 19 | +12.67% | 11 | 8 |

## Missing Decision Trace Detail
| symbol | name | detected_at | candidate_id | role | reason_code | time_policy | source | stage | data_quality |
|---|---|---|---|---|---|---|---|---|---|
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:24 | 0363f3b95d514604bca88f935c7e1439 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 006340 | 대원전선 | 2026-05-19 09:00:26 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 356680 | 엑스게이트 | 2026-05-19 09:00:33 | 11fa203843644d838b3781065f973974 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:38 | 0363f3b95d514604bca88f935c7e1439 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:00:40 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | 3ca39d9805d34d549c4be9775d799a71 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | missing | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | 3ca39d9805d34d549c4be9775d799a71 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:00:42 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 321370 | 센서뷰 | 2026-05-19 09:00:47 | cdd7950fa4424c0f85a74f8e7814336e | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 006340 | 대원전선 | 2026-05-19 09:00:48 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:00:49 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:00:51 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 178320 | 서진시스템 | 2026-05-19 09:00:52 | c84728762d124b50b56e976747a09438 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 003280 | 흥아해운 | 2026-05-19 09:00:54 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:00:57 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | 6e1a1ee8d56f4dd480a395381a508320 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | missing | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | 6e1a1ee8d56f4dd480a395381a508320 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:01:20 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:01:25 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:01:27 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:28 | 6e1a1ee8d56f4dd480a395381a508320 | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:29 | 6e1a1ee8d56f4dd480a395381a508320 | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:31 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 006340 | 대원전선 | 2026-05-19 09:01:37 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:01:37 | 22ab90f2a27f4380bd606a0792024006 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:39 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:01:40 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:40 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:41 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:01:42 | 22ab90f2a27f4380bd606a0792024006 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:43 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:51 | 6e1a1ee8d56f4dd480a395381a508320 | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:52 | 6e1a1ee8d56f4dd480a395381a508320 | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:01:57 | 22ab90f2a27f4380bd606a0792024006 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:02:04 | 6e1a1ee8d56f4dd480a395381a508320 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:02:05 | 22ab90f2a27f4380bd606a0792024006 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:02:05 | 0363f3b95d514604bca88f935c7e1439 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:09 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:02:09 | 0363f3b95d514604bca88f935c7e1439 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:02:10 | 0363f3b95d514604bca88f935c7e1439 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:12 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:16 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 440110 | 파두 | 2026-05-19 09:02:16 | 11dafcfc6be24f9c9a011215848d3a12 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 440110 | 파두 | 2026-05-19 09:02:16 | 11dafcfc6be24f9c9a011215848d3a12 | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 042660 | 한화오션 | 2026-05-19 09:02:17 | 10b839b90d244f86b9fa622306826745 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 003280 | 흥아해운 | 2026-05-19 09:02:18 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:20 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:22 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:02:27 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | missing | ALLOW_CANDIDATE_CAPTURE | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:31 | c241d9dbb686495ba1c11f5a41c0330e | trading | missing | BONUS_CONDITION_AFTER_PRIMARY | missing | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |

## Data Quality High MFE
- none

## Time Policy Blocks
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 005930 | 삼성전자 | TIME_POLICY_BLOCK | closing_strength_paper_only | +2715.00% | +2655.00% | +2655.00% |
| 078890 | 가온그룹 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +19.02% | -3.85% | +12.02% |
| 243070 | 휴온스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +14.64% | -4.83% | +5.52% |
| 142280 | 녹십자엠에스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +13.78% | -3.44% | +8.00% |
| 142280 | 녹십자엠에스 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +13.78% | -0.22% | +8.00% |
| 900300 | 오가닉티코스메틱 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +12.82% | -6.84% | -4.27% |
| 000370 | 한화손해보험 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.90% | -2.01% | +2.41% |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.58% | -17.05% | -16.19% |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.58% | -17.05% | -16.19% |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.58% | -17.05% | -16.19% |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.58% | -17.05% | -16.19% |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.58% | -17.05% | -16.19% |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.58% | -17.05% | -16.19% |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +7.58% | -17.05% | -16.19% |
| 052900 | KX하이텍 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.98% | -3.58% | +3.03% |
| 052900 | KX하이텍 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.98% | -2.91% | +3.03% |
| 046970 | 우리로 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +4.46% | -10.09% | -7.98% |
| 039980 | 폴라리스AI | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +3.87% | -11.27% | -8.84% |
| 039980 | 폴라리스AI | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +3.87% | -11.27% | -8.84% |
| 052900 | KX하이텍 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +3.10% | -4.11% | +1.19% |

## OrderGuard Blocks
| symbol | name | category | reason_code | MFE | MAE | close return |
|---|---|---|---|---:|---:|---:|
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | -1.17% | +25.91% |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | +3.24% | +25.91% |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | +3.24% | +25.91% |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | +3.24% | +25.91% |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | +3.24% | +25.91% |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | +3.24% | +25.91% |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | +3.24% | +25.91% |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | FINAL_BUY_READY | +25.91% | +3.24% | +25.91% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | max_position_size_exceeded | +23.18% | -2.43% | +6.36% |

## Reason Code Ranking
| reason_code | count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae | missing_mfe | missing_mae | missed_opportunity_count | missed_opportunity_rate | good_reject_count | good_reject_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TIME_POLICY_ANALYSIS_ONLY | 297 | +3.11% | -7.01% | 70 | 70 | 227 | 227 | 13 | 4.38% | 0 | 0.00% |
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 140 | +2.61% | -6.74% | 140 | 140 | 0 | 0 | 17 | 12.14% | 123 | 87.86% |
| missing | 136 | +6.88% | -9.07% | 55 | 55 | 81 | 81 | 25 | 18.38% | 30 | 22.06% |
| max_position_size_exceeded | 90 | +11.11% | -4.42% | 90 | 90 | 0 | 0 | 73 | 81.11% | 0 | 0.00% |
| FINAL_PAPER_ONLY_STRATEGY | 37 | +6.07% | -0.90% | 37 | 37 | 0 | 0 | 32 | 86.49% | 5 | 13.51% |
| FINAL_BUY_READY | 20 | +14.27% | -4.75% | 20 | 20 | 0 | 0 | 13 | 65.00% | 0 | 0.00% |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 14 | -0.00% | -6.64% | 14 | 14 | 0 | 0 | 0 | 0.00% | 14 | 100.00% |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 6 | +1.90% | -2.66% | 6 | 6 | 0 | 0 | 0 | 0.00% | 6 | 100.00% |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 4 | +2.45% | -5.95% | 4 | 4 | 0 | 0 | 0 | 0.00% | 4 | 100.00% |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 2 | +2.15% | -3.50% | 2 | 2 | 0 | 0 | 0 | 0.00% | 2 | 100.00% |
| TIME_POLICY_PRE_MOMENTUM_BLOCK | 2 | missing | missing | 0 | 0 | 2 | 2 | 0 | 0.00% | 0 | 0.00% |
| closing_strength_paper_only | 1 | +2715.00% | +2655.00% | 1 | 1 | 0 | 0 | 1 | 100.00% | 0 | 0.00% |

## Relaxed Pullback Dry Run
| policy | candidate_rows | unique_symbols | pullback_signal_rows | non_traded_signal_rows | top_signal_block_reason |
|---|---:|---:|---:|---:|---|
| pullback >= 0.5% | 749 | 41 | 218 | 218 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 0.8% | 749 | 38 | 209 | 209 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 1.0% | 749 | 38 | 209 | 209 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 1.5% | 749 | 34 | 189 | 189 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |

- pullback_signal_rows only means the relaxed pullback threshold passed; it is not a full buy-gate allowed count.

## Would Buy Comparison
| policy | row_count | unique_symbol_count | traded_count | top_reason |
|---|---:|---:|---:|---|
| baseline | 58 | 8 | 0 | FINAL_PAPER_ONLY_STRATEGY |
| pullback_0p5_signal | 218 | 41 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_0p8_signal | 209 | 38 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_1p0_signal | 209 | 38 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_1p5_signal | 189 | 34 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| breakout_small_trace | 0 | 0 | 0 | missing |
| pullback_reclaim_vwap | 20 | 4 | 0 | FINAL_BUY_READY |

- pullback_*_signal is a relaxed pullback signal count, not a full buy-gate pass count.

## Weak Volume Ratio MFE
- none

## Reconciliation
- post_market raw detected rows: 749
- post_market unique symbols: 120
- post_market unique candidate_ids: 96
- baseline full-gate buy/order rows: 58
- relaxed pullback 0.5% signal rows: 218
- entry_gate_dry_run groups condition captures by symbol and then expands policy rows, while post_market keeps raw condition detections. Compare unique_symbol_count with raw_detected before tuning.
- previous relaxed pullback would_buy_count meant pullback-threshold signal only. It is now reported as signal rows to avoid implying that VWAP, volume, time policy, and order guard also passed.

## Time Bucket Analysis
| time_bucket | capture_count | strategy_candidate_count | paper_only_count | traded_count | non_traded_count | missed_opportunity_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09:00~09:30 | 315 | 2 | 2 | 0 | 315 | 103 | 106 | +7.05% | -7.25% | 234 | 234 |
| 09:30~10:30 | 47 | 3 | 3 | 0 | 47 | 13 | 24 | +6.56% | -7.28% | 47 | 47 |
| 10:30~13:00 | 132 | 0 | 0 | 0 | 132 | 3 | 0 | +3.23% | -6.62% | 29 | 29 |
| 13:00~14:20 | 100 | 32 | 32 | 0 | 100 | 45 | 54 | +3.77% | -2.09% | 99 | 99 |
| 14:20 이후 | 155 | 1 | 1 | 0 | 155 | 10 | 0 | +92.92% | +83.12% | 30 | 30 |

## Paper Strategy Performance
| strategy_type | candidate_count | paper_only_count | traded_count | missed_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AFTERNOON_SECOND_WAVE | 32 | 32 | 0 | 32 | 0 | +6.30% | -0.06% | 32 | 32 |
| CLOSING_STRENGTH | 1 | 1 | 0 | 1 | 0 | +2715.00% | +2655.00% | 1 | 1 |
| TREND_CONTINUATION | 5 | 5 | 0 | 0 | 5 | +4.57% | -6.28% | 5 | 5 |

## Parameter Tuning Hints
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