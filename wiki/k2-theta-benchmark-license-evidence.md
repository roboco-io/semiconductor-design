---
title: "K2-θ: MLPerf Tiny v1.3 Streaming + License & Provenance — Direction Evidence"
type: synthesis
tags: [k2, mlperf-tiny, streaming-wakeword, license-gate, provenance, sbom, shuttle-path]
status: active
confidence: medium
created: 2026-05-10
updated: 2026-05-10
sources:
  - raw/papers/k2-theta-benchmark-license.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §3.2 provenance · §5.3 H1c · §11 risk · §13 License Gate
  - docs/superpowers/specs/2026-04-26-L3-content-design.md  # 본 evidence가 직접 backing
related_wiki:
  - raw/repos/open-pdks-installer-and-ciel.md  # ciel + sky130A SHA-pin
  - pdk-file-formats.md  # tape-out mesh
---

# K2-θ: MLPerf Tiny v1.3 + License & Provenance — Direction Evidence

본 프로젝트의 **L3 evaluation harness (MLPerf Tiny v1.3 streaming Marvin)** + **§13 License & Provenance Gate** + **Iter 3+ shuttle 경로** 14 source 종합. K1+K2 evidence 그래프의 마지막 페이지 — License Gate 통과 + 실측 baseline 정렬.

## Spec Direct Backing — 핵심 결정 5개

| 결정 | 본 페이지 evidence | spec anchor |
|------|---------------------|-------------|
| **MLPerf Tiny v1.2 → v1.3 uplift** | source #1 streaming Marvin 정의 | spec §11 metric ([[k1-gamma-opensource-eda-evidence]] Trigger 보강) |
| **NVDLA를 corpus에서 분리** | source #7+#8 NVDLA license 호환 불명 + upstream frozen | spec §13 License Gate |
| **Gemmini + Chipyard 공개 배포 clean** | source #5 BSD3 + #6 Apache-2.0 + NOTICE 보존 | spec §13 |
| **Iter 3+ shuttle: ChipFoundry default + wafer.space secondary + IHP 학술** | source #9~#12 mesh | spec §11 risk |
| **provenance.yaml self-defined 스키마 = process novelty 일부** | source #14 SLSA+SPDX prior + hardware SBOM 표준 부재 | spec §3.2 + §1 intent |

## Source 카테고리

### MLPerf Tiny v1.3 (4종)
- **v1.3 Tech Announcement** (2025-09-17, critical-read): **streaming Marvin** = MCU-based interface board, audio↔GPIO synchronous, 20분 합성 audio + Marvin 50회 + MUSAN noise, 1D time-separable DS-CNN baseline FN ≤ 7. **continuous duty-cycle + energy 1차 지표** (vs v1.2 단발 clip KWS).
- **v1.3 Results Round** (2025-09): 5 benchmark × 70 submission. 확인된 제출처 **Qualcomm · STMicroelectronics · Syntiant** (Bosch/Renesas는 v1.3 미확인 — K1-γ 추정은 v1.2 기준이었음). streaming wakeword 첫 공식 reference power.
- **mlcommons/tiny_results_v1.3 repo** (critical-read): `closed/` submitter dir, systems_under_test, measurement logs. **Gemmini 제출 흉내내려면 이 repo dir convention 그대로**.
- **mlcommons/tiny harness**: `benchmark/streaming_wakeword/` 신규 + 기존 `benchmark/{kws,vww,ic,ad}/` 4태스크 병렬. EEMBC EnergyRunner 동일. **Gemmini 측은 GPIO/UART synchronous wrapper firmware 필요**.

### License (4종)
- **Gemmini BSD 3-Clause** (Regents of UC, critical-read): copyright + disclaimer retention만으로 파생물 공개·상용 모두 허용. Endorsement 금지 외 실질 제약 없음. **generated RTL은 BSD3 상속해 공개 저장소 배포 가능**.
- **Chipyard Apache 2.0**: 본체 Apache-2.0 + submodule (Gemmini BSD3, Rocket-Chip BSD3, CHIPS Alliance) 보존. **NOTICE 파일에 변경 사항 기재 + 각 LICENSE 보존** 필요. 논문 README에 "Uses Gemmini (BSD-3) / Chipyard (Apache-2.0)" 못박기.
- **NVDLA Open NVDLA License v1.0** (critical-read): NVIDIA 자체 작성 — BSD/Apache/Prosperity 어느 것도 아님. Royalty-free patent + copyright but **"retain all original notices"**가 BSD3/Apache2와 clean 결합 불가. 공식 호환성 매트릭스 없음. **§13 통과 위해 NVDLA 산출물 분리 corpus 필수**.
- **NVDLA Activity 2025-2026**: nvdla.org + GitHub org 접근 가능하나 upstream commit 수년 정지. K1-γ "frozen but usable baseline" 평가와 일치. 학술 사용은 architecture reference (RTL 재배포 ✗). **2차 비교군에서도 채택 ✗가 §13 통과 안전**.

### Shuttle path (4종, 2025-02 Efabless 셧다운 후속)
- **Efabless 후속 mapping** (critical-read): sky130 → ChipFoundry + Cadence Academic / gf180 → wafer.space / 130nm 유럽 → IHP SG13G2. Tiny Tapeout 세 경로 모두 인프라 포팅 중. **단일 turnkey 사라짐 → shuttle 캘린더 tracking이 program rule로 추가**.
- **ChipFoundry.io** (sky130 default): 2026 사실상 sky130 MPW 상업 운영자. **단가 $14,950/tapeout** + 100 QFN + eval board + bare die. 확인 schedule: CI2605 (tapeout 2026-05-13 / delivery 2026-10-28), CI2609 (2026-09-16 / 2027-03-03).
- **wafer.space** (gf180mcu): Swiss Chips/Tillitis 컨소시엄 자금. Tiny Tapeout을 gf180mcu에 포팅 중. 2025 말~2026 초 첫 shuttle. sky130/IHP 병행. **스케줄형(on-demand 아님)**, gf180 유일 소규모 공급자.
- **IHP SG13G2 Open PDK** (학술 유럽): IHP Microelectronics(독일) **130nm SiGe BiCMOS**. `TO_Apr2025`, `TO_May2025` MPW 저장소. 후자 = "Experimental open-source Tiny Tapeout for IHP SG13G2"(IHP25a 라인). **LICENSE 파일 명시 미흡 — §13 open question**. 유럽 학술 경로. 본 페이지의 `raw/repos/open-pdks-installer-and-ciel.md`에서 사전 ciel 통합 확인.

### PDK governance (1종)
- **open_pdks** (Tim Edwards, critical-read): 본 프로젝트 Nix bundle 의존. SkyWater 자체 PDK 여전히 "experimental preview" (sky130_release_0.0.4a) + Google 경고. **2026-01 IonQ → SkyWater 인수 발표** (2026 Q2/Q3 closing 예상)로 거버넌스 장기 전망 불확실 — CHIPS Alliance 호스팅은 계속. **sky130A commit hash를 provenance.yaml에 고정 이유**.

### Provenance / SBOM (1종)
- **SLSA + SPDX SBOM** (foundational): SW SLSA (build provenance) + SPDX (component inventory) 조합이 표준. **하드웨어 전용 SBOM 표준은 2026 미존재** — CHIPS Alliance/FOSSi 공식 작업 확인 불가. 실질 참고는 EdgeBit AWS Nitro Enclave SLSA L3 attestation. **본 프로젝트 `provenance.yaml`이 self-defined 스키마로 시작 → 이 포맷 자체가 process-novelty 후보**.

## 본 프로젝트와의 연결 (Direction Evidence)

### L3 Open-Ideation 평가 plane (MLPerf Tiny v1.3)

| 항목 | 본 페이지 결정 |
|------|----------------|
| 평가 metric | duty-cycle + energy (v1.3 streaming Marvin 1차 지표) |
| baseline | 공식 reference power v1.3 라운드 (2025-09 Qualcomm/STMicro/Syntiant) |
| Gemmini 제출 dir convention | `closed/<submitter>/<system>/` (mlcommons/tiny_results_v1.3 그대로) |
| Gemmini wrapper firmware | streaming harness GPIO/UART synchronous 대응 |
| Gemmini 차별자 | **idle power / clock-gating 구현** ([[cmos-fundamentals]] 누설 영역의 직접 응용) — 계산 강한 행렬곱 profile에서는 idle 거동이 ranking 결정 |

### §13 License Gate 통과 체크리스트

- ✅ Gemmini BSD3 + Chipyard Apache 2.0 조합 = clean
- ✅ NOTICE 파일에 변경 사항 + 각 submodule LICENSE 보존
- ✅ README 라인: "Uses Gemmini (BSD-3) / Chipyard (Apache-2.0)"
- ❌ **NVDLA 분리** — 2차 비교군도 X (corpus 격리)
- 🟡 **IHP SG13G2 LICENSE 확인** — open issue, program 진입 전
- 🟡 IonQ-SkyWater 인수 영향 — 현재 monitor only

### Iter 3+ shuttle 경로 (§11 risk)

| Path | 사용 시점 | 상태 |
|------|-----------|------|
| **ChipFoundry sky130** ($14,950/tapeout) | Iter 3 default | 2026 commercial operator, schedule 확인됨 |
| wafer.space gf180mcu | secondary | 2025 말~2026 초 첫 shuttle, 스케줄형 |
| IHP SG13G2 (유럽 학술) | tertiary | LICENSE 확인 후 |
| Cadence Academic sky130 | URL/초대제 미확인 | open question |

### `provenance.yaml` 스키마 (process novelty 일부)

source #14 SLSA+SPDX prior 위에 본 프로젝트가 hardware SBOM 표준 부재를 메우는 self-defined:

```yaml
provenance:
  tools:
    - librelane: <commit-hash>
    - openroad: <commit-hash>
    - yosys: <commit-hash>
  pdk:
    - sky130A: <ciel commit-hash>     # ← K2-ζ + ciel 통합
  accelerator:
    - chipyard: 69eba86
    - gemmini: <commit-hash>
  seeds:
    - rtl_gen_seed: <int>
    - mutation_seed: <int>
  license_tags: [BSD-3, Apache-2.0]
  corpus_scope: public                  # ← NVDLA 격리
  build_attestation: <SLSA L3 hash>
```

이 스키마 자체가 spec §3.2 (`provenance_uri`)의 구체화 + spec §1 intent (process novelty) 직접 산출.

## Caveats / 미해결 (open issue)

- **Bosch/Renesas v1.3 submission**: 공식 results CSV로 교차검증 필요.
- **IHP SG13G2 SPDX identifier**: Apache-2.0 추정, 공식 LICENSE 파일 확인 미완.
- **wafer.space 공식 URL**: 본 조사에서 확정적 답변 부재 — 1차 접속으로 cross-check.
- **Cadence Academic Network sky130 shuttle**: public URL / 초대제 여부 미확인.
- **IonQ-SkyWater 인수 영향**: 2026 Q2/Q3 closing 예상 — sky130 거버넌스 monitor only.
- **하드웨어 SBOM 표준 부재**: 본 프로젝트 self-defined 스키마가 고립된 표준이 될지, 후속 표준화에 기여할지는 결과 평가 후.

## 교차 참조

- [[k1-gamma-opensource-eda-evidence]] — MLPerf Tiny v1.2 → v1.3 갱신 trigger의 1차 출처. 본 페이지가 v1.3 detail로 확장.
- [[k1-alpha-llm-for-hdl-evidence]] — CVDP-agentic 34% novelty seam ↔ MLPerf Tiny v1.3 streaming의 평가 plane 매핑.
- [[k1-beta-agentic-eda-evidence]] — agent reward 신호로 v1.3 duty-cycle/energy 사용.
- [[k1-delta-research-memory-evidence]] — provenance.yaml 자체가 K1-δ "negative-result recall" + audit trail의 hardware 영역 구체화.
- [[k2-epsilon-graph-quality-judge-evidence]] — HELM-style metric plane 분리가 v1.3 평가 plane과 정합.
- [[k2-zeta-l1-runtime-evidence]] — L1 lockfile.yaml의 SHA-pin이 본 페이지 provenance.yaml에 직접 흡수.
- [[k2-eta-patch-mutation-evidence]] — structural transform 카탈로그가 v1.3 차별자(idle power/clock-gating)에 어떻게 작용하는지 검증.
- [[pdk-file-formats]] — sky130A + IHP + gf180 mesh 정합.
- [[cmos-fundamentals]] — 누설 영역의 idle power/clock-gating 구현이 v1.3 차별자.
- [[fsm-and-pipeline]] — Gemmini systolic의 idle 거동 = clock-gating 적용 단위.
- [[clock-and-timing]] — 동기 GPIO/UART harness 정합.

## Source

- 원본: `raw/papers/k2-theta-benchmark-license.md` (2026-04-22 collected, 14 sources, confidence: low → spec 채택 시 high)
- decision_anchors: `raw/imports_manifest.yaml`
- 직접 backing: `docs/superpowers/specs/2026-04-26-L3-content-design.md` (L3 content) + spec §13 License Gate
