# src/pipeline/ — AutoResearch 진화 루프 오케스트레이션 (skeleton)

serverless-autoresearch `src/pipeline/` 아날로그. 4-step generation cycle을 구동한다:

1. **candidate_gen** — baseline `train.py`에서 N개 변형 후보 생성 (전략 다양화)
2. **batch_launcher** — 후보를 병렬 SageMaker Spot job으로 제출 (HUGI)
3. **result_collector** — job 폴링 + CloudWatch에서 val 지표 추출
4. **selection** — 최저 val winner 식별 → Operator 승인 후 git tag commit
5. **orchestrator** — 위 단계를 세대 루프로 묶음

ERD 매핑: GENERATION·CANDIDATE·JOB 엔티티의 라이프사이클 관리. 구현은 plan 승인 후.
