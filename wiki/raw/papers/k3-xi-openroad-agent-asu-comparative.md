---
type: raw-import
axis: xi
title: "K3 ξ. OpenROAD Agent (ASU) — self-correcting Python script generator (positioning evidence)"
date: 2026-05-25
phase: K3
curator: claude-opus-4-7
source_count: 1
intent: "본 프로젝트의 4 위임 agent(특히 experiment-runner의 script 호출) 분업과 *기능 단위 비교* 가능. Qwen2.5-Coder + hybrid SFT/RL training. 94% script accuracy. *오픈소스*. ASU Chhabria group의 *별도 sustained program* (UCSD ABK와 분리)."
---

# ξ. OpenROAD Agent (ASU) — Self-Correcting Python Script Generator (positioning baseline)

## Meta

- **Scope**: single-agent fine-tuned model for OpenROAD Python script generation. real-time error detection + correction
- **본 K3 축 역할**: 본 프로젝트의 `experiment-runner` agent(`make run` + Fargate task script 호출)와 *script-level* 비교. *오픈소스 도메인 fine-tuned model*을 본 프로젝트가 *내부 도구로 활용 가능* 여부 검토
- **Spec 참조**: `.claude/agents/experiment-runner.md`의 Bash 도구 권한 + script 호출 패턴, INTENT.md What > Operator 운영 인터페이스 § "위임 task 정의 패턴"
- **K1+K2 cut-off (2026-04-22) 이후 발표** — 2025-06-26 ICLAD, K3 ingest 필수

## Primary Source

### 1. OpenROAD Agent — Intelligent Self-Correcting Script Generator (ICLAD 2025)
- ASU PURE: https://asu.elsevierpure.com/en/publications/openroad-agent-an-intelligent-self-correcting-script-generator-fo/
- ICLAD 2025 proceedings TOC: https://www.proceedings.com/content/081/081950webtoc.pdf
- Authors: **Bing-Yue Wu** (ASU), **Utsav Sharma** (NYU), **Austin Rovinski** (NYU), **Vidya A. Chhabria** (ASU)
- Tag: [recent-SOTA, comparative-baseline, single-agent, open-source, asu-chhabria-lab]
- WHAT: **Qwen2.5-Coder** backbone + **hybrid SFT(supervised fine-tuning) + RL training**. Real-time Python script generation for OpenROAD with error detection/correction. Dynamic output refinement based on tool feedback. **94% pass@1** on script generation tasks. *Model, data, scripts 모두 open-sourced*. ASU Chhabria group의 OpenROAD-Assistant(2024 RAFT 챗봇)의 직접 후속.

### 보조 reference (같은 lab line)
- OpenROAD-Assistant (2024-09-09, Llama3-8B + RAFT, 77% pass@1, 98% BERTScore Q&A) — https://asu.elsevierpure.com/en/publications/openroad-assistant-an-open-source-large-language-model-for-physic/

## 본 프로젝트와의 5축 비교

| 차원 | OpenROAD Agent (ASU) | 본 프로젝트 | 차이 |
|---|---|---|---|
| **(a) 메타 layer** | 없음 | INTENT.md cycle | **본 프로젝트만** 메타 layer |
| **(b) Context routing** | RAFT-style retrieval (선행 OpenROAD-Assistant) + fine-tuned weights (Qwen2.5-Coder) | wiki-first hybrid (Karpathy 패턴) | **다른 substrate** — ASU는 *embedded retrieval + fine-tuning*, 본 프로젝트는 *컴파일된 위키 + LLM-agnostic* |
| **(c) Agent 분업** | 단일 fine-tuned model (specialized to OpenROAD scripting) | 4-role + Operator (specialized roles + general LLMs) | **single-domain-fine-tuned vs role-split-LLM-agnostic** |
| **(d) Scientific contribution** | 94% script accuracy (벤치마크) | reasoning trace fidelity + H1b structural patch | **다른 contribution 축** — ASU는 *task accuracy*, 본 프로젝트는 *process + novelty* |
| **(e) Skill accumulation** | fine-tuned model weights (정적, 재학습 필요) | reversible-patch skill library (iteration-grow) | **정적 vs 누적** |

**핵심 차이**: ASU OpenROAD Agent는 *fine-tuned single model*이 OpenROAD-specific script를 생성. 본 프로젝트는 *agent role 분업 + LLM 모델 agnostic*(Claude/Codex 등). **본 프로젝트의 `experiment-runner`가 ξ를 *내부 도구로 사용 가능*** — 즉 두 시스템 *complementary* 측면 존재 (mu / nu와 유사).

**Sustained program 분리 (K3-λ와의 차이)**:
- **UCSD ABK lab** (Kahng, K3-λ): ORFS-agent → ICCAD invited → AuDoPEDA(추정). *autonomous coordination + 3-tier roadmap* 지향.
- **ASU Chhabria lab** (K3-ξ): OpenROAD-Assistant(2024) → OpenROAD Agent(2025). *single-model fine-tuning + open-source release* 지향.
- **두 lab line이 직교** — 본 프로젝트 publishing 시 양쪽 모두 *위에서 인용 가능한 prior work*.

## K1/K2 cross-link 후보

- **K1-α** `k1-alpha-llm-for-hdl-evidence` — Qwen2.5-Coder fine-tuned for hardware scripting을 RTL LLM 도구 카탈로그에 추가. 현재 K1-α는 *RTL generation 모델* 중심이지만 ξ는 *script generation 모델* — *task-specific fine-tuning trend* 추가 evidence
- **K1-β** `k1-beta-agentic-eda-evidence` — ABK line(ORFS-agent → ICCAD invited)과 ASU Chhabria line(OpenROAD-Assistant → OpenROAD Agent) **두 sustained program** 비교 표 추가. parameter tuning(ABK 초기) → autonomous coordination(ABK 후기) vs Q&A(ASU 초기) → script gen(ASU 후기)의 *서로 다른 진화 궤적* 명시

## 본 K3 evidence의 spec/INTENT 영향

- **본 프로젝트의 `experiment-runner` agent system prompt에 ξ를 *호출 가능 도구로* 명시 후보** — `.claude/agents/experiment-runner.md` Bash 권한으로 ξ wrapper script 호출 가능. 본 프로젝트가 ξ를 *script generation backend*로 사용하면 LLM 비용 절감 + script accuracy 94% 활용
- **INTENT.md What > Operator 운영 인터페이스** 갱신 완료 (2026-05-25) — "K3-ξ OpenROAD Agent(ASU) fine-tuned single model 대신 LLM-agnostic 4-role 분업" 명시. 향후 ξ를 *도구로 활용*하면 본 항목 수정 필요 ("LLM-agnostic 4-role + 선택적 domain fine-tuned model 호출")
- **INTENT.md Why > 문제 두 번째 bullet** 이미 인용 완료 (commit `4148ff5`, 2026-05-25)

## Pending (Operator 결정)

- [ ] ξ 오픈소스 weights URL 확인 (Hugging Face 등)
- [ ] 본 프로젝트 `experiment-runner` Bash 권한 + ξ wrapper 통합 patch 가능성 검토 — `code-author` 위임 후보
- [ ] ASU Chhabria lab 후속 작업 모니터링 (K3-λ ABK와 별도 추적)
- [ ] 본 프로젝트 publishing 시 *두 sustained program*(ABK + ASU)을 *직교 prior work*로 인용하는 framing 확정
