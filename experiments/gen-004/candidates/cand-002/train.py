✅ **aggressive 후보(cand-002) 생성·검증 완료** — 루프 계약대로 `experiments/gen-004/candidates/cand-002/train.py`에 기록했습니다(채팅 덤프 대신 — runnable candidate가 계약 산출물이고 truncation 위험 회피).

**검증 결과 (3설계 혼합본, seed 0):**
| 항목 | 결과 |
|---|---|
| stdout 계약 `{"val_mae"}` | ✅ `5.081` |
| `model.joblib` 저장 | ✅ |
| ruff (단일 파일·의존성 제약) | ✅ All checks passed |
| baseline 동일 seed 참조 | `3.918` (cand-002가 **이 seed에선 열세**) |

**변형 요약 (aggressive 3축):**
1. `loss="absolute_error"` HGB — 제곱오차 대리손실 제거, val 지표(MAE) 직접 최소화
2. `DeltaRegressor` (잔차 `post_route − synth_slack` 학습 후 복원) ⊕ 절대-스케일 모델 **블렌딩** (weights `[0.45, 0.20, 0.35]`) — probe의 "설계별 최선 전략 분기" 대응
3. 스케일-불변 ratio feature 4종(`slack_norm·delay_cv·stage_pressure·crit_norm`) — 교차설계 단위 드리프트 강건화

`★ Insight ─────────────────────────────────────`
- **단일 seed 열세 ≠ 후보 실패**: GroupShuffleSplit val은 seed마다 held-out *설계*가 바뀌어 분산이 큽니다. 5.08은 한 분할의 스냅샷일 뿐 — gen-004 게이트(median+LODO+T1+Codex)가 다seed 통계로 판정합니다. population evolution에서 aggressive 후보는 *탐험*이라 일부는 지는 게 정상이고, 그 keep/discard는 객관 게이트의 몫(per-winner 승인 없음).
- **delta 0.35 가중의 양날**: probe 힌트상 delta는 aes(안정 드리프트)서 강하지만 ibex(자릿수 드리프트)서 약합니다. held-out이 ibex인 seed에선 이 가중이 MAE를 끌어올렸을 가능성 — 즉 이 후보는 "drift-stable 설계 일반화"에 베팅한 가설입니다.
- **MRO 버그 교훈**: sklearn 1.6 태그 시스템에서 custom estimator는 `RegressorMixin`을 `BaseEstimator`보다 **앞**에 둬야 `VotingRegressor` 검증을 통과합니다(순서 역전 시 `should be a regressor`).
`─────────────────────────────────────────────────`

후보는 gen-004 평가 파이프라인(`orchestrator.py run_all`)에 투입 준비됐습니다. cand-000/001과 함께 게이트를 돌릴까요, 아니면 delta 가중을 낮춘 변종을 하나 더 만들어 비교군을 넓힐까요?
