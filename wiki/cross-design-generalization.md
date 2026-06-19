---
title: Cross-Design Generalization
aliases: [cross-design-generalization, LODO, distribution shift]
type: concept
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[gate-chain]], [[generation-log]]
---

# Cross-Design Generalization — 교차설계 일반화와 분포 shift

> surrogate가 *학습에서 안 본 설계*에 전이되는가. 본 프로젝트의 핵심 난제이자 LODO 게이트의 근거.

## 배경
교차설계 첫 실측(2026-06-10)에서 **분포 shift가 모든 학습 모델을 무력화**함을 발견. 설계별 timing
slack 분포가 거의 비중첩: gcd [−1.37,0], aes [+0.44,+2.93], ibex [+1.49,+8.23].

## 핵심 내용 (probe 실측 — 사실, 지시 아님)
- **델타 label**(`post_route_slack − synth_slack` 잔차 학습)은 드리프트 안정 설계(aes)서 naive 37% 격파,
  자릿수 드리프트(ibex)선 약함.
- **혼합 분포 훈련**이 절대 스케일 모델의 미관측 설계 전이를 회복(ibex held-out서 naive 4.3× 격파).
  gen-004 자율 세대에서도 재현됨([[generation-log]]).
- held-out 설계별 최선 전략이 갈림 — **단일 정답 축 없음**.
- 정규화 축: V1(델타 label) · V2(per-design 통계 표준화) · V3(무차원 비율) · V4(V1×V3).

## LODO 게이트 (Leave-One-Design-Out)
- 설계마다 한 설계를 held-out으로 빼고 winner/baseline/naive 비교 → 방향성 verdict
  (`generalizes_better`/`worse`/`mixed`/`unverifiable`).
- **저표본 한계**: 설계 3개 → 통계 검정 불가, 경향 probe일 뿐. 설계 확보(Sub-A) 시 유의성 격상.

## 주의사항 / 오해
- 다설계 dataset의 `val_mae`는 설계 교체 때문에 **단일설계 세대(gen-001~003)와 직접 비교 금지**.

## 참고
- `experiments/multidesign/probe/probe.md`, `probe-3design.md`.
