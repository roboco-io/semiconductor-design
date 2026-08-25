# Issue 013 — 연구 가설 수립 스킬 선정

> status: decided (2026-08-25 — meta-research 채택·vendored 설치) · created: 2026-08-25
> 목적: INTENT의 가설을 판정 가능한 형태(H1/H2, 사전 고정 판정 기준, 반증 조건)로
> 정식화할 때 쓸 도구 선정. 근거: exa grounded 조사 (citation 13건, hypothesis-skill-research).

## 결론

로컬에는 없음(grep 확인). 외부 생태계에는 다수 존재 — 본 프로젝트 맥락 최적합 2개:

### 1순위 후보

| 이름 | 핵심 기능 | 적합 이유 |
|---|---|---|
| **AmberLJC/meta-research** | 6단계 가설 주도 연구 루프: YAML 가설 트리 → Judgment Gate(novel/feasible/falsifiable) → **locked analysis plan(사전 고정 분석 계획)** → 반증 지향 실험 → 탐색/확증 분리 | "사전 고정 판정·반증 조건" 요구와 가장 직결. 도메인 중립 |
| **scdenney/open-science-skills** (`hypothesis-building` + `pre-registration-writing`) | falsifiability·반사실·3-level 가설 명세 + 사전등록(PAP) 문서 | pre-registration = 본 프로젝트 "사전 고정 판정" 원칙과 정확히 대응. 도메인 중립 |

### 기타 발견 (요약)

- **K-Dense `hypothesis-generation`**: 경쟁 가설 3-5개 + falsifiability 품질 기준 — 생명과학(PubMed) 지향
- **lhqezio/MegaResearcher**: hypothesis-smith → red-team 반증 공격 → eval-designer 사전 등록 스웜 — "생성≠심사" 원칙과 구조 유사 (superpowers 하드 의존)
- **Anthropic 공식 `scientific-problem-selection`** (knowledge-work-plugins): 문제 선택·성공 지표 사전 정의 중심 — 가설 정식화 자체는 부차
- panjose/Co-Scientist, archora-skills, euanai/novum, HypoGeniC, open-coscientist 등 — 토너먼트/자동화 특화
- 공통 패턴: 다수 가설 생성 → 독립 심사(red-team) → 랭킹 → 반증 기준 사전 등록

### 자체 제작 시 참조 설계

가설 트리 YAML(meta-research) · 판정 루브릭(Judgment Gate) · 사전등록 문서 구조(PAP).

## Citation (13건)

1. https://github.com/AmberLJC/meta-research
2. https://github.com/K-Dense-AI/claude-scientific-skills/blob/main/skills/hypothesis-generation/SKILL.md
3. https://claudemarketplaces.com/skills/k-dense-ai/scientific-agent-skills/hypothesis-generation
4. https://github.com/scdenney/open-science-skills
5. https://github.com/panjose/Co-Scientist
6. https://github.com/richard-kim-79/archora-skills
7. https://github.com/lhqezio/megaresearcher
8. https://github.com/euanai/novum
9. https://github.com/anthropics/knowledge-work-plugins/blob/HEAD/bio-research/skills/scientific-problem-selection/SKILL.md
10. https://claude.com/resources/tutorials/how-to-use-the-scientific-problem-selection-skill-with-claude
11. https://github.com/ChicagoHAI/hypothesis-generation
12. https://github.com/jataware/open-coscientist
13. https://www.anthropic.com/news/claude-science-ai-workbench

## 결정

- [x] 선택 (2026-08-25, Operator가 선정 위임): **meta-research 채택** —
  skill-vetting 에이전트 전문 검증 통과 (실물 = 보고 일치: 6단계 루프·YAML 가설 트리·
  Judgment Gate 5기준·locked analysis plan + "plan 커밋이 results 커밋보다 선행" git 규칙.
  red flag 없음. 유의점: star 11·6개월 무업데이트 — 마크다운 스킬이라 위험 낮음).
  `.claude/skills/meta-research/`에 vendored copy (MIT, upstream 94496f5, VENDORED.md 참조).
- 후속 결합안: judgment-rubric·experiment-protocol 템플릿에 open-science-skills의
  **decision rule 사전 명세 + SESOI 정당화** 패턴 이식 (정량 임계값 기반 판정 보강).
  Heartbeat/Advisor 모드는 미사용 — codex-review-approval 게이트로 대체.
- 사용법: 세션 재시작 후 `/meta-research [주제]` (agent staleness invariant — 이번 세션에서는 미활성).
