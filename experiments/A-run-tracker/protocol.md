# 트랙 A 실험 프로토콜 — RTL-to-GDS 실험 추적 도구 (H1)

상태: **LOCKED v5** (2026-08-25, Codex 게이트 5차 심사 approve) — 이탈은 EXPLORATORY 라벨 필수
날짜: 2026-08-25 · 가설: [`research-tree.yaml`](../../research-tree.yaml) H1 · 계획: [`plans/A-run-tracker.md`](../../plans/A-run-tracker.md) · 환경: [`experiments/INFRA-0/environment.md`](../INFRA-0/environment.md)
주의: H1(도구)만 다룸 — H1.1(QoR 예측기)은 별도 프로토콜. 제약(불변): 구독 CLI만(metered 금지), 로컬 컴퓨트만, plan/results 커밋 분리.

## 1. 가설 (전사 — 재수정 금지)

**H1**: 게이트 기반 바이브 코딩으로 개발한 RTL-to-GDS 실험 추적·비교 도구(METRICS2.1 수집→run 디프·파라미터-결과 상관 대시보드)는, 사전 고정 유용성 기준(메트릭 수집 정합성 + 수작업 대비 run 비교 시간 절감 + 외부 사용 증거)을 충족한다.

## 2. 산출물 정의 (MVP 동결)

CLI `hwtrack`: `scan`(LibreLane run 디렉토리의 **`final/metrics.json`(메트릭) + `resolved.json`(run 파라미터 — 설정의 권위 원천)** 및 ORFS METRICS2.1 JSON → SQLite, 수치는 **원문 텍스트 보존 저장**), `list`/`show`, `diff <A> <B>`, `web`(run 테이블·PPA 추이·파라미터-결과 산점도). 파서는 비표준 JSON 토큰(`Infinity`/`NaN` — SPM 실측 존재) 허용 필수, `format_version` 태깅. 비스코프: 원격/팀 기능, 상용 포맷, run 오케스트레이션.

## 3. 검증 코퍼스 (본 문서에서 전면 동결 — 커밋 ②는 스크립트化만)

**(가) LibreLane 로컬 run 21개 — 설계·매트릭스 완전 열거**: 설계 = **`spm`**(LibreLane 3.0.11 동봉 예제, INFRA-0에서 완주 검증됨) 단일. 구성 = 기본 1 + `PL_TARGET_DENSITY_PCT`∈{35,45,55,65,75} (LibreLane 3.0.11 canonical 키 — 구 `PL_TARGET_DENSITY`는 deprecated alias로 resolved.json에 부재) × `CLOCK_PERIOD`∈{기본×0.7,×0.85,×1.0,×1.15} 격자 20 = **21 run**. run ID = `spm-d{밀도}-c{배율}`(기본=`spm-base`). run당 timeout 60분·재시도 0·직렬 실행. 실패 run도 코퍼스 포함(파서 검증 대상). **완주 15/21 미달 → 무효(T1)**.
**(나) ORFS 정적 코퍼스 (K1 전용, K2 비사용)**: `The-OpenROAD-Project/OpenROAD-flow-scripts` @ `427bd762b7b7448f8bb6bc4e14207aa3963fca30`의 glob `flow/designs/**/metadata*.json` 전수(clone 후 목록을 커밋 ②에 기록 — glob이 SHA에 대해 결정적이므로 사후 재량 없음).

## 4. 판정 기준 (사전 고정)

### K1. 수집 정합성 (필수)
- **대상 파일 = `final/metrics.json` + `resolved.json`(파라미터 정합도 K1에 포함) + ORFS 정적 코퍼스. 대상 필드 = 각 파일의 모든 수치 키 전수 + `resolved.json`의 K2 태스크 파라미터 키(`PL_TARGET_DENSITY_PCT`, `CLOCK_PERIOD` — 문자열/수치 불문)** (화이트리스트 없음 — 선별 재량 제거). 도구는 각 키의 **원문 토큰 문자열**을 보존 저장해야 하며, 독립 오라클(도구 코드와 무관, python stdlib + 정규식 토큰 추출)이 코퍼스 전 파일에서 키별 원문 토큰과 도구 DB 값을 **문자열 동일 비교**. 키 부재 = 도구도 부재(NULL)여야 일치. `Infinity`/`NaN` 토큰 포함. 1건 불일치 또는 키 누락 → K1 실패.
- K1 검증은 1차 창 내 완료 의무 — 미완은 무효(T1)이되, **실패가 이미 관측된 경우 관측이 우선**(§6 트리 순서).

### K2. 시간 절감 (합산 ≥50%)
- **모집단**: 코퍼스 (가)의 **완주 run만**. 변형 분할(동형·복잡도 균형): 밀도×클럭 격자의 **체스판 교대 배정** — (밀도 인덱스+클럭 인덱스)가 짝수 → 변형A, 홀수 → 변형B; `spm-base`는 변형A. 특정 태스크 필요 키가 결측인 run은 해당 태스크 모집단에서 제외(오라클이 기계 판별). **모집단 균형화(기계적)**: 완주·키충족 필터 후 태스크별로 A/B 유효 run 수를 `min(|A|,|B|)`로 맞추되 각 변형에서 run ID 사전순 앞에서부터 채택 — 판정 시 오라클이 자동 수행, 균형화 후 변형당 유효 run <4 이면 해당 태스크 무효(태스크 제외).
- **태스크 (정답 키 고정)**: (a) `magic__drc_error__count`=0 이면서 `timing__setup__ws` 최대인 run 식별(동률 시 run ID 사전순 최솟값) (b) 해당 변형 완주 run을 ID 사전순 정렬한 2번째·끝에서 2번째 쌍의 파라미터 차이 전부 + {`design__die__area`, `power__total`, `timing__setup__ws`, `magic__drc_error__count`} 차이 (c) `PL_TARGET_DENSITY_PCT` 값별 `power__total` 표.
- **조건 규칙**: 수작업 = coreutils/grep/jq/python stdlib만, `hwtrack` 접근 금지. 도구 = `hwtrack`만, `scan` 시간 포함, 조건 시작 시 DB·캐시 초기화.
- **배정·순서 (동결)**: (a) 수작업(A) 먼저→도구(B) / (b) 도구(A) 먼저→수작업(B) / (c) 수작업(B) 먼저→도구(A).
- **계측 (자동·결정적)**: 계측 스크립트가 태스크 프롬프트 표시 시각(시작)과 정답 파일 저장 시각(종료)을 UTC 타임스탬프로 자동 기록 — 수기 계측 금지, 로그 파일 커밋. 경과 시간 = 종료-시작(재시도 포함 연속 누적, 중단·일시정지 불허).
- **실패·재시도 규칙 (도구에 불리한 방향으로 보수적)**: 조건당 총 상한 30분. 오답 시 즉시 재시도 1회 허용 — **재시도 중 도구 코드·코퍼스 데이터·환경 설정 변경 금지**(동일 상태에서 질의만 다시). **도구 조건이 오답·timeout으로 종결 → K2 실패**(캡 부여 없음). **수작업 조건이 오답·timeout으로 종결 → 해당 태스크 제외**(baseline 부풀림 방지). 유효 태스크 <2 → 무효(T1).
- **판정**: 유효 태스크에 대해 Σ(도구) ≤ 0.5 × Σ(수작업). 정답 판정은 K1 오라클 산출값과의 완전 일치.
- 한계 명시: 측정자=개발자 — 절차 동결·자동 타임스탬프 로그 공개로 완화, 전 보고에 병기.

### K3. 품질 게이트 (판정 아님, v0.1 태깅 전제)
pytest 커버리지 ≥80% + CI + Codex 코드 리뷰 게이트.

### K4. 외부 사용 증거 (2차 판정)
- **공개 앵커** = GitHub Release `v0.1`의 `published_at`(API 감사 가능). 공개 절차 = repo public 전환 + Release + ORFS discussions·TT Discord 공지 각 1회. **창 = published_at + 60일 (UTC, 자동 종결)**.
- **인정 기준(전부 충족)**: ① 제3자(계정 생성일 < 공개일, 본인·본 프로젝트 무관) ② **실행 증거 필수** — 도구 실행 산출물·로그·구체적 동작 서술이 포함된 이슈/댓글/포스트, **실행 결과·재현 로그가 포함된** PR, 또는 타 저장소의 의존 선언. 실행 증거 없는 PR(오타 수정 등)·스타·포크 불인정 ③ URL + 아카이브 스냅샷 커밋 보존.
- **판정 주체**: Codex 게이트 심사, 모호하면 불인정이 기본값.

## 5. 예산

1차 창 = "실행 개시" 커밋 UTC + 14일. 코퍼스 21 run × ≤60분 직렬 = 최대 21h (Docker VM 6CPU/8GB, SPM 완주 실적으로 실행성 검증). **공개 의무(전 구성요소)** = 1차 판정 결과 커밋 UTC + 3일 내 {repo public 전환(GitHub API 감사) + Release v0.1 발행(published_at) + ORFS discussions·TT Discord 공지 각 1건(URL 아카이브)} 전부 완료 — 하나라도 미이행 시 §6-4 적용.

## 6. 판정 결정 트리 (순서대로 첫 매칭 — 전수 포괄, 불리 결과 보존 우선)

1. K1 **실패 관측** → **refuted** (미완·기한과 무관하게 관측이 우선)
2. K2 **실패 관측** (도구 조건 오답·timeout 포함) → **refuted**
3. 1차 창 종료 시 {K1 검증 미완 · K2 미완 · K3 미통과 · 완주 <15 · 유효 태스크 <2} → **실험 무효** (T1, 사유 기록·Reflection)
4. K1·K2 통과 & 결과 커밋 +3일 내 공개 구성요소(§5: public 전환·Release·공지 2건) 하나라도 미이행 → **partially supported** ("자체 유용성 입증, 외부 채택 미검증" — 승격 금지)
5. 2차 창 종료 시 인정 증거 0건 → **partially supported** (동일 표기)
6. 2차 창 내 인정 증거 ≥1건 → **supported**

## 7. 커밋 체인 (병합 금지)

① protocol LOCK(본 문서 — 매트릭스·키·규칙 전부 포함) → ② 코퍼스 생성 스크립트 + 독립 오라클 + ORFS 파일 목록 → ②′ "실행 개시" 커밋(14일 기산) → ③ 도구 구현(트랙 repo) → ④ 1차 판정 결과(research(results)) → ⑤ Release·K4 창 개시 기록 → ⑥ 2차 판정 결과 + 증거 아카이브.

## 8. LOCK 이력

- [x] Codex 1차: request_changes 5건 → v2 (코퍼스·오라클·K2·K4·트리·예산)
- [x] Codex 2차: request_changes 5건 → v3 (매트릭스·키 본문 동결 / 실패 규칙 비대칭 보수화 / 체스판 변형 매칭·결측 규칙 / 불리 결과 보존 트리·Release 앵커 / PR 실행 증거)
- [x] Codex 3차: request_changes 4건 → v4 (자동 계측 복원·재시도 무변경 / resolved.json 동결·K1 편입 / 모집단 균형화 / 공개 전 구성요소 기한·참조 수정)
- [x] Codex 4차: request_changes 1건 → v5 (canonical 키 `PL_TARGET_DENSITY_PCT` 교정 — Codex가 venv 소스 검증으로 발견한 사실 오류)
- [x] Codex 5차: **approve** (2026-08-25) → LOCKED
