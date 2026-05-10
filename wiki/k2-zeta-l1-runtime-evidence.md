---
title: "K2-ζ: L1 Runtime — Fargate Spot + Nix + LibreLane 3.0.2 + Chipyard/Gemmini — Direction Evidence"
type: synthesis
tags: [k2, l1-runtime, fargate-spot, nix, librelane-3-0-2, chipyard, gemmini, sha-pin]
status: active
confidence: medium
created: 2026-05-10
updated: 2026-05-10
sources:
  - raw/papers/k2-zeta-l1-runtime.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §6.2 lockfile · §8 G1 KG-A~E · §11 risk
  - docs/superpowers/specs/2026-04-20-L1-process-design.md  # 본 evidence가 직접 backing
related_wiki:
  - raw/repos/open-pdks-installer-and-ciel.md  # ciel commit-hash SHA-pin 메커니즘
  - raw/docs/librelane-3-architecture-official.md  # LibreLane 3.0.2 immutable State 5 strict 원칙
---

# K2-ζ: L1 Runtime — Direction Evidence

본 프로젝트의 **L1 Process layer**(SHA-pinned Nix bundle + AWS Fargate Spot + Step Functions Map + S3/DynamoDB artifact plane)의 13 source 종합. 모든 KG-A~KG-E kill gate의 직접 backing + spec **§6.2 lockfile.yaml 수정 사항 4개** 도출.

## Spec 수정 포인트 (K2-ζ가 도출한 4개)

| spec 영역 | 기존 가정 | K2-ζ 도출 변경 |
|-----------|-----------|----------------|
| §6.2 lockfile LibreLane 버전 | 2.4 series | **3.0.2** (2026-04-02 카논, 2.4.13이 2.x 종착) |
| §6 ephemeral storage | "10 GB" | **50–100 GiB** (Fargate 최대 200 GiB 한도 내) |
| §3.2 `maxConcurrency` | 10 | 10 유지 (보수). Distributed Map 사용 시 ≤10,000 확장 여력 |
| Chipyard / Gemmini lockfile | 태그 기반 | **SHA pin 강제** — Chipyard 1.13.0=69eba86, Gemmini는 v0.7.1(2023-05) 이후 무태그 |

## Source 카테고리

### LibreLane / Flow tooling (3종)
- **LibreLane 3.0.2** (2026-04-02, critical-read): 3.0(2026-03-25)에서 Synlig→Slang, nix-eda 6, Python 3.10+, FP_ config 정리, KLayout DRC/LVS IHP 지원, SPICE RCX. 2.4.13(2026-02-19)이 2.x 종착. **§6.2 lockfile 재작성 trigger**.
- **LibreLane 설치 매트릭스**: Nix(권장, x86_64/aarch64) / Docker(`--dockerized`, Windows) / pip(unsupported). **Fargate 표적은 Nix path가 SHA-pin 재현성 측면에서 §6.2 정합** (`raw/docs/librelane-3-architecture-official.md`).
- **FOSSi LibreLane 2.4 발표** (2025-08-17, foundational): OpenLane2 → LibreLane rename의 1차 공식 소스. Efabless 2025-02 셧다운으로 `efabless/openlane2` namespace 회수 불가 → FOSSi 이관. immutable State + Step + metric 아키텍처 재확인 ([[k1-gamma-opensource-eda-evidence]] Trigger 2와 정합).

### AWS Fargate / Step Functions (5종)
- **Fargate Spot 중단 신호** (AWS 공식): **2분 warning → SIGTERM → `stopTimeout`(기본 30s, 최대 120s) → SIGKILL**. EventBridge `SpotInterruption` stopCode. **AWS는 중단 Spot을 On-Demand로 자동 대체 안 함** — KG-D 재시도 로직의 핵심 제약.
- **Fargate ephemeral 200 GiB** (AWS 공식): 기본 20 GiB, `ephemeralStorage.sizeInGiB`로 최대 200 GiB. PV 1.4.0+ AES-256. 컨테이너 이미지(압축·비압축) 모두 소비. **§6 "10GB" 가정 stale**.
- **Fargate Spot 운영 패턴** (oneuptime 2026-02): 디스카운트 ~70%, **공식 SLA 없음**. 권장: base On-Demand 2 task + Spot weight 4 다중 AZ. "수 주간 무사고 가동" 보고 — long-tail PnR(>20min)은 **반드시 reclaim 발생 가정 + checkpoint 설계**.
- **Step Functions Distributed Map**: 최대 **10,000 child workflow** 병렬, `MaxConcurrency` 기본 1,000. **Inline Map은 40 상한**. Distributed는 Standard parent만, child는 Standard/Express. spec `maxConcurrency=10`은 보수 — 확장 시 Distributed로 수평 확장 근거.
- **Standard vs Express** (AWS 공식): **Express 5분 한도** — 20분 PnR LibreLane child에는 **Standard 필수**. Standard $0.025/1,000 transitions. KG-A 30min p95 + parent/child 모두 Standard가 합리 default.

### Nix / Reproducibility (1종)
- **ORFS Nix flake** (공식): OpenROAD, Yosys, KLayout, Verilator, Perl/Python3+pandas/numpy/pyyaml를 `nix develop` 한 번에. input에 OpenROAD/Yosys commit hash 고정. **G1 Nix bundle 구성의 직접 출발점** — 이 flake를 base로 LibreLane 3.0.x + Chipyard + Gemmini 추가 derivation 작성이 KG-A 선행 실험.

### Accelerator template (2종)
- **Chipyard 1.13.0** (2024-09-30, lockfile-data): SHA `69eba86`. Saturn/Ara 벡터, RISC-V B 확장, FireSim decouple. **2025~2026 main에 태그 없음 → SHA pin 강제**. 빌드 자원 공식 수치 부재 — **KG-B 실측 1차 데이터**.
- **Gemmini main only** (critical-read): v0.7.1(2023-05-22) 이후 무태그. 827 commits 활성 PR/issue. **SHA pin 유일 재현 방법**. RoCC 인터페이스 미묘한 변화가 Chipyard 버전 호환성에 영향 — Chipyard SHA와 일관성 락킹 필요.

### AWS 안정성 evidence (1종 negative + 1종 reference)
- **re:Invent 2025 ECS/Fargate 업데이트** (2025-12 기준, recent-SOTA, **negative evidence**): Fargate Spot reclaim 빈도·가격 체계의 파괴적 변경 **없음**. 즉 2026-04 기준 L1 설계가 "2분 warning · ~70% 디스카운트 · 비보장 SLA" 모델을 그대로 전제해도 안전.
- **ORFS AutoTuner** (Ray Tune): ORFS 내장 tuner. **`L1.run` 계약 초기 구현은 "Ray Tune 로컬 fallback ↔ Step Functions Map 원격" 이중 경로**가 KG-A/KG-B 분리 검증에 유리.

## KG-A~KG-E 직접 backing

| Kill Gate | 본 페이지 evidence |
|-----------|---------------------|
| **KG-A**: LibreLane-on-Fargate 4vCPU/16GB/30min p95 | source #1 LibreLane 3.0.2 + #4 Spot SIGTERM 경로 + #11 ORFS Nix flake. ORFS flake → LibreLane 3.0.x + sky130A derivation → Fargate Standard Map concurrency 10에서 `gcd` 30min p95 검증 |
| **KG-B**: Chipyard+Gemmini build 메모리 | source #9 Chipyard 1.13.0 + #10 Gemmini SHA pin. **KG-B에서 실측 = 1차 데이터** (공식 수치 없음). Fargate 메모리 계층(16/32 GB) 선택 + ephemeral 튜닝 결정 |
| KG-C: LLM SDK quota | 본 축 범위 외 |
| **KG-D**: Spot reclaim 재시도 | source #4 + #6. AWS는 자동 대체 X — 본 프로젝트 retry 로직 자체 구현. checkpoint 메커니즘 + EventBridge `SpotInterruption` 감지 + 새 Spot task spawn |
| **KG-E**: DynamoDB write amp | (본 raw에 직접 source 없음) — 별도 K2 ingest 후속 |

## SHA-pin 메커니즘 통합 (F branch 결합)

[[pdk-file-formats]]에서 발견한 **ciel** 패키지 매니저 + 본 페이지의 lockfile 요구가 결합:

| 컴포넌트 | SHA-pin 메커니즘 |
|----------|------------------|
| sky130A PDK | ciel `commit-hash` (`raw/repos/open-pdks-installer-and-ciel.md`) |
| LibreLane 3.0.2 | Nix flake input commit hash |
| OpenROAD / Yosys / KLayout | ORFS flake의 input commit hash |
| Chipyard 1.13.0 | submodule SHA `69eba86` 명시 |
| Gemmini | `gemmini.rev` SHA (태그 부재) |

→ `lockfile.yaml`에 5개 component SHA를 모두 명시하면 G1 Nix bundle은 byte-identical 재현. 이게 본 프로젝트의 **process novelty 1차 증거**(K1-γ Small-team novelty contribution #3 — citable frozen bundle).

## 2026-04 카논 stack (Landscape)

```
LibreLane 3.0.2
+ OpenROAD + Yosys (ORFS flake)
+ Chipyard 1.13.0 (SHA 69eba86)
+ Gemmini (main SHA pin)
+ sky130A / gf180mcuD
+ Fargate Standard workflow (Express 금지)
+ Step Functions Distributed Map (이후 확장)
+ 200 GiB ephemeral (실무 50~100 GiB)
```

## KG-A 선행 실험 시나리오 (본 페이지에서 도출)

1. ORFS Nix flake clone
2. LibreLane 3.0.x + sky130A derivation 추가
3. Fargate Spot 4vCPU/16GB + 50 GiB ephemeral
4. Standard Map concurrency 10
5. `gcd` 디자인 → LibreLane `run` 30min p95 검증
6. SpotInterruption 재시도 로직 검증

## KG-B 선행 실험 시나리오

1. Chipyard 69eba86 + Gemmini SHA pin → 동일 Nix derivation
2. RTL elaborate + Verilator build 지점의 **peak RSS·disk IO 실측**
3. Fargate 메모리 계층 (16 / 32 GB) 선택
4. ephemeral 용량 튜닝 (50 / 100 GiB)

## 미해결 / 추가 탐색

- **ECR 병렬 pull throttling**: 공식 수치 미공개. VPC endpoint / pull-through cache 검토.
- **Cachix 다중 GB EDA 바이너리 캐싱**: best-practice 공식 문서 없음. 커뮤니티 ad-hoc.
- **Fargate Spot reclaim 통계적 빈도**: AWS 비공개. 외부 운영 사례 추정만.
- **KG-E (DynamoDB write amp)**: 본 raw 미커버. K2 후속 raw 또는 별도 perplexity round.

## 교차 참조

- [[k2-epsilon-graph-quality-judge-evidence]] — L2 substrate freshness가 L1 artifact lake와 cross-link
- [[k1-gamma-opensource-eda-evidence]] — Trigger 2(LibreLane rename) 이력이 본 페이지에서 3.0.2까지 진행
- [[k1-beta-agentic-eda-evidence]] — ORFS-agent가 본 페이지 ORFS Nix flake 위에서 동작
- [[pdk-file-formats]] — sky130A 디렉토리 + ciel SHA-pin 메커니즘
- [[eda-flow-report-reading]] — Fargate task 로그·`*.rpt` 해석이 operator 책무
- `raw/repos/open-pdks-installer-and-ciel.md` — ciel commit-hash 메커니즘
- `raw/docs/librelane-3-architecture-official.md` — 5 strict 원칙 + State_i = Step_i 정식
- (pending) `[[k2-eta-patch-mutation-evidence]]` — reversible patch가 L1 candidate 사이 propagate
- (pending) `[[k2-theta-benchmark-license-evidence]]` — MLPerf Tiny v1.3 evaluation이 L1 artifact lake 위에서

## Source

- 원본: `raw/papers/k2-zeta-l1-runtime.md` (2026-04-22 collected, 13 sources, confidence: medium → spec 채택 시 high)
- decision_anchors: `raw/imports_manifest.yaml`
- 직접 backing: `docs/superpowers/specs/2026-04-20-L1-process-design.md`
