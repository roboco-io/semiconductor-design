# OD-4 모델 클래스 — grounded 조사 (2026-06-06)

> 목적: OD-4(surrogate 모델 클래스) brainstorm의 근거. per-endpoint timing slack 회귀(OD-1)에 어떤 모델이 적합한가.
> 방법: Perplexity `*search*`(grounded). ⚠️ `perplexity_research`(Sonar Deep Research) 출력은 **citation 0개 + 환각**으로 *전체 거부*(Operating Invariant #5) — 아래는 grounded 검색 결과만.

## ⚠️ 환각 거부 기록 (H3 reasoning-trace 증거)

`perplexity_research` 58KB 응답은 URL 0 / inline citation 0. 본문이 **"SNS = Symposium on Nanoscale Science"**라 단언(이 맥락 SNS는 timing 예측 연구이지 나노과학 심포지엄 아님) + "GPU clusters 필요" 등 무근거 주장. 2026-05-25 Learnings #5("LibreSoC's LibreLane" 환각)의 재발. **first-check=citation 개수**가 차단. 본 노트는 grounded `*search*`만 사용.

## A. EDA path-level timing의 실제 SOTA = tabular

- **MasterRTL** (ICCAD'23, [arxiv 2311.08441](https://arxiv.org/pdf/2311.08441.pdf), [github](https://github.com/hkust-zhiyao/MasterRTL)) — pre-synthesis PPA의 정전.
  - design-level calibration = **XGBoost** (45 estimators, max_depth 8).
  - path-level timing = **Random Forest + human-extracted path features**.
  - 명시: *"tree-based models are more accurate in path-level timing and module-level power, outperforming deep learning models (Transformer and GCN)"* / *"Random Forest > Transformer"* / *"XGBoost regressor > GCN"*.
  - → 우리 OD-1 태스크(per-endpoint/path slack)의 실제 SOTA가 정확히 **tabular tree-based**.
- **TAMU thesis** (pre-CTS timing-critical FF 예측): LR/MLP/RF/XGBoost/GraphSAGE/GAT 비교, 최고 0.98 AUROC, CTS+route 대비 62000–73000×↑.

## B. 일반 ML: tabular에서 tree-based가 DL 압도 (우리 조건과 정합)

- **Grinsztajn et al., NeurIPS'22** ([neurips pdf](https://proceedings.neurips.cc/paper_files/paper/2022/file/0378c7692da36807bdec87ab043cdadc-Supplemental-Datasets_and_Benchmarks.pdf)) — tree-based가 ~10K 데이터에서 SOTA, NN 튜닝 후에도. NN은 uninformative feature·rotation invariance로 불리.
- **Shwartz-Ziv & Armon** ([arxiv 2106.03253](https://arxiv.org/pdf/2106.03253.pdf)) "Deep Learning is Not All You Need" — XGBoost가 deep model 압도, 튜닝 훨씬 적음. deep+XGBoost 앙상블이 최고.
- **McElfresh et al., NeurIPS'23** ([arxiv 2305.02997](https://arxiv.org/abs/2305.02997)) — GBDT가 **skewed/heavy-tailed 분포에서 NN보다 훨씬 우월**. slack 분포(critical-path 쏠림)가 정확히 이 경우. 단 **TabPFN**(prior-data-fitted NN)은 <3000 샘플서 우월 — 그러나 PyTorch 의존이라 NFR-1 위배.

## C. CircuitNet의 CNN/GNN은 *우리가 피한* 태스크용

- **CircuitNet 2.0** (ICLR'24, [pdf](https://proceedings.iclr.cc/paper_files/paper/2024/file/464917b6103e074e1f9df7a2bf3bf6ba-Paper-Conference.pdf)) — routability/IR-drop = **CNN(이미지)**, net-delay = **MLP(5×32) + GNN**. spatial/graph 태스크. 우리는 F2/F3에서 per-endpoint tabular를 의도적으로 선택 → CircuitNet식 CNN/GNN은 비해당.

## OD-4 함의

1. **tabular tree-based(XGBoost / RandomForest / sklearn HistGradientBoosting)**가 (a) 이 태스크의 실제 SOTA(MasterRTL), (b) heavy-tailed slack 분포(McElfresh), (c) 소~중 데이터(Grinsztajn), (d) CPU·저의존성(NFR-1) 모두에서 정답 방향.
2. 반례 TabPFN(<3000 우월)은 PyTorch 의존으로 NFR-1이 이미 차단.
3. 남은 brainstorm 결정: baseline 구체(XGBoost vs sklearn-only HistGBDT/RandomForest) + 허용 의존성 경계 + AutoResearch 변형 공간(n_estimators·max_depth·lr·subsample·feature subset·RF↔GBDT).
