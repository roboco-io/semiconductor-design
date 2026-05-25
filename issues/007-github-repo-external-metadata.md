---
id: 007
title: GitHub repo 외부 metadata + milestone tagging
status: open
type: operations
related_spec: README.md
layer: meta
iteration: G0-continuous
blocks: []
---

# Issue 007 — GitHub repo 외부 metadata + milestone tagging

## 배경

README Highlights 섹션 추가 ([commit `2d7f697`](https://github.com/roboco-io/semiconductor-design/commit/2d7f697))로 *코드 안*의 자랑은 완료. 그러나 외부 *repo 메타데이터* (GitHub Description / Topics / Releases) 미정합 시 discoverability 손실 — README가 아무리 잘 작성돼도 검색·발견 substrate 부재.

Issue 006 (publishing artifacts)와 함께 *external visibility substrate* 형성. 본 issue는 *운영 단순 작업* 위주라 소요 짧고 ROI 높음.

## 1. Public/Private 상태 확인 + License

### 액션
- [ ] `gh repo view roboco-io/semiconductor-design --json visibility` 확인
- [ ] private인 경우 → public 전환 시 expose 영향 검토:
  - INTENT.md "고객의 말" anchor의 자전적 표현 *공개 적합성*
  - `wiki/raw/papers/k1-*/k2-*` raw notes의 외부 source 인용 권한 (대부분 OK — 모두 공개 paper/blog)
  - `docs/learning/phase-0-curriculum.md` 학습 노트 공개 적합성
- [ ] LICENSE 파일 부재 여부 확인 — 후보: MIT / Apache 2.0 (오픈소스 EDA 도구와 호환)

### 결정 기준
- 본 repo의 모든 내용이 외부 공개 *적합*한가
- License 선택: 본 프로젝트는 *논문 + 오픈소스 reference*가 deliverable이므로 *상용 활용 허용*하는 라이선스 권장 (Apache 2.0 — patent grant 포함, Chipyard와 정합)

## 2. GitHub Description + Topics 갱신

### Description (현재 미설정 추정)
**후보** (140자 이내):
> AI-agent research for open-source EDA + DL accelerator design. Single-operator multi-agent vibe-coding + AutoResearch on LibreLane/OpenROAD/Yosys + sky130A.

### Topics 후보 (각 tag = GitHub Topics search hit)
**기술 stack tags**:
- `ai-agents`, `open-source-eda`, `chip-design`, `risc-v`
- `librelane`, `openroad`, `yosys`, `sky130`, `gemmini`, `mlperf-tiny`

**패러다임 tags**:
- `intent-engineering`, `vibe-coding`, `autoresearch`, `karpathy-llm-wiki`
- `claude-code`, `multi-agent`, `evaluator-separation`

**언어/지역 tags**:
- `korean-tech`, `korean-ai-research`

### 액션
- [ ] `gh repo edit --description "..."`
- [ ] `gh repo edit --add-topic ai-agents --add-topic open-source-eda ...` (모든 topic 추가)
- [ ] (optional) repo banner image — `docs/showcase/banner.png` 후보

## 3. Milestone tag 부여 + Release

### Milestone tag 후보
- **`v0.1-six-week-showcase`** (commit `2d7f697` 또는 가장 최근) — 6주 운영 결과 결정화 시점, README Highlights 활성
- `v0.0-g0-bootstrap-complete` (commit `bfe982f` 또는 G0 완료 시점 — retro-tag, optional)
- `g1-smoke-pre` 기존 freeze tag 유지 (G1 진입 marker)

### 액션
- [ ] `git tag v0.1-six-week-showcase 2d7f697` (or latest commit)
- [ ] `git push origin v0.1-six-week-showcase`
- [ ] (optional) GitHub Release 생성 — `gh release create v0.1-six-week-showcase` 본 6주 chain commit 요약 첨부

### Release notes 형식 후보
- 12-commit chain narrative (`bfe982f → 2d7f697`)
- 핵심 결정 (5 Operating Invariants + Codex retain cycle + K3 6 axes + Highlights)
- "What's not yet there" 그대로 인용 (정직 boundary)
- 다음 milestone 예고 (`v0.2-g1-first-smoke-pass` — G1 KG-A/B 실 통과 시)

### 결정 기준
- semver vs descriptive — 본 프로젝트는 *실험 프로그램*이라 *milestone descriptive tag*가 적합
- *현재 시점*에 `v0.1` 의미 — code 자체보다 *process maturity milestone*

## 우선순위 (소요 짧음 모두 가능)

| 순위 | 항목 | 소요 | Blocking |
|---|---|---|---|
| 1 | Description + Topics | 5분 | 없음 |
| 2 | Public/private 확인 + license 결정 | 30분 | 없음 (조사 위주) |
| 3 | Milestone tag + Release notes | 30분 | License 확정 후 권장 |

## Blocking

- *Public 전환 결정*이 Issue 006 (publishing artifacts)의 *전제 조건*
- License 확정이 *3rd party adoption* 가능성 결정 (Apache 2.0 권장 시 즉시 차단 해소)
- Release notes의 *narrative 정합성*은 README Highlights와 일관성 필요
