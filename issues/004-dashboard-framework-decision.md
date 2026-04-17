---
id: 004
title: 대시보드 프레임워크 최종 확정
status: open
type: design-decision
related_spec: docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md#5.1
iteration: 1
blocks: [W5]
---

# 004. 대시보드 프레임워크 최종 확정

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
