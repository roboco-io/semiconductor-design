---
id: 001
title: Planner의 structural mutation operator 설계 (구 crossover 알고리즘)
status: open (재정의 2026-04-19)
type: design-decision
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md#10
layer: L3
iteration: G3
blocks: [L3 파생 spec]
---

# 001. Planner의 structural mutation operator 설계 (구 crossover 알고리즘)

## 재배치 노트 (2026-04-19)

원 이슈는 구 spec의 evolutionary loop 맥락. 통합 프로그램 overview spec §10에서 본 이슈는 **L3 파생 spec 범위**로 재배치되며, 단순 parameter crossover가 아니라 **Open-Ideation 에이전트의 structural mutation operator 설계**로 재정의된다.

핵심 질문: parameter vector 조합이 아닌 **구조적 변주 생성 전략**을 어떻게 설계할 것인가. 여기서 "구조적"은 overview spec 부록 C.1~C.4 knob exclusion list에 **없는** transform을 의미한다. H1b "non-knob structural patch" 지표(§4.1·§5.1) 달성이 본 이슈의 평가 기준.

새 옵션 도출은 L3 파생 spec 작성 시점에 수행. 아래 원본 내용은 history로 유지.

---

## 배경

Planner 에이전트는 세대마다 10개 후보를 생성한다. 4가지 mutation_kind 중
`crossover`는 이전 세대 Top-2 후보의 파라미터를 결합하는 역할인데,
구체 알고리즘이 spec 단계에서 결정되지 않았다.

## 옵션

| ID | 알고리즘 | 장점 | 단점 |
|---|---|---|---|
| A | LLM이 두 부모 파라미터를 보고 새 자식 직접 제안 | 컨텍스트 반영, novelty 강조 | 비결정적, 재현성 약함 |
| B | NSGA-II 스타일 Simulated Binary Crossover + LLM이 변이만 담당 | 확립된 알고리즘, 재현성 | 구현 복잡, LLM 기여 축소 |
| C | 토너먼트 선택 + 파라미터별 균일 교차 | 단순, 빠름 | 탐색 다양성 낮음 |

## 결정 기준

- W4까지 Planner 구현 완료 필요
- gen 3까지 Pareto hypervolume 증가율이 Random DSE(B4) 대비 유의미하게 높은 옵션 채택
- 이터레이션 1에서는 A를 기본값으로 두고 W4 중반 실측 후 B/C 전환 검토

## 액션 아이템

- [ ] W3 종료 시 3개 옵션 각각을 10 candidate × 3 gen로 dry-run 스텁 비교
- [ ] 결정 후 `src/agents/planner.py`에 구현
- [ ] spec §16 업데이트 후 이 이슈 closed
