# models/ — 학습 artifact (skeleton)

serverless-autoresearch `models/` 아날로그. 세대 winner surrogate 모델 artifact를 둔다
(실 artifact는 S3, 여기엔 참조/메타). ERD 매핑: CANDIDATE.artifact_uri + is_winner +
git_tag(`gen-NNN-best`). 구현은 plan 승인 후.
