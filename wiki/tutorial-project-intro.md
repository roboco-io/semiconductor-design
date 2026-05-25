---
title: "Tutorial — Project Intro for External Developers"
type: policy
tags: [tutorial, entry-point, software-developer, vibe-coding, external-audience]
status: active
confidence: high
created: 2026-05-25
updated: 2026-05-25
sources:
  - docs/tutorial/PROJECT_TUTORIAL.md
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
  - INTENT.md
---

# Tutorial — 외부 개발자 진입로 정책 페이지

> **본 페이지의 역할**: 외부 소프트웨어 개발자(칩 설계 비전문가)가 본 프로젝트에 진입할 때 *어디서 시작할지*를 결정하는 routing 정책 + chapter별 wiki 교차참조. 본 페이지는 *synthesis pointer* — 본문 자체는 짧고, canonical tutorial 문서와 기존 wiki 페이지로 위임한다.
>
> **Canonical doc**: `docs/tutorial/PROJECT_TUTORIAL.md` (408줄, 23 KB, 30분 분량 6 chapter + outro). 본 wiki 페이지는 그 압축 routing 표.

## 의도 (Why this page exists)

INTENT.md "고객의 말" anchor:

> 비전문가인 내가 다중 에이전트를 감독해 칩 설계 연구를 수행하면서 동시에 학습할 수 있었다 — 이 패러다임 자체가 새 모범.

이 anchor가 *재현 가능*하려면 외부 비전문가가 본 프로젝트를 30분 안에 이해할 수 있는 진입로가 필요. canonical tutorial이 그 진입로이고, 본 wiki 페이지는 *wiki-first hybrid 라우팅* (CLAUDE.md L13)이 그 진입로를 graph 일부로 정합 인덱싱한다.

## 진입 분기 (which doc do you start with?)

| 본인 역할 | 시작 문서 | 본 wiki 페이지 활용 |
|---|---|---|
| **외부 개발자** (칩 설계 비전문가) | `docs/tutorial/PROJECT_TUTORIAL.md` | 본 페이지로 chapter별 wiki backlink 확인 후 detail dive |
| **Operator** (신규 참여자) | `docs/onboarding.md` | 본 페이지 skip 가능 — 외부 공유용 |
| **프로젝트 *역사* 관심자** | `docs/vibe-coding-tutorial/` | 본 페이지 skip 가능 — 시간 흐름 case study가 별도 |
| **3-layer deep dive** | `~/.claude/plans/intent-md-l1-l2-l3-sorted-wozniak.md` (operator local) | 본 페이지 chapter 4-5 wiki backlink부터 진입 |

## 6 Chapter Map + Wiki Cross-Reference

| Chapter | 주제 | 핵심 비유 | 관련 wiki 페이지 (2-hop 확장 시드) |
|---|---|---|---|
| **1** 왜 이 프로젝트가 흥미로운가 | 칩 설계 진입 장벽 + vibe-coding 답 | GitHub Copilot 다중 agent 버전 | `k1-beta-agentic-eda-evidence` (ORFS-agent 비교축) |
| **2** 칩 설계 10분 입문 (비유 사전) | RTL/synth/PnR/sign-off 용어 매핑 | Synthesis≈컴파일 / DRC≈Lint / STA≈profiler | `eda-flow-report-reading` (`.rpt` 읽기), `pdk-file-formats` (`.lib`/`.lef`/`.def`/`.sdc`), `fsm-and-pipeline` (회로 시간 모델), `cmos-fundamentals` (기본), `digital-logic-gates` |
| **3** 왜 오픈소스 EDA + AI Agent | parameter sweep vs structural patch | Copilot 함수 본문 vs 모듈 재설계 | `k1-gamma-opensource-eda-evidence` (오픈소스 스택), `k1-alpha-llm-for-hdl-evidence` (LLM-for-HDL state), `k2-eta-patch-mutation-evidence` (H1b structural patch 첫 entry) |
| **4** 프로젝트 구조 한 번에 | 3-layer + 4 agent + wiki-first | 인프라/메모리/실험 + PM/QA/Junior/Reviewer + RAG 전처리 | `k2-zeta-l1-runtime-evidence` (L1 substrate KG-A~D + lockfile), `k2-epsilon-graph-quality-judge-evidence` (L2 substrate 4 deferred items + H3 falsifier), `phase-0-eda-operator-lens` (Branch A 진입점) |
| **5** `make run` 한 줄이 일으키는 일 | 5 stage + Object Lock + KG 판정 | Helm chart 치환 → GitHub Actions checks pass | `k2-zeta-l1-runtime-evidence` (KG-A~D 실행 backing), `eda-flow-report-reading` (artifact 해석) |
| **6** 평가·결정·다음 단계 | H1×H3 매트릭스 + R0 override | A/B 통계 유의성 × qualitative review | `k2-theta-benchmark-license-evidence` (License Gate §13 + MLPerf v1.3 + provenance.yaml), `k1-delta-research-memory-evidence` (L2 memory 효과 측정) |

## 핵심 비유 사전 (concise 인용)

상세는 chapter 2 본문 참조. 본 표는 cross-grep 용이성 위해 wiki 페이지로 별도 보존:

| 칩 설계 용어 | 소프트웨어 비유 | 본 프로젝트 사용 도구 |
|---|---|---|
| RTL | 고수준 소스 (`.v`/`.sv` = `.py`/`.go`) | Chisel(Chipyard), Verilog |
| Synthesis | 컴파일 (소스 → 게이트 IR) | **Yosys** (`yosys-0.64`) |
| Place-and-Route (PnR) | 링커 + 메모리 레이아웃 | **OpenROAD** (LibreLane wrapper) |
| PDK | 타겟 아키텍처 (x86 vs ARM) | **sky130A** + 옵션 gf180mcuD |
| DRC | Lint | `magic`, `klayout` |
| LVS | 통합 테스트 (논리/물리 일치) | `netgen` |
| STA | 정적 성능 분석 | **OpenSTA** |
| Sign-off clean | CI green (모든 check 통과) | DRC=0 + LVS pass + STA slack ≥ 0 |

## Karpathy 원칙 정합

본 페이지는 Karpathy LLM Wiki 패턴(wiki-first hybrid, CLAUDE.md L13)의 *compile, not search* 원칙을 따른다:
- canonical tutorial(`docs/tutorial/PROJECT_TUTORIAL.md`)이 *원본*
- 본 wiki 페이지가 *컴파일된 routing 인덱스*
- 외부 개발자는 본 페이지로 *어디로 갈지* 결정 후, canonical doc 또는 cross-linked wiki 페이지로 분기

graphify 보조 path-query(`uv run graphify query "tutorial"`)는 본 페이지가 *상위 결과*로 등장하도록 설계됨 — frontmatter sources/related_specs로 INTENT.md + overview spec과 명시 연결.

## 본 페이지의 한계 + 후속

- **자체 정보 없음**: 본 페이지는 routing/cross-link만. 학습 내용 자체는 canonical doc + cross-linked wiki에 위임.
- **외부 공유용 단일 진입점**: blog post / repo README 외부 링크 시 canonical doc URL 직접 인용 권장. 본 wiki 페이지는 *프로젝트 내부 navigation* 용.
- **2-hop 확장 한계**: 본 페이지의 양방향 wiki 링크만 따라가면 ~15 wiki 페이지 도달. spec 원문까지 가려면 각 evidence 페이지의 `related_specs` frontmatter 추가 확장 필요.

## See Also

- `docs/tutorial/PROJECT_TUTORIAL.md` — **canonical 30분 튜토리얼** (본 페이지의 원본)
- `docs/vibe-coding-tutorial/` — 프로젝트 *역사* (chapter별, 시간 흐름)
- `docs/onboarding.md` — Operator 신규 참여 가이드
- `docs/glossary.md` — 용어집 (한국어 정의)
- `INTENT.md` — Why/What/Not/Learnings (single source of truth)
- `CLAUDE.md` — 운영 규칙 + 아키텍처 요약 + wiki-first 정책
