# Wiki Ingest Log

| Date | Sources | Pages created/updated | Operator | Note |
|------|---------|------------------------|----------|------|
| 2026-05-09 | `raw/sessions/phase-0-a1..a4` (4개) | `cmos-fundamentals.md`, `digital-logic-gates.md`, `clock-and-timing.md`, `fsm-and-pipeline.md`, `phase-0-eda-operator-lens.md` (5 new) | claude-opus-4.7 + dohyunjung | **wiki-first 전환 1차 ingest** (Phase-0 sessions). Karpathy 72-run benchmark 근거. graphify-out/는 보조 path-query 도구로 유지. |
| 2026-05-09 | `raw/papers/k1-alpha-llm-for-hdl.md`, `raw/papers/k1-beta-agentic-eda.md`, `raw/papers/k1-gamma-opensource-eda.md`, `raw/papers/k1-delta-research-memory.md` (4개) | `k1-alpha-llm-for-hdl-evidence.md`, `k1-beta-agentic-eda-evidence.md`, `k1-gamma-opensource-eda-evidence.md`, `k1-delta-research-memory-evidence.md` (4 new, type=synthesis) | claude-opus-4.7 + dohyunjung | **2차 ingest** (K1 4축 × 평균 13 source = 52 paper). 페이지마다 `related_specs` 명시로 spec 결정의 근거 그래프 형성. 사용자 검증을 위해 1페이지 단위로 보고-진행 사이클. K1 종합 페이지는 `docs/knowledge-base/2026-04-19-k1-direction-report.md` 중복 회피로 스킵. |
