# data/raw/ — 데이터 참조 (skeleton)

serverless-autoresearch `data/raw/` 아날로그. 실데이터(feature/label shard, tokenizer 등)는
S3에 두고, 여기에는 참조·매니페스트만 둔다.

ERD 매핑: **DATASET** 엔티티 (source_design, feature_set, label_metric, s3_uri,
flow_lockfile_sha). `prepare.py`가 EDA flow 1회 실행으로 생성. 구현은 plan 승인 후.
