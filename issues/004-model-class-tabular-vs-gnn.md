---
id: 004
title: 모델 클래스 (tabular vs GNN, CPU 학습 가능성)
status: open
type: decision
blocks: [NFR-1, "train.py 구조"]
related_prd: OD-4
related_intent: "Not §기술제약 (고정 학습 예산·신규 의존성 금지)"
depends_on: [001, 002]
---

# 004 — 모델 클래스

## 배경

`train.py`(에이전트 변형 단일 파일, NFR-1)가 학습하는 모델 클래스가 미정. 이 결정은 NFR-1의 "고정 학습 예산"·"신규 의존성 금지"와 직접 충돌 가능 — GNN은 학습 비용↑, 의존성(torch-geometric 등)↑. 002 feature 형태(스칼라 vs 그래프)와 짝을 이룬다.

## 옵션

- **A. tabular regression** — XGBoost/LightGBM 또는 MLP. CPU 학습 가능, 의존성 가벼움. feature는 스칼라(002-A). 에이전트 변형 공간이 명확(하이퍼파라미터·feature 조합).
- **B. GNN** — netlist 그래프 직접 학습. CircuitNet/RouteNet 정합도↑이나 GPU·무거운 의존성. NFR-1 "신규 의존성 금지"와 긴장.
- **C. 단계적** — 1차 tabular로 루프 검증, 2차 GNN 확장.

## 결정 기준

- NFR-1 고정 예산 내 학습 완료 가능한가 (Spot 단위 시간).
- "신규 의존성 금지" 제약 — baseline `train.py`에 미리 포함할 라이브러리 범위.
- 001 지표·002 feature와의 정합 (routability heatmap이면 GNN/CNN 유리).
- 에이전트 변형 공간이 충분히 풍부한가 (population evolution 의미).

## 액션 아이템

- [ ] 001·002 확정 후 모델 클래스 1개를 baseline `train.py`로 고정.
- [ ] 허용 의존성 목록을 `program.md`/`config.yaml`에 명시 (NFR-1 경계).
- [ ] CPU 1-job 학습 시간이 고정 예산 내인지 smoke 측정.
