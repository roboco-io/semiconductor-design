---
title: "K1-γ: Open-Source EDA Stack + DL Accelerator Templates — Direction Evidence"
type: synthesis
tags: [k1, openroad, librelane, yosys, sky130, gemmini, mlperf-tiny, tape-out]
status: active
confidence: medium
created: 2026-05-09
updated: 2026-05-09
sources:
  - raw/papers/k1-gamma-opensource-eda.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §3 L1 / §10 PDK / §11 metric
  - docs/superpowers/specs/2026-04-20-L1-process-design.md  # SHA-pinned Nix bundle
  - docs/superpowers/specs/2026-04-22-graphify-adoption-design.md  # 무관 (transition history)
---

# K1-γ: Open-Source EDA Stack — Direction Evidence

본 프로젝트의 **L1 Process layer가 의존하는 도구·PDK·템플릿**의 가용성·버전·법적 경로를 결정하는 1차 근거. 15 source. **Efabless 셧다운**(source #9)과 **OpenLane2 → LibreLane rename**(source #2)이 spec 갱신을 강제한 두 trigger.

## Production-Ready 스택 (2026-04 기준)

| Layer | 도구 / 버전 | 본 프로젝트 채택 |
|-------|-------------|------------------|
| Synthesis | Yosys 0.50–0.56 (tag pin 필수, e.g., `yosys-0.55`) | ✓ (lockfile.yaml SHA pin) |
| RTL→GDSII flow | **LibreLane 2.4** (FOSSi Foundation, OpenLane2 successor) — K2 ζ 2026-04-22에서 **3.0.2로 갱신** | ✓ |
| Place & Route + STA | OpenROAD (600+ tapeouts to 12nm, 최신 tag는 fetch 시 검증 필요) | ✓ |
| Simulation | Verilator 5.038 / 5.042 | ✓ |
| Testbench | cocotb 2.0.1 (Python DV) | ✓ — **agent-written TB의 표준**로 선택 |
| Sign-off viewer / DRC | KLayout (Virtuoso 대비 inspection 동등, 편집 UX 약함) | ✓ |
| PDK | open_pdks: **sky130A** (no ReRAM, primary), sky130B (ReRAM), gf180mcuD (option) | ✓ — sky130A primary |
| Accelerator template | Chipyard 1.13.0 + **Gemmini** (no tag since 2023, **SHA pin 필수**) | ✓ |
| External benchmark | **MLPerf Tiny v1.3** (2025-09-24, streaming Marvin 추가) | ✓ — **v1.2에서 v1.3으로 uplift** |

## Two Trigger Events (spec 결정 강제)

### Trigger 1 — Efabless Shutdown (Feb 2025)
- chipIgnite 종료. 80 commercial + 50 academic tapeout 합계 폐쇄.
- **본 프로젝트 영향**: 이전 spec의 "Iter 3 Efabless Shuttle" 경로 **무효**.
- **대체 mesh** (모두 viable, less turnkey):
  - **wafer.space** (GF180)
  - **ChipFoundry.io** (sky130 — TT08/TT09 packaging 회복 경로)
  - **IHP** (European 130nm)
  - **Cadence sky130 shuttle**
- 현 spec §부록(테이프아웃 경로)는 "Iter 3+ 결정"으로 보류 — Tiny Tapeout(source #8) 경로가 그동안의 대체.

### Trigger 2 — OpenLane2 → LibreLane Rename
- 2025-08-17 FOSSi Foundation 이관 (lead: Mohamed Gaber).
- immutable design-state object + first-class MACROS config 추가.
- **본 프로젝트 영향**: 이전 spec의 `efabless/openlane2@main` reference **stale**.
- **현재 canonical**: LibreLane (K2 ζ에서 3.0.2로 추가 갱신).

## Source 카테고리

### Tooling (6종)
OpenROAD · LibreLane 2.4 · Yosys 0.5x · Verilator 5.0x · cocotb 2.0 · KLayout. → 본 프로젝트의 L1 Tool plane (CLAUDE.md L62).

### PDK (1종)
**open_pdks** sky130A/B + gf180mcuD. Google 자체 경고 "not for production" — **academic/process novelty 트랙에서는 충분**.

### Tape-out pipeline (2종)
Tiny Tapeout 2025 (1000+ designs, 12 chips, 3 fabs) · Efabless Shutdown. → 본 프로젝트의 silicon 검증 경로 결정 영역.

### Accelerator templates (4종)
Chipyard · **Gemmini** · NVDLA · CFU Playground · TVM-VTA. → 본 프로젝트의 L3 Content target = **Gemmini**(systolic, RoCC, WS/OS dataflow). NVDLA는 frozen baseline, CFU는 lower ceiling.

### Benchmark (1종)
**MLPerf Tiny v1.3** — streaming Marvin (20-min audio, duty-cycle + energy). v1.2 baselines: Bosch/Qualcomm/Renesas/STMicro/Syntiant.

## 본 프로젝트와의 연결 (Direction Evidence)

### Real holes vs commercial — "absolute PPA parity는 unrealistic"

| 영역 | 오픈 측 한계 | 본 프로젝트 함의 |
|------|--------------|------------------|
| STA corners/CPPR | PrimeTime 미달 | 단일 corner 분석 |
| CTS quality | TritonCTS skew/power | f_max 보수적 |
| Sub-130nm PDK | 부재 | 7nm 비교 **금지** — academic/process novelty 트랙 고수 |
| Conformal-level formal | 부재 | sign-off 외 verification 회피 |
| UVM/constraints-random DV | VCS 미달 | cocotb + agent-written TB로 우회 |
| Efabless 대체 mesh | turnkey ↓ | Tiny Tapeout이 1차, 직접 shuttle은 Iter 3+ |

### Small-team novelty contributions (3종 — H1b/H3 직접 정합)

1. **AI-agent exploration of Gemmini parameter space + template-breaking variants on MLPerf Tiny v1.3 streaming** — *유일한* 미공표 axis. spec H1b의 직접 타겟.
2. **RTL/report-interpretation agents (`*.rpt` first-class)** — "EDA operator" thesis와 정합, academic 미개척.
3. **Reproducibility harness — LibreLane + OpenROAD + Yosys + sky130A를 SHA-pinned Nix bundle로** — community에 citable frozen bundle 부재. **publishing 자체가 process novelty.**

### Spec / DSE 영향

| 결정 | K1-γ 근거 | 어디 |
|------|-----------|------|
| sky130A primary, gf180mcuD option | source #7 (production-usable) | spec §10 |
| LibreLane 채택 (OpenLane2 X) | source #2 (rename + 도구 전환) | spec §6.2 lockfile |
| Yosys/OpenROAD/Verilator/cocotb SHA pin | sources #1/#3/#4/#5 (lockfile.yaml) | L1-process-design §SHA-pin |
| MLPerf Tiny v1.3 (v1.2 X) | source #15 (streaming Marvin 추가) | spec §11 metric |
| Gemmini commit SHA pin (no tag since 2023) | source #11 critical caveat | spec §6.2 |
| 7nm 절대 비교 금지 | landscape "absolute PPA parity not realistic" | spec §1 intent guard |
| Iter 3 Efabless 경로 폐기, 대체는 Iter 3+ 결정 | source #9 | spec §부록 (open) |

## 미해결 / 추가 탐색 (Caveats)

- **OpenROAD 최신 tag 미검증** — `git ls-remote --tags` 후 lockfile에 pin (source #1 caveat).
- **Yosys 0.50–0.56 개별 release date** 미확인 — CHANGELOG로 보강 필요.
- **Gemmini main 브랜치 안정성** — tag 부재로 SHA 변경 시 재현성 영향. lockfile 갱신 정책 필요.

## 교차 참조

- [[k1-alpha-llm-for-hdl-evidence]] — RTL 생성 SOTA가 본 페이지의 도구 stack을 사용한다는 의존 관계
- [[k1-beta-agentic-eda-evidence]] — ORFS-agent가 **본 페이지 stack 위에서** 동작 (METRICS2.1 + ORFS = OpenROAD-flow-scripts)
- [[clock-and-timing]] — STA corner 한계가 OpenSTA의 어디서 드러나는지
- [[fsm-and-pipeline]] — Gemmini systolic의 위치
- [[cmos-fundamentals]] — sky130 130nm 노드의 의미
- [[phase-0-eda-operator-lens]] — `.rpt` 해석이 본 페이지 도구의 산출물 해석 능력
- (pending) `[[k1-delta-research-memory-evidence]]` — Karpathy AutoResearch / process novelty 패러다임
- [[k2-theta-benchmark-license-evidence]] — sky130A stack + Efabless 셧다운 trigger가 §13 License Gate + shuttle 4축 후속 mapping으로 정제

## Source

- 원본: `raw/papers/k1-gamma-opensource-eda.md` (2026-04-19 collected, confidence: low → medium)
- 15개 외부 source의 decision_anchors는 `raw/imports_manifest.yaml`
- LibreLane 3.0.2로의 추가 갱신은 K2 ζ (`raw/papers/k2-zeta-l1-runtime.md`, 2026-04-22)
