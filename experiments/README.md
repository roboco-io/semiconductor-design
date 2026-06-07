# experiments/ — 세대별 실험 리포트

serverless-autoresearch `experiments/` 아날로그. 세대(GENERATION)마다 후보·val 지표·winner를
디렉터리로 누적한다. 각 세대 디렉터리 구조: `candidates/cand-NNN/{train.py, art/model.joblib}`,
`results.tsv`(후보별 median_val_mae + per_seed_vals), `generation.json`(winner·status·eval_seeds).

## 누적 기록

| 디렉터리 | 내용 |
|---|---|
| `real-gcd-fargate/` | 진짜 EDA flow 산출(STA 리포트 + dataset 53행). `VALIDATION.md` 참고 |
| `gen-001/` | 첫 세대 — Codex winner 승격(tag `gen-001-best`, status `promoted`) |
| `gen-002/` | 두 번째 세대 — **reject**. 단일 seed winner가 5-seed median에선 baseline에 패배(위양성). `rejudge.md` 참고 |

ERD 매핑: GENERATION + 그 CANDIDATE/JOB 결과의 사람-읽기용 요약. 향후 연기된
process novelty(reasoning trace·decision·finding)의 부착점.
