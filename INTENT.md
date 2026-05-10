# INTENT — semiconductor-design (Report-Grounded Vibe-Coded AutoResearch)

> status: clarified
> created: 2026-05-10
> spec authority: [`docs/superpowers/specs/2026-04-19-integrated-research-program-design.md`](docs/superpowers/specs/2026-04-19-integrated-research-program-design.md) (Codex 3-round review 통과)

## Why

**문제**:
- 칩 설계는 비전문가 진입 장벽이 매우 높다. 상용 EDA 도구는 비싸고 폐쇄적, 오픈소스 도구 체인은 분산되어 진입 비용이 큼.
- 기존 agentic EDA (ORFS-agent 2025) 는 parameter knob tuning에 한정. 구조적 patch · reasoning trace 복원 가능성 · 비전문가 운영 모델 미검증.
- 의도공학(intent engineering) 패러다임이 vibe-coding + AutoResearch 환경에서 우수한지에 대한 reproducible 사례 연구 부재.

**목표 (6개월 후, 2026-11-10 무렵)**:
- L1/L2/L3 파생 spec 완료. gcd → ibex → aes 3 디자인의 sign-off clean run 완주. ORFS-agent baseline 대비 H1a/H1b/H1c 검증 결과 도출 (overview spec §5.3 canonical decision table 따라 publish/reframed/kill).
- Operator 1명이 K1 + K2 누적 위에서 spec → 코드 → 위키 → 결정의 cycle을 안정 운영. 의도공학 + Operator·프로젝트 co-evolution 1차 사례 연구 published.

**지표** (overview spec §5.4 인용 — spec authority가 nail down):
- KG-A ~ KG-E 전부 통과 (overview spec §8 G1 exit criterion).
- **H1a Finding reuse rate**: linear regression slope > 0, α = 0.05, R² ≥ 0.3 + blinded audit N ≥ 2 일치율 ≥ 80%.
- **H1b Non-knob structural patch**: 부록 C 제외 transform이 sign-off clean × seed×3 재현, **최소 3건**.
- **H1c Cold-start failure rate**: ORFS-agent baseline 대비 **감소** (seed × 3 평균).
- **H3 LLM-as-judge** κ ≥ 0.6 (§5.3 falsifier).
- Coverage ≥ 85% per module (`src/semi_design_runner/`).
- Graph integrity: orphan = 0 / dangling = 0 / AMBIGUOUS ≤ 0.3.

**고객의 말 (한 문장)**:
> 비전문가인 내가 다중 에이전트를 감독해 칩 설계 연구를 수행하면서 동시에 학습할 수 있었다 — 이 패러다임 자체가 새 모범.

## What

**핵심 기능**:
- [ ] **L1 Process**: SHA-pinned Nix (LibreLane 3.0.2 + OpenROAD + Yosys + sky130A) + AWS Fargate Spot + Step Functions Distributed Map + S3 artifact lake + DynamoDB metadata.
- [ ] **L2 Substrate**: typed-frontmatter memory + reversible-patch skill library + `L2.lint` · `skill_library` · `memory` 인터페이스 (graphify backend).
- [ ] **L3 Content**: Open-Ideation Gemmini DSE on MLPerf Tiny v1.3 streaming (Marvin) + gcd / ibex / aes 평가.
- [ ] **Operator 운영 인터페이스**: `semi-run` CLI + wiki-first hybrid 컨텍스트 라우팅 + 4 위임 agent (`experiment-designer` · `experiment-runner` · `code-author` · `eda-code-reviewer`, `.claude/agents/`) + 위임 task 정의 패턴.
- [ ] **의도공학 layer**: `INTENT.md` 생명주기 + spec ↔ wiki ↔ 결정의 *Why* 추적.
- [ ] **Co-evolution layer**: Operator Phase 0 학습 결과가 spec / wiki / skill library를 *역으로* 변형시키는 양방향 순환.

**사용자 흐름**:
1. Operator가 spec 결정 또는 위임 task 정의 (CLAUDE.md "Before Non-Trivial Work" 5단계 인용).
2. 에이전트 (Researcher / Developer 채널) 가 patch 또는 evidence 제안.
3. Operator가 검토 · 디버깅 · 머지 · 결정 승인.
4. `wiki/raw/` 에 결과 (reasoning trace · finding · decision) 누적 → wiki 컴파일 → 다음 cycle.
5. Phase 0 학습 통찰이 spec / wiki 갱신 후보로 자동 식별 → co-evolution 사이클 1회전.

**엣지 케이스**:
- Fargate Spot 회수 시 retry / fallback (issue #002 partially-resolved).
- 에이전트가 spec 의도를 왜곡한 patch 제안 → Operator 머지 거절 + reasoning trace 누적 (H3 evidence).
- Phase 0 학습 lens 부족으로 출력 검수 실패 → 학습 채널 강화 (co-evolution 신호).
- License Gate 위반 source ingest 시도 → overview spec §13 차단.

## Not

**절대 금지**:
- PPA absolute 수치 자체를 publish 축으로 삼지 않는다 (process novelty + 학술 contribution이 본진).
- 상용 EDA 도구 체인 사용. 오픈소스만.
- Efabless 경로 의존 (2025-02 셧다운으로 폐기, 대체 경로는 Iter 3+ 결정).
- functional simulation 없는 sign-off clean으로 functional correctness 주장.
- `wiki/raw/` 원본 수정 (불변 read-only).
- Researcher / Developer 역할을 사람이 추가로 수행 (single-operator multi-agent 구조 유지).

**기술 제약**:
- Python 3.12, uv 관리. ruff 100 char, target-version py312, `src tests scripts` 모두 lint/fmt.
- SHA-pinning + `lockfile.yaml` 로 도구 drift 차단.
- Reversible patch 정신 — baseline 직접 덮지 않고 patch 단위 (overview spec §7).
- 답변 · 문서 작성 시 `[[wiki/페이지]]` 인용 강제 (CLAUDE.md L13 wiki-first).
- 테스트는 `tmp_path` + fixture, `wiki/raw/` 실데이터 절대 미사용.
- Direct commits to `main` 외 feature branch 워크플로 (현재).

**범위 밖**:
- 모바일·웹 앱 인터페이스 (CLI + wiki 만).
- 다중 사용자·팀 협업 기능 (single-operator).
- 칩 양산·상용화 (학술 reproducible run 까지).
- Parameter sweep 단독 (ORFS-agent 영역, 본 프로젝트는 Open-Ideation + structural patch가 차별화 축).
- Agent system 내부 API (`L2.memory.recall` 등) 에 wiki-first 정책 적용 — spec-frozen graphify backend 유지.

**품질 기준**:
- Coverage ≥ 85% per module (`src/semi_design_runner/`).
- Graph integrity: orphan = 0 / dangling = 0 / AMBIGUOUS ≤ 0.3.
- LLM-as-judge κ ≥ 0.6 (H3 falsifier).
- KG-A ~ KG-E 전부 통과 (G1 exit).
- Reasoning trace 복원 가능 (H3 충족).

## Learnings

- **2026-05-10** — INTENT.md 첫 작성. 초안에서 (?)로 표시했던 4개 영역 중 H1a / H1b / H1c 정량 임계값이 모두 overview spec §5.4 에 이미 nail down되어 있음을 발견 (Codex 3차 리뷰에서 "H1a threshold 강화 / H1b 최소 3건 / H1c direction" 명시). **의도공학 layer 첫 invariant**: INTENT.md 는 spec 과 *정합* 해야지 *spec 을 다시 정의* 하면 안 된다. 진짜 (?)로 남는 것은 *주관적 의도 anchor* ("고객의 말 한 문장") 1개. spec 권한과 INTENT 권한의 layer 분리가 INTENT.md 단위에서 처음 명시됨.

- **2026-05-10** (agent dogfooding 첫 시도) — 4 위임 agent 정의 commit 직후 `experiment-designer` 를 `Agent` tool로 호출하니 "Agent type not found" 오류. Available agents 목록에 본 프로젝트 agent 4개가 없음. **운영 invariant 발견**: agent 정의 ↔ 호출 가능성 사이에 *세션 재시작이 필요한 시간 지연*이 존재. 의도공학 layer가 의도(추상) → agent system prompt(구체) → *호출 가능 시점*(시간) 의 3 단계임을 첫 dogfooding이 드러냄. 향후 agent system 갱신 시 "정의 후 즉시 dogfooding 불가, 세션 재시작 필요"가 운영 규칙. 본 발견 자체가 의도공학 우수성 증명의 첫 evidence point — *추상 의도가 어디서 운영 boundary와 마찰하는가*.

- **2026-05-10** (정합 작업) — 직전 turn에 "K2 cluster의 K2 → K1 backlink가 없는 비대칭" 이라 advisory를 적었으나, 실제 grep 검증 시 K2 4 페이지 모두 K1 backlink 풍부 보유 (k2-η·k2-θ는 K1 4개 모두). **추측이 사후 grep 검증을 대체하지 않는다는 invariant 확인** — 정합 작업 전 grep 검증이 default로 들어가야 함. 본 발견은 본 프로젝트 H3 가설(reasoning trace 복원 가능성)의 *작은 실패 사례* — Operator 검토가 추측을 잡아냄.
