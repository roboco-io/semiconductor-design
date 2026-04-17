# Issues

로컬 이슈 트래커. GitHub 리포에 push한 이후에는 `gh issue create`로 이전 가능.

| ID | 제목 | 상태 | blocks |
|---|---|---|---|
| [001](001-planner-crossover-algorithm.md) | Planner의 crossover 알고리즘 확정 | open | W4 |
| [002](002-fargate-spot-vs-ondemand-mix.md) | Fargate Spot vs On-Demand 혼합 정책 | open | W3 |
| [003](003-wiki-ingest-automation-trigger.md) | Wiki ingest 자동화 전환 기준 | open | — |
| [004](004-dashboard-framework-decision.md) | 대시보드 프레임워크 최종 확정 | open | W5 |

## 이슈 작성 규칙

각 이슈는 프론트매터(`id, title, status, type, related_spec, iteration, blocks`)
+ 배경 / 옵션 / 결정 기준 / 액션 아이템 구조를 따른다.

해결되면 `status: resolved`로 변경하고 본문 맨 아래에 `## Resolution` 섹션 추가.
