---
id: 002
title: Fargate Spot vs On-Demand 혼합 정책 확정
status: open
type: design-decision
related_spec: docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md#16
iteration: 1
blocks: [W3]
---

# 002. Fargate Spot vs On-Demand 혼합 정책

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
