---
id: 006
title: Showcase rollout — audience-targeted publishing artifacts
status: open
type: publishing
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
layer: meta
iteration: G0-continuous
blocks: []
---

# Issue 006 — Showcase rollout (audience-targeted publishing)

## 배경

2026-05-25 README Highlights 섹션 추가 ([commit `2d7f697`](https://github.com/roboco-io/semiconductor-design/commit/2d7f697))로 GitHub stargazer audience 1차 cover 완료. 그러나 user-selected 4 audience 중 3개는 *별도 채널* 필요:

1. **학술 reviewer** (DAC/ICCAD/MLCAD) → position paper draft
2. **AI agent paradigm 관심자** (Karpathy 류) → Twitter 쓰레드 + Hacker News/GitHub Discussions
3. **Korean dev community** (Roboco) → [roboco.io](https://roboco.io) 블로그 글

각 채널은 *서로 다른 evidence subset*과 *서로 다른 framing*을 요구. INTENT.md "고객의 말" anchor의 *재현 가능성* 입증을 위한 외부 visibility 확보.

본 issue는 Issue 007 (GitHub repo metadata)와 함께 *external visibility substrate* 형성.

## 1. 학술 reviewer position paper draft

### Scope
- **Venue 후보**: DAC 2026 invited / ICCAD 2026 / MLCAD 2026
- **형식**: position paper (UCSD ABK ICCAD invited 2025-09 모델)
- **분량**: 4-6 pages
- **위치**: `docs/superpowers/position/2026-XX-position-paper-draft.md`

### 핵심 evidence
- K1+K2+K3 evidence corpus (119 sources)
- 5축 novelty framing (K3 6 axes vs 본 프로젝트)
- spec §3.2 layer contract + §5.3 decision table + §5.4 thresholds (정량 falsifier)
- INTENT.md Learnings 1-5 entries (의도공학 layer evidence)
- Codex retain cycle (evaluator separation 1st operational data point)

### 결정 기준
- (a) 어느 venue가 본 프로젝트 5축 차별화를 evaluate 가능한가
- (b) submission deadline 일정 (DAC 2026 fall vs ICCAD 2026 summer)
- (c) Operator 직접 작성 vs `code-author` agent 위임
- (d) Codex 3-round review 시점 (draft 후 1차 / Operator 검토 후 2차 / 최종 3차)

### 액션 아이템
- [ ] Venue 3개 submission window 비교 표 작성
- [ ] Position paper outline (5 section, 1 page each: motivation / related work / approach / evidence / discussion)
- [ ] K1+K2+K3 evidence 요약 표 (INTENT.md Why 표를 paper 형식으로 변환)
- [ ] 첫 draft 작성
- [ ] Codex 3-round review

## 2. AI agent paradigm Twitter/HN 글

### Scope
- **형식**: Twitter 쓰레드 (10-15 트윗) 또는 Hacker News "Show HN" post
- **분량**: 짧고 강한 hook, evidence link 위주
- **위치**: 작성 후 외부 공개 — 본 repo에는 `docs/showcase/twitter-thread-2026-XX.md`로 archive

### Hook 후보
- "비전문가 1명 + 4 AI agent + 오픈소스 EDA로 6주 만에 sustained chip design research program 구축"
- "Codex(OpenAI)가 Claude 작성 INTENT system을 *수정 없이 retain* — evaluator separation 1st operational cycle (N=1)"
- "Karpathy LLM Wiki 패턴을 칩 설계 연구에 적용 — 72-run 벤치 토큰 −53.6%, 시간 −39.3% 입증"
- "6주 운영에서 5개 Operating Invariant 자동 발견 → 영구 운영 규칙으로 결정화"

### 결정 기준
- (a) 어느 hook이 paradigm audience 핵심을 자극하는가
- (b) Operator authority 강조 vs Codex retain cycle 강조 vs Karpathy 벤치 강조
- (c) 본 Twitter 글이 README/spec/K3 evidence로 funnel하는 link 흐름
- (d) 외부 공유 timing — *현재* vs *G1 첫 smoke 실 run 통과 후*

### 액션 아이템
- [ ] Hook 1-2 선택 + A/B test 후보
- [ ] 쓰레드 draft (10-15 트윗 또는 HN post 1 page)
- [ ] Evidence link funnel 설계 (Twitter → README → K3 raw)
- [ ] 공유 timing 결정

## 3. Korean dev community blog post (Roboco)

### Scope
- **Channel**: [roboco.io](https://roboco.io) 블로그 (이미 [Karpathy LLM Wiki 72-run 벤치 글](https://roboco.io/posts/karpathy-llm-wiki-72-run-benchmark/) 존재)
- **형식**: 한국어 narrative — 6주 사례 연구
- **분량**: 2000-3000 words
- **위치**: `docs/showcase/roboco-blog-2026-XX.md` (publish 후 외부)

### Narrative arc (5-7 section)
1. 시작: "비전문가가 칩 설계 연구를 한다 — 가능한가?"
2. 패러다임: 의도공학 + Operator authority + 4 agent + wiki-first
3. 증거: K3 6 axes + Codex retain cycle + 5 Operating Invariants
4. 운영: 6주 chain (`bfe982f → 2d7f697` 11 commits) narrative
5. 결론: 외부 재현 가능한 모범 — `docs/onboarding.md` 진입로

### 결정 기준
- (a) Roboco blog 기존 글과의 정합 (Karpathy 글의 *후속 사슬*)
- (b) 한국어 톤 (technical vs narrative balance)
- (c) Korean dev community 진입로 명시 (Roboco 사용자 → 본 repo)

### 액션 아이템
- [ ] 기존 Karpathy 블로그 글 톤 분석 (`https://roboco.io/posts/karpathy-llm-wiki-72-run-benchmark/`)
- [ ] Narrative arc 5-7 section 결정
- [ ] 첫 draft (Operator 한국어 직접 작성 권장)
- [ ] Codex 한국어 평가는 어려움 → Claude review 보조

## 우선순위

| 순위 | 항목 | 이유 | 예상 ROI |
|---|---|---|---|
| 1 | **Korean blog post** | Roboco 기존 audience 활용. 현재 evidence로 *즉시 가치*. | 🟢 High |
| 2 | **Twitter/HN 쓰레드** | viral 가능성. G1 첫 smoke 실 run 통과 후 timing 적합. | 🟡 Medium |
| 3 | **학술 position paper** | 시간 가장 큼. submission deadline 따라. | 🟡 Medium (long-term) |

## Blocking

- *전부* G1 첫 smoke 실 run pending 상태 — 통과 후가 *각 글의 강도*가 더 높음
- 단 Korean blog는 *현재 상태로도* 충분 (process novelty + sustained execution evidence)
- Issue 007 (repo metadata) — public 전환 결정이 *본 issue의 전제*. private repo면 외부 공개 자랑 의미 없음
