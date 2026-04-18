---
phase: 0
branch: A
code: A4
title: 조합 회로 vs 순차 회로 — FSM과 파이프라인
date: 2026-04-19
status: reviewed
confidence: high
---

# A4. 조합 회로 vs 순차 회로 — FSM과 파이프라인

## 학습 목표

- A2·A3에서 나눠 다룬 개념을 **하나의 설계 단위로 통합**
- **FSM (Finite State Machine)** — 모든 순차 로직의 표준 표현
- **Moore vs Mealy** — 출력이 상태에만 의존 vs 입력에도 의존
- **파이프라인 (pipeline)** — critical path를 짧게 쪼개 처리량을 올리는 핵심 기법
- Phase B(HDL)로 넘어가는 다리: "Verilog/Chisel로 쓴다는 건 결국 FSM+파이프라인을 쓴다는 것"

## 핵심 설명 (assistant)

### 1. 통합 관점 — 디지털 회로 = 조합 + 순차

지금까지 배운 것을 한 그림으로:

```
입력 ──▶ [조합 논리] ──▶ [FF] ──▶ [조합 논리] ──▶ [FF] ──▶ 출력
              │             ▲             │             ▲
              │             │             │             │
              └────── 피드백 ──────────────┴────── 피드백 ─
                              (상태)
              ▲             ▲             ▲             ▲
             CLK           CLK           CLK           CLK
```

- **조합 논리**: 현재 입력만으로 출력 계산 (AND/OR/MUX/덧셈기...)
- **FF 사이**: critical path가 결정되는 구간 (A3)
- **피드백**: FF 출력이 다시 조합 논리 입력으로 → **상태(state)**를 만드는 구조

이 세트가 반복되면 모든 디지털 회로가 된다. CPU, GPU, Gemmini, MCU — 구조는 전부 같고 **조합 논리가 뭘 계산하는지 + 상태 비트가 뭘 뜻하는지**만 다를 뿐.

### 2. FSM — 순차 로직의 표준 표현

**FSM (Finite State Machine, 유한 상태 기계)**: 상태의 집합 + 전이 규칙으로 동작을 기술하는 모델.

구성 3요소:
- **상태 (State)**: FF 묶음으로 저장되는 값. N비트면 상태 2^N개.
- **전이 함수 (Next State Logic)**: `next_state = f(current_state, input)` — 조합 논리.
- **출력 함수 (Output Logic)**: `output = g(current_state, input)` — 조합 논리.

예: 신호등 FSM. 상태 = {Red, Yellow, Green}, 입력 = 타이머. 전이: Red→Green→Yellow→Red 순환.

**하드웨어 매핑**:
- State 저장 FF → "state register"
- f, g → 조합 논리 블록

이게 Verilog `always @(posedge clk) state <= next_state;` 또는 Chisel `val state = RegInit(...)` 가 하는 일.

### 3. Moore vs Mealy

**출력이 어디에 의존하느냐**가 구분 기준.

- **Moore**: `output = g(state)` — 출력이 **상태에만** 의존. 입력이 바뀌어도 같은 상태면 같은 출력.
  - 특성: 출력이 클럭 에지에서만 바뀜 → 글리치(glitch) 없음. 타이밍 분석 깔끔.
- **Mealy**: `output = g(state, input)` — 출력이 **상태 + 현재 입력** 모두에 의존.
  - 특성: 입력이 바뀌면 출력이 즉시 바뀜 → 상태 수를 적게 써도 됨. 하지만 글리치 가능.

**실무 팁**: 합성기는 둘 다 지원하지만, 검증·타이밍이 깨끗한 **Moore를 기본으로** 쓰고, 레이턴시가 치명적일 때만 Mealy. 이 프로젝트의 RTL도 Moore 중심.

### 4. 파이프라인 — "길을 쪼개서 동시에 굴려라"

**문제**: critical path(T_comb)가 너무 길면 T_clk가 길어져 주파수가 낮아진다.

**아이디어**: 긴 조합 논리를 **중간에 FF로 자름**. 각 단계가 짧아져 f_max 증가.

```
단일 단계 (T_comb = 10 ns, f_max = 100 MHz):
in ─▶ [ Stage1+Stage2+Stage3 ] ─▶ FF ─▶ out

3단 파이프라인 (각 단 3.3 ns, f_max = 300 MHz):
in ─▶ [Stage1] ─▶ FF ─▶ [Stage2] ─▶ FF ─▶ [Stage3] ─▶ FF ─▶ out
```

**트레이드오프**:
- **처리량 (throughput)**: 매 클럭마다 결과 하나. 파이프라인화 → 3배 빠른 클럭 → **3배 처리량**.
- **레이턴시 (latency)**: 입력이 들어와서 출력이 나오기까지는 여전히 3 클럭. 파이프라인 자체는 레이턴시를 줄이지 않음(조금 늘림).
- **면적 (area)**: 중간 FF들이 추가 → 면적·전력 증가.
- **하자드 (hazard)**: 파이프라인 중간 단계에서 의존성이 생기면 stall/bypass 로직 필요 (CPU 파이프라인이 복잡한 이유).

### 5. Systolic Array — 파이프라인의 2D 확장

Gemmini 같은 DL 가속기의 **systolic array**는 파이프라인을 **2차원 격자**로 확장한 것.

```
PE ─ PE ─ PE ─ PE
 │    │    │    │
PE ─ PE ─ PE ─ PE
 │    │    │    │
PE ─ PE ─ PE ─ PE
```

각 PE(Processing Element) 사이가 FF로 나뉘어 **클럭마다 데이터가 이웃 PE로 한 칸씩 이동**. 행렬 곱을 이 격자 위에서 "데이터가 흐르듯" 계산. 이게 Phase D2의 주제.

### 6. A 브랜치 마무리 — 추상화 계단 완성

```
A1 트랜지스터 (물리)
  ↓
A2 NAND/NOR/INV → AND/OR/MUX + D-FF (게이트·FF)
  ↓
A3 클럭·타이밍 (박자와 제약)
  ↓
A4 FSM + 파이프라인 (설계 단위)   ← 여기까지
  ↓
B Verilog/Chisel (텍스트로 A4를 기술하는 언어)
```

RTL을 쓴다는 것은 결국 **조합 논리 식 + FF를 언제 쓰는지만 기술**하는 일. 그 아래는 합성기+PDK가 알아서 트랜지스터까지 낮춰준다.

## 이 프로젝트와의 연결

- **Gemmini Systolic Array (Phase D2)**: 위의 2D 파이프라인 그림이 핵심 구조.
- **Chisel `Reg`·`when` (Phase B2)**: Moore FSM을 간결하게 쓰는 기본 블록.
- **파이프라인 stage 수**: Gemmini 탐색 공간의 `dataflow: {WS, OS}` + `meshRows/Cols` 선택이 파이프라인 깊이·너비를 결정.
- **STA (Phase C3)**: 파이프라인 FF 사이 각 구간을 별도 path로 분석. 파이프라인화 = critical path를 **설계적으로** 깎는 1차 수단.

## Q&A

(사용자 질문이 들어오면 여기에 추가)

## 참고 자료

- Harris & Harris, "Digital Design and Computer Architecture" (3장 FSM, 7장 pipelining)
- Hennessy & Patterson, "Computer Architecture: A Quantitative Approach" (파이프라인 해저드)
- Wikipedia: Finite-state machine, Pipeline (computing), Systolic array

## 학습 종료 체크

- [x] 사용자가 "이해됨" 확인
- [x] curriculum 체크리스트 업데이트
- [x] 세션 파일 커밋
