# graphify Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 1a `src/semi_design_wiki/` 기반 LLM Wiki 엔진을 graphify v0.4.25로 전면 대체한다. frontmatter·promotion_policy 계약을 폐기하고 `L2.lint.check()`를 graph integrity check(orphan=0, dangling=0, AMBIGUOUS 비율 ≤ 0.3)로 재정의한다.

**Architecture:** 4-stage Strangler swap — (S1) graphify 실측 평가 → (S2) overview spec §3.2/§5/§7 v2 재작성 + Codex 3-round → (S3) 구 코드·CLI 제거 + graph integrity check 신규 구현 → (S4) CLAUDE.md·스킬·wiki 레거시 정리. 각 단계에 롤백 게이트.

**Tech Stack:** Python 3.12, `uv`, graphify (NetworkX + tree-sitter + Leiden + Claude 서브에이전트), pytest, ruff.

**Reference spec:** `docs/superpowers/specs/2026-04-22-graphify-adoption-design.md` (commit `2fda5f5`).

---

## File Structure

**New files**
- `docs/superpowers/specs/2026-04-22-graphify-evaluation.md` — S1 평가 리포트
- `docs/superpowers/specs/2026-04-22-graphify-adoption-codex-review.md` — S2 Codex 3-round 로그
- `scripts/graph_integrity_check.py` — graph integrity checker (S3)
- `tests/test_graph_integrity.py` — checker tests (S3)

**In-place revisions**
- `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` — S2에서 v2로 재작성 (§3.2, §5, §5.3, §7)
- `pyproject.toml` — S3에서 CLI entry points 제거, wheel 패키지 목록 축소, graphify dep 추가
- `Makefile` — S3에서 `graph`/`graph-serve`/`graph-lint` 타겟 추가
- `.gitignore` — S3에서 `build/graph/`, `tmp/graphify-eval/`, `graphify-out/`, `.graphify-cache/` 추가
- `CLAUDE.md` (프로젝트) — S4에서 Commands·Repository Map·Conventions 갱신
- `.claude/skills/semi-design-learning/SKILL.md` (경로 확정 필요) — S4에서 graphify-aware 개정

**Deletions**
- `src/semi_design_wiki/` 전체 (5 Python 파일)
- `tests/test_frontmatter.py`, `test_init_wiki.py`, `test_lint_wiki.py`, `test_sync_index.py`, `test_integration.py`
- `.claude/skills/semi-design-wiki/` 전체
- `wiki/program/program.md`, `scoring.md`, `promotion_policy.md` (S2에서 내용 이관 후)
- `wiki/index.md`

**Preserved (graphify seed corpus)**
- `wiki/raw/**` 전부 (papers, sessions, benchmarks, blogs, docs, repos, imports_manifest.yaml)

---

## Phase S1 — Evaluate

### Task 1: graphify 설치 & 평가용 디렉토리 준비

**Files:**
- Modify: `.gitignore`
- Create: `tmp/graphify-eval/` (gitignored)

- [ ] **Step 1: `.gitignore`에 graphify 산출물 경로 추가**

`.gitignore` 끝에 다음을 append:

```gitignore

# graphify evaluation & output (2026-04-22)
tmp/graphify-eval/
build/graph/
graphify-out/
.graphify-cache/
```

- [ ] **Step 2: graphify 설치**

```bash
uv tool install graphify
graphify --version
```

Expected: `graphify 0.4.25` 또는 더 최신. 실패 시 `uv tool install graphify --python 3.12` 시도.

- [ ] **Step 3: 평가 디렉토리 생성**

```bash
mkdir -p tmp/graphify-eval
```

- [ ] **Step 4: .gitignore만 커밋**

```bash
git add .gitignore
git commit -m "chore: gitignore graphify outputs for adoption eval"
```

---

### Task 2: K1 핵심 개념 20개 확정 (BLOCKING — 사용자 입력)

**Files:**
- Create: `docs/superpowers/specs/2026-04-22-graphify-evaluation.md` (스켈레톤)

- [ ] **Step 1: 평가 리포트 스켈레톤 작성**

`docs/superpowers/specs/2026-04-22-graphify-evaluation.md`:

```markdown
---
title: graphify S1 평가 리포트
status: in-progress
date: 2026-04-22
related: docs/superpowers/specs/2026-04-22-graphify-adoption-design.md
---

# graphify S1 평가 리포트

## 1. K1 핵심 개념 20개 (ex-post 합리화 방지 — 평가 전 고정)

<!-- 사용자 결정: 평가 시작 전 고정. 이후 수정 금지. -->
1.
2.
...
20.

## 2. 실행 로그

### 2.1 corpus-narrative (wiki/raw/)
- command:
- runtime:
- node count:
- edge count:
- API cost:

### 2.2 corpus-contract (wiki/program/)
- command:
- runtime:
- node count:
- edge count:
- API cost:

### 2.3 corpus-code (src/)
- command:
- runtime:
- node count:
- edge count:
- API cost:

### 2.4 corpus-all (repo root)
- command:
- runtime:
- node count:
- edge count:
- API cost:

## 3. 지표

| # | 지표 | 합격선 | 실측 | Pass/Fail |
|---|------|-------|------|-----------|
| M1 | `src/semi_design_wiki/` 5 모듈 + 주요 함수(`sync_index.regenerate`, `lint_wiki.check`, `frontmatter.parse_file`) 노드화 | 3/3 함수 노드 존재 | | |
| M2 | K1 핵심 개념 20개 중 node 존재 | ≥16/20 | | |
| M3 | inter-trench edge (narrative↔contract↔code) 수 ÷ 해당 3 trench 합산 node 수 | ≥ 0.5 | | |
| M4 | Leiden 커뮤니티 중 K1 α/β/γ/δ 축과 육안 매칭 | ≥ 1개 | | |
| M5 | 전체 스캔 비용 / 시간 | < $5 / < 10분 | | |

## 4. God-node 정성 리뷰 (top 5)

## 5. 판정

- [ ] M1~M5 중 ≥4개 합격 → S2 진행
- [ ] M1~M3 중 2개 이상 미달 → graphify 채택 철회, 사용자 재질의
- [ ] M5만 미달 → 비용 최적화 후 S1 재시도

판정 결과: TBD
```

- [ ] **Step 2: 사용자에게 K1 핵심 개념 20개 요청 (Learn by Doing)**

AskUserQuestion으로 직접 입력받거나, 사용자가 위 파일의 §1을 직접 채우도록 안내한다. 예시 후보(최종은 사용자 결정):

```
LibreLane 2.4 · OpenROAD · Yosys · sky130A · Gemmini ·
MLPerf Tiny v1.3 · ORFS-agent · Karpathy AutoResearch ·
H1b non-knob patch · Leiden clustering · tree-sitter ·
Fargate Spot · Step Functions Map · DynamoDB 4-tables ·
lockfile.yaml SHA pin · L1 Process · L2 Substrate ·
L3 Content · reversible-patch skill · typed-frontmatter
```

사용자가 최종 20개를 확정한 뒤 §1을 채운 상태로 다음 단계 진행.

- [ ] **Step 3: 스켈레톤 커밋 (판정 전이라 status: in-progress로 유지)**

```bash
git add docs/superpowers/specs/2026-04-22-graphify-evaluation.md
git commit -m "docs(spec): add S1 graphify evaluation skeleton"
```

---

### Task 3: graphify 전체 스캔 (skill.md 레시피, 단일 실행)

> **(2026-04-22 수정)** 원래 플랜의 4-corpus 분리 스캔은 graphify CLI가 stand-alone에서 전체 파이프라인을 실행하지 않는다는 사실(spec §1.3)이 드러나 폐기. 단일 전체 repo 스캔으로 모든 지표 평가 가능.

**Files:**
- Write outputs to `graphify-out/` (gitignored via existing `graphify-out/` rule) — graphify 기본 위치
- Modify: `docs/superpowers/specs/2026-04-22-graphify-evaluation.md` §2 실행 로그 (단일 scan)

- [ ] **Step 1: Detect — 파일 분류**

`uv tool` 로 설치한 graphify interpreter 경로 확보 후:

```bash
GRAPHIFY_PY=$(uv tool run --from graphifyy python -c "import sys; print(sys.executable)")
echo "$GRAPHIFY_PY" > graphify-out/.graphify_python
mkdir -p graphify-out

"$GRAPHIFY_PY" -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('.'))
print(json.dumps(result, indent=2))
" > graphify-out/.graphify_detect.json
```

Expected: `files.{code,docs,papers,images,video}` 카테고리별 분류 출력. `total_files`, `total_words` 확인.

- [ ] **Step 2: AST 추출 (Part A) — 코드 파일**

```bash
"$GRAPHIFY_PY" -c "
import json
from pathlib import Path
from graphify.extract import extract

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
code_files = [Path(p) for p in detect.get('files', {}).get('code', [])]
print(f'Extracting AST from {len(code_files)} code files...')
result = extract(code_files, cache_root=Path('graphify-out/cache'))
Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result))
print(f'AST extraction complete: {len(result.get(\"extractions\", []))} extractions')
"
```

Expected: 결정론적. LLM 비용 0. `graphify-out/.graphify_ast.json` 생성.

- [ ] **Step 3: 의미 추출 (Part B) — 마크다운/문서 subagent dispatch**

skill.md Step 3B의 dispatch 레시피를 따라, `detect.files.docs` 리스트의 각 `.md` 파일마다 **fresh Claude subagent**를 dispatch(controller = this Claude Code session). 각 subagent는:
- 파일 1개를 읽고 EXTRACTED/INFERRED/AMBIGUOUS 트리플 리스트 반환
- 출력 형식: skill.md에 명시된 JSON 구조 준수

이 세션에서 `Agent` tool로 병렬 dispatch. 결과를 `graphify-out/.graphify_semantic.json`에 merge.

대상 파일(2026-04-22 시점):
- `wiki/raw/papers/k1-{alpha,beta,gamma,delta}-*.md` (4)
- `wiki/raw/sessions/phase-0-a{1..4}-*.md` (4)
- `wiki/program/{program,scoring,promotion_policy}.md` (3)
- `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` (1)
- `docs/knowledge-base/2026-04-19-k1-direction-report.md` (1)
- `CLAUDE.md` (1)
- 기타 docs/*/ 마크다운 (변수)

추정 subagent 수: ~15~25개. 비용 예산 $5 내로 관리 (M5 게이트).

- [ ] **Step 4: Build + Cluster + Analyze + Export**

```bash
"$GRAPHIFY_PY" -c "
import json
from pathlib import Path
from graphify.build import build
from graphify.cluster import cluster
from graphify.analyze import god_nodes, surprising_connections
from graphify.export import generate_html

ast = json.loads(Path('graphify-out/.graphify_ast.json').read_text())
sem = json.loads(Path('graphify-out/.graphify_semantic.json').read_text())
extractions = ast.get('extractions', []) + sem.get('extractions', [])

G = build(extractions)
communities, labels = cluster(G)
gods = god_nodes(G, top_n=10)
surprises = surprising_connections(G, communities=communities, top_n=5)

# Export
generate_html(G, communities, 'graphify-out/graph.html', community_labels=labels)
Path('graphify-out/graph.json').write_text(json.dumps({'nodes': list(G.nodes(data=True)), 'edges': list(G.edges(data=True))}, default=str))
# GRAPH_REPORT.md 는 god_nodes + communities 요약
print(f'nodes={G.number_of_nodes()}, edges={G.number_of_edges()}, communities={len(communities)}')
print('gods:', [g['label'] for g in gods])
"
```

(`cluster` 함수의 정확한 시그니처는 실행 시점에 검증. 필요시 `inspect.signature`로 확인 후 조정.)

- [ ] **Step 5: 실행 로그를 §2에 기록**

결과(node/edge/community/runtime/cost)를 `docs/superpowers/specs/2026-04-22-graphify-evaluation.md` §2에 기록. 분리 스캔이 아니므로 §2는 단일 "전체 repo 스캔" 섹션으로 통합.

- [ ] **Step 6: 커밋**

```bash
git add docs/superpowers/specs/2026-04-22-graphify-evaluation.md
git commit -m "docs(spec): record S1 graphify scan measurements (single-corpus)"
```

**Implementation Notes**
- 이 Task는 주로 controller (this session) + subagent dispatch 루프로 구성. 자동화된 bash 스크립트가 아님.
- 시간 예산: 10분(AST+build+export) + subagent 병렬 dispatch 대기 시간.
- subagent prompt 템플릿은 skill.md Step 3B의 JSON 출력 규약을 그대로 사용.

---

### Task 4: M1~M5 채점 + Pass/Fail 판정 (단일 graph.json)

> **(2026-04-22 수정)** 4-corpus 폐기 반영 — 모든 grep/계산은 단일 `graphify-out/graph.json` 기준.

**Files:**
- Modify: `docs/superpowers/specs/2026-04-22-graphify-evaluation.md` §3, §4, §5

- [ ] **Step 1: M1 — 코드 그래프 정밀도**

```bash
grep -E "(sync_index|lint_wiki|frontmatter)" graphify-out/graph.json
```

3개 함수 노드(`sync_index.regenerate`, `lint_wiki.check`, `frontmatter.parse_file`)의 존재 여부 확인. 채점표 §3에 Pass/Fail 기록.

- [ ] **Step 2: M2 — K1 개념 커버리지**

§1의 20개 개념 각각을 `graph.json`에서 grep (대소문자 무시, 동의어 허용 — 예: "LibreLane 2.4" ≈ "librelane"):

```bash
"$GRAPHIFY_PY" -c "
import json
from pathlib import Path

concepts = ['CVDP', 'VerilogEval', 'RTLLM', 'EvolVE', 'ORFS-agent', 'METRICS2.1', 'ORFS AutoTuner', 'AutoEDA', 'LibreLane', 'OpenROAD', 'sky130', 'Gemmini', 'MLPerf Tiny', 'Karpathy', 'Voyager', 'A-MEM', 'L1 Process', 'L2 Substrate', 'L3 Content', 'H1b']

graph = json.loads(Path('graphify-out/graph.json').read_text())
text = json.dumps(graph).lower()
hits = [(c, c.lower() in text) for c in concepts]
for c, hit in hits:
    print(f'{\"✓\" if hit else \"✗\"} {c}')
print(f'\\nTotal: {sum(1 for _,h in hits if h)}/20')
"
```

≥16/20이면 Pass. 매칭은 raw string substring(정규식 아님).

- [ ] **Step 3: M3 — inter-trench edge 비율**

단일 graph.json에서 각 node의 `source_file` (또는 graphify 실제 스키마 키)을 파싱해 파일 경로 prefix 기준으로 trench 분류:
- **narrative** = `wiki/raw/` 하위
- **contract** = `wiki/program/` 하위
- **code** = `src/` 하위
- **spec** = `docs/superpowers/specs/` 하위

```bash
"$GRAPHIFY_PY" -c "
import json
from pathlib import Path
graph = json.loads(Path('graphify-out/graph.json').read_text())
nodes = {n['id']: n for n, *_ in graph.get('nodes', [])} if isinstance(graph.get('nodes', [None])[0], list) else {n['id']: n for n in graph.get('nodes', [])}

def trench(node):
    src = node.get('source_file', node.get('file', ''))
    if 'wiki/raw' in src: return 'narrative'
    if 'wiki/program' in src: return 'contract'
    if 'src/' in src: return 'code'
    if 'docs/superpowers/specs' in src: return 'spec'
    return 'other'

trenches_of_interest = {'narrative','contract','code'}
nodes_in_3 = [nid for nid, n in nodes.items() if trench(n) in trenches_of_interest]
edges = graph.get('edges', [])

def edge_nodes(e):
    if isinstance(e, list): return e[0], e[1]
    return e.get('source'), e.get('target')

inter = 0
for e in edges:
    s, t = edge_nodes(e)
    if s in nodes and t in nodes:
        ts, tt = trench(nodes[s]), trench(nodes[t])
        if ts != tt and ts in trenches_of_interest and tt in trenches_of_interest:
            inter += 1

ratio = inter / max(len(nodes_in_3), 1)
print(f'nodes in 3 trenches: {len(nodes_in_3)}, inter-trench edges: {inter}, ratio: {ratio:.3f}')
"
```

Ratio ≥ 0.5이면 Pass. 실제 graphify 스키마에서 node 객체의 `source_file` 키 이름이 다르면 그에 맞게 조정 (예: `file`, `origin`, `path`).

- [ ] **Step 4: M4 — Leiden 커뮤니티 육안 매칭**

`open graphify-out/graph.html` 로 HTML 시각화 열기. `GRAPH_REPORT.md`의 커뮤니티 리스트와 god-node 목록을 함께 리뷰. K1 α(LLM-for-HDL) · β(agentic EDA) · γ(opensource EDA) · δ(research memory) 중 ≥1개와 육안 매칭되는지 판단. §3·§4에 기록.

- [ ] **Step 5: M5 — 비용·시간 합산**

Task 3 로그에서 runtime + API cost 총합. `< 10분` AND `< $5`면 Pass. subagent dispatch가 주 비용 드라이버.

- [ ] **Step 6: 판정 + §5 작성**

3 시나리오 중 하나 선택:
- Pass (≥4/5): §5에 "S2 진행" 명시, status를 `passed`로
- Fail (M1~M3 중 2개 이상 미달): §5에 "graphify 채택 철회 권고, 사용자 재질의 필요" 명시, status를 `failed`로, **Task 5 이후 전부 중단**
- Partial (M5만 미달): §5에 "비용 최적화 후 재시도" 명시, status를 `retry`로, Task 3부터 다시 실행

- [ ] **Step 7: 평가 리포트 최종 커밋**

```bash
git add docs/superpowers/specs/2026-04-22-graphify-evaluation.md
git commit -m "docs(spec): S1 evaluation verdict ([pass|fail|retry])"
```

---

## Phase S2 — Spec Revise (Pass일 때만 진행)

### Task 5: Overview spec §3.2 L2 interface 재작성

**Files:**
- Modify: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3.2

- [ ] **Step 1: 기존 §3.2 블록 위치 파악**

```bash
grep -n "L2.memory.recall\|L2.skill_library\|L2.lint" docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
```

§3.2 상단과 끝 라인 확인.

- [ ] **Step 2: §3.2 블록 교체**

기존 L2 interface 정의를 다음으로 교체:

```markdown
### 3.2 Layer Interface Contracts (v2, 2026-04-22 graphify 전환)

> **Revision note:** v1의 wiki-engine 기반 계약을 graphify v0.4.25 기반으로 재정의. 구현체는 `docs/superpowers/specs/2026-04-22-graphify-adoption-design.md` §3.2·§4 참조.

| Interface | Signature | 구현체 |
|-----------|-----------|--------|
| `L1.run(spec_uri)` | → run artifact bundle | 기존 유지 |
| `L2.memory.recall(query: str)` | → `Node[]` with `tier ∈ {EXTRACTED, INFERRED, AMBIGUOUS}` | `graphify query` / MCP server |
| `L2.skill_library.query(name: str)` | → `Skill` 또는 null | graphify `.claude/skills/` 인덱싱 결과 |
| `L2.lint.check()` | → `Report(ok: bool, errors: list[str])` | `scripts/graph_integrity_check.py` (orphan=0, dangling=0, AMBIGUOUS 노드/전체 ≤ 0.3) |

**의미 gap 공지**: graphify `tier`는 **추출 신뢰도**이며 **주장 타당성**이 아님. 소비자(L1/L3 agent)는 `tier`를 "검토 필요도" 신호로만 해석하고, 주장 타당성은 H1/H3 실험 결과에서만 판정한다 (§5 참조).
```

- [ ] **Step 3: 체크 — 파일 전체에서 이전 L2 인터페이스 참조가 v2와 충돌하는 곳 없는지**

```bash
grep -n "wiki-lint\|wiki-sync\|promotion_policy\|frontmatter.parse_file" docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
```

출력이 남아있으면 §5·§7에서도 참조가 있다는 뜻 — 해당 지점은 Task 6·8에서 제거된다.

- [ ] **Step 4: 부분 커밋**

```bash
git add docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
git commit -m "docs(spec): revise §3.2 L2 interfaces for graphify (v2)"
```

---

### Task 6: Overview spec §5 G-score / Promotion 재작성

**Files:**
- Modify: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §5

- [ ] **Step 1: 기존 §5 블록 위치 파악**

```bash
grep -n "^## 5\.\|### 5\." docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
```

- [ ] **Step 2: §5.1·§5.2의 G-score 문단 교체**

Phase 1a의 `confidence_score` frontmatter 기반 서술을 다음으로 교체:

```markdown
### 5.1 Knowledge tier (v2, graphify 전환)

그래프 지식은 graphify 3-tier를 사용한다:
- **EXTRACTED** (confidence 1.0) — 소스에서 직접 발견된 사실
- **INFERRED** (confidence < 1.0) — graphify의 Claude 서브에이전트가 문맥에서 합리적으로 추론
- **AMBIGUOUS** — 자동 판정 어려움, human review 대기

구 `confidence_score` frontmatter는 폐기됨.

### 5.2 Promotion (v2)

Promotion = graphify UI 또는 CLI 워크플로에서 **AMBIGUOUS → INFERRED/EXTRACTED** 이동 (human review pass). 자동 promotion은 없다.
```

- [ ] **Step 3: §5.3 canonical decision table — 증거 경로만 최소 수정**

기존 §5.3의 "evidence from wiki findings/decisions/failures" 문구를 다음으로 교체:

```markdown
**증거 출처 (v2)**: `graphify query` 결과에서 `tier ∈ {EXTRACTED, INFERRED}` 인 god-node 및 human-reviewed claim. publish/reframed/kill 분기 기준(H1 pass count × H3 validity)은 v1과 동일.
```

**건드리지 말 것**: publish/reframed/kill 분기 규칙 자체.

- [ ] **Step 4: 부분 커밋**

```bash
git add docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
git commit -m "docs(spec): revise §5 G-score/Promotion for graphify (v2)"
```

---

### Task 7: Overview spec §7 운영 규칙 재작성

**Files:**
- Modify: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §7
- Read: `wiki/program/program.md`, `scoring.md`, `promotion_policy.md`

- [ ] **Step 1: wiki/program/*.md 내용 읽기**

```bash
cat wiki/program/program.md wiki/program/scoring.md wiki/program/promotion_policy.md
```

- [ ] **Step 2: §7에 inline으로 운영 헌법 흡수**

§7 기존 내용 유지하되, `wiki/program/*.md` 참조 문구를 해당 파일의 실제 내용으로 치환. 요지:
- 주기: weekly cadence
- sub-plan 승인: gate-by-gate
- 스코어링: H1 × H3 기반 (자체 스코어링 정책 선언 없음, §5.3 canonical decision table 준수)
- promotion: §5.2 (graphify AMBIGUOUS→INFERRED/EXTRACTED)

`wiki/program/*.md` 파일은 아직 삭제하지 않는다 (S4 Task 18에서 삭제).

- [ ] **Step 3: §7 헤더에 v2 revision note 추가**

```markdown
### 7 Operating Rules (v2, 2026-04-22 graphify 전환)

> **Revision note:** `wiki/program/*.md`의 운영 헌법을 이 §7에 흡수. 해당 파일은 S4에서 삭제 예정. v1의 promotion_policy는 graphify AMBIGUOUS→INFERRED/EXTRACTED human review로 대체 (§5.2).
```

- [ ] **Step 4: 부분 커밋**

```bash
git add docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
git commit -m "docs(spec): absorb wiki/program/* into §7 operating rules (v2)"
```

---

### Task 8: Codex 3-round review

**Files:**
- Create: `docs/superpowers/specs/2026-04-22-graphify-adoption-codex-review.md`

- [ ] **Step 1: 리뷰 로그 파일 생성**

`docs/superpowers/specs/2026-04-22-graphify-adoption-codex-review.md`:

```markdown
---
title: graphify 전환 overview spec v2 Codex 3-round review
date: 2026-04-22
target: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md (v2)
---

# Codex 3-round review log

## Round 1 — 구조/일관성 (L2 인터페이스 호환성)
- dispatched:
- findings:
- resolution:

## Round 2 — 의미 gap 설명 충분성 (graphify confidence ≠ 주장 타당성)
- dispatched:
- findings:
- resolution:

## Round 3 — §5.3 증거 경로 변경이 H1/H3 falsifier를 훼손하지 않는지
- dispatched:
- findings:
- resolution:

## Verdict
- [ ] 3 rounds all pass → S3 진행
- [ ] ≥1 round fail after 3 iterations → S3 진입 금지, spec 재작성 필요
```

- [ ] **Step 2: Round 1 — Codex dispatch**

`codex:rescue` 또는 `Agent(subagent_type=general-purpose)` 로 다음 프롬프트 전달:

> 다음 spec의 §3.2만 검토해줘: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` (v2). 검토 관점: L1.run(spec_uri)·L2.memory·L2.skill_library·L2.lint 네 인터페이스가 상호 호환되는가? L2.lint가 graph integrity check로 좁혀진 것이 L2.memory.recall 반환값 품질 보장에 충분한가? 200단어 이내.

응답을 §Round 1에 기록. 이슈 발견 시 spec 수정 후 재-dispatch.

- [ ] **Step 3: Round 2 — Codex dispatch**

> 위 spec의 §5만 검토해줘. 검토 관점: graphify confidence tier가 "추출 신뢰도"인 것과 v1 `confidence_score`가 내포한 "주장 타당성" 사이 의미 gap을 §3.2·§5가 충분히 명시하는가? 독자가 이 gap을 놓쳐 H1/H3 실험 없이 tier로 주장을 판정할 위험이 남아있는가? 200단어 이내.

§Round 2에 기록.

- [ ] **Step 4: Round 3 — Codex dispatch**

> 위 spec의 §5.3 canonical decision table만 검토해줘. 검토 관점: publish/reframed/kill 분기 규칙은 v1과 동일하되 "증거 출처"만 graphify god-node + human-reviewed claim으로 교체되었다. 이 변경이 H1(non-knob structural patch)·H3 falsifier에 영향을 주는가? 구체적으로 어떤 falsifier가 흔들리는가? 200단어 이내.

§Round 3에 기록.

- [ ] **Step 5: 판정 + 커밋**

3 rounds 전부 pass면 `Verdict`에 pass 체크 후:

```bash
git add docs/superpowers/specs/2026-04-22-graphify-adoption-codex-review.md
git commit -m "docs(spec): complete Codex 3-round review for graphify v2"
```

≥1 round fail → spec 수정 후 해당 round만 재-dispatch. 3회 반복 실패 시 **S3 진입 금지**.

---

## Phase S3 — Code Swap (S2 Pass일 때만 진행)

### Task 9: graph_integrity_check — 실패 테스트 작성 (TDD Red)

**Files:**
- Create: `tests/test_graph_integrity.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_graph_integrity.py`:

```python
import json
from pathlib import Path

import pytest


def _write_graph(path: Path, nodes: list[dict], edges: list[dict]) -> Path:
    path.write_text(json.dumps({"nodes": nodes, "edges": edges}))
    return path


def test_clean_graph_passes(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "EXTRACTED"},
            {"id": "b", "tier": "INFERRED"},
        ],
        edges=[{"source": "a", "target": "b"}],
    )
    ok, errors = check_graph_integrity(graph)
    assert ok, errors


def test_orphan_node_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "EXTRACTED"},
            {"id": "b", "tier": "INFERRED"},
            {"id": "orphan", "tier": "EXTRACTED"},
        ],
        edges=[{"source": "a", "target": "b"}],
    )
    ok, errors = check_graph_integrity(graph)
    assert not ok
    assert any("orphan" in e.lower() for e in errors)


def test_dangling_edge_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[{"id": "a", "tier": "EXTRACTED"}],
        edges=[{"source": "a", "target": "nonexistent"}],
    )
    ok, errors = check_graph_integrity(graph)
    assert not ok
    assert any("dangling" in e.lower() for e in errors)


def test_ambiguous_ratio_exceeded_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "AMBIGUOUS"},
            {"id": "b", "tier": "AMBIGUOUS"},
            {"id": "c", "tier": "EXTRACTED"},
        ],
        edges=[
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "a"},
        ],
    )
    ok, errors = check_graph_integrity(graph, ambiguous_threshold=0.3)
    assert not ok
    assert any("AMBIGUOUS" in e for e in errors)


def test_ambiguous_ratio_within_threshold_passes(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "AMBIGUOUS"},
            {"id": "b", "tier": "EXTRACTED"},
            {"id": "c", "tier": "EXTRACTED"},
            {"id": "d", "tier": "EXTRACTED"},
        ],
        edges=[
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
        ],
    )
    ok, errors = check_graph_integrity(graph, ambiguous_threshold=0.3)
    assert ok, errors


def test_empty_graph_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(tmp_path / "graph.json", nodes=[], edges=[])
    ok, errors = check_graph_integrity(graph)
    assert not ok
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
uv run pytest tests/test_graph_integrity.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts'` 또는 `scripts.graph_integrity_check` import 실패 (6 tests fail/error).

---

### Task 10: graph_integrity_check 구현 (TDD Green)

**Files:**
- Create: `scripts/graph_integrity_check.py`
- Create: `scripts/__init__.py` (empty, pytest가 scripts를 package로 인식하도록)

- [ ] **Step 1: `scripts/__init__.py` 빈 파일 생성**

```bash
mkdir -p scripts
touch scripts/__init__.py
```

- [ ] **Step 2: `scripts/graph_integrity_check.py` 작성**

```python
"""Graph integrity check for graphify-generated graph.json.

Verifies three invariants:
1. No orphan nodes (every node has at least one incident edge)
2. No dangling edges (every edge references existing nodes)
3. AMBIGUOUS node ratio <= threshold (default 0.3)

Exits non-zero on any violation. Used as L2.lint.check() replacement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_AMBIGUOUS_THRESHOLD = 0.3


def check_graph_integrity(
    graph_path: Path,
    ambiguous_threshold: float = DEFAULT_AMBIGUOUS_THRESHOLD,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    graph = json.loads(graph_path.read_text())
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        return False, ["graph has no nodes"]

    node_ids = {n["id"] for n in nodes}

    for e in edges:
        if e["source"] not in node_ids:
            errors.append(f"dangling edge source: {e['source']} -> {e['target']}")
        if e["target"] not in node_ids:
            errors.append(f"dangling edge target: {e['source']} -> {e['target']}")

    referenced = set()
    for e in edges:
        referenced.add(e["source"])
        referenced.add(e["target"])
    orphans = node_ids - referenced
    if orphans:
        sample = sorted(orphans)[:5]
        errors.append(f"orphan nodes ({len(orphans)}): {sample}")

    ambiguous = sum(1 for n in nodes if n.get("tier") == "AMBIGUOUS")
    ratio = ambiguous / len(nodes)
    if ratio > ambiguous_threshold:
        errors.append(
            f"AMBIGUOUS ratio {ratio:.2%} exceeds threshold {ambiguous_threshold:.2%}"
        )

    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path, help="Path to graphify-generated graph.json")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_AMBIGUOUS_THRESHOLD,
        help=f"AMBIGUOUS ratio threshold (default {DEFAULT_AMBIGUOUS_THRESHOLD})",
    )
    args = parser.parse_args()

    ok, errors = check_graph_integrity(args.graph, args.threshold)
    if not ok:
        print("graph integrity check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("graph integrity check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: `tool.pytest.ini_options`에 scripts 경로 추가 확인**

`pyproject.toml`의 `[tool.pytest.ini_options]` 섹션에서 `pythonpath` 가 `["src"]` 만 포함하면 `scripts`도 import 가능하도록 `"."` 추가:

```bash
grep -A 5 "tool.pytest" pyproject.toml
```

`pythonpath` 를 `["src", "."]`로 수정 (`.` 추가로 `scripts.graph_integrity_check` import 가능).

- [ ] **Step 4: 테스트 실행 → 전부 통과 확인**

```bash
uv run pytest tests/test_graph_integrity.py -v
```

Expected: 6 passed.

- [ ] **Step 5: 커밋**

```bash
git add scripts/__init__.py scripts/graph_integrity_check.py tests/test_graph_integrity.py pyproject.toml
git commit -m "feat(graph): add graph_integrity_check (orphan/dangling/AMBIGUOUS)"
```

---

### Task 11: pyproject.toml — graphify 의존성 추가 + CLI entry points 제거

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: graphify를 dev dependency로 추가**

> **(2026-04-22 수정)** graphify는 PyPI에 없음. PyPI distribution 이름은 `graphifyy` (double-y) 이고 CLI는 `graphify`. 본 프로젝트는 git URL + commit pin을 사용.

`pyproject.toml`의 `[project.optional-dependencies]` `dev` 리스트에 추가:

```toml
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "graphifyy @ git+https://github.com/safishamsi/graphify@215b5d40e78e498100cbf8855224331c40f757d9",
]
```

commit `215b5d4`는 v0.4.25 기준으로 Task 1에서 검증된 버전. 향후 upstream 업데이트 시 이 pin을 갱신.

- [ ] **Step 2: `[project.scripts]`에서 wiki CLI 3개 제거**

기존:
```toml
[project.scripts]
wiki-init = "semi_design_wiki.init_wiki:main"
wiki-sync = "semi_design_wiki.sync_index:main"
wiki-lint = "semi_design_wiki.lint_wiki:main"
semi-run = "semi_design_runner.cli:main"
semi-metric-collector = "semi_design_runner.metric_collector_main:main"
```

교체:
```toml
[project.scripts]
semi-run = "semi_design_runner.cli:main"
semi-metric-collector = "semi_design_runner.metric_collector_main:main"
```

- [ ] **Step 3: `[tool.hatch.build.targets.wheel]`의 패키지 목록에서 `semi_design_wiki` 제거**

기존:
```toml
packages = ["src/semi_design_wiki", "src/semi_design_runner"]
```

교체:
```toml
packages = ["src/semi_design_runner"]
```

- [ ] **Step 4: 프로젝트 name/description 갱신 (옵션)**

```toml
[project]
name = "semi-design"
version = "0.1.0"
description = "Semiconductor design research program (L1 runner + graphify knowledge graph)"
```

- [ ] **Step 5: `uv sync` 로 lock 갱신**

```bash
uv sync --all-extras
```

Expected: graphify>=0.4.25가 `uv.lock`에 추가됨. 실패 시 graphify의 Python 버전 요구와 충돌 여부 확인.

- [ ] **Step 6: 커밋**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): add graphify, drop wiki-* CLI entry points"
```

---

### Task 12: Makefile — graph 타겟 추가

**Files:**
- Modify: `Makefile`

> **(2026-04-22 수정)** `make graph`를 순수 bash 타겟으로 둘 수 없음 — graphify 전체 빌드는 AI 에이전트 세션에서 `/graphify .` 슬래시커맨드로 실행해야 함. Makefile은 증분 업데이트·serve·lint 위주로 구성.

- [ ] **Step 1: 새 타겟 추가**

기존 Makefile 끝에 append:

```makefile

graph-update:
	uv run graphify update .

graph-build:
	@echo "Full graphify build must be run from an AI agent session."
	@echo "In Claude Code, invoke: /graphify ."
	@echo "Or follow skill.md recipe (see docs/superpowers/specs/2026-04-22-graphify-adoption-design.md §4.1)."

graph-serve:
	uv run python -m graphify.serve graphify-out/graph.json

graph-lint:
	uv run python scripts/graph_integrity_check.py graphify-out/graph.json
```

`.PHONY` 리스트에 추가:

```makefile
.PHONY: install test lint fmt clean graph-update graph-build graph-serve graph-lint
```

- [ ] **Step 2: 동작 확인**

```bash
make graph-update   # graphify update . 호출 — AST-only, LLM 비용 0. 즉시 끝남.
make graph-build    # echo 안내만 출력. 실제 빌드는 /graphify . in Claude Code.
make graph-lint     # graphify-out/graph.json 검증. graph.json이 없으면 에러 — 정상.
```

**주의**: Task 14 전체 게이트에서 `make graph-lint` 가 OK 되려면 `graphify-out/graph.json`이 존재해야 함. S1 Task 3에서 이미 생성됐다면 문제 없음. S3를 S1 없이 테스트하려면 별도 fixture graph.json 필요.

`make graph-lint` 가 FAIL이면 3가지 중 하나: (a) orphan 노드가 레포에 실재 존재, (b) AMBIGUOUS 비율 0.3 초과, (c) graphify 스키마에서 `tier` 필드명이 다름. (c)라면 `scripts/graph_integrity_check.py`의 필드명을 실제 graph.json에 맞게 조정 후 `test_graph_integrity.py` 픽스처도 갱신.

- [ ] **Step 3: 커밋**

```bash
git add Makefile
git commit -m "feat(make): add graph-update/graph-build/graph-serve/graph-lint targets"
```

---

### Task 13: wiki 엔진 제거 (`src/semi_design_wiki/` + tests)

**Files:**
- Delete: `src/semi_design_wiki/` (5 파일)
- Delete: `tests/test_frontmatter.py`, `test_init_wiki.py`, `test_lint_wiki.py`, `test_sync_index.py`, `test_integration.py`

- [ ] **Step 1: 삭제 전 레포 내 참조 검색**

```bash
grep -rn "semi_design_wiki\|wiki-init\|wiki-sync\|wiki-lint" --include="*.py" --include="*.toml" --include="*.md" --include="Makefile" . | grep -v "^./docs/superpowers/specs\|^./docs/superpowers/plans\|^./.git\|^./tmp/\|^./build/"
```

남은 참조가 `docs/` 외부에 있으면 수정 필요 (현재 명시적으로 이 Task에 포함되지 않은 참조). 모두 수정/제거.

- [ ] **Step 2: 파일 삭제**

```bash
rm -rf src/semi_design_wiki/
rm tests/test_frontmatter.py tests/test_init_wiki.py tests/test_lint_wiki.py tests/test_sync_index.py tests/test_integration.py
```

- [ ] **Step 3: pytest 실행 — 남은 테스트만으로 통과 확인**

```bash
uv run pytest -v
```

Expected: wiki 관련 테스트 전부 사라지고, 남은 테스트 (runner, graph integrity, sanity 등) 전부 pass.

- [ ] **Step 4: ruff 실행**

```bash
uv run ruff check src tests scripts
```

Expected: pass. `src` 가 이제 `semi_design_runner` 만 포함.

- [ ] **Step 5: 커밋**

```bash
git add -A src/semi_design_wiki tests/test_frontmatter.py tests/test_init_wiki.py tests/test_lint_wiki.py tests/test_sync_index.py tests/test_integration.py
git commit -m "refactor: remove src/semi_design_wiki and wiki tests (graphify 전환)"
```

`git add -A <path>` 는 삭제를 스테이징한다.

---

### Task 14: S3 전체 게이트 검증

**Files:** (없음)

- [ ] **Step 1: `make test` 전체 통과**

```bash
make test
```

Expected: all pass.

- [ ] **Step 2: `make graph-lint` 통과**

```bash
make graph-lint
```

Expected: `graph integrity check OK`. 만약 없으면 `make graph` 먼저 실행.

- [ ] **Step 3: `make lint` 통과**

```bash
make lint
```

Expected: pass.

- [ ] **Step 4: 세 게이트 모두 OK면 S3 종료 마커 커밋 (메시지만)**

```bash
git commit --allow-empty -m "chore(s3): gates passed — code swap complete"
```

실패 시 **Phase S4 진입 금지**. `git log --oneline -10` 으로 Task 13 커밋 ID 확인 후 `git revert <sha>` 로 엔진 복구.

---

## Phase S4 — Doc & Skill Cleanup

### Task 15: 프로젝트 CLAUDE.md 갱신

**Files:**
- Modify: `CLAUDE.md` (프로젝트 루트)

- [ ] **Step 1: "Implementation Status" 표 갱신**

`## Implementation Status` 섹션의 "Phase 1a — Wiki Skill Engine ✅ done" 행을 다음으로 교체:

```markdown
| Phase 1a — Wiki Skill Engine | `src/semi_design_wiki/`, `tests/` | ⛔ **폐기** (2026-04-22 graphify로 전환, `docs/superpowers/specs/2026-04-22-graphify-adoption-design.md` 참조) |
| Wiki → graphify 전환 | `scripts/graph_integrity_check.py` + `build/graph/` + graphify v0.4.25 | ✅ S1~S4 완료 |
```

- [ ] **Step 2: "Commands" 섹션에서 wiki CLI 블록 제거, graph 타겟 추가**

다음 3줄 삭제:
```bash
uv run wiki-init --root wiki     # idempotent wiki scaffold
uv run wiki-sync --root wiki     # regenerate wiki/index.md atomically
uv run wiki-lint --root wiki     # validate frontmatter + links
```

다음으로 교체:
```bash
make graph            # scan repo, write build/graph/graph.json
make graph-serve      # start graphify MCP server for L2.memory.recall
make graph-lint       # graph integrity check (L2.lint.check)
uv run graphify query "MLPerf Tiny"   # ad-hoc query
```

- [ ] **Step 3: "Repository Map" 섹션에서 wiki 관련 항목 갱신**

다음 항목들 수정/제거:
- `` `.claude/skills/semi-design-wiki/` — shell for wiki ingest...`` → **항목 전체 삭제**
- `` `wiki/raw/sessions/phase-0-*.md` — ...`` → 유지 (graphify 입력)
- `` `wiki/raw/papers/k1-{alpha,...}` — ...`` → 유지
- `` `wiki/program/{program,scoring,promotion_policy}.md` — ...`` → **삭제 예정 마크**:
  ```markdown
  - ~~`wiki/program/*.md`~~ — 2026-04-22 spec §7로 흡수 후 삭제 예정 (Task 18)
  ```

- [ ] **Step 4: "Before Non-Trivial Work" 1번 항목 수정**

기존:
```markdown
1. Check `docs/learning/phase-0-curriculum.md` and `wiki/raw/sessions/` for the latest learning state.
```

교체:
```markdown
1. Check `docs/learning/phase-0-curriculum.md` and `wiki/raw/sessions/` for the latest learning state. For knowledge graph lookup, use `graphify query "..."` or open `build/graph/graph.html`.
```

- [ ] **Step 5: "Code Conventions" — "Frontmatter" 규칙 삭제**

다음 bullet 삭제:
```markdown
- **Frontmatter**: every wiki page starts with `---\n...\n---\n`. ...
```

- [ ] **Step 6: "Project Context" 근처에 전역 LLM Wiki 규칙 예외 조항 추가**

`## Project Context` 섹션 끝에 append:

```markdown
> **LLM Wiki 활용 규칙 예외**: 본 프로젝트는 2026-04-22부로 전역 `/Users/dohyunjung/Workspace/CLAUDE.md`의 "LLM Wiki 활용 규칙"을 따르지 않는다. 대신 graphify v0.4.25 기반 `build/graph/graph.json` 및 `graphify query` CLI를 사용한다. 지식 참조가 필요하면 `make graph-serve` 로 MCP 서버를 띄워 조회한다.
```

- [ ] **Step 7: 커밋**

```bash
git add CLAUDE.md
git commit -m "docs(claude-md): update project CLAUDE.md for graphify"
```

---

### Task 16: `.claude/skills/semi-design-wiki/` 제거

**Files:**
- Delete: `.claude/skills/semi-design-wiki/` 전체

- [ ] **Step 1: 디렉토리 내용 먼저 확인**

```bash
ls -la .claude/skills/semi-design-wiki/
cat .claude/skills/semi-design-wiki/SKILL.md 2>/dev/null | head -20
```

- [ ] **Step 2: 디렉토리 삭제**

```bash
rm -rf .claude/skills/semi-design-wiki/
```

- [ ] **Step 3: `.claude/settings.json` 또는 plugin manifest에서 참조 제거**

```bash
grep -rn "semi-design-wiki" .claude/ 2>/dev/null
```

참조가 있으면 해당 파일에서 엔트리 제거.

- [ ] **Step 4: 커밋**

```bash
git add -A .claude/
git commit -m "chore(skills): remove semi-design-wiki skill (replaced by graphify)"
```

---

### Task 17: `.claude/skills/semi-design-learning/` 재조준

**Files:**
- Modify: `.claude/skills/semi-design-learning/SKILL.md` (또는 해당 스킬의 메인 파일)

- [ ] **Step 1: 스킬 메인 파일 확인**

```bash
ls .claude/skills/semi-design-learning/
cat .claude/skills/semi-design-learning/SKILL.md 2>/dev/null
```

- [ ] **Step 2: "wiki ingest 예정" / "semi-design-wiki 스킬로 ingest" 문구 검색**

```bash
grep -rn "semi-design-wiki\|wiki ingest\|wiki-lint\|wiki-sync\|promotion" .claude/skills/semi-design-learning/
```

- [ ] **Step 3: 해당 문구를 graphify-aware로 교체**

예시 (실제 wording은 스킬 파일에 맞게 조정):
- `"Phase 1b에 semi-design-wiki 스킬로 ingest"` → `"Phase 0 Q&A는 wiki/raw/sessions/에 계속 저장한다. graphify가 자동 인덱싱해 build/graph/graph.json에 반영한다."`
- `"promotion_policy 기반 승격"` → `"graphify UI에서 AMBIGUOUS → INFERRED/EXTRACTED 수동 이동"`

트리거("학습 재개", "마인드맵", "Phase 0")는 건드리지 않는다.

- [ ] **Step 4: 스킬 설명 frontmatter (description)에 graphify 반영**

스킬 파일 상단 frontmatter의 `description` 필드에 "graphify 기반 지식 인덱스와 연동"류 문구 보강.

- [ ] **Step 5: 커밋**

```bash
git add .claude/skills/semi-design-learning/
git commit -m "chore(skills): retarget semi-design-learning to graphify"
```

---

### Task 18: `wiki/program/*.md` + `wiki/index.md` 삭제

**Files:**
- Delete: `wiki/program/program.md`, `scoring.md`, `promotion_policy.md`
- Delete: `wiki/index.md`

- [ ] **Step 1: spec §7에 내용이 실제로 흡수됐는지 확인 (S2 Task 7의 결과)**

```bash
grep -n "weekly cadence\|sub-plan\|promotion" docs/superpowers/specs/2026-04-19-integrated-research-program-design.md | head
```

Expected: §7에서 해당 개념이 보여야 한다. 누락됐으면 S2 Task 7로 돌아가 먼저 흡수.

- [ ] **Step 2: 파일 삭제**

```bash
rm wiki/program/program.md wiki/program/scoring.md wiki/program/promotion_policy.md
rmdir wiki/program/ 2>/dev/null || true
rm wiki/index.md
```

- [ ] **Step 3: 남은 wiki/raw/** 확인**

```bash
ls wiki/
ls wiki/raw/
```

Expected: `wiki/raw/` 및 하위 하위 디렉토리들 (papers, sessions, benchmarks, blogs, docs, repos)만 남음.

- [ ] **Step 4: 커밋**

```bash
git add -A wiki/
git commit -m "docs(wiki): remove index.md and program/* (absorbed into spec §7)"
```

---

### Task 19: auto memory 갱신 (선택)

**Files:**
- Modify: `/Users/dohyunjung/.claude/projects/-Users-dohyunjung-Workspace-roboco-io-research-semiconductor-design/memory/project_core_intent.md` (존재 시)

- [ ] **Step 1: 메모리 파일에서 Karpathy Wiki 언급 검색**

```bash
grep -l "Karpathy Wiki\|LLM Wiki" /Users/dohyunjung/.claude/projects/-Users-dohyunjung-Workspace-roboco-io-research-semiconductor-design/memory/*.md 2>/dev/null
```

- [ ] **Step 2: 발견된 파일에서 문구 갱신**

"Karpathy Wiki 패턴" → "graphify 기반 그래프 지식 인덱스". 다른 핵심 의도는 유지.

- [ ] **Step 3: 메모리는 git 관리 밖이므로 커밋 없음. 수정만 저장.**

---

### Task 20: 최종 전체 게이트 & README 갱신

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 전체 테스트·lint 재확인**

```bash
make test
make lint
make graph-lint
```

모두 pass여야 S4 종료.

- [ ] **Step 2: README 프로젝트 설명 한 문장 갱신 (있다면)**

```bash
grep -n "wiki\|frontmatter" README.md
```

해당 라인에서 "LLM Wiki" → "graphify 기반 graph index" 로 교체. 1문장 이내로 간결히.

- [ ] **Step 3: 종료 마커 커밋**

```bash
git add README.md
git commit -m "docs(readme): note graphify as knowledge index"
git commit --allow-empty -m "chore(s4): graphify adoption complete"
```

- [ ] **Step 4: 최종 커밋 로그 확인**

```bash
git log --oneline main ^$(git merge-base main main~30) | head -30
```

S1~S4의 모든 커밋이 main에 반영됐는지 육안 확인.

---

## Rollback Matrix

| 실패 지점 | 조치 |
|-----------|------|
| S1 (Task 4) — M1~M3 중 2개 이상 미달 | `docs/superpowers/specs/2026-04-22-graphify-evaluation.md`의 status를 `failed`로, S2 이후 중단. 사용자에게 접근안 C(spec-first) 또는 채택 철회 재질의. |
| S2 (Task 8) — Codex 3회 연속 fail | spec v2 revert: `git revert` Task 5~7 커밋. S3 진입 금지. |
| S3 (Task 14) — 게이트 실패 | `git revert` Task 13 커밋. `src/semi_design_wiki/` 및 wiki 테스트 복구. graphify 의존성은 유지. |
| S4 (Task 20) — 스킬/CLAUDE.md 문제 | 해당 Task (15~17) 커밋만 개별 revert. 코드(S3)는 유지. |

## Self-Review Notes

- **Spec coverage**: S1의 M2 K1 개념 20개는 Task 2에서 사용자 입력으로 확정 (blocking). M3 inter-trench 수식은 평가 리포트에 명시. §3 L2 인터페이스 재정의는 Task 5에서 in-place 반영. §5.3 최소 수정은 Task 6 Step 3에서 구체적 문구 지정. §7 운영 규칙 흡수는 Task 7. graph integrity check은 Task 9~10.
- **Placeholder scan**: Task 15 Step 2~6의 CLAUDE.md 문구는 모두 구체적으로 제시됨. Task 17의 스킬 wording은 "실제 wording은 스킬 파일에 맞게 조정" 여지를 남겼으나 검색·교체 대상 문구를 명시하고 예시도 포함 — 완결.
- **Type consistency**: `check_graph_integrity(graph_path, ambiguous_threshold)` 시그니처는 Task 9 테스트와 Task 10 구현·CLI에서 일관. `tier` 필드명은 graphify 실제 스키마 확인이 Task 12 Step 2 후속 조치(시그니처 자체는 테스트/구현/CLI 간 일관).

---

**Last update:** 2026-04-22 by Claude Opus 4.7
