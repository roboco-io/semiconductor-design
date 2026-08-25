# 조사 ④: 에이전틱/자율 칩 설계 플로우 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색, 기각 없음)

## SOTA 요약

2023년 Chip-Chat(대화형 GPT-4로 8-bit CPU 설계 → Tiny Tapeout 실리콘)이 개념 실증을 연 뒤, 2024-2025년에는 모듈 수준 RTL 생성 에이전트(AutoChip, VerilogCoder, MAGE)가 VerilogEval류 벤치마크를 95%+로 포화시켰고, 2025-2026년에는 (a) 복잡 스펙 문서→RTL(Spec2RTL-Agent), (b) 백엔드 툴 조작·파라미터 튜닝(ORFS-agent, AutoEDA, ChatEDA 계열), (c) RTL→GDSII 전 구간 에이전트 벤치마킹(FluxBench, CLOSER-Bench)으로 전선이 이동했다. 2025년 말 "Agentic EDA" 서베이(arXiv 2512.23189)는 자율성 수준을 L1(어시스턴트)-L4(완전 자율)로 계층화하며, 현재 SOTA는 "모듈 수준 L3(툴 사용 자율 루프), 플로우 수준 L2"로 평가한다. 산업 측은 ChipAgents(Alpha Design AI)가 VerilogEval-v2 97.4%와 $134M Series A로 선두이나 검증 보조 중심이다. 공통 결론: 프런트엔드 코딩은 거의 풀렸고, 병목은 검증·긴 피드백 루프·크로스 스테이지 폐루프다.

## 핵심 논문

| 제목 | 연도 | venue | URL | 핵심 주장 | 한계 | 자율성 수준 |
|---|---|---|---|---|---|---|
| Chip-Chat | 2023 | MLCAD'23 | arxiv.org/abs/2305.13243 | 대화형 GPT-4로 8-bit CPU 공동 설계, 세계 최초 LLM-작성 HDL tapeout | 테스트벤치는 인간 작성, 인간이 대화 주도 | L1 대화형 |
| AutoChip | 2023 | arXiv→ICCAD계열 | arxiv.org/html/2311.04887 | 컴파일/시뮬 에러 피드백 자동 루프로 HDL 생성 | 단일 모듈, 벤치마크 문제 한정 | L2 모듈 자동수정 |
| VerilogCoder | 2024 | AAAI'25 | arxiv.org/abs/2408.08927 | 그래프 기반 계획 + AST 파형 추적 툴로 94.2%(VerilogEval-v2) 자율 코딩 | 모듈 수준, 백엔드 미포함 | L3 모듈 |
| MAGE | 2024 | DAC'25/arXiv 2412.07822 | arxiv.org/html/2412.07822 | 최초 오픈소스 멀티에이전트 RTL 엔진, 95.7% VerilogEval-Human v2 | 벤치마크 포화 영역, 시스템 설계 미검증 | L3 모듈 멀티에이전트 |
| Spec2RTL-Agent | 2025 | arXiv (NVIDIA/Cadence) | arxiv.org/html/2506.13905 | 실제 복잡 스펙 문서의 이해→코딩→리플렉션 전 단계 자동화 | HLS 경유, PPA/백엔드 미포함 | L3 스펙→RTL |
| ASIC-Agent | 2025 | ICLAD'25 | doi.org/10.1109/iclad65226.2025.00033 | RTL+검증+OpenLane 하든까지 자율 멀티에이전트, 자체 벤치마크 | 오픈소스 플로우 한정, 평가 규모 작음 | L3 플로우 |
| ORFS-agent | 2025-26 | arXiv (UCSD Kahng) | arxiv.org/html/2506.08332v3 | LLM 에이전트가 OpenROAD 플로우 파라미터 튜닝, AutoTuner 대비 40% 적은 반복 | 백엔드 최적화만, 개선폭 1-3% | L2-L3 백엔드 |
| FluxBench: Can AI Agents Really Complete RTL-to-GDS? | 2026 | arXiv 2607.17528 | arxiv.org/html/2607.17528 | 통일 환경에서 에이전트 시스템별 RTL→GDS 평가, Token ROI 지표. 동일 모델에서도 하네스 아키텍처 차이로 성능 86% 격차 | 벤치마크는 PicoRV32 등 소수 케이스 | 평가 논문 |
| The Dawn of Agentic EDA (서베이) | 2025 | arXiv 2512.23189 | arxiv.org/html/2512.23189v1 | AI4EDA→AI-Native→Agentic 패러다임 정리, L1-L4 자율성 분류, 크로스 스테이지 PPA 피드백 강조 | 서베이 | 분류 체계 |

## 평가 방법론 현황과 갭

- **주류**: VerilogEval(-v2)·RTLLM의 pass@k — 테스트벤치 통과 = 성공. SOTA 95%+로 포화 (Revisiting VerilogEval, TODAES 2025).
- **차세대**: NVIDIA CVDP(에이전틱 모드, arXiv 2506.14074), RealBench(실제 IP), ChipBench, CLOSER-Bench(예산 제약 하 크로스 스테이지 클로저, arXiv 2607.16632), FluxBench(Token ROI = 토큰 비용 대비 개선), TuRTLe(합성 가능성·PPA 포함).
- **갭**: ① 판정 기준인 테스트벤치 자체가 불완전/LLM 생성(AutoBench·CorrectBench가 메타 문제로 다룸) ② 대부분 PPA/sign-off 게이트 부재 ③ 학습 데이터 오염(유명 IP 재생성 — Chip-Chat도 신규 ISA로 회피) ④ 비용·반복 횟수·인간 개입량 미계측(Token ROI가 최초 시도) ⑤ 모듈 수준 편중, 시스템/멀티모듈 평가 희소.

## Open Problems

- **긴 피드백 루프**: Caravel 통합 시뮬 45분+, P&R 수 시간 — 에이전트 반복 루프와 충돌 (Pearce 블로그, FluxBench)
- **블랙박스 툴 통합**: 상용 EDA 로그/GUI 해석, 툴별 이질적 인터페이스 (Agentic EDA 서베이; AutoEDA 2508.01012)
- **환각·데이터 희소성**: HDL 코퍼스 부족 (서베이; arXiv 2508.05266)
- **디버깅 능력**: 파형 추적·멀티모듈 원인 추적이 최약점
- **도메인 스킬만으론 불충분**: Claude Code+EDA 스킬이 전용 에이전트 시스템에 최대 8.4배 뒤짐 — 하네스 아키텍처가 결정적 (FluxBench)
- **검증 병목**: 설계자 1명당 검증 2-3명 구조, 자율 생성 RTL의 신뢰 확보 (ChipAgents/SiliconANGLE 2025-10)

## Underexplored Areas

- **구독형 CLI(Claude Code/Codex) + 오픈소스 플로우 하네스 설계 연구**: FluxBench가 Claude Code를 베이스라인으로만 썼을 뿐, "범용 코딩 에이전트를 EDA에 최적화하는 하네스/스킬 설계" 자체를 체계 연구한 논문은 부재 — 1인 연구자가 재현 가능한 공백
- **비용-효율(Token ROI) 재현 연구**: 구독 요금제 기준 실측 데이터 전무
- **에이전트 설계물의 실리콘 실증**: 대화형(Chip-Chat 계열) 이후 *자율 에이전트* 산출물의 Tiny Tapeout 검증 사례 공백
- **인간 학습 축**: LLM 협업 설계에서 비전문가의 역량 성장 측정 연구는 사실상 전무 (Chip-Chat이 user study 필요성만 제기)
- **테스트벤치 독립성**: 생성 엔진≠심사 엔진 구도의 체계적 평가 (CorrectBench가 초기 시도)

## 실리콘 실증 사례

1. **QTcore-A1** (Chip-Chat, GPT-4) — Tiny Tapeout 3, SKY130, 2023. 최초 LLM-작성 HDL tapeout
2. **QTcore-C1** (NYU) — Efabless AI Challenge 1위, Caravel/chipIgnite 제작, 2024-01 실물
3. **Cyberrio** (Tsinghua-Berkeley) — ChatGPT-4 RISC-V CPU, Efabless 2위
4. **MPC 회로** (Rapid Silicon) — MATLAB→ChatGPT-4→Verilog, Efabless 3위
5. **Spiking Neuron Array** (JHU, arXiv 2402.10920) — ChatGPT-4 전체 설계, Tiny Tapeout 5

공통점: 전부 대화형+인간 개입. 완전 자율 에이전트 산출물의 tapeout 공개 사례는 미확인 (ASIC-Agent가 타깃하나 실리콘 보고 없음).

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| survey paper on LLM agents for autonomous chip design flow spec to RTL to GDSII 2025 multi-agent | 10 |
| VerilogCoder MAGE AutoChip ChipChat LLM agent Verilog code generation paper benchmark results limitations | 10 |
| LLM-designed chip fabricated silicon Tiny Tapeout ChipChat GPT-4 microcontroller tapeout Efabless AI generated design contest | 10 |
| paper lessons benchmarking autonomous AI agents RTL-to-GDS OpenROAD tool-interactive EDA workflow failure modes open problems long feedback loop | 10 |
| ChipAgents AI agentic chip design verification startup Alpha Design AI autonomous RTL agent 2025 | 8 |

(추가로 arXiv 2607.17528, 2506.13905, 2506.08332 전문 fetch. 모든 응답 citation > 0 — 기각 없음)
