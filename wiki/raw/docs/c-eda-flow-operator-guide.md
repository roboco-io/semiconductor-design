---
type: raw-source-summary
axis: c-eda-flow
title: "C. EDA Flow Operator Guide — Yosys + OpenROAD + LibreLane 3.0.2 + sky130A 리포트 해석"
date: 2026-05-09
status: collected
confidence: medium
last_verified: 2026-05-09
curator: claude-opus-4-7 (perplexity_research medium)
collection_method: perplexity-ask perplexity_research (deep research, ~30s, 43 citations)
tags: [c-eda-flow, yosys, openroad, librelane, sky130a, drc, sta, operator]
source_count: 12
---

# C. EDA Flow Operator Guide — Report Interpretation

EDA *operator* (chip designer 아님) 관점에서 Yosys synth → OpenROAD STA → LibreLane 3.0.2 flow → sky130A DRC 4축 리포트를 한 번에 정리. 깊은 이론은 skip, 실제 `*.rpt` 한 번에 health/broken 판정 가능한 수준.

## Area 1 — Yosys Synthesis Report

### `stat -liberty sky130_fd_sc_hd__tt_025C_1v80.lib` 출력 골격

```
Number of wires:           1234
Number of cells:           987
  sky130_fd_sc_hd__a21oi_1   215
  sky130_fd_sc_hd__nand2_1   150
  sky130_fd_sc_hd__inv_1     120
  sky130_fd_sc_hd__dfxtp_1    87
  ...
Chip area for module '\top': 4567.890 μm²
```

### Operator 첫 점검 5 필드

| 필드 | 의미 | sky130A 정상 / Red flag |
|------|------|------------------------|
| Number of cells | 총 instance | 합성 추정의 ±30% 이상 어긋나면 RTL 손상 의심 |
| Cell type histogram | 표준 셀 분포 | logic cell 비중 ↑, buffer/inverter 비중 < 30% 정상 |
| Chip area (μm²) | 영역 추정 | RTL 변경 없이 < 20% 변동 정상 |
| Logic depth | 조합 path 깊이 | 8 stages 초과 시 STA에서 critical path 위험 |
| 미구현 셀 prefix | 예: `\$add_uns` 잔존 | 0이어야 함. 0 아니면 합성 실패 |

## Area 2 — OpenROAD STA `report_checks -path_delay max`

### Real example (sky130A, setup violation)

```
Startpoint: config_shift_i (input port clocked by config_clk_i)
Endpoint:   _3723_ (rising edge-triggered FF clocked by config_clk_i)
Path Group: config_clk_i
Path Type:  max
Delay:      1.2567 ns (actual)
Required:   1.2500 ns (required time)
Slack:     -0.0067 ns (setup violation)

Pin                 Cell                          Delay  Arrival  Slew   Load
config_shift_i      -                             0.000  0.000    0.050  -
gate_A_input        sky130_fd_sc_hd__and2_1       0.085  0.085    0.150  0.020
gate_B_output       sky130_fd_sc_hd__nand2_1      0.142  0.227    0.200  0.035
_3723_/D            -                             0.950  1.177    0.210  -
_3723_              sky130_fd_sc_hd__dffq_1       (setup) 1.200    -      -

Data required time:    1.2500 ns
Data arrival time:     1.1770 ns
Slack:                -0.0067 ns
```

### Operator 첫 점검 5 필드

| 필드 | 의미 |
|------|------|
| **Slack** | required − arrival. 음수면 violation. 가장 먼저 보는 값 |
| **Delay (actual)** | path 누적 지연. clock period 점유율 |
| **Startpoint / Endpoint** | 어떤 port/FF에서 어떤 FF로 가는 path인지 — 디버그 단서 |
| **Path Type** | `max` = setup check (최장 path), `min` = hold check (최단 path) |
| **Path Group** | clock 도메인 묶음. domain별 violation 분류 |

### path table column 의미

- **Pin**: net/cell 연결점
- **Cell**: 표준 셀 instance (sky130_fd_sc_hd__*)
- **Delay**: 해당 stage 증분 지연
- **Arrival**: startpoint부터 누적 시간
- **Slew**: 신호 transition 시간 (rise/fall slope) — 너무 크면 (> 0.3 ns sky130A) high-fanout 신호
- **Load**: cell이 driving하는 effective capacitance

### 요약 metric (전체 design)

| Metric | 의미 | sky130A 정상 / Red flag |
|--------|------|------------------------|
| WNS (Worst Negative Slack) | 가장 음수 slack 1개 | ≥ 0.0 ns 정상 / < −0.5 ns 심각 |
| TNS (Total Negative Slack) | 모든 violation 합 | = 0 정상 / < −10 ns 다수 path 손상 |
| failing endpoint count | 음수 slack endpoint 수 | 0 정상 |

명령: `report_wns`, `report_tns`, `report_worst_slack`. 출력 예: `>> wns 0`, `>> tns 0`.

### Setup vs Hold 우선순위

- **Setup violation 먼저 수정.** Hold violation은 setup 수정 과정에서 악화될 수 있음.
- Setup fix: cell upsizing, logic restructure, pipeline 추가
- Hold fix: 작은 cell 또는 inverter pair 삽입
- 두 리포트 분리: `max.rpt` (setup) / `min.rpt` (hold)

## Area 3 — LibreLane 3.0.2 Flow Stages

### 8 stages + per-stage outputs

| # | Stage | 핵심 출력 | 핵심 metric |
|---|-------|-----------|-------------|
| 1 | Synthesis (Yosys) | Verilog/JSON netlist + stat | `design__cell__count`, `design__area__um2` |
| 2 | Floorplan | DEF (core boundary, PDN, IO) | `design__core__area__um2`, `design__die__area__um2` |
| 3 | Macro Placement | DEF (macro 위치) | macro blockage area |
| 4 | Placement | DEF (cell 배치) | `design__placement__density`, `design__wirelength__estimated__um` |
| 5 | CTS (Clock Tree Synthesis) | DEF + clock buffer 삽입 | `design__clock__skew__setup` |
| 6 | Timing Opt + Routing | optimized DEF + 배선 | `design__timing__setup__ws`, `design__timing__tns` |
| 7 | DRC | KLayout/Magic 위반 리포트 | `design__drc__violations__count` |
| 8 | LVS | netlist match | `lvs__total_errors` |

### Configuration override 패턴

JSON/YAML/Tcl 모두 지원. scoped prefix:

```yaml
pdk::sky130A:
  scl::sky130_fd_sc_hd:
    CLOCK_PERIOD: 15.0
    PL_TARGET_DENSITY_PCT: "expr::($FP_CORE_UTIL + 10.0)"
```

- `pdk::<name>` — PDK 한정
- `scl::<lib>` — standard cell library 한정
- `expr::` — 동적 계산

### 3.0.2 vs OpenLane 2.x 차이 (immutable State)

OpenLane 2.x는 Tcl 전역 상태 + 파일 system 의존. LibreLane 3.0.2는:
- **State_i = Step_i(State_{i-1}, Config)** 함수형 정의
- 각 Step의 output state가 first-class object
- metrics가 State 안에 직접 기록 (post-process X)
- 같은 input → 같은 output 보장 (deterministic)

Step 5 strict 원칙 (LibreLane 공식):
1. 파일 in-place 수정 금지
2. config_in 수정 금지 (programmatic enforce)
3. external filesystem path 의존 금지
4. step 디렉토리 외부 파일 생성 금지
5. PRNG seed 고정

### `final-summary.json` / `metrics.csv`

flow output dir의 마지막 metric 집계. operator의 1차 stop:
- post-route WNS 음수 → timing 미해결
- DRC violation 초과 → physical 문제
- 추정 area > floorplan target → 닫히지 않음

### `metrics::` 네임스페이스 (LibreLane)

`design__cell__count`, `design__timing__setup__ws`, `design__drc__violations__count` 등 hierarchical key. CSV/JSON export로 다중 run 비교.

## Area 4 — sky130A DRC violations top 10

### KLayout DRC report 형식

```
Design Rule Violations Report
Layer: M1 (metal 1)
Rule: m1.1 - Metal spacing
Violations found: 42
Violation #1:
  Location: X=10.5um Y=20.3um
  Severity: Error
  Description: m1 spacing 0.120um < minimum 0.140um
  Cell: macro_instance
```

3 필드 우선: **Rule ID** / **Violation Count** / **Severity (Error/Warning)**.

### Top 10 frequency 순서

| # | Rule family | 의미 | 흔한 원인 |
|---|-------------|------|-----------|
| 1 | Metal spacing (m1.1, m2.1, …) | 같은 layer 두 metal 간격 < 0.14 µm (M1) | 라우팅 congestion ↑, 80%+ 영역 |
| 2 | Via spacing (via.1, via2.1, …) | via 간격 < 0.15–0.17 µm | 다층 교차 노드 밀집 |
| 3 | **Antenna rule** (ar_q.*) | poly 50:1 / met1 400:1 (no diode) / 2200:1 (with diode) | **Gemmini systolic** 같은 long path 데이터 net에서 빈발 |
| 4 | Width (m1.2, via.1b) | 최소 폭 미달 (M1 0.12–0.17 µm) | 라이브러리 정의 도구 mismatch — 도구 flow 문제 |
| 5 | Metal enclosure | metal이 via를 0.04 µm 이상 enclose 못함 | 라우팅 topology 좁음 |
| 6 | Density (CMP) | 40×40 µm tile에서 metal density 30–50% 벗어남 | 영역 over/under-routing |
| 7 | Latchup | NMOS↔PMOS 거리·well bias | 자동 합성에서는 드묾, 수동 layout 시 |
| 8 | Nwell (nwell.1, nwell.2) | nwell 구조·간격 | floorplan 단계 |
| 9 | Contact/Via alignment | via가 metal/diffusion 밖 | 도구 버그 — re-route |
| 10 | **Short** (bridging) | 다른 net이 같은 공간 점유 | **critical** — netlist/route 근본 문제 |

### Antenna rule + Gemmini

systolic array는 long data path (8+ PE 통과) → antenna ratio 초과 빈발. fix: intermediate power tap, antenna diode 삽입. LibreLane은 routing에서 자동 추가 가능 (`ROUTING_LAYER_DIODE` config). post-route에 violation 잔존 시 antenna fix enable 여부 확인.

### Magic vs KLayout

- KLayout: GUI 시각 + batch report
- Magic: interactive editor, `drc check` + `drc list all`
- 두 도구 violation count가 약간 다를 수 있음 — sign-off는 foundry 승인 도구(sky130A는 KLayout)
- 위반 waiver: KLayout는 RDB 기반 waiver DB, Magic는 별도 명시

## Operator 7-checkpoint workflow

| Checkpoint | 점검 |
|------------|------|
| Post-Synthesis | cell count 추정 ±30%, type 분포(logic 우선), 미구현 셀 0 |
| Post-Floorplan | core area 달성, PDN coverage 40–50% |
| Post-Placement | density 50–70%, congestion < 80%, critical path 추정 < clock period |
| Post-CTS | clock skew < 5% of clock period, 새 violation 0 |
| Post-Route | WNS ≥ 0, TNS = 0, DRC error 0, antenna 해소 |
| Post-DRC/LVS | short/connectivity error 0, LVS pass, waived violation 문서화 |
| metrics.csv | 위 metric 한 파일에 집계 — 1차 stop |

## Red Flag triage 5단계 (장애 시)

1. **Timing first**: WNS < −2 ns → closure 실패. 단일 bottleneck vs 시스템 — 후자면 clock period 완화
2. **Area**: floorplan 대비 +20% 초과 → infeasible. floorplan ↑ or 합성 ↓ or 다른 라이브러리
3. **Congestion**: 90% 초과 영역 존재 → routing 실패 위험. core 확대
4. **DRC**: short/connectivity → netlist/routing 근본 문제 (재합성). spacing/density → routing 재작업
5. **Cross-check**: stat area vs placement area mismatch → library/synth optimization 이상

## 본 프로젝트 적용 지점

- **Phase 0 F branch (PDK formats)**: `.lib`/`.lef`/`.def`/`.sdc` 정의 → 본 가이드 표의 standard cell prefix·DEF artifact 흐름과 직접 연결.
- **Phase 0 C branch**: 본 raw가 직접 컴파일 source.
- **K1-α evidence**: agent-generated RTL의 critical reading 능력 = 본 가이드의 Area 1·2 + checkpoint 7개.
- **K1-β evidence (ORFS-agent)**: agent가 METRICS2.1 읽고 path 결정 — 본 가이드 Area 3 metric namespace와 동일 구조.
- **K1-γ evidence**: stack(LibreLane 3.0.2 + Yosys + OpenROAD + sky130A) 구성 그대로.
- **L2 substrate `.rpt` typed memory**: K1-δ evidence가 제안한 reversible-patch + report-grounded memory 객체의 **schema 출처**.

## 인용 (perplexity 43 citations 중 operator 가치 ↑ 12개)

- [1] https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/index_backends.html (Yosys backend cmd)
- [2] https://yosyshq.readthedocs.io/projects/yosys/en/0.47/cmd/stat.html (stat 명령)
- [3] https://openroad.readthedocs.io/en/latest/main/src/sta/README.html (OpenSTA spec)
- [4] https://github.com/The-OpenROAD-Project/OpenROAD/discussions/3694 (`report_checks` 사용 예)
- [5] https://librelane.readthedocs.io/en/latest/reference/architecture.html (LibreLane 3.0.2 architecture)
- [6] https://librelane.readthedocs.io/en/stable/usage/timing_closure/index.html (LibreLane timing closure)
- [7] https://openlane2.readthedocs.io/en/latest/reference/configuration.html (config 유산)
- [8] https://www.zerotoasiccourse.com/post/librelane_output_files/ (output file 실제 예시 — 2025 갱신)
- [9] https://skywater-pdk.readthedocs.io/en/main/rules/antenna.html (sky130A antenna)
- [10] https://skywater-pdk.readthedocs.io/en/main/rules/periphery.html (sky130A 주변)
- [11] https://www.klayout.de/doc/manual/drc_basic.html (KLayout DRC engine)
- [12] https://fossi-foundation.org/blog/2025-08-17-librelane (LibreLane release announce — K1-γ evidence와 중복)

## Caveats / Unverified

- perplexity output에서 일부 sky130A spacing 수치(예: M1 0.14 µm)는 official rule와 cross-check 권장.
- Magic vs KLayout 위반 count 차이는 도구 알고리즘 차이 — sign-off는 KLayout 사용.
- LibreLane 3.0.2 → 2.x migration 가이드는 librelane.readthedocs.io의 "Migrating from OpenLane" 별도 문서 참조 (본 raw 미수집).
