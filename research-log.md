# Research Log: 반도체 설계에 유용한 SW/모델의 바이브 코딩 개발

| # | Date | Phase | Summary |
|---|------|-------|---------|
| 1 | 2026-08-25 | Pivot | 사이클 3 재시작. Operator 의도 명확화: "반도체 설계에 유용한 소프트웨어/모델을 바이브 코딩으로 개발"이 목표 — 하네스 연구(사이클 2)는 의도 불일치로 폐기(tag `archive/eda-harness-cycle-2026-08-25`). |
| 2 | 2026-08-25 | Field Survey | 개시. 조사 초점 변경: "무엇을 만들면 설계 현장에 유용한가" — 수요 근거(페인포인트·공백)와 1인 바이브 코딩 실행 가능성 중심. 5개 병렬 조사 에이전트 파견. |
| 3 | 2026-08-25 | Field Survey | 5축 완료(검색 31회, 기각 0건). 핵심 발견: ① 플로우 성숙·해석/관리 계층 공백 ② tabular QoR 예측 무주공산+CPU 가능 ③ 바이브 코딩 게이트 방법론 실증 선례(Normal Computing 580K줄 등) ④ 유용성 객관 검증 경로 명확(WOSET/JOSS/시간절감표). 후보 9개(C1-C9) 도출. `literature/survey.md`. |
| 4 | 2026-08-25 | Survey → Hypothesis Gen | 후보를 가설 5루트+1서브로 정식화 (H1 실험추적 도구→H1.1 QoR 예측기, H2 STA 분석기, H3 log doctor, H4 검증 관리, H5 IR drop 모델). 결정 브리프 issue 001 작성 — Operator 선택 대기. 권고: A(H1→H1.1). |
| 5 | 2026-08-25 | Judgment | Operator 결정: **A/B/C/D 4트랙 전부 승인, 병렬 구현·검증 방침**. H1·H1.1·H2·H3·H5 approved, H4 DEFERRED(신생 경쟁 관찰). D는 IR drop 경량 모델(H5)로 구체화 — 포트폴리오 균형(도구 3+모델 1). |
| 6 | 2026-08-25 | Experiment Design (계획) | 4트랙 계획서 작성: `plans/README.md`(총괄·공통 방법론·의존성 그래프) + A/B/C/D 트랙별 계획서(스코프·판정 기준 초안·태스크 그래프·리스크). 착수 우선순위 A ≥ D > B > C. 다음: 트랙별 protocol LOCK(Codex 게이트) 후 구현. |
| 7 | 2026-08-25 | Execution 착수 | Operator "진행" 지시. 로컬 환경 확인(Docker ✓·brew ✓·EDA 툴 전무·10코어/32GB) 후 병렬 착수: **INFRA-0**(LibreLane+PDK+시뮬레이터 구축·스모크), **D1**(ICCAD'23 IR drop 데이터 정찰), **C1**(실패 사례 코퍼스 수집 ≥30건). 전부 pre-LOCK 단계 작업(구현 아님). 트랙 작업 공간: `../semiconductor-design-tracks/`. |
| 8 | 2026-08-25 | Execution | **INFRA-0 완료** (전 항목 성공): LibreLane 3.0.11 dockerized + SKY130 + 스모크 80/80 + SPM 완주(DRC 0·LVS 0). A·B·C 선행 의존성 해소. **D1 완료**: 데이터 접근 리스크 해소(hidden 정답 공개·점수표 확보). **C1 완료**: 46건 코퍼스(9단계, 해결책 93%). |
| 9 | 2026-08-25 | Experiment Design | **트랙 D protocol LOCKED v6** — Codex 게이트 6차 왕복(request_changes 5회 → approve). 핵심 규율: fold별 전처리 통계(누출 차단), 절차적 홀드아웃 명시, 비교자 SHA 고정(Alpha-Chip@f41862cd), 전 레시피 동결, 예산 32h/28h + 하드스톱, 결정 트리 전수 포괄. |
| 10 | 2026-08-25 | Execution (D) | D 사전등록 체인 ② 완료: 데이터 클론 .git 삭제, hidden 10케이스 vault 격리(chmod 000)+SHA256 매니페스트 51파일 커밋. D2 구현 에이전트가 채점기·파이프라인·V1 구현 후 **V1 그리드 탐색 실행 개시**. C1.5 분할 매니페스트(개발 32/홀드아웃 14, 시드 42) 사전등록 커밋. |
| 11 | 2026-08-25 | Experiment Design | **트랙 A protocol LOCKED v5** — Codex 5차 왕복(4회 request_changes → approve). 특기: Codex가 venv 소스 검증으로 사실 오류(PL_TARGET_DENSITY→_PCT canonical 키) 적발. spm 21-run 코퍼스·전수 원문 토큰 정합·도구 불리 보수 실패 규칙·Release 앵커 60일 채택 창. A 인프라 에이전트 파견(코퍼스 스크립트+오라클+캠페인 개시). C protocol v2 Codex 재심사 진행 중. |
| 12 | 2026-08-25 | Execution (D) | V1 탐색 종결(18/36 — §8 축소 ①② 결정적 발동, 산술 로그 보존). 채점기 교차검증 완전 통과(75쌍, MAE 상대차 0·F1 전부 일치). 중간 신호: V1 최고 fold MAE 4.199e-4(게이트 3.649e-4 미달), **hotspot F1 0.01 미만** — tabular의 공간 구조 한계 시사. V2(U-Net) 단계 진입(fake 50 사전학습). A/C 트랙: 실행 개시 커밋 완료, hwtrack 구현·룰 개발 에이전트 가동 중. |
| 13 | 2026-08-25 | Execution → 판정 (C) | **H3 refuted** — 홀드아웃 hits 0/11 (Codex 심사 2건 포함 전부 miss), 재대입 32/32 대비 과적합 실증. 오진 0(unknown 정직 출력). Negative result를 유효 마일스톤으로 기록, `results.md` 작성. 후속 가설(H3.1: LLM 계층 부가 가치)은 Reflection에서. |
| 14 | 2026-08-25 | Execution (A) | hwtrack Codex 코드 리뷰(K3) request_changes 5건 — key-path 충돌(K1 감사 우회 가능), nested 파라미터 diff 누락(K2b 위반) 등 실질 버그. 구현 에이전트에 수정 지시. 21-run 캠페인·D V2 학습 계속. |
| 15 | 2026-08-25 | Execution → 판정 (A) | **H1 refuted** — K1 완벽 통과(8,837키 불일치 0)·정확도 전건 일치였으나 K2 절감 24%<50%. 원인: 수행 주체=AI 에이전트라 수작업 baseline이 수 초(jq 원라이너) + scan 고정비 지배(21 run 소규모). "도구 가치는 주체·규모에 상대적" — 재정식화 방향은 Reflection에서. K3는 Codex 3차 왕복 approve(실질 버그 7건 수정). |
