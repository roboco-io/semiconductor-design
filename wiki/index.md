---
title: "Wiki Index"
type: index
status: active
updated: 2026-05-09
note: "이 파일은 ingest/sync 시 자동 갱신될 수 있음. 페이지 본문은 각 *.md 에 작성하고 여기는 라우팅만."
---

# Project Wiki — Semiconductor Design (AutoResearch Program)

본 위키는 [Karpathy LLM Wiki 패턴](https://roboco.io/posts/karpathy-llm-wiki-72-run-benchmark/) 기반으로 컴파일된 **default 컨텍스트 라우팅**입니다. 답변 작성 시 `[[wiki-link]]`로 페이지를 인용하세요. 보조 그래프 쿼리(`graphify-out/`)는 cross-component path 탐색에만 사용합니다.

## 페이지 디렉토리

### Concept (학습·기초 개념)

- [[cmos-fundamentals]] — MOSFET·CMOS·sky130·전력 3성분
- [[digital-logic-gates]] — NAND universal·D-FF·조합 vs 순차
- [[clock-and-timing]] — setup/hold·critical path·skew/jitter (STA 기초)
- [[fsm-and-pipeline]] — FSM·Moore/Mealy·파이프라인·systolic array
- [[eda-flow-report-reading]] — Yosys/OpenROAD/LibreLane 3.0.2/sky130A 4단 리포트 operator-lens 진입점 (2026-05-09 추가)
- [[pdk-file-formats]] — Liberty/LEF/DEF/SDC 4 파일 포맷 + sky130A 디렉토리 + ciel 패키지 매니저 진입점 (2026-05-10 추가)

### Policy (정책·렌즈)

- [[phase-0-eda-operator-lens]] — Phase 0 학습 우선순위 (operator 렌즈, A 브랜치 진입점)

### Synthesis — K1 Direction Evidence (방향 판단 근거)

K1 4축 × 평균 13 source = 52 paper. 각 페이지 frontmatter `related_specs`로 spec 결정과 직접 연결.

- [[k1-alpha-llm-for-hdl-evidence]] — RTL 생성 SOTA + CVDP-agentic 34% novelty seam
- [[k1-beta-agentic-eda-evidence]] — ORFS-agent reframe trigger + 3 novelty windows
- [[k1-gamma-opensource-eda-evidence]] — Yosys/LibreLane/sky130A stack + Efabless·rename triggers
- [[k1-delta-research-memory-evidence]] — Karpathy + Voyager × EDA artifacts (본 wiki-first 결정의 메타 근거)

K1 4축을 묶는 종합 보고서는 `docs/knowledge-base/2026-04-19-k1-direction-report.md` 참조 (중복 회피).

### Synthesis — K2 Spec Backing Evidence (G1/G2/G3 spec 결정 근거)

K2 4축 × 평균 15 source = 61 paper. K1이 *forward synthesis*라면 K2는 spec 결정의 *backward evidence binding*. 각 페이지가 spec deferred items / kill gates / governance rule을 직접 backing.

- [[k2-epsilon-graph-quality-judge-evidence]] — L2 substrate 4 deferred items (per-node freshness, confidence_score 산식, ranking calibration, recall semantics) + §5.3 H3 falsifier (Cohen's κ ≥ 0.6)
- [[k2-zeta-l1-runtime-evidence]] — L1 KG-A~KG-E backing + §6.2 lockfile 4 수정 (LibreLane 3.0.2, ephemeral 200 GiB, Distributed Map 확장, SHA-pin 강제)
- [[k2-eta-patch-mutation-evidence]] — L2.skill_library = "Voyager × SEVerA × RSR" 교집합 + H1b non-knob structural patch 정량화 (SISA array-partitioning 첫 entry)
- [[k2-theta-benchmark-license-evidence]] — MLPerf Tiny v1.3 streaming Marvin + §13 License Gate (NVDLA 분리, BSD3+Apache2 clean) + Iter 3+ shuttle mesh + provenance.yaml self-defined 스키마

## 라우팅 규칙

1. **의도 정합**: 모든 작업·답변·결정 전에 [`INTENT.md`](../INTENT.md) Why · What · Not 정합 점검 (status: clarified, 2026-05-10).
2. **위키 우선**: `index.md`에서 관련 페이지 진입 → `[[link]]` 2-hop 확장.
3. **Spec/Plan**: program-level 결정은 `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` (단일 진실원천).
4. **코드 직접 read/grep**: 구현 검증.
5. **graphify 보조 쿼리**: cross-component path가 필요할 때 `uv run graphify query "..."` / `make graph-serve` MCP. 카탈로그는 `graphify-out/GRAPH_REPORT.md`.

## Raw 소스

`wiki/raw/` 는 불변(read-only). 신규 노트는 거기 드롭 후 ingest로 컴파일.

| 폴더 | 내용 | 미컴파일 분량 |
|------|------|---------------|
| `raw/sessions/` | Phase-0 학습 Q&A | a1~a4 (4개, 2026-05-09 컴파일 완료) |
| `raw/papers/` | K1+K2 논문 노트 | **K1 α/β/γ/δ (4개) — 2026-05-09 컴파일 완료** + **K2 ε/ζ/η/θ (4개) — 2026-05-10 컴파일 완료** (총 8 evidence 페이지) |
| `raw/docs/` | 공식 문서·종합 가이드 | `c-eda-flow-operator-guide` (2026-05-09) · `librelane-3-architecture-official` (2026-05-09) · `f-pdk-file-formats-operator-guide` (2026-05-10) · `sky130-libraries-naming-official` (2026-05-10) |
| `raw/repos/` | GitHub repo·tool 발견 | `librelane-summary-tool` (2026-05-09) · `open-pdks-installer-and-ciel` (2026-05-10) |
| `raw/blogs/`, `raw/benchmarks/` | (현재 비어있음) | — |

## 변경 이력

[[log]] — ingest 이력 표.

## Pending Compile

| 영역 | 우선순위 | 비고 |
|------|---------|------|
| Si2 Liberty Format full spec | ↑ | `cell_footprint`, `pin direction` enum 등 paywall 가능 |
| Cadence LEF/DEF 8 Reference | ↑ | TYPE/DIRECTION/CLASS/USE enum 전체 |
| OpenSTA 명령 reference | ↑ | `report_checks` flag, exception path, false_path, multicycle |
| KG-E DDB write amp evidence | ↑ | K2-ζ에서 미커버한 G1 kill gate. 별도 raw 또는 perplexity round |
| B branch (HDL Verilog/Chisel) | ↑ | synthesizable subset, 안티패턴, agent-generated RTL 검수 |
| SDC TCL extension 전체 명령 | ~ | `set_max_fanout`, `set_load`, `set_drive`, `set_clock_groups` 등 |
| LibreLane custom Step 작성법 | ~ | 5 strict 원칙의 실제 enforcement 코드, plugin 시스템 |
