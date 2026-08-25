# 조사 ③: 하드웨어 검증·디버깅 도구 공백 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색 7회, 기각 없음)

## 요약

2024-2026 오픈소스 하드웨어 검증 스택은 시뮬레이터(Verilator/Icarus)·테스트벤치(cocotb)·파형 뷰어(Surfer)까지는 성숙했으나, 그 사이를 잇는 **"검증 관리 계층"이 비어 있다**. cocotb 공식 설문과 포럼에서 반복 확인되는 페인포인트는 (1) 커버리지가 시뮬레이터(코드)와 Python(기능) 두 곳에 흩어져 merge/시각화가 안 됨, (2) 회귀 실패의 로그·파형 triage가 전부 수작업, (3) formal(SymbiYosys) 반례를 시뮬레이션으로 재현할 수 없음, (4) 초심자(TT)용 온보딩 마찰. Surfer의 성공은 "기존 워크플로에 꽂히는 단일 목적 도구"가 통한다는 것을, WAL의 저조한 채택은 "새 언어를 배우게 하는 도구"는 안 통한다는 것을 보여준다. 2025-2026년 TraceWeave·xevdb 같은 AI-agent용 파형/로그 디버그 MCP 서버의 등장 자체가 이 공백의 수요 증거다.

## 공백·수요 목록

| 공백 | 수요 근거 (URL) | 기존 대안 | 1인 개발 가능성 |
|---|---|---|---|
| 커버리지 통합 merge/rank/시각화 (cocotb 기능 + Verilator 코드) | cocotb 설문: 커버리지·VIP·툴링 최다 불만 (cocotb.org/2023/06/17/user-survey-2023.html); "coverage handled in two places… complicated" (verificationacademy.com/forums/t/uvm-vs-coco-tb-for-verification/50826) | verilator_coverage(--rank "experimental"), pyucis(33 stars) | **높음** — 파서+SQLite+웹 리포트. UCIS는 pyucis 재활용 |
| Verilator covergroup 미지원 | verilator #7099 (covergroup 파싱 후 무시), #3151 | cocotb-coverage/pyVSC 우회 | 낮음 (내부 작업) |
| 파형 diff (golden vs DUT, 회귀 간) | xevdb가 자체 구현할 만큼 표준 도구 부재 (github.com/aionhw/xevdb); "grep the VCD → wrong, GTKWave → no programmatic access" | 없음(수작업), WAL(학습장벽) | **높음** — VCD/FST 파서(Rust wellen) 위 diff |
| 시뮬 실패 triage/클러스터링 (로그+파형 연계) | TraceWeave (github.com/gokeshenzhen/TraceWeave), xevdb — 2025-2026 잇달아 등장 = 수요 신호 | 초기 도구들, 상용 Verdi | **높음** |
| sby 반례를 원본 RTL로 재실행 불가 | sby #300 (open, "generated test benches cannot be used with original source"); yosys #4426 트레이스 혼란 | design_prep.il 수동 변환 | **중간** — VCD 반례→cocotb/iverilog TB 생성기 |
| 초심자 온보딩 마찰 (TT·FPGA) | cocotb discussions #4917 첫날 이탈; HN 41578619 "fighting IDEs and tooling"; allaboutcircuits UVM-free 스레드 | TT 템플릿+Discord | **높음** — 차별화·검증 기준이 난점 |

## 최근 도구 채택 사례와 교훈

- **Surfer (통함)**: MIT 6.205 채택, quicksilicon(월 5천+ 시뮬), TT 공식 문서 등재 (CAV 2025). 교훈: **기존 포맷(VCD/FST) 그대로 + 명확히 나은 UX + 임베딩 가능**.
- **WAL (비었음)**: 논문 다수(TCAD, ASP-DAC)나 채택 미미 — 저자 스스로 "S-expression 진입장벽" 인정. 교훈: 분석 능력보다 **접근 문법**이 채택을 결정.
- **cocotb (반쯤)**: 월 12만+ 다운로드, 설문 최다 불만 = VIP 부재·커버리지 도구. cocotbext-fcov(furiosa-ai) 등 확장 수요 실재.
- **AI-agent 디버그 (신생)**: TraceWeave, xevdb, waveform-mcp, pyucis MCP — "파형/커버리지를 LLM이 질의 가능하게" 흐름이 방금 시작, 지배자 없음.

## 유망 후보 Top 3

1. **회귀 실패 triage 도구** (로그 정규화 + 실패 시각 앵커 파형 자동 절단·golden diff + 실패 클러스터링, CLI+MCP, Surfer 원격 프로토콜 연동): xevdb·TraceWeave 등장 = 수요 증명, 둘 다 초기라 오픈 필드. 검증: TT 제출작 10개 적용 triage 시간 단축 측정 + 커뮤니티 채택.
2. **커버리지 통합 리포트** (이기종 커버리지를 UCIS로 merge·rank·HTML 대시보드, CI 아티팩트): cocotb 최대 반론 직격. 검증: pyucis 상호운용 + 오픈 IP 회귀 적용 merge 정확성 대조.
3. **sby 반례 → 재실행 가능 시뮬 브리지**: sby#300 명시적 요청, 경쟁 전무. 검증: riscv-formal·ZipCPU류 공개 반례 재현율 정량 측정.

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| forum discussion pain points open-source hardware verification cocotb coverage limitations vs commercial UVM | 8 |
| Surfer waveform viewer adoption GTKWave alternative VCD FST 2024 2025 review | 8 |
| open source functional coverage merge ranking missing Verilator coverage tooling gap github issue | 8 |
| SymbiYosys formal verification usability pain counterexample debugging blog 2024 2025 | 8 |
| Tiny Tapeout FPGA hobbyist debugging testbench pain reddit verification beginners 2024 2025 | 8 |
| WAL waveform analysis language adoption regression failure triage tool missing | 8 |
| reddit r/FPGA open source verification missing functional coverage constrained random pain | 8 |
