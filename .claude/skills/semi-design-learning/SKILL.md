---
name: semi-design-learning
description: Phase 0 learning tracker for semiconductor-design project. Activates when user wants to resume learning sessions, check progress on the knowledge mindmap (A-K branches), or convert accumulated Q&A sessions into wiki pages. Triggers on mentions of "Phase 0", "학습 재개", "마인드맵", "sub-topic 진행", or when the user asks what's left to learn.
---

# semi-design-learning

Phase 0 커리큘럼의 학습 진행을 추적하고 재개를 돕는 스킬.

## 진행 상황 확인

1. `docs/learning/phase-0-curriculum.md`의 체크리스트를 읽는다.
2. `wiki/raw/sessions/phase-0-*.md` 파일 목록을 본다.
3. 아직 체크되지 않은 첫 sub-topic을 다음 학습 대상으로 제안한다.

## 새 학습 세션 시작

1. 마인드맵 순서 기준 다음 sub-topic 선택
2. `wiki/raw/sessions/phase-0-<code>-<slug>.md` 파일 생성 (템플릿은 `references/session-template.md`)
3. 사용자와 Q&A 진행 — 스타일은 **assistant-led**: 제가 먼저 5-10줄 설명, 사용자가 확인 질문
4. 세션 종료 시 curriculum 체크리스트 업데이트 + 세션 파일 커밋

## wiki 컴파일 (ingest)

2-3 브랜치 완료되면 raw/sessions/의 Q&A를 `wiki/` 페이지로 압축한다.
각 sub-topic → 1 페이지. 프론트매터는 `type: learning`, `tags: [phase-0, <branch>]`,
`confidence`는 세션 중 사용자가 "이해됨"을 확인한 수준에 따라 high/medium/low.

## 커밋 컨벤션

- 세션 파일 추가: `docs(phase-0): Q&A session for <code> <topic>`
- 체크리스트 업데이트: `docs(phase-0): mark <code> complete`
- ingest 후 wiki 페이지: `docs(wiki): ingest <code> into wiki/<Page-Name>`

## 참고

- 마인드맵: `docs/learning/phase-0-curriculum.md`
- 세션 템플릿: `references/session-template.md`
