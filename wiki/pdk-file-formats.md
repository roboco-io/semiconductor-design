---
title: "PDK File Formats — Liberty / LEF / DEF / SDC on sky130A"
type: concept
tags: [f-pdk-formats, liberty, lef, def, sdc, sky130a, open-pdks, operator]
status: active
confidence: high
created: 2026-05-10
updated: 2026-05-10
sources:
  - raw/docs/f-pdk-file-formats-operator-guide.md
  - raw/docs/sky130-libraries-naming-official.md
  - raw/repos/open-pdks-installer-and-ciel.md
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §10 PDK
  - docs/superpowers/specs/2026-04-20-L1-process-design.md  # SHA-pin / lockfile.yaml
  - docs/learning/phase-0-curriculum.md  # F branch elevate
---

# PDK File Formats — Liberty / LEF / DEF / SDC

EDA *operator* 입장에서 sky130A flow의 4 lingua franca 파일 포맷을 head/grep으로 읽고 진단하는 진입점. [[eda-flow-report-reading]]이 *리포트*를 다룬다면 본 페이지는 그 리포트의 *입력 substrate*.

## 4 포맷 한 눈에

| 포맷 | 내용 | 생성 | 소비 |
|------|------|------|------|
| `.lib` (Liberty) | cell timing/power/leakage 특성, PVT corner별 | SkyWater (PDK pre-shipped) | OpenROAD STA |
| `.lef` Library | cell macro · pin 위치 · blockage | SkyWater (PDK) | OpenROAD place + route |
| `.tlef` Technology | metal layer · via · design rule · routing track | SkyWater (PDK) | OpenROAD place + route |
| `.def` | placed/routed netlist + cell 좌표 + net 경로 | OpenROAD (per stage) | signoff (DRC, extraction, sim) |
| `.sdc` | clock period · IO delay · false_path | 사용자 작성 | OpenROAD STA |

모두 ASCII text — `head` / `grep` / `sed` 가능.

## sky130A 표준 명명 규칙

```
<process>_<source>_<type>[_<name>]
sky130   _fd     _sc   _hd
↓
sky130 (process) + fd (SkyWater Foundry) + sc (Standard Cell) + hd (High-Density)
```

| Source | Type |
|--------|------|
| `fd` SkyWater · `ef` Efabless · `osu` Oklahoma SU | `pr` primitive · `sc` standard · `bd` build space · `io` IO · `xx` misc |

> **Efabless 후속**: `ef` prefix는 유지 보수 불확실 — 본 프로젝트는 `fd`만 사용 ([[k1-gamma-opensource-eda-evidence]] Trigger 1).

### sky130 표준 셀 5 변종 (모두 `sky130_fd_sc_*`)

| 약어 | 의미 | 본 프로젝트 |
|------|------|-------------|
| **`hd`** | High Density | **default** |
| `hdll` | High Density Low Leakage | leakage 우선 시 후보 ([[cmos-fundamentals]]) |
| `hs` | High Speed | f_max 압박 시 후보 |
| `ls` | Low Speed | — |
| `ms` | Medium Speed | — |

## Liberty `.lib` — Anatomy

corner 코드 분해: `sky130_fd_sc_hd__tt_025C_1v80.lib`
- `tt`/`ff`/`ss` = process corner
- `025C`/`100C`/`n40C` = 온도
- `1v80`/`1v95`/`1v60` = 전압

corner별 signoff:
- **setup signoff**: `ss_n40C_1v60` (slow corner) — 가장 느린 조건에서도 setup 만족해야 함
- **hold signoff**: `ff_100C_1v95` (fast corner) — 가장 빠른 조건에서도 hold 만족해야 함
- **typical 분석**: `tt_025C_1v80`

4 계층:
```
library (sky130_fd_sc_hd) {
  time_unit, voltage_unit, ...           ← 단위 (반드시 첫 점검)
  cell (sky130_fd_sc_hd__buf_1) {        ← cell 정의
    area, leakage_power, ...
    pin (X) {                            ← pin
      direction, capacitance, ...
      timing () {                        ← timing arc (2D table)
        related_pin, timing_type
        cell_rise/cell_fall values
      }
    }
  }
}
```

## LEF Library + Technology — 두 변종 반드시 구분

| 변종 | 파일 | 핵심 grep |
|------|------|-----------|
| **Library LEF** | `sky130_fd_sc_hd.lef` | `^MACRO`, `PIN`, `OBS` |
| **Technology LEF** | `sky130_fd_sc_hd.tlef` | `^LAYER`, `^VIA`, `^VIARULE`, `^SITE` |

Library LEF는 셀별 `MACRO` 블록(`SIZE`, `PIN`, `OBS`), Technology LEF는 layer별 `LAYER` 블록(`PITCH`, `WIDTH`, `SPACING`).

> **정합 rule**: Liberty `cell()` ↔ LEF `MACRO` 1:1 매핑 — 한쪽만 있으면 도구 fail.

## DEF 6 핵심 section

```
DESIGN <name>
DIEAREA ( x1 y1 ) ( x2 y2 )      ← die 경계 (nm)
ROW … unithd … N DO N BY 1 …     ← cell 배치 grid
TRACKS X/Y … LAYER metalN        ← routing track
COMPONENTS                        ← cell instance + 좌표 + orientation
NETS                              ← signal 라우팅 segment
SPECIALNETS                       ← power/ground 라우팅
PINS                              ← die boundary IO
```

### Operator 5 일상 task

| Task | DEF 명령 |
|------|----------|
| 인스턴스 위치 찾기 | `grep "^- u_alu_1 " mydesign.def` |
| die size 정합 | `grep "DIEAREA" mydesign.def` |
| 두 run diff | `diff <(grep "^- " run1.def) <(grep "^- " run2.def)` |
| congestion 분석 | NETS post-process Python |
| signal trace | `grep -A 5 "NET clk" mydesign.def` |

## SDC 5 핵심 명령

```tcl
create_clock -name clk -period 10 [get_ports clk]                    # 1
set_clock_uncertainty -setup 0.2 -hold 0.1 [get_clocks clk]          # 2
set_input_delay  -clock clk -min -0.5 -max 2.5 [get_ports data_in]   # 3
set_output_delay -clock clk -min -0.5 -max 2.5 [get_ports data_out]  # 4
set_false_path -from [get_ports rst_n]                                # 5
set_multicycle_path -setup 2 -to [get_pins divider/q_reg/D]
```

### 완전성 검증 패턴

```bash
# RTL 클럭 입력 수
grep -cE "input.*\bclk\b" rtl/*.v
# SDC create_clock 수
grep -c "^create_clock" design.sdc
# 두 수가 일치해야 함
```

## sky130A 디렉토리 구조

```
$OPEN_PDKS/sky130/
├── libs.ref/sky130_fd_sc_hd/
│   ├── lef/sky130_fd_sc_hd.lef
│   ├── lib/sky130_fd_sc_hd__{tt_025C_1v80,ff_100C_1v95,ss_n40C_1v60}.lib
│   ├── verilog/         (functional)
│   └── gds/             (layout)
└── libs.tech/openlane/sky130_fd_sc_hd.tlef
```

LibreLane env var indirection (절대경로 hardcoding 금지):

```tcl
set ::env(TECH_LEF) $::env(OPEN_PDKS)/sky130/libs.tech/openlane/sky130_fd_sc_hd.tlef
set ::env(LEF)      $::env(OPEN_PDKS)/sky130/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
set ::env(SDC_FILE) $::env(DESIGN_DIR)/src/design.sdc
```

## 설치 — open_pdks 빌드 vs ciel 패키지 매니저

| 방식 | 명령 | 시간 | 본 프로젝트 정합 |
|------|------|------|-------------------|
| open_pdks 빌드 | `git clone … && ./configure --enable-sky130-pdk && make` | **1+ hour** | reproducibility 검증 시 1회 |
| **ciel** (구 volare) | `pip install ciel && ciel enable --pdk-family=sky130 <hash>` | **분 단위** | **L1 lockfile.yaml SHA-pin 후보** |

ciel은 commit hash 단위 pre-built PDK를 호출 — `lockfile.yaml`의 PDK SHA-pin 메커니즘으로 직접 매핑 가능.

## 후속 tape-out mesh (2025-09)

K1-γ Trigger 1 (Efabless 셧다운) 후속:

| Shuttle | PDK | 본 프로젝트 후보 |
|---------|-----|------------------|
| Cadence | sky130A, sky130B | 1순위 |
| Chip Foundry (TT08/TT09 회복) | sky130A, sky130B | 2순위 |
| Wafer.Space | gf180mcuD | 차선 |
| **IHP** | **SG13G2 (European 130nm)** | **사전 ciel 통합** — 즉시 사용 가능 |

## 4 포맷 통합 흐름

```
RTL (.v) ─┐
          │ Yosys
LEF       ┼──→ gate-level netlist (sky130_fd_sc_hd__* 인용)
          │
Liberty ──┤  OpenROAD
LEF + tlef┼──→ DEF (placement) ──→ DEF (routing)
SDC ──────┘                            │
                                        ↓
                                STA · DRC · LVS · extraction
```

## 본 프로젝트 적용 지점

| 지점 | 어디 |
|------|------|
| **Phase 0 F branch elevate 진입점** | [[phase-0-eda-operator-lens]]의 다음 step |
| **L1 lockfile.yaml SHA-pin** | ciel commit hash 메커니즘 |
| **L2 typed-memory schema** | 본 4 포맷이 typed object schema 출처 — `.rpt` 입력 substrate |
| **agent RTL → cell library 정합** | 에이전트 instantiate cell이 Liberty + LEF 둘 다 정의돼야 |
| **agent SDC ↔ pipeline depth** | 너무 깊은 pipeline은 cell 속도와 양립 불가 |

## 교차 참조

- [[eda-flow-report-reading]] — 본 페이지의 입력 → 리포트 출력 흐름
- [[clock-and-timing]] — SDC `create_clock period` ↔ STA timing 부등식 입력
- [[cmos-fundamentals]] — sky130 130nm 노드 + Liberty corner 의미
- [[fsm-and-pipeline]] — agent SDC pipeline depth 정합
- [[phase-0-eda-operator-lens]] — 학습 진입점
- [[k1-gamma-opensource-eda-evidence]] — sky130A 가용성 + Efabless 후속 mesh + LibreLane 3.0.2 stack

## 미해결 / 다음 ingest 후보

- **Si2 Liberty Format Standard** full spec (paywall 가능) — `cell_footprint`, `pin direction` enum 등 미커버 필드
- **Cadence LEF/DEF 8 Reference** — TYPE/DIRECTION/CLASS/USE enum 전체
- **SDC TCL extension 전체 명령** — `set_max_fanout`, `set_load`, `set_drive`, `set_clock_groups` 등
- **K2 papers ingest** (ε/ζ/η/θ 4개) — G1/G2/G3 spec 결정 baseline

## Source

- 종합 raw: `raw/docs/f-pdk-file-formats-operator-guide.md` (perplexity_research, 12 numbered authoritative sources)
- 명명 규칙: `raw/docs/sky130-libraries-naming-official.md` (exa.ai → skywater-pdk.readthedocs.io)
- 설치 + ciel: `raw/repos/open-pdks-installer-and-ciel.md` (exa.ai → github.com/RTimothyEdwards/open_pdks)
