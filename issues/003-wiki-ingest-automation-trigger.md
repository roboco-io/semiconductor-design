---
id: 003
title: Wiki ingest 자동화 전환 기준
status: open
type: design-decision
related_spec: docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md#8.5
iteration: 1→2
blocks: []
---

# 003. Wiki ingest 자동화 전환 기준

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
