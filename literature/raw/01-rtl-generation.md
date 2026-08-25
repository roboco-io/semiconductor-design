# 조사 ①: LLM 기반 RTL 생성·수리 (2024-2026)

> 조사 에이전트 원본 결과 (2026-08-25, exa 검색, 기각된 응답 없음)

## SOTA 요약

구세대 벤치마크(VerilogEval v1 Machine/Human, RTLLM v1.1)는 사실상 포화 상태다. ChipBench(2026)는 MAGE 등 SOTA 시스템이 이들 벤치마크에서 95% 이상 pass rate를 달성해 "saturation" 상태라고 명시한다. 현재 경쟁은 (1) VerilogEval v2(spec-to-RTL) — GPT-4o 약 63%, RLVR 학습된 7B 모델 CodeV-R1이 68.6% pass@1로 671B DeepSeek-R1급 성능(RTLLM v1.1은 72.9%), (2) 신세대 난이도 벤치마크 — NVIDIA CVDP에서 SOTA가 최대 34% pass@1, RealBench(실제 IP 설계)에서 o1-preview가 모듈 레벨 13.3%·시스템 레벨 0%, ChipBench에서 Claude-4.5-opus가 Verilog 생성 30.74%로 이동했다. 즉 "작은 단일 모듈 생성"은 풀린 문제, "실제 워크플로우(멀티모듈·검증·수리·PPA)"는 크게 미해결이다. 수리(repair) 쪽은 구문 오류는 RTLFixer가 98.5% 수정으로 거의 해결, 기능 버그 수리는 여전히 낮은 정확도다.

## 핵심 논문

| 제목 | 연도 | venue | URL | 핵심 주장 | 한계 |
|---|---|---|---|---|---|
| Revisiting VerilogEval (VerilogEval v2) | 2024-25 | ACM TODAES | https://arxiv.org/abs/2408.11053 | spec-to-RTL 과제 추가, GPT-4o 약 63% — 1년간 모델 개선 추적 | 소형 단일 모듈 위주, 곧 포화 |
| QiMeng-CodeV-R1 | 2025 | NeurIPS 2025 | https://arxiv.org/abs/2505.24183 | RLVR(testbench 등가검사 보상)+round-trip 데이터 합성으로 7B가 VerilogEval v2 68.6%, RTLLM 72.9% | 검증환경이 rule-based testbench에 의존, 단일 모듈 범위 |
| CraftRTL | 2025 | ICLR 2025 | https://proceedings.iclr.cc/paper_files/paper/2025/file/e112a4671e8779aa9f640a0e3f81bd26-Paper-Conference.pdf | correct-by-construction 비텍스트 표현(K-map·파형·FSM) 합성 데이터로 파인튜닝 SOTA | 합성 데이터 의존, 실설계 일반화 미검증 |
| RTLFixer | 2024 | DAC 2024 | https://arxiv.org/abs/2311.16543 | RAG+ReAct로 구문 오류 98.5% 자동 수정, pass@1 +32.3%p(Machine) | 구문 오류 한정 — 기능 버그는 범위 밖 |
| CVDP | 2025 | preprint (NVIDIA) | https://arxiv.org/abs/2506.14074 | 13개 과제 783문항(생성·검증·디버깅·spec 정합), SOTA ≤34% pass@1 | LLM-judge/BLEU 채점 일부, 아직 리뷰 중 |
| RealBench | 2025 | arXiv | https://arxiv.org/abs/2507.16200 | 실제 IP 설계 벤치마크(100% 라인커버리지 TB+formal), o1-preview 모듈 13.3%·시스템 0% | 과제 수 제한적, 오픈소스 IP에 한정 |
| ChipSeek-R1 | 2025 | arXiv | https://arxiv.org/abs/2507.04736 | 계층적 보상(구문→기능→PPA) RL로 인간 설계 능가 RTL 주장 | PPA 평가 재현 비용, 벤치마크 범위 한정 |
| Verilog 생성 SLR (102편) | 2025 | arXiv (survey) | https://arxiv.org/abs/2512.00020 | 2020-2025.10 체계적 문헌 리뷰, 로드맵 제시 | preprint |

## Open Problems

- **검증·테스트벤치가 최대 병목**: CVDP에서 agentic 검증·RTL 재사용 과제가 가장 어려움(≤34%); RLVR 보상용 "자동·정확한 검증 환경 부재"를 CodeV-R1이 3대 난제 중 1로 명시 (arxiv 2506.14074, 2505.24183)
- **시스템/멀티모듈 설계 실패**: RealBench 시스템 레벨 0%; "복잡한 멀티모듈 설계 처리에 큰 격차" (arxiv 2507.16200, 2504.03723)
- **기능 버그 수리 저조**: 구문 수리는 해결됐으나 기능 수리는 오픈소스 SOTA Acc@1이 10%대 (VeriDebug arxiv 2504.19099, MEIC arxiv 2405.06840)
- **고품질 NL-코드 쌍 데이터 희소**: CodeV-R1·survey 공통 지적 — 합성 데이터 의존 심화 (arxiv 2505.24183, 2512.00020)
- **기능 정합을 넘어선 PPA/타이밍 최적화 미성숙**: TuRTLe·CLOSER-Bench가 sign-off 단계 평가 공백 지적 (arxiv 2504.01986, 2607.16632)
- **레퍼런스 모델 생성**: ChipBench에서 Python 레퍼런스 모델 생성 13.33% — 명시적 "underexplored domain" (arxiv 2601.21448)
- **벤치마크 포화·오염**: 기존 벤치마크가 산업 워크플로우를 반영 못함 (ChipBench, CVDP)

## Underexplored Areas

- **비-Verilog HDL**: Chisel 생성은 "largely unexplored"(ReChisel arxiv 2505.19734), VHDL은 VHDL-Eval·IBM 사례 정도로 희박
- **EDA 툴 피드백 루프의 체계적 활용**: "Can EDA Tool Feedback Improve Verilog Generation?"(arxiv 2411.11856)이 초기 시도 — synthesis/lint 피드백 통합 baseline 부재
- **멀티모달 spec 입력**(파형·다이어그램·표): CraftRTL이 학습 데이터로만 다룸, 평가 축은 RealBench가 최초 수준
- **인간 학습·교육 축 부재**: LLM-RTL 연구는 전부 모델 성능 측정 — 비전문가의 학습 성과와 결합한 평가는 문헌에서 발견되지 않음 (조사 범위 내 추론)
- **에이전트 워크플로우 자동 탐색**: VFlow(arxiv 2504.03723)가 유일 수준; 예산 제약 하 cross-stage closure는 CLOSER-Bench가 막 제기

## 재현 가능 자산

- **VerilogEval v2**: github.com/NVlabs/verilog-eval
- **CodeV-R1**: 모델+학습코드+데이터셋 전부 공개 — https://iprc-dip.github.io/CodeV-R1/
- **RTLFixer**: github.com/NVlabs/RTLFixer (코드+212 오류 데이터셋)
- **CVDP**: NVIDIA 공개 벤치마크(783문항, 오픈소스 툴 채점 인프라)
- **RealBench**: github.com/IPRC-DIP/RealBench
- **ChipBench**: github.com/zhongkaiyu/ChipBench
- **OpenLLM-RTL**(RTLLM 계열 데이터+벤치마크): arxiv 2503.15112
- **TuRTLe**(통합 평가 프레임워크): arxiv 2504.01986
- 논문·자산 인덱스: Chip Design LLM Zoo — https://iprc-dip.github.io/Chip-Design-LLM-Zoo/

## 검색 로그

| 쿼리 | 결과 수 |
|---|---|
| VerilogEval RTLLM benchmark state of the art LLM Verilog code generation pass@1 results 2025 | 10 |
| survey paper LLM for RTL code generation and repair Verilog open problems challenges 2025 | 10 |
| LLM automatic RTL bug repair Verilog debugging RTLFixer paper 2024 2025 benchmark | 8 |
| VerilogEval benchmark saturation limitations criticism new harder hardware design benchmark 2025 2026 | 8 |
| LLM code generation for Chisel and VHDL hardware description languages beyond Verilog evaluation 2025 | 8 |

(추가로 CVDP·RealBench 원문 2건 fetch. 모든 검색 응답 citation 다수 — 기각 건 없음.)
