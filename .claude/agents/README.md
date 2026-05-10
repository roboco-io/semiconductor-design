# Project Agents — single-operator multi-agent

본 프로젝트의 4개 위임 채널 agent. 모두 *Operator의 감독 아래* patch · 보고서 · 리뷰만 *제안*하며, **머지 결정은 Operator**가 한다.

## 분업 매트릭스

| Agent | 채널 | 입력 | 출력 | 다음 단계 |
|---|---|---|---|---|
| [`experiment-designer`](experiment-designer.md) | Researcher | Operator 위임 task + INTENT.md + spec §4-§5.4 + K1/K2 evidence | Experiment Plan (markdown, candidate set + seed + KG 매핑 + freeze items) | Operator 승인 → `experiment-runner` |
| [`experiment-runner`](experiment-runner.md) | Researcher | 승인된 plan + lockfile.yaml | Run Report (`*.rpt` highlights + KG status + negative results + provenance) | Operator 검수 → 다음 iteration |
| [`code-author`](code-author.md) | Developer | Operator 위임 task + CLAUDE.md "Code Conventions" + INTENT.md Not | Patch Proposal (Edit/Write 적용 + ruff + pytest + coverage) | Operator → `eda-code-reviewer` 호출 권장 |
| [`eda-code-reviewer`](eda-code-reviewer.md) | Developer | code-author patch (또는 임의 PR) | Aggregated verdict (1차 EDA 검사 7항 + 2차 plugin agent 5종 verdict) | Operator 머지 결정 |

## INTENT.md 정합이 공통 substrate

4 agent 모두 system prompt에 **INTENT.md Not 정합 검사**를 박아둠. Operator 머지 거절을 *agent 단위에서 1차 차단* — reasoning trace가 깔끔해지고 H3 evidence 품질이 올라감 (의도공학 layer가 agent system prompt의 공통 substrate로 작동).

## 다른 agent와의 관계

- **`pr-review-toolkit:*` plugin** (6 agent) — `eda-code-reviewer`가 2차에서 오케스트레이션. 직접 호출도 가능.
- **`codex:codex-rescue`** — 4 agent 누구든 깊은 root-cause 디버깅이 필요하면 위임. 본 프로젝트 agent들은 *책무 분리* 우선.
- **`semi-design-learning`** skill (Operator 직접 학습 채널) — agent 위임 영역 아님. Operator가 직접 진행.

## 호출 패턴

- 자동 트리거 — frontmatter `description`의 키워드/예시가 매칭되면 자동.
- 명시 호출 — `Agent` tool에서 `subagent_type: experiment-designer` 등.
- 체인 호출 — `eda-code-reviewer`가 내부에서 `Agent` tool로 plugin agent 순차 호출.

## 절대 금지 (4 agent 공통)

- 직접 `git commit` / `git push` (Operator 권한).
- INTENT.md `Not` 섹션 위반을 우회.
- spec §3.2 layer interface signature 변경 (spec 재승인 필요).
- `wiki/raw/` 실데이터 mutation.
- 자기 책무 밖 작업 자체 수행 (다른 agent 위임 명시).
