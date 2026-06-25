---
id: 007
title: gen-009 다음 실험 지렛대 선택
status: open
type: decision
blocks: ["gen-009 실행", "negative-result 논문 contribution claim"]
related_prd: "§9 가설 지지 조건, 4-step 루프"
related_intent: "Why H-A(교차설계 미달), Learnings 2026-06-21d·2026-06-24, Not(개방 탐색·prepare.py frozen)"
depends_on: [005]
---

# 007 — gen-009 다음 실험 지렛대 선택

> **맥락 (2026-06-24 프레이밍)**: gen-002~008 7세대 연속 reject. "성공"은 H-A positive가 아니라
> *프로세스 novelty + co-evolution + 정직한 negative result*로 재정의됨(INTENT Learnings 2026-06-24).
> 이 문서는 *그럼에도 다음 실험을 한다면 어느 지렛대인가*를 결정하기 위한 brief다. 핵심 제약:
> 어떤 선택이든 **어느 프레이밍에서도 산출물이 되어야** 한다 — 성공하면 positive 반전, 실패하면
> negative result를 더 단단히.

## 배경 — 종합된 발견

**벽(5세대 견고)**: in-loop `val_mae`는 계속 최저 경신(gen-007 1.29 → gen-008 0.53)인데,
교차설계 T1은 gen-004~008 내내 `indistinguishable`. **in-distribution 최적화 ≠ 교차설계 일반화**.

**진단된 근본 원인** (INTENT Learnings):

| 원인 | 출처 | 상태 |
|---|---|---|
| feature가 절대 ns 스케일 → 분포 밖 설계는 순수 외삽 | 2026-06-10 | 미해결 |
| 델타/잔차 label이 전이의 지배 축 (단 드리프트 자릿수 다르면 약함) | 06-11·06-11b | **루프 미편입** |
| 혼합/다양 분포 훈련이 절대 모델 전이 회복 | 06-11b | 부분 적용(4설계) |
| jpeg 61% 지배 → 가까운 분포 전이만 개선 | gen-008 | **미해결·미시도** |

**지렛대 소진 맵** (grep 검증, 2026-06-24):

| 지렛대 | 시도? | 결과 / 근거 |
|---|---|---|
| 생성 힌트(델타·설계-불변 유도) | ✅ gen-006 | `program.md` L49·L57이 이미 힌트. LODO는 넘겼으나 T1 못 넘김 |
| 재추첨·데이터 추가 | ✅ gen-004~008 | 벽 견고 (Learnings 2026-06-21d "이걸론 못 넘음") |
| 델타/정규화가 챔피언 train.py에 편입 | ❌ | grep 결과 **0건** — 가장 유망했던 V1 신호가 루프 baseline에 없음 |
| **설계 균형(jpeg 비중 완화)** | ❌ **미시도** | gen-008 진단의 직접 대응책인데 한 번도 안 당김 |

> **핵심 통찰**: `program.md`는 델타를 *제안*했으나 에이전트는 채택 안 함(챔피언 train.py 델타 0건).
> AutoResearch 개방 탐색 철학상 program.md는 "전적으로 너의 선택"이라 열어뒀고, 그 자유가
> 가장 유망한 신호를 루프가 스스로 버리게 한 구조일 수 있다. 다음 분기의 진짜 축은 "어떤
> 데이터냐"가 아니라 **"에이전트의 자유를 어디까지 제약하나"** — INTENT Not(개방 탐색)과 맞닿음.

## 옵션

### A. 설계 균형 dataset (jpeg 비중 완화) — *추천*

- **방법**: jpeg(4410) 비중을 다른 설계 수준으로 다운샘플(또는 설계별 동수 샘플링)한 균형 dataset
  변형(`dataset-4design-balanced.jsonl`)을 생성 → 새 baseline 측정(re-baseline) → gen-009 실행.
  `prepare.py`는 건드리지 않음 — dataset 조합은 Operator config 선택(4설계 선택과 동일 층위).
- **INTENT 정합**: ✅ prepare.py frozen 유지, train.py 단일 파일 계약 유지, 게이트 불변. Not 위반 없음.
- **비용/속도**: 낮음. 기존 4설계 데이터 재조합만, AWS 재실행 불필요. 빠름.
- **기대 산출 (양 프레이밍)**: 성공 시 → "jpeg 편향이 벽의 원인"이라는 positive 반전.
  실패 시 → "균형까지 줬는데도 벽 견고" → negative result를 *반박 불가능*하게.
- **리스크**: 다운샘플로 유효 학습 데이터↓(7194→~수천행) → 학습 신호 약화. baseline 재설정 필요
  (균형 dataset의 baseline은 기존 4설계 baseline과 다른 분포라 직접 비교 주의).

### B. 델타/정규화를 구조적 기본값으로 강제

- **방법**: V1 델타(`post_route_slack − synth_slack` 잔차 학습) + 설계별 정규화를 train.py baseline에
  명시 주입하고 *거기서* 진화시키거나, `program.md`를 "선택 → 필수 구조"로 격상.
- **INTENT 정합**: ⚠️ **Not(개방 탐색·"전적으로 너의 선택") 인접**. 에이전트 자율성을 구조적으로
  제약 → AutoResearch 철학과 긴장. **spec-level 결정 필요** (가볍게 진행 불가).
- **비용/속도**: 중. train.py baseline 변경 또는 program.md 격상 + 게이트 재검토.
- **기대 산출**: lever 1을 끝까지 — "델타가 *강제*되면 T1이 깨지나?"에 답. gen-006은 델타를
  *제안*만 했으니 이건 미답 질문.
- **리스크**: 자율성 제약이 본 프로젝트 novelty 축(비전문가가 *방향만*)과 충돌할 수 있음.
  "강제했더니 됐다"는 H-A를 살리지만 "에이전트 자율"이라는 전제를 약화.

### C. 확정 실험 (negative result 못박기)

- **방법**: 추가 지렛대 없이 gen-009를 동일 조건 실행.
- **INTENT 정합**: ✅ 완전 정합. negative-result 프레이밍에 가장 부합.
- **비용/속도**: 가장 낮음·가장 빠름.
- **기대 산출**: 벽이 6세대째 안정임을 보여 논문 robustness↑. "재현성" 주장 강화.
- **리스크**: 새 발견 가능성 낮음 — 이미 5세대 같은 결과. 한계효용 체감.

### D. 5번째 설계 확보

- **방법**: 새 설계 ORFS flow(AWS Fargate) 실행 → 5설계 dataset → LODO/T1 fold 4→5로 통계력↑.
- **INTENT 정합**: ✅ 정합. 단 Learnings 2026-06-21d가 "데이터 추가만으론 벽 못 넘음" 명시.
- **비용/속도**: 높음 — **AWS 실과금**(D4 비용 게이트·Operator 동의 필요), 느림(설계당 ~50분 flow).
- **기대 산출**: T1 통계력↑로 "indistinguishable"이 더 단단해지거나, 새 설계가 분포를 바꿔 미세 변화.
- **리스크**: 비용 대비 새 발견 기대 낮음. Learnings가 이미 약효 한계 경고.

## 결정 기준

1. **어느 프레이밍에서도 산출물이 되는가** — 성공/실패 모두 논문에 기여하는 선택 우선(A가 최적).
2. **INTENT Not 정합** — B는 개방 탐색 제약이라 spec-level 판단 선행. A·C·D는 즉시 진행 가능.
3. **비용 대비 정보량** — 싼 실험이 비싼 결정을 정보화(06-10·06-11 "싼 probe" 패턴). A·C 우위, D 열위.
4. **미시도 지렛대 우선** — A(설계 균형)·B(델타 강제)가 미시도. C·D는 변형 없는 반복.

## 액션 아이템

- [ ] 지렛대 선택 (A/B/C/D) — Operator 결정.
- [ ] (A 선택 시) 균형 dataset 생성 방식 확정: 다운샘플 vs 설계별 동수 vs 가중 — sub-decision.
- [ ] (A 선택 시) re-baseline 측정 + 비교 프레임 정의(균형 dataset baseline은 별도).
- [ ] (B 선택 시) spec 작성 → Codex 검토 게이트 (자율성 제약은 spec-level 권한).
- [ ] 선택된 실험을 plan으로 전개 (writing-plans / 해당 spec).
- [ ] 정량 임계값은 **재정의 금지** — 설계 spec 인용만 (INTENT-vs-spec invariant).

> 본 issue는 임계값을 재정의하지 않는다. 게이트(median + LODO + 교차설계 T1 + Codex) 정의·임계값은
> 설계 spec 소유다 (issues/005 권한 주의 동일).
