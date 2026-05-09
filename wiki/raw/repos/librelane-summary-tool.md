---
type: raw-source-summary
axis: c-eda-flow
title: "librelane_summary — Matt Venn's LibreLane output browser"
date: 2026-05-09
status: collected
confidence: high
last_verified: 2026-05-09
curator: claude-opus-4-7 (exa.ai web_fetch via zero-to-asic-course)
source_url: https://github.com/mattvenn/librelane_summary
context_url: https://www.zerotoasiccourse.com/post/librelane_output_files/
collection_method: exa.ai web_fetch_exa (제3자 발견 — perplexity 인용 #20)
tags: [librelane, summary-tool, repo, operator-tool, mattvenn, zero-to-asic]
---

# librelane_summary — operator-utility 발견

LibreLane flow 결과 디렉토리를 browse·요약하는 CLI tool. Matt Venn(Tiny Tapeout/Zero-to-ASIC Course 운영자)이 maintain.

## 기능

- **결과 디렉토리 picker**: 다중 run 중 specific result 선택
- **Violation summary**: 각 stage의 위반 한 줄 요약
- **Antenna issue summary**: antenna rule 별 도식화
- **Standard cell usage**: 전체 design의 cell type histogram
- **Stage 시각화**: floorplan / PDN / placement / final GDS 각 단계 layout 미리보기

## 출처 맥락

`https://www.zerotoasiccourse.com/post/librelane_output_files/` (2021-04-16, 2025 갱신) 게시글에서 함께 언급. 동 게시글의 spreadsheet도 LibreLane output 파일별 의미 + 어떤 도구가 어떤 파일을 만드는지 매핑 (2025 LibreLane 기준 갱신).

## 본 프로젝트와의 연결

- **Phase 0 C branch (EDA Flow)**: violation/antenna 빠른 점검의 referenced tool. 본 프로젝트 Tool plane 후보(현재는 wrapper 직접 작성).
- **L2 substrate**: agent가 LibreLane output dir에서 metric을 추출할 때 본 tool의 출력 형식이 typed-memory schema 후보.
- **K1-γ evidence**: open-source EDA stack에서 reproducibility tool 부족 영역 — 본 tool이 부분 채우는 위치.

## Caveats

- 본 raw는 도구 발견 노트만. tool 본체 (코드, README) 본문은 미수집 — 도구 채택 결정 시 별도 fetch 필요.
- 2021 첫 게시 후 2025 갱신 — 현재 latest commit 시점은 GitHub direct check 필요.
- LibreLane 3.0.2 immutable state 구조와 호환 여부 미확인.
