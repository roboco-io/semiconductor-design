# Research Log: 반도체 설계에 유용한 SW/모델의 바이브 코딩 개발

| # | Date | Phase | Summary |
|---|------|-------|---------|
| 1 | 2026-08-25 | Pivot | 사이클 3 재시작. Operator 의도 명확화: "반도체 설계에 유용한 소프트웨어/모델을 바이브 코딩으로 개발"이 목표 — 하네스 연구(사이클 2)는 의도 불일치로 폐기(tag `archive/eda-harness-cycle-2026-08-25`). |
| 2 | 2026-08-25 | Field Survey | 개시. 조사 초점 변경: "무엇을 만들면 설계 현장에 유용한가" — 수요 근거(페인포인트·공백)와 1인 바이브 코딩 실행 가능성 중심. 5개 병렬 조사 에이전트 파견. |
| 3 | 2026-08-25 | Field Survey | 5축 완료(검색 31회, 기각 0건). 핵심 발견: ① 플로우 성숙·해석/관리 계층 공백 ② tabular QoR 예측 무주공산+CPU 가능 ③ 바이브 코딩 게이트 방법론 실증 선례(Normal Computing 580K줄 등) ④ 유용성 객관 검증 경로 명확(WOSET/JOSS/시간절감표). 후보 9개(C1-C9) 도출. `literature/survey.md`. |
| 4 | 2026-08-25 | Survey → Hypothesis Gen | 후보를 가설 5루트+1서브로 정식화 (H1 실험추적 도구→H1.1 QoR 예측기, H2 STA 분석기, H3 log doctor, H4 검증 관리, H5 IR drop 모델). 결정 브리프 issue 001 작성 — Operator 선택 대기. 권고: A(H1→H1.1). |
