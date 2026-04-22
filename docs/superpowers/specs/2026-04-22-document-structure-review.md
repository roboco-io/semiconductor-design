---
title: 문서 구조 리뷰와 graphify 전환 정리 제안
status: proposed
date: 2026-04-22
related:
  - docs/superpowers/specs/2026-04-22-graphify-adoption-design.md
  - docs/superpowers/specs/2026-04-22-graphify-evaluation.md
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
---

# 문서 구조 리뷰와 graphify 전환 정리 제안

## 1. 요약

현재 문서 구조의 가장 큰 문제는 **graphify 전면 전환 결정**과
**기존 wiki/QMD/frontmatter 기반 문서**가 동시에 canonical처럼 보인다는 점이다.

`docs/superpowers/specs/2026-04-22-graphify-adoption-design.md`는 Phase 1a
`semi_design_wiki` 엔진을 graphify로 전면 대체한다고 명시한다. 반면 `README.md`,
`issues/003-wiki-ingest-automation-trigger.md`, `docs/glossary.md`,
`wiki/program/*.md`는 여전히 `wiki-init`, `wiki-sync`, `wiki-lint`, QMD,
frontmatter, promotion policy를 현재 지식기반 운영 방식처럼 설명한다.

따라서 새 에이전트나 사람이 프로젝트에 들어오면 다음 질문이 불명확하다.

- 현재 authoritative knowledge index는 `wiki/`인가, graphify graph인가?
- `wiki/program/*.md`는 아직 운영 규칙인가, S2/S4 이후 흡수·삭제 예정인 legacy인가?
- QMD는 여전히 도입 예정인가, graphify query/MCP로 대체되는가?
- Graphify 산출물은 로컬 cache인가, 팀이 공유해야 하는 generated index인가?

본 문서는 코드 변경 없이 문서 구조 개선 방향을 정리한다.

## 2. 현재 관찰

### 2.1 graphify 전환 문서는 명확하다

Graphify adoption spec은 다음을 이미 결정한 상태로 기록한다.

- Phase 1a wiki engine 전면 대체
- frontmatter invariants, `promotion_policy`, `scoring` 폐기
- `L2.lint.check()`를 graph integrity check로 재정의
- `wiki/raw/**`는 graphify seed corpus로 보존
- `wiki/program/*.md`는 S2에서 overview spec §7로 흡수 후 삭제 예정

### 2.2 README는 아직 legacy 경로를 안내한다

`README.md`는 현재 G2를 `typed-frontmatter memory + QMD + skill library`로 설명하고,
Phase 1a 명령으로 `wiki-init`, `wiki-sync`, `wiki-lint`를 안내한다. Graphify 전환
문서를 읽기 전까지는 이 경로가 현재 canonical처럼 보인다.

### 2.3 issue 003은 graphify 결정과 충돌한다

`issues/003-wiki-ingest-automation-trigger.md`는 QMD reindex와 wiki ingest 자동화를
전제로 한다. Graphify 전환 후에는 이 이슈가 다뤄야 할 주제가 바뀐다.

기존 주제:
- wiki ingest 자동화
- QMD corpus/reindex
- `wiki-lint` 기반 경고

전환 후 주제:
- graphify refresh policy
- semantic rebuild 주기
- graph integrity threshold
- graph output commit policy
- cross-trench edge 보완 정책

### 2.4 Graphify S1 평가의 M3 실패는 구조적이다

`docs/superpowers/specs/2026-04-22-graphify-evaluation.md`는 M1/M2/M4/M5를 통과했지만,
M3 inter-trench edge는 0으로 실패했다.

원인은 chunk 경계와 AST-only code extraction이다.

- narrative/contract/root_doc chunk와 spec/plan/issues chunk가 분리됨
- code trench는 AST-only라 semantic edge가 추가되지 않음
- 결과적으로 narrative, contract, code 사이의 의미 연결이 자동 생성되지 않음

이는 graphify 채택 철회 사유는 아니지만, L2 Substrate에서 graph를 쓰려면 명시적
bridge 자료가 필요하다는 신호다.

### 2.5 graphify-out 산출물 정책이 아직 모호하다

현재 전환 spec은 `graphify-out/`을 gitignore 대상으로 본다. 그러나 이 프로젝트의
목적이 "소스코드와 문서, 자료의 지식기반을 graphify로 관리"하는 것이라면
`GRAPH_REPORT.md`와 `graph.json`은 단순 임시 cache가 아니라 공유 가능한 generated
index일 수 있다.

이 결정을 명확히 하지 않으면 다음 문제가 생긴다.

- 새 작업자가 graph를 재생성해야만 최신 지식기반을 볼 수 있음
- graphify 비용/시간이 모든 작업자의 진입 비용이 됨
- Graphify query/MCP가 팀 공통 기준인지, 로컬 보조 도구인지 불명확함

## 3. 제안

### 3.1 README를 graphify 기준 entrypoint로 갱신

README의 Knowledge base와 Phase 1a 섹션을 다음 방향으로 바꾼다.

- 현재 지식 탐색의 1차 경로는 graphify라고 명시
- `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json`, `graphify query`,
  `graphify path`, `graphify explain`를 안내
- `wiki/raw/**`는 raw corpus로 보존한다고 설명
- `wiki-init/wiki-sync/wiki-lint`는 legacy Phase 1a 도구로 내리거나 제거
- G2 설명을 `graphify-backed L2 Substrate`로 수정

### 3.2 Graphify 산출물 commit policy를 결정

두 옵션 중 하나를 명시적으로 선택해야 한다.

| 옵션 | 정책 | 장점 | 단점 |
|---|---|---|---|
| A | `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json`, `graphify-out/graph.html` 커밋. `graphify-out/cache/`만 ignore | 새 작업자가 즉시 그래프를 조회 가능. graph가 팀 공통 artifact가 됨 | generated artifact diff가 커질 수 있음 |
| B | `graphify-out/` 전체 ignore | 저장소가 가벼움. 재생성 중심 | 지식기반이 로컬 상태에 의존. 팀 공통 기준 약함 |

본 프로젝트 목적에는 **옵션 A**가 더 맞다. 다만 `graph.html`이 너무 자주 흔들리면
`GRAPH_REPORT.md`와 `graph.json`만 커밋하고 HTML은 로컬 생성으로 둘 수 있다.

### 3.3 Cross-trench bridge manifest 추가

Graphify S1의 M3 실패를 완화하려면 graphify가 자동으로 잡지 못한 관계를
명시적으로 먹일 얇은 bridge 문서가 필요하다.

추천 파일:

- `docs/graphify/cross-links.md`
- 또는 `docs/knowledge-map.md`

예시 항목:

| 관계 | 설명 |
|---|---|
| `K1 beta ORFS-agent -> L1 runner metrics parser` | ORFS-agent의 report-grounded loop가 L1 metric collection과 연결됨 |
| `H1b Non-knob structural patch -> issues/001 -> future L3 planner` | H1b metric이 L3 planner mutation operator 설계와 연결됨 |
| `K1 delta Voyager -> skill library -> reversible patch policy` | Voyager precedent가 reversible-patch skill library 설계 근거임 |
| `Graphify M3 failure -> cross-link manifest -> L2.memory.recall` | 자동 graph extraction의 경계 문제를 manifest로 보완함 |

이 문서는 사람이 읽기에도 좋고, graphify semantic extraction에도 직접적인 입력이 된다.

### 3.4 issue 003을 supersede 처리하고 새 이슈로 분리

`issues/003-wiki-ingest-automation-trigger.md`는 다음 중 하나로 처리한다.

1. `status: resolved (superseded by graphify adoption)`으로 닫고 Resolution 추가
2. 제목과 본문을 `Graphify refresh policy + graph integrity thresholds`로 재작성

권장 방식은 1번이다. 기존 history를 보존하고, 새 이슈를 별도로 만드는 편이 추적성이 좋다.

새 이슈 후보:

- `005-graphify-refresh-and-integrity-policy.md`

결정 항목:

- full graph rebuild 주기
- `graphify update` 실행 시점
- semantic extraction이 필요한 변경 범위
- AMBIGUOUS threshold
- orphan/dangling edge threshold
- graph output commit 여부
- cross-link manifest 필수 여부

### 3.5 문서 계층을 raw / canonical / derived / historical로 분리

현재 `docs/superpowers/plans`, `docs/superpowers/specs`, `wiki/raw`, `wiki/program`,
`docs/knowledge-base`, `issues`가 비슷한 무게로 보인다. Graphify가 전체 repo를
먹는 구조에서는 문서의 권위 수준이 파일 경로와 frontmatter에 더 명확히 드러나야 한다.

권장 분류:

| 계층 | 목적 | 예시 |
|---|---|---|
| raw | 원문 corpus. 사람이 직접 정제하지 않은 입력 | `wiki/raw/papers/`, `wiki/raw/sessions/` |
| canonical | 현재 의사결정과 운영 기준 | overview spec v2, L1 spec, graphify adoption spec |
| reports | 특정 시점 평가·조사 결과 | K1 direction report, graphify S1 evaluation |
| plans/active | 실행 중 계획 | 현재 phase plan |
| plans/archive | 완료되었거나 superseded된 계획 | Phase 1a wiki skill engine plan |
| drafts | 아직 승인되지 않은 작업 초안 | `docs/superpowers/plans/drafts/` |
| derived | graphify 생성물 | `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json` |
| issues | 열려 있는 결정·작업 추적 | active issues only |

이 분류를 README 또는 `docs/README.md`에 명시하면 graphify 결과를 읽는 사람도
노드의 권위 수준을 해석하기 쉬워진다.

### 3.6 glossary를 graphify 전환 후 기준으로 업데이트

`docs/glossary.md`는 최근 추가된 좋은 entrypoint지만, 현재는 legacy wiki 용어를
현재형으로 설명한다.

추가할 용어:

- Graphify
- `GRAPH_REPORT.md`
- `graph.json`
- `graph.html`
- EXTRACTED / INFERRED / AMBIGUOUS
- graph integrity check
- orphan node
- dangling edge
- god node
- Leiden community
- cross-trench edge
- bridge manifest

내릴 용어:

- `wiki-init`
- `wiki-sync`
- `wiki-lint`
- QMD
- typed frontmatter

이들은 삭제하지 말고 `Legacy Phase 1a` 또는 `Superseded` 섹션으로 이동하는 편이 좋다.

## 4. 권장 실행 순서

### P0 — 혼선 제거

1. README에서 Graphify를 현재 knowledge entrypoint로 명시
2. issue 003을 supersede 처리
3. glossary에 Graphify 핵심 용어 추가

### P1 — Graphify 운영 기준 확정

1. graphify output commit policy 결정
2. `.gitignore` 조정
3. `make graph-update`, `make graph-build`, `make graph-serve`, `make graph-lint`
   명령 체계 정리
4. `scripts/graph_integrity_check.py` 구현 여부를 S3 계획과 맞춤

### P2 — Graph 품질 개선

1. `docs/graphify/cross-links.md` 추가
2. Graphify rebuild
3. M3 inter-trench edge 개선 여부 재측정
4. `docs/superpowers/specs/2026-04-22-graphify-evaluation.md`에 S1.1 재평가 섹션 추가

### P3 — 문서 계층 정리

1. `docs/README.md` 또는 `docs/documentation-map.md` 추가
2. canonical / reports / active plans / archive / drafts / raw / derived 정의
3. 긴 plan 문서에 status와 superseded-by 표시
4. historical plan은 graphify에서 낮은 우선순위로 해석되도록 frontmatter 보강

## 5. 문서 구조 목표 상태

권장 목표 구조:

```text
docs/
├── README.md                         # 문서 계층과 읽는 순서
├── glossary.md
├── graphify/
│   └── cross-links.md                # graphify cross-trench 보정 manifest
├── knowledge-base/
│   └── 2026-04-19-k1-direction-report.md
├── reports/
│   └── 2026-04-22-graphify-evaluation.md
├── superpowers/
│   ├── specs/
│   │   ├── 2026-04-19-integrated-research-program-design.md
│   │   ├── 2026-04-20-L1-process-design.md
│   │   └── 2026-04-22-graphify-adoption-design.md
│   └── plans/
│       ├── active/
│       ├── archive/
│       └── drafts/
wiki/
└── raw/
    ├── papers/
    └── sessions/
graphify-out/
├── GRAPH_REPORT.md
├── graph.json
└── graph.html
issues/
├── README.md
└── 005-graphify-refresh-and-integrity-policy.md
```

이 구조의 핵심은 `wiki/raw/**`를 raw corpus로 유지하되, 운영 지식의 canonical
entrypoint는 graphify와 specs로 옮기는 것이다.

## 6. 남은 결정사항

1. `graphify-out/graph.json`을 커밋할 것인가?
2. `graphify-out/graph.html`도 커밋할 것인가, 로컬 생성물로 둘 것인가?
3. Graphify refresh를 언제 강제할 것인가?
   - 문서 변경마다
   - canonical docs 변경마다
   - release/gate 전
4. `docs/superpowers/specs/2026-04-22-graphify-evaluation.md`를 `docs/reports/`로 이동할 것인가?
5. `wiki/program/*.md`를 언제 overview spec §7로 흡수하고 삭제할 것인가?
6. `docs/eda_agent_handoff.md`는 archive로 이동할 것인가, 현 위치에 superseded note만 남길 것인가?

## 7. 결론

Graphify 채택 자체는 S1 평가 기준으로 타당하다. 다만 문서 구조가 아직 전환 중간 상태라
legacy wiki/QMD 계약과 graphify 계약이 동시에 살아 있다. 가장 먼저 해야 할 일은
코드 삭제가 아니라 **문서의 권위 체계 정리**다.

권장 첫 패치는 작게 간다.

1. README에 Graphify entrypoint 명시
2. issue 003 supersede
3. glossary Graphify 용어 추가
4. `docs/graphify/cross-links.md` 초안 추가

이 네 가지가 끝나면 S2/S3의 코드 전환이 훨씬 덜 위험해진다.
