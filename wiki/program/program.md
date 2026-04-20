---
type: program-rules
title: "연구 프로그램 운영 헌법 (program.md)"
date: 2026-04-19
status: active
owners: [serithemage@gmail.com]
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
---

# program.md — 운영 헌법

본 문서는 통합 연구 프로그램의 최상위 운영 규칙을 정의한다. overview spec §7의 구체화이며, 에이전트·운영자·평가자 모두가 참조해야 하는 공통 기반이다.

## 규칙 R1–R7

### R1. 작은 reversible patch만
- 모든 변경은 **되돌릴 수 있는 단위**여야 한다. baseline 직접 덮어쓰기 금지.
- `promotion_policy.md`의 승격 절차를 거친 patch만 baseline으로 승격.

### R2. 모든 claim은 evidence로 뒷받침
- wiki 페이지는 `confidence`, `contradiction`, `last_verified` 필드 필수.
- evidence-free 단정형 주장 금지. K1/K2 자료 링크 또는 자체 실험 run ID로 뒷받침.

### R3. Negative result도 자산
- 실패는 `wiki/failures/`에 first-class citizen으로 축적. 삭제 금지.
- 동일 finding의 재발견은 `L2.lint` duplicate-finding rule로 자동 감지 (overview spec §5.2-1).

### R4. 감독은 운영자 책임
- 에이전트 자동 결정은 JSONL trace로 로깅되며 **사후 감사 가능**해야 한다.
- Promotion(`scoring.md` 참조) 승인은 운영자 수동. 에이전트 자동 promotion 금지.

### R5. Process > 수치
- 논문 claim의 일부는 **reasoning trace 자체**다.
- PPA 수치가 나오지 않아도 프로그램은 진행. kill 조건은 overview spec §5.3 canonical table만이 결정한다.

### R6. Evaluator separation
- trace 생성 LLM ≠ trace 평가 LLM family (overview spec §4.3 H3).
- Claude가 생성 → Codex 또는 인간이 평가. 역도 성립.
- H3의 주 평가자는 **인간**. LLM 평가는 보조.

### R7. Pre-registration
- 실험 설계(sample size, threshold, exclusion list, seeds)는 실험 개시 전 git tag로 freeze.
- 사후 조정은 해당 회차 실험 무효 (overview spec §5.2).

## 규칙 변경 절차

본 문서의 수정은 overview spec 재승인 절차를 따른다. R1–R7 자체의 변경은 프로그램의 identity 변경이므로 사용자(serithemage) 명시 승인 필요. rule 추가는 허용되나 R1–R7 번호 재지정은 금지 (외부 참조 보호).
