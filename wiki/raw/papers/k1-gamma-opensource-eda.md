---
type: raw-axis-summary
axis: gamma
title: "γ. Open-Source EDA Stack + DL Accelerator Templates — K1 Resource Survey"
date: 2026-04-19
status: collected
confidence: low
last_verified: 2026-04-19
curator: claude-opus-4-7
tags: [k1, open-source-eda, openroad, librelane, pdk, tape-out, accel-template, benchmark]
source_count: 15
---

# γ. Open-Source EDA Stack + DL Accelerator Templates — K1 Resource Survey

## Resources

### 1. OpenROAD
- URL: https://github.com/The-OpenROAD-Project/OpenROAD
- Tag: [tooling, critical-read]
- WHAT: RTL-to-GDSII unified app; actively developed, reportedly used in 600+ silicon-ready tapeouts up to 12nm. **Note**: latest specific tag unverified at fetch — pin via `git ls-remote --tags` before CI use.

### 2. LibreLane 2.4.0 (2025-07-17) — OpenLane2 successor
- URL: https://fossi-foundation.org/blog/2025-08-17-librelane
- Tag: [tooling, critical-read]
- WHAT: After Efabless's Feb-2025 shutdown, OpenLane2 was renamed LibreLane and moved under FOSSi Foundation (lead: Mohamed Gaber). Adds immutable design-state objects, first-class MACROS config. **This is now the canonical flow to target — NOT `efabless/openlane2`.** Our prior spec's `efabless/openlane2@main` reference is stale.

### 3. Yosys (0.5x series, 2025–2026)
- URL: https://github.com/YosysHQ/yosys/releases
- Tag: [tooling]
- WHAT: 0.50–0.56 shipped in 2025–2026 window. Still de-facto open synth frontend; ABC-dependent for tech mapping. Pin a tag (e.g., `yosys-0.55`) in Dockerfiles.

### 4. Verilator 5.038 / 5.042 (2025)
- URL: https://github.com/verilator/verilator/releases
- Tag: [tooling]
- WHAT: 5.032 (2025-01-01), 5.038 (2025-07-08), 5.042 (2025-11). Default DV simulator for Chipyard/Gemmini flows. SystemVerilog coverage good for synthesizable RTL; constraints/UVM weaker than VCS/Xcelium.

### 5. cocotb 2.0.1 (2025-11-15)
- URL: https://github.com/cocotb/cocotb/releases
- Tag: [tooling]
- WHAT: Major 2.0 line shipped 2025-09-12. Python DV framework of choice for agent-written testbenches.

### 6. KLayout
- URL: https://github.com/KLayout/klayout
- Tag: [tooling]
- WHAT: Actively maintained GDSII/OASIS viewer + DRC engine; used by Tiny Tapeout and most sky130 flows for sign-off viewing. No parity gap vs Virtuoso for layout *inspection*; interactive editing UX weaker.

### 7. open_pdks — sky130A / sky130B / gf180mcuD
- URL: https://github.com/RTimothyEdwards/open_pdks
- Tag: [pdk, critical-read]
- WHAT: As of Sep-2025: sky130A (no ReRAM), sky130B (with ReRAM), gf180mcuD (5-metal, 1.1µm top) are production-usable. Google explicitly warns **"not intended for production settings."** PDKs moved to Linux Foundation CHIPS Alliance in 2023.

### 8. Tiny Tapeout 2025 Retrospective
- URL: https://www.zerotoasiccourse.com/post/year_update_2025/
- Tag: [tape-out-pipeline, status-report, critical-read]
- WHAT: 1000+ designs across 12 chips to 3 fabs in 2025, including first GF180mcu test chips. TT08/TT09 recovered via ChipFoundry packaging onto `TTIHP25a`. New routes: **wafer.space** (GF180), **ChipFoundry.io** (sky130), **IHP** (European 130nm), **Cadence sky130 shuttle**.

### 9. Efabless Shutdown (Feb 2025) — CRITICAL CONSTRAINT CHANGE
- URLs: https://www.eenewseurope.com/en/tiny-tapeout-hit-as-efabless-closes/ · https://news.ycombinator.com/item?id=43222168
- Tag: [tape-out-pipeline, critical-read]
- WHAT: chipIgnite dead; 80 commercial + 50 academic tapeouts over the program's life. **Implication for this project: any plan assuming Caravel-on-sky130-via-Efabless needs replanning onto ChipFoundry, wafer.space, IHP, or Cadence shuttle.** Prior spec's Iter 3 Efabless Shuttle target is **invalid**.

### 10. Chipyard 1.13.0 (2024-09-30)
- URL: https://github.com/ucb-bar/chipyard/releases
- Tag: [accel-template]
- WHAT: Integrates Rocket, BOOM, Saturn + Ara vector units, VexiiRiscv, RISC-V B-ext. Reference SoC harness for integrating Gemmini.

### 11. Gemmini v0.7.1 (2023-05-22) — no tagged release since 2023
- URL: https://github.com/ucb-bar/gemmini
- Tag: [accel-template, critical-read]
- WHAT: Berkeley systolic array generator, RoCC-attached; output- and weight-stationary dataflows runtime-selectable. **Active on `main` only — pin by commit SHA for reproducibility.**

### 12. NVDLA
- URLs: https://nvdla.org · https://github.com/nvdla · recent academic use 2025 https://arxiv.org/html/2508.16095v1
- Tag: [accel-template]
- WHAT: Nvidia's open DL accelerator; Verilog RTL + compiler under NVIDIA Open NVDLA License. Upstream quiet for years; treat as "frozen but usable baseline."

### 13. Apache TVM-VTA
- URLs: https://github.com/apache/tvm-vta · Sep-2025 standalone compiler https://arxiv.org/abs/2509.19790
- Tag: [accel-template]
- WHAT: Versatile tensor accelerator tied to TVM. 2025 standalone Python compiler pipeline released — signals ongoing life outside core TVM.

### 14. CFU Playground
- URL: https://github.com/google/CFU-Playground
- Tag: [accel-template]
- WHAT: FPGA-only RISC-V + custom function unit framework, TFLM integration, published 55–75× speedups on tinyML kernels. Lower ceiling than Gemmini; far lower barrier to first silicon via Tiny Tapeout.

### 15. MLPerf Tiny v1.3 (2025-09-24) — CURRENT STANDARD
- URLs: https://mlcommons.org/2025/09/mlperf-tiny-v1-3-tech/ · https://github.com/mlcommons/tiny
- Tag: [benchmark, critical-read]
- WHAT: Adds **streaming wakeword detection (Marvin, 20-min audio, duty-cycle + energy metrics)** on top of v1.2 tasks (KWS, VWW, IC, AD). v1.2 results (Bosch/Qualcomm/Renesas/STMicro/Syntiant) are the most recent baseline. **Our prior spec targeted v1.2 — should uplift to v1.3.**

## Landscape Snapshot

- **Production-ready right now**:
  Yosys + Verilator + cocotb for RTL→DV; OpenROAD + LibreLane 2.4 on sky130A/gf180mcuD for RTL→GDS at 130/180nm; KLayout for sign-off viewing; MLPerf Tiny v1.3 as external yardstick. Chipyard 1.13 + Gemmini (main branch, SHA-pinned) is the stable accelerator harness.

- **Real holes vs commercial**:
  1. No open-source STA matching PrimeTime on corners/CPPR.
  2. No open-source CTS at commercial quality (TritonCTS lags Innovus on skew/power).
  3. **No open PDK below 130nm** — all claims are "130nm silicon, extrapolated." Absolute comparison to commercial 7nm is **not** fair.
  4. No open formal-equivalence at Conformal level.
  5. UVM/constraints-random DV much weaker than VCS.
  6. Efabless collapse removed the only at-cost hosted end-to-end sky130 pipeline — replacement mesh is viable but less turnkey.

- **Small-team novelty contributions**:
  1. **AI-agent exploration of Gemmini parameter space + template-breaking variants**, evaluated on MLPerf Tiny v1.3 streaming — no existing published autonomous agent targets this specific loop.
  2. **RTL/report-interpretation agents** treating `*.rpt` files as first-class (synth area, STA slack, DRC) — aligns with project's "EDA operator" thesis, underexplored academically.
  3. **A reproducibility harness pinning LibreLane+OpenROAD+Yosys+sky130A by SHA** into one Nix/container — community lacks a citable, frozen bundle; publishing one is itself process-novelty.

  **Chasing absolute PPA parity with 7nm commercial tools is NOT a realistic axis.**

## Caveats / Unverified

- OpenROAD latest release tag unverified at fetch — pin via `git ls-remote --tags` before citing.
- Yosys 0.50–0.56 release dates exist in CHANGELOG but individual date stamps not fetched.
- Gemmini's lack of tags post-2023 is a real finding; active on `main` — always pin by SHA.
