---
phase: 0
branch: A
code: A3
title: 클럭·타이밍·동기/비동기
date: 2026-04-18
status: reviewed
confidence: high
---

# A3. 클럭·타이밍·동기/비동기

## 학습 목표

- **클럭 신호**가 왜 디지털 회로의 "심장 박동"인지
- **setup time / hold time** — 모든 타이밍 분석의 두 기둥
- **동기식(synchronous) vs 비동기식(asynchronous)** 설계의 차이와 실무에서 동기식이 지배적인 이유
- **클럭 스큐(skew)와 지터(jitter)** — 클럭이 완벽하지 않다는 현실
- **Critical path**가 칩의 최대 주파수를 결정하는 이유

## 핵심 설명 (assistant)

### 1. 클럭은 회로 전체의 박자

클럭(CLK)은 일정 주기로 0↔1을 반복하는 사각파 신호. 수십 MHz에서 수 GHz까지.
**주기 T = 1/f**. 예: 1 GHz 칩은 T = 1 ns.

역할: **모든 플립플롭이 동시에 상태를 업데이트하는 박자**를 제공.
지휘자가 박자를 내주면 오케스트라 전원이 함께 연주하는 것과 같은 구조. 이게 **동기식 설계(synchronous design)**.

### 2. Setup Time과 Hold Time — 타이밍의 두 축

D 플립플롭의 핵심 제약:

- **Setup time (tsu)**: 클럭 에지 **직전**, 데이터 D가 **안정돼 있어야 하는 최소 시간**.
  - "수업 시작 5분 전에는 자리에 앉아 있어야 함" 같은 규칙.
  - 위반하면 D 값을 제대로 못 잡아 **metastability**(0도 1도 아닌 애매한 상태)가 발생.
- **Hold time (th)**: 클럭 에지 **직후**, 데이터 D가 **그대로 유지돼야 하는 최소 시간**.
  - "종이 치고 1분 동안은 자리에 앉아 있어야 함" 같은 규칙.
  - 위반하면 새로 들어온 데이터를 이전 값으로 오인.

**타이밍 검증 = 회로의 모든 path에 대해 tsu와 th를 만족하는지 확인**.
이걸 통계·분석적으로 하는 도구가 **STA (Static Timing Analysis, C3에서 다룸)**.

### 3. Critical Path = 최대 주파수의 결정자

두 플립플롭 사이의 조합 논리 경로 중 **가장 긴(느린) 경로**가 critical path.

```
FF_A ──[게이트·와이어 지연 Tcomb]── FF_B
                    │
                    └─ 이 Tcomb + tsu가 T보다 커지면 → 타이밍 위반
```

**부등식**: `T ≥ T_clk-to-Q + T_comb + T_setup`
- T_clk-to-Q: FF_A에서 데이터가 Q에 나오기까지 지연 (~수십 ps)
- T_comb: 조합 논리를 지나는 지연 (가장 큰 변수)
- T_setup: FF_B의 setup time

즉 **critical path가 결정적으로 최대 주파수 f_max = 1/T_min을 결정**.
칩을 더 빨리 돌리고 싶으면 critical path를 깎아야 한다 — 이게 Physical Design·합성 최적화의 핵심 목표.

### 4. 동기식 vs 비동기식

**동기식 (synchronous)**:
- 모든 FF가 **같은 클럭**에 맞춰 업데이트.
- 장점: 설계·검증·합성이 단순. 상용 EDA 도구가 모두 이걸 가정.
- 단점: 클럭을 모든 FF까지 균일하게 분배하는 비용 (clock tree가 칩 전력의 20-40%).

**비동기식 (asynchronous)**:
- 클럭 없이 **handshake(request/acknowledge)** 신호로 동기화.
- 장점: 전력 효율, 평균 성능 향상 가능.
- 단점: 설계·검증이 극도로 어렵고, EDA 도구 지원이 빈약.
- 현실: 연구 주제로는 존재하지만 **주류 상용 칩은 거의 100% 동기식**. 이 프로젝트도 동기식만 다룸.

### 5. Clock Skew와 Jitter — 현실의 노이즈

이상적인 클럭은 **모든 FF에 같은 순간 도달**해야 하지만 현실은 그렇지 못하다.

- **Skew (스큐)**: 클럭이 FF마다 도달 시각이 **공간적으로** 다른 정도.
  - 원인: 클럭 트리의 와이어 길이·버퍼 지연 차이.
  - 영향: setup/hold margin을 깎아먹음.
- **Jitter (지터)**: 같은 FF에서도 클럭 에지가 **시간적으로** 흔들리는 정도.
  - 원인: PLL 노이즈, 전원 노이즈.
  - 영향: 유효 클럭 주기를 단축.

**실제 타이밍 부등식은 스큐·지터를 빼준 margin으로 검증**:
```
T ≥ T_clk-to-Q + T_comb + T_setup + T_skew + T_jitter
```
도구가 알아서 반영하지만 "왜 내 칩이 100 MHz로 합성됐는데 실제로는 95 MHz밖에 안 도나"라는 질문의 답이 여기서 나온다.

### 6. 이 프로젝트에서 보게 될 타이밍 개념들

| 개념 | 어디서 보나 |
|------|-------------|
| Setup/Hold | OpenSTA 리포트의 `.slack`, `.violation` 필드 |
| Critical path | STA 리포트의 `report_checks -path_delay max` 출력 |
| Clock skew | P&R 단계의 clock tree synthesis(CTS) 결과 |
| f_max | Gemmini 탐색 공간의 50/100/200 MHz 선택 근거 |
| 동기 도메인 | SoC 내 여러 클럭 도메인 사이 **clock domain crossing(CDC)** — 이 프로젝트는 단일 도메인이라 우선 생략 |

## 이 프로젝트와의 연결

- **STA (Phase C3)**: 위 부등식을 **모든 path**에 대해 자동 검사. Yosys·OpenROAD가 내장.
- **주파수 선택 (Gemmini DSE)**: 50 MHz = 여유 많음 (낮은 전력), 200 MHz = critical path를 강하게 압박 → area·power 증가 Pareto tradeoff.
- **Power model**: 동적 전력 ∝ f이므로 주파수가 직접 `power_mw` 메트릭에 반영됨.
- **Floorplan 단계**: CTS로 skew를 낮추는 것이 높은 f_max의 필수 조건.

## Q&A

(사용자 질문이 들어오면 여기에 추가)

## 참고 자료

- Harris & Harris, "Digital Design and Computer Architecture" (3.5절 타이밍)
- OpenSTA 문서: https://github.com/parallaxsw/OpenSTA
- Wikipedia: Clock skew, Metastability (electronics)

## 학습 종료 체크

- [x] 사용자가 "이해됨" 확인
- [x] curriculum 체크리스트 업데이트
- [x] 세션 파일 커밋
