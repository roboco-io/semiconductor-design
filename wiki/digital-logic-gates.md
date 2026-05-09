---
title: "Digital Logic Gates and Flip-Flops"
type: concept
tags: [phase-0, gates, flipflop, rtl, yosys]
status: active
confidence: high
created: 2026-05-09
updated: 2026-05-09
sources: [raw/sessions/phase-0-a2-logic-gates.md]
---

# Digital Logic Gates and Flip-Flops

[[cmos-fundamentals]] 위에 쌓이는 첫 추상화 — 트랜지스터를 NAND/NOR로 묶고, FF로 1비트 메모리를 만들면 RTL 레벨이 시작된다.

## 핵심 정리

### 기본 게이트 — CMOS 구현 비용

| 게이트 | 트랜지스터 수 | 비고 |
|--------|---------------|------|
| INV | 2 | PMOS↑ + NMOS↓ |
| NAND2 | 4 | PMOS 2 병렬 + NMOS 2 직렬 |
| AND2 | 6 | NAND + INV |
| NOR2 | 4 | PMOS 2 직렬 + NMOS 2 병렬 |

**NAND가 AND보다 싸다.** 칩 안에서 NAND가 편재하는 물리적 이유. Yosys가 RTL을 풀 때도 NAND·NOR·INV로 normalize 후 PDK 표준 셀에 매핑한다.

### NAND universal

`NAND(A,A) = ¬A`, `NAND(NAND(A,B), NAND(A,B)) = AND`, De Morgan으로 OR도 표현. 합성기 내부 표현의 이론적 기반.

### 조합 vs 순차

- **조합 (combinational)**: 출력 = 입력만의 함수. 메모리 없음.
- **순차 (sequential)**: 출력 = 입력 + **상태**. FF 묶음이 상태를 저장.

### D Flip-Flop — 1비트 카메라

신호 3개 (D, CLK, Q). **CLK 상승 에지에서 D를 잡아 Q에 고정.** 다음 에지까지 Q는 변하지 않는다.

이게 왜 결정적인가:
- **타이밍 단위**: 두 FF 사이 조합 회로는 1 클럭 주기 안에 완료해야 한다 → [[clock-and-timing]]의 setup/hold 기둥.
- **레지스터 = N-bit FF 묶음**: CPU GPR, Gemmini 가중치 버퍼, 파이프라인 stage 경계가 모두 FF 뭉치.
- **동기식 설계 기반**: 클럭 에지에서만 상태 변화 → 검증·합성이 단순.

## 추상화 계단

```
트랜지스터 → NAND/NOR/INV → AND/OR/XOR/MUX → 조합 블록
                          → D-FF → 레지스터 → 순차 블록 → FSM/CPU/Gemmini
```

RTL 작성은 **조합+순차 레벨**의 텍스트화. 트랜지스터 레이어는 합성기+PDK가 자동 처리.

## 프로젝트 적용 지점

| 지점 | 어디서 보이나 |
|------|---------------|
| Verilog `always @(posedge clk)` / Chisel `Reg` | RTL 작성 시 D-FF 직접 인스턴스화 |
| Yosys 합성 매핑 | NAND/NOR/INV → `sky130_fd_sc_hd` 표준 셀 |
| Gemmini PE 경계 | 각 PE가 FF로 둘러싸여 클럭마다 데이터 한 칸 이동 ([[fsm-and-pipeline]]) |

## 교차 참조

- [[cmos-fundamentals]] — 게이트 아래 트랜지스터 층
- [[clock-and-timing]] — FF 사이 타이밍 부등식
- [[fsm-and-pipeline]] — FF가 모여 만드는 상태기와 파이프라인
- [[phase-0-eda-operator-lens]] — 학습 진입점

## Source

- 원본: `raw/sessions/phase-0-a2-logic-gates.md` (2026-04-18 reviewed)
- 외부: Harris & Harris "Digital Design and Computer Architecture" 2-3장, SkyWater 표준 셀 문서
