# Issues

로컬 이슈 트래커. GitHub 리포에 push한 이후에는 `gh issue create`로 이전 가능.

| ID | 제목 | 상태 | Layer | Gate | 비고 |
|---|---|---|---|---|---|
| [001](001-planner-crossover-algorithm.md) | Planner의 structural mutation operator 설계 (구 crossover) | open (재정의) | L3 | G3 | parameter crossover → H1b non-knob transform 생성 |
| [002](002-fargate-spot-vs-ondemand-mix.md) | Fargate Spot retry/fallback 정책 | partially-resolved | L1 | G1 | Spot 확정, 재시도 정책만 남음, KG-D 기준 |
| [003](003-wiki-ingest-automation-trigger.md) | Wiki ingest 자동화 + QMD reindex | open (expanded) | L2 | G2 | QMD 도입으로 범위 확장 |
| [004](004-dashboard-framework-decision.md) | Observability 대시보드 scope 재평가 | open (scope 재평가) | L1 or L3 | G1 or G3 | L1 operational vs L3 scientific 선행 질문 |
| [005](005-graphify-refresh-and-integrity-policy.md) | graphify refresh + integrity policy + cross-links 정제 cadence | resolved (2026-04-23) | L2 | G0-continuous | GitHub Issue #4, issue 003 Resolution에서 예고됨 |
| [006](006-showcase-rollout-publishing.md) | Showcase rollout — audience-targeted publishing artifacts | open | meta | G0-continuous | 3 sub-task (학술 position paper / Twitter/HN / Korean blog). README Highlights commit `2d7f697` 후속 |
| [007](007-github-repo-external-metadata.md) | GitHub repo 외부 metadata + milestone tagging | open | meta | G0-continuous | public 전환 / Description+Topics / `v0.1-six-week-showcase` tag. Issue 006 전제 |

## 2026-04-19 재배치

전 이슈가 구 spec(archived `2026-04-17-...design.md`) 기준으로 작성됨. 통합 프로그램 overview spec(`2026-04-19-integrated-research-program-design.md`) §10 재배치 계획에 따라 각 이슈는 L1/L2/L3 파생 spec 범위로 이관. 각 이슈 파일 상단 "재배치 노트" 섹션 참조.

## 이슈 작성 규칙

각 이슈 프론트매터 필드(신규 포함): `id, title, status, type, related_spec, layer (L1/L2/L3), iteration (G0-G4), blocks`.
본문 구조: (재배치 노트가 있으면 최상단) 배경 / 옵션 / 결정 기준 / 액션 아이템.

해결되면 `status: resolved`로 변경하고 본문 맨 아래에 `## Resolution` 섹션 추가.
