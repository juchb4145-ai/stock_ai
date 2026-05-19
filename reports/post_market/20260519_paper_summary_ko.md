# 2026-05-19 장마감 조건검색 리뷰 (paper)

## 일일 요약
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
- win rate: 없음
- realized pnl: 없음
- mode: paper
- generated_at: 2026-05-19 22:39:25

## 데이터 소스 상태
| 소스 | 상태 | 경로 | 데이터 행 | 유효 행 | 무효 행 | 누락 컬럼 |
|---|---|---|---:|---:|---:|---|
| sector_map | 정상 | data/sector_map.csv | 4277 | 4277 | 0 | 정상 |
| theme_map | 정상 | data/theme_map.csv | 909 | 909 | 0 | 정상 |

## 일일 매수 게이트 퍼널
| 지표 | 값 |
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

## 시장/업종/테마 게이트
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
| sector_code | 전기전자 | 178 | 26 | 85 | +25.98% |
| sector_code | 운송창고 | 79 | 5 | 1 | +1.90% |
| sector_code | 제약 | 72 | 12 | 12 | +6.59% |
| sector_code | 일반서비스 | 64 | 13 | 0 | +2.55% |
| sector_code | 화학 | 63 | 7 | 5 | +2.04% |
| sector_code | 금융 | 52 | 7 | 21 | +5.95% |
| sector_code | 기계장비 | 43 | 7 | 3 | +1.52% |
| sector_code | IT_서비스 | 34 | 9 | 12 | +5.89% |
| sector_code | 운송장비부품 | 31 | 5 | 23 | +15.46% |
| sector_code | unknown | 26 | 1 | 1 | +12.82% |
| sector_code | 보험 | 26 | 4 | 2 | +4.17% |
| sector_code | 금속 | 24 | 6 | 0 | +2.94% |
| sector_code | 의료정밀기기 | 17 | 7 | 8 | +19.39% |
| sector_code | 유통 | 14 | 5 | 1 | +5.15% |
| sector_code | 오락문화 | 13 | 3 | 0 | 없음 |
| sector_code | 건설 | 7 | 1 | 0 | +1.34% |
| sector_code | 전기가스 | 4 | 1 | 0 | +2.06% |
| sector_code | 음식료담배 | 2 | 1 | 0 | +1.53% |
| sector_name | 전기/전자 | 178 | 26 | 85 | +25.98% |
| sector_name | 운송/창고 | 79 | 5 | 1 | +1.90% |
| sector_name | 제약 | 72 | 12 | 12 | +6.59% |
| sector_name | 일반서비스 | 64 | 13 | 0 | +2.55% |
| sector_name | 화학 | 63 | 7 | 5 | +2.04% |
| sector_name | 금융 | 52 | 7 | 21 | +5.95% |
| sector_name | 기계/장비 | 43 | 7 | 3 | +1.52% |
| sector_name | IT 서비스 | 34 | 9 | 12 | +5.89% |
| sector_name | 운송장비/부품 | 31 | 5 | 23 | +15.46% |
| sector_name | 보험 | 26 | 4 | 2 | +4.17% |
| sector_name | 금속 | 24 | 6 | 0 | +2.94% |
| sector_name | 의료/정밀기기 | 17 | 7 | 8 | +19.39% |
| sector_name | 유통 | 14 | 5 | 1 | +5.15% |
| sector_name | 오락/문화 | 13 | 3 | 0 | 없음 |
| sector_name | 건설 | 7 | 1 | 0 | +1.34% |
| sector_name | 전기/가스 | 4 | 1 | 0 | +2.06% |
| sector_name | 음식료/담배 | 2 | 1 | 0 | +1.53% |
| sector_index_code | KOSDAQ:전기전자 | 158 | 21 | 79 | +6.09% |
| sector_index_code | KOSPI:운송창고 | 79 | 5 | 1 | +1.90% |
| sector_index_code | KOSDAQ:제약 | 66 | 10 | 9 | +5.14% |
| sector_index_code | KOSDAQ:화학 | 57 | 5 | 5 | +2.04% |
| sector_index_code | KOSDAQ:일반서비스 | 48 | 11 | 0 | +3.35% |
| sector_index_code | KOSDAQ:기계장비 | 43 | 7 | 3 | +1.52% |
| sector_index_code | KOSPI:금융 | 27 | 4 | 0 | +0.82% |
| sector_index_code | KOSDAQ:unknown | 26 | 1 | 1 | +12.82% |
| sector_index_code | KOSPI:보험 | 26 | 4 | 2 | +4.17% |
| sector_index_code | KOSDAQ:금융 | 25 | 3 | 21 | +11.28% |
| sector_index_code | KOSDAQ:운송장비부품 | 23 | 2 | 23 | +18.78% |
| sector_index_code | KOSDAQ:IT_서비스 | 21 | 6 | 5 | +7.41% |
| sector_index_code | KOSPI:금속 | 20 | 4 | 0 | +2.94% |
| sector_index_code | KOSPI:전기전자 | 20 | 5 | 6 | +196.47% |
| sector_index_code | KOSPI:일반서비스 | 16 | 2 | 0 | -0.05% |
| sector_index_code | KOSDAQ:의료정밀기기 | 14 | 5 | 8 | +23.15% |
| sector_index_code | KOSPI:IT_서비스 | 13 | 3 | 7 | +4.72% |
| sector_index_code | KOSDAQ:유통 | 9 | 3 | 1 | +7.74% |
| sector_index_code | KOSPI:운송장비부품 | 8 | 3 | 0 | +0.22% |
| sector_index_code | KOSPI:건설 | 7 | 1 | 0 | +1.34% |
| sector_index_code | KOSPI:오락문화 | 7 | 1 | 0 | 없음 |
| sector_index_code | KOSDAQ:오락문화 | 6 | 2 | 0 | 없음 |
| sector_index_code | KOSPI:제약 | 6 | 2 | 3 | +21.59% |
| sector_index_code | KOSPI:화학 | 6 | 2 | 0 | 없음 |
| sector_index_code | KOSPI:유통 | 5 | 2 | 0 | +1.91% |
| sector_index_code | KOSDAQ:금속 | 4 | 2 | 0 | 없음 |
| sector_index_code | KOSPI:전기가스 | 4 | 1 | 0 | +2.06% |
| sector_index_code | KOSPI:의료정밀기기 | 3 | 2 | 0 | +2.46% |
| sector_index_code | KOSDAQ:음식료담배 | 2 | 1 | 0 | +1.53% |
| sector_ranked_count | 0 | 142 | 14 | 118 | +10.47% |
| sector_regime | unknown | 223 | 43 | 62 | +4.04% |
| sector_gate_action | dry_run_allow | 223 | 43 | 62 | +4.04% |
| sector_gate_reason | SECTOR_UNKNOWN_FALLBACK | 223 | 43 | 62 | +4.04% |
| primary_theme | 운송_해운 | 71 | 3 | 1 | +2.65% |
| primary_theme | 반도체_후공정소재 | 34 | 1 | 34 | +6.65% |
| primary_theme | 바이오_진단/백신 | 20 | 2 | 0 | +2.08% |
| primary_theme | 보험_생명보험 | 15 | 1 | 0 | +4.58% |
| primary_theme | 강관 | 14 | 1 | 0 | +3.47% |
| primary_theme | 2차전지_소재(양극화물질등) | 12 | 1 | 0 | +1.46% |
| primary_theme | 네트워크/광통신 | 12 | 1 | 12 | +5.60% |
| primary_theme | AMOLED_장비 | 10 | 1 | 0 | +4.07% |
| primary_theme | 보험_손해보험 | 8 | 2 | 2 | +3.40% |
| primary_theme | 셋톱박스 | 8 | 1 | 8 | +19.02% |
| primary_theme | 우주항공 | 8 | 2 | 0 | +0.42% |
| primary_theme | 건설_국내주택 | 7 | 1 | 0 | +1.34% |
| primary_theme | 건설_해외건설 | 7 | 2 | 0 | +1.20% |
| primary_theme | 운송_항공 | 7 | 1 | 0 | +0.35% |
| primary_theme | 컨텐츠_음원 | 6 | 2 | 0 | 없음 |
| primary_theme | SNS(Social Network Service) | 5 | 1 | 0 | +1.64% |
| primary_theme | 반도체_전공정소재 | 5 | 1 | 5 | +5.04% |
| primary_theme | 반도체_후공정 | 5 | 1 | 0 | +0.69% |
| primary_theme | 반도체_설계(fabless) | 4 | 1 | 0 | +3.76% |
| primary_theme | 소프트웨어_자동차용 | 4 | 1 | 4 | +9.22% |
| primary_theme | 태양광_부품/소재/장비 | 4 | 1 | 0 | +0.55% |
| primary_theme | 방위산업 | 3 | 1 | 0 | +0.03% |
| primary_theme | 기계_공작기계 | 2 | 1 | 0 | 없음 |
| primary_theme | 무선충전기관련주 | 2 | 1 | 0 | +0.00% |
| primary_theme | 반도체_전공정장비 | 2 | 1 | 0 | 없음 |
| primary_theme | 배합사료 | 2 | 1 | 0 | +1.53% |
| primary_theme | 비철금속주 | 2 | 1 | 0 | 없음 |
| primary_theme | PCB(인쇄회로기판) | 1 | 1 | 0 | 없음 |
| primary_theme | 바이오_줄기세포치료제 | 1 | 1 | 0 | 없음 |
| primary_theme | 반도체_생산 | 1 | 1 | 1 | +2715.00% |
| primary_theme | 백화점 | 1 | 1 | 0 | 없음 |
| primary_theme | 조선_LNG보냉재 | 1 | 1 | 0 | +0.65% |
| theme_names | 운송_해운 | 71 | 3 | 1 | +2.65% |
| theme_names | 반도체_후공정소재 | 34 | 1 | 34 | +6.65% |
| theme_names | 바이오_진단/백신 | 17 | 1 | 0 | +2.08% |
| theme_names | 보험_생명보험 | 15 | 1 | 0 | +4.58% |
| theme_names | 강관 | 14 | 1 | 0 | +3.47% |
| theme_names | 2차전지_소재(양극화물질등);합성섬유_원료 | 12 | 1 | 0 | +1.46% |
| theme_names | 네트워크/광통신;통신장비 | 12 | 1 | 12 | +5.60% |
| theme_names | AMOLED_장비;LCD_장비;반도체_전공정장비;태양광_부품/소재/장비 | 10 | 1 | 0 | +4.07% |
| theme_names | 보험_손해보험 | 8 | 2 | 2 | +3.40% |
| theme_names | 셋톱박스 | 8 | 1 | 8 | +19.02% |
| theme_names | 건설_국내주택;건설_해외건설 | 7 | 1 | 0 | +1.34% |
| theme_names | 운송_항공 | 7 | 1 | 0 | +0.35% |
| theme_names | 건설_해외건설 | 6 | 1 | 0 | +1.20% |
| theme_names | 컨텐츠_음원;컨텐츠_한류 | 6 | 2 | 0 | 없음 |
| theme_names | LCD_소재;반도체_전공정소재 | 5 | 1 | 5 | +5.04% |
| theme_names | SNS(Social Network Service);게임_모바일 | 5 | 1 | 0 | +1.64% |
| theme_names | 반도체_시스템반도체;반도체_후공정 | 5 | 1 | 0 | +0.69% |
| theme_names | 반도체_설계(fabless) | 4 | 1 | 0 | +3.76% |
| theme_names | 방위산업;우주항공 | 4 | 1 | 0 | +0.54% |
| theme_names | 소프트웨어_자동차용;자동차_전장화 수혜 | 4 | 1 | 4 | +9.22% |
| theme_names | 우주항공 | 4 | 1 | 0 | +0.36% |
| theme_names | 태양광_부품/소재/장비 | 4 | 1 | 0 | +0.55% |
| theme_names | 바이오_진단/백신;코스닥_라이징스타;코스닥_히든챔피언 | 3 | 1 | 0 | 없음 |
| theme_names | 방위산업;조선_Eco선;조선_해양플랜트 | 3 | 1 | 0 | +0.03% |
| theme_names | 기계_공작기계 | 2 | 1 | 0 | 없음 |
| theme_names | 무선충전기관련주 | 2 | 1 | 0 | +0.00% |
| theme_names | 반도체_전공정장비;코스닥_라이징스타 | 2 | 1 | 0 | 없음 |
| theme_names | 배합사료 | 2 | 1 | 0 | +1.53% |
| theme_names | 비철금속주 | 2 | 1 | 0 | 없음 |
| theme_names | PCB(인쇄회로기판) | 1 | 1 | 0 | 없음 |
| theme_names | 건설_해외건설;합성수지 | 1 | 1 | 0 | 없음 |
| theme_names | 바이오_줄기세포치료제 | 1 | 1 | 0 | 없음 |
| theme_names | 반도체_생산 | 1 | 1 | 1 | +2715.00% |
| theme_names | 백화점 | 1 | 1 | 0 | 없음 |
| theme_names | 조선_LNG보냉재 | 1 | 1 | 0 | +0.65% |
| theme_member_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_member_count | 7 | 89 | 8 | 3 | +4.88% |
| theme_member_count | 6 | 20 | 4 | 2 | +6.32% |
| theme_member_count | 5 | 17 | 5 | 0 | +0.68% |
| theme_member_count | 8 | 12 | 2 | 0 | +4.07% |
| theme_member_count | 3 | 10 | 3 | 9 | +318.57% |
| theme_member_count | 4 | 7 | 1 | 0 | +1.34% |
| theme_member_count | 10 | 4 | 2 | 0 | +0.03% |
| theme_member_count | 11 | 2 | 1 | 0 | 없음 |
| theme_member_count | 12 | 2 | 1 | 0 | 없음 |
| theme_member_count | 13 | 1 | 1 | 0 | 없음 |
| theme_active_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_rising_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_falling_count | 0 | 142 | 14 | 118 | +10.47% |
| theme_top_turnover | 0 | 142 | 14 | 118 | +10.47% |
| theme_leader_code | 064550 | 17 | 1 | 0 | +2.08% |
| theme_leader_code | 003490 | 7 | 1 | 0 | +0.35% |
| theme_leader_code | 028050 | 6 | 1 | 0 | +1.20% |
| theme_leader_code | 005290 | 5 | 1 | 5 | +5.04% |
| theme_leader_code | 036540 | 5 | 1 | 0 | +0.69% |
| theme_leader_code | 047810 | 4 | 1 | 0 | +0.54% |
| theme_leader_code | 086960 | 4 | 1 | 4 | +9.22% |
| theme_leader_code | 089010 | 2 | 1 | 0 | +0.00% |
| theme_leader_code | 005930 | 1 | 1 | 1 | +2715.00% |
| theme_regime | unknown | 223 | 43 | 62 | +4.04% |
| theme_gate_action | dry_run_allow | 223 | 43 | 62 | +4.04% |
| theme_gate_reason | THEME_UNKNOWN_FALLBACK | 223 | 43 | 62 | +4.04% |

## 종목 기준 사유 집계
| reason | row_count | unique_symbol_count | avg_mfe_pct | missed_count |
|---|---:|---:|---:|---:|
| TIME_POLICY_ANALYSIS_ONLY | 297 | 63 | +3.11% | 13 |
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 140 | 32 | +2.61% | 17 |
| 없음 | 136 | 26 | +6.88% | 25 |
| max_position_size_exceeded | 90 | 9 | +11.11% | 73 |
| FINAL_PAPER_ONLY_STRATEGY | 37 | 3 | +6.07% | 32 |
| FINAL_BUY_READY | 20 | 4 | +14.27% | 13 |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 14 | 2 | -0.00% | 0 |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 6 | 1 | +1.90% | 0 |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 4 | 1 | +2.45% | 0 |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 2 | 1 | +2.15% | 0 |
| TIME_POLICY_PRE_MOMENTUM_BLOCK | 2 | 2 | 없음 | 0 |
| closing_strength_paper_only | 1 | 1 | +2715.00% | 1 |

## 회복 관찰
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

## 매매 결과
- no traded candidates

## 청산 유형별 성과
- no traded candidates

## 미체결/미매수 리뷰
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:24 | 191500 | 없음 | missing | 없음 | +4.07% | -12.01% | GOOD_REJECT |
| 006340 | 대원전선 | 2026-05-19 09:00:26 | 15390 | 없음 | missing | 없음 | +6.89% | -9.55% | MISSED_OPPORTUNITY |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:31 | 26800 | 없음 | missing | max_position_size_exceeded | +22.95% | -2.61% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:31 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 356680 | 엑스게이트 | 2026-05-19 09:00:33 | 16760 | 없음 | missing | 없음 | +15.93% | -4.18% | MISSED_OPPORTUNITY |
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:38 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | 38850 | 없음 | Analysis-only condition capture by TimePolicy ALLOW_CANDIDATE_CAPTURE | TIME_POLICY_ANALYSIS_ONLY | +2.06% | -2.83% | TIME_POLICY_BLOCK |
| 006340 | 대원전선 | 2026-05-19 09:00:40 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:00:42 | 2765 | 없음 | missing | 없음 | +7.41% | -11.03% | MISSED_OPPORTUNITY |
| 321370 | 센서뷰 | 2026-05-19 09:00:47 | 3940 | 없음 | missing | 없음 | +10.15% | -6.09% | MISSED_OPPORTUNITY |
| 006340 | 대원전선 | 2026-05-19 09:00:48 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 006340 | 대원전선 | 2026-05-19 09:00:49 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:00:51 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 178320 | 서진시스템 | 2026-05-19 09:00:52 | 73700 | 없음 | missing | 없음 | +0.41% | -6.24% | GOOD_REJECT |
| 003280 | 흥아해운 | 2026-05-19 09:00:54 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:00:57 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:08 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | 29850 | 없음 | Analysis-only condition capture by TimePolicy ALLOW_CANDIDATE_CAPTURE | TIME_POLICY_ANALYSIS_ONLY | +1.34% | -10.05% | TIME_POLICY_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:12 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:01:20 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:01:25 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 003280 | 흥아해운 | 2026-05-19 09:01:27 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:28 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 047040 | 대우건설 | 2026-05-19 09:01:29 | 없음 | missing | 없음 | missing | 없음 | missing | DATA_QUALITY_BLOCK |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:31 | 4215 | 없음 | missing | 없음 | +20.52% | -13.29% | MISSED_OPPORTUNITY |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:33 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |

## 놓친 기회
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
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:31 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:00:32 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |
| 274090 | 켄코아에어로스페이스 | 2026-05-19 09:01:08 | 26750 | 없음 | missing | max_position_size_exceeded | +23.18% | -2.43% | ORDER_GUARD_BLOCK |

## MFE 상위 놓친 기회
| symbol | name | category | MFE | close | block_source | detail | sector | theme |
|---|---|---|---:|---:|---|---|---|---|
| 005930 | 삼성전자 | TIME_POLICY_BLOCK | +2715.00% | +2655.00% | time_policy | BLOCK_AFTER_ENTRY_CUTOFF | 전기/전자 | 반도체_생산 |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | +25.91% | +25.91% | order_guard | position_limit | 의료/정밀기기 | 없음 |
| 005500 | 삼진제약 | MISSED_OPPORTUNITY | +23.92% | +18.18% | strategy_reject | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 제약 | 없음 |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | +23.18% | +6.36% | order_guard | position_limit | 운송장비/부품 | 없음 |
| 066430 | 아이로보틱스 | MISSED_OPPORTUNITY | +20.52% | +1.90% | strategy_reject | MISSED_OPPORTUNITY | 유통 | 없음 |
| 078890 | 가온그룹 | TIME_POLICY_BLOCK | +19.02% | +12.02% | time_policy | ALLOW_CANDIDATE_CAPTURE | 전기/전자 | 셋톱박스 |
| 356680 | 엑스게이트 | MISSED_OPPORTUNITY | +15.93% | +13.37% | strategy_reject | MISSED_OPPORTUNITY | IT 서비스 | 없음 |
| 243070 | 휴온스 | TIME_POLICY_BLOCK | +14.64% | +5.52% | time_policy | ALLOW_CANDIDATE_CAPTURE | 제약 | 없음 |
| 142280 | 녹십자엠에스 | TIME_POLICY_BLOCK | +13.78% | +8.00% | time_policy | ALLOW_CANDIDATE_CAPTURE | 제약 | 없음 |
| 027360 | 아주IB투자 | ORDER_GUARD_BLOCK | +13.22% | -1.93% | order_guard | position_limit | 금융 | 없음 |
| 456010 | 아이씨티케이 | ORDER_GUARD_BLOCK | +13.11% | +13.11% | order_guard | position_limit | 전기/전자 | 없음 |
| 900300 | 오가닉티코스메틱 | TIME_POLICY_BLOCK | +12.82% | -4.27% | time_policy | ALLOW_CANDIDATE_CAPTURE | 없음 | missing |
| 033160 | 엠케이전자 | MISSED_OPPORTUNITY | +12.29% | +9.56% | strategy_reject | MISSED_OPPORTUNITY | 전기/전자 | 반도체_후공정소재 |
| 478340 | 나라스페이스테크놀로지 | ORDER_GUARD_BLOCK | +10.55% | -9.36% | order_guard | position_limit | 운송장비/부품 | 없음 |
| 321370 | 센서뷰 | MISSED_OPPORTUNITY | +10.15% | -3.05% | strategy_reject | MISSED_OPPORTUNITY | 전기/전자 | 없음 |

## 비용이 컸던 차단
| symbol | name | category | MFE | close | block_source | detail | sector | theme |
|---|---|---|---:|---:|---|---|---|---|
| 005930 | 삼성전자 | TIME_POLICY_BLOCK | +2715.00% | +2655.00% | time_policy | BLOCK_AFTER_ENTRY_CUTOFF | 전기/전자 | 반도체_생산 |
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | +25.91% | +25.91% | order_guard | position_limit | 의료/정밀기기 | 없음 |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | +23.18% | +6.36% | order_guard | position_limit | 운송장비/부품 | 없음 |
| 078890 | 가온그룹 | TIME_POLICY_BLOCK | +19.02% | +12.02% | time_policy | ALLOW_CANDIDATE_CAPTURE | 전기/전자 | 셋톱박스 |
| 005500 | 삼진제약 | ORDER_GUARD_BLOCK | +16.93% | +11.51% | order_guard | position_limit | 제약 | 없음 |
| 243070 | 휴온스 | TIME_POLICY_BLOCK | +14.64% | +5.52% | time_policy | ALLOW_CANDIDATE_CAPTURE | 제약 | 없음 |
| 142280 | 녹십자엠에스 | TIME_POLICY_BLOCK | +13.78% | +8.00% | time_policy | ALLOW_CANDIDATE_CAPTURE | 제약 | 없음 |
| 027360 | 아주IB투자 | ORDER_GUARD_BLOCK | +13.22% | -1.93% | order_guard | position_limit | 금융 | 없음 |
| 456010 | 아이씨티케이 | ORDER_GUARD_BLOCK | +13.11% | +13.11% | order_guard | position_limit | 전기/전자 | 없음 |
| 900300 | 오가닉티코스메틱 | TIME_POLICY_BLOCK | +12.82% | -4.27% | time_policy | ALLOW_CANDIDATE_CAPTURE | 없음 | missing |
| 478340 | 나라스페이스테크놀로지 | ORDER_GUARD_BLOCK | +10.55% | -9.36% | order_guard | position_limit | 운송장비/부품 | 없음 |
| 086960 | MDS테크 | ORDER_GUARD_BLOCK | +9.22% | +1.02% | order_guard | position_limit | IT 서비스 | 소프트웨어_자동차용 |
| 000370 | 한화손해보험 | TIME_POLICY_BLOCK | +7.90% | +2.41% | time_policy | ALLOW_CANDIDATE_CAPTURE | 보험 | 보험_손해보험 |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | +7.58% | -16.19% | time_policy | ALLOW_CANDIDATE_CAPTURE | IT 서비스 | 없음 |
| 033160 | 엠케이전자 | ORDER_GUARD_BLOCK | +6.30% | +3.72% | order_guard | position_limit | 전기/전자 | 반도체_후공정소재 |

## OrderGuard 검토 후보
| symbol | name | category | MFE | close | block_source | detail | sector | theme |
|---|---|---|---:|---:|---|---|---|---|
| 439960 | 코스모로보틱스 | ORDER_GUARD_BLOCK | +25.91% | +25.91% | order_guard | position_limit | 의료/정밀기기 | 없음 |
| 274090 | 켄코아에어로스페이스 | ORDER_GUARD_BLOCK | +23.18% | +6.36% | order_guard | position_limit | 운송장비/부품 | 없음 |
| 005500 | 삼진제약 | ORDER_GUARD_BLOCK | +16.93% | +11.51% | order_guard | position_limit | 제약 | 없음 |
| 027360 | 아주IB투자 | ORDER_GUARD_BLOCK | +13.22% | -1.93% | order_guard | position_limit | 금융 | 없음 |
| 456010 | 아이씨티케이 | ORDER_GUARD_BLOCK | +13.11% | +13.11% | order_guard | position_limit | 전기/전자 | 없음 |
| 478340 | 나라스페이스테크놀로지 | ORDER_GUARD_BLOCK | +10.55% | -9.36% | order_guard | position_limit | 운송장비/부품 | 없음 |
| 086960 | MDS테크 | ORDER_GUARD_BLOCK | +9.22% | +1.02% | order_guard | position_limit | IT 서비스 | 소프트웨어_자동차용 |
| 033160 | 엠케이전자 | ORDER_GUARD_BLOCK | +6.30% | +3.72% | order_guard | position_limit | 전기/전자 | 반도체_후공정소재 |
| 032500 | 케이엠더블유 | ORDER_GUARD_BLOCK | +5.65% | -2.44% | order_guard | position_limit | 전기/전자 | 네트워크/광통신 |
| 272210 | 한화시스템 | ORDER_GUARD_BLOCK | +5.36% | -3.79% | order_guard | position_limit | 전기/전자 | 없음 |
| 005290 | 동진쎄미켐 | ORDER_GUARD_BLOCK | +5.04% | +0.17% | order_guard | position_limit | 화학 | 반도체_전공정소재 |
| 088350 | 한화생명 | ORDER_GUARD_BLOCK | +4.58% | -1.53% | order_guard | position_limit | 보험 | 보험_생명보험 |
| 003280 | 흥아해운 | ORDER_GUARD_BLOCK | +3.48% | -10.80% | order_guard | position_limit | 운송/창고 | 운송_해운 |
| 218410 | RFHIC | ORDER_GUARD_BLOCK | +1.66% | -8.21% | order_guard | position_limit | 전기/전자 | 없음 |

- blocked_after_buy_ready: 52
- order_guard_recoverable: 45

## TimePolicy 검토 후보
| symbol | name | category | MFE | close | block_source | detail | sector | theme |
|---|---|---|---:|---:|---|---|---|---|
| 005930 | 삼성전자 | TIME_POLICY_BLOCK | +2715.00% | +2655.00% | time_policy | BLOCK_AFTER_ENTRY_CUTOFF | 전기/전자 | 반도체_생산 |
| 078890 | 가온그룹 | TIME_POLICY_BLOCK | +19.02% | +12.02% | time_policy | ALLOW_CANDIDATE_CAPTURE | 전기/전자 | 셋톱박스 |
| 243070 | 휴온스 | TIME_POLICY_BLOCK | +14.64% | +5.52% | time_policy | ALLOW_CANDIDATE_CAPTURE | 제약 | 없음 |
| 142280 | 녹십자엠에스 | TIME_POLICY_BLOCK | +13.78% | +8.00% | time_policy | ALLOW_CANDIDATE_CAPTURE | 제약 | 없음 |
| 900300 | 오가닉티코스메틱 | TIME_POLICY_BLOCK | +12.82% | -4.27% | time_policy | ALLOW_CANDIDATE_CAPTURE | 없음 | missing |
| 000370 | 한화손해보험 | TIME_POLICY_BLOCK | +7.90% | +2.41% | time_policy | ALLOW_CANDIDATE_CAPTURE | 보험 | 보험_손해보험 |
| 037270 | YG PLUS | TIME_POLICY_BLOCK | +7.58% | -16.19% | time_policy | ALLOW_CANDIDATE_CAPTURE | IT 서비스 | 없음 |
| 052900 | KX하이텍 | TIME_POLICY_BLOCK | +4.98% | +3.03% | time_policy | ALLOW_CANDIDATE_CAPTURE | 화학 | 없음 |
| 046970 | 우리로 | TIME_POLICY_BLOCK | +4.46% | -7.98% | time_policy | ALLOW_CANDIDATE_CAPTURE | 유통 | 없음 |
| 039980 | 폴라리스AI | TIME_POLICY_BLOCK | +3.87% | -8.84% | time_policy | ALLOW_CANDIDATE_CAPTURE | IT 서비스 | 없음 |
| 003280 | 흥아해운 | TIME_POLICY_BLOCK | +2.95% | -11.27% | time_policy | ALLOW_CANDIDATE_CAPTURE | 운송/창고 | 운송_해운 |
| 217590 | 티엠씨 | TIME_POLICY_BLOCK | +2.21% | +2.21% | time_policy | ALLOW_CANDIDATE_CAPTURE | 전기/전자 | 없음 |
| 100790 | 미래에셋벤처투자 | TIME_POLICY_BLOCK | +2.18% | -11.50% | time_policy | ALLOW_CANDIDATE_CAPTURE | 금융 | 없음 |
| 064550 | 바이오니아 | TIME_POLICY_BLOCK | +2.08% | -6.24% | time_policy | ALLOW_CANDIDATE_CAPTURE | 제약 | 바이오_진단/백신 |
| 015760 | 한국전력 | TIME_POLICY_BLOCK | +2.06% | +0.77% | time_policy | ALLOW_CANDIDATE_CAPTURE | 전기/가스 | 없음 |

| time_bucket | missed_count |
|---|---:|
| 14:20~close | 8 |
| 09:00~09:30 | 3 |
| 10:30~13:00 | 3 |

## TimePolicy Paper 검증 후보
- paper-only 검증 목록입니다. 실거래 진입 완화가 아닙니다.

| 종목코드 | 종목명 | 시간대 | paper 전략 유형 | 사유 | MFE | 종가 수익률 | 업종 | 테마 |
|---|---|---|---|---|---:|---:|---|---|
| 005930 | 삼성전자 | 14:20~close | CLOSING_STRENGTH | BLOCK_AFTER_ENTRY_CUTOFF | +2715.00% | +2655.00% | 전기/전자 | 반도체_생산 |
| 078890 | 가온그룹 | 09:00~09:30 | OPENING_RECOVERY_PROBE | ALLOW_CANDIDATE_CAPTURE | +19.02% | +12.02% | 전기/전자 | 셋톱박스 |
| 243070 | 휴온스 | 09:00~09:30 | OPENING_RECOVERY_PROBE | ALLOW_CANDIDATE_CAPTURE | +14.64% | +5.52% | 제약 | 없음 |
| 142280 | 녹십자엠에스 | 10:30~13:00 | MIDDAY_VWAP_RECLAIM | ALLOW_CANDIDATE_CAPTURE | +13.78% | +8.00% | 제약 | 없음 |
| 900300 | 오가닉티코스메틱 | 10:30~13:00 | MIDDAY_VWAP_RECLAIM | ALLOW_CANDIDATE_CAPTURE | +12.82% | -4.27% | 없음 | missing |
| 000370 | 한화손해보험 | 09:00~09:30 | OPENING_RECOVERY_PROBE | ALLOW_CANDIDATE_CAPTURE | +7.90% | +2.41% | 보험 | 보험_손해보험 |
| 037270 | YG PLUS | 14:20~close | CLOSING_STRENGTH | ALLOW_CANDIDATE_CAPTURE | +7.58% | -16.19% | IT 서비스 | 없음 |
| 052900 | KX하이텍 | 10:30~13:00 | MIDDAY_VWAP_RECLAIM | ALLOW_CANDIDATE_CAPTURE | +4.98% | +3.03% | 화학 | 없음 |
| 046970 | 우리로 | 09:00~09:30 | OPENING_RECOVERY_PROBE | ALLOW_CANDIDATE_CAPTURE | +4.46% | -7.98% | 유통 | 없음 |
| 039980 | 폴라리스AI | 10:30~13:00 | MIDDAY_VWAP_RECLAIM | ALLOW_CANDIDATE_CAPTURE | +3.87% | -8.84% | IT 서비스 | 없음 |
| 217590 | 티엠씨 | 09:00~09:30 | OPENING_RECOVERY_PROBE | ALLOW_CANDIDATE_CAPTURE | +2.21% | +2.21% | 전기/전자 | 없음 |
| 100790 | 미래에셋벤처투자 | 09:00~09:30 | OPENING_RECOVERY_PROBE | ALLOW_CANDIDATE_CAPTURE | +2.18% | -11.50% | 금융 | 없음 |
| 064550 | 바이오니아 | 10:30~13:00 | MIDDAY_VWAP_RECLAIM | ALLOW_CANDIDATE_CAPTURE | +2.08% | -6.24% | 제약 | 바이오_진단/백신 |
| 015760 | 한국전력 | 09:00~09:30 | OPENING_RECOVERY_PROBE | ALLOW_CANDIDATE_CAPTURE | +2.06% | +0.77% | 전기/가스 | 없음 |

## 업종/테마 집중도
### 업종명
| name | rows | unique_symbols | missed | order_guard | time_policy | avg_MFE | max_MFE |
|---|---:|---:|---:|---:|---:|---:|---:|
| 전기/전자 | 178 | 26 | 85 | 58 | 30 | +25.98% | +2715.00% |
| 운송장비/부품 | 31 | 5 | 23 | 23 | 3 | +15.46% | +23.18% |
| 금융 | 52 | 7 | 21 | 21 | 9 | +5.95% | +13.22% |
| 제약 | 72 | 12 | 12 | 1 | 60 | +6.59% | +23.92% |
| IT 서비스 | 34 | 9 | 12 | 4 | 19 | +5.89% | +15.93% |
| 의료/정밀기기 | 17 | 7 | 8 | 8 | 6 | +19.39% | +25.91% |
| 화학 | 63 | 7 | 5 | 5 | 55 | +2.04% | +5.04% |
| 기계/장비 | 43 | 7 | 3 | 0 | 10 | +1.52% | +6.64% |
| 보험 | 26 | 4 | 2 | 15 | 4 | +4.17% | +7.90% |
| 유통 | 14 | 5 | 1 | 0 | 2 | +5.15% | +20.52% |

### 테마명
| name | rows | unique_symbols | missed | order_guard | time_policy | avg_MFE | max_MFE |
|---|---:|---:|---:|---:|---:|---:|---:|
| (blank) | 465 | 81 | 107 | 67 | 213 | +6.29% | +25.91% |
| 반도체_후공정소재 | 34 | 1 | 34 | 32 | 0 | +6.65% | +12.29% |
| 네트워크/광통신 | 12 | 1 | 12 | 12 | 0 | +5.60% | +5.65% |
| 통신장비 | 12 | 1 | 12 | 12 | 0 | +5.60% | +5.65% |
| 셋톱박스 | 8 | 1 | 8 | 0 | 1 | +19.02% | +19.02% |
| LCD_소재 | 5 | 1 | 5 | 5 | 0 | +5.04% | +5.04% |
| 반도체_전공정소재 | 5 | 1 | 5 | 5 | 0 | +5.04% | +5.04% |
| 소프트웨어_자동차용 | 4 | 1 | 4 | 4 | 0 | +9.22% | +9.22% |
| 자동차_전장화 수혜 | 4 | 1 | 4 | 4 | 0 | +9.22% | +9.22% |
| 보험_손해보험 | 8 | 2 | 2 | 0 | 1 | +3.40% | +7.90% |

## 다음 파라미터 점검 추천
- OrderGuard: review 45 BUY-ready blocked rows before changing strategy thresholds.
- TimePolicy: simulate a narrower relaxation around 14:20~close; 14 recoverable rows qualify.
- Theme map: 107 missed rows still have blank theme coverage; improve the map before theme gating.

## 좋은 거절
| symbol | name | detected_at | capture_price | final_decision | final_reason | reason_code | MFE | MAE | category |
|---|---|---|---:|---|---|---|---:|---:|---|
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:24 | 191500 | 없음 | missing | 없음 | +4.07% | -12.01% | GOOD_REJECT |
| 178320 | 서진시스템 | 2026-05-19 09:00:52 | 73700 | 없음 | missing | 없음 | +0.41% | -6.24% | GOOD_REJECT |
| 028050 | 삼성E&A | 2026-05-19 09:01:37 | 49900 | 없음 | missing | 없음 | +1.20% | -4.71% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-19 09:01:56 | 378000 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +2.65% | -5.95% | GOOD_REJECT |
| 196170 | 알테오젠 | 2026-05-19 09:01:57 | 378000 | BLOCKED | Momentum decision is not BUY: REJECT below VWAP with weak reclaim flow curren... | FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | +2.65% | -5.95% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:09 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:11 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 042660 | 한화오션 | 2026-05-19 09:02:17 | 118700 | 없음 | missing | 없음 | +0.42% | -6.49% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:17 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:21 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 007610 | 선도전기 | 2026-05-19 09:02:24 | 10410 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 43.9 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +1.54% | -13.54% | GOOD_REJECT |
| 007610 | 선도전기 | 2026-05-19 09:02:24 | 10410 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 43.9 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +1.54% | -13.54% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:37 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 223250 | 드림씨아이에스 | 2026-05-19 09:02:38 | 6870 | BLOCKED | Momentum decision is not BUY: BLOCK_CHASE leader score weak 36.4 < 60.0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER | +4.80% | -15.87% | GOOD_REJECT |
| 036540 | SFA반도체 | 2026-05-19 09:02:39 | 8720 | 없음 | missing | 없음 | +0.80% | -12.61% | GOOD_REJECT |

## 추격매수 차단 리뷰
- none

## 데이터 품질 차단
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
| 066430 | 아이로보틱스 | MISSED_OPPORTUNITY | 없음 | +20.52% | -13.29% | +1.90% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | TIME_POLICY_BLOCK | TIME_POLICY_ANALYSIS_ONLY | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | MISSED_OPPORTUNITY | 없음 | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | MISSED_OPPORTUNITY | 없음 | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 078890 | 가온그룹 | MISSED_OPPORTUNITY | 없음 | +19.02% | -3.85% | +12.02% | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |

| data_quality | count | avg_mfe_pct | n_mfe | missing_mfe |
|---|---:|---:|---:|---:|
| MISSING_SPREAD_RATE | 525 | +7.43% | 215 | 310 |
| MISSING_TRADE_STRENGTH | 525 | +7.43% | 215 | 310 |
| partial_data | 525 | +7.43% | 215 | 310 |
| MISSING_DECISION_TRACE | 435 | +4.77% | 125 | 310 |
| MISSING_CAPTURE_PRICE | 310 | 없음 | 0 | 310 |
| MISSING_MFE_MAE | 310 | 없음 | 0 | 310 |
| MISSING_VOLUME_RATIO | 19 | +12.67% | 11 | 8 |

## 누락된 의사결정 Trace 상세
| symbol | name | detected_at | candidate_id | role | reason_code | time_policy | source | stage | data_quality |
|---|---|---|---|---|---|---|---|---|---|
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:24 | 0363f3b95d514604bca88f935c7e1439 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 006340 | 대원전선 | 2026-05-19 09:00:26 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 356680 | 엑스게이트 | 2026-05-19 09:00:33 | 11fa203843644d838b3781065f973974 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:00:38 | 0363f3b95d514604bca88f935c7e1439 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:00:40 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | 3ca39d9805d34d549c4be9775d799a71 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | 없음 | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 015760 | 한국전력 | 2026-05-19 09:00:40 | 3ca39d9805d34d549c4be9775d799a71 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:00:42 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 321370 | 센서뷰 | 2026-05-19 09:00:47 | cdd7950fa4424c0f85a74f8e7814336e | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 006340 | 대원전선 | 2026-05-19 09:00:48 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:00:49 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:00:51 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 178320 | 서진시스템 | 2026-05-19 09:00:52 | c84728762d124b50b56e976747a09438 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;MISSING_VOL... |
| 003280 | 흥아해운 | 2026-05-19 09:00:54 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:00:57 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | 6e1a1ee8d56f4dd480a395381a508320 | analysis_only | TIME_POLICY_ANALYSIS_ONLY | ALLOW_CANDIDATE_CAPTURE | 없음 | analysis_only | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 047040 | 대우건설 | 2026-05-19 09:01:09 | 6e1a1ee8d56f4dd480a395381a508320 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:01:20 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:01:25 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:01:27 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:28 | 6e1a1ee8d56f4dd480a395381a508320 | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:29 | 6e1a1ee8d56f4dd480a395381a508320 | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:31 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 006340 | 대원전선 | 2026-05-19 09:01:37 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:01:37 | 22ab90f2a27f4380bd606a0792024006 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:39 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:01:40 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:40 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:41 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:01:42 | 22ab90f2a27f4380bd606a0792024006 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 066430 | 아이로보틱스 | 2026-05-19 09:01:43 | 2d02f4e7debe4f42aae1b2f5560560cd | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:51 | 6e1a1ee8d56f4dd480a395381a508320 | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:01:52 | 6e1a1ee8d56f4dd480a395381a508320 | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:01:57 | 22ab90f2a27f4380bd606a0792024006 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 047040 | 대우건설 | 2026-05-19 09:02:04 | 6e1a1ee8d56f4dd480a395381a508320 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 028050 | 삼성E&A | 2026-05-19 09:02:05 | 22ab90f2a27f4380bd606a0792024006 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:02:05 | 0363f3b95d514604bca88f935c7e1439 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:09 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:02:09 | 0363f3b95d514604bca88f935c7e1439 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 036930 | 주성엔지니어링 | 2026-05-19 09:02:10 | 0363f3b95d514604bca88f935c7e1439 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:12 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:16 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 440110 | 파두 | 2026-05-19 09:02:16 | 11dafcfc6be24f9c9a011215848d3a12 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 440110 | 파두 | 2026-05-19 09:02:16 | 11dafcfc6be24f9c9a011215848d3a12 | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 042660 | 한화오션 | 2026-05-19 09:02:17 | 10b839b90d244f86b9fa622306826745 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_DECISION_TRACE;MISSING_SPREAD_RATE;MISSING_TRADE_STRENGTH;partial_data |
| 003280 | 흥아해운 | 2026-05-19 09:02:18 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:20 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:22 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 006340 | 대원전선 | 2026-05-19 09:02:27 | 2618ce60795b4a23a7c67b9c99ddf2b3 | trading | 없음 | ALLOW_CANDIDATE_CAPTURE | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |
| 003280 | 흥아해운 | 2026-05-19 09:02:31 | c241d9dbb686495ba1c11f5a41c0330e | trading | 없음 | BONUS_CONDITION_AFTER_PRIMARY | 없음 | market_metrics_missing | MISSING_CAPTURE_PRICE;MISSING_DECISION_TRACE;MISSING_MFE_MAE;MISSING_SPREAD_R... |

## 데이터 품질 이슈 중 고MFE 종목
- none

## 시간 정책 차단
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

## OrderGuard 차단
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

## 사유 코드 순위
| reason_code | count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae | missing_mfe | missing_mae | missed_opportunity_count | missed_opportunity_rate | good_reject_count | good_reject_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TIME_POLICY_ANALYSIS_ONLY | 297 | +3.11% | -7.01% | 70 | 70 | 227 | 227 | 13 | 4.38% | 0 | 0.00% |
| FINAL_MOMENTUM_BLOCK_WEAK_LEADER | 140 | +2.61% | -6.74% | 140 | 140 | 0 | 0 | 17 | 12.14% | 123 | 87.86% |
| 없음 | 136 | +6.88% | -9.07% | 55 | 55 | 81 | 81 | 25 | 18.38% | 30 | 22.06% |
| max_position_size_exceeded | 90 | +11.11% | -4.42% | 90 | 90 | 0 | 0 | 73 | 81.11% | 0 | 0.00% |
| FINAL_PAPER_ONLY_STRATEGY | 37 | +6.07% | -0.90% | 37 | 37 | 0 | 0 | 32 | 86.49% | 5 | 13.51% |
| FINAL_BUY_READY | 20 | +14.27% | -4.75% | 20 | 20 | 0 | 0 | 13 | 65.00% | 0 | 0.00% |
| FINAL_MOMENTUM_BLOCK_UPPER_WICK | 14 | -0.00% | -6.64% | 14 | 14 | 0 | 0 | 0 | 0.00% | 14 | 100.00% |
| FINAL_MOMENTUM_REJECT_TRADE_STRENGTH | 6 | +1.90% | -2.66% | 6 | 6 | 0 | 0 | 0 | 0.00% | 6 | 100.00% |
| FINAL_MOMENTUM_BLOCK_BELOW_VWAP_WEAK_FLOW | 4 | +2.45% | -5.95% | 4 | 4 | 0 | 0 | 0 | 0.00% | 4 | 100.00% |
| FINAL_MOMENTUM_BLOCK_SIGNAL_CANDLE_RANGE | 2 | +2.15% | -3.50% | 2 | 2 | 0 | 0 | 0 | 0.00% | 2 | 100.00% |
| TIME_POLICY_PRE_MOMENTUM_BLOCK | 2 | 없음 | missing | 0 | 0 | 2 | 2 | 0 | 0.00% | 0 | 0.00% |
| closing_strength_paper_only | 1 | +2715.00% | +2655.00% | 1 | 1 | 0 | 0 | 1 | 100.00% | 0 | 0.00% |

## 완화된 눌림목 드라이런
| policy | candidate_rows | unique_symbols | pullback_signal_rows | non_traded_signal_rows | top_signal_block_reason |
|---|---:|---:|---:|---:|---|
| pullback >= 0.5% | 749 | 41 | 218 | 218 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 0.8% | 749 | 38 | 209 | 209 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 1.0% | 749 | 38 | 209 | 209 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback >= 1.5% | 749 | 34 | 189 | 189 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |

- pullback_signal_rows only means the relaxed pullback threshold passed; it is not a full buy-gate allowed count.

## 매수 가능성 비교
| policy | row_count | unique_symbol_count | traded_count | top_reason |
|---|---:|---:|---:|---|
| baseline | 58 | 8 | 0 | FINAL_PAPER_ONLY_STRATEGY |
| pullback_0p5_signal | 218 | 41 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_0p8_signal | 209 | 38 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_1p0_signal | 209 | 38 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| pullback_1p5_signal | 189 | 34 | 0 | FINAL_MOMENTUM_BLOCK_WEAK_LEADER |
| breakout_small_trace | 0 | 0 | 0 | 없음 |
| pullback_reclaim_vwap | 20 | 4 | 0 | FINAL_BUY_READY |

- pullback_*_signal is a relaxed pullback signal count, not a full buy-gate pass count.

## 약한 거래량 비율 MFE
- none

## 데이터 대조
- post_market raw detected rows: 749
- post_market unique symbols: 120
- post_market unique candidate_ids: 96
- baseline full-gate buy/order rows: 58
- relaxed pullback 0.5% signal rows: 218
- entry_gate_dry_run groups condition captures by symbol and then expands policy rows, while post_market keeps raw condition detections. Compare unique_symbol_count with raw_detected before tuning.
- previous relaxed pullback would_buy_count meant pullback-threshold signal only. It is now reported as signal rows to avoid implying that VWAP, volume, time policy, and order guard also passed.

## 시간대별 분석
| time_bucket | capture_count | strategy_candidate_count | paper_only_count | traded_count | non_traded_count | missed_opportunity_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 09:00~09:30 | 315 | 2 | 2 | 0 | 315 | 103 | 106 | +7.05% | -7.25% | 234 | 234 |
| 09:30~10:30 | 47 | 3 | 3 | 0 | 47 | 13 | 24 | +6.56% | -7.28% | 47 | 47 |
| 10:30~13:00 | 132 | 0 | 0 | 0 | 132 | 3 | 0 | +3.23% | -6.62% | 29 | 29 |
| 13:00~14:20 | 100 | 32 | 32 | 0 | 100 | 45 | 54 | +3.77% | -2.09% | 99 | 99 |
| 14:20 이후 | 155 | 1 | 1 | 0 | 155 | 10 | 0 | +92.92% | +83.12% | 30 | 30 |

## Paper 전략 성과
| strategy_type | candidate_count | paper_only_count | traded_count | missed_count | good_reject_count | avg_mfe_pct | avg_mae_pct | n_mfe | n_mae |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AFTERNOON_SECOND_WAVE | 32 | 32 | 0 | 32 | 0 | +6.30% | -0.06% | 32 | 32 |
| CLOSING_STRENGTH | 1 | 1 | 0 | 1 | 0 | +2715.00% | +2655.00% | 1 | 1 |
| TREND_CONTINUATION | 5 | 5 | 0 | 0 | 5 | +4.57% | -6.28% | 5 | 5 |

## 파라미터 튜닝 힌트
- TimePolicy blocked rows later moved strongly. Review entry windows manually, especially recurring time buckets.

## 다음 작업 체크리스트
- [ ] Review top 5 MISSED_OPPORTUNITY rows.
- [ ] Check high-MFE DATA_QUALITY_BLOCK rows before tuning strategy parameters.
- [ ] Verify whether BLOCK_CHASE actually prevented weak follow-through.
- [ ] Review TIME_POLICY_BLOCK rows that rallied after the block.
- [ ] Inspect TRADED_LOSS reason_code clustering.
- [ ] Record config candidates only; do not change config immediately.

---
Generated from files only. This review does not connect to live trading.