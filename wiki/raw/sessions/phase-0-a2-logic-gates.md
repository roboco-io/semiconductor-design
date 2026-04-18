---
phase: 0
branch: A
code: A2
title: 디지털 로직 게이트와 플립플롭
date: 2026-04-18
status: reviewed
confidence: high
---

# A2. 디지털 로직 게이트 (AND/OR/NOT/NAND + Flip-flop)

## 학습 목표

- 기본 로직 게이트가 트랜지스터로 어떻게 구현되는지
- **NAND가 "universal gate"인** 이유 (모든 회로를 NAND만으로 만들 수 있음)
- **조합 논리(combinational)** vs **순차 논리(sequential)**의 구분
- **Flip-flop**이 "1비트 메모리"로서 클럭 동기 시스템의 기본 단위인 이유

## 핵심 설명 (assistant)

### 1. 기본 게이트 — 진리표와 CMOS 구현

**게이트**는 입력(0/1)에 대해 출력(0/1)을 계산하는 함수. 표기는 수학 기호처럼.

| 게이트 | 식 | 진리표 요약 |
|--------|-----|-------------|
| NOT (inverter) | `Y = ¬A` | 뒤집기 |
| AND | `Y = A·B` | 둘 다 1일 때만 1 |
| OR | `Y = A+B` | 하나라도 1이면 1 |
| NAND | `Y = ¬(A·B)` | AND의 반대 |
| NOR | `Y = ¬(A+B)` | OR의 반대 |
| XOR | `Y = A⊕B` | 두 입력이 다를 때만 1 |

CMOS로 만들 때는 항상 **PMOS 네트워크(VDD 쪽) + NMOS 네트워크(GND 쪽)**가 서로 반대로 배치됨.
가장 간단한 예, **인버터(NOT)**:
- 입력 A=0 → PMOS ON, NMOS OFF → 출력이 VDD(=1)
- 입력 A=1 → PMOS OFF, NMOS ON → 출력이 GND(=0)

NAND는 **PMOS 2개 병렬 + NMOS 2개 직렬**. 트랜지스터 4개로 완성. AND는 NAND+인버터라 트랜지스터 6개.
**즉, NAND가 AND보다 싸다.** 이게 칩 안에서 NAND가 편재한 물리적 이유.

### 2. NAND는 왜 "universal"인가

NAND 하나로 모든 논리 함수를 만들 수 있다는 뜻:
- NOT: `NAND(A, A)` — 두 입력에 같은 값 넣으면 ¬A
- AND: `NAND(NAND(A,B), NAND(A,B))` — NAND 뒤집으면 AND
- OR: De Morgan 법칙으로 `NAND(¬A, ¬B) = A+B`

실무 의미: 합성기(Yosys)가 RTL을 게이트로 풀어낼 때, 표준 셀 라이브러리의 NAND·NOR·INV를 조합해 내부 표현을 만든다. 테크놀로지 매핑 단계에서 PDK 셀로 치환.

### 3. 조합 vs 순차

- **조합 논리 (combinational)**: 출력 = 현재 입력만의 함수. 메모리 없음. 예: 덧셈기, 멀티플렉서, 디코더.
- **순차 논리 (sequential)**: 출력 = 현재 입력 + **과거 상태**. 메모리 있음. 예: 카운터, FSM, 레지스터.

순차 회로의 "상태"를 1비트 단위로 저장하는 게 **플립플롭**.

### 4. D Flip-flop — 가장 중요한 순차 소자

신호 3개: `D`(데이터), `CLK`(클럭), `Q`(출력).

동작 규칙: **CLK의 상승 에지(rising edge) 순간, D 값을 붙잡아 Q에 저장. 다음 에지까지 Q는 고정.**

즉 "매 클럭 한 번씩 사진을 찍어서 값을 고정시키는 1비트 카메라".

이게 왜 중요한가:
- **타이밍의 단위**: 조합 회로의 계산은 두 플립플롭 사이 시간(= 1 클럭 주기)에 끝나야 한다.
  끝나지 못하면 **timing violation**. STA(C3에서 배울 예정)의 핵심 분석 대상.
- **레지스터 = N비트 플립플롭 묶음**: CPU의 범용 레지스터, Gemmini의 가중치 버퍼, 파이프라인 스테이지 사이 latch 모두 플립플롭 뭉치.
- **동기식 설계의 기반**: 클럭 에지에서만 상태가 바뀌므로 회로 전체가 한 박자에 움직임 → 검증·합성이 훨씬 단순.

### 5. 요약된 추상화 계단

```
트랜지스터 (물리) → NAND/NOR/INV (게이트) → AND/OR/XOR/MUX (조합 블록)
                                          → D-FF → 레지스터 (순차 블록)
                                          → 유한상태기·CPU·Gemmini ...
```

Verilog·Chisel로 RTL을 쓴다는 건 이 계단의 **조합+순차 레벨**에서 설계한다는 뜻. 아래 트랜지스터 레벨은 합성기와 PDK가 담당.

## 이 프로젝트와의 연결

- **RTL (Phase B)**: Chisel의 `Reg`, Verilog의 `always @(posedge clk)`는 전부 D-FF를 만든다.
- **STA (Phase C3)**: "두 플립플롭 사이 조합 경로가 1 클럭 안에 끝나는가"를 모든 path에 대해 검증.
- **Gemmini Systolic Array (Phase D2)**: 각 PE(Processing Element)가 플립플롭으로 경계를 이뤄 클럭마다 데이터가 한 칸씩 이동.
- **Sky130 표준 셀**: `sky130_fd_sc_hd` 라이브러리에 NAND2, NOR2, INV, DFF 등 기본 셀이 들어 있고 우리가 쓰는 최종 칩은 이 셀들의 조합.

## Q&A

(사용자 질문이 들어오면 여기에 추가)

## 참고 자료

- Harris & Harris, "Digital Design and Computer Architecture" (2장·3장)
- SkyWater 표준 셀 문서: https://skywater-pdk.readthedocs.io/en/main/contents/libraries.html
- Wikipedia: NAND logic, Flip-flop (electronics)

## 학습 종료 체크

- [x] 사용자가 "이해됨" 확인
- [x] curriculum 체크리스트 업데이트
- [x] 세션 파일 커밋
