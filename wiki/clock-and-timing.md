---
title: "Clock and Timing Basics (STA Foundations)"
type: concept
tags: [phase-0, timing, sta, fmax, opensta]
status: active
confidence: high
created: 2026-05-09
updated: 2026-05-09
sources: [raw/sessions/phase-0-a3-clock-timing.md]
---

# Clock and Timing Basics

OpenSTA 리포트(`*.rpt`)를 실제로 읽기 위한 최소 모델. setup/hold·critical path·skew/jitter가 한 부등식 안에 어떻게 들어가는지를 외운다.

## 핵심 정리

### 클럭 = 회로의 박자

주기 `T = 1/f`. 1 GHz → T=1ns. 모든 FF가 같은 박자에 상태 갱신 = **동기식 설계 (synchronous)**.

### Setup/Hold — 두 기둥

- **Setup time (tsu)**: 클럭 에지 **직전** D가 안정돼 있어야 하는 최소 시간. 위반 시 metastability.
- **Hold time (th)**: 클럭 에지 **직후** D가 유지돼야 하는 최소 시간. 위반 시 새 데이터를 이전 값으로 오인.

타이밍 검증 = 모든 path에 대해 위 둘을 만족하는지 자동 체크 → **STA (Static Timing Analysis)**.

### Critical Path — f_max 결정자

두 FF 사이 조합 path 중 가장 긴 것. 부등식:

```
T ≥ T_clk-to-Q + T_comb + T_setup + T_skew + T_jitter
```

| 항 | 의미 |
|----|------|
| T_clk-to-Q | FF의 출력 지연 (~수십 ps) |
| T_comb | 조합 path 지연 (가장 큰 변수, 최적화 대상) |
| T_setup | 다음 FF의 setup 요구 |
| T_skew | 클럭이 FF마다 도달 시각 차이 (CTS로 줄임) |
| T_jitter | PLL/전원 노이즈로 인한 에지 흔들림 |

**critical path를 깎는 일 = 최대 주파수를 올리는 일.** Physical Design 최적화의 1차 목표.

### 동기식 vs 비동기식

상용 EDA는 사실상 100% 동기식 가정. 비동기는 연구 영역. **본 프로젝트도 동기식 단일 도메인.**

### Skew vs Jitter

- **Skew (공간적)**: 같은 시점에서 FF마다 도달 시각이 다름. 원인: clock tree 와이어/버퍼.
- **Jitter (시간적)**: 같은 FF에서 에지가 흔들림. 원인: PLL·전원 노이즈.

## 프로젝트에서 마주칠 출력

| 개념 | 어디 |
|------|-----|
| Setup/Hold slack | OpenSTA `.slack`, `.violation` |
| Critical path | `report_checks -path_delay max` |
| Clock skew | P&R의 CTS(clock tree synthesis) 결과 |
| f_max | Gemmini DSE 탐색 공간 50/100/200 MHz |
| CDC | 본 프로젝트 단일 도메인이라 우선 생략 |

## 프로젝트 적용 지점

- **STA (Phase C3)**: 위 부등식을 모든 path에 자동 검사. OpenROAD/Yosys 내장.
- **주파수 선택**: 50 MHz=여유↑·전력↓, 200 MHz=critical path 압박↑·면적/전력↑ → Pareto.
- **Power model**: 동적 전력 ∝ f → `power_mw` 메트릭 직접 영향 ([[cmos-fundamentals]]).
- **Floorplan**: CTS skew 최소화가 높은 f_max의 필수 조건.

## 교차 참조

- [[digital-logic-gates]] — FF가 타이밍 분석의 단위 노드
- [[fsm-and-pipeline]] — 파이프라인은 critical path를 설계적으로 깎는 1차 수단
- [[cmos-fundamentals]] — 동적 전력의 `f` 변수
- [[phase-0-eda-operator-lens]] — Phase 0 학습 정책

## Source

- 원본: `raw/sessions/phase-0-a3-clock-timing.md` (2026-04-18 reviewed)
- 외부: OpenSTA (https://github.com/parallaxsw/OpenSTA), Harris & Harris 3.5장
