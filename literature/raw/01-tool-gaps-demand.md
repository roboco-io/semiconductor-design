# 조사 ①: 오픈소스 EDA 생태계 도구 공백·수요 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색 6회, 기각 없음)

## 요약

오픈소스 EDA 생태계(OpenROAD/LibreLane/Yosys 등)는 "플로우 자체"는 성숙했지만(OpenLane 계열 800+ 테이프아웃), **결과물 해석·디버깅 계층이 공백**이다. 커뮤니티가 반복 호소하는 페인포인트는 (1) 타이밍 리포트가 읽기 어렵다, (2) 플로우 실패 시 에러가 암호 같다(LVS/PDN/안테나/라우팅), (3) 로그·메트릭이 기계가독 형식이 아니다, (4) PDK 통합 문서·설정이 빈약하다. 이들은 모두 **코어 엔진 수정 없이 독립 소프트웨어(파서+시각화+진단)로 해결 가능**해서 1인 개발자에게 적합하다. 성공 선례는 Surfer 파형 뷰어 — 1인 시작 → 2년 만에 FOSSi 프로젝트·Tiny Tapeout/QuickSilicon/상용 플랫폼에 임베드. 2025-2026년에는 AI 에이전트+MCP로 EDA를 감싸는 흐름(openroad-mcp, vibe-ic, eda-agents, SiliconWeaver)이 빠르게 형성 중이며, OpenROAD 측이 직접 "타이밍 리포트의 구조화가 AI 지원 타이밍 클로저를 가능케 한다(Impact: High)"고 명시한 이슈가 존재한다.

## 도구 공백·수요 목록

| 공백 | 수요 근거 (URL) | 기존 대안 | 1인 개발 가능성 |
|---|---|---|---|
| STA/타이밍 리포트 해석·시각화 (구조화 JSON, slack 히스토그램, 경로 탐색) | OpenROAD #1759 "Timing results are really hard to understand"; openroad-mcp #96 "Raw timing reports are hard to read… Impact: High" (github.com/The-OpenROAD-Project/OpenROAD-MCP/issues/96); OR #10020 정적 HTML 타이밍 리포트 제안; OR #9371, #4633 | GUI 내 제한적 위젯, PathView(경로 회로도만, 유지보수 미미) | **높음** — 텍스트 리포트 파싱+웹 시각화. 검증은 OpenSTA 출력 대조 |
| 플로우 실패 진단 (암호 같은 에러 → 원인·수정 제안) | OpenLane #1183 "errors are very cryptic… literally almost everybody encountered"; LVS 헬프 스레드 (web.open-source-silicon.dev/t/26945328/), OpenLane #1768 PDN 매크로 훅 LVS 실패 | Slack/Discord에서 사람이 수동 진단 | **높음** — 로그 파서+실패 패턴 DB. TT 커뮤니티 실사례로 검증 |
| 기계가독 로그·메트릭 내보내기/대시보드 | OR #1759 "lack of machine-readable logs/parameters/metrics export (METRICS2.1)" | ORFS 한정 METRICS2.1, 그 외 grep | **높음** |
| 안테나 위반 이해·수정 가이드 | OpenLane #1231 5가지 시도에도 미해결; Slack #openroad 스레드 "10 diodes per gate" 질문 | repair_antennas 재실행, 전문가 답변 대기 | **중** — 수정 제안 정확성 검증이 관건 |
| PDK 통합 문서·설정 검사기 | ORFS 토론 #3784 "Sky130 PDK documentation… lackluster"; siliconcompiler #842 LEF 병합 삽질 | 각 플로우 저장소 소스 읽기 | **중** |
| ngspice/아날로그 파형·시뮬 워크플로우 | open-source-silicon #analog 스레드 "ngspice 출력과 잘 통합되는 파형 뷰어" | gaw, Python 스크립트 | **중** — 니치는 시뮬 오케스트레이션 |
| 계층 플로우용 Liberty 타이밍 모델 생성기 | OR #1759 "+1 … even a basic liberty file generator would be very useful" | 없음(수동 .lib) | **낮음** — STA 정확성 리스크 큼 |
| cocotb×Verilator 통합 마찰 | cocotb #3894, #3831, verilator #5758 | 업스트림 수정 대기 | **낮음** — 업스트림 PR 성격 |

## 최근 성공 사례와 교훈

- **Surfer** (2022 첫 커밋 → 2024-12 v0.3, FOSSi 프로젝트化, LUBIS EDA 스폰서): GTKWave 정체를 "현대적 UX + 확장성 + 임베드 가능(WASM/VSCode) + 원격 제어 프로토콜(WCP)"로 공략. TT·QuickSilicon·MakerChip·상용 플랫폼 채택. CAV 2025 논문 (ics.jku.at/files/2025CAV_Surfer.pdf). **교훈**: 코어 엔진이 아니라 "매일 쓰는 뷰어/해석 계층"에서, 통합 프로토콜을 열어두면 플랫폼들이 알아서 임베드해 준다.
- **LibreLane** (2025-08, fossi-foundation.org/blog/2025-08-17-librelane): Python API·커스텀 Step으로 OpenLane 대체, TT 기본 플로우. **교훈**: 파이썬 확장점이 열려 있어 서드파티 Step/플러그인 진입 적기.
- **AI×EDA 도구 급부상 (2025-2026)**: openroad-mcp(공식 조직 산하), vibe-ic, eda-agents, SiliconWeaver. 공통 병목이 "도구 출력의 구조화" — 파서/리포트 계층이 AI 플로우의 전제 부품이 됐다.

## 유망 후보 Top 3

1. **STA 리포트 분석기 "타이밍 리포트의 Surfer"**: OpenSTA/OpenROAD `report_checks` 출력 → 구조화 JSON + 자체완결 HTML(slack 히스토그램, 경로 드릴다운). CLI + MCP 겸용. 수요 근거 최다(OR #1759/#10020/#9371/#4633 + mcp #96 "Impact: High"). 검증: ORFS 예제 전수 파싱 golden diff 100% + 커뮤니티 채택 측정.
2. **LibreLane/ORFS 플로우 실패 진단기 (log doctor)**: 런 디렉토리에서 실패 시그니처 매칭 → 원인·수정 config 제안. "거의 모두가 겪는다"(#1183). 검증: 공개 실패 사례 코퍼스로 원인 적중률 사전 고정 측정.
3. **LVS/PDN 위반 트리아지 뷰어**: netgen lvs.rpt+PDN 로그 → 넷·유형·좌표를 KLayout 마커/웹 뷰 연결. 검증: 알려진 실패 사례 재현 대조 + netgen 포맷 회귀 테스트.

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| forum discussion about missing tools and pain points in open source EDA flow OpenROAD OpenLane sky130 users complaining | 8 |
| Surfer waveform viewer adoption why users switched from GTKWave 2024 | 8 |
| reddit r/chipdesign discussion what open source EDA tools are missing frustrating gaps hobbyist ASIC flow | 8 |
| feature request tool for parsing understanding OpenSTA timing reports visualization OpenROAD user issue | 8 |
| cocotb verilator iverilog user pain points missing features 2024 2025 verification open source testbench frustration forum | 8 |
| OpenLane LibreLane users struggling cryptic error logs DRC LVS debugging antenna violations help thread Tiny Tapeout discord common problems | 8 |
