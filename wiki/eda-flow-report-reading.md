---
title: "EDA Flow Report Reading (Yosys + OpenROAD + LibreLane on sky130A)"
type: concept
tags: [c-eda-flow, operator, sta, drc, librelane, yosys, openroad, sky130a]
status: active
confidence: high
created: 2026-05-09
updated: 2026-05-09
sources:
  - raw/docs/c-eda-flow-operator-guide.md
  - raw/docs/librelane-3-architecture-official.md
  - raw/repos/librelane-summary-tool.md
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §11 metric · §3 L2
  - docs/superpowers/specs/2026-04-23-L2-substrate-design.md  # typed memory schema 출처
  - docs/learning/phase-0-curriculum.md  # C branch elevate
---

# EDA Flow Report Reading

EDA *operator* (chip designer 아님) 입장에서 **Yosys synth → OpenROAD STA → LibreLane 3.0.2 → KLayout DRC** 4단 리포트를 읽고 design 건강 여부를 판정하는 진입점.

## Operator 1차 점검 4 리포트

| 단계 | 도구 | 핵심 파일 | 첫 확인 metric |
|------|------|-----------|---------------|
| Synthesis | Yosys | `*.stat` / `*.json` | Number of cells, cell type 분포, Chip area |
| STA | OpenSTA (in OpenROAD) | `max.rpt` (setup), `min.rpt` (hold) | **WNS / TNS / failing endpoint count** |
| Flow orchestration | LibreLane 3.0.2 | `final-summary.json` / `metrics.csv` | `design__timing__setup__ws`, `design__drc__violations__count` |
| DRC | KLayout / Magic | violation report (RDB) | Rule ID, Violation count, Severity |

## STA `report_checks` Anatomy (가장 자주 보게 됨)

```
Startpoint: ...        ← path 기점 (input port 또는 FF)
Endpoint:   ...        ← path 종점 (FF의 D pin 또는 output port)
Path Group: <clock>    ← clock domain
Path Type:  max | min  ← max = setup, min = hold
Delay:      X ns       ← path 누적 지연
Required:   Y ns       ← required time (clock period 기반)
Slack:      Y − X ns   ← 음수면 violation
```

Path table 6 column:

| Column | 의미 | Operator 진단 단서 |
|--------|------|---------------------|
| Pin | net 연결점 | path 흐름 trace |
| Cell | sky130_fd_sc_hd__* | drive strength 약함 의심? |
| Delay | stage 증분 | 가장 큰 stage 찾기 |
| Arrival | 누적 시간 | clock period 점유율 |
| Slew | rise/fall slope | > 0.3 ns sky130A → high-fanout 의심 |
| Load | effective C | buffer 부족? |

> **부등식**: `T ≥ T_clk-to-Q + T_comb + T_setup + T_skew + T_jitter` ([[clock-and-timing]] 부등식과 동일 — STA는 위 부등식을 모든 path에 자동 검사).

## sky130A 정상 / Red flag 표

| Metric | 정상 | Red flag |
|--------|------|----------|
| WNS | ≥ 0 ns | < −0.5 ns 심각 |
| TNS | = 0 | < −10 ns 다수 path 손상 |
| Failing endpoint count | 0 | > 0 |
| Slew (sky130A) | ≤ 0.3 ns | > 0.3 ns → high-fanout buffer 필요 |
| Synthesis cell count | 추정 ±30% | > 30% 초과 |
| Logic depth | ≤ 8 stages | > 8 → critical path 위험 |
| Placement density | 50–70% | > 80% congestion |
| DRC error (sky130A) | 0 | shorts/connectivity 1개도 critical |
| Antenna ratio (poly) | < 50:1 | > 50:1 |
| Antenna ratio (M1 no-diode) | < 400:1 | > 400:1 |

## LibreLane 3.0.2 metric namespace

flow output dir의 `final-summary.json` / `metrics.csv`에 hierarchical key (`::` 또는 `__`):

```
design__cell__count
design__instance__count
design__area__um2
design__core__area__um2
design__placement__density
design__wirelength__estimated__um
design__clock__skew__setup
design__timing__setup__ws        ← setup WNS
design__timing__hold__wns         ← hold WNS
design__timing__tns
design__drc__violations__count
```

이 namespace는 multi-run 비교 + agent가 reward 신호로 사용 가능 ([[k1-beta-agentic-eda-evidence]]의 ORFS-agent METRICS2.1 패턴).

## LibreLane 3.0.2 immutable State 5 원칙 (operator 의미)

1. **In-place 수정 금지** — 임의 파일 수정 흔적 = step 구현 버그
2. **Config immutable** — 같은 config 재실행 = 같은 결과 (CI 단순화)
3. **External path 의존 금지** — flow 외부 파일이 input이면 잘못된 step
4. **PRNG seed 고정** — reproducibility
5. **결정성**: `State_i = Step_i(State_{i-1}, Config)` 함수형

operator 함의: 어느 stage output이든 inspect 가능, intermediate에서 fork·재실행 trivial. 자세히는 [[raw/docs/librelane-3-architecture-official]] (공식 reference).

## DRC violation top 10 sky130A — frequency 순서

[[k1-gamma-opensource-eda-evidence]]의 sky130A stack과 직접 연결:

1. **Metal spacing** (m1.1, m2.1, …) — 라우팅 congestion
2. **Via spacing** (via.1, via2.1, …)
3. **Antenna rule** (ar_q.*) — **Gemmini systolic** ([[fsm-and-pipeline]]) 빈발
4. Width (m1.2 등) — 도구 flow 문제
5. Metal enclosure
6. Density (CMP)
7. Latchup (자동 합성에서는 드묾)
8. Nwell
9. Contact/Via alignment
10. **Short** (bridging) — **critical**, 재합성 필요

## 7-checkpoint operator workflow

| Checkpoint | Pass 기준 |
|------------|-----------|
| Post-Synthesis | cell count ±30%, logic 우선, 미구현 셀 0 |
| Post-Floorplan | core area 달성, PDN 40–50% coverage |
| Post-Placement | density 50–70%, congestion < 80% |
| Post-CTS | clock skew < 5% of T, 새 violation 0 |
| Post-Route | WNS ≥ 0, TNS = 0, antenna 해소 |
| Post-DRC/LVS | short/connectivity 0, LVS pass |
| `metrics.csv` | 위 metric 한 파일에 집계 (1차 stop) |

## Red Flag triage 5단계 (장애 발생 시)

1. **Timing first** — WNS < −2 ns → closure 실패. 단일 bottleneck or 시스템 문제 판정
2. **Area** — floorplan +20% 초과 → infeasible (floorplan ↑ / 합성 ↓)
3. **Congestion** — 90% 초과 영역 → routing 실패 위험
4. **DRC** — short/connectivity → 재합성. spacing/density → routing 재작업
5. **Cross-check** — stat area vs placement area mismatch → library/optimization 이상

## 본 프로젝트와의 연결

| 지점 | 어디 |
|------|------|
| **L2 substrate `.rpt` typed-memory schema** | spec §3.2 — 본 페이지의 4 리포트가 schema 출처 |
| **agent reward 신호** | [[k1-beta-agentic-eda-evidence]] ORFS-agent — METRICS2.1 = 본 페이지 metric namespace |
| **Gemmini DSE 평가** | [[fsm-and-pipeline]] systolic + [[k1-gamma-opensource-eda-evidence]] LibreLane 3.0.2 stack |
| **Phase 0 학습 진행** | [[phase-0-eda-operator-lens]] 다음 step (B/D/E branch 진입 전 elevate 1순위) |
| **`.rpt` 해석 능력** | feedback memory `feedback_learning_lens` "리포트·파일 해석 우선"의 직접 산출물 |

## 보조 도구

- [[raw/repos/librelane-summary-tool]] — Matt Venn의 violation/antenna/cell-usage browser. Tool plane 후보.

## 미해결 / 다음 ingest 후보

- **`.lib`/`.lef`/`.def`/`.sdc` 포맷 detail** — Phase 0 F branch (PDK formats elevate). 다음 ingest 우선.
- **OpenSTA 명령 reference** — `report_checks -from/-through/-to`, exception path, false_path, multicycle. K1-γ evidence URL [3] 추가 fetch.
- **LibreLane custom Step 작성법** — 5 strict 원칙의 실제 enforcement 코드. plugin 시스템 페이지 미수집.

## 교차 참조

- [[clock-and-timing]] — STA 부등식 기초
- [[digital-logic-gates]] — FF가 STA 단위 노드
- [[fsm-and-pipeline]] — systolic의 antenna rule 영향
- [[cmos-fundamentals]] — sky130 130nm 노드 + 표준 셀 prefix
- [[phase-0-eda-operator-lens]] — 학습 정책 진입점
- [[k1-alpha-llm-for-hdl-evidence]] — agent-generated RTL critical reading의 직접 적용
- [[k1-beta-agentic-eda-evidence]] — ORFS-agent METRICS2.1 패턴
- [[k1-gamma-opensource-eda-evidence]] — open-source stack 가용성

## Source

- 종합 raw: `raw/docs/c-eda-flow-operator-guide.md` (perplexity_research, 12 numbered authoritative sources)
- 공식 architecture: `raw/docs/librelane-3-architecture-official.md` (exa.ai → librelane.readthedocs.io)
- 보조 도구 발견: `raw/repos/librelane-summary-tool.md` (mattvenn/librelane_summary)
