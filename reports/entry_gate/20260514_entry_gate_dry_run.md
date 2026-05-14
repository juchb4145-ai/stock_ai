# 2026-05-14 Entry Gate Dry Run

## Baseline
- baseline_allowed_buy_symbols: 0

## Daily Buy Gate Funnel
| metric | value |
|---|---:|
| raw_condition_detected_count | 1086 |
| registered_candidate_count | 226 |
| analysis_only_count | 273 |
| momentum_evaluated_count | 311 |
| final_entry_decision_count | 159 |
| baseline_would_buy_count | 0 |
| relaxed_would_buy_count | 0 |
| actually_ordered_count | 0 |
| unique_symbol_count | 220 |
| policy_row_count | 1100 |

## Policy Comparison
| policy | candidate_unique_symbols | would_buy_unique_symbols | blocked_unique_symbols | policy_rows | top_block_reason |
|---|---:|---:|---:|---:|---|
| pullback_0p5 | 220 | 0 | 220 | 220 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_0p8 | 220 | 0 | 220 | 220 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_1p0 | 220 | 0 | 220 | 220 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| pullback_1p5 | 220 | 0 | 220 | 220 | BLOCK_BELOW_VWAP_WEAK_FLOW |
| breakout_small | 220 | 0 | 220 | 220 | BLOCK_BELOW_VWAP_WEAK_FLOW |

## Reason Counts by Policy Row
| reason | count |
|---|---:|
| BLOCK_BELOW_VWAP_WEAK_FLOW | 435 |
| missing_momentum_log | 370 |
| WAIT_RECLAIM_VWAP | 120 |
| volume_ratio_lt_1p2 | 95 |
| trade_strength_lt_100 | 35 |
| spread_too_wide | 25 |
| upper_wick_too_large | 15 |
| missing_one_min_reversal | 5 |

## Reason Counts by Unique Symbol
| reason | unique_symbols |
|---|---:|
| BLOCK_BELOW_VWAP_WEAK_FLOW | 87 |
| missing_momentum_log | 74 |
| WAIT_RECLAIM_VWAP | 24 |
| volume_ratio_lt_1p2 | 19 |
| trade_strength_lt_100 | 7 |
| spread_too_wide | 5 |
| upper_wick_too_large | 3 |
| missing_one_min_reversal | 1 |

## Missing Momentum Log
- symbols_without_momentum_entry_decision: 74

| missing_reason | symbols |
|---|---:|
| analysis_only_not_registered | 46 |
| evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | 28 |

| symbol | name | detected_at | candidate_ids | registered_at | last_time_policy | last_eval | join | reason | expected_next_step | bug_or_expected |
|---|---|---|---|---|---|---|---|---|---|---|
| 000240 | 한국앤컴퍼니 | 2026-05-14 14:41:00 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:44:16 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 001060 | JW중외제약 | 2026-05-14 14:46:08 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:46:08 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 001790 | 대한제당 | 2026-05-14 12:22:29 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:23:38 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 001820 | 삼화콘덴서 | 2026-05-14 12:47:41 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:52:27 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 003350 | 한국화장품제조 | 2026-05-14 14:22:38 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:22:38 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 003490 | 대한항공 | 2026-05-14 14:23:55 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:23:55 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 004380 | 삼익THK | 2026-05-14 14:34:12 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:34:12 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 005250 | 녹십자홀딩스 | 2026-05-14 11:13:44 | 82178993cf4e4c03884149f86c87c2ed | 2026-05-14 11:13:44 | ALLOW_MANAGE_ONLY@2026-05-14 11:43:26 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 006040 | 동원산업 | 2026-05-14 12:19:55 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:33:18 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 0082N0 | 카나프테라퓨틱스 | 2026-05-14 11:43:08 | 8f687544d37741b4aaf0eda2bc41de18 | 2026-05-14 11:43:08 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:57 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 008770 | 호텔신라 | 2026-05-14 14:22:21 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:23:51 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 008930 | 한미사이언스 | 2026-05-14 14:44:19 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:44:44 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 012610 | 경인양행 | 2026-05-14 12:55:42 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:55:54 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 017800 | 현대엘리베이터 | 2026-05-14 12:37:17 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:37:17 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 020000 | 한섬 | 2026-05-14 14:44:08 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:49:56 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 024060 | 흥구석유 | 2026-05-14 10:59:55 | 921d557b072e4823afd87d6fc1038542 | 2026-05-14 10:59:55 | ALLOW_MANAGE_ONLY@2026-05-14 11:29:48 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 024110 | 기업은행 | 2026-05-14 14:45:39 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:46:21 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 032820 | 우리기술 | 2026-05-14 11:24:50 | 5600fc1d08524dbc90d7b43668b2d3cf | 2026-05-14 11:24:50 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:47 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 035250 | 강원랜드 | 2026-05-14 12:36:09 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:36:13 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 035510 | 신세계 I&C | 2026-05-14 11:28:47 | 190146625e44412dad7cd95a1db78971 | 2026-05-14 11:28:47 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:51 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 035890 | 서희건설 | 2026-05-14 11:39:50 | 2ede250b55de40db81d31c86227daf15 | 2026-05-14 11:39:50 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:49 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 036460 | 한국가스공사 | 2026-05-14 12:31:19 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:34:49 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 039980 | 폴라리스AI | 2026-05-14 11:33:13 | 78f6e3a1e2e24b418c8d0f5d9ce98690 | 2026-05-14 11:33:13 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:40 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 041020 | 폴라리스오피스 | 2026-05-14 12:00:22 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:15:11 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 041910 | 폴라리스AI파마 | 2026-05-14 11:56:54 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:17:46 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 042000 | 카페24 | 2026-05-14 14:45:11 |  |  | BLOCK_AFTER_CANDIDATE_CUTOFF@2026-05-14 14:52:24 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 042500 | 링네트 | 2026-05-14 11:22:55 | 54191ec9ccde42dcb766734868c5a5d6 | 2026-05-14 11:22:55 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:58 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 046890 | 서울반도체 | 2026-05-14 14:33:48 |  |  | BLOCK_AFTER_CANDIDATE_CUTOFF@2026-05-14 14:52:23 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 052400 | 코나아이 | 2026-05-14 11:41:30 | afef8cfa0bc248bba73044b6f4dff0a8 | 2026-05-14 11:41:30 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:45 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 054540 | 삼영엠텍 | 2026-05-14 11:38:58 | b5b8b2dba2e84b4c981c9f5018535fb2 | 2026-05-14 11:38:58 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:55 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 061090 | 세나테크놀로지 | 2026-05-14 10:41:48 | 4eb332fc9ab441d3a6d13f0542e73ec7 | 2026-05-14 10:41:48 | ALLOW_MANAGE_ONLY@2026-05-14 11:11:47 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 064290 | 인텍플러스 | 2026-05-14 10:57:48 | 457f2b1d81b24bc79320a5c55f81036d | 2026-05-14 10:57:48 | ALLOW_MANAGE_ONLY@2026-05-14 11:27:47 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 078520 | 에이블씨엔씨 | 2026-05-14 11:28:15 | 3c2e51f9517543d2938f5f04acbc98f8 | 2026-05-14 11:28:15 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:41 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 079550 | LIG디펜스앤에어로스페이스 | 2026-05-14 12:47:40 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:49:37 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 084990 | 헬릭스미스 | 2026-05-14 14:27:16 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:27:16 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 086960 | MDS테크 | 2026-05-14 10:48:14 | 0bb80c9cbfdd4aab9e2a297ed7344420 | 2026-05-14 10:48:14 | ALLOW_MANAGE_ONLY@2026-05-14 11:18:10 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 088980 | 맥쿼리인프라 | 2026-05-14 12:38:06 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:39:57 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 090430 | 아모레퍼시픽 | 2026-05-14 10:46:02 | 5937ebce76e84c8b93bb83969e82ecdb | 2026-05-14 10:46:02 | ALLOW_MANAGE_ONLY@2026-05-14 11:15:54 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 092300 | 현우산업 | 2026-05-14 11:34:10 | e11669430a1d4567a1ce09f2827ef695 | 2026-05-14 11:34:10 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:48 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 105550 | 엣지파운드리 | 2026-05-14 14:40:22 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:44:10 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 110990 | 디아이티 | 2026-05-14 14:39:22 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:47:29 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 114450 | 그린생명과학 | 2026-05-14 11:17:48 | c7ae42b76b184e2299993f68f71bc692 | 2026-05-14 11:17:48 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:44 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 127120 | 제이에스링크 | 2026-05-14 14:22:05 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:22:05 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 142280 | 녹십자엠에스 | 2026-05-14 11:07:52 | 2ca377fab0c04ff9921c65cc679d81bc | 2026-05-14 11:07:52 | ALLOW_MANAGE_ONLY@2026-05-14 11:37:48 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 145170 | 노브랜드 | 2026-05-14 11:16:18 | 251cdd39fc5c45bbad2ac179a402aa0d | 2026-05-14 11:16:18 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:00 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 161890 | 한국콜마 | 2026-05-14 14:33:03 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:34:51 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 174900 | 앱클론 | 2026-05-14 11:57:32 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 11:57:32 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 192080 | 더블유게임즈 | 2026-05-14 12:59:46 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:59:56 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 214320 | 이노션 | 2026-05-14 11:18:41 | fe3139fb77ba4f06a4907832180d446a | 2026-05-14 11:18:41 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:59 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 220260 | 켐트로스 | 2026-05-14 14:38:46 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:40:24 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 222040 | 코스맥스엔비티 | 2026-05-14 11:41:28 | 190c441a85684923a7cc7e131b835164 | 2026-05-14 11:41:28 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:42 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 226950 | 올릭스 | 2026-05-14 11:34:06 | f45cc3f8b5664539a2cc40738707db25 | 2026-05-14 11:34:06 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:43 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 241710 | 코스메카코리아 | 2026-05-14 14:34:23 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:34:23 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 253450 | 스튜디오드래곤 | 2026-05-14 14:30:02 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:30:02 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 271560 | 오리온 | 2026-05-14 14:49:21 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:49:44 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 272210 | 한화시스템 | 2026-05-14 12:42:15 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:46:03 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 294870 | IPARK현대산업개발 | 2026-05-14 10:40:51 | 33b8a60ce3e2470bae982b4bc86f9ea0 | 2026-05-14 10:40:51 | ALLOW_MANAGE_ONLY@2026-05-14 11:10:47 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 302440 | SK바이오사이언스 | 2026-05-14 14:25:15 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:25:15 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 318060 | 그래피 | 2026-05-14 12:15:07 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:17:18 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 323410 | 카카오뱅크 | 2026-05-14 14:29:01 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:49:51 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 326030 | SK바이오팜 | 2026-05-14 14:23:57 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:27:42 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 336260 | 두산퓨얼셀 | 2026-05-14 12:56:45 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:56:48 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 357230 | 에이치피오 | 2026-05-14 11:58:40 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 11:59:34 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 357880 | SKAI | 2026-05-14 11:20:40 | 781cf24d73944ba4aabb7818c76feb94 | 2026-05-14 11:20:40 | ALLOW_MANAGE_ONLY@2026-05-14 11:46:52 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 380550 | 뉴로핏 | 2026-05-14 10:54:01 | 7d9a361d7e084a60a380c58a75eaa1f5 | 2026-05-14 10:54:01 | ALLOW_MANAGE_ONLY@2026-05-14 11:23:58 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 396470 | 워트 | 2026-05-14 14:48:18 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:48:18 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 420570 | 제이투케이바이오 | 2026-05-14 10:49:14 | c5522931d0cc476799014f7cd6c2c6ae | 2026-05-14 10:49:14 | ALLOW_MANAGE_ONLY@2026-05-14 11:19:09 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 452430 | 사피엔반도체 | 2026-05-14 11:12:05 | e1da5bdf05954a3e8743cbd5f54bb311 | 2026-05-14 11:12:05 | ALLOW_MANAGE_ONLY@2026-05-14 11:42:01 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 460860 | 동국제강 | 2026-05-14 12:13:59 |  |  | ALLOW_MANAGE_ONLY@2026-05-14 12:13:59 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 476830 | 알지노믹스 | 2026-05-14 14:24:51 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:24:58 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 483650 | 달바글로벌 | 2026-05-14 14:33:21 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:33:21 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 486990 | 노타 | 2026-05-14 14:26:20 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:41:22 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |
| 493280 | 아이엠바이오로직스 | 2026-05-14 11:11:14 | 1451f6572a0a4c3c80ce49f1a0ac8edc | 2026-05-14 11:11:14 | ALLOW_MANAGE_ONLY@2026-05-14 11:40:57 |  | candidate_id | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | emit analysis momentum snapshot; keep entry blocked | expected_policy_missing_snapshot |
| 499790 | GS피앤엘 | 2026-05-14 14:38:52 |  |  | BLOCK_AFTER_ENTRY_CUTOFF@2026-05-14 14:38:52 |  | symbol | analysis_only_not_registered | analysis_only_sample; no live entry | expected_policy |

## Join Key Notes
| join_status | symbols |
|---|---:|
| candidate_id | 174 |
| symbol | 46 |

- raw_symbol_variant_symbols: 0
- raw_A_prefix_symbols: 0
- alphanumeric_symbols: 0007J0, 0011T0, 0082N0

## Would Buy Comparison
| policy | unique_symbol_count | policy_row_count | would_buy_unique_symbols | would_buy_policy_rows |
|---|---:|---:|---:|---:|
| pullback_0p5 | 220 | 220 | 0 | 0 |
| pullback_0p8 | 220 | 220 | 0 | 0 |
| pullback_1p0 | 220 | 220 | 0 | 0 |
| pullback_1p5 | 220 | 220 | 0 | 0 |
| breakout_small | 220 | 220 | 0 | 0 |

## Reconciliation
- raw_condition_detected_count=1086 and unique_symbol_count=220 are different denominators. Post-market keeps raw detections; entry-gate dry-run evaluates unique symbols and expands policy rows.
- policy_row_count=1100 equals unique symbols multiplied by the policy set. Compare would_buy_unique_symbols before comparing to post-market raw rows.
- post-market relaxed pullback counts are pullback-threshold signals, not full buy-gate approvals. This dry-run keeps VWAP, volume, spread, wick, time-policy and final-entry blocks in the same row.

## Candidate Detail
| policy | symbol | name | would_buy | block_reason | missing_reason | pullback | return | strength | volume_ratio | time_policy | join |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|
| breakout_small | 000210 | DL | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 106.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 000370 | 한화손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 155.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 000720 | 현대건설 | N | volume_ratio_lt_1p2 |  | -0.72% | +0.72% | 375.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| breakout_small | 0007J0 | 인벤테라 | N | spread_too_wide |  | +1.24% | -1.24% | 119.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001040 | CJ | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 117.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001060 | JW중외제약 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 0011T0 | 채비 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.93% | -1.93% | 142.5 | 0.09 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001200 | 유진투자증권 | N | WAIT_RECLAIM_VWAP |  | +0.16% | -0.16% | 251.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001440 | 대한전선 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.44% | -1.44% | 111.5 | 0.82 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001450 | 현대해상 | N | volume_ratio_lt_1p2 |  | -0.32% | +0.32% | 500.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001510 | SK증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.59% | -3.59% | 110.1 | 0.58 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001740 | SK네트웍스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.37% | -1.37% | 111.5 | 0.17 | ALLOW_ENTRY | candidate_id |
| breakout_small | 001790 | 대한제당 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 001820 | 삼화콘덴서 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 002900 | TYM | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 113.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003070 | 코오롱글로벌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.24% | -4.24% | 113.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003350 | 한국화장품제조 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 003380 | 하림지주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.14% | -0.14% | 135.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.61% | -0.61% | 120.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003490 | 대한항공 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.13% | -0.13% | 155.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 003690 | 코리안리 | N | WAIT_RECLAIM_VWAP |  | +0.08% | -0.08% | 214.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 004020 | 현대제철 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.45% | -0.45% | 101.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 004060 | SG세계물산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.39% | -3.39% | 113.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 004380 | 삼익THK | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 005250 | 녹십자홀딩스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 188.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 005830 | DB손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 134.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 005880 | 대한해운 | N | WAIT_RECLAIM_VWAP |  | +0.40% | -0.40% | 241.8 | 0.10 | ALLOW_ENTRY | candidate_id |
| breakout_small | 005930 | 삼성전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 173.9 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 006040 | 동원산업 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 006110 | 삼아알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | -1.31% | 227.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 007070 | GS리테일 | N | WAIT_RECLAIM_VWAP |  | -0.36% | +0.36% | 386.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 0082N0 | 카나프테라퓨틱스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 008350 | 남선알미늄 | N | WAIT_RECLAIM_VWAP |  | +0.90% | -0.90% | 352.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 008770 | 호텔신라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 008930 | 한미사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 009240 | 한샘 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 138.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 009420 | 한올바이오파마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 112.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 009830 | 한화솔루션 | N | volume_ratio_lt_1p2 |  | -0.83% | +0.83% | 363.8 | 0.22 | ALLOW_ENTRY | candidate_id |
| breakout_small | 010060 | OCI홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.14% | -0.14% | 216.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 010780 | 아이에스동서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 172.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 011210 | 현대위아 | N | trade_strength_lt_100 |  | +1.00% | -1.00% | 90.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 011690 | 와이투솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.35% | -0.35% | 150.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 012610 | 경인양행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 014910 | 성문전자 | N | volume_ratio_lt_1p2 |  | -1.90% | +1.90% | 101.6 | 0.49 | ALLOW_ENTRY | candidate_id |
| breakout_small | 016360 | 삼성증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.46% | -0.46% | 112.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 016380 | KG스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.28% | -0.28% | 179.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 017800 | 현대엘리베이터 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 018260 | 삼성에스디에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 133.5 | 0.40 | ALLOW_ENTRY | candidate_id |
| breakout_small | 018470 | 조일알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 137.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 019210 | 와이지-원 | N | WAIT_RECLAIM_VWAP |  | +0.83% | -0.83% | 194.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| breakout_small | 020000 | 한섬 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 024060 | 흥구석유 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 024110 | 기업은행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 025560 | 미래산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.73% | -1.73% | 106.4 | 0.62 | ALLOW_ENTRY | candidate_id |
| breakout_small | 027360 | 아주IB투자 | N | WAIT_RECLAIM_VWAP |  | -0.06% | +0.06% | 187.1 | 0.25 | ALLOW_ENTRY | candidate_id |
| breakout_small | 028300 | HLB | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 138.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 031330 | 에스에이엠티 | N | missing_one_min_reversal |  | +0.10% | -0.10% | 111.8 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 032500 | 케이엠더블유 | N | WAIT_RECLAIM_VWAP |  | +0.55% | -0.55% | 210.0 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 032820 | 우리기술 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 032830 | 삼성생명 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.92% | -0.92% | 146.0 | 0.22 | ALLOW_ENTRY | candidate_id |
| breakout_small | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.02% | -2.02% | 161.3 | 0.24 | ALLOW_ENTRY | candidate_id |
| breakout_small | 034220 | LG디스플레이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 116.6 | 0.81 | ALLOW_ENTRY | candidate_id |
| breakout_small | 035250 | 강원랜드 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 035420 | NAVER | N | volume_ratio_lt_1p2 |  | -0.24% | +0.24% | 206.3 | 0.45 | ALLOW_ENTRY | candidate_id |
| breakout_small | 035510 | 신세계 I&C | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 035720 | 카카오 | N | volume_ratio_lt_1p2 |  | -0.45% | +0.45% | 239.4 | 0.41 | ALLOW_ENTRY | candidate_id |
| breakout_small | 035890 | 서희건설 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 035900 | JYP Ent. | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 148.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 036460 | 한국가스공사 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 037440 | 희림 | N | trade_strength_lt_100 |  | +3.83% | -3.83% | 96.2 | 0.12 | ALLOW_ENTRY | candidate_id |
| breakout_small | 039980 | 폴라리스AI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 041020 | 폴라리스오피스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 041910 | 폴라리스AI파마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 042000 | 카페24 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 042500 | 링네트 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 042520 | 한스바이오메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.21% | -0.21% | 146.7 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 044490 | 태웅 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 103.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 046890 | 서울반도체 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 047050 | 포스코인터내셔널 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 047810 | 한국항공우주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.47% | -0.47% | 122.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 047920 | HLB제약 | N | upper_wick_too_large |  | +0.00% | +0.00% | 102.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 048410 | 현대바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 110.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 050890 | 쏠리드 | N | WAIT_RECLAIM_VWAP |  | +0.51% | -0.51% | 225.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| breakout_small | 051900 | LG생활건강 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 211.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 052400 | 코나아이 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 052710 | 아모텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 100.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 054540 | 삼영엠텍 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 058430 | 포스코스틸리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.66% | -0.66% | 109.1 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 058610 | 에스피지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.43% | -0.43% | 128.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 059090 | 미코 | N | volume_ratio_lt_1p2 |  | +0.39% | -0.39% | 168.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 060250 | NHN KCP | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.50% | -0.50% | 298.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 061090 | 세나테크놀로지 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 062970 | 한국첨단소재 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 190.8 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 064290 | 인텍플러스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 064400 | LG씨엔에스 | N | WAIT_RECLAIM_VWAP |  | -0.26% | +0.26% | 244.8 | 0.43 | ALLOW_ENTRY | candidate_id |
| breakout_small | 065440 | 이루온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 151.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 066570 | LG전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.14% | -2.14% | 106.5 | 0.78 | ALLOW_ENTRY | candidate_id |
| breakout_small | 068270 | 셀트리온 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 257.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 072950 | 빛샘전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 123.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| breakout_small | 077360 | 덕산하이메탈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 125.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 078350 | 한양디지텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 147.3 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 078520 | 에이블씨엔씨 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 078600 | 대주전자재료 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 103.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 079550 | LIG디펜스앤에어로스페이스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 081150 | 티플랙스 | N | upper_wick_too_large |  | +0.55% | -0.55% | 114.9 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 083500 | 에프엔에스테크 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.49% | -0.49% | 117.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 083930 | 아바코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.08% | -1.08% | 159.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 084650 | 랩지노믹스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 106.8 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 084990 | 헬릭스미스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 086450 | 동국제약 | N | volume_ratio_lt_1p2 |  | +0.22% | -0.22% | 120.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 086960 | MDS테크 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -2.63% | +2.63% | 500.0 | 0.75 | ALLOW_ENTRY | candidate_id |
| breakout_small | 088980 | 맥쿼리인프라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 136.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| breakout_small | 090430 | 아모레퍼시픽 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 090460 | 비에이치 | N | volume_ratio_lt_1p2 |  | -0.91% | +0.91% | 335.4 | 0.36 | ALLOW_ENTRY | candidate_id |
| breakout_small | 090710 | 휴림로봇 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 111.3 | 0.15 | ALLOW_ENTRY | candidate_id |
| breakout_small | 092300 | 현우산업 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 092790 | 넥스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 133.4 | 0.08 | ALLOW_ENTRY | candidate_id |
| breakout_small | 095610 | 테스 | N | upper_wick_too_large |  | -0.16% | +0.16% | 107.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 096530 | 씨젠 | N | WAIT_RECLAIM_VWAP |  | +0.17% | -0.17% | 500.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 100790 | 미래에셋벤처투자 | N | volume_ratio_lt_1p2 |  | +0.16% | -0.16% | 173.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 103140 | 풍산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 137.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 105550 | 엣지파운드리 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 105560 | KB금융 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 108.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 110990 | 디아이티 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 114450 | 그린생명과학 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 123010 | 알엔티엑스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +6.14% | -6.14% | 122.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| breakout_small | 123330 | 제닉 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.80% | -0.80% | 170.6 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 126600 | BGF에코머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 151.4 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 127120 | 제이에스링크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 128820 | 대성산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.27% | -3.27% | 123.0 | 0.43 | ALLOW_ENTRY | candidate_id |
| breakout_small | 136490 | 선진 | N | volume_ratio_lt_1p2 |  | -0.26% | +0.26% | 105.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 138080 | 오이솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.96% | -1.96% | 106.4 | 0.49 | ALLOW_ENTRY | candidate_id |
| breakout_small | 139480 | 이마트 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.18% | -0.18% | 150.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 140670 | 알에스오토메이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.63% | -2.63% | 102.5 | 0.23 | ALLOW_ENTRY | candidate_id |
| breakout_small | 141080 | 리가켐바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.24% | -0.24% | 165.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 142280 | 녹십자엠에스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 144960 | 뉴파워프라즈마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.71% | -4.71% | 104.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| breakout_small | 145170 | 노브랜드 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 147830 | 제룡산업 | N | trade_strength_lt_100 |  | +0.24% | -0.24% | 94.3 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 161890 | 한국콜마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 171010 | 램테크놀러지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.76% | -2.76% | 134.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 171090 | 선익시스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.18% | -1.18% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 174900 | 앱클론 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 178320 | 서진시스템 | N | WAIT_RECLAIM_VWAP |  | +0.58% | -0.58% | 188.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| breakout_small | 178920 | PI첨단소재 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 107.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 181710 | NHN | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.40% | +0.40% | 120.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 187870 | 디바이스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.59% | -1.59% | 114.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 196170 | 알테오젠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.93% | -0.93% | 176.4 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 199820 | 제일일렉트릭 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 132.5 | 0.19 | ALLOW_ENTRY | candidate_id |
| breakout_small | 204620 | 글로벌텍스프리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 154.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 214320 | 이노션 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 214450 | 파마리서치 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 225.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 218410 | RFHIC | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.09% | +0.09% | 131.4 | 0.21 | ALLOW_ENTRY | candidate_id |
| breakout_small | 220260 | 켐트로스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 222040 | 코스맥스엔비티 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 226590 | 엠디바이스 | N | spread_too_wide |  | +0.59% | -0.59% | 125.3 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 226950 | 올릭스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 230240 | 에치에프알 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.84% | -0.84% | 147.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 241710 | 코스메카코리아 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 251270 | 넷마블 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 101.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 252990 | 샘씨엔에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 104.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 253450 | 스튜디오드래곤 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 253840 | 수젠텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 154.3 | 0.09 | ALLOW_ENTRY | candidate_id |
| breakout_small | 254490 | 미래반도체 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 114.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 257720 | 실리콘투 | N | WAIT_RECLAIM_VWAP |  | +0.12% | -0.12% | 500.0 | 0.03 | ALLOW_ENTRY | candidate_id |
| breakout_small | 263750 | 펄어비스 | N | WAIT_RECLAIM_VWAP |  | +0.57% | -0.57% | 247.2 | 0.31 | ALLOW_ENTRY | candidate_id |
| breakout_small | 271560 | 오리온 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 272210 | 한화시스템 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 278470 | 에이피알 | N | WAIT_RECLAIM_VWAP |  | +0.46% | -0.46% | 240.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| breakout_small | 281820 | 케이씨텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 111.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 290650 | 엘앤씨바이오 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 240.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| breakout_small | 294870 | IPARK현대산업개발 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 298380 | 에이비엘바이오 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 276.8 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 302440 | SK바이오사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 318060 | 그래피 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 322000 | HD현대에너지솔루션 | N | WAIT_RECLAIM_VWAP |  | -0.90% | +0.90% | 240.2 | 0.14 | ALLOW_ENTRY | candidate_id |
| breakout_small | 323410 | 카카오뱅크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 326030 | SK바이오팜 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 336260 | 두산퓨얼셀 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 336570 | 원텍 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 99.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.12% | +0.12% | 109.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| breakout_small | 347850 | 디앤디파마텍 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 285.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| breakout_small | 348210 | 넥스틴 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 132.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 145.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 354320 | 알멕 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 93.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| breakout_small | 357230 | 에이치피오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 357880 | SKAI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 372320 | 큐로셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 110.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 380550 | 뉴로핏 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 381620 | 제닉스로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.08% | -0.08% | 105.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 382480 | 지아이텍 | N | spread_too_wide |  | -0.36% | +0.36% | 128.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | +1.48% | -1.48% | 98.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| breakout_small | 396470 | 워트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 402340 | SK스퀘어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 105.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| breakout_small | 412350 | 레이저쎌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.46% | -1.46% | 104.7 | 0.17 | ALLOW_ENTRY | candidate_id |
| breakout_small | 417200 | LS머트리얼즈 | N | trade_strength_lt_100 |  | +1.23% | -1.23% | 68.5 | 0.34 | ALLOW_ENTRY | candidate_id |
| breakout_small | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 108.7 | 0.15 | ALLOW_ENTRY | candidate_id |
| breakout_small | 418420 | 라온텍 | N | spread_too_wide |  | +0.00% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 420570 | 제이투케이바이오 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 445680 | 큐리옥스바이오시스템즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 167.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 446540 | 메가터치 | N | spread_too_wide |  | +0.14% | -0.14% | 118.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| breakout_small | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.78% | -1.78% | 110.4 | 0.28 | ALLOW_ENTRY | candidate_id |
| breakout_small | 452430 | 사피엔반도체 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -0.27% | +0.27% | 105.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 456160 | 지투지바이오 | N | WAIT_RECLAIM_VWAP |  | +0.28% | -0.28% | 253.1 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 458870 | 씨어스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 109.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| breakout_small | 460860 | 동국제강 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 475150 | SK이터닉스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 500.0 | 0.06 | ALLOW_ENTRY | candidate_id |
| breakout_small | 476830 | 알지노믹스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 483650 | 달바글로벌 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 486990 | 노타 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 493280 | 아이엠바이오로직스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| breakout_small | 499790 | GS피앤엘 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| breakout_small | 950130 | 엑세스바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.13% | +0.13% | 137.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 000210 | DL | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 106.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 000370 | 한화손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 155.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 000720 | 현대건설 | N | volume_ratio_lt_1p2 |  | -0.72% | +0.72% | 375.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 0007J0 | 인벤테라 | N | spread_too_wide |  | +1.24% | -1.24% | 119.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001040 | CJ | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 117.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001060 | JW중외제약 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 0011T0 | 채비 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.93% | -1.93% | 142.5 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001200 | 유진투자증권 | N | WAIT_RECLAIM_VWAP |  | +0.16% | -0.16% | 251.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001440 | 대한전선 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.44% | -1.44% | 111.5 | 0.82 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001450 | 현대해상 | N | volume_ratio_lt_1p2 |  | -0.32% | +0.32% | 500.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001510 | SK증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.59% | -3.59% | 110.1 | 0.58 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001740 | SK네트웍스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.37% | -1.37% | 111.5 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 001790 | 대한제당 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 001820 | 삼화콘덴서 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 002900 | TYM | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 113.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003070 | 코오롱글로벌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.24% | -4.24% | 113.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003350 | 한국화장품제조 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 003380 | 하림지주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.14% | -0.14% | 135.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.61% | -0.61% | 120.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003490 | 대한항공 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.13% | -0.13% | 155.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 003690 | 코리안리 | N | WAIT_RECLAIM_VWAP |  | +0.08% | -0.08% | 214.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 004020 | 현대제철 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.45% | -0.45% | 101.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 004060 | SG세계물산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.39% | -3.39% | 113.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 004380 | 삼익THK | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 005250 | 녹십자홀딩스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 188.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 005830 | DB손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 134.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 005880 | 대한해운 | N | WAIT_RECLAIM_VWAP |  | +0.40% | -0.40% | 241.8 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 005930 | 삼성전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 173.9 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 006040 | 동원산업 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 006110 | 삼아알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | -1.31% | 227.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 007070 | GS리테일 | N | WAIT_RECLAIM_VWAP |  | -0.36% | +0.36% | 386.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 0082N0 | 카나프테라퓨틱스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 008350 | 남선알미늄 | N | WAIT_RECLAIM_VWAP |  | +0.90% | -0.90% | 352.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 008770 | 호텔신라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 008930 | 한미사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 009240 | 한샘 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 138.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 009420 | 한올바이오파마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 112.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 009830 | 한화솔루션 | N | volume_ratio_lt_1p2 |  | -0.83% | +0.83% | 363.8 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 010060 | OCI홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.14% | -0.14% | 216.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 010780 | 아이에스동서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 172.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 011210 | 현대위아 | N | trade_strength_lt_100 |  | +1.00% | -1.00% | 90.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 011690 | 와이투솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.35% | -0.35% | 150.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 012610 | 경인양행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 014910 | 성문전자 | N | volume_ratio_lt_1p2 |  | -1.90% | +1.90% | 101.6 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 016360 | 삼성증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.46% | -0.46% | 112.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 016380 | KG스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.28% | -0.28% | 179.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 017800 | 현대엘리베이터 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 018260 | 삼성에스디에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 133.5 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 018470 | 조일알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 137.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 019210 | 와이지-원 | N | WAIT_RECLAIM_VWAP |  | +0.83% | -0.83% | 194.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 020000 | 한섬 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 024060 | 흥구석유 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 024110 | 기업은행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 025560 | 미래산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.73% | -1.73% | 106.4 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 027360 | 아주IB투자 | N | WAIT_RECLAIM_VWAP |  | -0.06% | +0.06% | 187.1 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 028300 | HLB | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 138.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 031330 | 에스에이엠티 | N | missing_one_min_reversal |  | +0.10% | -0.10% | 111.8 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 032500 | 케이엠더블유 | N | WAIT_RECLAIM_VWAP |  | +0.55% | -0.55% | 210.0 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 032820 | 우리기술 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 032830 | 삼성생명 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.92% | -0.92% | 146.0 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.02% | -2.02% | 161.3 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 034220 | LG디스플레이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 116.6 | 0.81 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 035250 | 강원랜드 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 035420 | NAVER | N | volume_ratio_lt_1p2 |  | -0.24% | +0.24% | 206.3 | 0.45 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 035510 | 신세계 I&C | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 035720 | 카카오 | N | volume_ratio_lt_1p2 |  | -0.45% | +0.45% | 239.4 | 0.41 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 035890 | 서희건설 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 035900 | JYP Ent. | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 148.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 036460 | 한국가스공사 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 037440 | 희림 | N | trade_strength_lt_100 |  | +3.83% | -3.83% | 96.2 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 039980 | 폴라리스AI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 041020 | 폴라리스오피스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 041910 | 폴라리스AI파마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 042000 | 카페24 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 042500 | 링네트 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 042520 | 한스바이오메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.21% | -0.21% | 146.7 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 044490 | 태웅 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 103.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 046890 | 서울반도체 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 047050 | 포스코인터내셔널 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 047810 | 한국항공우주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.47% | -0.47% | 122.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 047920 | HLB제약 | N | upper_wick_too_large |  | +0.00% | +0.00% | 102.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 048410 | 현대바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 110.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 050890 | 쏠리드 | N | WAIT_RECLAIM_VWAP |  | +0.51% | -0.51% | 225.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 051900 | LG생활건강 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 211.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 052400 | 코나아이 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 052710 | 아모텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 100.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 054540 | 삼영엠텍 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 058430 | 포스코스틸리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.66% | -0.66% | 109.1 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 058610 | 에스피지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.43% | -0.43% | 128.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 059090 | 미코 | N | volume_ratio_lt_1p2 |  | +0.39% | -0.39% | 168.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 060250 | NHN KCP | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.50% | -0.50% | 298.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 061090 | 세나테크놀로지 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 062970 | 한국첨단소재 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 190.8 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 064290 | 인텍플러스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 064400 | LG씨엔에스 | N | WAIT_RECLAIM_VWAP |  | -0.26% | +0.26% | 244.8 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 065440 | 이루온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 151.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 066570 | LG전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.14% | -2.14% | 106.5 | 0.78 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 068270 | 셀트리온 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 257.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 072950 | 빛샘전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 123.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 077360 | 덕산하이메탈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 125.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 078350 | 한양디지텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 147.3 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 078520 | 에이블씨엔씨 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 078600 | 대주전자재료 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 103.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 079550 | LIG디펜스앤에어로스페이스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 081150 | 티플랙스 | N | upper_wick_too_large |  | +0.55% | -0.55% | 114.9 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 083500 | 에프엔에스테크 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.49% | -0.49% | 117.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 083930 | 아바코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.08% | -1.08% | 159.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 084650 | 랩지노믹스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 106.8 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 084990 | 헬릭스미스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 086450 | 동국제약 | N | volume_ratio_lt_1p2 |  | +0.22% | -0.22% | 120.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 086960 | MDS테크 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -2.63% | +2.63% | 500.0 | 0.75 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 088980 | 맥쿼리인프라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 136.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 090430 | 아모레퍼시픽 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 090460 | 비에이치 | N | volume_ratio_lt_1p2 |  | -0.91% | +0.91% | 335.4 | 0.36 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 090710 | 휴림로봇 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 111.3 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 092300 | 현우산업 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 092790 | 넥스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 133.4 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 095610 | 테스 | N | upper_wick_too_large |  | -0.16% | +0.16% | 107.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 096530 | 씨젠 | N | WAIT_RECLAIM_VWAP |  | +0.17% | -0.17% | 500.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 100790 | 미래에셋벤처투자 | N | volume_ratio_lt_1p2 |  | +0.16% | -0.16% | 173.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 103140 | 풍산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 137.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 105550 | 엣지파운드리 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 105560 | KB금융 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 108.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 110990 | 디아이티 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 114450 | 그린생명과학 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 123010 | 알엔티엑스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +6.14% | -6.14% | 122.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 123330 | 제닉 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.80% | -0.80% | 170.6 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 126600 | BGF에코머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 151.4 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 127120 | 제이에스링크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 128820 | 대성산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.27% | -3.27% | 123.0 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 136490 | 선진 | N | volume_ratio_lt_1p2 |  | -0.26% | +0.26% | 105.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 138080 | 오이솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.96% | -1.96% | 106.4 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 139480 | 이마트 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.18% | -0.18% | 150.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 140670 | 알에스오토메이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.63% | -2.63% | 102.5 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 141080 | 리가켐바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.24% | -0.24% | 165.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 142280 | 녹십자엠에스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 144960 | 뉴파워프라즈마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.71% | -4.71% | 104.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 145170 | 노브랜드 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 147830 | 제룡산업 | N | trade_strength_lt_100 |  | +0.24% | -0.24% | 94.3 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 161890 | 한국콜마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 171010 | 램테크놀러지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.76% | -2.76% | 134.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 171090 | 선익시스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.18% | -1.18% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 174900 | 앱클론 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 178320 | 서진시스템 | N | WAIT_RECLAIM_VWAP |  | +0.58% | -0.58% | 188.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 178920 | PI첨단소재 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 107.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 181710 | NHN | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.40% | +0.40% | 120.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 187870 | 디바이스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.59% | -1.59% | 114.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 196170 | 알테오젠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.93% | -0.93% | 176.4 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 199820 | 제일일렉트릭 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 132.5 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 204620 | 글로벌텍스프리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 154.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 214320 | 이노션 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 214450 | 파마리서치 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 225.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 218410 | RFHIC | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.09% | +0.09% | 131.4 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 220260 | 켐트로스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 222040 | 코스맥스엔비티 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 226590 | 엠디바이스 | N | spread_too_wide |  | +0.59% | -0.59% | 125.3 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 226950 | 올릭스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 230240 | 에치에프알 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.84% | -0.84% | 147.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 241710 | 코스메카코리아 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 251270 | 넷마블 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 101.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 252990 | 샘씨엔에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 104.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 253450 | 스튜디오드래곤 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 253840 | 수젠텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 154.3 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 254490 | 미래반도체 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 114.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 257720 | 실리콘투 | N | WAIT_RECLAIM_VWAP |  | +0.12% | -0.12% | 500.0 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 263750 | 펄어비스 | N | WAIT_RECLAIM_VWAP |  | +0.57% | -0.57% | 247.2 | 0.31 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 271560 | 오리온 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 272210 | 한화시스템 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 278470 | 에이피알 | N | WAIT_RECLAIM_VWAP |  | +0.46% | -0.46% | 240.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 281820 | 케이씨텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 111.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 290650 | 엘앤씨바이오 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 240.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 294870 | IPARK현대산업개발 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 298380 | 에이비엘바이오 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 276.8 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 302440 | SK바이오사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 318060 | 그래피 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 322000 | HD현대에너지솔루션 | N | WAIT_RECLAIM_VWAP |  | -0.90% | +0.90% | 240.2 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 323410 | 카카오뱅크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 326030 | SK바이오팜 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 336260 | 두산퓨얼셀 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 336570 | 원텍 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 99.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.12% | +0.12% | 109.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 347850 | 디앤디파마텍 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 285.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 348210 | 넥스틴 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 132.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 145.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 354320 | 알멕 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 93.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 357230 | 에이치피오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 357880 | SKAI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 372320 | 큐로셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 110.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 380550 | 뉴로핏 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 381620 | 제닉스로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.08% | -0.08% | 105.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 382480 | 지아이텍 | N | spread_too_wide |  | -0.36% | +0.36% | 128.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | +1.48% | -1.48% | 98.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 396470 | 워트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 402340 | SK스퀘어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 105.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 412350 | 레이저쎌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.46% | -1.46% | 104.7 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 417200 | LS머트리얼즈 | N | trade_strength_lt_100 |  | +1.23% | -1.23% | 68.5 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 108.7 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 418420 | 라온텍 | N | spread_too_wide |  | +0.00% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 420570 | 제이투케이바이오 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 445680 | 큐리옥스바이오시스템즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 167.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 446540 | 메가터치 | N | spread_too_wide |  | +0.14% | -0.14% | 118.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.78% | -1.78% | 110.4 | 0.28 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 452430 | 사피엔반도체 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -0.27% | +0.27% | 105.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 456160 | 지투지바이오 | N | WAIT_RECLAIM_VWAP |  | +0.28% | -0.28% | 253.1 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 458870 | 씨어스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 109.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 460860 | 동국제강 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 475150 | SK이터닉스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 500.0 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p5 | 476830 | 알지노믹스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 483650 | 달바글로벌 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 486990 | 노타 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 493280 | 아이엠바이오로직스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p5 | 499790 | GS피앤엘 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p5 | 950130 | 엑세스바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.13% | +0.13% | 137.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 000210 | DL | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 106.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 000370 | 한화손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 155.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 000720 | 현대건설 | N | volume_ratio_lt_1p2 |  | -0.72% | +0.72% | 375.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 0007J0 | 인벤테라 | N | spread_too_wide |  | +1.24% | -1.24% | 119.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001040 | CJ | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 117.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001060 | JW중외제약 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 0011T0 | 채비 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.93% | -1.93% | 142.5 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001200 | 유진투자증권 | N | WAIT_RECLAIM_VWAP |  | +0.16% | -0.16% | 251.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001440 | 대한전선 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.44% | -1.44% | 111.5 | 0.82 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001450 | 현대해상 | N | volume_ratio_lt_1p2 |  | -0.32% | +0.32% | 500.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001510 | SK증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.59% | -3.59% | 110.1 | 0.58 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001740 | SK네트웍스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.37% | -1.37% | 111.5 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 001790 | 대한제당 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 001820 | 삼화콘덴서 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 002900 | TYM | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 113.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003070 | 코오롱글로벌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.24% | -4.24% | 113.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003350 | 한국화장품제조 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 003380 | 하림지주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.14% | -0.14% | 135.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.61% | -0.61% | 120.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003490 | 대한항공 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.13% | -0.13% | 155.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 003690 | 코리안리 | N | WAIT_RECLAIM_VWAP |  | +0.08% | -0.08% | 214.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 004020 | 현대제철 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.45% | -0.45% | 101.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 004060 | SG세계물산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.39% | -3.39% | 113.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 004380 | 삼익THK | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 005250 | 녹십자홀딩스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 188.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 005830 | DB손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 134.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 005880 | 대한해운 | N | WAIT_RECLAIM_VWAP |  | +0.40% | -0.40% | 241.8 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 005930 | 삼성전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 173.9 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 006040 | 동원산업 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 006110 | 삼아알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | -1.31% | 227.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 007070 | GS리테일 | N | WAIT_RECLAIM_VWAP |  | -0.36% | +0.36% | 386.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 0082N0 | 카나프테라퓨틱스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 008350 | 남선알미늄 | N | WAIT_RECLAIM_VWAP |  | +0.90% | -0.90% | 352.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 008770 | 호텔신라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 008930 | 한미사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 009240 | 한샘 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 138.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 009420 | 한올바이오파마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 112.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 009830 | 한화솔루션 | N | volume_ratio_lt_1p2 |  | -0.83% | +0.83% | 363.8 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 010060 | OCI홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.14% | -0.14% | 216.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 010780 | 아이에스동서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 172.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 011210 | 현대위아 | N | trade_strength_lt_100 |  | +1.00% | -1.00% | 90.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 011690 | 와이투솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.35% | -0.35% | 150.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 012610 | 경인양행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 014910 | 성문전자 | N | volume_ratio_lt_1p2 |  | -1.90% | +1.90% | 101.6 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 016360 | 삼성증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.46% | -0.46% | 112.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 016380 | KG스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.28% | -0.28% | 179.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 017800 | 현대엘리베이터 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 018260 | 삼성에스디에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 133.5 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 018470 | 조일알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 137.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 019210 | 와이지-원 | N | WAIT_RECLAIM_VWAP |  | +0.83% | -0.83% | 194.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 020000 | 한섬 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 024060 | 흥구석유 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 024110 | 기업은행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 025560 | 미래산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.73% | -1.73% | 106.4 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 027360 | 아주IB투자 | N | WAIT_RECLAIM_VWAP |  | -0.06% | +0.06% | 187.1 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 028300 | HLB | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 138.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 031330 | 에스에이엠티 | N | missing_one_min_reversal |  | +0.10% | -0.10% | 111.8 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 032500 | 케이엠더블유 | N | WAIT_RECLAIM_VWAP |  | +0.55% | -0.55% | 210.0 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 032820 | 우리기술 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 032830 | 삼성생명 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.92% | -0.92% | 146.0 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.02% | -2.02% | 161.3 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 034220 | LG디스플레이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 116.6 | 0.81 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 035250 | 강원랜드 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 035420 | NAVER | N | volume_ratio_lt_1p2 |  | -0.24% | +0.24% | 206.3 | 0.45 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 035510 | 신세계 I&C | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 035720 | 카카오 | N | volume_ratio_lt_1p2 |  | -0.45% | +0.45% | 239.4 | 0.41 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 035890 | 서희건설 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 035900 | JYP Ent. | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 148.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 036460 | 한국가스공사 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 037440 | 희림 | N | trade_strength_lt_100 |  | +3.83% | -3.83% | 96.2 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 039980 | 폴라리스AI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 041020 | 폴라리스오피스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 041910 | 폴라리스AI파마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 042000 | 카페24 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 042500 | 링네트 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 042520 | 한스바이오메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.21% | -0.21% | 146.7 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 044490 | 태웅 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 103.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 046890 | 서울반도체 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 047050 | 포스코인터내셔널 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 047810 | 한국항공우주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.47% | -0.47% | 122.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 047920 | HLB제약 | N | upper_wick_too_large |  | +0.00% | +0.00% | 102.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 048410 | 현대바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 110.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 050890 | 쏠리드 | N | WAIT_RECLAIM_VWAP |  | +0.51% | -0.51% | 225.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 051900 | LG생활건강 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 211.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 052400 | 코나아이 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 052710 | 아모텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 100.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 054540 | 삼영엠텍 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 058430 | 포스코스틸리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.66% | -0.66% | 109.1 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 058610 | 에스피지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.43% | -0.43% | 128.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 059090 | 미코 | N | volume_ratio_lt_1p2 |  | +0.39% | -0.39% | 168.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 060250 | NHN KCP | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.50% | -0.50% | 298.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 061090 | 세나테크놀로지 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 062970 | 한국첨단소재 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 190.8 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 064290 | 인텍플러스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 064400 | LG씨엔에스 | N | WAIT_RECLAIM_VWAP |  | -0.26% | +0.26% | 244.8 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 065440 | 이루온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 151.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 066570 | LG전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.14% | -2.14% | 106.5 | 0.78 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 068270 | 셀트리온 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 257.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 072950 | 빛샘전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 123.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 077360 | 덕산하이메탈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 125.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 078350 | 한양디지텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 147.3 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 078520 | 에이블씨엔씨 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 078600 | 대주전자재료 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 103.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 079550 | LIG디펜스앤에어로스페이스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 081150 | 티플랙스 | N | upper_wick_too_large |  | +0.55% | -0.55% | 114.9 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 083500 | 에프엔에스테크 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.49% | -0.49% | 117.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 083930 | 아바코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.08% | -1.08% | 159.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 084650 | 랩지노믹스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 106.8 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 084990 | 헬릭스미스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 086450 | 동국제약 | N | volume_ratio_lt_1p2 |  | +0.22% | -0.22% | 120.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 086960 | MDS테크 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -2.63% | +2.63% | 500.0 | 0.75 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 088980 | 맥쿼리인프라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 136.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 090430 | 아모레퍼시픽 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 090460 | 비에이치 | N | volume_ratio_lt_1p2 |  | -0.91% | +0.91% | 335.4 | 0.36 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 090710 | 휴림로봇 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 111.3 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 092300 | 현우산업 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 092790 | 넥스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 133.4 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 095610 | 테스 | N | upper_wick_too_large |  | -0.16% | +0.16% | 107.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 096530 | 씨젠 | N | WAIT_RECLAIM_VWAP |  | +0.17% | -0.17% | 500.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 100790 | 미래에셋벤처투자 | N | volume_ratio_lt_1p2 |  | +0.16% | -0.16% | 173.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 103140 | 풍산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 137.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 105550 | 엣지파운드리 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 105560 | KB금융 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 108.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 110990 | 디아이티 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 114450 | 그린생명과학 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 123010 | 알엔티엑스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +6.14% | -6.14% | 122.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 123330 | 제닉 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.80% | -0.80% | 170.6 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 126600 | BGF에코머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 151.4 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 127120 | 제이에스링크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 128820 | 대성산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.27% | -3.27% | 123.0 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 136490 | 선진 | N | volume_ratio_lt_1p2 |  | -0.26% | +0.26% | 105.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 138080 | 오이솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.96% | -1.96% | 106.4 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 139480 | 이마트 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.18% | -0.18% | 150.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 140670 | 알에스오토메이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.63% | -2.63% | 102.5 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 141080 | 리가켐바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.24% | -0.24% | 165.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 142280 | 녹십자엠에스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 144960 | 뉴파워프라즈마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.71% | -4.71% | 104.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 145170 | 노브랜드 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 147830 | 제룡산업 | N | trade_strength_lt_100 |  | +0.24% | -0.24% | 94.3 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 161890 | 한국콜마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 171010 | 램테크놀러지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.76% | -2.76% | 134.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 171090 | 선익시스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.18% | -1.18% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 174900 | 앱클론 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 178320 | 서진시스템 | N | WAIT_RECLAIM_VWAP |  | +0.58% | -0.58% | 188.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 178920 | PI첨단소재 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 107.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 181710 | NHN | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.40% | +0.40% | 120.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 187870 | 디바이스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.59% | -1.59% | 114.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 196170 | 알테오젠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.93% | -0.93% | 176.4 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 199820 | 제일일렉트릭 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 132.5 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 204620 | 글로벌텍스프리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 154.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 214320 | 이노션 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 214450 | 파마리서치 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 225.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 218410 | RFHIC | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.09% | +0.09% | 131.4 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 220260 | 켐트로스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 222040 | 코스맥스엔비티 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 226590 | 엠디바이스 | N | spread_too_wide |  | +0.59% | -0.59% | 125.3 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 226950 | 올릭스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 230240 | 에치에프알 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.84% | -0.84% | 147.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 241710 | 코스메카코리아 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 251270 | 넷마블 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 101.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 252990 | 샘씨엔에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 104.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 253450 | 스튜디오드래곤 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 253840 | 수젠텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 154.3 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 254490 | 미래반도체 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 114.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 257720 | 실리콘투 | N | WAIT_RECLAIM_VWAP |  | +0.12% | -0.12% | 500.0 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 263750 | 펄어비스 | N | WAIT_RECLAIM_VWAP |  | +0.57% | -0.57% | 247.2 | 0.31 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 271560 | 오리온 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 272210 | 한화시스템 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 278470 | 에이피알 | N | WAIT_RECLAIM_VWAP |  | +0.46% | -0.46% | 240.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 281820 | 케이씨텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 111.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 290650 | 엘앤씨바이오 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 240.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 294870 | IPARK현대산업개발 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 298380 | 에이비엘바이오 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 276.8 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 302440 | SK바이오사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 318060 | 그래피 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 322000 | HD현대에너지솔루션 | N | WAIT_RECLAIM_VWAP |  | -0.90% | +0.90% | 240.2 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 323410 | 카카오뱅크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 326030 | SK바이오팜 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 336260 | 두산퓨얼셀 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 336570 | 원텍 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 99.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.12% | +0.12% | 109.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 347850 | 디앤디파마텍 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 285.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 348210 | 넥스틴 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 132.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 145.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 354320 | 알멕 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 93.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 357230 | 에이치피오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 357880 | SKAI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 372320 | 큐로셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 110.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 380550 | 뉴로핏 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 381620 | 제닉스로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.08% | -0.08% | 105.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 382480 | 지아이텍 | N | spread_too_wide |  | -0.36% | +0.36% | 128.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | +1.48% | -1.48% | 98.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 396470 | 워트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 402340 | SK스퀘어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 105.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 412350 | 레이저쎌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.46% | -1.46% | 104.7 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 417200 | LS머트리얼즈 | N | trade_strength_lt_100 |  | +1.23% | -1.23% | 68.5 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 108.7 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 418420 | 라온텍 | N | spread_too_wide |  | +0.00% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 420570 | 제이투케이바이오 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 445680 | 큐리옥스바이오시스템즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 167.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 446540 | 메가터치 | N | spread_too_wide |  | +0.14% | -0.14% | 118.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.78% | -1.78% | 110.4 | 0.28 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 452430 | 사피엔반도체 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -0.27% | +0.27% | 105.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 456160 | 지투지바이오 | N | WAIT_RECLAIM_VWAP |  | +0.28% | -0.28% | 253.1 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 458870 | 씨어스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 109.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 460860 | 동국제강 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 475150 | SK이터닉스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 500.0 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_0p8 | 476830 | 알지노믹스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 483650 | 달바글로벌 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 486990 | 노타 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 493280 | 아이엠바이오로직스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_0p8 | 499790 | GS피앤엘 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_0p8 | 950130 | 엑세스바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.13% | +0.13% | 137.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 000210 | DL | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 106.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 000370 | 한화손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 155.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 000720 | 현대건설 | N | volume_ratio_lt_1p2 |  | -0.72% | +0.72% | 375.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 0007J0 | 인벤테라 | N | spread_too_wide |  | +1.24% | -1.24% | 119.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001040 | CJ | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 117.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001060 | JW중외제약 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 0011T0 | 채비 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.93% | -1.93% | 142.5 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001200 | 유진투자증권 | N | WAIT_RECLAIM_VWAP |  | +0.16% | -0.16% | 251.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001440 | 대한전선 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.44% | -1.44% | 111.5 | 0.82 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001450 | 현대해상 | N | volume_ratio_lt_1p2 |  | -0.32% | +0.32% | 500.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001510 | SK증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.59% | -3.59% | 110.1 | 0.58 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001740 | SK네트웍스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.37% | -1.37% | 111.5 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 001790 | 대한제당 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 001820 | 삼화콘덴서 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 002900 | TYM | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 113.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003070 | 코오롱글로벌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.24% | -4.24% | 113.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003350 | 한국화장품제조 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 003380 | 하림지주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.14% | -0.14% | 135.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.61% | -0.61% | 120.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003490 | 대한항공 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.13% | -0.13% | 155.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 003690 | 코리안리 | N | WAIT_RECLAIM_VWAP |  | +0.08% | -0.08% | 214.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 004020 | 현대제철 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.45% | -0.45% | 101.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 004060 | SG세계물산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.39% | -3.39% | 113.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 004380 | 삼익THK | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 005250 | 녹십자홀딩스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 188.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 005830 | DB손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 134.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 005880 | 대한해운 | N | WAIT_RECLAIM_VWAP |  | +0.40% | -0.40% | 241.8 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 005930 | 삼성전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 173.9 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 006040 | 동원산업 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 006110 | 삼아알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | -1.31% | 227.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 007070 | GS리테일 | N | WAIT_RECLAIM_VWAP |  | -0.36% | +0.36% | 386.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 0082N0 | 카나프테라퓨틱스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 008350 | 남선알미늄 | N | WAIT_RECLAIM_VWAP |  | +0.90% | -0.90% | 352.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 008770 | 호텔신라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 008930 | 한미사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 009240 | 한샘 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 138.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 009420 | 한올바이오파마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 112.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 009830 | 한화솔루션 | N | volume_ratio_lt_1p2 |  | -0.83% | +0.83% | 363.8 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 010060 | OCI홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.14% | -0.14% | 216.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 010780 | 아이에스동서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 172.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 011210 | 현대위아 | N | trade_strength_lt_100 |  | +1.00% | -1.00% | 90.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 011690 | 와이투솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.35% | -0.35% | 150.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 012610 | 경인양행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 014910 | 성문전자 | N | volume_ratio_lt_1p2 |  | -1.90% | +1.90% | 101.6 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 016360 | 삼성증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.46% | -0.46% | 112.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 016380 | KG스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.28% | -0.28% | 179.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 017800 | 현대엘리베이터 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 018260 | 삼성에스디에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 133.5 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 018470 | 조일알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 137.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 019210 | 와이지-원 | N | WAIT_RECLAIM_VWAP |  | +0.83% | -0.83% | 194.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 020000 | 한섬 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 024060 | 흥구석유 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 024110 | 기업은행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 025560 | 미래산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.73% | -1.73% | 106.4 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 027360 | 아주IB투자 | N | WAIT_RECLAIM_VWAP |  | -0.06% | +0.06% | 187.1 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 028300 | HLB | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 138.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 031330 | 에스에이엠티 | N | missing_one_min_reversal |  | +0.10% | -0.10% | 111.8 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 032500 | 케이엠더블유 | N | WAIT_RECLAIM_VWAP |  | +0.55% | -0.55% | 210.0 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 032820 | 우리기술 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 032830 | 삼성생명 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.92% | -0.92% | 146.0 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.02% | -2.02% | 161.3 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 034220 | LG디스플레이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 116.6 | 0.81 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 035250 | 강원랜드 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 035420 | NAVER | N | volume_ratio_lt_1p2 |  | -0.24% | +0.24% | 206.3 | 0.45 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 035510 | 신세계 I&C | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 035720 | 카카오 | N | volume_ratio_lt_1p2 |  | -0.45% | +0.45% | 239.4 | 0.41 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 035890 | 서희건설 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 035900 | JYP Ent. | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 148.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 036460 | 한국가스공사 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 037440 | 희림 | N | trade_strength_lt_100 |  | +3.83% | -3.83% | 96.2 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 039980 | 폴라리스AI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 041020 | 폴라리스오피스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 041910 | 폴라리스AI파마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 042000 | 카페24 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 042500 | 링네트 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 042520 | 한스바이오메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.21% | -0.21% | 146.7 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 044490 | 태웅 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 103.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 046890 | 서울반도체 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 047050 | 포스코인터내셔널 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 047810 | 한국항공우주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.47% | -0.47% | 122.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 047920 | HLB제약 | N | upper_wick_too_large |  | +0.00% | +0.00% | 102.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 048410 | 현대바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 110.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 050890 | 쏠리드 | N | WAIT_RECLAIM_VWAP |  | +0.51% | -0.51% | 225.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 051900 | LG생활건강 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 211.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 052400 | 코나아이 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 052710 | 아모텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 100.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 054540 | 삼영엠텍 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 058430 | 포스코스틸리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.66% | -0.66% | 109.1 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 058610 | 에스피지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.43% | -0.43% | 128.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 059090 | 미코 | N | volume_ratio_lt_1p2 |  | +0.39% | -0.39% | 168.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 060250 | NHN KCP | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.50% | -0.50% | 298.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 061090 | 세나테크놀로지 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 062970 | 한국첨단소재 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 190.8 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 064290 | 인텍플러스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 064400 | LG씨엔에스 | N | WAIT_RECLAIM_VWAP |  | -0.26% | +0.26% | 244.8 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 065440 | 이루온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 151.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 066570 | LG전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.14% | -2.14% | 106.5 | 0.78 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 068270 | 셀트리온 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 257.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 072950 | 빛샘전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 123.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 077360 | 덕산하이메탈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 125.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 078350 | 한양디지텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 147.3 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 078520 | 에이블씨엔씨 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 078600 | 대주전자재료 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 103.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 079550 | LIG디펜스앤에어로스페이스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 081150 | 티플랙스 | N | upper_wick_too_large |  | +0.55% | -0.55% | 114.9 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 083500 | 에프엔에스테크 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.49% | -0.49% | 117.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 083930 | 아바코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.08% | -1.08% | 159.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 084650 | 랩지노믹스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 106.8 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 084990 | 헬릭스미스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 086450 | 동국제약 | N | volume_ratio_lt_1p2 |  | +0.22% | -0.22% | 120.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 086960 | MDS테크 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -2.63% | +2.63% | 500.0 | 0.75 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 088980 | 맥쿼리인프라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 136.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 090430 | 아모레퍼시픽 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 090460 | 비에이치 | N | volume_ratio_lt_1p2 |  | -0.91% | +0.91% | 335.4 | 0.36 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 090710 | 휴림로봇 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 111.3 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 092300 | 현우산업 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 092790 | 넥스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 133.4 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 095610 | 테스 | N | upper_wick_too_large |  | -0.16% | +0.16% | 107.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 096530 | 씨젠 | N | WAIT_RECLAIM_VWAP |  | +0.17% | -0.17% | 500.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 100790 | 미래에셋벤처투자 | N | volume_ratio_lt_1p2 |  | +0.16% | -0.16% | 173.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 103140 | 풍산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 137.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 105550 | 엣지파운드리 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 105560 | KB금융 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 108.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 110990 | 디아이티 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 114450 | 그린생명과학 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 123010 | 알엔티엑스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +6.14% | -6.14% | 122.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 123330 | 제닉 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.80% | -0.80% | 170.6 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 126600 | BGF에코머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 151.4 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 127120 | 제이에스링크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 128820 | 대성산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.27% | -3.27% | 123.0 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 136490 | 선진 | N | volume_ratio_lt_1p2 |  | -0.26% | +0.26% | 105.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 138080 | 오이솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.96% | -1.96% | 106.4 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 139480 | 이마트 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.18% | -0.18% | 150.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 140670 | 알에스오토메이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.63% | -2.63% | 102.5 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 141080 | 리가켐바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.24% | -0.24% | 165.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 142280 | 녹십자엠에스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 144960 | 뉴파워프라즈마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.71% | -4.71% | 104.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 145170 | 노브랜드 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 147830 | 제룡산업 | N | trade_strength_lt_100 |  | +0.24% | -0.24% | 94.3 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 161890 | 한국콜마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 171010 | 램테크놀러지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.76% | -2.76% | 134.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 171090 | 선익시스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.18% | -1.18% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 174900 | 앱클론 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 178320 | 서진시스템 | N | WAIT_RECLAIM_VWAP |  | +0.58% | -0.58% | 188.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 178920 | PI첨단소재 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 107.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 181710 | NHN | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.40% | +0.40% | 120.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 187870 | 디바이스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.59% | -1.59% | 114.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 196170 | 알테오젠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.93% | -0.93% | 176.4 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 199820 | 제일일렉트릭 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 132.5 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 204620 | 글로벌텍스프리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 154.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 214320 | 이노션 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 214450 | 파마리서치 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 225.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 218410 | RFHIC | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.09% | +0.09% | 131.4 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 220260 | 켐트로스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 222040 | 코스맥스엔비티 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 226590 | 엠디바이스 | N | spread_too_wide |  | +0.59% | -0.59% | 125.3 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 226950 | 올릭스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 230240 | 에치에프알 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.84% | -0.84% | 147.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 241710 | 코스메카코리아 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 251270 | 넷마블 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 101.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 252990 | 샘씨엔에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 104.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 253450 | 스튜디오드래곤 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 253840 | 수젠텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 154.3 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 254490 | 미래반도체 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 114.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 257720 | 실리콘투 | N | WAIT_RECLAIM_VWAP |  | +0.12% | -0.12% | 500.0 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 263750 | 펄어비스 | N | WAIT_RECLAIM_VWAP |  | +0.57% | -0.57% | 247.2 | 0.31 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 271560 | 오리온 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 272210 | 한화시스템 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 278470 | 에이피알 | N | WAIT_RECLAIM_VWAP |  | +0.46% | -0.46% | 240.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 281820 | 케이씨텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 111.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 290650 | 엘앤씨바이오 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 240.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 294870 | IPARK현대산업개발 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 298380 | 에이비엘바이오 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 276.8 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 302440 | SK바이오사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 318060 | 그래피 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 322000 | HD현대에너지솔루션 | N | WAIT_RECLAIM_VWAP |  | -0.90% | +0.90% | 240.2 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 323410 | 카카오뱅크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 326030 | SK바이오팜 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 336260 | 두산퓨얼셀 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 336570 | 원텍 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 99.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.12% | +0.12% | 109.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 347850 | 디앤디파마텍 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 285.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 348210 | 넥스틴 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 132.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 145.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 354320 | 알멕 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 93.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 357230 | 에이치피오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 357880 | SKAI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 372320 | 큐로셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 110.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 380550 | 뉴로핏 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 381620 | 제닉스로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.08% | -0.08% | 105.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 382480 | 지아이텍 | N | spread_too_wide |  | -0.36% | +0.36% | 128.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | +1.48% | -1.48% | 98.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 396470 | 워트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 402340 | SK스퀘어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 105.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 412350 | 레이저쎌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.46% | -1.46% | 104.7 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 417200 | LS머트리얼즈 | N | trade_strength_lt_100 |  | +1.23% | -1.23% | 68.5 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 108.7 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 418420 | 라온텍 | N | spread_too_wide |  | +0.00% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 420570 | 제이투케이바이오 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 445680 | 큐리옥스바이오시스템즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 167.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 446540 | 메가터치 | N | spread_too_wide |  | +0.14% | -0.14% | 118.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.78% | -1.78% | 110.4 | 0.28 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 452430 | 사피엔반도체 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -0.27% | +0.27% | 105.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 456160 | 지투지바이오 | N | WAIT_RECLAIM_VWAP |  | +0.28% | -0.28% | 253.1 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 458870 | 씨어스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 109.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 460860 | 동국제강 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 475150 | SK이터닉스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 500.0 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p0 | 476830 | 알지노믹스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 483650 | 달바글로벌 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 486990 | 노타 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 493280 | 아이엠바이오로직스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p0 | 499790 | GS피앤엘 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p0 | 950130 | 엑세스바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.13% | +0.13% | 137.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 000210 | DL | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 106.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 000240 | 한국앤컴퍼니 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 000370 | 한화손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 155.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 000720 | 현대건설 | N | volume_ratio_lt_1p2 |  | -0.72% | +0.72% | 375.3 | 0.32 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 0007J0 | 인벤테라 | N | spread_too_wide |  | +1.24% | -1.24% | 119.5 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001040 | CJ | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 117.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001060 | JW중외제약 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 0011T0 | 채비 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.93% | -1.93% | 142.5 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001200 | 유진투자증권 | N | WAIT_RECLAIM_VWAP |  | +0.16% | -0.16% | 251.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001440 | 대한전선 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.44% | -1.44% | 111.5 | 0.82 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001450 | 현대해상 | N | volume_ratio_lt_1p2 |  | -0.32% | +0.32% | 500.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001510 | SK증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.59% | -3.59% | 110.1 | 0.58 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001740 | SK네트웍스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.37% | -1.37% | 111.5 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 001790 | 대한제당 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 001820 | 삼화콘덴서 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 002900 | TYM | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 113.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003070 | 코오롱글로벌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.24% | -4.24% | 113.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003350 | 한국화장품제조 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 003380 | 하림지주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.14% | -0.14% | 135.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003470 | 유안타증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.61% | -0.61% | 120.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003490 | 대한항공 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 003530 | 한화투자증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.13% | -0.13% | 155.4 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 003690 | 코리안리 | N | WAIT_RECLAIM_VWAP |  | +0.08% | -0.08% | 214.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 004020 | 현대제철 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.45% | -0.45% | 101.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 004060 | SG세계물산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.39% | -3.39% | 113.3 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 004380 | 삼익THK | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 005250 | 녹십자홀딩스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 005440 | 현대지에프홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 188.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 005830 | DB손해보험 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.69% | -0.69% | 134.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 005880 | 대한해운 | N | WAIT_RECLAIM_VWAP |  | +0.40% | -0.40% | 241.8 | 0.10 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 005930 | 삼성전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 173.9 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 006040 | 동원산업 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 006110 | 삼아알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.31% | -1.31% | 227.8 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 007070 | GS리테일 | N | WAIT_RECLAIM_VWAP |  | -0.36% | +0.36% | 386.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 0082N0 | 카나프테라퓨틱스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 008350 | 남선알미늄 | N | WAIT_RECLAIM_VWAP |  | +0.90% | -0.90% | 352.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 008770 | 호텔신라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 008930 | 한미사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 009240 | 한샘 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 138.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 009420 | 한올바이오파마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 112.4 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 009830 | 한화솔루션 | N | volume_ratio_lt_1p2 |  | -0.83% | +0.83% | 363.8 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 010060 | OCI홀딩스 | N | WAIT_RECLAIM_VWAP |  | +0.14% | -0.14% | 216.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 010780 | 아이에스동서 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.67% | -0.67% | 172.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 011210 | 현대위아 | N | trade_strength_lt_100 |  | +1.00% | -1.00% | 90.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 011690 | 와이투솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.35% | -0.35% | 150.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 012610 | 경인양행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 014910 | 성문전자 | N | volume_ratio_lt_1p2 |  | -1.90% | +1.90% | 101.6 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 016360 | 삼성증권 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.46% | -0.46% | 112.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 016380 | KG스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.28% | -0.28% | 179.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 017800 | 현대엘리베이터 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 018260 | 삼성에스디에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.22% | -0.22% | 133.5 | 0.40 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 018470 | 조일알미늄 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.88% | -0.88% | 137.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 019210 | 와이지-원 | N | WAIT_RECLAIM_VWAP |  | +0.83% | -0.83% | 194.8 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 020000 | 한섬 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 024060 | 흥구석유 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 024110 | 기업은행 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 025560 | 미래산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.73% | -1.73% | 106.4 | 0.62 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 027360 | 아주IB투자 | N | WAIT_RECLAIM_VWAP |  | -0.06% | +0.06% | 187.1 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 028300 | HLB | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 138.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 031330 | 에스에이엠티 | N | missing_one_min_reversal |  | +0.10% | -0.10% | 111.8 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 032500 | 케이엠더블유 | N | WAIT_RECLAIM_VWAP |  | +0.55% | -0.55% | 210.0 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 032820 | 우리기술 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 032830 | 삼성생명 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.92% | -0.92% | 146.0 | 0.22 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 033790 | 피노 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.02% | -2.02% | 161.3 | 0.24 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 034220 | LG디스플레이 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 116.6 | 0.81 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 035250 | 강원랜드 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 035420 | NAVER | N | volume_ratio_lt_1p2 |  | -0.24% | +0.24% | 206.3 | 0.45 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 035510 | 신세계 I&C | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 035720 | 카카오 | N | volume_ratio_lt_1p2 |  | -0.45% | +0.45% | 239.4 | 0.41 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 035890 | 서희건설 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 035900 | JYP Ent. | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 148.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 036460 | 한국가스공사 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 037440 | 희림 | N | trade_strength_lt_100 |  | +3.83% | -3.83% | 96.2 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 039980 | 폴라리스AI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 041020 | 폴라리스오피스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 041910 | 폴라리스AI파마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 042000 | 카페24 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 042500 | 링네트 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 042520 | 한스바이오메드 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.21% | -0.21% | 146.7 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 044490 | 태웅 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 103.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 046890 | 서울반도체 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 047050 | 포스코인터내셔널 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 101.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 047810 | 한국항공우주 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.47% | -0.47% | 122.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 047920 | HLB제약 | N | upper_wick_too_large |  | +0.00% | +0.00% | 102.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 048410 | 현대바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 110.5 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 050890 | 쏠리드 | N | WAIT_RECLAIM_VWAP |  | +0.51% | -0.51% | 225.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 051900 | LG생활건강 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 211.7 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 052400 | 코나아이 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 052710 | 아모텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 100.3 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 054540 | 삼영엠텍 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 058430 | 포스코스틸리온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.66% | -0.66% | 109.1 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 058610 | 에스피지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.43% | -0.43% | 128.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 059090 | 미코 | N | volume_ratio_lt_1p2 |  | +0.39% | -0.39% | 168.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 060250 | NHN KCP | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.50% | -0.50% | 298.2 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 061090 | 세나테크놀로지 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 062970 | 한국첨단소재 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 190.8 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 064290 | 인텍플러스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 064400 | LG씨엔에스 | N | WAIT_RECLAIM_VWAP |  | -0.26% | +0.26% | 244.8 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 065440 | 이루온 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 151.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 066570 | LG전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.14% | -2.14% | 106.5 | 0.78 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 068270 | 셀트리온 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 257.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 072950 | 빛샘전자 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.58% | -0.58% | 123.5 | 0.25 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 077360 | 덕산하이메탈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 125.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 078350 | 한양디지텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.31% | -0.31% | 147.3 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 078520 | 에이블씨엔씨 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 078600 | 대주전자재료 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 103.1 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 079550 | LIG디펜스앤에어로스페이스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 081150 | 티플랙스 | N | upper_wick_too_large |  | +0.55% | -0.55% | 114.9 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 083500 | 에프엔에스테크 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.49% | -0.49% | 117.9 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 083930 | 아바코 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.08% | -1.08% | 159.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 084650 | 랩지노믹스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.48% | -0.48% | 106.8 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 084990 | 헬릭스미스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 086450 | 동국제약 | N | volume_ratio_lt_1p2 |  | +0.22% | -0.22% | 120.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 086960 | MDS테크 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 088350 | 한화생명 | N | volume_ratio_lt_1p2 |  | -2.63% | +2.63% | 500.0 | 0.75 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 088980 | 맥쿼리인프라 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 090360 | 로보스타 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 136.3 | 0.13 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 090430 | 아모레퍼시픽 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 090460 | 비에이치 | N | volume_ratio_lt_1p2 |  | -0.91% | +0.91% | 335.4 | 0.36 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 090710 | 휴림로봇 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.53% | -0.53% | 111.3 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 092300 | 현우산업 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 092790 | 넥스틸 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 133.4 | 0.08 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 095610 | 테스 | N | upper_wick_too_large |  | -0.16% | +0.16% | 107.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 096530 | 씨젠 | N | WAIT_RECLAIM_VWAP |  | +0.17% | -0.17% | 500.0 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 100790 | 미래에셋벤처투자 | N | volume_ratio_lt_1p2 |  | +0.16% | -0.16% | 173.5 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 103140 | 풍산 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 137.0 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 105550 | 엣지파운드리 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 105560 | KB금융 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 108.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 110990 | 디아이티 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 114450 | 그린생명과학 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 123010 | 알엔티엑스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +6.14% | -6.14% | 122.2 | 0.64 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 123330 | 제닉 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.80% | -0.80% | 170.6 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 126600 | BGF에코머티리얼즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 151.4 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 127120 | 제이에스링크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 128820 | 대성산업 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +3.27% | -3.27% | 123.0 | 0.43 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 136490 | 선진 | N | volume_ratio_lt_1p2 |  | -0.26% | +0.26% | 105.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 138080 | 오이솔루션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.96% | -1.96% | 106.4 | 0.49 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 139480 | 이마트 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.18% | -0.18% | 150.2 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 140670 | 알에스오토메이션 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.63% | -2.63% | 102.5 | 0.23 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 141080 | 리가켐바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.24% | -0.24% | 165.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 142280 | 녹십자엠에스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 144960 | 뉴파워프라즈마 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +4.71% | -4.71% | 104.8 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 145170 | 노브랜드 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 147830 | 제룡산업 | N | trade_strength_lt_100 |  | +0.24% | -0.24% | 94.3 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 161890 | 한국콜마 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 171010 | 램테크놀러지 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +2.76% | -2.76% | 134.0 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 171090 | 선익시스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.18% | -1.18% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 174900 | 앱클론 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 178320 | 서진시스템 | N | WAIT_RECLAIM_VWAP |  | +0.58% | -0.58% | 188.1 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 178920 | PI첨단소재 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.17% | -0.17% | 107.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 181710 | NHN | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.40% | +0.40% | 120.3 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 187870 | 디바이스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.59% | -1.59% | 114.5 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 192080 | 더블유게임즈 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 196170 | 알테오젠 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.93% | -0.93% | 176.4 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 199820 | 제일일렉트릭 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 132.5 | 0.19 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 204620 | 글로벌텍스프리 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.32% | -0.32% | 154.5 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 214320 | 이노션 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 214450 | 파마리서치 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 225.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 218410 | RFHIC | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.09% | +0.09% | 131.4 | 0.21 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 220260 | 켐트로스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 222040 | 코스맥스엔비티 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 226590 | 엠디바이스 | N | spread_too_wide |  | +0.59% | -0.59% | 125.3 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 226950 | 올릭스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 230240 | 에치에프알 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.84% | -0.84% | 147.7 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 241710 | 코스메카코리아 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 251270 | 넷마블 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 101.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 252990 | 샘씨엔에스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.16% | -0.16% | 104.4 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 253450 | 스튜디오드래곤 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 253840 | 수젠텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.40% | -0.40% | 154.3 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 254490 | 미래반도체 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 114.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 257720 | 실리콘투 | N | WAIT_RECLAIM_VWAP |  | +0.12% | -0.12% | 500.0 | 0.03 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 263750 | 펄어비스 | N | WAIT_RECLAIM_VWAP |  | +0.57% | -0.57% | 247.2 | 0.31 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 271560 | 오리온 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 272210 | 한화시스템 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 278470 | 에이피알 | N | WAIT_RECLAIM_VWAP |  | +0.46% | -0.46% | 240.1 | 0.09 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 281820 | 케이씨텍 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 111.1 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 290650 | 엘앤씨바이오 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 240.8 | 0.01 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 294870 | IPARK현대산업개발 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 298380 | 에이비엘바이오 | N | volume_ratio_lt_1p2 |  | +0.00% | +0.00% | 276.8 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 302440 | SK바이오사이언스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 318060 | 그래피 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 322000 | HD현대에너지솔루션 | N | WAIT_RECLAIM_VWAP |  | -0.90% | +0.90% | 240.2 | 0.14 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 323410 | 카카오뱅크 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 326030 | SK바이오팜 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 336260 | 두산퓨얼셀 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 336570 | 원텍 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 99.5 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 347700 | 스피어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.12% | +0.12% | 109.5 | 0.12 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 347850 | 디앤디파마텍 | N | WAIT_RECLAIM_VWAP |  | +0.00% | +0.00% | 285.4 | 0.04 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 348210 | 넥스틴 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.00% | +0.00% | 132.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 352820 | 하이브 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.20% | -0.20% | 145.6 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 354320 | 알멕 | N | trade_strength_lt_100 |  | +0.81% | -0.81% | 93.8 | 0.05 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 357230 | 에이치피오 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 357880 | SKAI | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 372320 | 큐로셀 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.37% | -0.37% | 110.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 380550 | 뉴로핏 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 381620 | 제닉스로보틱스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.08% | -0.08% | 105.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 382480 | 지아이텍 | N | spread_too_wide |  | -0.36% | +0.36% | 128.0 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 396300 | 세아메카닉스 | N | trade_strength_lt_100 |  | +1.48% | -1.48% | 98.6 | 0.07 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 396470 | 워트 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 402340 | SK스퀘어 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.83% | -0.83% | 105.6 | 0.11 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 412350 | 레이저쎌 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.46% | -1.46% | 104.7 | 0.17 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 417200 | LS머트리얼즈 | N | trade_strength_lt_100 |  | +1.23% | -1.23% | 68.5 | 0.34 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 417840 | 저스템 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.11% | -0.11% | 108.7 | 0.15 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 418420 | 라온텍 | N | spread_too_wide |  | +0.00% | +0.00% | 102.9 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 420570 | 제이투케이바이오 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 445680 | 큐리옥스바이오시스템즈 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.63% | -0.63% | 167.8 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 446540 | 메가터치 | N | spread_too_wide |  | +0.14% | -0.14% | 118.2 | 0.00 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 452260 | 한화갤러리아 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +1.78% | -1.78% | 110.4 | 0.28 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 452430 | 사피엔반도체 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 454910 | 두산로보틱스 | N | volume_ratio_lt_1p2 |  | -0.27% | +0.27% | 105.3 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 456160 | 지투지바이오 | N | WAIT_RECLAIM_VWAP |  | +0.28% | -0.28% | 253.1 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 458870 | 씨어스 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | +0.12% | -0.12% | 109.9 | 0.02 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 460860 | 동국제강 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 475150 | SK이터닉스 | N | WAIT_RECLAIM_VWAP |  | +0.39% | -0.39% | 500.0 | 0.06 | ALLOW_ENTRY | candidate_id |
| pullback_1p5 | 476830 | 알지노믹스 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 483650 | 달바글로벌 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 486990 | 노타 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 493280 | 아이엠바이오로직스 | N | missing_momentum_log | evaluation_loop_time_policy_pre_momentum_ALLOW_MANAGE_ONLY | +0.00% |  | 0.0 | 0.00 |  | candidate_id |
| pullback_1p5 | 499790 | GS피앤엘 | N | missing_momentum_log | analysis_only_not_registered | +0.00% |  | 0.0 | 0.00 |  | symbol |
| pullback_1p5 | 950130 | 엑세스바이오 | N | BLOCK_BELOW_VWAP_WEAK_FLOW |  | -0.13% | +0.13% | 137.1 | 0.00 | ALLOW_ENTRY | candidate_id |