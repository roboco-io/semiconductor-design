# src/sagemaker/ — SageMaker 학습 인터페이스 (skeleton)

serverless-autoresearch `src/sagemaker/` 아날로그. SageMaker Spot 학습 job의
entry point wrapper와 training interface를 담는다. `train.py`(에이전트 변형 파일)를
SageMaker 컨테이너에서 실행하고 val 지표를 CloudWatch로 emit한다.

구현은 plan 승인 후. PRD.md §5 참조.
