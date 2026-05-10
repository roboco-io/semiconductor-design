---
plan_id: 2026-05-10-g1-first-smoke
status: approved
gate: G1
intent_alignment: confirmed
created: 2026-05-10
approved: 2026-05-10
author: experiment-designer (delegated)
operator_review: serithemage@gmail.com
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §3.2, §5.4, §6.2, §8 G1
related_intent: INTENT.md
freeze_tag: g1-smoke-pre
supersedes: none
---

# G1 첫 smoke 실험 — gcd sign-off clean run

> **Smoke level declaration**: 본 plan은 **G1 toolchain 활성화 1차 sanity** 검증이다. H1/H2/H3 *동시* 검증 *아님*. novelty 가설 검증은 본 smoke 통과 후 별도 plan에서 착수한다 (§8 후속 trigger).
>
> **Output authority**: 본 plan은 `experiment-designer` agent의 message-only output을 Operator(serithemage) 승인 후 commit한 결과물이다. 4 agent 공통 금지조항(direct commit 금지) 우회 없음.

---

## 0. INTENT.md Not 정합 declaration

각 Not 항목 · 본 plan 충돌 여부:

| Not 항목 (INTENT.md) | 본 plan에서 충돌 여부 | 근거 |
|---|---|---|
| 절대 금지 #1: PPA absolute 수치를 publish 축으로 | ✓ 위반 없음 | 본 smoke는 `sign-off clean = pass` boolean만 측정. WNS/TNS는 KG-B trigger 보조 신호로만 인용, publish claim 미생성 |
| 절대 금지 #2: 상용 EDA 사용 | ✓ 위반 없음 | LibreLane 3.0.2 + OpenROAD + Yosys + sky130A 전부 오픈소스 (§6.2 stack) |
| 절대 금지 #3: Efabless 의존 | ✓ 위반 없음 | Fargate Spot + ECR 자체 호스팅. Efabless shuttle 미참조 |
| 절대 금지 #4: functional simulation 없는 sign-off clean으로 functional correctness 주장 | ✓ 위반 없음 | 본 plan은 *toolchain 재현성*만 주장. functional correctness 주장 *없음* — 명시적 비주장 §1 |
| 절대 금지 #5: `wiki/raw/` 원본 수정 | ✓ 위반 없음 | 본 plan은 read-only 인용 — `wiki/raw/papers/k2-zeta-*` (KG-A backing) |
| 절대 금지 #6: Researcher/Developer 역할을 사람이 추가 수행 | ✓ 위반 없음 | 본 plan은 experiment-designer agent → Operator merge → experiment-runner agent 라인. 추가 사람 추가 채널 미생성 |
| 범위 밖: parameter sweep 단독 | ✓ 위반 없음 | 본 smoke는 1 candidate 1회 실행. sweep *아님* |

**총평**: 본 plan은 INTENT.md `Not` 7개 항목 중 어느 것도 위반하지 않는다.

---

## 1. 목표 (smoke level)

다음 4개 미니멈 — **하나라도 실패하면 본 plan은 negative result로 기록되고 후속 plan에서 재설계**:

1. **`make run DESIGN=gcd STACK=orfs ...` 1회 sign-off clean 완주** — gcd가 `_SUCCESS` marker로 종결, `synth.rpt` + `sta.rpt` + `drc.rpt` 모두 생성, **DRC violation = 0** + **STA WNS ≥ 0**.
2. **KG-A pass** (toolchain reproducibility): `lockfile.yaml`의 `commit_shas` + `container_digests` + `pdk_digests`가 실제 실행 컨테이너와 byte-identical, 동일 seed 재실행 시 결과 hash 동일.
3. **KG-B pass** (candidate execution): Fargate Spot 4vCPU/16GB/200 GiB ephemeral에서 LibreLane 3.0.2 gcd flow가 timeout(30분) 내 완주 (§8 G1 KG-B 정의의 smoke-축소 버전 — Chipyard+Gemmini는 본 smoke *밖*).
4. **Reasoning trace 1개** L2 substrate에 저장 — `s3://<BUCKET>/artifact/<run_id>/trace.jsonl` 형식. H3 evidence bundle 후속 plan을 위한 schema sanity. 본 smoke는 trace의 *생성 가능성*만 검증, *품질 평가*(Cohen's κ 등) *아님*.

**비주장 (smoke 명시)**:
- H1a Finding reuse rate 측정 *아님* (linear regression × seed×3 inadequate, finding corpus 미축적).
- H1b Non-knob structural patch 카운트 *아님* (본 plan은 `flow_parameters`만 사용 — gcd-orfs.yaml은 부록 C *내* knob 조합. structural patch 0건은 baseline 정의이지 H1b fail 아님).
- H1c Cold-start failure rate *아님* (single run, ORFS-agent baseline 비교 *없음*).
- H3 reasoning trace fidelity *아님* (생성만, 평가자 N≥5 미모집).
- H2 복리 효과 *아님* (1 디자인).

---

## 2. Pre-registration Freeze

**실험 시작 *전*에 git tag `g1-smoke-pre`로 freeze**. 이후 변경은 본 plan을 무효화하고 새 plan 필요 (spec §5.2-1 + §7 R7 인용).

### 2.1 Lockfile SHA freeze
- **대상 파일**: `lockfile.yaml` (repo root, §6.2)
- **freeze 시점**: smoke 시작 직전 HEAD commit SHA
- **필수 필드 검증**:
  - `commit_shas`: LibreLane 3.0.2 tag SHA, OpenROAD pinned SHA, Yosys SHA, Verilator SHA
  - `container_digests`: ECR 이미지별 SHA256
  - `pdk_digests`: open_pdks sky130A 고정 hash
  - `source_tarball_mirrors`: 미러 URL 4종 이상
- **검증 명령**: `make lockfile-verify` (Makefile 미정의 시 본 plan 시작 *전* code-author에게 위임 — separate turn).

### 2.2 Spec yaml freeze
- **대상 파일**: `specs/gcd-orfs.yaml` (repo root)
- **frozen 값**: `design: gcd` / `stack: orfs` / `flow_parameters` 6개 / `compute_budget_usd: 0.50` / `resource_overrides` (cpu_units 4096, memory_mb 16384, ephemeral_storage_gb 200)
- **이유**: gcd ~600 cells, KG-B의 30분 timeout 내 여유. ORFS stack은 LibreLane 미경유 baseline (KG-A 분리 검증 가능).

### 2.3 Seed set freeze
- **frozen seeds**: **42, 1337, 31415** (3개)
- **할당**:
  - run #1 (`gcd-orfs-<ts>-s42`): seed=42 — *primary* sign-off clean 검증
  - run #2 (`gcd-orfs-<ts>-s42-replay`): seed=42 *재실행* — 동일 seed → 결과 hash deterministic 검증 (KG-A의 핵심)
  - run #3 (`gcd-orfs-<ts>-s1337`): seed=1337 — 분포 sanity #1
  - run #4 (`gcd-orfs-<ts>-s31415`): seed=31415 — 분포 sanity #2
- **총 4 runs** = (1 primary + 1 replay) + (2 다른 seed). spec §5.4 H1b의 "seed×3" 정의(다른 seed 3개 모두 sign-off clean)는 *후속 plan*에 위임. 본 smoke의 seed×3은 *KG-A determinism 1축* + *분포 sanity 2축*으로 분리.
- **Spec 분기 방식 (Q1=a 승인)**: Makefile `run` target에 `SEED=` 변수 추가 + yq substitute 확장으로 처리. `code-author` 별도 turn 위임 — smoke 시작 *전* 선행 작업.

### 2.4 KG-A pass criteria (toolchain reproducibility)
**모두 충족 시 pass**:
- (a) **Lockfile coherence**: 4 runs 모두 spec의 `l1_lockfile_sha`가 동일 (Makefile이 `semi-run lockfile-verify --scope l1`로 주입한 값).
- (b) **Container digest coherence**: 4 runs의 ECS task definition image digest가 `lockfile.yaml.container_digests`와 byte-identical.
- (c) **Determinism**: run #1과 run #2 (둘 다 seed=42)의 `synth.rpt` + `sta.rpt` + `drc.rpt` 3 파일 SHA256 hash가 byte-identical. **하나라도 다르면 KG-A fail**.
- (d) **Provenance bundle**: 4 runs 모두 `provenance.yaml`에 `lockfile_sha` 필드 존재 + 동일.

**Note (R0 경계 인용)**: KG-A fail은 **R0 override 조건이 *아님*** (§5.3 R0 v2 — graph integrity / lint fail은 R0가 아니듯 toolchain reproducibility도 R0 publication 결정 layer 분리). KG-A는 G1 *진입* gate로만 작동.

### 2.5 KG-B pass criteria (candidate execution, smoke-축소, Q2=a 승인)
**모두 충족 시 pass**:
- (a) **Sign-off completion**: 4 runs 모두 `_SUCCESS` marker 생성 + `sign_off_status == clean`.
- (b) **Required reports**: `synth.rpt` + `sta.rpt` + `drc.rpt` 4 runs × 3 reports = 12 파일 모두 size > 0.
- (c) **DRC violation count**: 4 runs 모두 0.
- (d) **STA WNS**: 4 runs 모두 ≥ 0 ns (gcd @ 200 MHz는 여유 — clock_period_ps=5000).
- (e) **Timeout**: 각 run wall-clock ≤ 30분 (Fargate task timeout).
- (f) **Cost**: 각 run cost ≤ $0.50 (`compute_budget_usd`), 4 runs 총합 ≤ $2.00.

**Smoke 축소 (Q2=a Operator 승인)**: spec §8 KG-B 원문은 "Chipyard + Gemmini 빌드 Fargate Spot 성공"이지만, 본 plan은 gcd 단독이라 Chipyard+Gemmini 빌드는 제외. **KG-B의 *Chipyard 부분 검증*은 본 smoke 통과 후 별도 plan에서 ibex/aes 합류 시 재검증**.

### 2.6 Reasoning trace schema freeze (Q3=a 승인 — Makefile + Fargate stdout만)
- **저장 위치**: `s3://<BUCKET>/artifact/<run_id>/trace.jsonl` (L1 bundle 일부, §3.2 `reports[]` URI 리스트에 포함)
- **schema (smoke level — minimum required fields)**:
  ```json
  {"ts": ISO8601, "run_id": ULID, "stage": "rtl-build|synth|pnr|signoff|metrics",
   "actor": "agent_id|tool|human", "decision": "<freeform>", "evidence_uris": [...]}
  ```
- **본 smoke의 trace 생성 source (Q3=a 축소)**: `experiment-runner` agent의 `make run` 호출 + 각 stage Fargate task의 stdout 첫 줄 + 마지막 줄. agent decision step trace 추가는 H3 측정 plan으로 위임.
- **검증 가능성 sanity**: 4 runs × `trace.jsonl` 4 파일 모두 valid JSONL (라인당 JSON parse 성공) + 각 파일 ≥ 5 records.

---

## 3. Candidate set (1 candidate, 4 runs)

| # | Candidate | Spec | Stack | Seed | Role | Baseline 비교 |
|---|---|---|---|---|---|---|
| 1 | gcd-orfs-baseline | `specs/gcd-orfs.yaml` | ORFS | 42 | primary sign-off | self (smoke) |
| 2 | gcd-orfs-baseline-replay | (동일) | ORFS | 42 | KG-A determinism | run #1과 hash 동일 검증 |
| 3 | gcd-orfs-baseline-s1337 | (seed override) | ORFS | 1337 | distribution sanity | self |
| 4 | gcd-orfs-baseline-s31415 | (seed override) | ORFS | 31415 | distribution sanity | self |

**Reasoning trace (왜 1 candidate인가)**: K1-β `orfs-agent` source는 ORFS-agent(2025)가 ~13% slack / -40% TNS ceiling을 점유했음을 보고 (`wiki/raw/papers/k1-beta-agentic-eda.md`). 본 smoke는 그 ceiling과 *경쟁 아님* — toolchain 활성화 검증이라 candidate 1개로 충분. 다중 candidate sweep은 H1b non-knob structural patch *후속 plan*에서 시작하며, 그 때까지 본 plan은 G1 진입 gate로만 작동.

**Baseline 비교 명시 (smoke 수준)**:
- **ORFS-agent 2025 ceiling**: ~13% slack improvement / -40% TNS (K1-β source #1, `[[k1-beta-agentic-eda-evidence]]`). 본 smoke와 *비교 아님* — ORFS-agent는 *agentic tuning* 결과, 본 smoke는 *baseline ORFS flow* 1회 run.
- **이전 iteration 본 프로젝트 metrics**: *없음* (G1 첫 smoke).

---

## 4. Execution sequence

`experiment-runner` agent에 위임 시 다음 순서 (Q5=a 순차 실행 승인):

1. **Pre-flight (Operator turn, smoke 시작 *전*)**:
   1. `lockfile.yaml` 존재 + 필수 필드 검증 → 없으면 `code-author` 위임 (separate turn).
   2. Makefile `run` target에 `SEED=` 변수 추가 (`code-author` 위임, Q1=a) → smoke 시작 *전* 선행.
   3. `git tag g1-smoke-pre` (freeze §2.1~§2.6) → 본 plan commit과 atomic (Q4=c).
   4. AWS env 변수 freeze: `BUCKET`, `STATE_MACHINE_ARN`.
2. **Run #1 (seed=42 primary)**: `make run DESIGN=gcd STACK=orfs SEED=42 BUCKET=$BUCKET STATE_MACHINE_ARN=$ARN`.
3. **모니터링**: `experiment-runner` Bash + Read tool로 Step Functions execution status + Fargate task logs. Spot pre-emption 시 issues/002 retry policy (KG-D는 본 smoke *밖*이지만 Spot reclaim 발생하면 negative result 분류).
4. **`_SUCCESS` 확인 + artifact 수집**: `synth.rpt` + `sta.rpt` + `drc.rpt` + `trace.jsonl` + `provenance.yaml` 5 파일.
5. **Run #2 (seed=42 replay)**: 동일 명령 재실행 → KG-A determinism 검증.
6. **Run #3 (seed=1337)** → **Run #4 (seed=31415)**: 순차 (Q5=a — KG-D Spot reclaim 회피 + 디버그 가능성 우선).
7. **KG aggregator**: `make kg-all-smoke` (offline mode) → 본 plan §2.4 + §2.5 criteria로 pass/fail 판정.
8. **Run report 작성**: `experiment-runner` 출력 schema (`.claude/agents/experiment-runner.md` L36-L71). Operator 검수.

---

## 5. KG mapping

| KG | 본 plan 검증 | 정의 위치 | 후속 plan |
|---|---|---|---|
| **KG-A** LibreLane on Fargate (toolchain reproducibility) | ✓ §2.4 | spec §8 G1 | — |
| **KG-B** Chipyard+Gemmini build (candidate execution, smoke-축소) | ⚠ 부분 (gcd 단독, Gemmini 제외) | spec §8 G1 | KG-B full = ibex/aes + Gemmini 합류 plan |
| **KG-C** LLM SDK quota | ✗ 본 smoke 밖 | spec §8 G1 | "10-후보 세대 × 7일" 패턴 plan |
| **KG-D** Spot reclaim tolerance | ✗ 본 smoke 밖 (단, 발생 시 negative result 분류) | spec §8 G1 | PnR >20분 design plan |
| **KG-E** DDB write amplification | ✗ 본 smoke 밖 | spec §8 G1 | candidate sweep plan (multi-candidate 발생 시) |

**KG-A·KG-B 통과 = G1 *부분* 진입 신호**. G1 full exit (KG-A~KG-E 전부)은 **본 plan *밖***이며 INTENT.md 지표 "KG-A ~ KG-E 전부 통과"의 후속 plan에서 누적.

---

## 6. Negative result classification

본 smoke가 fail할 경우 `experiment-runner` 출력의 "Negative results" 섹션에 다음 분류 사용 (R3 인용 — "실패는 자산"):

| 분류 | 트리거 | 후속 plan trigger |
|---|---|---|
| **NR-toolchain-drift** | KG-A (a)·(b)·(d) fail (lockfile/digest/provenance 불일치) | code-author 위임 — lockfile 재pin |
| **NR-determinism-fail** | KG-A (c) fail (run #1 vs #2 hash 불일치) | 깊은 디버깅 → `codex:codex-rescue` (toolchain non-determinism 원인) |
| **NR-execution-fail** | KG-B (a)·(b)·(c)·(d) fail (sign-off non-clean) | gcd-orfs.yaml `flow_parameters` 재조정 plan |
| **NR-timeout** | KG-B (e) fail (>30분) | Fargate 8vCPU/32GB upgrade plan (spec §11 fallback) |
| **NR-budget-exceeded** | KG-B (f) fail (cost > $0.50/run) | `compute_budget_usd` 재산정 plan |
| **NR-spot-reclaim** | KG-D 미정의 영역에서 Spot pre-emption 발생 | issues/002 retry policy 활성화 plan |
| **NR-trace-malformed** | §2.6 reasoning trace schema 위반 | `experiment-runner` Bash command refinement |

**모든 NR은 `wiki/failures/<YYYY-MM-DD>-g1-smoke-<NR-id>.md` 후보**. 단, 본 smoke 수준에서는 finding/failure ingest *후속 plan*으로 위임 — 본 plan은 negative result *분류*만 freeze.

---

## 7. Spec §5.4 정량 임계값 인용 (참고용 — 본 smoke 검증 *아님*)

본 plan이 §5.4 임계값을 *수정·재정의 금지* (INTENT.md Learnings entry #1 invariant). 후속 plan을 위한 *복사 인용*만:

| Hypothesis | Threshold (spec §5.4 원문 인용) |
|---|---|
| **H1a** Finding reuse rate | freeze된 graphify query duplicate-finding heuristic의 자동 매칭 비율이 iteration에 따라 *non-trivial하게 증가* (linear regression **slope > 0**, **α=0.05**, **R² ≥ 0.3**) + blinded audit N≥2 일치율 ≥80% |
| **H1b** Non-knob patch | 부록 C 제외 transform이 sign-off clean × seed×3 재현, **최소 3건** |
| **H1c** Cold-start failure rate | ORFS-agent baseline 대비 **감소** (seed×3 평균) |
| **H2** 복리 효과 | linear regression slope < 0, α=0.05, R² ≥ 0.3 |
| **H3** Tertiary | N≥5 & **Cohen's κ≥0.6** & FM1~FM4 pass율 ≥50% & evaluator separation 준수 |

**본 plan에서 측정하는 임계값**: 위 5개 모두 *측정하지 않는다*. 본 plan은 §5.4 마지막 행 "L1 process — `make run` clean-VM pass, 세대당 $ 추적, KG-A~KG-E 통과" 중 KG-A + KG-B 부분만.

---

## 8. 후속 plan trigger

| 본 smoke 결과 | 후속 plan |
|---|---|
| **All green** (KG-A pass + KG-B 부분 pass + trace 4개 valid) | (a) ibex 합류 plan (KG-B Chipyard 합류) → (b) seed×3 본격 재현 plan (H1b 카운트 시작점) → (c) ORFS-agent baseline run plan (H1c 측정 baseline 확보) |
| **KG-A fail** (NR-toolchain-drift / NR-determinism-fail) | code-author + codex-rescue 위임. 본 plan을 git tag `g1-smoke-pre`로 rollback 후 재시작 |
| **KG-B fail** (NR-execution-fail / NR-timeout / NR-budget-exceeded) | gcd-orfs.yaml `flow_parameters` 또는 `resource_overrides` 재조정 plan |
| **KG-D 발생** (NR-spot-reclaim) | issues/002 retry policy 본격 활성화 plan (KG-D를 후속 plan의 1차 대상으로 격상) |

---

## 9. Hand-off to experiment-runner

본 plan이 머지된 시점 이후, **별도 turn에서 `experiment-runner` agent에 다음 4 runs 일괄 위임 권장**:

```
승인된 plan: docs/superpowers/plans/2026-05-10-g1-first-smoke.md
실행 대상: §3 candidate set 4 runs
출력: §2.4 + §2.5 criteria 기반 KG-A/KG-B pass 판정 + Run Report (experiment-runner schema)
artifact 저장: s3://<BUCKET>/artifact/<run_id>/
freeze tag: g1-smoke-pre
선행 조건: (a) lockfile.yaml verify pass + (b) Makefile SEED= 변수 추가 (code-author 별도 turn)
```

**experiment-runner contract**: `.claude/agents/experiment-runner.md` L36-L71 출력 schema 준수. 결과 해석 *금지* (rule #1 — "자동 해석 금지"). 머지 결정은 Operator.

---

## 10. Operator decisions (confirmed 2026-05-10)

| Q# | 질문 | 결정 |
|---|---|---|
| Q1 | seed×3 spec 분기 방식 | **(a) Makefile target에 `SEED=` 추가 + yq substitute 확장** — `code-author` 별도 turn 위임 |
| Q2 | KG-B Chipyard+Gemmini 축소 승인 여부 | **(a) gcd만으로 KG-B 부분 pass 인정** — smoke 수준 유지 |
| Q3 | reasoning trace 생성 source 범위 | **(a) Makefile + Fargate stdout만** — schema sanity 우선 |
| Q4 | commit 시점 + freeze tag atomicity | **(c) `git tag g1-smoke-pre`와 plan commit atomic** — §5.2-1 준수 |
| Q5 | 4 runs 실행 모드 | **(a) 순차** — KG-D 회피 + 디버그 가능성 우선 |

**모두 권장값 수용**. plan 본문 §2.3 / §2.5 / §2.6 / §4 에 결정 반영 완료.

---

## Reasoning trace (experiment-designer 자체)

본 plan을 이렇게 설계한 이유:

1. **Smoke level 명시**: 직전 INTENT.md Learnings #2가 "추상 의도 → agent system prompt → 호출 가능 시점"의 시간 layer 마찰을 발견했다. 본 plan도 같은 마찰을 인정 — G1 첫 dogfooding이라 "한 번에 H1/H2/H3 다 잡자" 유혹을 거부하고, **toolchain 활성화 boundary**만 검증하는 minimum scope로 잡았다. 이게 의도공학 layer가 *agent 단위*에서 처음 작동하는 evidence point.

2. **§5.4 임계값 *복사 인용*만**: INTENT.md Learnings #1 invariant — "INTENT.md/plan은 spec과 *정합* 해야지 *spec을 다시 정의* 하면 안 된다". 본 plan은 §7에서 spec §5.4 5개 행을 byte-identical 복사 인용. 새 정의 0건.

3. **KG-A determinism 축 = run #1 vs #2 hash 동일**: spec §8 KG-A 원문은 "30분 timeout 내 완주"만 명시하지만, *reproducibility의 hard test*는 동일 seed 재실행 hash 동일성. 이 추가 criterion은 KG-A를 *더 엄격하게* 해석한 것이지 *재정의* 아님 (spec authority 존중).

4. **gcd-orfs.yaml 단일 candidate**: K1-β source #1 ORFS-agent 2025의 13%/-40% ceiling은 *agentic tuning 영역*. 본 smoke가 그 영역을 침범하면 H1b non-knob structural patch evidence가 오염된다. 따라서 본 smoke는 **baseline ORFS flow 1회 run**으로 ceiling을 *건드리지 않고* toolchain만 활성화. 후속 plan에서 ORFS-agent baseline run을 별도 추가해 H1c 측정 시 separation 확보.

5. **KG-B 부분 검증 명시**: spec §8 KG-B는 Chipyard+Gemmini 빌드까지 포함하지만, 본 smoke가 그것까지 검증하면 **KG-B fail 원인이 LibreLane Fargate vs Chipyard 빌드 vs Gemmini SHA pin 중 어느 것인지 분리 불가**. smoke의 본질은 *원인 분리 가능한 1차 sanity*이므로 §10-Q2에서 Operator 승인 받아 명시 축소.

6. **Open questions 5개 모두 message-only output**: experiment-designer는 머지 결정 권한 *없음* (4 agent 공통 금지). Q1~Q5는 plan 본문에 박아 두고 Operator 답변 후 §2 freeze 갱신 + commit이 atomic하게 일어나야 §5.2-1 pre-registration이 실제로 작동한다.

---

## INTENT.md Why · What · Not 정합 점검 (final)

- **Why ✓**: "L1/L2/L3 파생 spec 완료 → gcd → ibex → aes 3 디자인 sign-off clean run 완주" 의 *첫 단계 — gcd*. 본 smoke는 INTENT.md Why 첫 milestone과 직접 정합.
- **What ✓**: `[ ] L1 Process: SHA-pinned Nix + Fargate Spot + Step Functions Distributed Map + S3 artifact lake + DynamoDB metadata` 의 *최소 활성화 검증*. 본 smoke가 통과하면 What L1 Process 체크리스트 1개 부분 충족.
- **Not ✓**: §0 declaration table — 7개 Not 항목 모두 위반 없음.
- **Learnings ✓**: 본 plan 자체가 INTENT.md Learnings 4번째 entry 후보 — agent dogfooding 첫 *성공* evidence. plan 품질이 의도공학 layer evidence.
