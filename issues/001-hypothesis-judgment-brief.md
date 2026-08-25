# issue 001: Judgment Gate 결정 브리프 — 주 연구 방향 선택

날짜: 2026-08-25 · 상태: OPEN (Operator 결정 대기)
근거: [`literature/survey.md`](../literature/survey.md) · 가설 전문: [`research-tree.yaml`](../research-tree.yaml)

## 심사 요약표

| H | 한 줄 요약 | Novel | 중요도 | 실행성 | 반증성 | 미해결 | 권고 |
|---|---|---|---|---|---|---|---|
| H1 | EDA 하네스 설계 → 범용 에이전트 완주율 ≥2배 | Y | HIGH | Y | Y | Y | **APPROVE** |
| H1.1 | 하네스별 Token ROI 2배+ 차이, 구독 요금제 실측 | Y | MED | Y | Y | Y | APPROVE (H1 부속) |
| H2 | 교차 엔진 검증 → mutation 검출률 +10%p | Y | HIGH | Y | Y | Y | **APPROVE** |
| H3 | TT 코퍼스 오염-내성 평가셋 → pass@1 하락 | ? | MED | Y | Y | ? | REVISE (novelty 재조사) |
| H4 | 기능 pass RTL의 >30%가 sign-off 실패/PPA 열화 | Y | HIGH | Y | Y | Y | **APPROVE** |
| H5 | N=1 종단: 성과-학습 해리 + 퀴즈 게이트 분리 측정 | Y | MED | Y | Y | Y | APPROVE (사례연구 한정) |
| H6 | LLM 다목적 ORFS 튜닝 > AutoTuner | N | MED | Y | Y | Y | DEFER |

## 방향 선택지 (루트 가설은 순차 실행 — 첫 착수 대상을 고르는 결정)

### A. H1 하네스 설계 연구 (권장)
**Summary**: "범용 코딩 에이전트 + EDA 스킬/하네스"의 설계 원리를 실험으로 규명. FluxBench 지표(완주율·QoR·Token ROI)로 측정.
- **Pros**: ① 문헌이 명시한 공백(FluxBench 2026)이고 공인 비교 지표 존재 ② Operator의 강점(에이전트 하네스 설계 경험)과 정합 ③ H1 실험 인프라(로컬 ORFS 플로우)가 H4·H2의 기반 인프라와 동일 — 후속 가설 재사용 ④ 결과가 negative여도(하네스 무효) FluxBench 반박으로 가치
- **Cons**: ① FluxBench 재현에 환경 구축 비용 선불 ② 신생 벤치마크라 태스크 셋 안정성 리스크 ③ 전용 에이전트 시스템과의 절대 격차는 1인 규모로 못 좁힐 수 있음(주장 범위를 baseline 대비로 한정 필요)

### B. H4 sign-off 해리 정량화 (빠른 첫 결과)
**Summary**: VerilogEval류 통과 RTL을 LibreLane sign-off 게이트에 통과시켜 기능 정합-실무 사용성 해리를 정량화.
- **Pros**: ① 실험 구조 단순(기존 벤치마크 산출물 + 로컬 flow) — 최단 시간 첫 결과 ② ChiPBench의 "중간지표≠최종성능" 논지를 RTL 레벨로 확장하는 명확한 novelty ③ 결과가 어느 쪽이든 정보 가치
- **Cons**: ① 벤치마크 실행(모델 추론) 규모가 구독 CLI 한도와 충돌 가능 ② "측정 논문" 성격이라 후속 연구 방향 견인력이 A보다 약함

### C. H2 교차 엔진 검증 (검증 병목 정면)
**Summary**: 생성≠심사 구도의 testbench 품질을 mutation 검출률로 체계 비교.
- **Pros**: ① 분야 최대 병목(검증) 직결, HIGH 중요도 ② 본 프로젝트 불변 원칙(생성≠심사)을 연구 주제화 — 운영 경험이 곧 도메인 지식 ③ 전 과정 로컬(Verilator+mutation)
- **Cons**: ① mutation 셋 설계가 결과를 좌우 — 방법론 공격면 넓음 ② CorrectBench 계열 후속작이 빠르게 나올 수 있는 경쟁 영역

### D. H5 학습 축 N=1 종단 (최저 경쟁 밀도)
**Summary**: Operator 본인의 설계-학습 사이클을 퀴즈 게이트로 분리 측정하는 사례 연구.
- **Pros**: ① 경쟁 밀도 최저, Krupp 2026이 공백 명시 ② 이전 사이클 INTENT와 연속성 — 기존 사고 자산 재활용 ③ 다른 가설 실행 위에 얹어 병행 가능
- **Cons**: ① N=1 단독으로는 학술 기여 폭이 좁음(사례 연구 한정) ② 자기 측정의 객관성 문제(루브릭·채점 분리 필수) ③ 단독 주제로는 "EDA 연구"보다 "교육 연구"로 분류될 위험

## 권고

**A(H1)를 주 가설로 승인·착수하고, H1.1을 부속 측정으로 동반. H5는 사이클 위에 경량 병행(퀴즈 게이트만), H4·H2는 H1 인프라 완성 후 순차 재입장. H3은 novelty 재조사 후 재심사, H6은 DEFER.**

이유: H1의 실험 인프라(로컬 RTL→GDS 플로우 + 계측)가 H4·H2·H5의 실행 기반을 겸하므로, 어떤 순서로 가더라도 H1 인프라가 선행 투자가 된다. 그렇다면 문헌 공백이 가장 명확하고 비교 지표가 공인된 H1을 먼저 소진하는 것이 정보 가치/비용 비가 최대.
