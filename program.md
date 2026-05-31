# program.md — 에이전트 baseline 지시문 (placeholder)

serverless-autoresearch의 `program.md` 아날로그. AutoResearch 루프의 에이전트가
`train.py`를 변형할 때 따르는 baseline 지시·맥락·제약을 담는다.

구현 plan 승인 후 작성. 최소 포함 후보:
- 목표: surrogate val 지표(예: 예측 MAE) 최소화
- 변형 허용 범위: `train.py` 단일 파일, 신규 의존성 금지, 고정 학습 예산
- 변형 전략: conservative / moderate / aggressive / crossover
- Operator 감독: winner 선택·머지는 항상 사람

> PRD.md §2-§3 및 설계 spec 참조.
