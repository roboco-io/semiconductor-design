---
name: semi-design-learning
description: Phase 0 learning tracker for semiconductor-design project (graphify-aware). Activates when user wants to resume learning sessions, check progress on the knowledge mindmap (A-K branches), or inspect what the graphify knowledge graph has captured from accumulated Q&A. Triggers on mentions of "Phase 0", "학습 재개", "마인드맵", "sub-topic 진행", or when the user asks what's left to learn.
---

# semi-design-learning

Phase 0 커리큘럼의 학습 진행을 추적하고 재개를 돕는 스킬. 2026-04-22 graphify 전환 이후, 학습 세션 결과는 raw 파일로만 유지하고 graphify가 자동 인덱싱한다.

## 진행 상황 확인

1. `docs/learning/phase-0-curriculum.md`의 체크리스트를 읽는다.
2. `wiki/raw/sessions/phase-0-*.md` 파일 목록을 본다.
3. 아직 체크되지 않은 첫 sub-topic을 다음 학습 대상으로 제안한다.
4. (선택) `uv run graphify query "phase 0 <topic>"` 로 그래프에 이미 연결된 개념을 조회해 재학습 여부 판단.

## 새 학습 세션 시작

1. 마인드맵 순서 기준 다음 sub-topic 선택
2. `wiki/raw/sessions/phase-0-<code>-<slug>.md` 파일 생성 (템플릿은 `references/session-template.md`)
3. 사용자와 Q&A 진행 — 스타일은 **assistant-led**: 제가 먼저 5-10줄 설명, 사용자가 확인 질문
4. 세션 종료 시 curriculum 체크리스트 업데이트 + 세션 파일 커밋

## graphify 인덱싱

v1의 "wiki 컴파일" 단계는 graphify로 대체됨.

- 세션 파일은 `wiki/raw/sessions/`에 저장되면 graphify의 seed corpus가 된다.
- 단일 세션 추가 후 빠른 AST-only 업데이트: `make graph-update`
- 3-4개 세션 누적 시 full rebuild: Codex 세션에서 `/graphify .` 호출 (Part B 의미 추출까지 실행)
- rebuild 결과는 `graphify-out/{graph.json, GRAPH_REPORT.md, graph.html}`에 반영. `make graph-lint`로 orphan=0 / AMBIGUOUS≤0.3 검증.
- v1의 typed-frontmatter 필드 (`confidence` · `contradiction` · `last_verified`)는 폐기. 증거 강도는 graphify tier(EXTRACTED/INFERRED/AMBIGUOUS)가 전담. AMBIGUOUS 노드는 overview spec §7.3 triage workflow로 처리.

## 커밋 컨벤션

- 세션 파일 추가: `docs(phase-0): Q&A session for <code> <topic>`
- 체크리스트 업데이트: `docs(phase-0): mark <code> complete`
- graphify 인덱스 갱신 후 (Option A+ commit policy): `docs(graph): /graphify update after phase-0 <code>` + `graphify-out/graph.json` · `GRAPH_REPORT.md` · `graph.html` 함께 커밋 (cache · .graphify_*는 gitignore)

## 참고

- 마인드맵: `docs/learning/phase-0-curriculum.md`
- 세션 템플릿: `references/session-template.md`
- graphify 계약: overview spec `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3.2 v2
- AMBIGUOUS triage: 동 spec §7.3
