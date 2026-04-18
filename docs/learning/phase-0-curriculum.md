# Phase 0 — 비전문가 학습 커리큘럼

> **목적**: 이 프로젝트(AI 에이전트 기반 딥러닝 반도체 설계)를 이해·수행하기 위한
> 최소 필요 지식을 마인드맵 가지처럼 순차 학습한다. 학습 결과는 `wiki/raw/sessions/`
> 에 Q&A 원문으로 저장되고, 주기적 ingest로 `wiki/` 페이지가 된다.
>
> 이 프로세스 자체가 프로젝트의 목표("비전문가가 에이전트를 통해 단기간에 설계
> 지식을 습득한다")를 내부적으로 실천·검증하는 증거가 된다.

## 진행 규칙

- **Q&A 주도권**: **(a) assistant-led** — 내가 설명하고 사용자가 확인 질문. 필요 시 소크라테스식 교차.
- **세션 단위**: 한 번에 1~2 브랜치. 브랜치 내 sub-topic들은 순차.
- **기록**: 각 sub-topic 완료 시 `wiki/raw/sessions/phase-0-<code>.md`에 원문 보관.
- **ingest 시점**: 2-3 브랜치 쌓이면 `wiki/` 페이지로 컴파일.

## 마인드맵 & 진행 체크리스트

### A. 반도체 하드웨어 기초 — full
- [x] A1. 트랜지스터·CMOS
- [x] A2. 디지털 로직 게이트 (AND/OR/NOT/NAND + Flip-flop)
- [x] A3. 클럭·타이밍·동기/비동기
- [ ] A4. 조합 회로 vs 순차 회로

### B. HDL — 하드웨어 기술 언어 — full
- [ ] B1. Verilog 핵심 구조
- [ ] B2. Chisel (Gemmini 이해에 필수)
- [ ] B3. RTL 추상화 수준
- [ ] B4. Testbench·Verilator 멘탈 모델

### C. EDA Flow — RTL → GDSII — full
- [ ] C1. Logic Synthesis (Yosys)
- [ ] C2. Floorplan·Placement·Routing (OpenROAD)
- [ ] C3. STA (Static Timing Analysis)
- [ ] C4. DRC / LVS (물리 검증)
- [ ] C5. Sign-off + Tapeout

### D. DL 가속기 아키텍처 — full
- [ ] D1. PE와 MAC 배열
- [ ] D2. Systolic Array (Gemmini·TPU)
- [ ] D3. Dataflow: WS / OS / IS
- [ ] D4. 메모리 계층
- [ ] D5. Precision (INT8/FP16/BF16)

### E. ML 워크로드 & 벤치마크 — full
- [ ] E1. MLPerf Tiny 개요 (KWS 중심)
- [ ] E2. Quantization (FP32 → INT8)
- [ ] E3. TFLite Micro
- [ ] E4. 정확도·레이턴시·면적 tradeoff

### F. PDK와 제조 경로 — full
- [ ] F1. SkyWater sky130A
- [ ] F2. Liberty / LEF / DEF 파일 포맷
- [ ] F3. Tiny Tapeout / Efabless Shuttle
- [ ] F4. 마스크·레이어·셀 라이브러리

### G. 오픈소스 스택 통합 — full
- [ ] G1. Chipyard 프레임워크
- [ ] G2. Rocket Chip·BOOM
- [ ] G3. FireSim (이터레이션 2+)
- [ ] G4. cocotb

### H. 프로젝트 고유 개념 — full
- [ ] H1. HUGI 패턴의 EDA 적용
- [ ] H2. Evolutionary DSE
- [ ] H3. Pareto frontier
- [ ] H4. Cross-LLM consensus

### I. AWS 서버리스 — light-review (30분)
- [ ] I1. Step Functions Map state + retry 정책이 EDA 워크로드에 맞는 이유
- [ ] I2. Fargate Spot의 회수 처리 패턴
- [ ] I3. DynamoDB 4-테이블 모델 선택 근거
- [ ] I4. CDK stack 분할 전략 (NetworkStack/StorageStack/...)

### J. LLM 에이전트 프로그래밍 — light-review (30분)
- [ ] J1. Claude Code SDK ↔ Codex SDK API 차이
- [ ] J2. Cross-LLM consensus 구현 패턴
- [ ] J3. JSONL trace 로깅 구조
- [ ] J4. Spec/Architect/RTL 에이전트 시스템 프롬프트 설계

### K. LLM Wiki 패턴 — SKIP (Phase 1a에서 체화 완료)

## 산출물

1. **본 문서** — 진행 체크리스트
2. **`wiki/raw/sessions/phase-0-*.md`** — 각 sub-topic Q&A 원문
3. **`wiki/` 컴파일 페이지** — ingest 이후 생성 (Phase 0 종료 직전)
4. **`.claude/skills/semi-design-learning/`** — 학습 진행 스킬 (재개·공유용)

## 완료 기준

- A~H 모든 sub-topic 체크
- I·J light-review 체크
- 관련 `wiki/` 페이지 ≥ 25개 (ingest 후)
- `make test`가 여전히 통과 (무관 영역이므로 당연하나 확인)
