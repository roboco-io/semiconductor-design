# 결정 brief — LODO↔T1 게이트 충돌 해소 (2026-06-20)

## 맥락
gen-006에서 강화된 program.md(승격 기준=LODO salience)로 winner cand-001이 **처음 LODO 통과**
(`generalizes_better`, 우세 2/3, 평균 −0.083)했으나, **T1에서 worse**(2.92 vs baseline 2.48, dz=2.89)
→ `rejected_t1`. 두 게이트가 *다른 것*을 측정한다:

- **LODO**: 설계 하나씩 전체 held-out → *미관측 설계* 분포-이동 강건성. (프로젝트 north star)
- **T1**: 50-fold repeated K-fold, 설계 *혼합* → *in-distribution* 정확도. (피벗 이전 단일설계 잔재)

winner는 교차설계 강건성을 얻는 대가로 혼합-CV 적합을 희생(robustness↔accuracy 트레이드오프). 내가
program.md에 "승격 기준=LODO"라 적었으나(Codex 승인) 실제 체인은 `median→LODO→T1→Codex`로 T1이
LODO와 부분 상반된 목표를 강제 → **stated bar ≠ enforced bar** 불일치.

## 선택지

### A. LODO가 바 — T1을 교차설계(group/leave-design-out) fold로 재정의 (권장)
- **요지**: T1의 fold 스킴을 혼합 K-fold → group-disjoint(설계 단위)로 바꿔, T1도 LODO와 *같은 것*
  (교차설계 일반화)을 통계적으로 검정. 게이트 체인이 stated bar와 정합.
- **pros**: "측정 대상이 옳다." 피벗의 north star(교차설계)와 일치. gen-006 winner처럼 진짜 일반화
  개선을 in-distribution 잣대로 차단하는 모순 제거. "옳은 걸 부정확하게 > 틀린 걸 정확하게."
- **cons**: 3설계뿐이라 group-fold는 ~3 fold → 통계 파워 급감(T1의 50-fold rigor 상실). 사실상 C(설계
  확보)와 결합해야 강한 결론. spec 변경 필요(validation.py 게이트 재정의).

### B. LODO+T1 공동요건 유지 — program.md를 "LODO AND in-distribution"으로 정정
- **요지**: winner는 교차설계 강건성 *및* in-distribution 정확도 둘 다 개선해야(Pareto). program.md의
  "승격 기준=LODO"를 "LODO + T1 둘 다"로 정정.
- **pros**: 보수적, 코드/spec 무변경, baseline 품질을 양축에서 보존. 즉시 루프 지속 가능(무비용).
- **cons**: 더 높은 바 — 승격이 드물어질 수 있음. 피벗의 교차설계 강조를 희석(in-distribution이
  동등 가중). 방금 강화한 힌트 메시지와 긴장.

### C. 설계 확보(Sub-A) 먼저 — 근본 원인(3설계 저표본) 해소 후 게이트 재설계
- **요지**: 3설계로는 어느 게이트도 통계적으로 빈약(LODO는 "probe only", group-T1은 3 fold). 설계를
  더 확보한 뒤 A를 파워 있게 구현.
- **pros**: 근본 원인 해소. A를 통계적으로 정당하게 만듦.
- **cons**: AWS 비용·시간·Operator per-instance 동의. 개념적 충돌 자체는 데이터만으로 안 풀림.

## 병행 (선택지와 독립)
- **2차 harness 갭 수정**: cand-000이 *산문+코드*(펜스 없음) 반환 → `_looks_like_source` 토큰 검사 통과
  → SyntaxError(inf). `ast.parse` 기반으로 강화(parseable 보장). 어느 선택지든 무관하게 적용 가능.

## 권장
**A** — 게이트가 *옳은 것*을 측정하게 만드는 게 우선. 단 3설계 저파워라 당장은 약한 결론이므로,
중기적으로 C(설계 확보)와 묶어 파워를 확보. B는 north star를 희석하므로 비권장.
(임계값 재정의는 spec 권한 — INTENT/plan은 인용만. A 채택 시 별도 spec에서 fold 스킴·임계값 nail down.)

## Operator 결정 (2026-06-20)
- **선택지 A 채택** (T1을 교차설계로 재정의).
- **A 내부 세부 — A2 채택**: T1을 *repeated leave-one-design-out 통계판*으로 만든다(방향성 단순화 A1
  대신). leave-one-design-out을 R seed로 반복(D×R fold)해 paired Wilcoxon/CI를 유지, T1이 LODO의 통계
  강화판이 되어 같은 축(교차설계)을 측정. 3설계 저파워는 상관 caveat 명기 + 중기 C(설계 확보)로 보강.
- 구현 spec: `docs/superpowers/specs/2026-06-20-crossdesign-t1-gate-design.md` (§4가 임계값 single source).
- 병행: 2차 harness 갭(산문+코드 → `ast.parse`)은 선택지와 독립으로 처리.
