---
id: 003
title: Wiki ingest 자동화 + QMD reindex 전략 (L2 substrate)
status: resolved (superseded by graphify adoption, 2026-04-22)
type: design-decision
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md#3.2
superseded_by: docs/superpowers/specs/2026-04-22-graphify-adoption-design.md
layer: L2
iteration: G2
blocks: [L2 파생 spec]
---

# 003. Wiki ingest 자동화 + QMD reindex 전략 (L2 substrate)

## Resolution (2026-04-22)

본 이슈는 **graphify 도입 결정 (2026-04-22)** 으로 supersede. 사유:

- 아래 옵션 A/B/C/D는 모두 **Phase 1a wiki 엔진**(`wiki-init`·`wiki-sync`·`wiki-lint` + `lint_wiki.py`)을 전제로 함
- graphify 전환으로 해당 엔진 자체가 폐기 대상(`docs/superpowers/specs/2026-04-22-graphify-adoption-design.md`)
- QMD 검색 계층 또한 graphify MCP(`graphify query` + `graph.json`)로 대체 — overview spec §3.2 L2 인터페이스 v2 참조

새 주제(graphify refresh policy, graph integrity threshold, output commit policy 등)는 별도 이슈 [`005-graphify-refresh-and-integrity-policy.md`](005-graphify-refresh-and-integrity-policy.md) (TBD)로 분리 예정.

역사적 맥락은 아래 본문 유지.

---

## 재배치 노트 (2026-04-19)

QMD 검색층 도입이 MVP 범위로 확정(overview spec §6 Knowledge plane)되면서 이 이슈는 **L2 파생 spec 범위**로 재배치. 단순 "언제 자동 ingest로 전환하는가"에서 확장 — "QMD 인덱스 갱신 + findings/failures 생성 + skill library 등록 자동화 수준" 전체가 이 이슈의 대상.

- **M1 (G1 완료 시)**: QMD corpus 수동 빌드, ingest 수동
- **M2 (G2 구현 중)**: `L2.lint.check()`의 duplicate-finding rule 자동 alert, ingest는 수동
- **M3 (G2 완료 시)**: 새 finding 생성 시 QMD reindex 자동 + skill library 업데이트 자동

Interfaces는 overview spec §3.2 contract table 참조: `L2.memory.recall()`, `L2.skill_library.query()`, `L2.lint.check()`.

아래 원 옵션 A/B/C/D는 L2 파생 spec에서 재검토. History 유지.

---

## 배경

이터레이션 1에서 `wiki ingest`는 수동 트리거다(Scope 제한). 이터레이션 2부터
자동화 전환이 예정되어 있으나, 트리거 조건이 미정.

## 옵션

| ID | 트리거 | 장점 | 단점 |
|---|---|---|---|
| A | wiki 페이지 수 임계치(예: 50+) 초과 시 자동 전환 | 단순 | 페이지 수가 품질 proxy가 아님 |
| B | `lint_wiki.py` 경고 수가 세대별 5건 초과 시 자동 ingest | 품질 주도 | lint 정밀도에 의존 |
| C | 각 세대 종료 후 무조건 ingest | 복리 효과 최대 | Claude Code SDK 비용 증가 |
| D | 이터레이션 2에서 재평가 (현재는 수동 유지) | 현상 유지 | 자동화 지연 |

## 결정 기준

- 이터레이션 1 종료 시 wiki 페이지 수·lint 경고 실측 수치로 옵션 판단
- 세대당 Claude Code SDK 토큰 비용 < 이터레이션 1 총비용의 10% 유지

## 액션 아이템

- [ ] 이터레이션 1 W6-7에 실측 후 이슈 재검토
- [ ] 옵션 D가 기본값, B/C는 수치에 따라 승격
