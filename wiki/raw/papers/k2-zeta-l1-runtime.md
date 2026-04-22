---
type: raw-import
axis: zeta
title: "K2 축별 자료 — L1 runtime: Fargate Spot + Nix + Chipyard/Gemmini"
date: 2026-04-22
phase: K2
curator: claude-opus-4-7
source_count: 13
intent: "G1 kill gates (KG-A~KG-E)를 L1 파생 spec 착수 전에 선제 검증하기 위한 자료. LibreLane 2.4 on Fargate 실증, Nix 이미지 배포·크기, Chipyard 1.13+ build 메모리, Gemmini main SHA 2026 동향, AWS Step Functions Map 스케일 특성."
---

# ζ. L1 Runtime Substrate — Fargate Spot + Nix + Chipyard/Gemmini — K2 Resource Survey

## Meta

- **Scope**: L1 Process layer 런타임 기반. SHA-pinned Nix bundle + AWS Fargate Spot + Step Functions Map + S3/DynamoDB artifact plane.
- **Gate 매핑**: overview spec §8 G1 gate — KG-A (LibreLane-on-Fargate 4vCPU/16GB/30min p95), KG-B (Chipyard+Gemmini build 메모리), KG-C (LLM SDK quota — 본 축 범위 외), KG-D (Spot reclaim 재시도), KG-E (DDB write amp).
- **Spec 참조**: §3.2 `L1.run(spec_uri)` 인터페이스 계약 · §6.2 `lockfile.yaml` SHA-pin 규칙 · §11 리스크(Chipyard OOM, PnR > 20min Spot reclaim).
- **학습 lens**: Phase 0 EDA operator — Fargate 로그·`*.rpt`·SIGTERM 이벤트 해석이 operator 책무.

## Resources

### 1. LibreLane 3.0.2 (2026-04-02) — 최신 카논 flow
- URL: https://github.com/librelane/librelane/releases
- Tag: [tooling, critical-read, container, nix]
- WHAT: FOSSi LibreLane가 2026-04-02 기준 **3.0.2** 까지 진행. 3.0(2026-03-25)에서 Synlig→Slang 전환, nix-eda 6 업그레이드, Python 3.10+, FP_ config 대규모 정리, KLayout DRC/LVS IHP 지원, SPICE RCX 전체화. 2.4.13(2026-02-19)가 2.x 종착. **spec §6.2 lockfile 재작성 필요 — v2.4 series 기준 가정은 이미 stale이며, G1 MVP는 3.0.x로 pin.**

### 2. LibreLane 설치 매트릭스 (Nix / Docker / pip)
- URL: https://github.com/librelane/librelane
- Tag: [tooling, container, nix, critical-read]
- WHAT: 공식 설치 경로 세 가지 — **Nix (권장, macOS·Linux x86_64/aarch64, 파일시스템 통합 강)**, Docker (`--dockerized` 플래그, Windows 포함), `pip install librelane` (컴파일된 유틸 별도 제공 — unsupported). Colab 데모 제공. **Fargate 표적은 Docker path가 가장 단순하나, Nix path가 SHA-pin 재현성 측면에서 spec §6.2 요구에 맞음.**

### 3. FOSSi LibreLane 2.4 발표 (2025-08-17)
- URL: https://fossi-foundation.org/blog/2025-08-17-librelane
- Tag: [foundational, critical-read]
- WHAT: OpenLane2 → LibreLane rename의 공식 기록. 2.4.0(2025-07-17) 출시, Efabless 2025-02 셧다운으로 `efabless/openlane2` 네임스페이스 회수가 현실적으로 불가해 FOSSi 산하로 이관. Python 기반 immutable State 객체·Step·metric 수집 아키텍처 재확인. **Efabless 경로 폐기의 1차 공식 소스.**

### 4. AWS Fargate Spot 공식 문서 — 중단 신호
- URL: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html
- Tag: [aws-reference, critical-read]
- WHAT: Fargate Spot 중단 시 **2분 warning → SIGTERM → `stopTimeout`(기본 30s, 최대 120s) → SIGKILL** 경로 공식화. Task State Change 이벤트가 EventBridge로 `SpotInterruption` stopCode와 함께 송출. **AWS는 중단된 Spot capacity를 On-Demand로 자동 대체하지 않음** — KG-D (재시도 로직) 설계 시 핵심 제약.

### 5. AWS Fargate ephemeral storage 200 GiB (공식)
- URL: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-storage.html
- Tag: [aws-reference, lockfile-data]
- WHAT: Fargate task 기본 20 GiB, `ephemeralStorage.sizeInGiB` 로 **최대 200 GiB까지 확장 가능**. 컨테이너 이미지(압축·비압축) 모두 이 공간을 소비. PV 1.4.0+ AES-256 암호화. **spec §6에서 "10GB ephemeral" 가정은 stale — Chipyard + sky130A + OpenROAD 통합 이미지(수 GB)를 수용하려면 50~100 GiB 설정을 lockfile에 기록해야 함.**

### 6. Fargate Spot reliability — 실전 운영 패턴 (2026)
- URL: https://oneuptime.com/blog/post/2026-02-12-use-spot-instances-with-ecs-fargate/view
- Tag: [aws-reference, recent-SOTA]
- WHAT: Fargate Spot 디스카운트 **~70%**, 공식 SLA 없음. 권장 패턴: base On-Demand(예: 2 task) + Spot 가중(예: weight 4)으로 다중 AZ 분산. 실전 리포트는 "적절한 배포 시 수 주간 무사고 가동" — **즉 reclaim은 통계적 드문 사건이지만 long-tail PnR job(>20min)에서는 반드시 발생한다 가정하고 checkpoint를 설계**.

### 7. AWS Step Functions Distributed Map (공식)
- URL: https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html
- Tag: [aws-reference, critical-read]
- WHAT: Distributed Map은 **child workflow 최대 10,000 병렬**, `MaxConcurrency` 기본 1,000. **Inline Map은 40 병렬이 상한**. Distributed Map은 Standard workflow에서만 parent로 동작하지만, child는 Standard/Express 선택 가능. **spec의 `maxConcurrency=10` 은 보수 설정 — 확장 시 Distributed 모드로 전환하면 그대로 수평 확장 가능하다는 근거.**

### 8. Step Functions Standard vs Express — >5분 잡
- URL: https://docs.aws.amazon.com/step-functions/latest/dg/state-map.html
- Tag: [aws-reference, critical-read]
- WHAT: Express workflow는 **최대 5분 한도** — 20분 PnR이 필요한 LibreLane child에는 **Standard 필수**. Standard는 state transition당 과금($0.025 / 1,000 transitions)이라 per-candidate job 수준에서는 저렴. **KG-A(30min p95) 요구와 결합하면 parent/child 모두 Standard가 합리적 디폴트.**

### 9. Chipyard 1.13.0 (2024-09-30) — 아직 최신
- URL: https://github.com/ucb-bar/chipyard/releases
- Tag: [accel-template, lockfile-data]
- WHAT: 1.13.0이 2026-04 현재까지도 최신 태그 (69eba86). Saturn/Ara 벡터 유닛 통합, RISC-V B 확장, FireSim decouple. 2025~2026 main에는 태그 없음 — **spec §6.2는 Chipyard도 commit SHA pin으로 통일**. 빌드 자원 공식 수치는 문서 내 명시 없음 — CI 벤치마크 실측 필요(KG-B 실험 설계 포인트).

### 10. Gemmini — `main` only, 2023-05 이후 무태그
- URL: https://github.com/ucb-bar/gemmini
- Tag: [accel-template, critical-read, lockfile-data]
- WHAT: 최신 태그 v0.7.1(2023-05-22) 이후 태그 없음, 주 개발은 `master`/`main`에서 지속(827 commits, 활성 PR/issue 다수). **재현성 유일 방법은 commit SHA pin** — lockfile에 `gemmini.rev`를 명시하고, Chipyard submodule 버전과 일관성 락킹 필요. RoCC 인터페이스 미묘한 변화가 Chipyard 버전 호환성에 영향.

### 11. OpenROAD-flow-scripts Nix flake (공식)
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/master/flake.nix
- Tag: [nix, open-source-impl, critical-read]
- WHAT: ORFS 저장소가 **공식 `flake.nix` 를 유지** — OpenROAD, Yosys, KLayout, Verilator, Perl/Python3(+pandas/numpy/pyyaml) 을 `nix develop` 으로 한 번에 재현. input에 OpenROAD/Yosys commit hash 고정. **G1 Nix bundle 구성의 직접 출발점이며, 이 flake를 base로 LibreLane 3.0.x + Chipyard + Gemmini 를 추가하는 derivation을 작성하는 게 KG-A 선행 실험.**

### 12. re:Invent 2025 ECS/Fargate 업데이트
- URL: https://aws.amazon.com/blogs/containers/amazon-ecs-at-aws-reinvent-2025/
- Tag: [aws-reference, recent-SOTA]
- WHAT: re:Invent 2025는 ECS/Fargate에 **Fargate Spot reclaim 빈도나 가격 체계의 파괴적 변경을 발표하지 않음** (2025-12 기준). 즉 2026-04 기준 L1 설계는 "2분 warning · ~70% 디스카운트 · 비보장 SLA" 라는 기존 모델을 그대로 전제해도 안전. **spec 가정의 안정성을 뒷받침하는 negative evidence.**

### 13. ORFS AutoTuner (Ray Tune) — 기존 인프라 참조
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts
- Tag: [open-source-impl, foundational]
- WHAT: ORFS는 Ray Tune 기반 AutoTuner를 이미 내장 — LibreLane/OpenROAD 파라미터 sweep을 **로컬 Ray 클러스터 또는 단일 컨테이너**로 돌릴 수 있는 기성 해법. **spec §3.2 L1.run 계약 초기 구현은 "Ray Tune 로컬 fallback ↔ Step Functions Map 원격" 이중 경로**로 시작하는 것이 KG-A/KG-B 분리 검증에 유리.

## Landscape Snapshot

- **현재 카논 스택 (2026-04)**:
  LibreLane **3.0.2** + OpenROAD + Yosys (ORFS flake) + Chipyard **1.13.0 (SHA 69eba86)** + Gemmini **main SHA pin** + sky130A/gf180mcuD + Fargate Standard workflow(Express 금지) + Step Functions Distributed Map(이후 확장) + 200 GiB ephemeral(실무 50~100 GiB).
- **spec 수정 포인트 누적**:
  1. §6.2 lockfile에 LibreLane 2.x → 3.0.x 반영.
  2. §6에서 "10 GB ephemeral" 가정 → 200 GiB 상한 기반 설정값으로 수정.
  3. §3.2 `maxConcurrency=10` 은 보수 기본값 유지 (Distributed Map으로 확장 여력 ≥1,000 확보).
  4. Chipyard/Gemmini는 모두 SHA pin 강제 — 태그가 부재 혹은 2년 이상 stale.
- **KG-A 선행 실험 시나리오**:
  ORFS Nix flake → LibreLane 3.0.x + sky130A derivation 추가 → Fargate Spot 4vCPU/16GB + 50 GiB ephemeral + Standard Map(concurrency 10)에서 `gcd` 디자인을 LibreLane `run` → 30 min p95 내 완료 및 SpotInterruption 재시도 로직 검증.
- **KG-B 선행 실험 시나리오**:
  Chipyard 69eba86 + Gemmini SHA pin을 동일 Nix derivation에 얹어 RTL elaborate + Verilator build 지점의 peak RSS·디스크 IO 실측 → Fargate 메모리 계층(16/32 GB) 선택과 ephemeral 용량 튜닝.

## Caveats / Unverified

- Chipyard·Gemmini 구체적 빌드 메모리(피크 RSS), 디스크 용량은 공식 문서에 수치 없음 — **KG-B에서 실측이 1차 데이터**.
- ECR 병렬 pull throttling·실시간 속도는 공식 수치 미공개 — 재현성 필요 시 VPC endpoint/pull-through cache 검토.
- Cachix 다중 GB EDA 바이너리 캐싱 best-practice 공식 문서 없음 — 커뮤니티 ad-hoc 관행 기반.
- Fargate Spot 통계적 reclaim 빈도는 AWS 공식 수치 비공개 — 외부 운영 사례 기반 추정만 가능.
