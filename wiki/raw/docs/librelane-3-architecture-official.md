---
type: raw-source-summary
axis: c-eda-flow
title: "LibreLane 3.0.2 Architecture (official)"
date: 2026-05-09
status: collected
confidence: high
last_verified: 2026-05-09
curator: claude-opus-4-7 (exa.ai web_fetch)
source_url: https://librelane.readthedocs.io/en/latest/reference/architecture.html
collection_method: exa.ai web_fetch_exa (5000 char cap)
tags: [librelane, architecture, immutable-state, sequential-flow, official-docs]
---

# LibreLane 3.0.2 Architecture — Official Reference

> Source: LibreLane Documentation, "Architectural Overview" page. **Authoritative**.

## Core 4-module 구조

LibreLane은 Python module:

- `librelane.flows` — Flow 정의·실행
- `librelane.steps` — Step 추상 base + 구현
- `librelane.config` — Configuration 클래스 + Builder
- `librelane.state` — State + DesignFormat
- `librelane.common` (assisting) — 공용 utility

CLI / Python script / Jupyter Notebook에서 호출 가능.

## State (snapshot)

`librelane.state.State` = 시점 t의 design view 모음.

- key: `librelane.state.DesignFormat` (Netlist, DEF, GDS 등)
- value: `librelane.config.Path` 또는 N-nested dict (leaf=Path)
- attribute: **metrics** — design statistics dict (모든 step이 read/write)

## Step (atomic execution unit)

각 Step:
- 입력: Configuration object + State
- 출력: 새로운 State (modified/new artifacts + metrics)

### **5 strict 원칙 (LibreLane 공식)**

1. **In-place 수정 금지** — 새 파일은 step 전용 디렉토리에 생성. 도구가 in-place만 지원하면 copy 후 수정.
2. **config_in 수정 금지** — programmatic하게 enforce.
3. **External filesystem path 의존 금지** — config나 input state에 없으면 존재하지 않는 것. 반대로 step 디렉토리 외부에 파일 생성도 금지.
4. **PRNG seed 고정** — 재현성. config variable로 노출 가능.
5. **결정성 원칙**: same step + same input config + same input state → same output (LibreLane 동일 버전 기준).

> **Acceptable break**: timestamp in views, file path 등 완전 deterministic 불가능한 측면.

`librelane.steps.Step` 추상 base class.

## Flow

여러 Step을 묶어 design goal 달성 (e.g., RTL → GDSII).

`librelane.flows.Flow` abstract base class.

### SequentialFlow

가장 흔한 subclass. Step을 순차 실행:

```
State_i = Step_i(State_{i-1}, Config)
```

- 같은 Config가 모든 step에 전달
- consecutive states로 연쇄
- n-step flow의 final = State_n

**Default flow**: `Classic` (CLI 실행 시) — OpenLane 기반 RTL→GDSII.

## Configuration

### Object

- 검증된 dict of values
- Flow의 config variable = 포함 step 모두의 union
- 지원 type: scalar (`float` 제외), `Decimal`, `List`, `Dict` (List/Dict 무한 nest)
- Step에 input으로 전달

### Builder

`Flow + raw config → librelane.config.Config (validated, immutable string dict)`

raw config 입력 형식:
- Python dict
- JSON file path
- YAML file path
- Tcl file path

Builder 작업: validation, path resolution, type fix.

## Operator 함의

| 원칙 | Operator 행위 변화 |
|------|---------------------|
| State immutability | 어느 step output이든 inspect 가능 — flow 중단 후 재시작 trivial |
| metric in State | metrics.csv post-process가 아니라 step 직후 즉시 readable |
| Config immutability | 동일 config 재실행 = 동일 결과 (CI/CD 단순화) |
| 5 strict 원칙 | 도구가 임의 파일 수정한 흔적 발견 시 Step 구현 버그 의심 |
| SequentialFlow 함수형 | 임의 stage에서 fork 가능 — `Configuration::derive()` 패턴으로 분기 실험 |

## OpenLane 2.x 대비 핵심 차이

OpenLane 2.x는 Tcl 전역 + 파일system 의존. LibreLane 3.0.2:
- State first-class object
- metrics 직접 기록
- step functional purity 보장
- intermediate state 항상 readable
- 재실행/branch trivial

## Caveats

- exa.ai 5000 char cap로 fetch — 전체 문서의 architectural overview만 확보. Step/Flow/Config의 API stability policy, plugin 시스템, custom step 작성법은 미수집 (해당 페이지: `librelane.api`, `Writing Custom Steps`).
- 본 raw는 LibreLane 공식 문서 latest 기준 — 3.0.2 정확한 changelog는 https://github.com/librelane/librelane/blob/main/Changelog.md 참조.
