---
title: "CMOS Fundamentals"
type: concept
tags: [phase-0, cmos, pdk, power, sky130]
status: active
confidence: high
created: 2026-05-09
updated: 2026-05-09
sources: [raw/sessions/phase-0-a1-cmos.md]
---

# CMOS Fundamentals

MOSFET이 "전압으로 제어하는 스위치"라는 사실에서 출발해, 본 프로젝트가 sky130A를 쓰는 근거와 전력 메트릭의 출처까지 한 줄로 잇는 페이지.

## 핵심 정리

- **MOSFET = 전자 수도꼭지** — Gate 전압이 Source↔Drain 채널을 열고 닫는다. 나노미터 단위로 수억 개 집적된 것이 현대 칩.
- **CMOS = NMOS + PMOS pair** — 항상 한 쪽만 ON이라 VDD↔GND 관통 전류가 거의 0. 1970년대 NMOS-only 대비 저전력·고집적의 물리적 기반.
- **공정 노드 "130nm"** — Gate 길이를 의미. 작을수록 빠르고 집적도↑. 130nm는 [SkyWater PDK](https://skywater-pdk.readthedocs.io)로 오픈된 **유일한 현실적 테이프아웃 경로**.
- **전력 3성분** — 동적(`f·C·V²`) / 단락 / 누설. 공정 미세화↓ → 누설 지배적 → "power wall" → DL 가속기가 INT8·저전압으로 도피.

## 프로젝트 적용 지점

| 지점 | 어디서 보이나 |
|------|---------------|
| PDK 선택 (sky130A vs gf180mcu) | spec §10 |
| `power_mw` 메트릭 | OpenROAD power 추정 (3성분 합) |
| 저정밀 precision | Gemmini 탐색 공간 `inputType: SInt(8)` (스위칭 활동 감소) |
| 주파수 50/100/200 MHz | Pareto frontier의 동적 전력 ∝ f |

## 2nm 누설 대응 (Q&A 요약)

- **트랜지스터 구조**: GAA/Nanosheet (4면 게이트 제어), High-k Metal Gate
- **회로**: Multi-Vt 셀, Power Gating, Body Biasing
- **시스템**: BSPDN(Backside Power Delivery), DVFS, near-threshold

본 프로젝트(130nm)는 누설이 동적 전력보다 작으므로 **Multi-Vt 셀 / 클럭 게이팅 / 주파수 조절**만 설계 자유도. 이게 Gemmini DSE 탐색 공간이 좁혀지는 근거.

## 교차 참조

- [[digital-logic-gates]] — CMOS 게이트가 NAND/NOR/INV로 조합되는 다음 층
- [[clock-and-timing]] — 동적 전력의 `f` 변수와 STA의 연결
- [[phase-0-eda-operator-lens]] — Phase 0 학습 정책 진입점

## Source

- 원본: `raw/sessions/phase-0-a1-cmos.md` (2026-04-17 reviewed, confidence: high)
- 외부: SkyWater sky130 PDK 문서, Weste & Harris "CMOS VLSI Design"
