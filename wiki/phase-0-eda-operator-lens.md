---
title: "Phase 0 — EDA Operator Lens"
type: policy
tags: [phase-0, learning, lens, curriculum]
status: active
confidence: high
created: 2026-05-09
updated: 2026-05-09
sources: [docs/learning/phase-0-curriculum.md, raw/sessions/phase-0-a1-cmos.md, raw/sessions/phase-0-a2-logic-gates.md, raw/sessions/phase-0-a3-clock-timing.md, raw/sessions/phase-0-a4-combinational-sequential.md]
---

# Phase 0 — EDA Operator Lens

## 정책 (운영자 렌즈)

본 학습 트랙의 목적은 **칩 설계자(designer)** 가 되는 것이 아니라 **에이전트를 supervise/debug 할 수 있는 EDA 운영자(operator)** 가 되는 것이다.

| 우선 | 영역 | 이유 |
|------|------|------|
| ↑↑ | LLM 생성 RTL을 비판적으로 읽기 | 에이전트가 만든 회로의 결함을 잡아낼 수 있어야 함 |
| ↑↑ | `*.rpt` 해석 (synth area / STA slack / DRC violation) | 결과 판정의 기본 단위 |
| ↑↑ | 파일 포맷 (`.v / .lib / .lef / .def / .sdc`) | 에이전트가 다루는 substrate의 식별 |
| ↓ | 이론 깊이 (예: 양자 효과·noise margin) | 리포트 해석을 막지 않는 한 skip |

이 우선순위 결정은 [feedback memory](../../../.claude/projects/-Users-dohyunjung-Workspace-roboco-io-research-semiconductor-design/memory/feedback_learning_lens.md) 와 [phase-0-curriculum.md](../../docs/learning/phase-0-curriculum.md) 에서 합의됨.

## A 브랜치 (트랜지스터→FSM) 진입점

추상화 계단을 따라 1회 통과 완료:

1. [[cmos-fundamentals]] — 트랜지스터·CMOS·sky130·전력 3성분
2. [[digital-logic-gates]] — NAND universal·D-FF·조합 vs 순차
3. [[clock-and-timing]] — setup/hold·critical path·skew/jitter
4. [[fsm-and-pipeline]] — FSM·Moore vs Mealy·파이프라인·systolic array

각 페이지 하단 "프로젝트 적용 지점" 표가 Phase B/C/D로 가는 다리.

## 다음 학습 우선순위 (curriculum 기준)

| 브랜치 | 코드 | 우선 | 비고 |
|--------|------|------|------|
| C — EDA Flow | C1~C4 | **상승** | 운영자 렌즈에서 핵심 (`.rpt` 해석 직결) |
| F — PDK 포맷 | F1~F3 | **상승** | `.lib/.lef/.def/.sdc` 식별 |
| B — RTL 언어 | B1~B3 | 표준 | Verilog·Chisel 읽기 |
| D — 가속기 구조 | D1~D2 | 표준 | Gemmini systolic |
| E — 시스템 | E1~E2 | 압축 | 운영자 렌즈에서 weight↓ |

상세는 `docs/learning/phase-0-curriculum.md` 참조.

## 운영 규칙

- **Q&A 형식**: assistant 5–10줄 설명 → user 확인/질문 → 세션 파일에 즉시 기록 → "다음" 신호 후 완료 마킹.
- **새 세션 저장 위치**: `wiki/raw/sessions/phase-0-{branch}{n}-{slug}.md`. ingest 시 본 페이지 + 해당 concept 페이지로 컴파일.
- **graphify 동기화**: ingest 후 `make graph-update` 한 번 (보조 path-query를 위해 wiki 페이지를 그래프에도 반영).

## 교차 참조

- [[cmos-fundamentals]], [[digital-logic-gates]], [[clock-and-timing]], [[fsm-and-pipeline]]
- [[tutorial-project-intro]] — 외부 개발자 진입로 정책. 본 페이지(Operator 관점)와 직교 — 본 페이지는 *내부 학습 자*(Operator)용, tutorial-project-intro는 *외부 공유*용.

## Source

- `docs/learning/phase-0-curriculum.md` (curriculum + branch 정의)
- `raw/sessions/phase-0-a{1..4}-*.md` (Branch A 4개 reviewed sessions)
- 사용자 합의: 2026-04-19 EDA 운영자 렌즈 retarget
