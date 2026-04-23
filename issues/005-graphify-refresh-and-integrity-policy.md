---
id: 005
title: graphify refresh + integrity policy + cross-links 정제 cadence
status: resolved
type: policy
related_spec: docs/superpowers/specs/2026-04-22-graphify-adoption-design.md
layer: L2
iteration: G0-continuous
blocks: []
---

# Issue 005 — graphify refresh + integrity policy

## 배경

graphify 전환 프로젝트(S1–S4, 2026-04-22) + Path B cross-links manifest 완료로 `L2.lint.check() PASS` 최초 달성 (commit `ec9593c`, orphan 0 / dangling 0 / AMBIGUOUS 0%). 그러나 다음 운영 규칙이 공식화되지 않아 drift 재발 위험:

1. Graph rebuild cadence — full rebuild vs incremental update 판단 기준
2. Cross-links.md lifecycle — AST/Part B가 후에 자연 발견하면 manifest 항목 제거 (중복 방지)
3. Option A+ commit policy 적용 범위 — `graphify-out/memory/` 커밋 여부 명시
4. Graph integrity FAIL 발생 시 대응 SOP — orphan > 0 / AMBIGUOUS > 0.3 / dangling > 0

본 policy는 issue 003 Resolution 섹션에서 예고됨.

## 1. Graph rebuild cadence

### 1.1 Full rebuild triggers (`/graphify .` — AI 세션 수동 실행, LLM 비용 발생)

다음 4개 조건 중 **하나라도** 충족 시 full rebuild 수행:

- **(a) 대량 신규 source**: `wiki/raw/**`에 **5+ 파일** 추가된 커밋 (signed diff 기준)
- **(b) L2 contract 변경**: overview spec §3.2 L2 contract table 수정 (breaking 또는 additive 모두 포함). 신규 derived spec 작성도 포함.
- **(c) 신규 Codex review round**: overview·derived spec에 Codex 3-round review가 추가되는 커밋. Review 문서 자체도 ingest 대상이므로 full rebuild로 god-node 재평가 필요.
- **(d) 정기 cadence**: **월 1회 정기**. 지난 full rebuild 기준 30일 경과 시점에 별도 트리거 없이 1회 수행. `graphify-out/manifest.json`의 `build_timestamp` 기준.

### 1.2 Incremental update triggers (`make graph-update` — AST-only, LLM 비용 0)

다음은 incremental 범위로 충분:

- 일반 코드 편집 (단일 파일 수정 · 테스트 추가)
- 단일 doc 수정 (rpt template 조정 · CLAUDE.md patch)
- spec `.md` 파일 metadata-only 수정 (Reviews 표 row 추가 등)

Post-commit hook 자동화는 **옵션**. 비용 0이라 PR 머지 후 CI에서 돌려도 무방.

### 1.3 rebuild 방식 매핑

| Trigger 조건 | 명령 | LLM 비용 | 실행 주체 |
|---|---|---|---|
| 1.1 (a)–(d) | `/graphify .` | 발생 (세션당 ~$0.5–$3) | AI 세션 수동 |
| 1.2 | `make graph-update` | 0 | dev 로컬 또는 CI |

## 2. Cross-links.md lifecycle

`docs/graphify/cross-links.md`는 AST+Part B pipeline이 놓치는 cross-trench edges를 **명시적 자연어 문장**으로 유지하는 bridge manifest다. 본 policy가 정의하는 lifecycle:

### 2.1 매 full rebuild 후 재검증

```
make graph-lint          # orphan=0 / dangling=0 / AMBIGUOUS≤0.3 확인
```

fail 시: cross-links.md에 누락된 bridge 선제 추가 → 해당 `.md` 자체가 corpus에 포함돼 있으므로 다음 full rebuild에서 EXTRACTED edge로 추출됨. §3 FAIL 대응 SOP 참조.

### 2.2 Natural-discovery pruning (AST/Part B 발견분 제거)

graphify가 후속 rebuild에서 manifest 문장의 edge를 **자연 발견**(AST에 포함되거나 Part B가 독립 추출)한 경우, manifest에서 해당 bullet을 **제거**한다. 중복 유지 시:

- 그래프에 동일 edge가 2배로 태깅되어 centrality score 왜곡
- bridge manifest가 불필요 팽창 → 유지보수 비용 증가

판단 기준: 매 full rebuild 후 `graphify-out/graph.json`에서 해당 edge의 `source` 속성(AST vs manifest)을 확인. AST가 발견했으면 manifest pulled.

### 2.3 PR-level diff 점검

새 파일(특히 `__init__.py` · `conftest.py` · 신규 K3 paper · 신규 CDK test)을 추가하는 PR에서 cross-links.md **선제 추가** 없이 머지되면, 다음 full rebuild에서 orphan 재발생 가능.

PR 체크리스트 (`CLAUDE.md`·PR template에 링크):
- [ ] 신규 파일이 AST-invisible 종류(empty symbol · cross-stack test · paper `.md`)인가?
- [ ] Yes → cross-links.md에 bridge 문장 추가 (section 1-6 중 적절한 곳)
- [ ] No → PR 머지 후 다음 rebuild 시 자연 수렴

### 2.4 Cadence 요약

| 시점 | 작업 |
|---|---|
| full rebuild 직후 | 2.1 재검증 + 2.2 natural-discovery pruning |
| PR 제출 시 | 2.3 선제 추가 체크리스트 |
| 월 1회 (1.1 (d) 정기 rebuild와 함께) | manifest 전체 re-audit (6 섹션 각 bridge 유효성 sample 점검) |

## 3. Option A+ commit policy — 적용 범위

`.gitignore` 최신 상태 기준 확정 범위:

### 3.1 커밋 대상 (`git add` 허용)

| 파일 | 용도 | 커밋 이유 |
|---|---|---|
| `graphify-out/graph.json` | knowledge graph raw | 팀 공유 단일 진실, L2.lint.check 입력 |
| `graphify-out/GRAPH_REPORT.md` | markdown summary | PR review · issue 참조용 |
| `graphify-out/graph.html` | interactive viz | 탐색/리뷰용, 크기 수 MB |
| `graphify-out/cost.json` | LLM 비용 기록 | rebuild audit, overview §12 비용 추적 |
| `graphify-out/manifest.json` | build metadata | rebuild timestamp · corpus hash |
| `graphify-out/memory/` | query 결과 markdown | **다음 rebuild 시 재인제스트 가치** — query·path·explain 출력이 다음 corpus의 일부 |

### 3.2 Gitignore 대상 (`.gitignore` 등재)

| 파일 | 이유 |
|---|---|
| `graphify-out/cache/` | LLM response cache, 재현 불필요 |
| `graphify-out/.graphify_*` | runtime scratch |
| `.graphify-cache/` | root-level cache |
| `tmp/graphify-eval/` | evaluation scratch |
| `build/graph/` | build artifact |

### 3.3 `graphify-out/memory/` 커밋 근거 (본 policy 결정)

- 매 `graphify query "..."` 또는 `graphify path` 호출이 해당 디렉토리에 markdown 결과를 저장한다.
- 그 결과가 다음 `/graphify --update` 시 **corpus의 일부로 재인제스트**되어 graph에 `INFERRED` 노드 추가 가능성.
- 즉 query 결과가 **지식 응축 → 재사용** 파이프라인의 첫 stage로 기능 → 팀 공유 가치 있음 → 커밋.
- 크기 관리: `graphify-out/memory/**/*.md` 파일당 수 KB, 월별 정리 권장(본 policy §1.1 (d) 정기 rebuild와 함께).

## 4. Graph integrity FAIL 대응 SOP

`make graph-lint` FAIL 시 failure 유형별 대응:

### 4.1 Orphan > 0

```
$ make graph-lint
FAIL: 3 orphan nodes: cdk/test/NewStack.test.ts, wiki/raw/papers/k3-xxx.md, ...
```

단계:
1. orphan 노드 리스트 확인 (`scripts/graph_integrity_check.py` 상세 출력)
2. 각 노드의 **AST-invisible 원인** 진단:
   - CDK test → `cdk_test_*` / `cdk_lib_stacks_*` 간 bridge 필요
   - `__init__.py` / `conftest.py` → empty symbol, `packages` 관계로 bridge 필요
   - K1/K2/K3 paper `.md` → §5.1 spec 섹션 또는 §9 K2 축 memo와의 `grounds` 관계 bridge 필요
3. `docs/graphify/cross-links.md` section 1-6에 bridge 문장 추가 (자연어 문장이 Part B subagent 처리 대상)
4. full rebuild 또는 `make graph-update` (AST가 cross-links.md 자체를 corpus에 포함)
5. `make graph-lint` 재검증. orphan 0 복귀 확인.

### 4.2 AMBIGUOUS ratio > 0.3

overview §7.3 AMBIGUOUS triage workflow **full 적용**:

1. `graphify-out/GRAPH_REPORT.md`의 AMBIGUOUS 비율 + god-node top-N 변화율 확인
2. AMBIGUOUS 노드 리스트 추출 (`graph.json`에서 `tier == "AMBIGUOUS"` 필터)
3. Path A (자동화): 후보 edge와 evidence gap surface — 실제 tier 변경·승격·폐기는 human triage
4. Path B (manifest): cross-links.md에 AMBIGUOUS 노드 의미를 **명시 문장**으로 해소
5. Path A/B 적용 후 `make graph-lint` 반복, AMBIGUOUS ≤ 0.3 전까지 §7.3 promotion + 신규 L3 entry 차단 (진행 중 preregistered run은 예외, overview §7.3 step 6)

### 4.3 Dangling edges > 0

`graph.json` 손상 또는 incremental update의 partial failure 가능성:

1. `graphify-out/cache/` 삭제 (corrupted cache 의심)
2. `/graphify .` full rebuild 재수행 (incremental 아님)
3. 재실행 후에도 dangling 재발 시 → graphify upstream bug 가능성, `uv run graphify --version` 확인 + `.claude/skills/graphify/SKILL.md` 점검 후 이슈 제기

### 4.4 FAIL 상태의 블로킹 효과

overview §7.3 정의 준수:

- `L2.lint.check()` FAIL 은 **R0 조건이 아니다** (overview §5.3 · §7.3). publish/kill 판정 차단 안 함.
- AMBIGUOUS > 0.3 상태에서는 §7.3 promotion + 신규 L3 entry(신규 실험 착수·신규 candidate 세대·promotion PR 제출) 차단. 진행 중 preregistered run은 **예외**.
- orphan / dangling 단독 fail은 block 대상 아니고 lint-level signal로만 작동. CI 경고만 발생.

## 5. 액션 아이템 (이 policy 채택 후)

- [x] 본 policy 문서 작성 (`issues/005-graphify-refresh-and-integrity-policy.md`)
- [x] `issues/README.md` 인덱스에 005 등재
- [ ] `CLAUDE.md` PR 체크리스트 섹션에 §2.3 링크 추가 (후속 커밋 — 본 policy 적용 시점에 개별 PR로)
- [ ] 다음 월 1회 rebuild trigger: **2026-05-23** (본 policy 생성일 +30일)
- [ ] 본 policy의 cadence 규칙을 1개월 운영 후 실효성 재평가 (2026-06 즈음)

## Resolution

- **resolved**: 2026-04-23, commit (본 policy 최초 작성 커밋)
- **적용 범위**: graphify-out 전체 + cross-links.md lifecycle + `make graph-*` 명령
- **감시 지표**: 다음 1개월간 (a) orphan 재발생 횟수 · (b) manifest에서 자연 pruning된 bridge 개수 · (c) FAIL → recover 시간. 재평가 기준 데이터.
