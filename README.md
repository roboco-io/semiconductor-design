# semiconductor-design — AutoResearch for EDA Surrogate Models

> AI 에이전트가 **반도체 타이밍 예측(surrogate) 모델**을 *스스로 연구*하게 만드는 프로젝트.
> 단, 최종 채택은 **항상 사람(Operator)이 승인**한다.
>
> 📖 **EDA 배경 지식이 없어도 됩니다** — [`docs/TUTORIAL.md`](docs/TUTORIAL.md)에서 용어를 하나하나
> 풀어 설명합니다. 처음이라면 거기부터 읽으세요.

karpathy [AutoResearch](https://github.com/karpathy/autoresearch)의 진화 루프를 **EDA surrogate
지표예측 모델 학습**에 적용한다. 구조는
[roboco-io/serverless-autoresearch](https://github.com/roboco-io/serverless-autoresearch) 패턴을 따른다.

> 2026-05-29 피벗. 이전 통합 프로그램(L1/L2/L3 3-layer, 전체 RTL→GDSII)은
> `archive/integrated-program-3layer` 브랜치에 보존.

## 무엇을 하나

- **목표**: 합성 직후 정보(feature) → 최종 타이밍 슬랙(label)을 예측하는 **대리(surrogate) 모델**을,
  AI 에이전트가 학습 스크립트(`train.py`)를 반복 변형하며 자동으로 더 잘 학습.
- **루프**: 세대마다 N개 후보 변형(Claude+Codex) → 각각 **5개 seed로 학습** → 최저
  **median `val_mae`** winner 선택 → **Operator 승인 후** git tag(`gen-NNN-best`)로 승격.
- **차별 축(가설)**: **H-A** 에이전트 루프가 사람 수작업을 능가 · **H-B** 사람 승인을 유지해도
  성능을 잃지 않음(자율 무인 머지와 대비).

## 지금 상태 (2026-06-07)

✅ **시스템 functional + 2세대 실증 + 평가 프로토콜 진화.** (자세히는 [`INTENT.md`](INTENT.md) Learnings)

| 조각 | 파일 | 상태 |
|---|---|---|
| EDA flow (클라우드) | `cdk/`, `docker/eda-flow*` | ✅ AWS Fargate 배포·검증 (진짜 데이터 53행 확보) |
| 데이터 준비 (고정) | `prepare.py`, `src/prepare_lib/` | ✅ frozen 계약 |
| 학습 스크립트 (변형대상) | `train.py` | ✅ sklearn Gradient Boosting baseline |
| 진화 루프 | `src/pipeline/` | ✅ candidate_gen·runner·**multi-seed median**·selection·holdout·operator_gate·orchestrator (45 tests) |
| **gen-001** | tag `gen-001-best` | ✅ winner val_mae 0.177→**~0.11**(seed=0 기준), Operator 승인 후 승격 |
| **gen-002** | `experiments/gen-002/` | ❌ **reject** — 단일 seed winner가 5-seed median에선 baseline에 패배(위양성). [rejudge](experiments/gen-002/rejudge.md) |

> ⚠️ **측정 프로토콜 진화**: gen-002에서 단일 seed=0 선택이 *위양성* winner를 뽑은 걸 계기로,
> selection을 **5개 seed(0~4)의 median val_mae**로 강화([spec](docs/superpowers/specs/2026-06-06-multiseed-median-selection-design.md)).
> 이어 **승격 검증 게이트(T1)**로 50-fold paired 통계(Wilcoxon+CI+Cohen's dz)를 Operator에 advisory 제시
> ([spec](docs/superpowers/specs/2026-06-07-t1-promotion-validation-gate-design.md)).
> **gen-001 소급 재심 결과 H-A 엄밀 재확증** — winner(0.148) vs 사람 baseline(0.194), dz=−1.27, p<0.001,
> verdict `distinguishable` ([revalidation](experiments/gen-001/revalidation.md)). 단일 설계 한계상 *일반화*는 T4의 몫.

결정 기록(OD-1~6): 지표=per-path slack · feature=8개 · 모델=sklearn HistGBDT · 인프라=Fargate ·
baseline=naive — 모두 [`issues/`](issues/)에 resolved.

## 빠른 시작

```bash
make install                         # 의존성 설치
make test                            # 45 tests
uv run python prepare.py --synth experiments/real-gcd-fargate/synth.rpt \
  --route experiments/real-gcd-fargate/route.rpt \
  --lockfile experiments/real-gcd-fargate/versions.txt \
  --design-id gcd --out-dir /tmp/ds  # 진짜 데이터 → 표(53행)
make train DATA=/tmp/ds/dataset.jsonl OUT=/tmp/art SEED=0   # 대리 모델 1회 학습
make loop GEN=3 DATASET=/tmp/ds/dataset.jsonl N=2 PROGRAM=program.md  # 진화 1세대 (LLM 비용, 5-seed median 선택)
```

클라우드 EDA flow 재실행(AWS 비용)은 [`cdk/DEPLOY.md`](cdk/DEPLOY.md) 참조.

## 문서 지도

| 문서 | 내용 |
|---|---|
| [`docs/TUTORIAL.md`](docs/TUTORIAL.md) | **여기부터** — EDA 비전공자용 튜토리얼 + 용어 사전 |
| [`PRD.md`](PRD.md) | 제품 요구사항 + 데이터 모델(ERD) |
| [`INTENT.md`](INTENT.md) | 프로젝트의 Why/What/Not/Learnings (status: clarified) |
| [`issues/`](issues/) | 결정 기록 OD-1~6 |
| [`docs/superpowers/specs/`](docs/superpowers/specs/) | 단계별 설계 문서 |
| [`docs/superpowers/plans/`](docs/superpowers/plans/) | 단계별 TDD 구현 plan |
| [`experiments/real-gcd-fargate/VALIDATION.md`](experiments/real-gcd-fargate/VALIDATION.md) | 진짜 데이터 검증 기록 |

## 개발 규약

Python 3.12 · uv · ruff(100 char) · pytest. `main`에 직접 커밋. 에이전트가 변형하는 `train.py` 외의
substrate(`prepare.py`, 평가 규칙)는 **고정(frozen)** — 공정 비교를 위해. winner 승격은 **항상 사람**.
