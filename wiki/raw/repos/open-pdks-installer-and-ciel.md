---
type: raw-source-summary
axis: f-pdk-formats
title: "open_pdks installer + ciel package manager (official)"
date: 2026-05-10
status: collected
confidence: high
last_verified: 2026-05-10
curator: claude-opus-4-7 (exa.ai web_fetch)
source_url: https://github.com/RTimothyEdwards/open_pdks
context_url: https://github.com/fossi-foundation/ciel
collection_method: exa.ai web_fetch_exa (4000 char cap)
tags: [open-pdks, ciel, volare, sky130, gf180mcu, ihp, pdk-installer]
---

# open_pdks + ciel — PDK Installation Substrate

> Source: GitHub `RTimothyEdwards/open_pdks` (official). 마지막 push: 2026-03-05. Apache-2.0. **Authoritative**.

## open_pdks가 하는 일

PDK builder. foundry source를 받아 EDA-tool-friendly 디렉토리 구조로 설치:
- `<pdk_name>/libs.ref/` — IP (cell library views: layout, abstract, netlist 등)
- `<pdk_name>/libs.tech/` — EDA tool setup (magic, netgen, qflow, openlane, klayout 등)

빌드 명령:
```bash
git clone https://github.com/RTimothyEdwards/open_pdks.git
cd open_pdks
./configure --prefix=/usr --enable-sky130-pdk \
            --enable-sram-sky130 --enable-sram-space-sky130 \
            --enable-reram-sky130
make
sudo make install
```

설치 결과: `/usr/share/pdk/sky130A`, `/usr/share/pdk/sky130B` (ReRAM 옵션). gf180mcu PDK는 `gf180mcuA/B/C/D` 4종 동시 설치 가능.

## ciel — pre-built PDK 패키지 매니저

**ciel** (구 volare). pip로 설치:

```bash
pip install ciel
ciel ls-pdks                                  # supported PDK family
ciel ls-remote --pdk-family=sky130            # 다중 commit hash 별 pre-built PDK
ciel enable --pdk-family=sky130 <commit-hash> # 설치 (~/.ciel/에)
export PDK_ROOT=~/.ciel
```

**본 프로젝트 함의**: lockfile.yaml의 SHA-pin 정책과 정확히 매칭 — ciel은 commit hash 단위 pre-built PDK를 호출. 빌드 시간(open_pdks `make`로는 1+ hour) 대신 분 단위로 reproducible PDK 확보. **L1 process spec의 PDK SHA-pin 메커니즘 후보**.

## Shuttle 현황 (2025-09 기준)

| Shuttle | PDK |
|---------|-----|
| Cadence | sky130A, sky130B |
| Chip Foundry | sky130A, sky130B (TT08/TT09 packaging 회복) |
| Wafer.Space | gf180mcuD |
| (IHP) | SG13G2 (별도 — 아래) |

## IHP SG13G2 — open_pdks 형식 사전 통합

IHP GmbH가 SG13G2 (European 130nm) PDK를 open_pdks 형식 그대로 release. 별도 빌드 불필요. **ciel로도 즉시 enable 가능**.

> **K1-γ Trigger 1 (Efabless 셧다운) 후속**: 대체 mesh의 European 130nm 옵션으로 IHP SG13G2가 즉시 사용 가능 — 본 프로젝트 Iter 3+ tape-out 경로 결정에서 sky130A 외 1순위 후보.

## sky130A vs sky130B 차이

- `sky130A`: standard
- `sky130B`: with ReRAM
- 본 프로젝트는 `sky130A` 단독 사용 (ReRAM 비활용).

## gf180mcu 4 변종

| 이름 | metal stack | top metal |
|------|-------------|-----------|
| gf180mcuA | 3 metal | — |
| gf180mcuB | 4 metal | — |
| gf180mcuC | 5 metal | 0.9 µm |
| **gf180mcuD** | 5 metal | 1.1 µm |

본 프로젝트 spec은 sky130A primary, gf180mcuD option (K1-γ).

## Repository 통계 (2026-03-05 기준)

- Stars: 406, Forks: 112
- 주요 언어: Python (63.9%), Tcl (22.2%), Makefile (6.5%), Verilog (5.9%)
- License: Apache-2.0
- 30 contributors. Top: RTimothyEdwards, ax3ghazy, agorararmard, kareefardi, donn (Efabless), …

## 본 프로젝트 적용 지점

| 지점 | 어디 |
|------|------|
| L1 process lockfile.yaml에 PDK SHA-pin 메커니즘 | ciel `commit-hash` 단위 enable |
| Iter 3+ tape-out 경로 (Efabless 후속) | Cadence sky130 / ChipFoundry sky130 / Wafer.Space gf180 / IHP SG13G2 |
| sky130A vs sky130B 결정 | spec §10 (현재 sky130A 단독) |
| 빌드 시간 vs 재현성 | ciel pre-built (분 단위) vs `make install` (1+ hour) |

## Caveats

- ciel 설치 시 `~/.local/bin/ciel` 위치 — `PATH`에 없으면 명시 호출 필요.
- 본 raw는 README + 첫 instructions만. configure flag 전체 (예: `--enable-reram-sky130` 외 다양한 옵션)는 `./configure --help` 직접 확인.
- ciel commit hash 명명 규칙(예: `0.0.0-369-g7198cf6` 같은 git describe 출력)은 별도 확인 필요 — lockfile.yaml 작성 시 cross-check.
