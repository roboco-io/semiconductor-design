# 조사 ③: 오픈소스 EDA 툴체인·물리 설계 ML (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색, 5회 검색 모두 citation 확보)

## SOTA 요약

오픈소스 EDA는 OpenROAD/ORFS(RTL-to-GDSII 완전 자동 플로우)와 그 상위 인프라 LibreLane(OpenLane 2 후계, 2025 FOSSi 이관)을 축으로 성숙 단계에 진입했다. 2025년 IEEE DATC RDF는 사상 최초로 상용 툴(Siemens Aprisa v2025.2)의 공개 벤치마킹 결과를 NanGate45/ASAP7 오픈 테스트케이스로 발표해, 학계가 상용 baseline 대비 진척을 측정할 수 있는 기반을 열었다. ML 쪽은 (i) 데이터셋/벤치마크 구축(CircuitNet 1.0-3.0, EDA-Schema-V2, ChiPBench), (ii) 플로우 파라미터 자동 튜닝(AutoTuner + METRICS2.1, Antmicro의 Vizier/NSGA-II 다목적 확장), (iii) LLM 에이전트에 의한 플로우 조작(ORFS-agent, OpenROAD Agent, EDA Corpus)의 세 흐름이 주도한다.

ML placement는 AlphaChip 재현성 논쟁이 상징하듯 "중간 지표 개선 ≠ 최종 PPA 개선"이라는 평가 방법론 문제가 핵심 화두다. ChiPBench(2024)는 6개 SOTA AI placer를 end-to-end로 평가해 중간 지표 우세가 최종 PPA로 이어지지 않음을 실증했다.

## 핵심 논문

| 제목 | 연도 | venue | URL | 핵심 주장 | 한계 |
|---|---|---|---|---|---|
| Assessment of RL for Macro Placement (Cheng, Kahng 외) | 2023 | ISPD (invited) | https://vlsicad.ucsd.edu/Publications/Conferences/396/c396.pdf | Google Circuit Training(CT)의 blackbox 요소를 오픈 구현·평가. CT가 SA·상용 대비 열세 | 비-peer-review invited; Google은 pre-training 미수행·컴퓨트 부족을 지적 |
| An Updated Assessment of RL for Macro Placement | 2025 (게재 확정 2025-12) | IEEE TCAD | https://vlsicad.ucsd.edu/Publications/Journals/j148.pdf | ASAP7 테스트케이스 갱신·SA baseline 개선 후에도 결론 유지 | 여전히 Google 내부 pre-trained 모델·TPU 블록으로는 검증 불가 |
| That Chip Has Sailed (Goldie, Mirhoseini, Dean) | 2024 | arXiv:2411.10053 | https://arxiv.org/html/2411.10053 | ISPD'23 평가가 Nature 기술대로 실행되지 않았다(pre-training 생략, 20x 적은 collector, 미수렴)고 반박 | 반박의 근거 데이터·모델 다수가 여전히 비공개 |
| Reevaluating Google's RL for IC Macro Placement (Markov) | 2024 | CACM | https://cacm.acm.org/research/reevaluating-googles-reinforcement-learning-for-ic-macro-placement/ | Nature 논문·ISPD'23·자체 분석의 메타 분석, 검증 절차 문제 제기 | 이해충돌 논란 |
| ChiPBench | 2024 | arXiv:2407.15026 | https://arxiv.org/html/2407.15026 | 20개 회로에서 6개 AI placer를 OpenROAD end-to-end로 평가 — 중간 지표와 최종 PPA의 심각한 불일치 실증 | placement 단계 중심; 상용 signoff 대비 절대 QoR은 미검증 |
| CircuitNet 2.0 | 2024 | ICLR | https://openreview.net/forum?id=nMFSUjxMIl | 14nm FinFET 상용 플로우 10K+ 샘플 — congestion/IR drop/timing 예측용 대규모 공개 데이터셋 | 상용 툴·비공개 PDK 기반이라 재현·확장 불가(정적 데이터셋) |
| EDA-Schema-V2 | 2026 | arXiv:2605.06952 | https://arxiv.org/html/2605.06952v1 | OpenROAD + 4개 오픈 PDK(NG45/SKY130/IHP130/ASAP7)로 7,776 설계 인스턴스, 12개 예측 태스크 baseline까지 완전 재현 가능 | IWLS'05 벤치마크 기반이라 회로 다양성 제한 |
| METRICS2.1 + AutoTuner (Jung, Kahng 외) | 2021 | ICCAD | https://vlsicad.ucsd.edu/Publications/Conferences/388/c388.pdf | 표준화된 플로우 메트릭 + derivative-free 탐색으로 SKY130/ASAP7에서 PPA 목표별 튜닝(전력 41%/성능 21%/면적 68% 개선 사례) | 단일 스칼라 목적함수; 툴 노이즈·탐색 비용 문제 |
| IEEE DATC RDF-2025 | 2025 | DATC/ICCAD invited | https://vlsicad.ucsd.edu/Publications/Conferences/419/c419.pdf | 최초의 상용 툴(Aprisa) 공개 벤치마크 + OpenROAD-Research "innovation sandbox" 신설 | Aprisa 커버리지는 NG45/ASAP7 일부 테스트케이스에 한정 |
| ORFS-agent | 2025 | arXiv:2506.08332 | https://arxiv.org/html/2506.08332v3 | LLM tool-using 에이전트로 ORFS 플로우 파라미터를 반복 최적화 | LLM 호출 비용·재현성(모델 버전 의존) 문제 |

## Open Problems

- **평가 지표-최종 PPA 해리**: AI placer의 중간 지표(HPWL 등) 개선이 최종 PPA로 이어지지 않음 — end-to-end 평가가 표준이 아님 (ChiPBench, arXiv:2407.15026)
- **상용 툴 벤치마킹 금지 관행**: EULA가 벤치마킹을 금지해 SOTA 위치가 불명확. 2025년 Aprisa 공개가 첫 예외 (DATC RDF-2025)
- **재현성 인프라 부족**: OpenROAD 본체는 유효 도구만 유지해 알고리즘 baseline이 소실 — OpenROAD-Research가 보완 시도 (c419.pdf)
- **데이터 부족·정적 데이터셋**: 물리 설계 데이터 생성 비용이 커서 CircuitNet류도 다양성 부족 — diffusion 기반 합성 데이터(DALI-PD) 등장 배경 (c419.pdf)
- **AlphaChip류 재현의 구조적 장벽**: pre-trained 모델·독점 테스트케이스·대규모 컴퓨트 없이는 원 논문 조건 재현 자체가 불가 (arXiv:2411.10053 vs TCAD j148)
- **표준 데이터 표현 부재**: 툴별 포맷 파편화로 ML 연구 간 비교·재사용 곤란 (EDA-Schema-V2, METRICS2.1)

## Underexplored Areas (로컬 컴퓨트 실행 가능성 표시)

- **[가능] 플로우 파라미터 자동 튜닝의 소규모 설계 적용**: AutoTuner는 trial당 CPU 1개로 설정 가능, GCD/IBEX/AES급 설계는 로컬에서 수십-수백 iteration 실행 가능. 다목적(NSGA-II/Vizier)·stage caching은 2026년에야 추가된 신생 영역 (Antmicro 블로그 2026-01)
- **[가능] PPA/QoR 예측 모델 학습**: EDA-Schema-V2·CircuitNet 데이터는 tabular/GNN 소형 모델로 충분 — GPU 대규모 학습 불필요. stage-to-stage 예측 가능성 분석은 baseline만 존재
- **[가능] LLM 에이전트 기반 플로우 조작·자기수정**: ORFS-agent/OpenROAD Agent 계열은 컴퓨트가 아니라 API 호출 중심. 구독형 LLM + 로컬 ORFS로 실험 가능. 평가 벤치마크 미비한 초기 영역
- **[가능] 벤치마크·평가 방법론 자체**: ChiPBench식 end-to-end 평가의 확장(오픈 PDK 조합, sign-off 조건 통일)은 실행 위주로 CPU만 필요
- **[부분 가능] SA 등 고전 휴리스틱 baseline 강화**: MacroPlacement 저장소의 SA baseline 개선 사례처럼, RL 없는 baseline 연구가 여전히 유효
- **[불가/곤란] RL placement 원조건 재현**: 수십 GPU + 대량 experience collector 필요

## 재현 가능 자산

- **툴체인**: OpenROAD / OpenROAD-flow-scripts (github.com/The-OpenROAD-Project), LibreLane 3.x (github.com/librelane/librelane, Colab 데모), OpenROAD-Research·ORFS-Research (신설 sandbox)
- **튜닝**: ORFS `tools/AutoTuner` (Ray Tune + HyperOpt/Optuna/Ax/PBT/Nevergrad, Vizier 다목적 지원 PR #2428), METRICS2.1 (github.com/ieee-ceda-datc/datc-rdf-Metrics4ML)
- **벤치마크**: MacroPlacement (github.com/TILOS-AI-Institute/MacroPlacement — ASAP7 테스트케이스·SA·CT 결과), ChiPBench(20 회로), HighTide (github.com/VLSIDA/HighTide — 8 설계 x ASAP7/NG45/SKY130), DATC RDF repo(Aprisa 공개 결과·스크립트), EDA Corpus (github.com/OpenROAD-Assistant/EDA-Corpus)
- **데이터셋**: CircuitNet 1.0/2.0/3.0 (github.com/circuitnet/CircuitNet — 단 상용 툴 기반), EDA-Schema-V2 (오픈 툴 기반 약 320GB, 완전 재현 가능)
- **PDK**: SKY130 (Tiny Tapeout 표준), GF180MCU, IHP SG13G2 (LibreLane 3.0 first-class), ASAP7/NanGate45 (상용 대비 벤치마킹 표준 enablement), open-pdks (fossi-foundation/open-pdks)
- **실리콘 경로**: Tiny Tapeout (SKY130/IHP 셔틀, LibreLane + Docker로 로컬 hardening 약 10분)

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| OpenROAD open-source EDA machine learning physical design research paper 2024 2025 | 8 |
| AlphaChip Google RL chip placement reproducibility controversy Kahng Cheng ISPD rebuttal 2024 2025 | 8 |
| OpenROAD AutoTuner Bayesian optimization RTL-to-GDS flow parameter tuning paper PPA prediction machine learning | 8 |
| open-source PDK SKY130 GF180 ASAP7 research benchmark chip design education Tiny Tapeout OpenLane LibreLane 2024 2025 | 8 |
| machine learning EDA survey open problems benchmark gap commercial tools reproducibility CircuitNet dataset PPA prediction 2024 2025 | 8 |
