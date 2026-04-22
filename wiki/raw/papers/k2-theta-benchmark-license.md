---
type: raw-import
axis: theta
title: "K2 축별 자료 — MLPerf Tiny v1.3 streaming + License & provenance"
date: 2026-04-22
phase: K2
curator: claude-opus-4-7
source_count: 14
intent: "L3 벤치마크 구체화 (MLPerf Tiny v1.3 streaming wakeword harness detail) 및 §13 License & Provenance Gate 통과 준비 (NVDLA license 현실 검토, Gemmini BSD3 파생권, open PDK shuttle 2026 현황 — Efabless 셧다운 후 대체 경로)."
status: collected
confidence: low
last_verified: 2026-04-22
tags: [k2, benchmark, license, shuttle-path, open-source-impl, legal]
---

# θ. MLPerf Tiny v1.3 Streaming + License & Provenance — K2 Resource Survey

Spec anchors: §3.2 (`provenance_uri` on L1.run bundle) · §5.3 (H1c alt-benchmark) · §11 (Efabless 대체 경로 risk) · §13 (License & Provenance Gate).

## Resources

### 1. MLPerf Tiny v1.3 Technology Announcement (2025-09-17)
- URL: https://mlcommons.org/2025/09/mlperf-tiny-v1-3-tech/
- Tag: [benchmark, critical-read]
- WHAT: v1.3의 핵심 신규는 **streaming wakeword ("Marvin") 태스크**로, MCU-based interface board를 통해 audio 입력과 GPIO 검출 출력이 동기식으로 실시간 전달된다. 20분 합성 오디오 안에 Marvin 50회 + MUSAN noise, 1D time-separable DS-CNN 기준 FN ≤ 7로 정의. v1.2의 단발 clip KWS와 달리 **continuous duty-cycle + energy**가 1차 지표 — low-power idle/wake-up 거동까지 측정된다.

### 2. MLPerf Tiny v1.3 Results Round (2025-09)
- URL: https://mlcommons.org/2025/09/mlperf-tiny-v1-3-results/
- Tag: [benchmark, recent-SOTA]
- WHAT: 5개 벤치마크 70 submission. 확인된 제출처는 **Qualcomm · STMicroelectronics · Syntiant** (Bosch/Renesas는 이번 라운드 미확인 — K1-γ의 기존 기술 보도 추정은 v1.2 기준). streaming wakeword에 대한 첫 공식 reference power 수치가 이 라운드에서 공개 — 우리의 baseline은 여기에 정렬해야 한다.

### 3. mlcommons/tiny_results_v1.3 Repository
- URL: https://github.com/mlcommons/tiny_results_v1.3
- Tag: [benchmark, open-source-impl, critical-read]
- WHAT: v1.3 공식 결과 + submission artifacts 저장소. `closed/` submitter 디렉토리 구조, systems_under_test, measurement logs 포함. Gemmini 제출을 흉내내려면 이 repo의 디렉토리 컨벤션을 그대로 따라야 한다.

### 4. mlcommons/tiny Benchmark Suite (harness)
- URL: https://github.com/mlcommons/tiny
- Tag: [benchmark, open-source-impl]
- WHAT: Streaming harness는 `benchmark/streaming_wakeword/` 하위에 신규 디렉토리로 들어옴 — 기존 `benchmark/{kws,vww,ic,ad}/` 4태스크와 병렬 배치. EEMBC EnergyRunner 연동 포인트 동일. Gemmini 측은 이 harness의 GPIO/UART synchronous protocol에 맞춰 wrapper firmware를 붙여야 한다.

### 5. UCB-BAR Gemmini LICENSE (BSD 3-Clause)
- URL: https://github.com/ucb-bar/gemmini/blob/master/LICENSE
- Tag: [license-data, critical-read]
- WHAT: Regents of UC BSD 3-Clause — copyright notice + disclaimer retention만으로 파생물 공개·상용 재배포 모두 허용. Endorsement 금지 조항 외 실질 제약 없음. 우리의 generated RTL은 BSD3을 상속해 공개 저장소에 그대로 배포 가능.

### 6. Chipyard Umbrella LICENSE (Apache 2.0)
- URL: https://github.com/ucb-bar/chipyard/blob/main/LICENSE
- Tag: [license-data]
- WHAT: Chipyard 본체 Apache 2.0 + submodule로 BSD3(Gemmini, Rocket-Chip), CHIPS Alliance 하위 모듈들. 파생 배포 시 **NOTICE 파일에 변경 사항 기재** + 각 submodule LICENSE 보존 필요. 연구 논문 artifacts에서 "Uses Gemmini (BSD-3) / Chipyard (Apache-2.0)" 라인을 README에 못박는다.

### 7. NVDLA Open NVDLA License v1.0
- URL: https://nvdla.org/license.html
- Tag: [license-data, legal, critical-read]
- WHAT: NVIDIA 자체 작성 커스텀 라이선스 — BSD/Apache/Prosperity 어느 것도 아님. Royalty-free patent + copyright 부여하나 **"retain all original notices"** 조항과 patent grant의 contribution 결속이 BSD3/Apache2와 clean하게 결합하지 않는다. §13 License Gate에서 **NVDLA 산출물은 public corpus에서 분리**해야 하는 근거. 공식 호환성 매트릭스 없음.

### 8. NVDLA Project Activity 2025-2026
- URL: https://github.com/nvdla
- Tag: [legal, open-source-impl]
- WHAT: nvdla.org와 GitHub org 모두 "접근 가능"하나 upstream commit은 수년 정지 상태 — K1-γ의 "frozen but usable baseline" 평가와 일치. 라이선스 호환 재구현/포크 공식 확인 없음. 학술적으로는 arXiv 2508.16095 등 2025 사용 사례 존재하지만 대부분 아키텍처 참조이지 RTL 재배포가 아님. **우리 프로그램은 NVDLA를 2차 비교군으로도 채택하지 않는 쪽이 §13 통과에 안전**.

### 9. Efabless Shutdown & Alternative Path Mapping
- URL: https://www.zerotoasiccourse.com/post/excited_by_silicon/
- Tag: [shuttle-path, critical-read]
- WHAT: 2025-02 Efabless 셧다운 이후 sky130 루트는 **ChipFoundry.io + Cadence Academic Network**로, gf180mcu는 **wafer.space**로, 130nm 유럽은 **IHP SG13G2**로 분산 회복. Tiny Tapeout이 세 경로 모두에 인프라를 포팅 중. 단일 turnkey는 사라졌고, shuttle 캘린더 추적이 우리 program rule에 추가되어야 한다.

### 10. ChipFoundry.io Shuttle (sky130)
- URL: https://chipfoundry.io
- Tag: [shuttle-path]
- WHAT: 2026년 사실상의 sky130 MPW 상업 운영자. CI2605 (tapeout 2026-05-13 / delivery 2026-10-28), CI2609 (2026-09-16 / 2027-03-03) 확인. **단가 $14,950/tapeout**, 100 QFN + eval board + bare die 포함. Iter 3+ 실리콘 옵션의 default candidate.

### 11. wafer.space (gf180mcu 경로)
- URL: https://wafer.space
- Tag: [shuttle-path]
- WHAT: Swiss Chips/Tillitis 컨소시엄 자금으로 Tiny Tapeout을 gf180mcu에 포팅 중. 2025 말~2026 초 첫 shuttle 가동 확인, sky130/IHP도 병행 지원. **스케줄형 (on-demand 아님)**. Efabless 공백 중 gf180 유일한 소규모 공급자.

### 12. IHP SG13G2 Open PDK + MPW
- URL: https://github.com/IHP-GmbH/IHP-Open-PDK
- Tag: [pdk, shuttle-path]
- WHAT: IHP Microelectronics(독일)의 **130nm SiGe BiCMOS open PDK**. `TO_Apr2025`, `TO_May2025` 등 공식 MPW 저장소로 shuttle 운영 — 후자는 "Experimental open-source Tiny Tapeout for IHP SG13G2" 즉 IHP25a 라인. 라이선스 파일 명시 미흡 ("fully open source" 표방) — §13에서 실제 LICENSE 확인이 **open question**으로 열려야 한다. 유럽 학술 경로.

### 13. open_pdks — sky130A / gf180mcuD (CHIPS Alliance 2023~)
- URL: https://github.com/RTimothyEdwards/open_pdks
- Tag: [pdk, critical-read]
- WHAT: Tim Edwards 유지 PDK installer — 우리의 Nix bundle이 의존. SkyWater 자체 PDK는 여전히 "experimental preview" (sky130_release_0.0.4a 계열), Google 경고문 유지. **2026-01 IonQ → SkyWater 인수 발표**로 거버넌스 장기 전망은 불확실 — CHIPS Alliance 호스팅 자체는 계속. sky130A commit hash를 provenance.yaml에 고정해야 하는 이유.

### 14. SLSA Provenance + SPDX SBOM — hardware artifact 적용 선례
- URL: https://slsa.dev/blog/2022/05/slsa-sbom
- Tag: [foundational, legal]
- WHAT: SLSA(build provenance) + SPDX(component inventory)의 조합이 소프트웨어 쪽 표준. **하드웨어 전용 SBOM 표준은 2026 시점 미존재** — CHIPS Alliance/FOSSi에서 공식 작업 확인 불가. 실질 참고는 EdgeBit의 AWS Nitro Enclave 기반 SLSA L3 attestation. 우리 `provenance.yaml`은 이를 흉내내어 {tool SHAs, PDK commit, seed, license tags, corpus scope(public/private)} 필드를 수동 관리해야 한다 — 하드웨어용 표준이 없다는 것 자체가 본 프로그램의 process-novelty 후보.

## Landscape Snapshot

- **벤치마크 (L3 alt-bench 축)**: v1.3 streaming wakeword가 **확정된 up-to-date 타깃**. duty-cycle·energy가 1차 metric이므로, Gemmini의 "계산 강한 행렬곱" 프로파일에서는 idle power/clock-gating 구현이 ranking의 실질 차별자가 된다. 기존 spec이 언급한 v1.2 KWS 기준 수치는 폐기하고 v1.3 harness에 맞춰 재도출해야 한다.
- **라이선스 매트릭스 (§13 Gate)**:
  - Gemmini BSD-3 + Chipyard Apache-2.0 조합은 공개 배포 clean. 요구사항은 **NOTICE 파일 + submodule LICENSE 보존** 수준.
  - **NVDLA는 §13에서 분리된 corpus로 격리**하는 것이 안전 — 자체 라이선스가 BSD/Apache와 호환 증명이 없고 upstream frozen이라 법적·유지보수 양면 리스크.
  - IHP SG13G2 PDK LICENSE 파일 명시 미흡은 **open issue** — program에 진입하면 §13 통과 전 확인 필요.
- **Shuttle 경로 (§11 risk)**: Efabless 공백은 ChipFoundry(sky130, $14,950) · wafer.space(gf180) · IHP(SG13G2, 유럽) 셋으로 분산 회복. **Iter 3 실리콘은 ChipFoundry를 default, wafer.space를 secondary로** 가정하고 shuttle 캘린더 tracking을 program/에 고정 규칙으로 추가하는 것이 현실적이다.
- **Provenance**: hardware SBOM 표준 부재 — 우리의 `provenance.yaml`은 self-defined 스키마로 시작해야 하며, 이 포맷 자체를 **process novelty claim**의 일부로 프레이밍 가능하다.

## Caveats / Unverified

- Bosch/Renesas의 v1.3 submission 여부는 퍼플렉시티 응답에 미확인 — 공식 results CSV로 교차검증 필요.
- IHP SG13G2 PDK의 정확한 SPDX identifier (Apache-2.0 추정, 그러나 공식 LICENSE 파일 확인 미완).
- wafer.space 공식 URL은 본 조사에서 확정적 답변 부재 — "wafer.space" 도메인 추정 기재. 1차 접속으로 교차검증 필요.
- Cadence Academic Network sky130 shuttle은 public URL/초대제 여부 미확인 — §11에 open question으로 남긴다.
- IonQ-SkyWater 인수(2026-01 발표, 2026 Q2/Q3 closing 예상)가 sky130 거버넌스에 미칠 영향 — 현 시점 program risk로 모니터만.
