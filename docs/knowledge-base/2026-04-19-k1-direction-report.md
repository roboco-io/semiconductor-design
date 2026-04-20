# K1 방향 판단 리포트

| | |
|---|---|
| 작성일 | 2026-04-19 |
| Phase | K1 (개요 수집 → 방향 판단) |
| 전제 | 52 sources collected at `wiki/raw/papers/k1-*.md`, index at `wiki/raw/imports_manifest.yaml` |
| 목적 | "AI + 반도체 설계의 도전적 연구"라는 우산 아래 **구체적 연구 프로그램**을 증거 기반으로 제안 |

## 1. Executive Summary

K1 4개 축(α LLM-for-HDL, β Agentic EDA, γ Open-source EDA, δ Research memory) 52건을 조사한 결과, **단일 축의 단순 반복(또 하나의 Verilog LLM, 또 하나의 BO autotuner)은 모두 포화**다. 그러나 4축이 독립적으로 동일한 방향을 가리키는 **세 개의 교집합 seam**이 존재한다:

1. **Report-grounded agent operation** — `.rpt/.def/STA`를 structured memory로 다루는 에이전트
2. **Template-breaking + executable memory** — Voyager 스킬 라이브러리에 RTL/constraint/sign-off 패치를 축적
3. **Process-as-contribution** — 수치가 아닌 **reasoning trace + 재현성 번들**이 학술 기여물

본 리포트는 이 세 seam을 결합한 **단일 통합 연구 프로그램**을 권고하고, 기존 spec의 즉시 폐기·갱신 항목을 정리한다.

## 2. K1 주요 발견

### 2.1 제약 변경 (기존 spec의 가정을 흔드는 것)

| 발견 | 축 | 기존 spec에 미치는 영향 | 심각도 |
|---|---|---|---|
| **Efabless 셧다운** (2025-02) | γ | Iter 3 "Efabless Shuttle 테이프아웃" 계획 **무효** | 🔴 High |
| **OpenLane2 → LibreLane 2.4** (FOSSi Foundation 이관, 2025-07) | γ | `efabless/openlane2@main` 참조 stale, 스택 결정 재평가 필요 | 🟡 Medium |
| **MLPerf Tiny v1.3** (2025-09, streaming wakeword + duty-cycle/energy) | γ | v1.2 타겟을 v1.3로 상향 | 🟡 Medium |
| **ORFS-agent** (2025) 이미 존재 — BO 대비 +13% QoR, -40% runs | β | "ORFS autotuning MVP 자체"는 더 이상 novelty 아님 | 🔴 High |
| **상용 3사 모두 agentic 포지셔닝** (Cadence/Synopsys/Siemens, DAC 2025) | β | 오픈 차별화의 **window**가 좁혀지고 있음 | 🟡 Medium |

### 2.2 포화된 영역 (novelty 없음)

- 모듈 레벨 combinational/FSM RTL 생성 (VerilogEval-Human, RTLLM v2에서 복수 2025-2026 에이전트가 90%+ pass@1)
- BO/RL 기반 parameter sweep autotuner (ORFS-agent의 +13% ceiling이 BO 계열 집단 상한)
- 또 하나의 Verilog LLM fine-tune (차별화 training signal 없이)

### 2.3 열린 문제 (novelty 가능 지점)

| # | 열린 문제 | 축 | 참고 |
|---|---|---|---|
| 1 | CVDP-hard agentic tasks (RTL reuse, verification) — SOTA가 **34% pass@1** | α | CVDP (NVIDIA 2025) |
| 2 | 에이전트가 `.rpt`를 읽고 **targeted RTL/constraint patch**를 생성하는 능력 | α·β | ORFS-agent가 건드린 시작점 |
| 3 | 디자인 간 **memory transfer** — candidate N이 candidate N-1 실패를 참조 | β·δ | 현재 autotuner 대부분 memoryless |
| 4 | **Template-breaking microarchitecture** 제안 + 물리 realizability 유지 | α·β | EvolVE가 pioneering |
| 5 | **Negative-result first-class indexing** — 실패 재사용 | δ | Reflexion/Voyager는 가지고 있으나 EDA 미적용 |
| 6 | **Contradiction resolution at wiki scale** | δ | 미해결 |
| 7 | **장기 실험 프로그램 메모리** (hours-to-days, multimodal artifacts) | δ | LOCOMO 미커버 |
| 8 | **7nm 절대 PPA 비교는 불가능** (오픈 PDK 130nm 이하 없음) → 비교축을 다른 것으로 | γ | 구조적 제약 |

## 3. Cross-Axis Signals (4축 수렴)

### Seam A — Report-Grounded Agent Operation
**기여 축**: β (ORFS-agent의 METRICS2.1 활용), γ (open-source STA/DRC 리포트 풍부), δ (structured memory 미해결 seam), α (sign-off feedback을 reward로 쓰는 아이디어).  
**구체화**: `.rpt/.def/STA-slack/DRC-violation`을 blob이 아닌 **typed frontmatter가 붙은 구조화 문서**로 저장. lint pass가 "이 PnR 실패는 2주 전 finding X와 동일"을 감지. 에이전트는 parameter 재조정이 아니라 **targeted patch**를 계획.

### Seam B — Executable Memory + Template-Breaking Ideas
**기여 축**: δ (Voyager의 reversible-patch skill library), α (EvolVE의 Idea-Guided Refinement), β (ORFS-agent의 tool-calling 구조).  
**구체화**: 각 skill = "verified Yosys/OpenROAD transform + signed-off report attached". 에이전트가 parameter vector가 아니라 **구조 idea**(예: Gemmini의 dataflow를 WS→OS로, scratchpad 2-port→4-port로)를 제안. 스킬 라이브러리 자체가 논문의 중심 artifact.

### Seam C — Process-as-Contribution
**기여 축**: γ (재현성 번들 부재가 open problem), δ (Karpathy wiki의 compounding knowledge), 프로젝트 의도 (바이브 코딩 + 비전문가 운영자 감독 루프).  
**구체화**: `LibreLane+OpenROAD+Yosys+sky130A` SHA-pinned Nix bundle + AutoResearch harness + **"비전문가가 에이전트를 운영해 도달한 reasoning trace"**가 출판 artifact. scientific contribution이 PPA 수치가 아닌 **process 자체**.

## 4. Candidate Directions

다음 3개 candidate를 고려했고, 서로 **배타적이지 않고 계층적으로 통합 가능**하다.

| # | Candidate | Novelty | Feasibility | Evidence |
|---|---|---|---|---|
| **D1** | Report-grounded AutoResearch Agent System (Seam A 중심) | 높음 — ORFS-agent가 METRICS2.1까지만 쓰고, 실패 재사용·targeted RTL patch는 미개척 | 중간 — wiki engine + QMD 연결 + `.rpt` parser 필요 | α 열린문제 #1·#2, β ORFS-agent의 확장 방향 |
| **D2** | Open-Ideation DL Accelerator DSE (Seam B 중심) | 중-상 — EvolVE의 연장이나 MLPerf Tiny v1.3 streaming + Gemmini template-breaking 조합은 미발표 | 중 — Chipyard/Gemmini 파이프라인 복잡, 8주 이상 소요 확실 | α EvolVE, β ORFS-agent, γ Gemmini/MLPerf Tiny v1.3 |
| **D3** | Process/Reproducibility Framework (Seam C 중심) | 중 — "바이브 코더 비전문가가 운영" 실증은 개인 스타일 의존적이나 **수치로 방어하기 어려운 대신 매우 희소** | 고 — 번들링 자체는 엔지니어링 | γ LibreLane/OpenROAD/sky130, δ Karpathy wiki, 프로젝트 의도 |

**단일 선택의 한계**: D1만으로는 실험 대상이 추상적, D2만으로는 ORFS-agent 대비 차별화 부족, D3만으로는 academic claim이 약함.

## 5. 권고 — 통합 연구 프로그램

**"Report-Grounded Vibe-Coded AutoResearch for Open-Source DL Accelerator Design"** (가칭)

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  Layer 3: CONTENT (D2)                                          │
 │   Open-Ideation DSE on Gemmini + MLPerf Tiny v1.3 streaming     │
 │   - Agent proposes structural variants, not parameter vectors    │
 │   - Reject/accept via sign-off reports                           │
 └─────────────────────────────────────────────────────────────────┘
                              ▲
 ┌─────────────────────────────────────────────────────────────────┐
 │  Layer 2: SUBSTRATE (D1)                                        │
 │   Report-grounded AutoResearch memory system                    │
 │   - .rpt/.def/STA → typed-frontmatter structured memory          │
 │   - Reversible-patch skill library (Voyager-style, EDA-native)   │
 │   - Contradiction/negative-result first-class indexing           │
 └─────────────────────────────────────────────────────────────────┘
                              ▲
 ┌─────────────────────────────────────────────────────────────────┐
 │  Layer 1: PROCESS (D3)                                          │
 │   SHA-pinned LibreLane+OpenROAD+Yosys+sky130A Nix bundle         │
 │   + AutoResearch orchestrator (local CLI + AWS Fargate Spot)     │
 │   + Vibe-coded operator supervising agents (reasoning trace)     │
 └─────────────────────────────────────────────────────────────────┘
```

### 통합 접근의 novelty claim (3단)

- **Primary**: Structured report memory + reversible-patch skill library를 가진 에이전트가 Open-Ideation DSE에서 ORFS-agent(2025) 대비 **다른 종류의 개선**(PPA 점수가 아니라 실패 재사용률·새 구조 발견률)을 달성한다.
- **Secondary**: 축적된 findings/failures가 새 디자인에 투입될 때 **cold-start cost가 감소**한다 (복리 효과).
- **Tertiary (process)**: 비전문가 운영자가 LLM 에이전트를 감독해 오픈 스택에서 sign-off clean 결과에 도달하는 end-to-end trace 자체가 희소 artifact.

### 지표 (수치 가능한 것들)

- CVDP-agentic 서브셋에서 pass@1 delta vs bare-LLM / vs MAGE / vs VerilogCoder
- 동일 compute budget($)에서 Pareto hypervolume (design 3개 평균) vs ORFS-agent
- Finding reuse rate — "이 실패는 finding X와 동일"이라 lint가 자동 매칭한 비율
- Skill library에서 재사용된 transform의 percentage (Voyager의 skill reuse 지표 차용)

## 6. 즉시 처리해야 할 기존 spec 갱신

| 파일 | 갱신 내용 |
|---|---|
| `docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md` | §10 도구 버전에서 **OpenLane2 → LibreLane 2.4**, **MLPerf Tiny v1.2 → v1.3** 교체; §12 scope에서 **Iter 3 Efabless Shuttle 가정 삭제**, 대체 경로(ChipFoundry/wafer.space/IHP/Cadence shuttle) 명시; 또는 archive 처리 후 신규 spec으로 |
| `docs/eda_agent_handoff.md` | MVP 범위 섹션(§14)에 **ORFS-agent 존재 반영**, 단순 autotuning MVP의 novelty 약화 명시 |
| `issues/004-dashboard-framework-decision.md` | D2 실행 관련 대시보드로 재정의 필요 여부 표기 |

## 7. 다음 단계 (제안)

1. **사용자 승인**: Layer 3 통합 프로그램 또는 D1/D2/D3 단일 선택 중 어느 방향?
2. 승인 후 **기존 spec 재작성 또는 신규 spec 작성** (`2026-04-19-report-grounded-autoresearch-design.md`)
3. **K2 심화 수집** (선택된 방향에서 재현 가능 코드 수준까지): ORFS-agent 코드, EvolVE 재현 저장소, Voyager skill library 구현, A-MEM 레포.
4. **writing-plans 스킬**로 implementation plan 작성 (M1/M2/M3 게이트 + 태스크·의존성 그래프 재구성 — 주단위 일정 없이)

---

## 부록 A — K1에서 검증 실패하거나 주의가 필요한 항목

- δ의 arXiv 2603.07670 ("Memory for Autonomous LLM Agents" 서베이) — URL 포맷 의심, 인용 전 재확인
- γ의 OpenROAD 최신 릴리스 태그 — 페이지 fetch 실패, CI 투입 전 `git ls-remote --tags` 필수
- γ의 Yosys 0.50-0.56 개별 릴리스 일자 — CHANGELOG에는 존재하나 날짜 fetch 부분 실패
- Gemmini는 `main` only, 태그 없음 — 반드시 commit SHA로 핀

## 부록 B — 인용

본 리포트의 모든 주장은 `wiki/raw/papers/k1-{alpha,beta,gamma,delta}-*.md`와 `wiki/raw/imports_manifest.yaml`에 저장된 52건의 primary sources에서 유래한다. 축별 자료 ID는 manifest의 `axes.<axis>.resources[].id` 필드로 참조 가능.
