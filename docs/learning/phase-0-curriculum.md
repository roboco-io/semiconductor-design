# Phase 0 — 바이브 코더의 EDA 운영 매뉴얼

> **목적 (재정의, 2026-04-19)**: 이 프로젝트를 수행하기 위한 최소 지식은 **"칩 설계자의 이해"가 아니라
> "에이전트를 감독·디버깅하는 EDA 운영자의 이해"**다. 핵심은 깊은 이론이 아니라,
> 도구 체인이 주고받는 **파일·리포트를 읽고, LLM 출력의 함정을 찾고, 다음 수정 지시를
> 내릴 수 있는 감각**이다.
>
> 학습 결과는 `wiki/raw/sessions/`에 Q&A 원문으로 저장되고, 주기적 ingest로 `wiki/` 페이지가 된다.
> 이 프로세스 자체가 "비전문가가 에이전트를 통해 단기간에 설계 지식을 습득한다"는
> 프로젝트 핵심 가설의 내부 검증 증거다.

## 관점 전환 (핵심)

- **읽고 이해 > 쓰기**: Verilog를 처음부터 쓰는 법이 아니라, **LLM이 토해낸 RTL의 함정을 찾는 법**.
- **파일 포맷이 lingua franca**: EDA 도구 간 교환은 `.v / .lib / .lef / .def / .sdc / .gds`로 이뤄진다. 이 포맷이 무엇을 기술하는지가 이론보다 중요.
- **리포트 해석이 실력**: synth/STA/DRC 리포트를 읽고 "어디를 고쳐야 하는지" 판단할 수 있어야 한다.
- **상용 vs 오픈소스 지도**: 상용(Cadence/Synopsys/Siemens)과 오픈(Yosys/OpenROAD/Verilator)의 차이를 알아야 "상용 대비 의미"를 평가할 수 있다.

## 진행 규칙

- **Q&A 주도권**: **(a) assistant-led** — 내가 설명하고 사용자가 확인·질문.
- **세션 단위**: 한 번에 1~2 브랜치.
- **기록**: 각 sub-topic 완료 시 `wiki/raw/sessions/phase-0-<code>-<slug>.md`에 원문 보관.
- **ingest 시점**: 2-3 브랜치 쌓이면 `wiki/` 페이지로 컴파일.
- **취사선택**: 운영자 관점에 불필요한 이론은 **과감히 건너뛴다**. 필요 시 Phase 1 실습 중 재학습.

## 마인드맵 & 진행 체크리스트

### A. 반도체 하드웨어 기초 — compact (운영자 직관용)
- [x] A1. 트랜지스터·CMOS (why leakage matters, why 130nm)
- [x] A2. 디지털 로직 게이트 + D-FF (RTL이 합성되는 대상)
- [x] A3. 클럭·타이밍·동기/비동기 (STA 리포트 읽기 전제)
- [x] A4. 조합+순차+파이프라인 = RTL이 기술하는 대상

### B. HDL — "LLM 출력 검수 + Gemmini config 수정" 수준 — compact
- [ ] B1. Verilog 읽기 (module/always/assign — 문법 전부 X, 자주 틀리는 패턴 O)
- [ ] B2. Chisel 최소한 (Gemmini `GemminiConfig.scala` 수정 가능한 수준)
- [ ] B3. RTL 추상화 — behavioral/structural/dataflow 구분과 합성 가능성
- [ ] B4. Testbench 멘탈 모델 — "무엇을 얼마나 검증하는지"만. Verilator·cocotb 사용은 실습에서.

### C. EDA Flow — **핵심**: 리포트·파일 중심 (elevate)
- [ ] C1. Synthesis (Yosys) — 입/출력 파일, `*.rpt`, area·cell 리포트 읽기
- [ ] C2. Floorplan/Place/Route (OpenROAD) — 각 단계가 바꾸는 것, `.def` 관찰
- [ ] C3. STA — slack, violation, critical path 리포트 해석과 대응 지시
- [ ] C4. DRC / LVS — 물리 검증 에러 유형과 LLM에게 수정 지시하는 방법
- [ ] C5. Sign-off — 최종 체크리스트, GDSII 확인
- [ ] **C6 (신규). 상용 EDA 지도** — Cadence/Synopsys/Siemens가 뭘 하는지, 오픈 스택의 구멍, "상용 대비 의미"의 기준

### D. DL 가속기 아키텍처 — 실질만 — compact
- [ ] D1. MAC 배열의 의미와 한계
- [ ] D2. Systolic Array — Gemmini 구조 중심
- [ ] D3. Dataflow: WS / OS / IS가 실제로 다르게 하는 것
- [ ] D4. 메모리 계층과 데이터 이동 비용
- [ ] D5. Precision (INT8/FP16/BF16)이 하드웨어에 미치는 영향

### E. ML 워크로드 — 실질만 — compact
- [ ] E1. MLPerf Tiny KWS — 왜 선택했나, 입출력 형태
- [ ] E2. Quantization 결과물(INT8 TFLite) 형태
- [ ] E3. 정확도·레이턴시·면적 Pareto 감각

### F. PDK와 파일 포맷 — **핵심**: lingua franca (elevate)
- [ ] F1. SkyWater sky130A — 무엇이 포함돼 있나 (셀 라이브러리·모델·룰)
- [ ] F2. Liberty(.lib) / LEF / DEF — 각 포맷이 기술하는 것
- [ ] F3. SDC 제약 파일 — 클럭·타이밍 제약을 도구에 전달하는 방법
- [ ] F4. Tiny Tapeout / Efabless Shuttle — 우리 결과물이 실리콘까지 가는 경로

### G. 오픈소스 스택 통합 — 실용만 — compact
- [ ] G1. Chipyard/Rocket/BOOM — Gemmini가 어떻게 끼는지만
- [ ] G2. Verilator·cocotb — 에이전트가 호출하는 명령 수준
- [ ] G3. FireSim — Phase 2+ 검토용 (optional)

### H. 프로젝트 고유 개념 — full
- [ ] H1. HUGI 패턴의 EDA 적용
- [ ] H2. Evolutionary DSE + **Open Ideation tier** (2-tier 탐색)
- [ ] H3. Pareto frontier
- [ ] H4. Cross-LLM consensus (Claude × Codex)

### I. AWS 서버리스 — light-review (30분)
- [ ] I1. Step Functions Map state + retry 정책이 EDA 워크로드에 맞는 이유
- [ ] I2. Fargate Spot의 회수 처리 패턴
- [ ] I3. DynamoDB 4-테이블 모델 선택 근거
- [ ] I4. CDK stack 분할 전략

### J. LLM 에이전트 프로그래밍 — light-review (30분)
- [ ] J1. Claude Code SDK ↔ Codex SDK API 차이
- [ ] J2. Cross-LLM consensus 구현 패턴
- [ ] J3. JSONL trace 로깅 구조
- [ ] J4. Spec/Architect/RTL 에이전트 시스템 프롬프트 설계

### K. LLM Wiki 패턴 — SKIP (Phase 1a에서 체화 완료)

## 산출물

1. **본 문서** — 재정의된 학습 체크리스트
2. **`wiki/raw/sessions/phase-0-*.md`** — 각 sub-topic Q&A 원문
3. **`wiki/` 컴파일 페이지** — ingest 이후 생성
4. **`.claude/skills/semi-design-learning/`** — 학습 진행 스킬

## 완료 기준

- A 완료 + B~F 핵심 sub-topic 체크 (C/F는 **elevated**이므로 모두 체크)
- D·E·G 최소 커버
- H 전부 체크
- I·J light-review 체크
- 관련 `wiki/` 페이지 ≥ 20개 (ingest 후, 목표 축소됨)
- `make test`가 여전히 통과

## 변경 이력

- **2026-04-19**: 관점 재정의 (칩 설계자 → EDA 운영자). C·F elevate, B·D·E compact, C6 신규 추가.
- **2026-04-17**: 초기 작성.
