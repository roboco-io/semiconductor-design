# Research Log — 반도체 설계 × 바이브 코딩

| # | Date | Phase | Summary |
|---|------|-------|---------|
| 1 | 2026-08-22 | Literature Survey | exa grounded 조사(citation 18건, issues/011)로 field understanding 확보: 설계 측정 표준(pass@k·METRICS2.1·sign-off), 실무 기준(OpenTitan V단계), 학습 측정(DLCI·pre/post), 성과-학습 해리(TUM RCT), novelty 공백(게이트×학습 단일 사이클 연구 부재) 식별. |
| 2 | 2026-08-25 | Hypothesis Gen | INTENT.md 가설을 판정 가능한 트리로 정식화: 루트 4개(H1 설계 사다리 도달, H2 학습 게이트 효과, H3 학습→설계 환류, H4 TT 제출 승인) + 서브 2개(H1.1 스모크 테스트, H2.1 해리 재현). 전부 two-sentence pitch 통과. 우선순위: H1.1 → H1 → H2 → H2.1 → H3 → H4. Operator 트리 승인. |
| 3 | 2026-08-25 | Judgment | 5기준 판정: H1·H2 APPROVED(5기준 통과), H1.1 APPROVED(novelty 낮으나 H1의 최저비용 반증 테스트), H2.1 APPROVED(H2 데이터 무임승차 관찰), H4 APPROVED(연구 주장 아닌 실무성 마일스톤으로 재분류), H3 DEFERRED(난이도-교락 미통제 — 사이클 5개 축적 후 재입장). Operator 확정. |
| 4 | 2026-08-25 | Experiment Design | H1.1 프로토콜 LOCKED: 4-bit adder, LibreLane+SKY130A+TT 템플릿, 판정 4항목(전수 테스트벤치 256/256·flow 완주·DRC 0/LVS clean/STA clean·7일 이내) 사전 고정, decision rule = 전부 충족 시 supported. 학습 축 파일럿(튜토리얼+퀴즈+Codex 채점) 동시 수행 명시. plan 커밋 ≠ results 커밋 규율 적용. |
