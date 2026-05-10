---
type: raw-source-summary
axis: f-pdk-formats
title: "SkyWater SKY130 Library Naming + 5 표준 셀 라이브러리 (official)"
date: 2026-05-10
status: collected
confidence: high
last_verified: 2026-05-10
curator: claude-opus-4-7 (exa.ai web_fetch)
source_url: https://skywater-pdk.readthedocs.io/en/main/contents/libraries.html
collection_method: exa.ai web_fetch_exa (4000 char cap)
tags: [sky130, libraries, naming-convention, fd-sc-hd, official-docs]
---

# SkyWater SKY130 Libraries — Official

> Source: SkyWater SKY130 PDK Documentation, "Libraries" page. **Authoritative**.

## Library 명명 규칙

```
<process>_<source>_<type>[_<name>]
```

모두 lowercase, underscore separator. 예: `sky130_fd_sc_hd`.

### Process
`sky130` — fixed (이 PDK는 항상 sky130).

### Library Source Abbreviation (3종)

| Source | 약어 |
|--------|------|
| The SkyWater Foundry | `fd` |
| Efabless | `ef` |
| Oklahoma State University | `osu` |

> **Efabless 셧다운 후속 (2025-02)**: `ef` prefixed 라이브러리는 maintenance 불확실 — 본 프로젝트는 `fd` 라이브러리만 사용 (K1-γ Trigger 1 정합).

### Library Type Abbreviation (5종)

| Type | 약어 |
|------|------|
| Primitive Cells | `pr` |
| Digital Standard Cells | `sc` |
| Build Space (Flash, SRAM) | `bd` |
| IO and Periphery | `io` |
| Miscellaneous | `xx` |

### Optional Library Name

같은 source/type 다중 library 시 구분. 본 프로젝트 기본 `sky130_fd_sc_hd`의 `hd`가 그 위치.

## SkyWater Provided Digital Standard Cell 라이브러리 (5종)

| 라이브러리 | 의미 |
|-----------|------|
| **`sky130_fd_sc_hd`** | **High Density** (본 프로젝트 기본) |
| `sky130_fd_sc_hdll` | High Density Low Leakage |
| `sky130_fd_sc_hs` | High Speed |
| `sky130_fd_sc_ls` | Low Speed |
| `sky130_fd_sc_ms` | Medium Speed |

> **본 프로젝트 함의**: Gemmini DSE 탐색 공간이 표준 셀 library 변종까지 확장될 가능성. K2 ζ에서 결정 예정. 현 spec은 `hd` 단독.

## 그 외 SkyWater 라이브러리

- **Foundry primitive libraries** (`pr` type) — 1.8V/3.0V/5.0V FET, 다양한 고전압 FET, 다이오드, BJT, SRAM, MiM/VPP 캐패시터, 저항.
- **Build Space libraries** (`bd` type) — memory compiler 등 specialized.
- **IO and Periphery**: `sky130_fd_io` (IO/periphery cells).

## 3rd-party 라이브러리 등록 기준

OSI approved license 하에 release 시 SKY130 PDK에 포함 가능. 기준 finalize는 PDK 측 TODO.

## 본 프로젝트 적용

- **명명 규칙 정합성**: 본 프로젝트의 모든 cell instance는 `sky130_fd_sc_hd__*` 패턴이어야 함. 다른 prefix 등장 = library mismatch (재합성 trigger).
- **library 변종 선택의 trade-off**:
  - `hd` ↔ `hs`: 면적 vs 속도
  - `hd` ↔ `hdll`: leakage 절감 (저전력 운영 영역, K1-α의 [[cmos-fundamentals]] 누설 논의)
  - L1 process spec에서 lockfile에 정확한 라이브러리 SHA-pin 필요.

## Caveats

- 본 페이지 fetch 시점의 PDK 버전: `0.0.0-369-g7198cf6`. 정확한 commit hash는 [open_pdks installer 페이지](raw/repos/open-pdks-installer-and-ciel.md) 참조.
- 4000 char cap으로 `Build Space libraries` `Foundry provided` 하위는 미수집 — SRAM/Flash compile 결정 시 별도 fetch.
- "Third party provided Digital Standard Cell Libraries"는 빈 항목으로 표시됨 (본 fetch 시점 미등록).
