---
title: "FSM and Pipelining"
type: concept
tags: [phase-0, fsm, pipeline, systolic, gemmini]
status: active
confidence: high
created: 2026-05-09
updated: 2026-05-09
sources: [raw/sessions/phase-0-a4-combinational-sequential.md]
---

# FSM and Pipelining

[[digital-logic-gates]] + [[clock-and-timing]] 을 하나의 설계 단위로 통합. RTL 작성 = "FSM + 파이프라인을 Verilog/Chisel로 쓰는 일".

## 핵심 정리

### 통합 그림

```
입력 ─▶ [조합 논리] ─▶ [FF] ─▶ [조합 논리] ─▶ [FF] ─▶ 출력
            │            ▲           │            ▲
            └── 피드백 ───┴─ 피드백 ──┘            │
                          (상태)                   │
            ▲             ▲           ▲            ▲
           CLK           CLK         CLK          CLK
```

CPU/GPU/Gemmini/MCU 모두 구조는 동일. **조합 논리가 뭘 계산하는지 + 상태 비트가 뭘 의미하는지**만 다르다.

### FSM — 순차 로직의 표준 표현

3요소: **State (FF)**, **Next State Logic (조합)**, **Output Logic (조합)**.

```verilog
always @(posedge clk) state <= next_state;
```

```scala
val state = RegInit(IDLE)  // Chisel
```

### Moore vs Mealy

| 변종 | 출력 의존 | 특성 |
|------|-----------|------|
| Moore | `g(state)` | 클럭 에지에서만 출력 변화 → 글리치 없음, 타이밍 깔끔 |
| Mealy | `g(state, input)` | 입력 즉시 반영 → 상태 수↓, 글리치 가능 |

**실무 기본은 Moore.** 레이턴시가 치명적일 때만 Mealy.

### Pipelining — critical path를 잘라 처리량을 올린다

긴 조합 회로 중간에 FF를 꽂으면 각 단의 T_comb이 짧아져 f_max↑.

```
단일 단 (T=10ns, 100 MHz) ─▶ 3단 파이프 (T=3.3ns, 300 MHz)
                              throughput 3×, latency 동일(약간↑), area↑
```

| Tradeoff | 효과 |
|----------|------|
| Throughput | ↑ (매 클럭 결과 1개) |
| Latency | 동일~약간↑ (단 수만큼 클럭 소비) |
| Area | ↑ (중간 FF 추가) |
| Hazard | stall/bypass 로직 필요 (CPU 파이프라인 복잡성의 원인) |

### Systolic Array — 2D 파이프라인

```
PE ─ PE ─ PE ─ PE
 │    │    │    │
PE ─ PE ─ PE ─ PE
 │    │    │    │
PE ─ PE ─ PE ─ PE
```

각 PE 사이가 FF. 클럭마다 데이터가 이웃 PE로 한 칸씩 이동. 행렬 곱을 격자에서 "흐르듯" 계산. **Gemmini의 핵심 구조.**

## A 브랜치 추상화 계단

```
A1 트랜지스터 ─▶ A2 게이트·FF ─▶ A3 클럭·타이밍 ─▶ A4 FSM·파이프 ─▶ B Verilog/Chisel
```

[[cmos-fundamentals]] → [[digital-logic-gates]] → [[clock-and-timing]] → 본 페이지 → Phase B HDL 진입.

## 프로젝트 적용 지점

| 지점 | 어디 |
|------|------|
| Gemmini systolic array | Phase D2 핵심 구조, 위 2D 파이프 그림 그대로 |
| Chisel `Reg`/`when` | Moore FSM 작성의 기본 블록 (Phase B2) |
| `dataflow: {WS, OS}` × `meshRows/Cols` | Gemmini DSE 탐색 공간이 파이프 깊이·너비를 결정 |
| STA path 분리 | 파이프라인 FF 각 구간이 별도 path로 분석 |

## 교차 참조

- [[digital-logic-gates]] — FF + 조합 = 설계 원자
- [[clock-and-timing]] — 파이프라인화는 critical path를 설계적으로 깎는 행위
- [[cmos-fundamentals]] — 면적·전력 비용의 출처
- [[phase-0-eda-operator-lens]] — Phase 0 진입점

## Source

- 원본: `raw/sessions/phase-0-a4-combinational-sequential.md` (2026-04-19 reviewed)
- 외부: Harris & Harris 3장 FSM·7장 pipelining, Hennessy & Patterson 파이프라인 해저드
