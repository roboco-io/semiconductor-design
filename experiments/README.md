# experiments/ — 세대별 실험 리포트

serverless-autoresearch `experiments/` 아날로그. 세대(GENERATION)마다 후보·val 지표·winner를
디렉터리로 누적한다. 각 세대 디렉터리 구조: `candidates/cand-NNN/{train.py, art/model.joblib}`,
`results.tsv`(후보별 median_val_mae + per_seed_vals), `generation.json`(winner·status·eval_seeds).

## 누적 기록

| 디렉터리 | 내용 |
|---|---|
| `real-gcd-fargate/` | 진짜 EDA flow 산출(STA 리포트 + dataset 53행). `VALIDATION.md` 참고 |
| `gen-001/` | 첫 세대 — Codex winner 승격(tag `gen-001-best`, status `promoted`). T1 게이트 소급 재심에서 H-A 엄밀 재확증(`revalidation.md`, verdict `distinguishable`, dz=−1.27) |
| `gen-002/` | 두 번째 세대 — **reject**. 단일 seed winner가 5-seed median에선 baseline에 패배(위양성). `rejudge.md` 참고 |

ERD 매핑: GENERATION + 그 CANDIDATE/JOB 결과의 사람-읽기용 요약. 향후 연기된
process novelty(reasoning trace·decision·finding)의 부착점.

## 튜토리얼 시리즈 (비전문가용 실험 해설)

각 세대 폴더의 `README.md`는 그 실험의 전제·방법·결과·분석을 **이 분야를 처음 접하는 사람도 따라올 수
있도록** 정리한 튜토리얼이다. 전문 용어는 처음 등장할 때 풀어서 해설한다(유치한 말투가 아니라 명료한
설명체). 본 프로젝트 novelty 축인 *비전문가 empowerment + 큰 흐름의 이해가능성*의 산출물이며, 새 세대
완료 시 `experiment-tutorial` 스킬로 생성한다.

| 세대 | 한 줄 요지 | 결과 |
|---|---|---|
| [gen-001](gen-001/README.md) | 에이전트가 사람 작성 baseline을 능가 | 승격(promoted) |
| [gen-002](gen-002/README.md) | 단일 seed 1등이 5-seed median에선 꼴찌(위양성) | 미승격 → median 평가 도입 |
| [gen-003](gen-003/README.md) | Codex가 평가 누수(cherry-pick)를 적발 | 미승격(rejected_codex) |
| [gen-004](gen-004/README.md) | 다설계 혼합 + LODO 게이트 첫 도입 | 미승격(rejected_lodo) |
| [gen-005](gen-005/README.md) | 산문 반환 가드 검증(후보 4/4 유효) | 미승격(rejected_lodo) |
| [gen-006](gen-006/README.md) | LODO 통과↔혼합 T1 충돌 → T1을 교차설계로 수정 | 미승격(rejected_t1) |
| [gen-007](gen-007/README.md) | LODO(방향성)와 교차설계 T1(통계 유의)의 역할 분담 | 미승격(rejected_t1) |
| [gen-008](gen-008/README.md) | 4설계(+jpeg)에서도 "val_mae 개선 ≠ 일반화 우위" 확정 | 미승격(rejected_t1) |
