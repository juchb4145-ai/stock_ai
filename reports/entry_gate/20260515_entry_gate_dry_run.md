# 2026-05-15 Entry Gate Dry Run

## Baseline
- baseline_allowed_buy_symbols: 0

## Daily Buy Gate Funnel
| metric | value |
|---|---:|
| raw_condition_detected_count | 770 |
| registered_candidate_count | 487 |
| analysis_only_count | 204 |
| momentum_evaluated_count | 731 |
| final_entry_decision_count | 115 |
| baseline_would_buy_count | 0 |
| relaxed_would_buy_count | 2 |
| actually_ordered_count | 0 |
| unique_symbol_count | 146 |
| policy_row_count | 730 |

## Policy Comparison
| policy | candidate_unique_symbols | would_buy_unique_symbols | blocked_unique_symbols | policy_rows | top_block_reason |
|---|---:|---:|---:|---:|---|
| pullback_0p5 | 146 | 2 | 144 | 146 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_0p8 | 146 | 2 | 144 | 146 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_1p0 | 146 | 1 | 145 | 146 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_1p5 | 146 | 0 | 146 | 146 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| breakout_small | 146 | 0 | 146 | 146 | BLOCK_BELOW_VWAP_WEAK_FLOW |

## Reason Counts by Policy Row
| reason | count |
|---|---:|
| BLOCK_BELOW_VWAP_WEAK_FLOW | 220 |
| missing_momentum_log | 175 |
| volume_ratio_lt_1p2 | 155 |
| trade_strength_lt_100 | 125 |
| WAIT_RECLAIM_VWAP | 30 |
| upper_wick_too_large | 15 |
| would_buy | 5 |
| missing_one_min_reversal | 5 |

## Reason Counts by Unique Symbol
| reason | unique_symbols |
|---|---:|
| BLOCK_BELOW_VWAP_WEAK_FLOW | 44 |
| missing_momentum_log | 35 |
| volume_ratio_lt_1p2 | 32 |
| trade_strength_lt_100 | 25 |
| WAIT_RECLAIM_VWAP | 6 |
| upper_wick_too_large | 3 |
| would_buy | 2 |
| missing_one_min_reversal | 1 |

## Missing Momentum Log
- symbols_without_momentum_entry_decision: 35

| missing_reason | symbols |
|---|---:|
| analysis_only_not_registered | 19 |
| registered_but_no_momentum_event | 9 |
| time_policy_block_ALLOW_MANAGE_ONLY | 5 |
| time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | 2 |

| symbol | name | detected_at | candidate_ids | registered_at | last_time_policy | last_eval | join | reason | expected_next_step | bug_or_expected |
|---|---|---|---|---|---|---|---|---|---|---|
| 000240 | 한국앤컴퍼니 | 2026-05-15 12:31:06 | 5bccc5c2a88e4bb4bb26a8118c473e08 | 2026-05-15 12:31:10 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 12:36:51 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 003280 | 흥아해운 | 2026-05-15 11:01:39 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 11:06:06 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 003350 | 한국화장품제조 | 2026-05-15 10:48:27 | f9bb1b15b84c4ac28a5f840c241e3fcb | 2026-05-15 11:02:37 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 11:05:07 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 004370 | 농심 | 2026-05-15 14:26:02 | bda4db3727cf46a99028cb4a3f62c276 | 2026-05-15 14:27:00 | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-15 14:29:36 |  | candidate_id | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | keep as time policy block; no order | expected_policy |
| 005010 | 휴스틸 | 2026-05-15 12:44:54 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:49:52 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 005950 | 이수화학 | 2026-05-15 11:22:50 | 18624277a5bf4b948a9ebe2fb6a0cfa3 | 2026-05-15 11:22:50 | ALLOW_MANAGE_ONLY@2026-05-15 11:26:16 |  | candidate_id | time_policy_block_ALLOW_MANAGE_ONLY | keep as time policy block; no order | expected_policy |
| 007340 | DN오토모티브 | 2026-05-15 11:04:37 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 11:04:47 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 018880 | 한온시스템 | 2026-05-15 09:00:22 | e77b43cd724e49609fc497e8e8064b47 | 2026-05-15 09:00:22 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 09:06:23 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 024060 | 흥구석유 | 2026-05-15 11:02:08 | 87f6d699a5b34245a23b12fe42b5ab1c | 2026-05-15 11:13:16 | ALLOW_MANAGE_ONLY@2026-05-15 11:19:30 |  | candidate_id | time_policy_block_ALLOW_MANAGE_ONLY | keep as time policy block; no order | expected_policy |
| 030000 | 제일기획 | 2026-05-15 12:31:43 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:46:42 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 030190 | NICE평가정보 | 2026-05-15 12:47:56 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:47:56 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 031330 | 에스에이엠티 | 2026-05-15 11:29:21 | 66ceae28fd0d45b1a1c570b78dbc0ad5;ef658edf2982467f98201ccbe5a89ba5 | 2026-05-15 11:29:21 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 11:34:57 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 037460 | 삼지전자 | 2026-05-15 11:27:33 | 17f274dd91eb4605b455c40076271e2f;f7631dc3f63d4641a980df1b7bc97648 | 2026-05-15 11:27:47 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 11:34:57 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 041510 | 에스엠 | 2026-05-15 12:31:00 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:31:00 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 052900 | KX하이텍 | 2026-05-15 10:39:40 | 78a31b485f82407bb2aac61102741fcc | 2026-05-15 10:39:41 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 10:52:29 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 053610 | 프로텍 | 2026-05-15 14:23:51 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-15 14:23:51 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 066570 | LG전자 | 2026-05-15 09:02:19 | 5c88901a66064072940998b935b4144b | 2026-05-15 09:02:19 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 09:02:19 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 077500 | 유니퀘스트 | 2026-05-15 11:40:34 | 4fdff15e24d74cfbb33f072de1ea7c8d | 2026-05-15 11:40:34 | ALLOW_MANAGE_ONLY@2026-05-15 11:40:34 |  | candidate_id | time_policy_block_ALLOW_MANAGE_ONLY | keep as time policy block; no order | expected_policy |
| 081660 | 미스토홀딩스 | 2026-05-15 10:37:57 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 11:14:43 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 086980 | 쇼박스 | 2026-05-15 12:07:34 | a54de33cc8b548bb993654b62764726c | 2026-05-15 12:07:34 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 12:07:34 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 092790 | 넥스틸 | 2026-05-15 12:38:52 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:38:52 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 122870 | 와이지엔터테인먼트 | 2026-05-15 12:48:16 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:49:40 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 126600 | BGF에코머티리얼즈 | 2026-05-15 10:56:20 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 10:56:20 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 136490 | 선진 | 2026-05-15 12:44:20 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:45:12 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 138930 | BNK금융지주 | 2026-05-15 12:44:00 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:44:24 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 141080 | 리가켐바이오 | 2026-05-15 11:57:47 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:03:42 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 161390 | 한국타이어앤테크놀로지 | 2026-05-15 12:48:00 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:48:45 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 187870 | 디바이스 | 2026-05-15 10:52:37 | 29e2c4f20fd44ac9a294edec9edadb5e | 2026-05-15 10:52:37 | ALLOW_MANAGE_ONLY@2026-05-15 11:19:57 |  | candidate_id | time_policy_block_ALLOW_MANAGE_ONLY | keep as time policy block; no order | expected_policy |
| 189300 | 인텔리안테크 | 2026-05-15 11:59:39 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:03:00 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 192080 | 더블유게임즈 | 2026-05-15 12:38:25 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 12:49:36 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 214320 | 이노션 | 2026-05-15 12:39:30 | a119029485834189b9de95d229066767 | 2026-05-15 12:39:31 | ALLOW_CANDIDATE_CAPTURE@2026-05-15 12:39:31 |  | candidate_id | registered_but_no_momentum_event | inspect eval loop scheduling/log emission | needs_investigation |
| 253840 | 수젠텍 | 2026-05-15 11:20:31 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 11:23:20 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 260970 | 에스앤디 | 2026-05-15 12:59:29 | e499e66048c94c15a006aefe6f241a1f | 2026-05-15 14:31:57 | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-15 14:36:14 |  | candidate_id | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | keep as time policy block; no order | expected_policy |
| 420570 | 제이투케이바이오 | 2026-05-15 12:30:16 | b130ccfaccd24c91b96e7047e31ad696 | 2026-05-15 12:30:17 | ALLOW_MANAGE_ONLY@2026-05-15 12:31:11 |  | candidate_id | time_policy_block_ALLOW_MANAGE_ONLY | keep as time policy block; no order | expected_policy |
| 443060 | HD현대마린솔루션 | 2026-05-15 10:34:56 |  |  | ALLOW_MANAGE_ONLY@2026-05-15 10:34:56 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |

## Join Key Notes
| join_status | symbols |
|---|---:|
| candidate_id | 127 |
| symbol | 19 |

- raw_symbol_variant_symbols: 0
- raw_A_prefix_symbols: 0
- alphanumeric_symbols: 0004V0, 0007C0

## Would Buy Comparison
| policy | unique_symbol_count | policy_row_count | would_buy_unique_symbols | would_buy_policy_rows |
|---|---:|---:|---:|---:|
| pullback_0p5 | 146 | 146 | 2 | 2 |
| pullback_0p8 | 146 | 146 | 2 | 2 |
| pullback_1p0 | 146 | 146 | 1 | 1 |
| pullback_1p5 | 146 | 146 | 0 | 0 |
| breakout_small | 146 | 146 | 0 | 0 |

## Reconciliation
- raw_condition_detected_count=770 and unique_symbol_count=146 are different denominators. Post-market keeps raw detections; entry-gate dry-run evaluates unique symbols and expands policy rows.
- policy_row_count=730 equals unique symbols multiplied by the policy set. Compare would_buy_unique_symbols before comparing to post-market raw rows.
- post-market relaxed pullback counts are pullback-threshold signals, not full buy-gate approvals. This dry-run keeps VWAP, volume, spread, wick, time-policy and final-entry blocks in the same row.

## Candidate Detail
| policy | symbol | name | would_buy | block_reason | missing_reason | pullback | return | strength | volume_ratio | time_policy | join |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|
| breakout_small | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 000270 | 기아 | N | volume_ratio_lt_1p2 |  | -1.80% | +1.80% | 103.6 | 0.30 | ALLOW_ENTRY | candidate_id |
| breakout_small | 000370 | 한화손해보험 | N | volume_ratio_lt_1p2 |  | +1.25% | -1.25% | 173.6 | 0.17 | ALLOW_ENTRY | candidate_id |
| breakout_small | 0004V0 | 엔비알모션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 118.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 0007C0 | 아크릴 | N | WAIT_RECLAIM_VWAP |  | +0.41% | -0.41% | 185.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 000880 | 한화 | N | volume_ratio_lt_1p2 |  | -1.12% | +1.12% | 101.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001200 | 유진투자증권 | N | volume_ratio_lt_1p2 |  | -2.42% | +2.42% | 165.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001510 | SK증권 | N | trade_strength_lt_100 |  | +3.10% | -3.10% | 86.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001740 | SK네트웍스 | N | trade_strength_lt_100 |  | +4.17% | -4.17% | 75.7 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001820 | 삼화콘덴서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 157.0 | 0.27 | ALLOW_ENTRY | candidate_id |
| breakout_small | 002780 | 진흥기업 | N | missing_one_min_reversal |  | +0.76% | +0.00% | 100.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003280 | 흥아해운 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 003350 | 한국화장품제조 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.15% | -0.15% | 109.6 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.43% | -1.43% | 111.9 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003670 | 포스코퓨처엠 | N | trade_strength_lt_100 |  | +1.73% | -1.73% | 94.5 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003690 | 코리안리 | N | volume_ratio_lt_1p2 |  | +0.31% | +0.00% | 151.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 004020 | 현대제철 | N | volume_ratio_lt_1p2 |  | -2.40% | +2.40% | 168.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| breakout_small | 004370 | 농심 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 005010 | 휴스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.06% | -0.06% | 325.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 005880 | 대한해운 | N | trade_strength_lt_100 |  | +2.50% | -2.50% | 98.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 005950 | 이수화학 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 006400 | 삼성SDI | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.62% | +0.62% | 118.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 006800 | 미래에셋증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.32% | -1.32% | 113.7 | 0.68 | ALLOW_ENTRY | candidate_id |
| breakout_small | 007340 | DN오토모티브 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 009150 | 삼성전기 | N | volume_ratio_lt_1p2 |  | -4.47% | +4.47% | 118.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 011560 | 세보엠이씨 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.91% | -1.07% | 173.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 012330 | 현대모비스 | N | upper_wick_too_large |  | -0.30% | +0.30% | 115.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| breakout_small | 012610 | 경인양행 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.99% | -1.99% | 136.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 012860 | 모베이스전자 | N | trade_strength_lt_100 |  | +2.44% | -2.44% | 90.3 | 0.19 | ALLOW_ENTRY | candidate_id |
| breakout_small | 018260 | 삼성에스디에스 | N | volume_ratio_lt_1p2 |  | -4.49% | +4.49% | 178.4 | 0.33 | ALLOW_ENTRY | candidate_id |
| breakout_small | 018880 | 한온시스템 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 019210 | 와이지-원 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 101.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 020150 | 롯데에너지머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.48% | -4.48% | 103.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| breakout_small | 024060 | 흥구석유 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 027360 | 아주IB투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 93.3 | 0.69 | ALLOW_ENTRY | candidate_id |
| breakout_small | 027410 | BGF | N | volume_ratio_lt_1p2 |  | +0.19% | -0.19% | 223.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 028670 | 팬오션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.95% | -0.95% | 114.7 | 0.34 | ALLOW_ENTRY | candidate_id |
| breakout_small | 030000 | 제일기획 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 030190 | NICE평가정보 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 030530 | 원익홀딩스 | N | volume_ratio_lt_1p2 |  | -1.77% | +1.77% | 168.6 | 0.24 | ALLOW_ENTRY | candidate_id |
| breakout_small | 031330 | 에스에이엠티 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 033240 | 자화전자 | N | volume_ratio_lt_1p2 |  | -12.13% | +12.13% | 207.9 | 0.46 | ALLOW_ENTRY | candidate_id |
| breakout_small | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.51% | -2.51% | 159.8 | 0.16 | ALLOW_ENTRY | candidate_id |
| breakout_small | 034220 | LG디스플레이 | N | volume_ratio_lt_1p2 |  | -2.94% | +2.94% | 130.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| breakout_small | 035510 | 신세계 I&C | N | volume_ratio_lt_1p2 |  | -0.48% | +0.48% | 171.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| breakout_small | 036460 | 한국가스공사 | N | volume_ratio_lt_1p2 |  | -0.78% | +0.78% | 204.6 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 036930 | 주성엔지니어링 | N | trade_strength_lt_100 |  | +8.95% | -8.95% | 60.7 | 2.19 | ALLOW_ENTRY | candidate_id |
| breakout_small | 037460 | 삼지전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 041190 | 우리기술투자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.31% | +0.31% | 163.0 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 041510 | 에스엠 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 043260 | 성호전자 | N | trade_strength_lt_100 |  | +0.45% | -0.45% | 92.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| breakout_small | 049630 | 재영솔루텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.38% | -0.38% | 131.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 052400 | 코나아이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.09% | -0.28% | 149.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 052900 | KX하이텍 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 053610 | 프로텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 054450 | 텔레칩스 | N | volume_ratio_lt_1p2 |  | +0.88% | -0.88% | 150.4 | 0.14 | ALLOW_ENTRY | candidate_id |
| breakout_small | 056080 | 유진로봇 | N | volume_ratio_lt_1p2 |  | -3.83% | +3.83% | 188.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| breakout_small | 061970 | LB세미콘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.85% | -0.85% | 115.3 | 0.20 | ALLOW_ENTRY | candidate_id |
| breakout_small | 064260 | 다날 | N | trade_strength_lt_100 |  | +3.25% | -3.25% | 57.3 | 0.10 | ALLOW_ENTRY | candidate_id |
| breakout_small | 066570 | LG전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 066970 | 엘앤에프 | N | trade_strength_lt_100 |  | +2.80% | -2.80% | 98.7 | 0.33 | ALLOW_ENTRY | candidate_id |
| breakout_small | 074600 | 원익QnC | N | volume_ratio_lt_1p2 |  | -1.02% | +1.02% | 138.6 | 0.27 | ALLOW_ENTRY | candidate_id |
| breakout_small | 077500 | 유니퀘스트 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 078600 | 대주전자재료 | N | trade_strength_lt_100 |  | +3.64% | -3.64% | 66.4 | 0.23 | ALLOW_ENTRY | candidate_id |
| breakout_small | 078930 | GS | N | volume_ratio_lt_1p2 |  | -4.62% | +4.62% | 188.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 081660 | 미스토홀딩스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 086520 | 에코프로 | N | trade_strength_lt_100 |  | +2.84% | -2.84% | 85.7 | 0.21 | ALLOW_ENTRY | candidate_id |
| breakout_small | 086980 | 쇼박스 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -4.42% | +4.42% | 137.0 | 0.10 | ALLOW_ENTRY | candidate_id |
| breakout_small | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -2.34% | +2.34% | 106.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 090710 | 휴림로봇 | N | volume_ratio_lt_1p2 |  | -6.38% | +6.38% | 189.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 092300 | 현우산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.66% | -2.66% | 122.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 092460 | 한라IMS | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.61% | -0.48% | 143.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 092790 | 넥스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 094940 | 푸른기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 106.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 096770 | SK이노베이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 161.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 100790 | 미래에셋벤처투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 86.8 | 0.42 | ALLOW_ENTRY | candidate_id |
| breakout_small | 117730 | 티로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 165.6 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 122870 | 와이지엔터테인먼트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 125020 | 티씨머티리얼즈 | N | trade_strength_lt_100 |  | +5.07% | -5.07% | 85.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| breakout_small | 125490 | 한라캐스트 | N | WAIT_RECLAIM_VWAP |  | -0.47% | +0.47% | 231.0 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 126600 | BGF에코머티리얼즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 126720 | 수산인더스트리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.19% | -0.33% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 128940 | 한미약품 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 200.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 136490 | 선진 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 138360 | 앤로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -4.01% | +4.01% | 100.1 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 138930 | BNK금융지주 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 140670 | 알에스오토메이션 | N | volume_ratio_lt_1p2 |  | -0.62% | +0.62% | 105.7 | 0.26 | ALLOW_ENTRY | candidate_id |
| breakout_small | 141080 | 리가켐바이오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 161390 | 한국타이어앤테크놀로지 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 181710 | NHN | N | volume_ratio_lt_1p2 |  | +0.13% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 187870 | 디바이스 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 189300 | 인텔리안테크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 196170 | 알테오젠 | N | trade_strength_lt_100 |  | +2.24% | -2.24% | 84.8 | 0.35 | ALLOW_ENTRY | candidate_id |
| breakout_small | 204320 | HL만도 | N | volume_ratio_lt_1p2 |  | -1.88% | +1.88% | 188.7 | 0.50 | ALLOW_ENTRY | candidate_id |
| breakout_small | 204620 | 글로벌텍스프리 | N | WAIT_RECLAIM_VWAP |  | +1.54% | -1.54% | 187.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| breakout_small | 214320 | 이노션 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 215100 | 로보로보 | N | volume_ratio_lt_1p2 |  | +0.13% | -0.13% | 154.4 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 217500 | 러셀 | N | trade_strength_lt_100 |  | +1.92% | -1.92% | 91.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 234340 | 헥토파이낸셜 | N | trade_strength_lt_100 |  | +10.77% | -10.77% | 49.3 | 0.93 | ALLOW_ENTRY | candidate_id |
| breakout_small | 242040 | 나무기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 124.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 253840 | 수젠텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 259630 | 엠플러스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 143.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 260970 | 에스앤디 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 261780 | 차백신연구소 | N | upper_wick_too_large |  | -1.17% | +1.17% | 108.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 263860 | 지니언스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.26% | -4.26% | 134.5 | 0.08 | ALLOW_ENTRY | candidate_id |
| breakout_small | 264850 | 이랜시스 | N | volume_ratio_lt_1p2 |  | -0.88% | +0.88% | 108.6 | 0.25 | ALLOW_ENTRY | candidate_id |
| breakout_small | 271560 | 오리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | +0.00% | 134.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 274090 | 켄코아에어로스페이스 | N | WAIT_RECLAIM_VWAP |  | +0.23% | -0.23% | 194.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 295310 | 에이치브이엠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 120.2 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 307180 | 아이엘 | N | volume_ratio_lt_1p2 |  | -0.12% | +0.12% | 139.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 307950 | 현대오토에버 | N | volume_ratio_lt_1p2 |  | -1.55% | +1.55% | 122.2 | 0.33 | ALLOW_ENTRY | candidate_id |
| breakout_small | 319400 | 현대무벡스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.82% | -1.82% | 172.5 | 1.19 | ALLOW_ENTRY | candidate_id |
| breakout_small | 332570 | PS일렉트로닉스 | N | volume_ratio_lt_1p2 |  | -7.43% | +7.43% | 196.7 | 0.62 | ALLOW_ENTRY | candidate_id |
| breakout_small | 336260 | 두산퓨얼셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 177.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| breakout_small | 336570 | 원텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.72% | -0.72% | 102.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 340570 | 티앤엘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.81% | -0.81% | 116.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.34% | -0.34% | 110.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 347850 | 디앤디파마텍 | N | trade_strength_lt_100 |  | +0.14% | -0.14% | 99.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 348340 | 뉴로메카 | N | trade_strength_lt_100 |  | -0.54% | +0.54% | 98.7 | 0.25 | ALLOW_ENTRY | candidate_id |
| breakout_small | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 132.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 373220 | LG에너지솔루션 | N | trade_strength_lt_100 |  | +2.88% | -2.88% | 97.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| breakout_small | 381620 | 제닉스로보틱스 | N | volume_ratio_lt_1p2 |  | -0.31% | +0.31% | 152.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 381970 | 케이카 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.96% | +0.00% | 134.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 382800 | 지앤비에스 에코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 121.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 388720 | 유일로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 175.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 396270 | 넥스트칩 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 100.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | -0.33% | +0.33% | 98.4 | 0.40 | ALLOW_ENTRY | candidate_id |
| breakout_small | 403870 | HPSP | N | trade_strength_lt_100 |  | +1.43% | -1.43% | 89.1 | 0.20 | ALLOW_ENTRY | candidate_id |
| breakout_small | 412350 | 레이저쎌 | N | trade_strength_lt_100 |  | +2.13% | -2.13% | 85.0 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.33% | -0.33% | 113.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 418420 | 라온텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.01% | -1.01% | 120.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 420570 | 제이투케이바이오 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 425040 | 티이엠씨 | N | trade_strength_lt_100 |  | +2.67% | -2.67% | 88.8 | 0.17 | ALLOW_ENTRY | candidate_id |
| breakout_small | 440110 | 파두 | N | volume_ratio_lt_1p2 |  | -3.20% | +3.20% | 162.2 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 443060 | HD현대마린솔루션 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 450080 | 에코프로머티 | N | trade_strength_lt_100 |  | +2.83% | -2.83% | 80.5 | 0.15 | ALLOW_ENTRY | candidate_id |
| breakout_small | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 106.3 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -11.54% | +11.54% | 164.9 | 0.19 | ALLOW_ENTRY | candidate_id |
| breakout_small | 456010 | 아이씨티케이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +5.12% | -5.12% | 134.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 459510 | 나우로보틱스 | N | upper_wick_too_large |  | +0.17% | -0.17% | 101.1 | 0.14 | ALLOW_ENTRY | candidate_id |
| breakout_small | 466100 | 클로봇 | N | volume_ratio_lt_1p2 |  | -1.37% | +1.37% | 242.3 | 0.21 | ALLOW_ENTRY | candidate_id |
| breakout_small | 491000 | 리브스메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.59% | -0.59% | 154.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 000270 | 기아 | N | volume_ratio_lt_1p2 |  | -1.80% | +1.80% | 103.6 | 0.30 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 000370 | 한화손해보험 | Y |  |  | +1.25% | -1.25% | 173.6 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 0004V0 | 엔비알모션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 118.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 0007C0 | 아크릴 | N | WAIT_RECLAIM_VWAP |  | +0.41% | -0.41% | 185.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 000880 | 한화 | N | volume_ratio_lt_1p2 |  | -1.12% | +1.12% | 101.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001200 | 유진투자증권 | N | volume_ratio_lt_1p2 |  | -2.42% | +2.42% | 165.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001510 | SK증권 | N | trade_strength_lt_100 |  | +3.10% | -3.10% | 86.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001740 | SK네트웍스 | N | trade_strength_lt_100 |  | +4.17% | -4.17% | 75.7 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001820 | 삼화콘덴서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 157.0 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 002780 | 진흥기업 | N | missing_one_min_reversal |  | +0.76% | +0.00% | 100.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003280 | 흥아해운 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 003350 | 한국화장품제조 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.15% | -0.15% | 109.6 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.43% | -1.43% | 111.9 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003670 | 포스코퓨처엠 | N | trade_strength_lt_100 |  | +1.73% | -1.73% | 94.5 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003690 | 코리안리 | N | volume_ratio_lt_1p2 |  | +0.31% | +0.00% | 151.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 004020 | 현대제철 | N | volume_ratio_lt_1p2 |  | -2.40% | +2.40% | 168.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 004370 | 농심 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 005010 | 휴스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.06% | -0.06% | 325.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 005880 | 대한해운 | N | trade_strength_lt_100 |  | +2.50% | -2.50% | 98.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 005950 | 이수화학 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 006400 | 삼성SDI | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.62% | +0.62% | 118.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 006800 | 미래에셋증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.32% | -1.32% | 113.7 | 0.68 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 007340 | DN오토모티브 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 009150 | 삼성전기 | N | volume_ratio_lt_1p2 |  | -4.47% | +4.47% | 118.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 011560 | 세보엠이씨 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.91% | -1.07% | 173.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 012330 | 현대모비스 | N | upper_wick_too_large |  | -0.30% | +0.30% | 115.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 012610 | 경인양행 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.99% | -1.99% | 136.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 012860 | 모베이스전자 | N | trade_strength_lt_100 |  | +2.44% | -2.44% | 90.3 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 018260 | 삼성에스디에스 | N | volume_ratio_lt_1p2 |  | -4.49% | +4.49% | 178.4 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 018880 | 한온시스템 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 019210 | 와이지-원 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 101.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 020150 | 롯데에너지머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.48% | -4.48% | 103.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 024060 | 흥구석유 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 027360 | 아주IB투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 93.3 | 0.69 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 027410 | BGF | N | volume_ratio_lt_1p2 |  | +0.19% | -0.19% | 223.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 028670 | 팬오션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.95% | -0.95% | 114.7 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 030000 | 제일기획 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 030190 | NICE평가정보 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 030530 | 원익홀딩스 | N | volume_ratio_lt_1p2 |  | -1.77% | +1.77% | 168.6 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 031330 | 에스에이엠티 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 033240 | 자화전자 | N | volume_ratio_lt_1p2 |  | -12.13% | +12.13% | 207.9 | 0.46 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.51% | -2.51% | 159.8 | 0.16 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 034220 | LG디스플레이 | N | volume_ratio_lt_1p2 |  | -2.94% | +2.94% | 130.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 035510 | 신세계 I&C | N | volume_ratio_lt_1p2 |  | -0.48% | +0.48% | 171.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 036460 | 한국가스공사 | N | volume_ratio_lt_1p2 |  | -0.78% | +0.78% | 204.6 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 036930 | 주성엔지니어링 | N | trade_strength_lt_100 |  | +8.95% | -8.95% | 60.7 | 2.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 037460 | 삼지전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 041190 | 우리기술투자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.31% | +0.31% | 163.0 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 041510 | 에스엠 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 043260 | 성호전자 | N | trade_strength_lt_100 |  | +0.45% | -0.45% | 92.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 049630 | 재영솔루텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.38% | -0.38% | 131.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 052400 | 코나아이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.09% | -0.28% | 149.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 052900 | KX하이텍 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 053610 | 프로텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 054450 | 텔레칩스 | Y |  |  | +0.88% | -0.88% | 150.4 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 056080 | 유진로봇 | N | volume_ratio_lt_1p2 |  | -3.83% | +3.83% | 188.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 061970 | LB세미콘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.85% | -0.85% | 115.3 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 064260 | 다날 | N | trade_strength_lt_100 |  | +3.25% | -3.25% | 57.3 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 066570 | LG전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 066970 | 엘앤에프 | N | trade_strength_lt_100 |  | +2.80% | -2.80% | 98.7 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 074600 | 원익QnC | N | volume_ratio_lt_1p2 |  | -1.02% | +1.02% | 138.6 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 077500 | 유니퀘스트 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 078600 | 대주전자재료 | N | trade_strength_lt_100 |  | +3.64% | -3.64% | 66.4 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 078930 | GS | N | volume_ratio_lt_1p2 |  | -4.62% | +4.62% | 188.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 081660 | 미스토홀딩스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 086520 | 에코프로 | N | trade_strength_lt_100 |  | +2.84% | -2.84% | 85.7 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 086980 | 쇼박스 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -4.42% | +4.42% | 137.0 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -2.34% | +2.34% | 106.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 090710 | 휴림로봇 | N | volume_ratio_lt_1p2 |  | -6.38% | +6.38% | 189.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 092300 | 현우산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.66% | -2.66% | 122.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 092460 | 한라IMS | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.61% | -0.48% | 143.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 092790 | 넥스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 094940 | 푸른기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 106.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 096770 | SK이노베이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 161.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 100790 | 미래에셋벤처투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 86.8 | 0.42 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 117730 | 티로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 165.6 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 122870 | 와이지엔터테인먼트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 125020 | 티씨머티리얼즈 | N | trade_strength_lt_100 |  | +5.07% | -5.07% | 85.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 125490 | 한라캐스트 | N | WAIT_RECLAIM_VWAP |  | -0.47% | +0.47% | 231.0 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 126600 | BGF에코머티리얼즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 126720 | 수산인더스트리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.19% | -0.33% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 128940 | 한미약품 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 200.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 136490 | 선진 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 138360 | 앤로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -4.01% | +4.01% | 100.1 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 138930 | BNK금융지주 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 140670 | 알에스오토메이션 | N | volume_ratio_lt_1p2 |  | -0.62% | +0.62% | 105.7 | 0.26 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 141080 | 리가켐바이오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 161390 | 한국타이어앤테크놀로지 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 181710 | NHN | N | volume_ratio_lt_1p2 |  | +0.13% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 187870 | 디바이스 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 189300 | 인텔리안테크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 196170 | 알테오젠 | N | trade_strength_lt_100 |  | +2.24% | -2.24% | 84.8 | 0.35 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 204320 | HL만도 | N | volume_ratio_lt_1p2 |  | -1.88% | +1.88% | 188.7 | 0.50 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 204620 | 글로벌텍스프리 | N | WAIT_RECLAIM_VWAP |  | +1.54% | -1.54% | 187.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 214320 | 이노션 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 215100 | 로보로보 | N | volume_ratio_lt_1p2 |  | +0.13% | -0.13% | 154.4 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 217500 | 러셀 | N | trade_strength_lt_100 |  | +1.92% | -1.92% | 91.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 234340 | 헥토파이낸셜 | N | trade_strength_lt_100 |  | +10.77% | -10.77% | 49.3 | 0.93 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 242040 | 나무기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 124.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 253840 | 수젠텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 259630 | 엠플러스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 143.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 260970 | 에스앤디 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 261780 | 차백신연구소 | N | upper_wick_too_large |  | -1.17% | +1.17% | 108.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 263860 | 지니언스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.26% | -4.26% | 134.5 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 264850 | 이랜시스 | N | volume_ratio_lt_1p2 |  | -0.88% | +0.88% | 108.6 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 271560 | 오리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | +0.00% | 134.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 274090 | 켄코아에어로스페이스 | N | WAIT_RECLAIM_VWAP |  | +0.23% | -0.23% | 194.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 295310 | 에이치브이엠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 120.2 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 307180 | 아이엘 | N | volume_ratio_lt_1p2 |  | -0.12% | +0.12% | 139.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 307950 | 현대오토에버 | N | volume_ratio_lt_1p2 |  | -1.55% | +1.55% | 122.2 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 319400 | 현대무벡스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.82% | -1.82% | 172.5 | 1.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 332570 | PS일렉트로닉스 | N | volume_ratio_lt_1p2 |  | -7.43% | +7.43% | 196.7 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 336260 | 두산퓨얼셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 177.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 336570 | 원텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.72% | -0.72% | 102.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 340570 | 티앤엘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.81% | -0.81% | 116.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.34% | -0.34% | 110.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 347850 | 디앤디파마텍 | N | trade_strength_lt_100 |  | +0.14% | -0.14% | 99.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 348340 | 뉴로메카 | N | trade_strength_lt_100 |  | -0.54% | +0.54% | 98.7 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 132.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 373220 | LG에너지솔루션 | N | trade_strength_lt_100 |  | +2.88% | -2.88% | 97.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 381620 | 제닉스로보틱스 | N | volume_ratio_lt_1p2 |  | -0.31% | +0.31% | 152.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 381970 | 케이카 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.96% | +0.00% | 134.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 382800 | 지앤비에스 에코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 121.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 388720 | 유일로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 175.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 396270 | 넥스트칩 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 100.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | -0.33% | +0.33% | 98.4 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 403870 | HPSP | N | trade_strength_lt_100 |  | +1.43% | -1.43% | 89.1 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 412350 | 레이저쎌 | N | trade_strength_lt_100 |  | +2.13% | -2.13% | 85.0 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.33% | -0.33% | 113.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 418420 | 라온텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.01% | -1.01% | 120.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 420570 | 제이투케이바이오 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 425040 | 티이엠씨 | N | trade_strength_lt_100 |  | +2.67% | -2.67% | 88.8 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 440110 | 파두 | N | volume_ratio_lt_1p2 |  | -3.20% | +3.20% | 162.2 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 443060 | HD현대마린솔루션 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 450080 | 에코프로머티 | N | trade_strength_lt_100 |  | +2.83% | -2.83% | 80.5 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 106.3 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -11.54% | +11.54% | 164.9 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 456010 | 아이씨티케이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +5.12% | -5.12% | 134.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 459510 | 나우로보틱스 | N | upper_wick_too_large |  | +0.17% | -0.17% | 101.1 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 466100 | 클로봇 | N | volume_ratio_lt_1p2 |  | -1.37% | +1.37% | 242.3 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 491000 | 리브스메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.59% | -0.59% | 154.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 000270 | 기아 | N | volume_ratio_lt_1p2 |  | -1.80% | +1.80% | 103.6 | 0.30 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 000370 | 한화손해보험 | Y |  |  | +1.25% | -1.25% | 173.6 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 0004V0 | 엔비알모션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 118.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 0007C0 | 아크릴 | N | WAIT_RECLAIM_VWAP |  | +0.41% | -0.41% | 185.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 000880 | 한화 | N | volume_ratio_lt_1p2 |  | -1.12% | +1.12% | 101.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001200 | 유진투자증권 | N | volume_ratio_lt_1p2 |  | -2.42% | +2.42% | 165.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001510 | SK증권 | N | trade_strength_lt_100 |  | +3.10% | -3.10% | 86.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001740 | SK네트웍스 | N | trade_strength_lt_100 |  | +4.17% | -4.17% | 75.7 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001820 | 삼화콘덴서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 157.0 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 002780 | 진흥기업 | N | missing_one_min_reversal |  | +0.76% | +0.00% | 100.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003280 | 흥아해운 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 003350 | 한국화장품제조 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.15% | -0.15% | 109.6 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.43% | -1.43% | 111.9 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003670 | 포스코퓨처엠 | N | trade_strength_lt_100 |  | +1.73% | -1.73% | 94.5 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003690 | 코리안리 | N | volume_ratio_lt_1p2 |  | +0.31% | +0.00% | 151.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 004020 | 현대제철 | N | volume_ratio_lt_1p2 |  | -2.40% | +2.40% | 168.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 004370 | 농심 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 005010 | 휴스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.06% | -0.06% | 325.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 005880 | 대한해운 | N | trade_strength_lt_100 |  | +2.50% | -2.50% | 98.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 005950 | 이수화학 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 006400 | 삼성SDI | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.62% | +0.62% | 118.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 006800 | 미래에셋증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.32% | -1.32% | 113.7 | 0.68 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 007340 | DN오토모티브 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 009150 | 삼성전기 | N | volume_ratio_lt_1p2 |  | -4.47% | +4.47% | 118.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 011560 | 세보엠이씨 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.91% | -1.07% | 173.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 012330 | 현대모비스 | N | upper_wick_too_large |  | -0.30% | +0.30% | 115.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 012610 | 경인양행 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.99% | -1.99% | 136.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 012860 | 모베이스전자 | N | trade_strength_lt_100 |  | +2.44% | -2.44% | 90.3 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 018260 | 삼성에스디에스 | N | volume_ratio_lt_1p2 |  | -4.49% | +4.49% | 178.4 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 018880 | 한온시스템 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 019210 | 와이지-원 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 101.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 020150 | 롯데에너지머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.48% | -4.48% | 103.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 024060 | 흥구석유 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 027360 | 아주IB투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 93.3 | 0.69 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 027410 | BGF | N | volume_ratio_lt_1p2 |  | +0.19% | -0.19% | 223.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 028670 | 팬오션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.95% | -0.95% | 114.7 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 030000 | 제일기획 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 030190 | NICE평가정보 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 030530 | 원익홀딩스 | N | volume_ratio_lt_1p2 |  | -1.77% | +1.77% | 168.6 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 031330 | 에스에이엠티 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 033240 | 자화전자 | N | volume_ratio_lt_1p2 |  | -12.13% | +12.13% | 207.9 | 0.46 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.51% | -2.51% | 159.8 | 0.16 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 034220 | LG디스플레이 | N | volume_ratio_lt_1p2 |  | -2.94% | +2.94% | 130.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 035510 | 신세계 I&C | N | volume_ratio_lt_1p2 |  | -0.48% | +0.48% | 171.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 036460 | 한국가스공사 | N | volume_ratio_lt_1p2 |  | -0.78% | +0.78% | 204.6 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 036930 | 주성엔지니어링 | N | trade_strength_lt_100 |  | +8.95% | -8.95% | 60.7 | 2.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 037460 | 삼지전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 041190 | 우리기술투자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.31% | +0.31% | 163.0 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 041510 | 에스엠 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 043260 | 성호전자 | N | trade_strength_lt_100 |  | +0.45% | -0.45% | 92.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 049630 | 재영솔루텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.38% | -0.38% | 131.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 052400 | 코나아이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.09% | -0.28% | 149.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 052900 | KX하이텍 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 053610 | 프로텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 054450 | 텔레칩스 | Y |  |  | +0.88% | -0.88% | 150.4 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 056080 | 유진로봇 | N | volume_ratio_lt_1p2 |  | -3.83% | +3.83% | 188.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 061970 | LB세미콘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.85% | -0.85% | 115.3 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 064260 | 다날 | N | trade_strength_lt_100 |  | +3.25% | -3.25% | 57.3 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 066570 | LG전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 066970 | 엘앤에프 | N | trade_strength_lt_100 |  | +2.80% | -2.80% | 98.7 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 074600 | 원익QnC | N | volume_ratio_lt_1p2 |  | -1.02% | +1.02% | 138.6 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 077500 | 유니퀘스트 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 078600 | 대주전자재료 | N | trade_strength_lt_100 |  | +3.64% | -3.64% | 66.4 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 078930 | GS | N | volume_ratio_lt_1p2 |  | -4.62% | +4.62% | 188.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 081660 | 미스토홀딩스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 086520 | 에코프로 | N | trade_strength_lt_100 |  | +2.84% | -2.84% | 85.7 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 086980 | 쇼박스 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -4.42% | +4.42% | 137.0 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -2.34% | +2.34% | 106.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 090710 | 휴림로봇 | N | volume_ratio_lt_1p2 |  | -6.38% | +6.38% | 189.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 092300 | 현우산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.66% | -2.66% | 122.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 092460 | 한라IMS | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.61% | -0.48% | 143.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 092790 | 넥스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 094940 | 푸른기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 106.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 096770 | SK이노베이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 161.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 100790 | 미래에셋벤처투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 86.8 | 0.42 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 117730 | 티로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 165.6 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 122870 | 와이지엔터테인먼트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 125020 | 티씨머티리얼즈 | N | trade_strength_lt_100 |  | +5.07% | -5.07% | 85.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 125490 | 한라캐스트 | N | WAIT_RECLAIM_VWAP |  | -0.47% | +0.47% | 231.0 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 126600 | BGF에코머티리얼즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 126720 | 수산인더스트리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.19% | -0.33% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 128940 | 한미약품 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 200.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 136490 | 선진 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 138360 | 앤로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -4.01% | +4.01% | 100.1 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 138930 | BNK금융지주 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 140670 | 알에스오토메이션 | N | volume_ratio_lt_1p2 |  | -0.62% | +0.62% | 105.7 | 0.26 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 141080 | 리가켐바이오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 161390 | 한국타이어앤테크놀로지 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 181710 | NHN | N | volume_ratio_lt_1p2 |  | +0.13% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 187870 | 디바이스 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 189300 | 인텔리안테크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 196170 | 알테오젠 | N | trade_strength_lt_100 |  | +2.24% | -2.24% | 84.8 | 0.35 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 204320 | HL만도 | N | volume_ratio_lt_1p2 |  | -1.88% | +1.88% | 188.7 | 0.50 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 204620 | 글로벌텍스프리 | N | WAIT_RECLAIM_VWAP |  | +1.54% | -1.54% | 187.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 214320 | 이노션 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 215100 | 로보로보 | N | volume_ratio_lt_1p2 |  | +0.13% | -0.13% | 154.4 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 217500 | 러셀 | N | trade_strength_lt_100 |  | +1.92% | -1.92% | 91.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 234340 | 헥토파이낸셜 | N | trade_strength_lt_100 |  | +10.77% | -10.77% | 49.3 | 0.93 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 242040 | 나무기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 124.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 253840 | 수젠텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 259630 | 엠플러스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 143.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 260970 | 에스앤디 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 261780 | 차백신연구소 | N | upper_wick_too_large |  | -1.17% | +1.17% | 108.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 263860 | 지니언스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.26% | -4.26% | 134.5 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 264850 | 이랜시스 | N | volume_ratio_lt_1p2 |  | -0.88% | +0.88% | 108.6 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 271560 | 오리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | +0.00% | 134.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 274090 | 켄코아에어로스페이스 | N | WAIT_RECLAIM_VWAP |  | +0.23% | -0.23% | 194.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 295310 | 에이치브이엠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 120.2 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 307180 | 아이엘 | N | volume_ratio_lt_1p2 |  | -0.12% | +0.12% | 139.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 307950 | 현대오토에버 | N | volume_ratio_lt_1p2 |  | -1.55% | +1.55% | 122.2 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 319400 | 현대무벡스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.82% | -1.82% | 172.5 | 1.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 332570 | PS일렉트로닉스 | N | volume_ratio_lt_1p2 |  | -7.43% | +7.43% | 196.7 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 336260 | 두산퓨얼셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 177.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 336570 | 원텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.72% | -0.72% | 102.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 340570 | 티앤엘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.81% | -0.81% | 116.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.34% | -0.34% | 110.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 347850 | 디앤디파마텍 | N | trade_strength_lt_100 |  | +0.14% | -0.14% | 99.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 348340 | 뉴로메카 | N | trade_strength_lt_100 |  | -0.54% | +0.54% | 98.7 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 132.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 373220 | LG에너지솔루션 | N | trade_strength_lt_100 |  | +2.88% | -2.88% | 97.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 381620 | 제닉스로보틱스 | N | volume_ratio_lt_1p2 |  | -0.31% | +0.31% | 152.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 381970 | 케이카 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.96% | +0.00% | 134.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 382800 | 지앤비에스 에코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 121.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 388720 | 유일로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 175.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 396270 | 넥스트칩 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 100.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | -0.33% | +0.33% | 98.4 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 403870 | HPSP | N | trade_strength_lt_100 |  | +1.43% | -1.43% | 89.1 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 412350 | 레이저쎌 | N | trade_strength_lt_100 |  | +2.13% | -2.13% | 85.0 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.33% | -0.33% | 113.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 418420 | 라온텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.01% | -1.01% | 120.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 420570 | 제이투케이바이오 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 425040 | 티이엠씨 | N | trade_strength_lt_100 |  | +2.67% | -2.67% | 88.8 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 440110 | 파두 | N | volume_ratio_lt_1p2 |  | -3.20% | +3.20% | 162.2 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 443060 | HD현대마린솔루션 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 450080 | 에코프로머티 | N | trade_strength_lt_100 |  | +2.83% | -2.83% | 80.5 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 106.3 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -11.54% | +11.54% | 164.9 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 456010 | 아이씨티케이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +5.12% | -5.12% | 134.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 459510 | 나우로보틱스 | N | upper_wick_too_large |  | +0.17% | -0.17% | 101.1 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 466100 | 클로봇 | N | volume_ratio_lt_1p2 |  | -1.37% | +1.37% | 242.3 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 491000 | 리브스메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.59% | -0.59% | 154.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 000270 | 기아 | N | volume_ratio_lt_1p2 |  | -1.80% | +1.80% | 103.6 | 0.30 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 000370 | 한화손해보험 | Y |  |  | +1.25% | -1.25% | 173.6 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 0004V0 | 엔비알모션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 118.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 0007C0 | 아크릴 | N | WAIT_RECLAIM_VWAP |  | +0.41% | -0.41% | 185.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 000880 | 한화 | N | volume_ratio_lt_1p2 |  | -1.12% | +1.12% | 101.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001200 | 유진투자증권 | N | volume_ratio_lt_1p2 |  | -2.42% | +2.42% | 165.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001510 | SK증권 | N | trade_strength_lt_100 |  | +3.10% | -3.10% | 86.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001740 | SK네트웍스 | N | trade_strength_lt_100 |  | +4.17% | -4.17% | 75.7 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001820 | 삼화콘덴서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 157.0 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 002780 | 진흥기업 | N | missing_one_min_reversal |  | +0.76% | +0.00% | 100.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003280 | 흥아해운 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 003350 | 한국화장품제조 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.15% | -0.15% | 109.6 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.43% | -1.43% | 111.9 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003670 | 포스코퓨처엠 | N | trade_strength_lt_100 |  | +1.73% | -1.73% | 94.5 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003690 | 코리안리 | N | volume_ratio_lt_1p2 |  | +0.31% | +0.00% | 151.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 004020 | 현대제철 | N | volume_ratio_lt_1p2 |  | -2.40% | +2.40% | 168.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 004370 | 농심 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 005010 | 휴스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.06% | -0.06% | 325.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 005880 | 대한해운 | N | trade_strength_lt_100 |  | +2.50% | -2.50% | 98.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 005950 | 이수화학 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 006400 | 삼성SDI | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.62% | +0.62% | 118.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 006800 | 미래에셋증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.32% | -1.32% | 113.7 | 0.68 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 007340 | DN오토모티브 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 009150 | 삼성전기 | N | volume_ratio_lt_1p2 |  | -4.47% | +4.47% | 118.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 011560 | 세보엠이씨 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.91% | -1.07% | 173.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 012330 | 현대모비스 | N | upper_wick_too_large |  | -0.30% | +0.30% | 115.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 012610 | 경인양행 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.99% | -1.99% | 136.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 012860 | 모베이스전자 | N | trade_strength_lt_100 |  | +2.44% | -2.44% | 90.3 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 018260 | 삼성에스디에스 | N | volume_ratio_lt_1p2 |  | -4.49% | +4.49% | 178.4 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 018880 | 한온시스템 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 019210 | 와이지-원 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 101.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 020150 | 롯데에너지머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.48% | -4.48% | 103.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 024060 | 흥구석유 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 027360 | 아주IB투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 93.3 | 0.69 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 027410 | BGF | N | volume_ratio_lt_1p2 |  | +0.19% | -0.19% | 223.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 028670 | 팬오션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.95% | -0.95% | 114.7 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 030000 | 제일기획 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 030190 | NICE평가정보 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 030530 | 원익홀딩스 | N | volume_ratio_lt_1p2 |  | -1.77% | +1.77% | 168.6 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 031330 | 에스에이엠티 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 033240 | 자화전자 | N | volume_ratio_lt_1p2 |  | -12.13% | +12.13% | 207.9 | 0.46 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.51% | -2.51% | 159.8 | 0.16 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 034220 | LG디스플레이 | N | volume_ratio_lt_1p2 |  | -2.94% | +2.94% | 130.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 035510 | 신세계 I&C | N | volume_ratio_lt_1p2 |  | -0.48% | +0.48% | 171.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 036460 | 한국가스공사 | N | volume_ratio_lt_1p2 |  | -0.78% | +0.78% | 204.6 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 036930 | 주성엔지니어링 | N | trade_strength_lt_100 |  | +8.95% | -8.95% | 60.7 | 2.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 037460 | 삼지전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 041190 | 우리기술투자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.31% | +0.31% | 163.0 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 041510 | 에스엠 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 043260 | 성호전자 | N | trade_strength_lt_100 |  | +0.45% | -0.45% | 92.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 049630 | 재영솔루텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.38% | -0.38% | 131.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 052400 | 코나아이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.09% | -0.28% | 149.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 052900 | KX하이텍 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 053610 | 프로텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 054450 | 텔레칩스 | N | volume_ratio_lt_1p2 |  | +0.88% | -0.88% | 150.4 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 056080 | 유진로봇 | N | volume_ratio_lt_1p2 |  | -3.83% | +3.83% | 188.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 061970 | LB세미콘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.85% | -0.85% | 115.3 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 064260 | 다날 | N | trade_strength_lt_100 |  | +3.25% | -3.25% | 57.3 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 066570 | LG전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 066970 | 엘앤에프 | N | trade_strength_lt_100 |  | +2.80% | -2.80% | 98.7 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 074600 | 원익QnC | N | volume_ratio_lt_1p2 |  | -1.02% | +1.02% | 138.6 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 077500 | 유니퀘스트 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 078600 | 대주전자재료 | N | trade_strength_lt_100 |  | +3.64% | -3.64% | 66.4 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 078930 | GS | N | volume_ratio_lt_1p2 |  | -4.62% | +4.62% | 188.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 081660 | 미스토홀딩스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 086520 | 에코프로 | N | trade_strength_lt_100 |  | +2.84% | -2.84% | 85.7 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 086980 | 쇼박스 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -4.42% | +4.42% | 137.0 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -2.34% | +2.34% | 106.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 090710 | 휴림로봇 | N | volume_ratio_lt_1p2 |  | -6.38% | +6.38% | 189.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 092300 | 현우산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.66% | -2.66% | 122.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 092460 | 한라IMS | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.61% | -0.48% | 143.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 092790 | 넥스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 094940 | 푸른기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 106.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 096770 | SK이노베이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 161.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 100790 | 미래에셋벤처투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 86.8 | 0.42 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 117730 | 티로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 165.6 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 122870 | 와이지엔터테인먼트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 125020 | 티씨머티리얼즈 | N | trade_strength_lt_100 |  | +5.07% | -5.07% | 85.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 125490 | 한라캐스트 | N | WAIT_RECLAIM_VWAP |  | -0.47% | +0.47% | 231.0 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 126600 | BGF에코머티리얼즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 126720 | 수산인더스트리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.19% | -0.33% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 128940 | 한미약품 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 200.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 136490 | 선진 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 138360 | 앤로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -4.01% | +4.01% | 100.1 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 138930 | BNK금융지주 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 140670 | 알에스오토메이션 | N | volume_ratio_lt_1p2 |  | -0.62% | +0.62% | 105.7 | 0.26 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 141080 | 리가켐바이오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 161390 | 한국타이어앤테크놀로지 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 181710 | NHN | N | volume_ratio_lt_1p2 |  | +0.13% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 187870 | 디바이스 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 189300 | 인텔리안테크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 196170 | 알테오젠 | N | trade_strength_lt_100 |  | +2.24% | -2.24% | 84.8 | 0.35 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 204320 | HL만도 | N | volume_ratio_lt_1p2 |  | -1.88% | +1.88% | 188.7 | 0.50 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 204620 | 글로벌텍스프리 | N | WAIT_RECLAIM_VWAP |  | +1.54% | -1.54% | 187.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 214320 | 이노션 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 215100 | 로보로보 | N | volume_ratio_lt_1p2 |  | +0.13% | -0.13% | 154.4 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 217500 | 러셀 | N | trade_strength_lt_100 |  | +1.92% | -1.92% | 91.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 234340 | 헥토파이낸셜 | N | trade_strength_lt_100 |  | +10.77% | -10.77% | 49.3 | 0.93 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 242040 | 나무기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 124.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 253840 | 수젠텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 259630 | 엠플러스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 143.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 260970 | 에스앤디 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 261780 | 차백신연구소 | N | upper_wick_too_large |  | -1.17% | +1.17% | 108.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 263860 | 지니언스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.26% | -4.26% | 134.5 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 264850 | 이랜시스 | N | volume_ratio_lt_1p2 |  | -0.88% | +0.88% | 108.6 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 271560 | 오리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | +0.00% | 134.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 274090 | 켄코아에어로스페이스 | N | WAIT_RECLAIM_VWAP |  | +0.23% | -0.23% | 194.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 295310 | 에이치브이엠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 120.2 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 307180 | 아이엘 | N | volume_ratio_lt_1p2 |  | -0.12% | +0.12% | 139.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 307950 | 현대오토에버 | N | volume_ratio_lt_1p2 |  | -1.55% | +1.55% | 122.2 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 319400 | 현대무벡스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.82% | -1.82% | 172.5 | 1.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 332570 | PS일렉트로닉스 | N | volume_ratio_lt_1p2 |  | -7.43% | +7.43% | 196.7 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 336260 | 두산퓨얼셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 177.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 336570 | 원텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.72% | -0.72% | 102.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 340570 | 티앤엘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.81% | -0.81% | 116.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.34% | -0.34% | 110.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 347850 | 디앤디파마텍 | N | trade_strength_lt_100 |  | +0.14% | -0.14% | 99.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 348340 | 뉴로메카 | N | trade_strength_lt_100 |  | -0.54% | +0.54% | 98.7 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 132.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 373220 | LG에너지솔루션 | N | trade_strength_lt_100 |  | +2.88% | -2.88% | 97.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 381620 | 제닉스로보틱스 | N | volume_ratio_lt_1p2 |  | -0.31% | +0.31% | 152.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 381970 | 케이카 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.96% | +0.00% | 134.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 382800 | 지앤비에스 에코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 121.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 388720 | 유일로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 175.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 396270 | 넥스트칩 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 100.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | -0.33% | +0.33% | 98.4 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 403870 | HPSP | N | trade_strength_lt_100 |  | +1.43% | -1.43% | 89.1 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 412350 | 레이저쎌 | N | trade_strength_lt_100 |  | +2.13% | -2.13% | 85.0 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.33% | -0.33% | 113.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 418420 | 라온텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.01% | -1.01% | 120.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 420570 | 제이투케이바이오 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 425040 | 티이엠씨 | N | trade_strength_lt_100 |  | +2.67% | -2.67% | 88.8 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 440110 | 파두 | N | volume_ratio_lt_1p2 |  | -3.20% | +3.20% | 162.2 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 443060 | HD현대마린솔루션 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 450080 | 에코프로머티 | N | trade_strength_lt_100 |  | +2.83% | -2.83% | 80.5 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 106.3 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -11.54% | +11.54% | 164.9 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 456010 | 아이씨티케이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +5.12% | -5.12% | 134.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 459510 | 나우로보틱스 | N | upper_wick_too_large |  | +0.17% | -0.17% | 101.1 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 466100 | 클로봇 | N | volume_ratio_lt_1p2 |  | -1.37% | +1.37% | 242.3 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 491000 | 리브스메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.59% | -0.59% | 154.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 000270 | 기아 | N | volume_ratio_lt_1p2 |  | -1.80% | +1.80% | 103.6 | 0.30 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 000370 | 한화손해보험 | N | volume_ratio_lt_1p2 |  | +1.25% | -1.25% | 173.6 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 0004V0 | 엔비알모션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 118.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 0007C0 | 아크릴 | N | WAIT_RECLAIM_VWAP |  | +0.41% | -0.41% | 185.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 000880 | 한화 | N | volume_ratio_lt_1p2 |  | -1.12% | +1.12% | 101.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001200 | 유진투자증권 | N | volume_ratio_lt_1p2 |  | -2.42% | +2.42% | 165.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001510 | SK증권 | N | trade_strength_lt_100 |  | +3.10% | -3.10% | 86.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001740 | SK네트웍스 | N | trade_strength_lt_100 |  | +4.17% | -4.17% | 75.7 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001820 | 삼화콘덴서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 157.0 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 002780 | 진흥기업 | N | missing_one_min_reversal |  | +0.76% | +0.00% | 100.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003280 | 흥아해운 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 003350 | 한국화장품제조 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.15% | -0.15% | 109.6 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.43% | -1.43% | 111.9 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003670 | 포스코퓨처엠 | N | trade_strength_lt_100 |  | +1.73% | -1.73% | 94.5 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003690 | 코리안리 | N | volume_ratio_lt_1p2 |  | +0.31% | +0.00% | 151.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 004020 | 현대제철 | N | volume_ratio_lt_1p2 |  | -2.40% | +2.40% | 168.5 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 004370 | 농심 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 005010 | 휴스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.06% | -0.06% | 325.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 005880 | 대한해운 | N | trade_strength_lt_100 |  | +2.50% | -2.50% | 98.7 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 005950 | 이수화학 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 006400 | 삼성SDI | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.62% | +0.62% | 118.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 006800 | 미래에셋증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.32% | -1.32% | 113.7 | 0.68 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 007340 | DN오토모티브 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 009150 | 삼성전기 | N | volume_ratio_lt_1p2 |  | -4.47% | +4.47% | 118.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 011560 | 세보엠이씨 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.91% | -1.07% | 173.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 012330 | 현대모비스 | N | upper_wick_too_large |  | -0.30% | +0.30% | 115.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 012610 | 경인양행 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.99% | -1.99% | 136.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 012860 | 모베이스전자 | N | trade_strength_lt_100 |  | +2.44% | -2.44% | 90.3 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 018260 | 삼성에스디에스 | N | volume_ratio_lt_1p2 |  | -4.49% | +4.49% | 178.4 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 018880 | 한온시스템 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 019210 | 와이지-원 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 101.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 020150 | 롯데에너지머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.48% | -4.48% | 103.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 024060 | 흥구석유 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 027360 | 아주IB투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 93.3 | 0.69 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 027410 | BGF | N | volume_ratio_lt_1p2 |  | +0.19% | -0.19% | 223.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 028670 | 팬오션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.95% | -0.95% | 114.7 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 030000 | 제일기획 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 030190 | NICE평가정보 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 030530 | 원익홀딩스 | N | volume_ratio_lt_1p2 |  | -1.77% | +1.77% | 168.6 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 031330 | 에스에이엠티 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 033240 | 자화전자 | N | volume_ratio_lt_1p2 |  | -12.13% | +12.13% | 207.9 | 0.46 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.51% | -2.51% | 159.8 | 0.16 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 034220 | LG디스플레이 | N | volume_ratio_lt_1p2 |  | -2.94% | +2.94% | 130.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 035510 | 신세계 I&C | N | volume_ratio_lt_1p2 |  | -0.48% | +0.48% | 171.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 036460 | 한국가스공사 | N | volume_ratio_lt_1p2 |  | -0.78% | +0.78% | 204.6 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 036930 | 주성엔지니어링 | N | trade_strength_lt_100 |  | +8.95% | -8.95% | 60.7 | 2.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 037460 | 삼지전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 041190 | 우리기술투자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.31% | +0.31% | 163.0 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 041510 | 에스엠 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 043260 | 성호전자 | N | trade_strength_lt_100 |  | +0.45% | -0.45% | 92.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 049630 | 재영솔루텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.38% | -0.38% | 131.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 052400 | 코나아이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.09% | -0.28% | 149.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 052900 | KX하이텍 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 053610 | 프로텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 054450 | 텔레칩스 | N | volume_ratio_lt_1p2 |  | +0.88% | -0.88% | 150.4 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 056080 | 유진로봇 | N | volume_ratio_lt_1p2 |  | -3.83% | +3.83% | 188.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 061970 | LB세미콘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.85% | -0.85% | 115.3 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 064260 | 다날 | N | trade_strength_lt_100 |  | +3.25% | -3.25% | 57.3 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 066570 | LG전자 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 066970 | 엘앤에프 | N | trade_strength_lt_100 |  | +2.80% | -2.80% | 98.7 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 074600 | 원익QnC | N | volume_ratio_lt_1p2 |  | -1.02% | +1.02% | 138.6 | 0.27 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 077500 | 유니퀘스트 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 078600 | 대주전자재료 | N | trade_strength_lt_100 |  | +3.64% | -3.64% | 66.4 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 078930 | GS | N | volume_ratio_lt_1p2 |  | -4.62% | +4.62% | 188.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 081660 | 미스토홀딩스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 086520 | 에코프로 | N | trade_strength_lt_100 |  | +2.84% | -2.84% | 85.7 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 086980 | 쇼박스 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -4.42% | +4.42% | 137.0 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -2.34% | +2.34% | 106.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 090710 | 휴림로봇 | N | volume_ratio_lt_1p2 |  | -6.38% | +6.38% | 189.1 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 092300 | 현우산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.66% | -2.66% | 122.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 092460 | 한라IMS | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.61% | -0.48% | 143.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 092790 | 넥스틸 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 094940 | 푸른기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 106.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 096770 | SK이노베이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 161.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 100790 | 미래에셋벤처투자 | N | trade_strength_lt_100 |  | +2.59% | -2.59% | 86.8 | 0.42 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 117730 | 티로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 165.6 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 122870 | 와이지엔터테인먼트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 125020 | 티씨머티리얼즈 | N | trade_strength_lt_100 |  | +5.07% | -5.07% | 85.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 125490 | 한라캐스트 | N | WAIT_RECLAIM_VWAP |  | -0.47% | +0.47% | 231.0 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 126600 | BGF에코머티리얼즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 126720 | 수산인더스트리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.19% | -0.33% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 128940 | 한미약품 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 200.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 136490 | 선진 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 138360 | 앤로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -4.01% | +4.01% | 100.1 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 138930 | BNK금융지주 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 140670 | 알에스오토메이션 | N | volume_ratio_lt_1p2 |  | -0.62% | +0.62% | 105.7 | 0.26 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 141080 | 리가켐바이오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 161390 | 한국타이어앤테크놀로지 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 181710 | NHN | N | volume_ratio_lt_1p2 |  | +0.13% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 187870 | 디바이스 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 189300 | 인텔리안테크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 196170 | 알테오젠 | N | trade_strength_lt_100 |  | +2.24% | -2.24% | 84.8 | 0.35 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 204320 | HL만도 | N | volume_ratio_lt_1p2 |  | -1.88% | +1.88% | 188.7 | 0.50 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 204620 | 글로벌텍스프리 | N | WAIT_RECLAIM_VWAP |  | +1.54% | -1.54% | 187.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 214320 | 이노션 | N | missing_momentum_log | registered_but_no_momentum_event | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 215100 | 로보로보 | N | volume_ratio_lt_1p2 |  | +0.13% | -0.13% | 154.4 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 217500 | 러셀 | N | trade_strength_lt_100 |  | +1.92% | -1.92% | 91.9 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 234340 | 헥토파이낸셜 | N | trade_strength_lt_100 |  | +10.77% | -10.77% | 49.3 | 0.93 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 242040 | 나무기술 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 124.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 253840 | 수젠텍 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 259630 | 엠플러스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 143.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 260970 | 에스앤디 | N | missing_momentum_log | time_policy_block_BLOCK_AFTER_ENTRY_CUTOFF | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 261780 | 차백신연구소 | N | upper_wick_too_large |  | -1.17% | +1.17% | 108.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 263860 | 지니언스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.26% | -4.26% | 134.5 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 264850 | 이랜시스 | N | volume_ratio_lt_1p2 |  | -0.88% | +0.88% | 108.6 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 271560 | 오리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | +0.00% | 134.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 274090 | 켄코아에어로스페이스 | N | WAIT_RECLAIM_VWAP |  | +0.23% | -0.23% | 194.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 295310 | 에이치브이엠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 120.2 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 307180 | 아이엘 | N | volume_ratio_lt_1p2 |  | -0.12% | +0.12% | 139.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 307950 | 현대오토에버 | N | volume_ratio_lt_1p2 |  | -1.55% | +1.55% | 122.2 | 0.33 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 319400 | 현대무벡스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.82% | -1.82% | 172.5 | 1.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 332570 | PS일렉트로닉스 | N | volume_ratio_lt_1p2 |  | -7.43% | +7.43% | 196.7 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 336260 | 두산퓨얼셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 177.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 336570 | 원텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.72% | -0.72% | 102.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 340570 | 티앤엘 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.81% | -0.81% | 116.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.34% | -0.34% | 110.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 347850 | 디앤디파마텍 | N | trade_strength_lt_100 |  | +0.14% | -0.14% | 99.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 348340 | 뉴로메카 | N | trade_strength_lt_100 |  | -0.54% | +0.54% | 98.7 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 132.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 373220 | LG에너지솔루션 | N | trade_strength_lt_100 |  | +2.88% | -2.88% | 97.8 | 0.18 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 381620 | 제닉스로보틱스 | N | volume_ratio_lt_1p2 |  | -0.31% | +0.31% | 152.5 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 381970 | 케이카 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.96% | +0.00% | 134.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 382800 | 지앤비에스 에코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 121.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 388720 | 유일로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.64% | -0.64% | 175.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 396270 | 넥스트칩 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 100.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | -0.33% | +0.33% | 98.4 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 403870 | HPSP | N | trade_strength_lt_100 |  | +1.43% | -1.43% | 89.1 | 0.20 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 412350 | 레이저쎌 | N | trade_strength_lt_100 |  | +2.13% | -2.13% | 85.0 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.33% | -0.33% | 113.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 418420 | 라온텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.01% | -1.01% | 120.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 420570 | 제이투케이바이오 | N | missing_momentum_log | time_policy_block_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 425040 | 티이엠씨 | N | trade_strength_lt_100 |  | +2.67% | -2.67% | 88.8 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 440110 | 파두 | N | volume_ratio_lt_1p2 |  | -3.20% | +3.20% | 162.2 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 443060 | HD현대마린솔루션 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 450080 | 에코프로머티 | N | trade_strength_lt_100 |  | +2.83% | -2.83% | 80.5 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 106.3 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -11.54% | +11.54% | 164.9 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 456010 | 아이씨티케이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +5.12% | -5.12% | 134.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 459510 | 나우로보틱스 | N | upper_wick_too_large |  | +0.17% | -0.17% | 101.1 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 466100 | 클로봇 | N | volume_ratio_lt_1p2 |  | -1.37% | +1.37% | 242.3 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 491000 | 리브스메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.59% | -0.59% | 154.0 | 0.00 | ALLOW_ENTRY | candidate_id |