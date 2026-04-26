# L3 Content — Derived Spec (outline + §§1-2 + §§6-7)

**상태**: outline draft. §§3-5는 본 commit에서 stub만 — L1 G1 부분 완료(`.rpt` artifact 실측) 후 후속 이슈에서 본문 채움. §§1-2 + §§6-7은 artifact-orthogonal하므로 본 commit에서 full draft. Codex 3-round review는 §§3-5 본문 합류 후 단일 round에서 통합 수행 (issue #10 nominal scope).

**상위 spec**: [overview spec](2026-04-19-integrated-research-program-design.md) §3.2 v2 contract / §3.3 MVP boundary / §5.3 canonical decision / §7 operating rules / §13 license gate / 부록 C exclusion list.
**자매 spec**: [L2 substrate spec](2026-04-23-L2-substrate-design.md) §3.3 promotion gate / §6.2 evaluator separation / §6.4 L1 sign-off 역할 분리.

---

## 1. 목적 (Why L3 Derived Spec)

L3 Content layer는 overview §3.3 MVP 경계에서 "**gcd/ibex/aes 3개 디자인 대상 Open-Ideation 에이전트, MLPerf Tiny v1.3 KWS + streaming wakeword 평가, ORFS-agent와 대조 실험**"으로 정의된 실험 substrate다. 본 derived spec은 그 substrate의 **에이전트 구성 · evidence 소비 패턴 · search strategy · evaluator gate**를 overview/L2 계약과 충돌 없이 고정한다.

본 spec이 결정해야 할 deferred items (G3 entry 전 해소 필수):

1. L3 agent 8종의 역할·tool manifest·prompt template 인터페이스 (§3, stub).
2. `L2.memory.recall` / `L2.skill_library.query` 호출 패턴과 `confidence` 필드 격리 강제 (§4, stub).
3. Template DSE ↔ Open Ideation 2-tier search의 layer separation과 H1b "non-knob structural" 판정 진입점 (§5, stub).
4. Evaluator separation 강제 — overview §5.3 / L2 §6.2 / §6.4를 L3 layer에서 어떻게 enforce하는가 (§6).
5. Codex 3-round review plan — round별 acceptance criteria (§7).

**비범위 (out of scope — 다른 spec이 결정)**:

- Publish / reframed-publish / kill 기준 (overview §5.3 canonical decision table 단독 결정 — 본 spec은 자체 기준 선언 금지, R5 · L2 spec §3.3 #5 일관 원칙).
- L2 promotion gate / freshness / tier-confidence 매핑 (L2 spec §3, §4 결정).
- L1 `.rpt` 파싱 로직 (`semi_design_runner.metrics.parse_reports` 단일 출처, Codex C1 #8).
- License gate 통과 절차 (overview §13 정의, 본 spec은 §2에서 K2 θ 자료로 enforce 근거만 제시).
- Lockfile · Nix bundle · Fargate workflow (L1 spec 결정).

**Novelty dimension 정렬**: L3는 H1a/H1b/H1c 3개 hypothesis의 측정면이다. 그 중 **H1b "Non-knob structural patch count"** (overview §4.1 / §5.1 / §5.4 / 부록 C)가 L3 agent의 **존재 이유** — Template DSE 단독은 ORFS-agent(2025)에 흡수됨. 본 spec의 §3 / §5는 H1b를 카운트 가능하게 만드는 evidence chain을 설계한다.

## 2. K2 θ 근거 (License Gate + Benchmark v1.3 + Shuttle Path)

원본: `wiki/raw/papers/k2-theta-benchmark-license.md` (14 sources, 2026-04-22). 본 § 은 L3 실행 전제 4축에 대한 K2 θ landscape snapshot을 압축한다.

### 2.1 MLPerf Tiny v1.3 streaming wakeword가 L3 alt-bench 타깃 (K2 θ #1·#2·#3·#4)

- **확정 지표**: 20분 합성 오디오 안 Marvin 50회 검출 + MUSAN noise, FN ≤ 7. 1차 metric은 **continuous duty-cycle + energy** — v1.2 단발 KWS와 단절. Gemmini "계산 강한 행렬곱" 프로파일에서는 idle power / clock-gating 구현이 ranking 차별자.
- **공식 reference**: `mlcommons/tiny_results_v1.3` (2025-09 라운드, 70 submission across Qualcomm · ST · Syntiant) — Gemmini 측 baseline은 이 라운드 power 수치에 정렬.
- **Harness**: `mlcommons/tiny` 저장소의 `benchmark/streaming_wakeword/` 하위. EEMBC EnergyRunner GPIO/UART synchronous protocol — Gemmini wrapper firmware는 이 동기 프로토콜에 맞춰 붙는다.
- **Spec impact**: L1 lockfile `commit_shas.mlcommons_tiny`는 이 v1.3 release (정확 SHA는 G3 entry 전에 픽스, 현재 dry-run lockfile에서는 `null`). 기존 v1.2 KWS 기준 수치는 폐기.

### 2.2 License matrix는 Gemmini BSD-3 + Chipyard Apache-2.0 정렬, NVDLA 격리 (K2 θ #5·#6·#7·#8)

- **Gemmini BSD-3** (`ucb-bar/gemmini/LICENSE`): copyright + disclaimer 보존만으로 파생물 공개·상용 재배포 모두 허용. Endorsement 금지 외 실질 제약 없음. 우리 generated RTL은 BSD-3 상속.
- **Chipyard Apache-2.0** (`ucb-bar/chipyard/LICENSE`): 본체 Apache 2.0 + submodule BSD-3(Gemmini, Rocket-Chip) + CHIPS Alliance 모듈. 파생 배포 시 NOTICE 변경 기재 + 각 submodule LICENSE 보존 필요. README에 "Uses Gemmini (BSD-3) / Chipyard (Apache-2.0)" 라인 못박음.
- **NVDLA Open NVDLA License v1.0**: NVIDIA 자체 작성 커스텀 — BSD/Apache/Prosperity 모두 아님. Royalty-free patent + copyright는 부여되나 "retain all original notices" 조항과 patent grant의 contribution 결속이 BSD-3/Apache-2.0과 clean하게 결합 안 됨. Upstream commit 수년 정지(`github.com/nvdla`). **L3 scope에서 제외** — overview §13 NVDLA-specific 조항 그대로 enforce. 학술 비교군으로도 채택 안 함.
- **Spec impact**: L3 agent의 RTL output은 Gemmini 파생만, NVDLA 재구현 시도 금지. `provenance.yaml`에 BSD-3 / Apache-2.0 attribution 자동 inject (§4 stub에서 schema 확정 예정).

### 2.3 Shuttle path는 ChipFoundry default + wafer.space secondary (K2 θ #9·#10·#11·#12)

- **Efabless 셧다운 (2025-02)** 이후 sky130 default → **ChipFoundry.io** ($14,950/tapeout, CI2605 2026-05-13 / CI2609 2026-09-16). gf180mcu → **wafer.space** (스케줄형, Tiny Tapeout 포팅 중). 130nm 유럽 → **IHP SG13G2** (`TO_*2025` MPW).
- **IHP LICENSE 미명시**는 §13 open question — G3 entry 전 확인 필수. ChipFoundry shuttle 캘린더 tracking은 program 운영 규칙으로 추가 (overview §11 risk 대응).
- **Spec impact**: 본 spec의 L3 evidence chain은 **fabrication-independent** — sign-off `.rpt` artifact까지만 evaluate, 실리콘 비교는 Iter 3+ 별도 결정. Shuttle path는 §13 license gate에 종속, §6 evaluator gate와 무관.

### 2.4 Provenance는 self-defined `provenance.yaml` (K2 θ #13·#14)

- **Hardware SBOM 표준 부재 (2026 시점)** — SLSA(소프트웨어 build provenance) + SPDX(component inventory)는 SW만. CHIPS Alliance / FOSSi 공식 작업 없음.
- **본 프로그램 대안**: `provenance.yaml` self-defined schema = `{tool SHAs, PDK commit, seed, license tags, corpus scope (public/private)}`. EdgeBit Nitro Enclave SLSA L3 attestation 패턴 차용.
- **open_pdks sky130A**: Tim Edwards 유지 PDK installer가 우리 Nix bundle 의존성. SkyWater 자체 PDK는 "experimental preview" + 2026-01 IonQ → SkyWater 인수 발표로 거버넌스 장기 전망 불확실. **sky130A commit hash는 `provenance.yaml`에 고정** — Nix bundle SHA만으로는 PDK level lineage 부족.
- **Process novelty 후보**: hardware SBOM 표준 부재 자체가 **overview §4.3 H3 process-novelty의 evidence sub-strand** — 본 spec이 정의하는 `provenance.yaml` schema의 design rationale을 reasoning trace로 동결하면 H3 falsifier (FM1~FM4) 측정 surface로 연결 가능. 구체 매핑은 §4 stub에서 확정.

**§2 결론**: license gate (§13) + benchmark target (§3.3 MVP) + provenance schema 모두 K2 θ 자료로 정합. NVDLA 격리 · v1.3 streaming · ChipFoundry default 세 결정은 본 spec에서 자체 변경 금지 — overview spec 재승인 필요.

---

## 3. L3 Agent 8종 (STUB — L1 G1 build observation pending)

> **Status**: stub. 본 § 본문은 L1 G1 `gcd-orfs` run의 `.rpt` 실측 후 follow-up issue로 채운다. 이유: 각 agent의 prompt template과 tool manifest는 `Metrics` schema 필드 + `.rpt` artifact 구조에 부분 의존. 추상화 레벨 결정 전 본문 작성은 rework 리스크 (issue #10 본문 명시).

### 3.1 Agent 8종 역할 표 (확정 — 추상화 레벨)

| Agent | 책임 | tool 의존 | upstream 참조 |
|---|---|---|---|
| Spec | run candidate spec 생성 (Pydantic `Spec`) | `L2.memory.recall`, `L2.skill_library.query` | overview §3.2 v2 |
| Architect | RTL 모듈 분할 / interface 결정 | `L2.skill_library.query` | 부록 C exclusion list |
| RTL (L3) | Chisel/Verilog 작성 + `read_verilog` 검증 | Yosys, Verilator (sim 단계만) | overview §3.3 L3 MVP |
| TB (L3) | testbench (cocotb 기반) 생성 | cocotb | L1 spec C3 |
| Verif | functional sim + waveform 검토 | Verilator, cocotb | overview §3.3 L3 |
| Signoff | DRC / LVS / STA 통과 결정 | OpenROAD, LibreLane | L1 sign-off (§6.4 분리) |
| Evaluator | H1a/H1b/H1c rubric 채점 + blinded audit | (no EDA tool) | overview §5.4 |
| Planner | iteration 다음 candidate 선택 (Open Ideation) | `L2.memory.recall` | overview §4.1 H1b |

> **Reader / Synthesizer는 L3가 아닌 L2 소속** (overview §7 gating rule). 본 spec은 8종만 정의하며 Reader/Synthesizer 호출은 `L2.memory.recall` interface 너머의 implementation detail로 캡슐화.

### 3.2 Prompt template + tool manifest interface (TBD)

각 agent의 prompt template 구조와 tool manifest schema는 follow-up issue에서 결정. 후보 설계 axis:

- Prompt template: structural (Spec/Architect/Planner는 freeform NL) vs. structured (RTL/TB/Verif/Signoff는 file path + tool invocation을 JSON으로)
- Tool manifest: per-agent allowlist (LLM이 호출 가능한 MCP server / shell command 화이트리스트)
- Trace 형식: JSONL append-only (overview R4 + §4.3 H3 reasoning-trace 직접 evidence)

**Follow-up**: 별도 GitHub issue로 분리 — "L3 agent 8종 prompt template + tool manifest spec".

## 4. Evidence Consumption — `L2.memory.recall` + `confidence` 격리 (STUB)

> **Status**: stub. 본 § 본문은 L2 spec §5.1 recall query semantics + §5.2 output schema에 따른 L3 측 **소비 패턴**을 후속 이슈에서 채운다. 본 commit에서는 강제 규칙 4개만 anchor.

### 4.1 강제 규칙 4개 (확정 — schema-level)

1. **`confidence` 필드 drop 강제** (L2 spec §3.3 #5 인용): L3 agent (특히 Evaluator)의 input parser는 `L2.memory.recall` output에서 `confidence` · `confidence_score` 필드를 **명시적으로 drop**. overview §5.3 canonical decision input에 `confidence*`가 우회 입력되지 않도록 회귀 방지 assertion test 필수.
2. **`tier ∈ {EXTRACTED, INFERRED}` admissibility gate** (overview §3.2 v2 + §5.3): L3 agent가 evidence로 채택하는 노드는 이 두 tier 중 하나여야 함. AMBIGUOUS 노드는 §7.3 triage 후에만 사용 가능.
3. **`derived_from_hypothesis` 연결 필수**: L3가 생성하는 `wiki/findings/<date>-<slug>.md`는 H1a/H1b/H1c/H2/H3 중 하나와 연결되는 frontmatter 필드 필수 (overview §7.3 promotion gate 진입 조건).
4. **L1 sign-off boolean ↔ L3 evaluator 분리** (L2 spec §6.4): `Spec.lockfile_sha`로 식별된 L1 run의 sign-off 통과 boolean과, L3 Evaluator의 H1/H3 rubric 채점 결과는 **다른 agent instance** · **다른 LLM family** 가 생성. role conflation 시 overview §5.3 R0 위반.

### 4.2 Recall 호출 패턴 (TBD)

각 agent별 typical recall query 템플릿, BFS budget, ranking calibration 활용 패턴은 follow-up issue에서 결정. L2 spec §5.1 / §5.3 (Alternative B `confidence × tier`)이 base.

**Follow-up**: 별도 GitHub issue — "L3 evidence consumption patterns + assertion test 회귀 방지".

## 5. Search Strategy — 2-tier (STUB)

> **Status**: stub. Template DSE / Open Ideation의 layer separation, H1b 판정 진입점, 부록 C exclusion list 검증 자동화는 follow-up issue에서 채움. 본 commit에서는 layer 정의만 anchor.

### 5.1 2-tier 정의 (확정 — overview §3.2 / §4.1)

- **Tier 1 — Template DSE (safe baseline)**: Gemmini systolic array dimension + HBM config parameter sweep. **부록 C exclusion list 항목만 변경**. ORFS-agent(2025) 영역. H1b로 카운트 **불가**.
- **Tier 2 — Open Ideation (novelty primary)**: 부록 C에 없는 RTL 모듈 추가 / 재구성, 새 command/step 정의, upstream에 없는 constraint pattern. **H1b 후보**. sign-off clean × seed×3 + blinded audit N≥2 + "non-knob 판정" 통과 시 H1b 카운트 +1.

### 5.2 Layer separation 강제 (확정 — schema-level)

각 candidate spec의 frontmatter에 `search_tier: "template_dse" | "open_ideation"` 필드 필수. Template DSE candidate가 부록 C에 없는 transform을 시도하면 **L1 sign-off 단계에서 차단** (validate-spec Lambda 또는 Spec agent 측). Open Ideation candidate가 부록 C에 있는 knob만 변경하면 H1b 카운트 **불가** (실험 무효 아님 — Tier 1 fallback으로 재분류).

### 5.3 Open Ideation 진입점 (TBD)

Planner agent가 Open Ideation tier에서 candidate를 어떻게 sample하는지 (greedy / MCTS / LLM-direct), `L2.skill_library.query` 활용 비율, 부록 C exclusion 자동 검증 스크립트 위치 등은 follow-up issue에서 결정.

**Follow-up**: 별도 GitHub issue — "L3 Open Ideation Planner + 부록 C exclusion 자동 검증".

---

## 6. Evaluator Gate — overview §5.3 / L2 §6.2·§6.4 enforcement at L3 layer

본 § 은 overview §5.3 R0 + L2 spec §6.2 + §6.4 세 조건을 **L3 layer에서 어떻게 schema/process로 강제**하는지 명시. 자체 새 기준 도입 금지 — 모두 상위 spec 인용.

### 6.1 H3 evaluator 수 N≥5 across ≥3 model family (L2 spec §6.2 그대로 인용)

- **수**: L3 Evaluator agent는 최소 5 instance. Human primary가 default — L2 spec §6.2 + overview §5.3 "human-reviewed claim".
- **Family 다양성**: LLM 평가자 포함 시 ≥ 3 model family (Anthropic Claude / OpenAI Codex / Google Gemini 권장). 본 spec은 N을 하향하지 않고 family 다양성을 additive로만 적용.
- **Aggregation**: voting 또는 κ-weighted aggregate 중 하나를 H3 iteration 개시 전 freeze (§5.2-1). 혼용 금지.
- **L3 enforcement**: Evaluator agent invocation은 별도 `codex exec` 또는 별도 subprocess로 격리 — `L1.run` orchestrator와 동일 process에서 in-process 호출 금지 (role conflation 위험).

### 6.2 L1 sign-off ≠ L3 evaluator 강제 (L2 spec §6.4 그대로 인용 + L3 추가 강화)

- **L1 sign-off**: `.rpt` artifact가 `make kg-f-all` 통과를 boolean assertion. "주장 타당성 판정 아님" — overview §3.2 contract 그대로.
- **L3 evaluator**: L1 sign-off 통과한 `.rpt`를 input으로 받아 FM1~FM4 rubric으로 채점.
- **L3 추가 강화 (본 spec 신규)**:
  1. Spec agent와 Evaluator agent는 동일 LLM instance에서 실행 금지 — Spec이 자기가 생성한 candidate를 self-evaluate하면 H3 evaluator separation 무효 (R0 위반).
  2. Signoff agent (DRC/LVS/STA 결정)와 Evaluator agent도 동일 instance 금지 — Signoff는 L1 sign-off boolean 생성자, Evaluator는 그 boolean의 소비자 + H1/H3 채점자. 두 역할이 같은 instance면 §6.1 model family 다양성 조건이 무력화됨.
  3. 위 두 분리는 `provenance.yaml`에 agent ID + LLM family/version 필드로 audit-trail 가능해야 함 (overview §13 artifact lineage).

### 6.3 Blinded audit 강제 (overview §5.2 그대로 인용)

- **H1a / H1b 자동 카운트는 무효**: 운영자가 아닌 독립 평가자 N≥2가 blind로 샘플 검수. 일치율 < 80% 시 자동 카운트 무효.
- **L3 enforcement**: blinded audit 결과는 `provenance.yaml`의 `audit_results[]` 필드에 기록. 일치율 < 80% 발생 시 해당 iteration의 H1a/H1b 카운트는 §5.3 decision input에서 drop — assertion test로 회귀 방지.

### 6.4 freeze-before-experiment 강제 (overview §5.2-1 + L2 §6.3 그대로 인용)

- **Freeze 대상**: graphify query duplicate-finding heuristic, H1b novelty patch 분류 규칙, blinded audit rubric, FM1~FM4 정의.
- **Freeze 시점**: H1 / H3 iteration 개시 전 git tag (예: `freeze-iter-N`). 사후 조정 시 해당 iteration 무효.
- **L3 enforcement**: Spec agent가 candidate 생성을 시작하기 전, `git rev-parse freeze-iter-N`이 정상 응답하는지 assertion. 없으면 Spec agent abort. 본 assertion은 `validate-spec` Lambda (cdk/lambdas/validate-spec/) 측에 추가 — implementation은 follow-up issue.

---

## 7. Codex 3-round Review Plan

본 § 은 **§§3-5 본문 합류 후** 단일 Codex 3-round를 수행할 때의 round별 acceptance criteria. 본 outline draft 단계에서는 review 보류.

### 7.1 Round 1 — 구조/일관성 (overview §3.2 v2 + L2 §3.2 호환성)

- **검사 항목**: §3 agent 8종이 overview §7 gating rule 위반 없는가 (Reader/Synthesizer가 L3 agent로 잘못 분류되지 않았는가). §4 evidence consumption이 L2 spec §3.3 #5 `confidence` 격리 rule 준수하는가. §5 search 2-tier가 부록 C exclusion list와 정합인가.
- **Acceptance**: critical violation 0건. minor 권고는 §7.4에서 수용 또는 거부 명시.

### 7.2 Round 2 — H1b novelty dimension 보존 (overview §4.1 / §5.4)

- **검사 항목**: §3 agent 8종 + §5 search strategy 조합이 H1b "non-knob structural patch count" 측정 가능한가 (즉, ORFS-agent 2025 영역으로 회귀하지 않는가). §3.2 prompt template axis가 H1b 후보 패턴을 generate할 수 있는가 (Architect / Planner agent의 self-imposed constraint이 부록 C로 좁혀지지 않는가).
- **Acceptance**: H1b가 §3 / §5 양쪽에서 traceable. ORFS-agent (2025)와의 차별 지점이 §5.1 Tier 1 / Tier 2 layer separation으로 명문화됨.

### 7.3 Round 3 — H3 evaluator/sign-off 분리의 schema-level 강제

- **검사 항목**: §6.2 L3 추가 강화 3개 (Spec≠Evaluator, Signoff≠Evaluator, audit-trail) 가 `provenance.yaml` schema로 enforceable한가. role conflation 사례를 의도적으로 만들었을 때 (예: Spec agent가 자기 candidate evaluate 시도) FM1~FM4 rubric input에서 차단되는가.
- **Acceptance**: §6.2 의 3개 추가 강화가 schema/assertion test로 enforce 가능. role conflation 회귀 방지 test 케이스가 follow-up issue로 fileable.

### 7.4 Acceptance

3 rounds 모두 critical violation 0건이고 권고 수용/거부 결정이 PR description에 명시되면 본 spec을 freeze. minor open question은 follow-up issue로 분리. spec freeze 시 `git tag spec-freeze-l3-content-v1`.

---

## Follow-up Issues (filed alongside this commit)

본 commit은 §§3-5 stub 상태이므로 다음 3개 follow-up issue로 본문 채움 작업을 분할 제출:

1. **L3 agent 8종 prompt template + tool manifest spec** — §3.2 본문 채움. 선행: L1 G1 `gcd-orfs` run의 `.rpt` 실측.
2. **L3 evidence consumption patterns + `confidence` drop assertion test** — §4.2 본문 채움 + 회귀 방지 테스트 작성. 선행: L2 runtime 실구현 (`src/semi_design_runner/l2_runtime.py`).
3. **L3 Open Ideation Planner + 부록 C exclusion 자동 검증 스크립트** — §5.3 본문 채움. 선행: 1·2 완료.

세 이슈 모두 본 spec의 §§3-5 stub과 cross-reference. 본문 합류 후 단일 Codex 3-round (§7) 수행하고 spec freeze.
