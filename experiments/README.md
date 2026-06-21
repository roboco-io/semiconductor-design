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

## 📖 튜토리얼 시리즈 (12살도 이해하는 실험 이야기)

각 세대 폴더의 `README.md`는 그 실험을 **비전문가(12살)도 이해할 수 있는 이야기**로 풀어 쓴 튜토리얼이다
(비유: 점쟁이 기계·챔피언·깜짝 시험·심판). 본 프로젝트 novelty 축인 *비전문가 empowerment + 큰 흐름의
이해가능성*의 산출물. 새 세대 완료 시 `experiment-tutorial` 스킬로 생성한다.

| 세대 | 한 줄 이야기 | 결말 |
|---|---|---|
| [gen-001](gen-001/README.md) | 로봇이 사람 챔피언을 이겼어요 🏆 | 새 챔피언 등극(promoted) |
| [gen-002](gen-002/README.md) | 이긴 줄 알았는데 사실은 운이었어요 🎲 | 탈락 → 5번 시험(median) 규칙 |
| [gen-003](gen-003/README.md) | 검사관이 꼼수를 잡아냈어요 🕵️ | 탈락 → 정직함 검사관 도입 |
| [gen-004](gen-004/README.md) | 깜짝 시험에서 들통났어요 😲 | 탈락 → 깜짝 시험(LODO) 도입 |
| [gen-005](gen-005/README.md) | 또 졌고, 로봇이 잡담을 했어요 🙈 | 탈락 → 안전장치 보강 |
| [gen-006](gen-006/README.md) | 심판이 엉뚱한 걸 재고 있었어요 ⚖️ | 탈락 → 심판(T1) 고침 |
| [gen-007](gen-007/README.md) | "누가 이겼나"와 "확실히 이겼나"는 다른 질문 🤔 | 탈락(비김) → 두 심판 역할 분담 |
| [gen-008](gen-008/README.md) | 가장 큰 비밀을 알아냈어요 🔑 | 탈락(비김) → "점수↑ ≠ 새 칩에 강함" 확정 |
