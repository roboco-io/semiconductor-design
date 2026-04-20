---
id: 002
title: Fargate Spot retry/fallback 정책 (구 Spot vs On-Demand 혼합)
status: partially-resolved (Spot 확정 2026-04-19; 재시도 정책만 남음)
type: design-decision
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md#8
layer: L1
iteration: G1
blocks: [L1 파생 spec, KG-D pass]
---

# 002. Fargate Spot retry/fallback 정책 (구 Spot vs On-Demand 혼합)

## 재배치 노트 (2026-04-19)

Fargate Spot 사용은 overview spec §6 아키텍처에서 확정됨. 이 이슈는 이제 **재시도 + fallback 정책**으로 축소되고 L1 파생 spec + **G1 kill gate KG-D** (§8) 대응 범위.

- **KG-D 기준**: 긴 PnR(>20분) job이 Spot pre-emption 후 **최대 2회 재시도로 완주율 ≥ 80%**.
- 아래 원 옵션 C(Fallback 큐)가 KG-D 충족 시 기본. 미달 시 B(세대 후반 On-Demand 강제) 혼합.

실측 기반 결정은 L1 파생 spec 작성 중 진행. 아래 원본 내용은 history로 유지.

---

## 배경

비용 가정은 모든 job이 Fargate Spot에서 실행되는 것을 전제로 한다.
그러나 Spot 회수율이 리전·시간대에 따라 급변할 수 있고, 세대 내 마지막
몇 개 candidate가 반복 회수되면 전체 세대 진행이 막힌다.

## 옵션

| ID | 정책 | 장점 | 단점 |
|---|---|---|---|
| A | 100% Spot, Step Functions Retry(MaxAttempts=2)만 | 비용 최저 | 세대 완주 실패 리스크 |
| B | 세대 후반(예: 마지막 2 candidate)은 On-Demand 강제 | 완주 보장 | 비용 증가 추정 10-20% |
| C | Fallback 큐: Spot 3회 실패 시 자동 On-Demand 재시도 | 적응적 | 구현 복잡, 관찰성 필요 |

## 결정 기준

- W2-W3에 실측한 **리전별 Spot 회수율**
- us-east-1 기준 회수율 >15%이면 B 또는 C 필요
- 비용 초과 폭이 세대당 $1 이내면 B 채택

## 액션 아이템

- [ ] W2: CloudWatch로 Spot 회수 메트릭 수집 (최소 30 task)
- [ ] 회수율 기준 결정 매트릭스에 따라 옵션 선택
- [ ] CDK `ComputeStack.ts`에 정책 반영
