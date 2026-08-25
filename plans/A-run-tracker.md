# 트랙 A 계획서 — RTL-to-GDS 실험 추적 도구 → QoR 조기 예측기

가설: H1(도구), H1.1(모델) · 근거: [raw/04](../literature/raw/04-workflow-tool-gaps.md), [raw/02](../literature/raw/02-ml-model-opportunities.md)

## 목표

**Phase 1 (H1)**: ORFS/LibreLane run 디렉토리와 METRICS2.1 JSON을 자동 수집·인덱싱해 run 목록, run 간 PPA 디프, 파라미터-결과 상관을 보여주는 로컬 도구 — "하드웨어판 MLflow". 어느 기존 도구(ORFS·AutoTuner·SiliconCompiler·FuseSoC)에도 없는 기능임이 전수 비교로 확인된 공백.

**Phase 2 (H1.1)**: Phase 1이 축적한 데이터로 tabular QoR 조기 예측기(XGBoost/LightGBM)를 학습 — synth/place 단계 메트릭에서 post-route WNS/전력/면적을 예측, AutoTuner 조기중단 추천으로 통합.

## MVP 스코프 (Phase 1)

- `hwtrack scan <dir>`: run 디렉토리 재귀 스캔 → METRICS2.1 JSON + 플로우 설정(config) 파싱 → SQLite 인덱스
- `hwtrack list / show <run>`: run 목록·상세 (설계, PDK, 파라미터, 단계별 메트릭)
- `hwtrack diff <A> <B>`: 두 run의 파라미터·메트릭 차이 표
- `hwtrack web`: 로컬 정적 대시보드 (run 테이블, PPA 추이, 파라미터-결과 산점도)
- 지원 대상: ORFS(METRICS2.1)와 LibreLane(state/metrics) 두 포맷 — 버전 태깅

비스코프(명시): 원격 서버·팀 공유 기능, 상용 툴 포맷, run 실행 오케스트레이션(기존 도구 존중).

## 유용성 판정 기준 (protocol에서 LOCK할 항목 — 초안)

| 축 | 기준(초안) | 방법 |
|---|---|---|
| 정합성 (필수) | 수집 값 = 원본 JSON 100% 일치 | golden diff 테스트 (ORFS 예제 run 전수) |
| 시간 절감 | run 비교 작업의 전/후 소요 시간 표 (DVCon 형식) | 도그푸딩: 파라미터 스윕 분석 시나리오 N회 측정 |
| 외부 사용 | 공개 후 사전 고정 기간 내 외부 사용 증거(제3자 이슈/PR/사용 보고) 발생 여부 | GitHub 지표 + 커뮤니티 공유(ORFS discussions, TT Discord) |

정확한 임계값·기간은 착수 전 protocol LOCK에서 고정(Codex 게이트).

## 태스크 그래프

```
INFRA-0(EDA 환경) ─→ A1 ─→ A2 ─→ A3 ─→ [H1 판정] ─→ A4 ─→ A5 ─→ [H1.1 판정] ─→ A6
```

| ID | 태스크 | 산출물 | 의존 |
|---|---|---|---|
| A1 | 수집기: METRICS2.1/LibreLane 파서 + SQLite 스키마 + golden diff 테스트 | 파서 모듈, 테스트 스위트 | INFRA-0 (예제 run 생성용) |
| A2 | CLI(list/show/diff) + 로컬 웹 대시보드 | v0.1 릴리스 (public) | A1 |
| A3 | 도그푸딩 + 데이터 캠페인: ORFS 예제 설계(GCD·IBEX·AES 등) × 파라미터 스윕 run 수집 (H1.1 학습 데이터 겸용) | run 데이터셋 + 시간 절감 측정 기록 | A2 |
| A4 | QoR 예측기: 피처 파이프라인 + XGBoost/LightGBM, leave-one-design-out 스플릿 | 모델 + 평가 리포트 | A3 |
| A5 | EDA-Schema 프로토콜 비교(OpenROAD 자체 추정치 대비 MAE) + AutoTuner 조기중단 플러그인 | 비교 리포트, 플러그인 | A4 |
| A6 | WOSET/JOSS 제출 준비 (문서·CI·재현 아티팩트) | 제출물 | A5 |

## 리스크

- **run 데이터 생성의 캘린더 시간**: 스윕 1 run당 수 분-수십 분(소형 설계) — A3를 백그라운드 상시 실행으로 설계, 트랙 최우선 착수 이유.
- **LibreLane/ORFS 포맷 변화**: 파서를 버전 태깅 + 스키마 회귀 테스트로 방어.
- **채택 실패 가능성**: 판정 기준에서 정합성·시간 절감(자체 측정 가능)과 외부 사용(통제 불가)을 분리 — 외부 사용 미달 시 부분 지지로 기록, negative도 유효.

## 저장소

- 트랙 저장소: 신규 public repo (Apache-2.0, roboco-io org) — 이름은 착수 시 결정
- 본 리포: protocol·판정 결과·연구 로그만
