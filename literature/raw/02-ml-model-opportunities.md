# 조사 ②: 반도체 설계용 소형 ML 모델 기회 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색, 기각 없음)

## 요약

- 2024-2026 현재 ML-for-EDA용 공개 데이터셋은 충분히 성숙했다: CircuitNet(BSD-3), EDA-Schema(OpenROAD/Sky130 기반, 7,800+ 인스턴스), METRICS2.1/Metrics4ML(표 형식 플로우 메트릭), ICCAD'23 Problem C(IR drop 전용, 콘테스트 스플릿 포함). 모두 로컬 다운로드·CPU 학습 가능 규모.
- 학계 SOTA는 대부분 U-Net/Transformer 계열 이미지 모델이지만, **2025년 XGBoost 앙상블이 CNN/FCN을 정확도(R² +0.12)와 추론속도(14.95배)에서 이긴 사례**가 나옴 — "소형 tabular 모델로 이길 수 있는" 공간이 실증됨.
- 실무 근거는 강함: IR drop은 수십억 변수 선형계 풀이라 시뮬레이션이 수 시간 걸리고, 라우팅 실패 시 placement부터 재작업 — 조기 예측이 반복 루프를 끊는다. Synopsys DSO.ai(100+ 양산 테이프아웃), Cadence Cerebrus·RTL Design Studio가 같은 논리로 상용화됨.
- 최대 공백: 캘리브레이션된 불확실성/희소사건(hotspot) 지표, stage leakage 없는 정직한 pre-route 예측, 그리고 OpenROAD 플로우에 실제 꽂히는 "도구화"된 예측기 — 모두 소형 모델로 공략 가능.

## 태스크×데이터셋 기회 지도

| 태스크 | 데이터셋(URL) | 기존 SOTA/베이스라인 | 공백 | CPU 가능 |
|---|---|---|---|---|
| Congestion 예측 | CircuitNet N28/N14/N45 (circuitnet.github.io, HF `CircuitNet/CircuitNet`), BSD-3 | FCN/GPDL: NRMSE 0.040, SSIM 0.80; 2025 TransUNet 계열이 NRMSE 65% 개선 | XGBoost가 CNN을 이긴 선례 있음(타 데이터) → CircuitNet에서 tabular 재현·공개 베이스라인 부재 | ◎ (tile별 tabular화 시) |
| DRC violation 예측 | CircuitNet N28 (동일) | RouteNet FCN: ROC-AUC 0.95, PR-AUC 0.63 | PR-AUC 낮음 = 희소사건 미해결; 캘리브레이션·hotspot recall 리포트 없음 | ○ (소형 U-Net 수 시간-수일) |
| 정적 IR drop 예측 | ICCAD'23 Contest C (github.com/ASU-VDA-Lab/ML-for-IR-drop) + BeGAN 합성 수백 개; CircuitNet IR | MAVI/IREDGe U-Net: ROC 0.94; 2025 TransUNet MAE 0.374mV | 콘테스트 채점에 **모델 크기·런타임 포함** → 소형 모델에 구조적으로 유리; 공개 리더보드로 객관 비교 가능 | ○ |
| PPA/QoR 최종치 조기 예측 (tabular) | EDA-Schema (github.com/drexel-ice/EDA-schema), Metrics4ML (github.com/ieee-ceda-datc/datc-rdf-Metrics4ML) | 논문 자체 베이스라인 = OpenROAD 툴 자체 추정치(MAE/MAPE 표 제공); 확립된 SOTA 없음 | 사실상 무주공산 — 표준 스플릿·리더보드 없음, GBDT류 공개 구현 희소 | ◎ (수 분-수십 분) |
| Net delay/slack 예측 | CircuitNet timing features(SDF 그래프), EDA-Schema timing path | GNN 튜토리얼 수준 공개 베이스라인 | pre-route 입력만 쓰는 정직한 평가(stage leakage 배제)가 드묾 | ○ (소형 GNN) |
| 플로우 파라미터→QoR (autotuning 대리모델) | Metrics4ML DOE 수천 런 + 자체 ORFS 런 | AutoTuner는 탐색만 하고 학습된 예측기는 미탑재 | 예측기로 나쁜 trial 조기중단하는 도구 없음 | ◎ |

## 실무 유용성 근거

- **반복 시간 절약**: 백엔드 설계는 스테이지 간 피드백 루프가 길다(라우팅 실패 → placement 재작업). CircuitNet 논문 자체가 "cross-stage 예측으로 긴 피드백 루프를 국소 루프로 대체"를 존재 이유로 명시.
- **IR drop signoff 비용**: 정적 IR 해석은 수십억 변수 선형계 → 상당한 런타임. ICCAD'23 콘테스트가 ML 대체를 공식 문제로 채택했고 OpenROAD 프로젝트가 공동 주최 — 오픈소스 플로우 쪽 수요가 명시적.
- **상용 선례**: Synopsys DSO.ai 100+ 양산 테이프아웃, 생산성 3배·전력 -15%; Cadence Cerebrus는 독립 평가(MPC 그룹, 9개 산업 설계)에서 DRC 96% 감소·면적 23% 축소; Cadence RTL Design Studio는 "조기 PPAC 추정으로 반복 감소, 생산성 5배"를 제품 가치로 판매. 즉 "예측으로 반복을 줄인다"는 상품성이 검증된 명제.
- **연구 쪽 수요**: GNN-for-EDA 서베이(arXiv 2605.08291)가 캘리브레이션·희소사건 지표·stage leakage 감사를 "다음 단계 지배적 과제"로 지목 — 소형 모델+통계적 엄밀성으로 기여 가능한 지점.

## 유망 후보 Top 3

**1. OpenROAD 플로우용 tabular QoR 조기 예측기 + 조기중단 추천기 (최우선)**
- 무엇: METRICS2.1 JSON(synth/floorplan/place 단계 메트릭 + 플로우 파라미터)을 입력으로 post-route WNS/전력/면적/DRC 수를 XGBoost/LightGBM으로 예측. AutoTuner trial의 "가망 없음" 조기중단 추천 CLI로 포장.
- 왜: 데이터 자가생성 가능(ORFS는 완전 오픈, Sky130), 확립된 경쟁자 없음, 상용 도구들이 파는 가치(반복 감소)의 오픈소스 공백을 정확히 메움. 학습은 CPU 수 분.
- 검증: EDA-Schema 논문의 베이스라인(OpenROAD 자체 stage별 추정치의 MAE/MAPE)과 동일 프로토콜 비교 + 미학습 설계(leave-one-design-out) 스플릿 + AutoTuner 통합 시 총 탐색 시간 절감률.

**2. ICCAD'23 IR drop 콘테스트 벤치마크에서 경량 모델**
- 무엇: BeGAN 합성 데이터 사전학습 + 실회로 10개 미세조정으로 정적 IR drop 맵 예측(소형 U-Net 또는 tile-tabular GBDT).
- 왜: 채점 기준이 MAE·F1·**런타임·모델 크기** — 소형 모델이 구조적으로 유리한 유일한 공개 리더보드. 승자 점수 공개(xlsx)라 객관 비교 즉시 가능.
- 검증: 콘테스트 공식 hidden 10개 회로 스플릿, 공개 최종 점수표 대비 MAE/F1/모델크기.

**3. CircuitNet congestion/DRC에서 "XGBoost가 CNN을 이기는가" 재현 연구**
- 무엇: 2025년 앙상블-XGBoost 결과(R² +0.12, 추론 14.95배; 비공개 데이터)를 공개 CircuitNet에서 재현 — tile 단위 feature(RUDY, pin density 등)로 GBDT를 학습해 공식 FCN/U-Net 베이스라인과 비교, 캘리브레이션·hotspot recall까지 리포트.
- 왜: 데이터·베이스라인 코드·평가 지표가 전부 공개되어 있어 1인 개발자가 즉시 착수 가능하고, 결과가 어느 쪽이든(이기든 지든) 공백(공개 tabular 베이스라인 부재)을 메우는 기여.
- 검증: CircuitNet 공식 스플릿, NRMSE/SSIM(congestion)·ROC/PR-AUC(DRC) + 추론시간·파라미터 수 병기.

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| CircuitNet open dataset for ML in EDA congestion IR drop DRC hotspot prediction benchmark license | 8 |
| METRICS2.1 EDA-Schema open dataset tabular ML PPA QoR prediction physical design 2024 | 8 |
| ML EDA cross-stage prediction survey 2025 congestion IR drop timing SOTA benchmark CircuitNet baseline limitations | 8 |
| Commercial EDA ML prediction tools Cadence Cerebrus Synopsys DSO.ai early estimation flow iteration savings | 8 |
| ICCAD CAD contest 2023 static IR drop estimation dataset ISPD contest ML benchmark public data | 8 |
| XGBoost random forest tabular model OpenROAD flow QoR routability early prediction lightweight autotuner | 8 |
