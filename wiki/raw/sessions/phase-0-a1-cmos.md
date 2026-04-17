---
phase: 0
branch: A
code: A1
title: 트랜지스터·CMOS
date: 2026-04-17
status: reviewed
confidence: high
---

# A1. 트랜지스터·CMOS

## 학습 목표

- MOSFET이 "전자 스위치"로 동작하는 원리 이해
- CMOS = NMOS + PMOS 쌍이 **저전력의 핵심**인 이유
- "sky130A"의 **130nm**가 의미하는 것
- 누설전류(leakage)가 현대 반도체의 핵심 제약인 이유

## 핵심 설명 (assistant)

### 1. 트랜지스터 = 전자 수도꼭지

MOSFET은 단자 3개(Gate, Source, Drain)가 있는 소자다. Gate에 전압을 걸면
Source↔Drain 사이에 전자가 흐를 수 있는 **채널(channel)**이 열린다.
전압을 빼면 채널이 닫혀 전류가 막힌다. 즉 "전압으로 제어하는 스위치"다.
이걸 나노미터 단위로 수억~수백억 개 집적한 것이 현대 칩.

### 2. NMOS와 PMOS — CMOS의 핵심

- **NMOS**: 전자가 운반체. Gate에 High(전압)를 걸면 ON.
- **PMOS**: 정공(hole)이 운반체. Gate에 Low를 걸면 ON.

두 종류를 **쌍(pair)**으로 쓰면 어느 한쪽만 ON이므로 VDD(전원)에서 GND(접지)로
직접 관통하는 전류가 **거의 0**이 된다. 이게 **CMOS = Complementary MOS**의 핵심이다.
NMOS만 쓰던 1970년대 칩은 항상 전류가 새어 매우 뜨거웠다. CMOS 도입으로
집적도·저전력이 동시에 가능해졌고, 이게 오늘날 반도체 혁명의 물리적 기반.

### 3. "sky130"의 130 — 공정 노드

**130은 게이트 길이(전자가 지나는 통로의 짧은 쪽)가 130 나노미터**였다는 뜻이다.
숫자가 작을수록 트랜지스터가 작고 빠르며 집적도가 높다. 현대 상용은 3nm·2nm까지 내려왔다.
**하지만 130nm는 오픈 PDK(SkyWater)로 풀려 있어**, 교육·연구·Tiny Tapeout에서 실제 실리콘까지
도달할 수 있는 유일한 현실적 선택지다. 이 프로젝트가 sky130A를 쓰는 이유.

### 4. 전력의 3가지 성분 & 누설전류

칩 전력은 크게 세 가지로 나뉜다:

- **동적(스위칭) 전력**: 실제 0↔1 전환 시 캐패시턴스를 충·방전하며 소비. ~f·C·V²
- **단락 전류**: 전환 순간 NMOS·PMOS가 동시에 잠깐 켜지며 흐르는 작은 전류
- **누설 전력(leakage)**: 트랜지스터가 **꺼진 상태에서도** 새는 전류

공정이 작아질수록 누설이 지배적이 되어 **"전력벽(power wall)"**에 부딪힌다.
이게 DL 가속기가 INT8·저전압을 추구하는 뿌리 이유 — 저정밀로 스위칭 활동을
줄이고, 누설이 적은 영역에서 동작시켜 **에너지당 연산(ops/J)**을 극대화하려는 것.

## 이 프로젝트와의 연결

- **PDK 선택 (spec §10)**: sky130A는 오픈 130nm이라 테이프아웃·교육 경로 확보. gf180mcu(180nm)는 옵션.
- **전력 메트릭 (spec §11.2의 `power_mw`)**: OpenROAD의 power 추정은 위 3가지 성분을 다 합친 값.
- **저정밀 precision (Gemmini 탐색 공간의 `inputType: SInt(8)`)**: 스위칭 활동 감소 → 동적 전력 감소.
- **주파수 선택 (50/100/200 MHz)**: 주파수↑ = 동적 전력↑. Pareto frontier에서 곡선을 그리는 이유.

## Q&A

### Q1. (user) 2nm 공정은 누설을 어떻게 해결했어?

A. (assistant) 세 층위에서 동시에 해결.

**트랜지스터 구조**
- **GAA/Nanosheet**: FinFET(3면 제어)을 넘어 채널 4면 전체를 게이트가 감싸는 구조.
  게이트 제어력 극대화 → subthreshold leakage 크게 감소. TSMC N2, Samsung SF2, Intel 18A가 모두 채택.
- **High-k Metal Gate**: 게이트 유전체를 HfO₂ 등 high-k 소재로 바꿔 gate leakage 억제
  (물리 두께는 두껍지만 전기적 효과는 얇게).

**회로·전력 설계**
- **Multi-Vt 셀**: High-Vt(누설↓, 느림) / Low-Vt(빠름, 누설↑) 등 동일 기능 셀을 여러 Vt로 제공.
  타이밍 크리티컬 경로만 LVT, 나머진 HVT로 합성기가 자동 배치.
- **Power Gating**: 미사용 블록은 sleep transistor로 VDD를 끊어 누설 자체를 차단.
- **Body Biasing**: 기판 전압 조절로 Vt를 동적으로 올려 누설 감소.

**시스템 레벨**
- **Backside Power Delivery (BSPDN, 2nm 신기술)**: 전원 배선을 웨이퍼 뒷면으로 이동.
  IR drop 감소 → VDD 추가 인하 가능 (누설은 V에 지수적이므로 효과 큼).
- **DVFS / 클럭 게이팅 / near-threshold computing**: 활동률·전압·주파수를 워크로드에 맞춰 축소.

**이 프로젝트와의 관계**: sky130(130nm)은 누설보다 **동적 전력**이 지배적.
2nm 기법 대부분은 PDK/셀 라이브러리에 내장된 것이라, 우리가 설계 단계에서 고를 수 있는 건
**Multi-Vt 셀 선택, 클럭 게이팅, 주파수 조절** 정도. Gemmini DSE 탐색 공간이 이 범위로 좁혀지는 근거.

## 참고 자료

- SkyWater sky130 PDK: https://skywater-pdk.readthedocs.io
- Weste & Harris, "CMOS VLSI Design" (정식 교과서, 해당 장)
- Wikipedia: MOSFET, CMOS (빠른 확인용)

## 학습 종료 체크

- [x] 사용자가 "이해됨" 확인
- [x] curriculum 체크리스트 업데이트
- [x] 세션 파일 커밋
