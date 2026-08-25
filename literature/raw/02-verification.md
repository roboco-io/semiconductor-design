# 조사 ②: AI/LLM 기반 하드웨어 검증 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색, 기각된 응답 없음)

## SOTA 요약

AI/LLM 기반 하드웨어 검증 연구는 2024년을 기점으로 벤치마크 정립 단계에 진입했다. SVA 생성(AssertLLM, AssertionBench, FVEval), testbench 자동 생성(AutoBench→CorrectBench), RTL 디버깅(RTLFixer, HDLdebugger, MEIC) 등 서브태스크별 프레임워크가 나왔고, 2025년에는 검증 전 과정을 포괄하는 대형 벤치마크(FIXME 747 태스크, NVIDIA CVDP 783 문제)가 등장했다. 그러나 공통 결론은 "실무 투입 불가 수준": 최고 모델도 SVA 유효율 약 44%(AssertionBench 5-shot GPT-4o), CVDP pass@1 ≤34%이며, 구문 정확과 의미 정확 사이 괴리가 크다.

검증은 개발 주기의 약 70%를 차지함에도(ASPDAC 2026 서베이) LLM 연구는 RTL 생성에 편중돼 있다. RTL 생성 벤치마크(VerilogEval 2023, RTLLM)가 2년 이상 앞서 성숙했고, 검증 전용 벤치마크는 2024년 후반-2025년에야 등장 — 연구 밀도는 생성 대비 눈에 띄게 낮고, 특히 커버리지 클로저·formal과의 결합은 초기 단계다.

## 핵심 논문

| 제목 | 연도 | venue | URL | 핵심 주장 | 한계 |
|---|---|---|---|---|---|
| AssertionBench | 2024/25 | NAACL Findings 2025 | https://aclanthology.org/2025.findings-naacl.449/ | 100개 OpenCores 설계 + JasperGold 검증 SVA로 LLM 정량 평가. 최고 GPT-4o 44%(5-shot) | 얕은 temporal depth만, Verilog만, 상용 FPV 의존 |
| AssertLLM → AssertLLM2 | 2024→2026 | arXiv | https://arxiv.org/abs/2402.00386 / https://github.com/hkust-zhiyao/AssertLLM2 | 스펙→SVA 멀티-LLM 파이프라인; v2는 83개 실설계 + buggy RTL 입력으로 bug-hunting 최초 평가, mutation/COI 기반 품질 지표 | LLM은 구문상 유효한 SVA는 내지만 "실질 검증 가치"는 낮다고 자인 |
| FVEval | 2024 | arXiv (NVIDIA) | https://arxiv.org/abs/2410.23299 | formal verification 태스크(NL→SVA, RTL 기반 SVA 제안) 최초 종합 벤치마크 | 평가 범위가 SVA 중심, full formal flow(모델체킹 전략 등) 미포함 |
| AutoBench / CorrectBench | 2024 | ICCAD'24 / arXiv | https://arxiv.org/abs/2407.03891 / https://arxiv.org/abs/2411.08510 | NL 스펙만으로 testbench 생성+자기검증+자기수정. pass 33%→52%→70% | sequential 회로 여전히 취약, self-validation이 스펙 이해 오류에 취약 |
| RTLFixer | 2023/24 | DAC 2024 (NVIDIA) | https://arxiv.org/abs/2311.16543 | RAG+ReAct 에이전트로 Verilog 구문 오류 98.5% 자동 수정 | **구문 오류 한정** — 기능 버그는 범위 밖 |
| MEIC | 2024 | arXiv | https://arxiv.org/abs/2405.06840 | 반복적(iterative) RTL 기능 버그 수정 프레임워크 | 기존 접근 전반의 pass@k가 "실용과 거리 멀다"고 명시 |
| FIXME | 2025/26 | AAAI (v40) | https://arxiv.org/abs/2507.04276 | 검증 전 과정(스펙 이해·참조모델·TB·SVA·RTL 수리) 747 태스크 최초 end-to-end 벤치마크 | GPT-4.1급도 핵심 한계 노출; L3(고난도) 성능 급락 |
| CVDP | 2025 | arXiv (NVIDIA) | https://arxiv.org/abs/2506.14074 | 783 문제·13 카테고리(생성+검증+디버깅), 에이전틱 포맷 포함. SOTA ≤34% pass@1 | 검증·RTL 재사용 에이전틱 태스크에서 특히 저조함을 보고 |
| LLM-Assisted Circuit Verification Survey | 2026 | ASPDAC 2026 | https://www.cse.cuhk.edu.hk/~byu/papers/C312-ASPDAC2026-Verif.pdf | 검증(어서션·TB·디버깅·협업 프레임워크) 전 분야 서베이, 검증=개발주기 70% 병목 | — (서베이) |

## Open Problems (논문이 명시한 미해결 문제)

- **구문↔의미 괴리**: 구문 정확한 SVA도 최대 24%가 formal에서 반증됨 — 설계 의미론 이해 실패 (AssertionBench)
- **어서션 품질 함정**: 신호명 불일치, vacuous proof, 중복, 커버리지 부풀리기(misleading coverage inflation) — 품질 인지형 평가 필요 (Mali & Karfa, arXiv:2607.07444; AssertLLM2)
- **sequential/temporal 취약**: 순차 회로 testbench·다중 사이클 temporal 어서션에서 성능 급락 (CorrectBench, AssertionBench)
- **기능 버그 수리 미성숙**: 구문 수정(98.5%)과 달리 기능 디버깅 pass@k는 실용 불가 수준 (RTLFixer는 구문 한정 자인; MEIC)
- **산업 규모 확장성·EDA 통합·해석가능성**: 서베이 공통 지적 (MDPI Electronics 2024; ASPDAC 2026 서베이)
- **에이전틱 검증 태스크 최난도**: RTL 재사용·검증 관련 에이전트 태스크가 가장 낮은 점수 (CVDP)
- **스펙 품질 의존**: 원문 PDF 스펙의 표·그림 멀티모달 정보 처리 실패가 평가를 오염 (AssertLLM2)

## Underexplored Areas

- **커버리지 클로저**: LLM 유도 stimulus로 functional coverage를 닫는 연구는 VerilogReader(arXiv:2406.04373) 등 극소수, 표준 벤치마크 부재
- **formal 전략 자동화**: SVA 생성 이후 단계(abstraction, convergence, bug hunting 전략)는 FVEval조차 미포함
- **UVM 환경 전체 생성**: LLM-aided UVM Machine(arXiv:2504.19959) 등 초기 시도만 존재
- **클래식 baseline 비교 누락**: GoldMine/HARM 등 비-LLM 어서션 마이닝, CRV 대비 정량 비교가 대부분 논문에서 빠짐
- **오픈소스 평가 인프라**: 다수 벤치마크가 Cadence JasperGold 의존 → 재현성 제약 (CVDP만 오픈소스 툴 기반)
- **Verilog 외 언어**: VHDL/SystemC/Chisel 어서션·TB 생성은 거의 공백 (AssertionBench 명시)
- **buggy RTL 입력 평가**: 버그 탐지력 직접 측정은 AssertLLM2(2026)가 최초라 주장 — 그만큼 공백이었음

## 재현 가능 자산

- **CVDP**: https://github.com/NVlabs/cvdp_benchmark (783문제, 에이전틱 하네스 포함)
- **AssertionBench**: https://github.com/achieve-lab/assertion_data_for_LLM
- **FVEval**: https://github.com/NVlabs/FVEval
- **RTLFixer**: https://github.com/NVlabs/RTLFixer (디버깅 데이터셋 212건 포함)
- **AutoBench/CorrectBench**: https://github.com/AutoBench/CorrectBench
- **AssertLLM2**: https://github.com/hkust-zhiyao/AssertLLM2 (데이터셋·평가 스크립트·buggy RTL 생성 스크립트)
- **FIXME**: AAAI 논문 (747 태스크; arXiv:2507.04276 경유 공개)

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| LLM-based hardware verification survey 2024 2025: testbench generation, SVA generation, RTL bug detection, coverage closure papers | 10 |
| AssertionBench benchmark evaluating LLM SystemVerilog assertion generation paper | 8 |
| AutoBench CorrectBench LLM automatic testbench generation Verilog paper 2024 2025 | 8 |
| NVIDIA CVDP Comprehensive Verilog Design Problems benchmark LLM agent hardware verification 2025 | 8 |
| RTLFixer HDLdebugger LLM automatic RTL bug repair debugging Verilog paper limitations | 8 |
| survey LLM for hardware design and verification research gap coverage closure formal verification LLM open problems 2025 | 8 |
