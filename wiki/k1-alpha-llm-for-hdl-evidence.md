---
title: "K1-α: LLM for HDL — Direction Evidence"
type: synthesis
tags: [k1, llm-for-hdl, rtl-generation, novelty-window, benchmark]
status: active
confidence: medium
created: 2026-05-09
updated: 2026-05-09
sources:
  - raw/papers/k1-alpha-llm-for-hdl.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # H1b novelty
  - docs/knowledge-base/2026-04-19-k1-direction-report.md
---

# K1-α: LLM for HDL — Direction Evidence

본 프로젝트의 **H1b "non-knob structural patch"** 가설이 publishable seam인지 판단할 때 가장 자주 인용되는 12개 source의 결론. 자세한 source-by-source 노트는 `raw/papers/k1-alpha-llm-for-hdl.md` 참조.

## 핵심 Landscape (2026-04 시점)

| 영역 | 상태 | 시사점 |
|------|------|--------|
| **VerilogEval-Human / RTLLM v2** 모듈-레벨 RTL 생성 | **포화** — 2025–2026 agents가 90%+ pass@1 다발 | 점진 개선 단독 publish 불가 |
| **CVDP-agentic** (783 problems × 13 categories) | SOTA 34% pass@1 (Claude 3.7) | **하드 벤치마크 — novelty 가능 영역** |
| Spec→RTL→Testbench→sign-off 단일 PPA-aware 루프 | 미해결 (EvolVE가 첫 시도) | 본 프로젝트의 직접 타겟 |
| Non-Verilog HDL (Chisel/PyRTL/SpinalHDL/MLIR-CIRCT) | 벤치마크·모델 부재 | Chisel 채택 시 이 공백을 spec evidence로 활용 가능 |
| Trustworthy self-repair + 형식적 보증 (Proof2Silicon) | 초기 단계 | 본 프로젝트 scope 외 |

## Source 카테고리

### 벤치마크 layer (3종 — 모든 후속 평가의 좌표축)
- **VerilogEval V2** (Pinckney 2025) — pass@k de-facto, HDLBits 156 problems.
- **RTLLM 2.0** — 29+ designs, syntax/function/PPA 동시 점수.
- **CVDP** (NVIDIA 2025) — 783 problems, agentic + non-agentic. **본 프로젝트의 hard target.**

### Foundation models (3종 — 도메인 적응 패턴 확립)
- **ChipNeMo** (2023): domain-adapt + RAG, "domain > generic" 패턴.
- **VeriGen** (2024): 첫 open Verilog corpus + CodeGen finetune.
- **RTLCoder** (2024–2025): 7B + 27k samples, **fully-open stack** (희귀).

### Multi-agent / SOTA (5종 — 우리가 비교될 baseline)
- **MAGE** (2024) — 첫 open multi-agent, VerilogEval-Human V2 95.7%.
- **VerilogCoder** (AAAI 2025) — Task-Circuit Relation Graph + AST-based 파형 디버그.
- **AssertLLM** (ASP-DAC 2025) — 3-stage spec→SVA, 89% 합격. 검증 축의 핵심.
- **EvolVE** (2026) — MCTS vs Idea-Guided Refinement 비교 + Structured TB Gen. **PPA 66% 감소** 보고. **본 프로젝트 "Open Ideation" 트랙의 직접 이웃.**
- **RL with TB Feedback** (2025) + **CorrectBench** (2024): self-correction·RL reward 축.

### Survey (2종)
- LLM4Verilog Lit Review (2025): 102 papers, 27 benchmarks, 34 datasets.
- LLMs for EDA (2025): 2023→2025 paper 폭증(6→29→64) 정량화.

## 본 프로젝트와의 연결 (Direction Evidence)

### H1b novelty seam — "PPA-aware, sign-off-grounded, multi-agent HDL synthesis"

12개 source가 합쳐서 가리키는 미해결 seam:

> **OpenROAD/Yosys `.rpt` + STA slack + DRC를 reward·critique 신호로 쓰는 agentic 루프** + Karpathy-style **Open Ideation over Gemmini-like accelerator templates** + **CVDP-agentic** task family — 이 조합을 **AutoResearch process study**로 frame.

→ Survey들이 "missing"으로 명시한 항목과 정확히 일치. spec §H1b의 "non-knob structural patch"가 단순 의견이 아니라 **field-level open problem**임이 증거됨.

### Spec / DSE 영향

| 결정 | K1-α 근거 | 어디 |
|------|-----------|------|
| CVDP-agentic을 평가 축에 포함 | source #3, SOTA 34% = novelty window | spec §11 (평가 메트릭) |
| EvolVE 비교 baseline 명시 | source #10, "MCTS vs Idea-Guided" 직접 비교 | spec §H1b falsifier |
| Chisel 채택 (Verilog 단독 X) | survey #12 "non-Verilog HDL 공백" | spec §B (RTL 언어) |
| sign-off `.rpt` 기반 reward | landscape "PPA-aware 미해결" | spec §3 L2 substrate (skill_library) |

## 미해결 / 추가 탐색

- CVDP-agentic 13개 카테고리 중 본 프로젝트가 **어디에 집중**할지 (RTL reuse / 검증 / debug / assertions 중 선택)는 G1 직전 결정.
- EvolVE의 Structured Testbench Generation을 본 프로젝트가 재구현할지 vs reference로만 인용할지 (license 확인 필요 — License Gate §13).

## 교차 참조

- [[fsm-and-pipeline]] — agentic이 다루는 RTL 추상화 단위
- [[clock-and-timing]] — `.rpt` slack의 출처 (sign-off feedback 신호)
- [[phase-0-eda-operator-lens]] — `.rpt` 해석 능력이 K1-α 적용의 전제 조건
- (pending) `[[k1-beta-agentic-eda-evidence]]` — agent 패턴 source
- (pending) `[[k1-gamma-opensource-eda-evidence]]` — Yosys/OpenROAD 도구 layer
- (pending) `[[k1-delta-research-memory-evidence]]` — Karpathy AutoResearch 패러다임
- [[k2-eta-patch-mutation-evidence]] — RTL agent 출력에 reversible patch + SISA mutation이 적용되는 spec-binding (H1b non-knob structural patch)

## Source

- 원본: `raw/papers/k1-alpha-llm-for-hdl.md` (2026-04-19 collected, confidence: low → 본 페이지에서 medium으로 상향, spec 채택 후 high)
- 12개 외부 paper 모두 `raw/imports_manifest.yaml` 에 decision_anchors 표시됨
