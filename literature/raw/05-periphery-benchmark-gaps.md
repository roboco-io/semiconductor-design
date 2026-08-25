# 조사 ⑤: EDA×AI 주변부·미개척 영역 스캔 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색, 기각·재검색 0건)

## (a) Analog/Mixed-Signal 설계 자동화 + LLM

### 요약
2024년까지 거의 공백이었으나 2024-2025년에 급성장한 축. 디지털 RTL 대비 데이터 기근이 훨씬 심각해, 대부분의 연구가 "데이터 없이(training-free 에이전트) 또는 데이터를 만들며(합성 netlist)" 접근한다. 실전 수준 회로에서는 성공률이 여전히 낮다(실데이터 기준 23% 이하).

| 논문 | 연도/venue | URL | 핵심 주장 | 한계 |
|---|---|---|---|---|
| AnalogCoder | AAAI 2025 Oral | https://arxiv.org/abs/2405.14918 | 최초 training-free LLM 에이전트. PySpice 코드 생성 + 피드백 루프 + 서브회로 라이브러리. 24개 태스크 중 20개 성공 | 기본 회로 수준. AnalogXpert 실데이터 재평가에선 6% |
| AnalogXpert | arXiv 2024.12 | https://arxiv.org/abs/2412.19824 | subcircuit-level SPICE 생성 + proofreading. 실데이터 30개+합성 2k 벤치마크. 실데이터 23% vs GPT-4o 3% | 성공률 자체가 낮음 |
| LaMAGIC | ICML 2024 | https://proceedings.mlr.press/v235/chang24c.html | SFT 기반 토폴로지 생성, 단일 패스 96% | 전력변환기(소자 6개 이하) 한정 |
| LayoutCopilot | IEEE (DAC/TCAD 2025) | https://ieeexplore.ieee.org/document/11043664 | LLM 대화형 인터랙티브 아날로그 레이아웃 | 인터랙션 보조 수준 |
| AnalogSeeker | arXiv 2025.08 | https://arxiv.org/abs/2508.10409 | 교과서 코퍼스 증류로 Qwen2.5-32B 파인튜닝, AMSBench-TQA 85% | 지식 QA 중심 — 실제 설계 능력과 별개 |

### Open problems
- 검증된(기능 시뮬레이션 통과) 아날로그 netlist 대규모 데이터셋 부재 — AnalogCoder-Pro(arXiv 2508.02518)가 착수한 초기 단계
- 실무형 spec 입력 시 성공률 급락, 파형 멀티모달 디버깅 미성숙, layout·기생성분 end-to-end 부재

### 기여 가능 지점
- ngspice/PySpice 기반이라 전 파이프라인 로컬 무료 — 1인 재현·확장 용이. AnalogCoder 벤치마크(24개)는 작아 확장 여지 큼
- "검증 게이트 통과 netlist만 축적" 오픈 데이터셋 구축은 컴퓨트보다 방법론 싸움

## (b) HLS + LLM

### 요약
RTL 생성 대비 확연히 얇은 축(밀도: 보통). "C를 HLS-호환으로 리팩토링", "pragma 자동 삽입", "타이밍 인지 최적화"로 분화 중. 공통 병목은 HLS 공개 데이터셋·표준 벤치마크 부재 — SAGE-HLS는 VerilogEval을 개조해 평가할 정도.

| 논문 | 연도/venue | URL | 핵심 주장 | 한계 |
|---|---|---|---|---|
| HLSPilot | 2024 (arXiv) | https://arxiv.org/abs/2408.06810 | 최초 LLM-HLS 프레임워크: 프로파일링→C-to-HLS 전략→DSE pragma 튜닝 | pragma 수치 결정은 외부 DSE 의존 |
| C2HLSC | 2024 (arXiv) | https://arxiv.org/abs/2412.00214 | LLM으로 일반 C를 HLS-합성가능 C로 자동 리팩토링 | 케이스 스터디 규모 |
| LIFT | 2025 (arXiv) | https://arxiv.org/abs/2504.21187 | GNN 감독 신호로 LLM 파인튜닝해 성능 pragma 자동 삽입 | 학습 데이터·일반화 제한 |
| SAGE-HLS | 2025 (arXiv) | https://arxiv.org/abs/2508.03558 | Verilog→C 역포팅으로 16.7K HLS 데이터셋, 합성가능성 약 100% | 기능 정확도 75%, 표준 벤치 부재 방증 |

### Open problems
- HLS 전용 공개 벤치마크·검증 하네스 부재(pass@k + QoR 통합 프레임 없음)
- 수치 pragma 추론 취약, expert-HDL 대비 QoR 격차

### 기여 가능 지점
- 오픈소스 HLS(Bambu, XLS) + Verilator로 로컬 완결 평가 루프 가능 — "HLS판 VerilogEval" 자체가 빈 자리
- C→HDL 기능 등가성 검증 자동화 파이프라인은 1인 규모로 착수 가능

## (c) 벤치마크·데이터셋 부족 문제 자체를 다루는 연구

### 요약
데이터 기근 대응(합성 데이터)은 활발하나, 벤치마크 오염·포화를 정면으로 다룬 연구는 2025년에야 등장한 소수. VerilogEval/RTLLM 중심 평가 체계의 신뢰성 자체가 흔들리는 중.

| 논문 | 연도/venue | URL | 핵심 주장 | 한계 |
|---|---|---|---|---|
| VeriContaminated | 2025 (IEEE) | https://arxiv.org/abs/2503.13572 | 최초로 VerilogEval·RTLLM 데이터 오염을 CCD/Min-K%로 정량화 — 오염 심각 확인 | 탐지 중심, 완화책 초기 |
| Revisiting VerilogEval | TODAES 2025 | https://dl.acm.org/doi/10.1145/3718088 | 1년간 모델 향상 추적, 개선판 제시 | 포화 진행 — 변별력 하락 |
| CraftRTL | ICLR 2025 | https://openreview.net/forum?id=8KQzoD5XAr | correct-by-construction 합성 데이터 + 표적 오류수리 데이터 | 비텍스트 표현·minor error 국한 |
| OpenLLM-RTL | ICCAD 2024 | https://arxiv.org/abs/2503.15112 | RTLLM 2.0 + AssertEval + 80K 데이터 — 7K 검증본이 50K 원본보다 우수 | 기능 검증이 LLM 생성 assertion 의존 |
| RealBench / NotSoTiny | 2025 (arXiv) | https://arxiv.org/abs/2507.16200 / https://arxiv.org/abs/2512.20823 | 실제 IP 수준·오염 내성 "living benchmark"로 기존 벤치 비판 | 신생 — 커뮤니티 채택 미검증 |

### Open problems
- 오염-내성 평가 방법론(동적 문제 생성, 형식 등가성 기반 변형) 미확립; 훈련 데이터 기능 정확성 자동 보장 부재
- 벤치마크가 단일 모듈·장난감 수준 편중 — 실무 워크플로(리포지토리 수준, sign-off 게이트) 반영 초기 단계

### 기여 가능 지점
- Tiny Tapeout 공개 코퍼스(2,000+ 설계)는 living benchmark 원료로 미개발 상태
- Yosys 형식 등가성 검사로 "변형 생성→오염 무력화" 평가셋은 로컬 컴퓨트로 충분

## (d) LLM 기반 EDA 사용성·교육 연구

### 요약
네 축 중 가장 뚜렷한 연구 공백. 기존 LLM4EDA는 숙련자 생산성에 집중했고, 교육·진입장벽 연구는 2024-2026년에 소수 등장. 특히 "설계 성과"는 측정해도 "학습 효과"를 정량 측정한 연구는 사실상 없음(대표 논문이 스스로 future work로 명시).

| 논문 | 연도/venue | URL | 핵심 주장 | 한계 |
|---|---|---|---|---|
| LLM 기반 칩설계 교육 플랫폼 (Krupp·Venn·Wehn) | 2026 (arXiv) | https://www.arxiv.org/pdf/2601.13815 | Tiny Tapeout + LLM 챗 에이전트로 고교생 18명이 90분에 tapeout-ready VGA 칩 8개 완성 | 학습 곡선 정량화 미실시(명시적 future work) |
| GUIDE | 2026 (arXiv) | https://arxiv.org/abs/2603.17296 | GenAI 디지털설계 교육용 오픈 코스웨어, 4개 강좌 실운영 | 학습효과 통제 실험 없음 |
| LLM-aided EDA 합성 오류 설명 | LAD 2024 | https://arxiv.org/abs/2404.07235 | 합성 오류 936건 설명, 71%가 초보자용으로 완전·정확 | GPT-3.5/4 시절 PoC |
| GenAI 디지털전자 교육 프레임워크(HCLTF) | JEET 2026 | https://www.journaleet.in/index.php/jeet/article/view/3587 | 학부생 187명, HDL 개발 40% 단축 + SRL 개선. 단, AI 설계는 Fmax -4.2%·LUT +20% 열화 | 단일 과제, 학습측정 도구 비표준 |

### Open problems
- AI 보조 하드웨어 설계에서 학습(개념 습득) vs 성과(완성) 분리 측정 부재 — CS 교육의 DLCI류 도구가 HW에 이식된 사례 없음
- 난이도 사다리(비전문가 한계 지도), AI 의존이 디버깅 역량에 미치는 영향 등 전부 미탐

### 기여 가능 지점
- Tiny Tapeout 생태계 + 오픈 EDA + 1인 종단 실험으로 "학습 정량 측정을 갖춘 최초급 연구"가 가능한, 경쟁 밀도가 가장 낮은 축
- Krupp et al.의 미완 과제(학습 곡선 정량화)가 곧 빈 자리

## 검색 로그 (쿼리 | 결과 수)
1. LLM-based analog circuit design automation paper AnalogCoder LayoutCopilot analog mixed-signal EDA 2024 2025 | 8
2. LLM for High-Level Synthesis C to HDL code generation HLS pragma tuning large language model paper 2024 2025 | 8
3. paper on data scarcity and benchmark contamination problems in LLM hardware design EDA Verilog benchmark limitations VerilogEval RTLLM critique 2024 2025 | 8
4. LLM chatbot for teaching hardware design education FPGA Verilog learning lowering barrier to entry study 2024 2025 | 8
5. synthetic data generation to address Verilog training data scarcity LLM CraftRTL MG-Verilog OpenLLM-RTL dataset paper | 6
6. survey LLM for EDA open challenges future directions analog HLS education benchmark 2025 arxiv | 6
