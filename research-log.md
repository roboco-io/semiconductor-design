# Research Log: EDA 영역 연구 주제 발굴 (제로베이스)

| # | Date | Phase | Summary |
|---|------|-------|---------|
| 1 | 2026-08-25 | Pivot | 완전 제로베이스 재피벗. 구 사이클(바이브코딩×H1.1) 자산 전량 제거, tag `archive/pre-eda-zerobase-pivot-2026-08-25` 보존. Operator 승인 완료. |
| 2 | 2026-08-25 | Literature Survey | 개시. Review protocol 고정: EDA 전 영역, exa 검색, 2024-2026 우선, 제약(1인+에이전트/오픈소스/로컬 컴퓨트/구독 CLI). 5개 병렬 조사 에이전트 파견 (RTL 생성 / 검증 / 오픈소스 EDA·물리설계 ML / 에이전틱 플로우 / 주변부 스캔). |
| 3 | 2026-08-25 | Literature Survey | 5개 축 조사 완료 (검색 27회, 46편 synthesis, citation 기각 0건). Cross-cutting 공백 5개 도출: 평가 위기 / 검증 병목 / 하네스 설계 지식 부재 / 비용 계측 부재 / 학습 축 부재. `literature/survey.md` + `raw/01-05` 작성. |
| 4 | 2026-08-25 | Lit Survey → Hypothesis Gen | Survey 완료. FluxBench(2026)의 "하네스 86% 격차, 설계 원리 미연구" 공백이 최대 발견. 가설 생성으로 이동. |
| 5 | 2026-08-25 | Hypothesis Generation | 루트 5개 + 서브 1개 생성 (H1 하네스 설계, H1.1 Token ROI, H2 교차 엔진 검증, H3 오염-내성 평가셋, H4 sign-off 해리, H5 학습 축 N=1, H6 다목적 튜닝). 전부 two-sentence test 통과. Judgment 심사안 작성 — Operator 승인 대기. |
| 6 | 2026-08-25 | Judgment | Operator 결정(issue 001): **H1을 주 가설로 승인**, H1.1 부속 승인. H2·H4 승인(H1 인프라 완성 후 순차), H5 승인(경량 병행), H3 REVISE(novelty 재조사), H6 DEFERRED. 프로젝트 제목 갱신. |
| 7 | 2026-08-25 | Judgment → Experiment Design | H1 실험 설계 진입. 최우선 falsification 경로: baseline 완주율이 이미 높으면(개선 여지 없음) 가설 무의미 — 스모크 단계에 baseline 측정 선행 배치. |
| 8 | 2026-08-25 | Experiment Design | H1 protocol **LOCKED v4**. Codex 게이트 4회 왕복(request_changes 3회 → approve): goalpost 고정, QoR·Token ROI 정의, 결정 트리 판정(전수 포괄), 태스크 쌍 절단 동수 N, 재시도 상한(셀 1·총 3), pre-flight/7일 기산 분리. 실행 개시는 Operator 지시 대기 — 개시 커밋 전 RTL/결과물 생성 금지. |
