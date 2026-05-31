# semiconductor-design — AutoResearch for EDA Surrogate Models

> 2026-05-29 피벗됨. 이전 통합 프로그램(L1/L2/L3 3-layer, 전체 RTL→GDSII)은
> `archive/integrated-program-3layer` 브랜치에 보존되어 있다.

karpathy [AutoResearch](https://github.com/karpathy/autoresearch)의 population-based evolution
루프를 **EDA surrogate 지표예측 모델 학습**에 적용하는 연구 프로젝트. 구조는
[roboco-io/serverless-autoresearch](https://github.com/roboco-io/serverless-autoresearch)의
HUGI Spot 패턴을 따른다.

- **무엇**: 합성 직후 feature → 최종 PPA/routability를 예측하는 surrogate 모델을, 에이전트가
  학습 스크립트(`train.py`)를 반복 변형하며 자동으로 더 잘 학습.
- **어떻게**: 세대마다 N개 후보 변형 → 병렬 SageMaker Spot 학습 → 단일 val 지표로 winner 선택
  → **Operator 승인 후** git tag commit.
- **차별 축**: Operator 감독 + (2차 연기) reasoning trace 증거.

## 문서

- 제품 요구사항: [`PRD.md`](PRD.md)
- 설계 lineage: [`docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md`](docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md)
- 프로젝트 의도: [`INTENT.md`](INTENT.md) (피벗 반영 재작성 예정)

## 구조

`PRD.md` §5 참조. `prepare.py`/`train.py`/`program.md`/`config.yaml`은 현재 **placeholder**이며
구현 plan 승인 후 작성한다.
