# Experiment Protocol — H1.1 파이프라인 스모크 테스트

## 1. Hypothesis

- **Hypothesis ID:** H1.1 (research-tree.yaml)
- **Statement:** 가장 단순한 설계(조합 논리 1개)로 RTL 작성 → 테스트벤치 기능 정합 →
  합성 → P&R → sign-off clean GDSII(SKY130, TT 템플릿 제약)까지 로컬 파이프라인을
  **실행 개시일로부터 7일 이내** 완주할 수 있다.
- **Judgment verdict:** approved — novelty는 낮으나 H1의 최저비용 반증 테스트 (enabling test)
- **Scope:** Deployment-like (실제 도구 체인 그대로)

## 2. Contribution Type

- **Type:** Replication / feasibility (연구 주장 아님 — 후속 가설의 전제 검증)
- **기존 증거가 불충분한 이유:** 선행 사례(LLM+TT 교육 등)는 강사 인프라·사전 준비된
  환경에서의 완주. "이 환경(macOS 로컬, 비전문가 Operator 1인 + AI 에이전트, 구독
  CLI만)"에서의 완주는 미확인.

## 3. Data / Design Target (사전 고정)

- **설계물:** 4-bit ripple-carry adder (조합 논리, 난이도 사다리 1칸)
- **테스트벤치:** 전수 검사 — 입력 256조합(16×16) 전부, 기대값 대조. 표본 아님.
- **Flow:** LibreLane (Tiny Tapeout 표준 flow) + **SKY130A** PDK, Tiny Tapeout
  타일 템플릿(tt 최신 template repo) 제약 준수
- **Leakage 해당 없음** (벤치마크 학습 데이터 아님). 단 AI가 기존 오픈소스 adder
  코드를 그대로 복사해도 무방 — H1.1은 "Operator+AI 조합의 파이프라인 완주"를 검증하는
  것이지 코드 독창성을 검증하지 않는다 (사전 명시).

## 4. Variables & Controls

- **독립 변수:** 없음 (단일 조건 feasibility run)
- **종속 변수 — Primary (완주 판정, 전부 충족해야 supported):**
  1. 테스트벤치 256/256 pass (iverilog 또는 Verilator 시뮬레이션)
  2. LibreLane flow 정상 종료 → GDSII 생성
  3. sign-off clean: **DRC 위반 0** (Magic/KLayout), **LVS clean** (Netgen),
     **STA: TT 기본 클럭 제약에서 setup/hold 위반 0**
  4. 소요 기간 ≤ 7일 (실행 개시 커밋 ~ 최종 clean 리포트 커밋)
- **Secondary (exploratory, 판정에 불사용):** 셀 수·면적·타일 활용률, flow 소요
  wall-clock, AI 상호작용 턴 수
- **Sanity check:** 테스트벤치에 의도적 오류 1개 주입 시 fail이 검출되는지 확인
  (검출 못 하면 파이프라인 무효)
- **Negative control:** 해당 없음 (feasibility run)

## 5. Compute Plan

- **환경:** 로컬 macOS (darwin), LibreLane 공식 설치 경로(Nix 또는 Docker) 중
  실행 시점에 문서화된 권장 경로. 클라우드·유료 컴퓨트 사용 금지 (Not: 저비용 로컬).
- **결정론:** 도구 버전·PDK 버전·시드를 lockfile로 기록 (METRICS2.1 정신).
  OpenROAD 계열은 동일 버전+동일 config에서 결정론적.
- **AI 에이전트:** 구독 CLI(claude/codex)만 사용. metered API 금지.

## 6. Analysis Plan (사전 고정)

- **Decision rule:** §4 Primary 4항목 전부 충족 → **supported**.
  하나라도 미충족(7일 초과 포함) → **refuted** (부분 달성은 결과에 기술하되 판정은 refuted).
- **통계 검정:** 없음 (binary feasibility). 반복 수 1회 — 실패 시 원인 분석을 기록하고
  프로토콜 수정 후 재시도는 **새 사이클**로 계정 (이 프로토콜의 판정은 첫 시도 기준).
- **학습 축 파일럿 (H2 최저비용 테스트, 동시 수행):**
  - 사이클 구조 준수: 설계 → 튜토리얼(AI 생성, 이번 사이클 개념: 조합 논리·합성·sign-off 3검사) →
    서술형 퀴즈 1회 (Operator 응답)
  - 퀴즈 채점: 사전 고정 루브릭(퀴즈 출제 시점에 함께 작성·커밋) + **채점 엔진 = Codex**
    (생성≠심사). 점수는 H2 데이터의 1번 관측치 — H1.1 판정에는 불사용.
  - DLCI 입수 시도 및 pre 측정 — 입수 실패 시 대체 pre 검사(공개 디지털 논리 문항)로
    전환하고 그 사실을 기록 (EXPLORATORY 라벨).

## 7. Reproducibility Artifacts

- **위치:** `experiments/H1.1-smoke/` — src/(RTL·테스트벤치), results/(리포트·로그),
  lockfile(도구·PDK 버전), analysis.md
- **커밋 규율:** plan 커밋(이 파일) → code 커밋 → results 커밋. **plan과 results는
  절대 같은 커밋에 넣지 않는다** (git 히스토리가 사전등록 증명).

## 8. Ethics & Risk

- **Human subjects:** Operator 본인의 자기 실험(N=1) — 퀴즈·학습 데이터는 본인 동의
  하의 자기 측정. 공개 시 자기실험임을 명시. IRB 해당 없음.
- **Dual-use:** 없음 (4-bit adder).

## 9. Stop Criteria & Reporting

- **중단 기준:** 7일 기한 도달 시 그 시점 상태로 판정 확정.
- **보고 약속:** supported/refuted 어느 쪽이든 결과를 기록한다. refuted면 실패 지점·
  원인 분류가 산출물이다.

---

**Protocol status:** LOCKED (2026-08-25)
**Locked by:** Operator 승인 하 Claude(Executor) 작성 — 이후 이탈은 research-log에 EXPLORATORY로 기록
