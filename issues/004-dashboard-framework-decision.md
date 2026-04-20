---
id: 004
title: Observability 대시보드 scope 재평가 (L1 operational vs L3 scientific)
status: open (scope 재평가 2026-04-19)
type: design-decision
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
layer: L1 or L3 (선행 질문)
iteration: G1 또는 G3
blocks: []
---

# 004. Observability 대시보드 scope 재평가 (L1 operational vs L3 scientific)

## 재배치 노트 (2026-04-19)

통합 프로그램 overview spec은 Iter 1 MVP 범위에서 대시보드를 **선택 사항**으로 둔다 — 관측성은 L1 Process의 CloudWatch + DDB 쿼리로 최소 확보 가능(spec §8·§11). 본 이슈의 **선행 질문**은 대시보드가 L1인지 L3인지.

- **L1 operational 관점**: candidate status, cost, Spot 회수율, KG-A~KG-E 통과 현황, lockfile 검증 — 운영자가 실험 진행을 감시
- **L3 scientific 관점**: Pareto frontier, finding corpus 성장, skill library reuse, complete H1a/H1b/H1c 대시보드 — 논문 figure 1차 대시보드

두 관점은 **서로 다른 대시보드**가 될 수 있다. L1/L3 파생 spec 작성 단계에서 명확화. 아래 원 옵션 A/B/C는 구체 스택 비교 — 관점 선행 결정 후 재검토. History 유지.

---

## 배경

Observability UI는 "CloudFront + 정적 Next.js 대시보드"로 결정되어 있으나,
구체 템플릿·UI 라이브러리·차트 라이브러리 미정. Pareto front 시각화, 칩
floorplan 썸네일, 의사결정 로그 스트림이 주 렌더링 대상.

## 옵션

| ID | 스택 | 장점 | 단점 |
|---|---|---|---|
| A | Next.js (App Router) + shadcn/ui + Recharts | 생태계 풍부, shadcn 예제 많음 | 빌드 크기 중간 |
| B | Astro + Tailwind + ECharts | 정적 최적화, 빌드 크기 최소 | Next.js 대비 익숙도 낮음 |
| C | 단순 HTML + Alpine.js + Chart.js | 최소 의존성 | 확장성 낮음, 유지보수 추후 어려움 |

## 결정 기준

- S3/CloudFront에 올릴 빌드 산출물 크기 < 5MB
- DDB GSI 직접 조회(API Gateway + Lambda)로 SSR 불필요
- Pareto 3D 플롯 + 세대 timeline 렌더링 가능한지

## 액션 아이템

- [ ] W4 종료 전 3개 옵션 각각 PoC(페이지 1개, 차트 1개) 빌드해 크기·속도 비교
- [ ] W5 초반 확정, `web/` 디렉토리 스캐폴딩
