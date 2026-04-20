---
type: program-rules
title: "Baseline 승격 정책 (promotion_policy.md)"
date: 2026-04-19
status: active
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
---

# promotion_policy.md — Baseline 승격 정책

Candidate / finding / skill이 baseline으로 승격되는 절차를 정의한다. `program.md` R1 "작은 reversible patch만, baseline 덮어쓰기 금지" 원칙의 구체 시행 규칙.

## 승격 대상

1. **Candidate → baseline** (G3 이후): 특정 설계가 새 baseline design이 되려면
2. **Finding → wiki canonical page**: raw finding이 정제된 wiki 페이지로 승격
3. **Skill → promoted skill**: 실험적 skill이 `skill_library`의 `promoted` 분류로 승격

## 공통 승격 절차

1. **Gate conditions 충족** — 각 승격 대상 별 조건(아래).
2. **Promotion proposal**: 운영자가 PR 형태로 승격 제안 (`promotion-proposal/<id>.md`).
3. **Blinded review**: 독립 평가자 N≥2 승인. `program.md` R6 evaluator separation 준수.
4. **Evidence freeze**: 승격 후 해당 baseline 경로에 `frozen.lock` 파일 생성. 수정 시 재승격 절차.
5. **CI re-verification**: 승격 이후 CI가 해당 baseline에 대해 smoke test 통과.

## Gate Conditions

### Candidate → baseline
- Seed × 3 재현 통과
- `sign_off_status == clean` (DRC + LVS + STA)
- Blinded audit N≥2 pass
- `L1.run(spec).metrics`가 기존 baseline 대비 **regression 없음** (area, power, freq 전 항목)

### Finding → wiki canonical page
- `confidence` 필드가 `medium` 이상
- `last_verified` 필드가 **90일 이내**
- `contradiction` 필드 비어있음 (또는 모든 contradiction 해결됨)
- Related evidence run ≥ 3건
- `wiki-lint` 경고 0

### Skill → promoted skill
- `skill.version >= 2` (반복 사용 증명)
- **독립 디자인 2개 이상**에서 적용 이력
- 각 usage마다 signed-off report attached
- Blinded audit N≥2 승인

## 금지 사항

- **Baseline 경로 파일의 직접 git push 금지.** 모든 변경은 promotion-proposal PR 경유.
- **Promotion 우회 자동화 금지.** 에이전트가 자동으로 baseline을 바꿀 수 없다. 에이전트는 제안만, 승인은 인간.
- **Regression test 생략 금지.** CI 재검증 실패 시 승격 rollback.

## 승격 실패 시

- Gate condition 미충족: candidate/finding/skill은 원래 경로에 유지. `promotion-rejected/<id>.md`에 사유 기록.
- Blinded review 부결: 동일 승격은 최소 **다음 iteration**까지 재제출 금지.
- CI regression 검출: 자동 rollback + `wiki/failures/`에 `promotion_regression` failure 기록.
