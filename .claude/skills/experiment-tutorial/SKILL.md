---
name: experiment-tutorial
description: 한 세대(gen-NNN) 실험이 끝나면 비전문가도 이해할 수 있는 튜토리얼 README를 그 폴더에 생성한다. 실험 전제·전개·결과·인사이트를 명료하게 서술하되, 전문 용어는 처음 나올 때 풀어서 해설한다. 트리거 — "gen-NNN 튜토리얼 만들어줘", "실험 튜토리얼", "실험 README 정리", 또는 AutoResearch 루프로 새 세대가 완료된 직후 결과를 정리할 때.
---

# experiment-tutorial — 실험 튜토리얼 생성

AutoResearch EDA-surrogate 루프의 한 세대(`experiments/gen-NNN/`)가 끝나면, **이 분야를 처음 접하는
사람도 따라올 수 있는** `README.md`를 그 폴더에 만든다. 이 프로젝트의 novelty 축인 *비전문가
empowerment + 큰 흐름의 이해가능성*을 산출물로 구현하는 스킬.

## 핵심 원칙 — "쉽게 = 용어 해설 + 명료함", "쉽게 ≠ 유치한 말투"
- **전문 용어는 풀어서 해설한다.** 어떤 용어든 처음 나올 때 괄호나 짧은 절로 그 뜻을 설명한다.
  (예: "val_mae(검증 데이터에서의 평균 예측 오차, 낮을수록 정확)").
- **톤은 차분하고 전문적인 설명체(`~합니다`/`~입니다`)다.** 성인 독자를 존중하는 명료한 글로 쓴다.
- **금지**: 어린이에게 가르치는 듯한 말투(`~했어요`체), 억지 의인화·동화풍 비유(점쟁이·챔피언·
  깜짝시험·로봇 요리사·꾀돌이 등), 이모지 남발, 과장된 감탄. 비유는 꼭 필요할 때만 한 번, 절제해서.
- 목표는 "12살도 읽을 수 있다"이지 "12살에게 말한다"가 아니다. 정확성을 낮추지 말고, *진입 장벽*만 낮춘다.

## 언제 쓰나
- 새 세대 루프(`make loop` / `orchestrator.py`)가 끝나 `generation.json`이 생긴 직후 — **결과 정리의 마지막 단계로 항상 호출**.
- 기존 세대에 튜토리얼이 빠졌거나 톤을 정비할 때.

## 입력 (그 폴더에서 읽는다 — 추측 금지)
- `experiments/gen-NNN/generation.json` — gen_no, status, winner_candidate_id, winner_val_mae, lodo_verdict, dataset.
- `experiments/gen-NNN/results.tsv` — 후보별 median_val_mae·sdk·strategy.
- `experiments/gen-NNN/report.md` (있으면) — LODO/T1/Codex 게이트 표와 verdict.
- `experiments/gen-NNN/candidates/cand-*/train.py` — 각 후보가 실제로 시도한 모델/feature 전략(구체 서술의 근거).
- 보조 파일(`revalidation.md`·`rejudge.md`·`crossdesign-t1-reeval.md` 등)이 있으면 함께 반영.
- 직전 세대 README(`gen-(NNN-1)/README.md`)를 읽어 **맥락을 잇는다**.
- 코드 구조가 필요하면 [`docs/TRAIN.md`](../../docs/TRAIN.md) 참조.

## 용어 해설 사전 (처음 등장 시 이렇게 풀어 쓴다 — 비유가 아니라 정의)
| 용어 | 풀어쓴 설명 |
|---|---|
| surrogate 모델 | 칩 설계를 끝까지 진행하지 않고도 최종 타이밍 성능을 예측하는 회귀 모델 |
| `train.py` | surrogate를 학습시키는 스크립트. 에이전트가 변형하는 유일한 파일 |
| 에이전트(claude/codex) | `train.py`를 자동으로 변형하는 LLM |
| `val_mae` | 검증 데이터에서의 평균 예측 오차(MAE). 낮을수록 정확 |
| baseline | 현재 기준 모델. 직전까지의 최고 모델이며, 후보는 이를 이겨야 승격 |
| median(5-seed) | 5개 시드로 학습·평가한 val_mae의 중앙값. 데이터가 적을 때 운에 의한 변동을 억제 |
| LODO | Leave-One-Design-Out. 설계 하나를 학습에서 빼고 그 설계로만 평가해 *미지 설계* 일반화를 측정 |
| 교차설계 T1 | LODO를 여러 시드로 반복해 baseline 대비 개선이 통계적으로 유의한지 검정하는 게이트 |
| Codex 게이트 | 후보를 만든 LLM과 다른 LLM(Codex)이 코드를 읽어 평가 누수·꼼수를 점검하는 심사 |
| 승격(promote) | 후보가 모든 게이트를 통과해 새 baseline이 되는 것 |
| 설계(design/group_key) | gcd·aes·ibex·jpeg 등 서로 다른 회로 설계. 설계마다 데이터 분포가 다름 |

상태(status) 해설: `promoted`=승격(새 baseline) / `rejected`·`rejected_*`=미승격(baseline 유지),
이유는 `_lodo`=LODO 미통과, `_t1`=통계적으로 유의한 개선 아님, `_codex`=Codex가 평가 누수/꼼수 적발.

## README 형식 (섹션 순서를 지킨다 — 이모지는 헤더에만, 절제)
```
# 세대 N — 한 줄 요지 (간결한 제목)
> 2~3문장 개요: 이 세대의 질문과 결과를 압축.
## 실험 전제          — 이 세대가 던진 질문과 배경. 직전 세대에서 이어지는 맥락.
## 방법               — 데이터(설계·샘플 수), 후보들이 시도한 모델/feature 전략, 적용한 게이트.
## 결과               — 실제 수치(후보별 val_mae, 게이트 verdict)를 표와 함께. 무엇이 만들어졌나.
## 분석               — 결과가 의미하는 바. 핵심 한 가지와 그 근거.
## 다음 세대로        — 다음 세대 README 링크(없으면 후속 방향).
## 용어               — 이 세대에 처음 등장한 용어 3~6개를 정의로 해설.
```

## 규칙
- **수치는 산출물에서 그대로** 인용(반올림 OK, 지어내기 금지).
- 한 문단에 한 논점. 전문 용어는 처음 쓰기 직전에 해설한다.
- **솔직하게**: 미승격도 "실패"가 아니라 게이트가 무엇을 걸러냈는지로 설명한다. 승격 0건 세대도
  baseline 오염을 막은 결과로 서술하되, 과장하지 않는다.
- 분량은 충실하되 군더더기 없이(80~140줄 권장). 정확성 우선.

## 마무리
1. `experiments/gen-NNN/README.md` 작성.
2. `experiments/README.md`의 튜토리얼 시리즈 인덱스에 한 줄 추가(있으면, 같은 톤으로).
3. Operator에게 "세대 N 튜토리얼 생성 완료 + 한 줄 핵심"만 보고.

> 참고: `.claude/skills/` 변경은 세션 재시작 후 활성화된다(CLAUDE.md staleness invariant).
