---
name: experiment-tutorial
description: 한 세대(gen-NNN) 실험이 끝나면 12살도 이해할 수 있는 튜토리얼 README를 그 폴더에 생성한다. 실험 전제·전개·결과·인사이트를 일관된 비유(점쟁이/챔피언/깜짝시험/심판)로 서술. 트리거 — "gen-NNN 튜토리얼 만들어줘", "실험 튜토리얼", "12살 눈높이 README", 또는 AutoResearch 루프로 새 세대가 완료된 직후 결과를 정리할 때.
---

# experiment-tutorial — 12살 눈높이 실험 튜토리얼 생성

AutoResearch EDA-surrogate 루프의 한 세대(`experiments/gen-NNN/`)가 끝나면, 비전문가(특히 12살)도
"무엇을 알고 싶었고, 무슨 일이 있었고, 무엇을 배웠나"를 이해할 수 있는 `README.md`를 그 폴더에 만든다.
이 프로젝트의 novelty 축인 **비전문가 empowerment + 큰 흐름의 이해가능성**을 산출물로 구현하는 스킬.

## 언제 쓰나
- 새 세대 루프(`make loop` / `orchestrator.py`)가 끝나 `generation.json`이 생긴 직후 — **결과 정리의 마지막 단계로 항상 호출**.
- 기존 세대에 튜토리얼이 빠졌을 때 소급 생성.

## 입력 (그 폴더에서 읽는다 — 추측 금지)
- `experiments/gen-NNN/generation.json` — gen_no, status, winner_candidate_id, winner_val_mae, lodo_verdict, dataset.
- `experiments/gen-NNN/results.tsv` — 후보별 median_val_mae·sdk·strategy.
- `experiments/gen-NNN/report.md` (있으면) — LODO/T1/Codex 게이트 표와 verdict.
- 보조 파일(`revalidation.md`·`crossdesign-t1-reeval.md` 등)이 있으면 함께 반영.
- 직전 세대 README(`gen-(NNN-1)/README.md`)를 읽어 **이야기 흐름을 잇는다**.

## 고정 비유 사전 (항상 이 대응을 쓴다 — 세대 간 일관성)
| 기술 용어 | 12살 비유 |
|---|---|
| surrogate 모델 | 칩이 완성되기 전에 성능을 미리 맞히는 **점쟁이 기계** |
| `train.py` | 점쟁이를 가르치는 **레시피** |
| 에이전트(claude/codex) | 레시피를 맘대로 바꿔보는 **로봇 요리사** |
| `val_mae` | 예측이 실제와 얼마나 **빗나갔나**(작을수록 똑똑함) |
| baseline | 지금 1등 점쟁이 = **챔피언** |
| median(5 seed) | 운인지 보려고 **5번 시험봐 가운데 점수**로 판단 |
| LODO | 한 번도 안 가르친 칩으로 보는 **깜짝 시험** |
| 교차설계 T1 | 그게 운이 아니라 **확실한지** 통계로 따지는 **심판** |
| Codex 게이트 | 꼼수 없나 보는 **다른 회사 검사관** |
| promote | **새 챔피언 등극** |
| group_key/설계 | 서로 성격 다른 **칩 종류**(gcd·aes·ibex·jpeg) |

상태(status) → 결말 번역: `promoted`=새 챔피언 등극 🏆 / `rejected`·`rejected_*`=탈락(챔피언 유지),
이유는 `_lodo`=깜짝시험 패배, `_t1`=확실하지 않음(비김), `_codex`=검사관이 꼼수 적발.

## README 형식 (이 섹션 순서·이모지를 지킨다)
```
# 세대 N 이야기 — "한 줄 비유 부제" <이모지>
> 한 문장 요약 (이 세대에 무슨 일이)
## 🎯 알고 싶었던 것      — 이 세대의 질문(전제). 직전 세대에서 이어지는 맥락 한 줄.
## 🧪 우리가 한 일         — 전개. 어떤 칩·후보·게이트를 썼나.
## 📊 결과 (쉬운 말로)     — 실제 수치를 비유로. winner val_mae·게이트 verdict를 숫자와 함께.
## 💡 이 실험이 가르쳐준 것 — 인사이트. 한 문장 핵심 + 왜 중요한지.
## ⏭️ 다음 이야기          — 다음 세대 README로 링크(없으면 "앞으로의 모험").
## 💬 어려운 말 풀이        — 이 세대에 처음 나온 용어만 3~5개, 비유로.
```

## 규칙
- **수치는 report/generation.json에서 그대로** 인용(반올림은 OK, 지어내기 금지).
- 한 문장 = 한 생각. 어려운 말은 쓰기 전에 풀어준다. 전문용어는 괄호로 영어 병기(`깜짝 시험(LODO)`).
- **솔직하게**: 탈락도 "실패"가 아니라 "무엇을 배웠나"로 쓴다. 승격 0건 세대도 게이트가 위양성을 막은 성과로 서술.
- 분량은 12살이 끝까지 읽을 정도(50~70줄). 과장·칭찬 말고 이야기로.
- 세대 간 부제·이모지가 겹치지 않게(각 세대 고유의 "한 방"을 부제로).

## 마무리
1. `experiments/gen-NNN/README.md` 작성.
2. `experiments/README.md`의 튜토리얼 시리즈 인덱스에 한 줄 추가(있으면).
3. Operator에게 "세대 N 튜토리얼 생성 완료 + 한 줄 핵심"만 보고.

> 참고: `.claude/skills/` 변경은 세션 재시작 후 활성화된다(CLAUDE.md staleness invariant). 이 스킬을
> 막 만든 세션에서는 수동으로 위 형식을 따라 작성하고, 다음 세션부터 `/experiment-tutorial`로 호출.
