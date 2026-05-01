# Chapter 02 — 지식 기반이 먼저

> **시간**: 2026-04-19 ~ 2026-04-20 (약 2일, 약 12-15h active)
> **AWS 비용**: $0.00
> **핵심 인사이트**: spec을 짓기 전에 외부 자료를 충분히 ingest. *"방향 판단은 그 이후"* — 이 한 줄이 이후 모든 spec의 품질을 결정.

## 맥락

Chapter 01 끝에서 사용자는 이미 한 번 spec을 archive한 경험이 있다. 다시 같은 실수를 피하기 위해 한 가지 원칙을 글로벌 메모리로 등록하기로 했다 — *"지식 기반 우선 원칙"*. 본 chapter는 그 원칙이 어떻게 K1 4축 52 sources의 적재로 발현되었고, 그 결과 *3-round Codex 리뷰를 통과하는 통합 프로그램 spec*이 만들어졌는지를 추적한다.

## 등록된 원칙

```markdown
# ~/.claude/projects/.../memory/feedback_knowledge_first.md

지식 기반 우선 원칙: spec·MVP 결정 전 최신 자료·논문을 wiki에 ingest,
방향 판단은 그 이후.

Why: 4/17 spec이 OpenLane2 → LibreLane rename · Efabless 셧다운 · MLPerf v1.2→v1.3
  등 stale gates 다수로 archive. spec을 먼저 쓴 결과 14일 후 폐기.

How to apply: 새 영역에 들어갈 때 (a) perplexity_research로 핵심 paper survey,
  (b) wiki/raw/papers/<axis>-*.md로 정리, (c) spec 작성, (d) Codex review.
```

이 메모리는 본 프로젝트 11일간 *모든 새 spec*에 적용됐다. 4/22 K2 추가, 4/23 L2 derived spec, 4/26 L3 outline 모두 동일 패턴.

## K1 4축의 정의

사용자는 perplexity_research로 4축 survey를 수행하기로 했다. 4축 선정 기준:

1. **α — LLM-for-HDL** — RTL 생성·검증 자동화 어디까지 됐는가?
2. **β — Agentic EDA** — agent가 EDA flow를 어떻게 운영하는가?
3. **γ — Open-source EDA** — Yosys/OpenROAD/LibreLane이 sky130A 위에서 어디까지 가능한가?
4. **δ — Research Memory** — Karpathy AutoResearch 식 메모리 + reproducibility 인프라.

각 축당 ~13개 source, 합 52개. 각 source는:

```markdown
# wiki/raw/papers/k1-alpha-llm-for-hdl.md

## 1. <paper title>
- **저자**: ...
- **연도**: ...
- **링크**: ...
- **요지**: 2-3 줄
- **본 프로젝트와의 연결**: spec §X 어디에 anchor되는지
```

이 형식이 후일 graphify *EXTRACTED edge*의 직접 source가 된다 (chapter 04).

## K1 적재 결과 — 12 commits

```
2d4ca70 docs(k1): collect 52 sources across 4 axes and publish direction report
8ce8ceb docs(spec): add integrated program overview, archive 2026-04-17 predecessor
de9caba docs: realign README, CLAUDE, issues, wiki/program to integrated program
```

`2d4ca70` (4/20) 단일 commit이 52 sources + direction report 모두 포함. ~50 KB의 markdown. 이 commit이 *결정의 baseline* 역할을 했다.

## Direction report — 4 page summary

```
docs/knowledge-base/2026-04-19-k1-direction-report.md
```

이 문서가 4/19 ~ 4/20 사이 *하루 동안* 4축 survey 결과를 종합해서 본 프로젝트의 방향성을 결정한다. 핵심 발견 5가지 (요약):

1. **ORFS-agent (2025) 존재** — autotuning 단독 MVP 가설은 무효. 더 도전적인 *novelty dimension* 필요.
2. **EvolVE / VerilogCoder / MAGE 패턴** — agent가 RTL을 *작성*하는 단계는 도달. 다만 *reasoning trace*는 약함.
3. **Open-source EDA의 7nm 이하 parity 부재** — sky130A (130nm)에 머무는 게 맞음. 절대 PPA 비교 불가.
4. **Karpathy AutoResearch + Reflexion + Generative Agents 패턴** — *report-grounded executable memory*가 본 프로젝트의 차별점.
5. **Efabless 2025-02 셧다운** — silicon back-end는 본 프로젝트 scope 밖. design + sign-off-grounded reasoning까지가 한계.

## "Novelty 3축" — H1/H2/H3 hypothesis

direction report가 정의한 핵심 가설 (이후 spec §4의 baseline):

| ID | 가설 | Falsifier (publish/kill 판단의 근거) |
|---|---|---|
| **H1** | *report-grounded* agent가 template DSE를 ORFS-agent와 비등하거나 낫게 수행 | 동일 budget에서 H1이 ORFS-agent에 30% 이상 PPA 열세 → kill |
| **H1b** | *non-knob structural patch* (template-breaking) 도출 가능 | 부록 C exclusion list 안의 transform만 도출 → kill |
| **H2** | *reversible patch skill library*가 iteration 간 누적 효과 (compounding) | gen N의 평균 PPA가 gen 0 대비 개선 없음 → reframed |
| **H3** | *reasoning trace*가 evaluator-blind에서 인간 reviewer로 학술 가치 인정 | reviewer Cohen's κ < 0.6 → reframed (publish-as-process novelty) |

이 4-row table이 본 프로젝트의 *전체 evaluation framework*이 됐다. `§5.3 Canonical Decision Table`이라 부르며, 본 repo의 어떤 다른 문서도 자체 publish/kill 기준을 *선언하지 않는다*. Single source of truth.

## Integrated program overview spec — 4/20

```
8ce8ceb docs(spec): add integrated program overview, archive 2026-04-17 predecessor
```

`docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` 작성. 단일 commit으로 ~25 KB spec 생성. 4/17 spec과의 차이:

### 3-layer 구조 도입

```
L1 Process    : SHA-pinned Nix bundle + AWS Fargate Spot + ephemeral 200 GiB
L2 Substrate  : report-grounded memory + reversible-patch skill library
L3 Content    : Open-Ideation Gemmini DSE on MLPerf Tiny v1.3
```

L1 ↔ L2 ↔ L3의 *interface contract*를 §3.2 에 fix:

```python
L1.run(spec_uri) → RunArtifact
L2.skill_library.query(query) → list[Skill]
L2.memory.recall(query, k) → list[L2RecallNode]
L2.lint.check(graph) → LintResult
```

이 4개 함수 시그니처가 *breaking change* 시 overview spec 재승인을 요구한다. 즉 L1/L2/L3 각각의 derived spec이 이 contract를 어기지 못한다.

### 4-plane × 3-layer 구조

| | Local | AWS | Tool | Knowledge |
|---|---|---|---|---|
| **L1** | Python CLI orchestrator | SFN Map → Fargate | Yosys/OpenROAD/LibreLane | (none) |
| **L2** | (none) | (none) | (none) | **report-grounded memory + skill library** |
| **L3** | Open-Ideation agents | (uses L1) | (uses L1's tools) | (uses L2) |

이 구조가 chapter 03 (L1 코드), chapter 04 (graphify L2), chapter 05 (L2 substrate spec), chapter 06 (CDK 6 stacks)의 분할을 결정.

## Codex 3-round 리뷰 — 첫 적용

```
코덱스로 계획 리뷰하고 지적사항을 알려줘.
```

— 4/19 20:24

이 prompt가 본 프로젝트의 *Codex 패턴*을 정립했다.

```
Round 1 (Codex): structural feedback — "§5.3 publish/kill 기준이 §4 H1/H2/H3과
  cross-reference 되지 않음. 두 섹션이 독립적으로 진화하면 충돌 위험."
Round 2 (Claude): §5.3을 single source of truth로 명시 + §4가 §5.3을 reference
Round 3 (Codex): "이제 §13 License Gate가 §5.3과 의존 관계 explicit이어야 함"
Round 4 (Claude): cross-reference 추가 + spec freeze
```

3 rounds = 약 30분 wall clock. 이 패턴은 이후 *모든 derived spec* (L1/L2/L3)에 적용됐다.

`★ Insight ─────────────────────────────────────`
- Codex가 Claude를 *모르고* 리뷰하는 게 핵심. 같은 LLM이 자기 산출물을 자기 점검하면 hallucination feedback loop가 생기지만, 다른 모델은 *다른 가정*에서 본다.
- 3 rounds 정도가 spec이 *converged*된다. 그 이상은 nitpick, 그 이하는 critical issue 미발견.
- 본 프로젝트는 Codex와 Claude가 *각각* superpowers skill을 인지함 — 즉 같은 best practice framework 안에서 다른 의견을 냄. 완전히 다른 framework로 리뷰받으면 noise가 더 큼.
`─────────────────────────────────────────────────`

## 4/20 — README + CLAUDE.md 정렬

```
de9caba docs: realign README, CLAUDE, issues, wiki/program to integrated program
```

새 spec이 단일 source of truth가 된 이상 다른 모든 문서가 그것을 가리키도록 재정렬:

- `README.md` — G0~G4 gate summary 추가, "이전 1a~6 번호는 archived" 주석
- `CLAUDE.md` — Phase 1a/1b/...를 G0/G1/G2/G3/G4로 매핑 + each gate description
- `issues/*.md` — 각 이슈 상단에 "재배치 노트" 섹션 + 새 spec § 참조
- `wiki/program/*.md` — 새 spec의 §7 operating rules로 흡수 (별도 program 문서 폐기)

이 *re-alignment* 작업이 거의 하루 걸렸다. 100+ files touched. 그 가치는 다음 4-5 chapter에서 모든 commit message가 spec § 를 참조할 수 있게 됐다는 것.

## Issue 005: 그래프 갱신 정책

```
aff5ad3 docs(issues): add issue 005 graphify refresh + integrity policy  (4/23)
```

직접 4/23에 작성된 이슈지만, 4/20 시점에 이 정책의 *정신*이 결정됐다 — *"외부 자료가 새로 들어올 때마다 spec이 stale gate를 가질 위험이 있으므로, 자료 적재 → spec 갱신 cadence를 systematize"*. Issue 005가 정식 정책이 되어:

```
- wiki/raw 5+ 파일 신규 → /graphify . full rebuild
- L2 contract 변경 → /graphify . full rebuild
- 신규 Codex review → /graphify . full rebuild
- 정기 cadence: 3주
```

본 정책이 *graphify의 인덱스가 stale하지 않게* 강제한다. chapter 04에서 이 정책의 디테일.

## 결과: 4/20 끝 시점 상태

| 자산 | 상태 |
|---|---|
| Integrated overview spec | 작성 완료, Codex 3-round 통과, freeze |
| 4/17 spec | archived |
| K1 52 sources | wiki/raw/papers/k1-{α,β,γ,δ}-*.md 4개 파일 |
| Direction report | docs/knowledge-base/2026-04-19-k1-direction-report.md |
| §5.3 Canonical Decision Table | publish/reframed/kill의 single source of truth |
| 3-layer × 4-plane 구조 | spec §6에 fix |
| L1/L2/L3 interface contract | spec §3.2에 fix (4개 함수 시그니처) |
| H1/H1b/H2/H3 hypothesis + falsifier | spec §4에 fix |

다음 chapter (03)는 이 spec의 L1 부분을 *derived spec + plan + 실 코드*로 펼쳐낸 4/21 하루를 다룬다 — 약 30 commits로 semi_design_runner 패키지 골격 + ORFS Docker + 첫 CDK stack까지.

## Try It Yourself

본 chapter를 따라하려면:

```bash
# 1. perplexity로 새 도메인 4축 survey
> perplexity_research를 사용해서 [도메인]의 핵심 자료 4축으로 정리해줘
> 각 축당 10-15개 source. 각 source는 wiki/raw/papers/<axis>-*.md로 저장.

# 2. direction report 작성 — Claude에게 위임
> wiki/raw/papers/ 안의 모든 자료를 읽고 docs/knowledge-base/[date]-direction-report.md
> 작성. 5가지 핵심 발견 + 본 프로젝트 영향 + reject할 가설.

# 3. Codex 3-round 리뷰
> codex_rescue subagent로 docs/superpowers/specs/[spec].md 리뷰. 3 round 진행.

# 4. memory 등록 — 다음 spec 작성에서도 같은 원칙 따르도록
> memory/feedback_knowledge_first.md 작성:
> "지식 기반 우선 원칙. spec 작성 전 외부 자료를 wiki에 ingest. Why: ..."
```

### Running cost (chapter 누적)

| Phase | 항목 | 비용 | 누적 |
|---|---|---|---|
| (ch01) | Setup + Phase 0 + first pivot | $0.00 | $0.00 |
| K1 적재 | perplexity_research + 52 sources 정리 (~6h) | $0.00 | $0.00 |
| Direction report | hand-written 분석 (~2h) | $0.00 | $0.00 |
| Spec 작성 + Codex 3-round | overview spec 25 KB | $0.00 | $0.00 |
| Re-alignment | README/CLAUDE/issues 재정렬 | $0.00 | $0.00 |
| **Total ch02** | | **$0.00** | **$0.00** |

### Timeline

- 04-19 04:56 — `/init` (이전 chapter 끝)
- 04-19 ~ 20 (1.5일) — K1 4축 survey + 52 sources 적재
- 04-20 ~ 12:00 — direction report 초안
- 04-20 12:00 ~ 18:00 — overview spec 작성
- 04-20 18:00 ~ 19:30 — Codex 3-round 리뷰
- 04-20 19:30 ~ 23:00 — README/CLAUDE/issues re-alignment

다음 chapter는 *L1 spec → L1 plan → L1 코드 (semi_design_runner Phase A)*가 4/21 하루 만에 30 commits로 완성된 패턴을 다룬다. spec-to-code 변환 속도의 한계를 시험하는 chapter.
