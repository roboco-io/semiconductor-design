---
type: raw-source-summary
axis: f-pdk-formats
title: "F. PDK 파일 포맷 Operator Guide — Liberty / LEF / DEF / SDC on sky130A"
date: 2026-05-10
status: collected
confidence: medium
last_verified: 2026-05-10
curator: claude-opus-4-7 (perplexity_research medium)
collection_method: perplexity-ask perplexity_research (deep research, ~30s, 12 numbered authoritative sources)
tags: [f-pdk-formats, liberty, lef, def, sdc, sky130a, open-pdks]
source_count: 12
---

# F. PDK File Formats Operator Guide

EDA *operator* (chip designer 아님) 입장에서 **`.lib` / `.lef` / `.def` / `.sdc` 4 lingua franca 포맷**을 head/grep으로 읽고 진단하는 가이드. Liberty/LEF/DEF/SDC는 모두 ASCII text라 grep 가능.

## Format 1 — Liberty `.lib`

### 명명 규칙

`sky130_fd_sc_hd__tt_025C_1v80.lib` 분해:
- `sky130_fd_sc_hd` = library 이름 (high-density 표준 셀)
- `tt` = process corner (typical-typical)
- `025C` = 25°C 동작 온도
- `1v80` = 1.8V 전원

다른 corner: `ff_100C_1v95` (fast-fast, 100°C, 1.95V — 빠른 corner) / `ss_n40C_1v60` (slow-slow, −40°C, 1.6V — 느린 corner = setup signoff용).

### 4 계층 구조

```
library (sky130_fd_sc_hd) {
  time_unit : "1ns" ; voltage_unit : "1V" ; current_unit : "1A" ;
  capacitance_unit : "1pF" ; power_unit : "1W" ;
  ...
  cell (sky130_fd_sc_hd__buf_1) {
    cell_footprint : "buf" ;
    area : 6.2496 ;
    leakage_power () { ... }
    pin (A) { direction : input ; capacitance : 0.0033 ; }
    pin (X) {
      direction : output ;
      timing () {
        related_pin : "A" ;
        timing_type : combinational ;
        cell_rise (delay_template) { values ( "0.05, 0.10, …" ) ; }
        cell_fall (delay_template) { values ( "..." ) ; }
      }
    }
  }
}
```

### Operator 첫 점검 5 필드

| 필드 | 위치 | 의미 |
|------|------|------|
| `time_unit`, `capacitance_unit` 등 | library 블록 첫 부분 | 단위 missing 시 모든 수치 의미 모호 |
| corner 이름 (filename + library 헤더) | filename `tt`/`ff`/`ss` | signoff corner 잘못 선택하면 false-positive/negative |
| `cell()` 블록 정의된 셀 목록 | library 직속 | netlist에 쓰인 모든 cell이 library에 있어야 함 |
| `pin (X) direction` | cell 블록 안 | input/output/inout/power/ground 구분 |
| `timing()` block 안 `cell_rise`/`cell_fall` 2D table | pin 블록 안 | input slew × output load 2D delay |

### 생성·소비 흐름

- **생성**: SkyWater/Efabless characterization tools (PDK pre-shipped, 사용자가 만들지 않음)
- **소비**: 
  1. **Yosys**: 직접 안 읽음. ABC liberty 통해 area/depth 추정 가이드
  2. **OpenROAD STA**: 핵심 소비자. timing graph 구축 + slack 계산 + 모든 timing 분석

### sky130A 실제 위치

`$OPEN_PDKS/sky130/libs.ref/sky130_fd_sc_hd/lib/`

### 단일 셀 timing 추출 grep

```bash
sed -n '/^cell(sky130_fd_sc_hd__and2_1)/,/^}/p' \
  $OPEN_PDKS/sky130/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
```

## Format 2 — LEF `.lef` (Library + Technology)

### 두 가지 변종 — 반드시 구분

| 변종 | 파일 | 내용 |
|------|------|------|
| **Technology LEF** (`.tlef`) | `sky130_fd_sc_hd.tlef` | metal layer 정의, via stack, design rule, routing track grid |
| **Library LEF** (`.lef`) | `sky130_fd_sc_hd.lef` | cell macro, 핀 위치, blockage |

### Technology LEF 핵심 section

```
LAYER metal1
  TYPE ROUTING ;
  DIRECTION HORIZONTAL ;
  PITCH 0.34 ;
  WIDTH 0.14 ;
  SPACING 0.14 ;
END metal1

VIA via12_default
  LAYER metal1 ; RECT -0.085 -0.085 0.085 0.085 ;
  LAYER via12  ; RECT -0.085 -0.085 0.085 0.085 ;
  LAYER metal2 ; RECT -0.085 -0.085 0.085 0.085 ;
END via12_default
```

5 핵심 grep 키워드: `^LAYER` / `^VIA` / `^VIARULE` / `^SITE` / `^MACRO` (Library LEF 끼리 섞일 때).

### Library LEF 핵심 section

```
MACRO sky130_fd_sc_hd__nand2_1
  CLASS CORE ;
  ORIGIN 0 0 ;
  SIZE 1.38 BY 2.72 ;
  SYMMETRY X Y ;
  SITE unithd ;
  PIN A
    DIRECTION INPUT ;
    USE SIGNAL ;
    PORT
      LAYER li1 ;
      RECT 0.085 0.205 0.255 0.435 ;
    END
  END A
  ... (pin B, Y, VPB, VNB, VPWR, VGND)
  OBS
    LAYER li1 ;
    RECT 0.0 0.0 1.38 2.72 ;
  END
END sky130_fd_sc_hd__nand2_1
```

### Operator 첫 점검 4 필드

| 필드 | 의미 |
|------|------|
| `LAYER <name> PITCH/SPACING/WIDTH` | routing 자원 가용도 + congestion 한계 |
| `VIA / VIARULE` | metal 간 transition 비용·가능성 |
| `MACRO <cell> SIZE` | 셀 bounding box (placement grid 일치 검증) |
| `OBS / OBSTRUCTION` | routing 금지 영역 (예상치 못한 placement 실패 단서) |

### sky130A 실제 위치

- Library LEF: `$OPEN_PDKS/sky130/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef`
- Technology LEF: `$OPEN_PDKS/sky130/libs.tech/openlane/sky130_fd_sc_hd.tlef`

### LibreLane env var 참조

```tcl
set ::env(TECH_LEF) $::env(OPEN_PDKS)/sky130/libs.tech/openlane/sky130_fd_sc_hd.tlef
set ::env(LEF)      $::env(OPEN_PDKS)/sky130/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
```

PDK 경로 hardcoding 절대 금지 — env var 통한 indirection 필수.

## Format 3 — DEF `.def`

### 6 핵심 section

```
DESIGN mydesign ;
DIEAREA ( 0 0 ) ( 2000000 2000000 ) ;     ← die 경계 (nm)
ROW ROW_0 unithd 0 5440 N DO 1438 BY 1 STEP 1380 0 ;
  ↓ 표준 셀이 들어갈 horizontal band
TRACKS X 170 DO 5882 STEP 340 LAYER metal1 ;
  ↓ routing track grid

COMPONENTS 12345 ;
  - u_alu_1 sky130_fd_sc_hd__and2_1 + PLACED ( 5500 8160 ) N ;
  - u_alu_2 sky130_fd_sc_hd__buf_4  + PLACED ( 6900 8160 ) FN ;
  ...
END COMPONENTS

NETS 8932 ;
  - clk
    ( PIN clk ) ( u_alu_1 A ) ( u_alu_2 A ) ...
    + ROUTED metal2 ( 5500 8160 ) ( 6900 * ) ...
END NETS

SPECIALNETS 4 ;
  - VPWR
    ( * VPWR )
    + ROUTED metal4 + USE POWER + WIDTH metal4 480 ...
END SPECIALNETS

PINS 16 ;
  - data_in + NET data_in + DIRECTION INPUT + LAYER metal3 ...
END PINS
```

### Operator 5 핵심 task

| Task | 어디서 |
|------|--------|
| 인스턴스 위치 추적 (`u_mem_decoder_52` 어디?) | `COMPONENTS` section grep |
| die size 정합 (예상 2 mm × 2 mm = 2,000,000 nm 정확?) | `DIEAREA` |
| 두 run 간 변경 instance 추출 | DEF 두 개 `COMPONENTS` 섹션 diff |
| congestion 분석 (특정 영역 metal utilization) | `NETS` + `SPECIALNETS` post-process script |
| signal integrity (clock latency 비정상?) | clock buffer instance grep + `NETS clk` 추적 |

### 생성·소비 흐름

- **생성**: OpenROAD place → route 각 단계마다 새 DEF (timestamp별 DEF snapshot 가능)
- **소비**: signoff 도구 (DRC, parasitic extraction, gate-level simulation)

### LibreLane 출력 위치

```
$BUILD_DIR/runs/current/results/placement/design.def
$BUILD_DIR/runs/current/results/routing/design.def
$BUILD_DIR/runs/current/results/<step>/design_<step>_<iter>.def
```

## Format 4 — SDC `.sdc`

### TCL 기반 declarative 5 명령

```tcl
# 1. 클럭 정의
create_clock -name clk -period 10 [get_ports clk]
  ↓ 100 MHz (10 ns 주기)

# 2. 클럭 관계
set_clock_uncertainty -setup 0.2 -hold 0.1 [get_clocks clk]
set_clock_latency 1.5 [get_clocks clk]

# 3. 입력 timing
set_input_delay  -clock clk -min -0.5 -max 2.5 [get_ports data_in]
  ↓ data_in: clk보다 0.5 ns 빠르거나 2.5 ns 후 안정

# 4. 출력 timing
set_output_delay -clock clk -min -0.5 -max 2.5 [get_ports data_out]

# 5. 예외
set_false_path     -from [get_ports rst_n]
set_multicycle_path -setup 2 -to [get_pins divider/q_reg/D]
```

### Operator 첫 점검 5 명령

| 명령 | 첫 점검 |
|------|---------|
| `create_clock` | 모든 clock signal이 정의됐는가? netlist clock signal 수와 일치 |
| `set_clock_uncertainty` | 너무 conservative(큰 값) → margin 작음 / 너무 optimistic → silicon에서 violation |
| `set_input_delay` / `set_output_delay` | 모든 functional IO에 적용됐는가? |
| `set_false_path` | 의도적인 false path만 — RST async나 mode-only 신호 |
| `set_multicycle_path` | divider·pipeline 같은 의도적 N-cycle 경로만 |

### Constraint 완전성 검증 패턴

```bash
# netlist의 clock 입력 추출
grep -E "input.*clk" mydesign.v | wc -l
# SDC의 create_clock 수
grep -c "^create_clock" mydesign.sdc
# 두 수가 일치해야 함
```

### 생성·소비 흐름

- **생성**: 사용자 작성 (RTL 작성자 또는 spec 자동 생성)
- **소비**: OpenROAD STA (Yosys는 직접 안 읽음)

### LibreLane 참조

```tcl
set ::env(SDC_FILE) $::env(DESIGN_DIR)/src/design.sdc
```

## sky130A PDK 디렉토리 구조

```
$OPEN_PDKS/sky130/
├── libs.ref/
│   └── sky130_fd_sc_hd/      ← high-density 표준 셀
│       ├── lef/              ← Library LEF
│       │   └── sky130_fd_sc_hd.lef
│       ├── lib/              ← Liberty (corner별 다중)
│       │   ├── sky130_fd_sc_hd__tt_025C_1v80.lib
│       │   ├── sky130_fd_sc_hd__ff_100C_1v95.lib
│       │   └── sky130_fd_sc_hd__ss_n40C_1v60.lib
│       ├── verilog/          ← functional Verilog
│       └── gds/              ← GDS layout
└── libs.tech/
    ├── openlane/             ← OpenLane/LibreLane용 tech files
    │   └── sky130_fd_sc_hd.tlef
    ├── magic/                ← Magic용
    ├── netgen/               ← LVS용
    └── klayout/              ← KLayout DRC deck
```

설치 경로 default: `/usr/local/share/pdk/` 또는 ciel은 `~/.ciel/`. 환경변수 `PDK_ROOT` 또는 `OPEN_PDKS` 사용.

## sky130 표준 셀 라이브러리 변종 (5종)

SkyWater fd 라이브러리 (모두 `sky130_fd_sc_*`):

| 약어 | 의미 |
|------|------|
| `hd` | High Density (1.8V, 본 프로젝트 기본) |
| `hdll` | High Density Low Leakage |
| `hs` | High Speed |
| `ls` | Low Speed |
| `ms` | Medium Speed |

## 4 포맷 통합 흐름 (Yosys → OpenROAD)

```
Verilog RTL ─┐
             ├─[Yosys]→ gate-level netlist (sky130_fd_sc_hd__* 인용)
LEF (lib)    ─┘                              │
                                              ▼
                  ┌─[OpenROAD]→ DEF (placement)
Liberty (.lib)    ┤
LEF (.lef/.tlef)  ┤            DEF (routing)
SDC (.sdc)        ┘                  │
                                      ▼
                                STA (slack/WNS/TNS)
                                DRC (KLayout)
                                LVS (Netgen/Magic)
```

핵심 정합 rule: **Liberty cell == LEF MACRO** (둘 중 하나만 존재 → 도구 fail).

## RTL agent 함의

- agent가 instantiate하는 cell이 Library LEF + Liberty에 모두 정의돼 있어야 함
- agent가 정한 clock period와 .sdc에 적힌 `create_clock period`가 일치
- pipeline depth가 cell library 속도와 양립 가능한지 — 너무 깊으면 closure 불가
- custom macro (multi-port memory, analog) 사용 시 별도 LEF/Liberty 필요

## 본 프로젝트 적용 지점

| 지점 | 어디 |
|------|------|
| **Phase 0 F branch elevate** | 본 raw가 직접 컴파일 source — `[[pdk-file-formats]]` |
| **`[[clock-and-timing]]`** | SDC `create_clock period` ↔ STA timing 부등식의 입력 |
| **`[[eda-flow-report-reading]]`** | LibreLane 8 stage 흐름의 입출력 포맷 매핑 |
| **`[[k1-gamma-opensource-eda-evidence]]`** | sky130A 가용성 + open_pdks 정확한 path |
| **L2 substrate `.rpt` typed memory schema** | 본 4 포맷이 typed object의 schema 출처 |

## 인용 (perplexity 12 numbered authoritative sources)

1. IEEE 1076-2008 VHDL + IEEE 1181 Verilog (HDL standards)
2. **Si2 Liberty Format Standard** — www.si2.org (Liberty 공식 spec)
3. **Cadence LEF/DEF Standard** (Cadence/Si2)
4. **OpenROAD docs** — openroad.readthedocs.io
5. **LibreLane 3.0.2 docs** — github.com/The-OpenROAD-Project/OpenLane (LibreLane fork)
6. **Open PDK Sky130** — github.com/RTimothyEdwards/open_pdks (본 raw exa fetch 대상)
7. OpenROAD GitHub (DEF/LEF/Liberty handling 예시)
8. Yosys docs — yosyshq.net
9. SDC Standard (Synopsys, 사실상 표준)
10. **SkyWater Sky130 PDK release notes** — skywater-pdk.readthedocs.io (본 raw exa fetch 대상)
11. VLSI Design 학회 publications (DAC, ISCA)
12. OpenROAD Project 2024-2026 publications

## Caveats / Unverified

- Liberty `cell_footprint` semantics, `pin direction` 추가 enum (예: `inout`) 등 detail은 Si2 spec 직접 참조 필요 (paywall 가능).
- LEF 명령어 enum (TYPE/DIRECTION/CLASS/USE) 전체 리스트는 본 raw에 없음 — Cadence LEF/DEF Reference 8 spec 별도.
- DEF의 `SPECIALNETS` `WIDTH` 단위 (technology LEF에 의존) cross-check 필요.
- SDC TCL extension의 모든 명령(예: `set_max_fanout`, `set_load`, `set_drive`)은 본 raw에 없음.
