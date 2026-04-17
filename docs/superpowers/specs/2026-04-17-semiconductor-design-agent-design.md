# Semiconductor Design Agent — 설계 문서

| | |
|---|---|
| **작성일** | 2026-04-17 |
| **작성자** | Jung Do Hyun (serithemage@gmail.com) |
| **프로젝트 경로** | `roboco-io/research/semiconductor-design` |
| **이터레이션** | 1 (MVP) |
| **상태** | Draft — 브레인스토밍 합의 완료, 구현 계획 대기 |

---

## 1. 목적 (Why)

비전문가(반도체·HW 입문자)가 **AI 에이전트를 통해 단기간에 딥러닝 가속기를 end-to-end로 설계**하고, **시뮬레이션에서 MLPerf Tiny급 벤치마크를 통과**하는 결과물을 만들 수 있음을 실증한다. 결과물은 두 축:

1. **논문** — 에이전트 기반 칩 설계 자동화, 특히 "도메인 위키를 갖춘 LLM 에이전트 + 서버리스 DSE" 조합의 novelty를 데이터로 방어한다.
2. **오픈소스** — GitHub 공개 저장소. `make run` 한 줄로 누구나 $30 내에서 재현 가능한 레퍼런스 구현.

## 2. 비목표 (Not)

- 자체 LLM fine-tune (기성 Claude·Codex SDK만 사용)
- 상용 EDA(Synopsys·Cadence) 비교
- 실물 테이프아웃 (Tiny Tapeout·Efabless) — 이터레이션 3+
- FPGA 에뮬레이션(FireSim) — 이터레이션 2+
- MLPerf Training·Datacenter Inference — 규모 초과

## 3. 배경·선행 연구

- **LLM for HDL**: RTLCoder, VeriGen, ChipNeMo, VerilogCoder(agentic), MAGE(multi-agent), EvolVE(2026, SOTA)
- **RL for 칩 설계**: Google AlphaChip(floorplan)
- **오픈소스 EDA 스택**: Yosys · OpenLane2 · OpenROAD · Verilator · SkyWater sky130A PDK
- **오픈소스 가속기 템플릿**: Gemmini(Berkeley, Chipyard 통합)
- **유사 서버리스 패턴**: `roboco-io/research/serverless-autoresearch` — HUGI(Hurry Up and Get Idle) + Population Evolution
- **지식 베이스 패턴**: Karpathy LLM Wiki(gist 2026-04), qmd 하이브리드 검색, LanceDB + Embedding Atlas

## 4. 타깃 사용자 프로필

- MLOps / ML Pipeline 엔지니어 (AWS 서버리스 숙련)
- PyTorch·CUDA 직접 구현 경험 없음
- 반도체 HW·EDA 도메인은 초보
- 에이전트 오케스트레이션 경험 풍부 (Step Functions·Lambda·SageMaker)

## 5. 시스템 아키텍처

### 5.1 4-plane 분리

```
┌─────────────────────────────────────────────────────────────────────┐
│ LOCAL (개발자 머신)                                                    │
│ - Python CLI orchestrator (uv)                                       │
│ - Claude Code SDK → Spec / Architect / Planner / Evaluator / Verif.  │
│ - Codex SDK        → RTL Agent / Testbench Agent                     │
│ - boto3로 Step Functions StartExecution, S3 업로드                    │
│ - SQLite(population 캐시), .cache/traces/*.jsonl (LLM 원본 로그)       │
└─────────────────────────────────────────────────────────────────────┘
           │ (1) spec.yaml, candidates.json → S3 put
           │ (2) StartExecution(stateMachineArn, input)
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ AWS (전부 CDK TypeScript로 프로비저닝)                                  │
│                                                                     │
│ Step Functions Standard Workflow                                     │
│   Map state (maxConcurrency=10) — 한 세대 = 10 후보                   │
│     ├─ rtl-build  Fargate Spot, 2-5분                                │
│     ├─ synth      Fargate Spot, 5-15분 (Yosys)                       │
│     ├─ pnr        Fargate Spot, 15-30분 (OpenLane2/OpenROAD)         │
│     ├─ simulate   Fargate Spot, 10분 (Verilator + MLPerf Tiny)       │
│     └─ sign-off   Fargate Spot, 10분 (STA·DRC·LVS)                   │
│                                                                     │
│ S3 artifacts / DynamoDB(4 tables) / ECR(4 repos) / EventBridge       │
│ CloudFront + 정적 Next.js 대시보드                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 설계 원칙

- **LLM은 로컬, 컴퓨팅은 AWS 서버리스** — LLM 비용 통제·디버깅 용이, EDA 무거운 작업만 Spot으로 burst
- **Anti-reinvention** — 기존 도구(Yosys·OpenLane2·Chipyard·Gemmini·mlcommons/tiny) wrap/delegate, 재구현 금지
- **경계 원칙**: Control plane은 코드를 짜지 않는다(LLM은 spec 변환·파라미터 선택·로그 해석만). Tool plane은 에이전트 존재를 모른다(모두 CLI 호출 가능)
- **멱등성**: 모든 job은 `{stage}/_SUCCESS` 파일 체크 → 있으면 skip. `candidate_id = hash(params.json)`

### 5.3 novelty 포인트 (논문 방어)

1. **"HUGI for Silicon"** — 전통적으로 수시간 wall-clock인 DSE를 Fargate Spot 병렬 10배수로 압축한 사례
2. **Cross-LLM Consensus** — Claude·Codex가 서로의 RTL을 검증하고, 불일치 시 시뮬레이션으로 중재. 수집된 일치·불일치 데이터는 "어느 LLM이 어느 HW 도메인에 강한가"의 실증 데이터셋
3. **Knowledge-augmented Agent** — 도메인 위키 ablation(B1 vs B3)으로 위키 기여도를 수치 입증
4. **로컬-클라우드 하이브리드** — LLM 비용을 개발자가 통제하면서 서버리스 burst

## 6. 에이전트 설계

| # | 에이전트 | SDK | 입력 | 출력 | 실패 처리 |
|---|---|---|---|---|---|
| 1 | Spec Agent | Claude Code | 자연어 요구사항(대화) | `spec.yaml` | 사용자 재질문 |
| 2 | Architect Agent | Claude Code | `spec.yaml` | `search_space.yaml` | Spec으로 에스컬레이션 |
| 3 | Planner (규칙+LLM) | Claude Code(소량) | `search_space` + 이전 메트릭 | `population.json` (10후보) | 결정론적 fallback |
| 4 | RTL Agent | **Codex**(1차) + Claude(리뷰) | 후보 파라미터 | `rtl/*.v` | 3회 self-heal 후 포기 |
| 5 | Testbench Agent | Codex | RTL + spec | `tb/*.v` + cocotb | Claude 재시도 |
| 6 | Verification Agent | Claude Code | 시뮬 로그·파형 | {pass/fail, 원인, 수정 제안} | RTL Agent에 re-gen |
| 7 | Sign-off Agent | Claude Code | STA/DRC 로그 | {violations, 권고} | 파라미터 축소 제안 |
| 8 | Evaluator Agent | Claude + Codex(consensus) | 세대 Pareto | 다음 세대 전략 | 로그 남기고 Planner로 |
| D1 | Metric Aggregator | - | job 결과 | DDB put | SF Catch → DLQ |
| D2 | Cost Tracker | - | CloudWatch + SF 이력 | 세대별 $ 리포트 | - |

### 6.1 Cross-LLM Consensus (이터레이션 1은 RTL Agent에만 적용)

```
RTL Agent (Codex) ─┐
                   ├→ diff 비교
RTL Reviewer (Claude)┘
  ↓ 불일치 시
Arbitration: 양측 RTL을 모두 합성·시뮬레이션 → 통과한 쪽 선택
```

### 6.2 통신 패턴

- 에이전트끼리 직접 통신 X. 로컬 orchestrator가 모든 호출을 조율
- 모든 LLM 호출은 JSONL 트레이스로 로컬에 저장 (`~/.cache/semi-design/traces/`)
- AWS에는 확정된 artifact만 업로드

## 7. 데이터 모델

### 7.1 Pydantic 스키마 핵심

```python
class Spec(BaseModel):
    run_id: str                                 # ULID
    target_model: Literal["mlperf_tiny_kws", "mlperf_tiny_ic", ...]
    constraints: Constraints                    # max_area_um2, max_power_mw, target_latency_us
    technology: Literal["sky130hd", "gf180mcu"]
    iteration: int = 1

class Candidate(BaseModel):
    candidate_id: str                           # hash(params) 기반
    params: GemminiParams                       # meshRows/Cols, dataflow, precision, ...
    parent_ids: list[str]
    mutation_kind: Literal["conservative","moderate","aggressive","crossover"]
    llm_trace_uri: str

class Metrics(BaseModel):
    area_um2: float; power_mw: float; max_freq_mhz: float
    mlperf_accuracy: float; mlperf_latency_us: float
    synth_wns_ns: float; drc_violations: int
    pareto_rank: int | None
    cost_usd: float
```

### 7.2 S3 레이아웃

```
s3://semi-design-{account}-{region}/
├── runs/{run_id}/
│   ├── spec.yaml
│   ├── search_space.yaml
│   ├── gen_000/population.json
│   ├── gen_000/cand_{0..9}/
│   │   ├── params.json
│   │   ├── rtl/, synth/, pnr/, sim/, signoff/
│   │   └── logs/
│   └── gen_001/...
└── shared/pdk/sky130/, shared/docker-digests.json
```

### 7.3 DynamoDB (4 테이블)

| 테이블 | PK | SK | 주요 속성 |
|---|---|---|---|
| `Runs` | `run_id` | — | spec_uri, status, total_cost |
| `Generations` | `run_id` | `gen#{N}` | population_uri, pareto_uri, cost |
| `Candidates` | `run_id` | `gen#{N}#cand#{K}` | params, stage_status, metrics, sfn_execution_arn |
| `Events` | `run_id` | `ts#{iso}` | kind, payload (TTL 90일) |

GSI: `Candidates` on `status`, on `pareto_rank`

## 8. Knowledge Substrate (도메인 위키 + 스킬화)

### 8.1 물리 구조

```
semiconductor-design/
├── wiki/                              # main repo에 커밋 (숨김 아님)
│   ├── raw/
│   │   ├── papers/ manuals/ pdk/ benchmarks/ sessions/
│   │   └── (한국어 노트 포함)
│   ├── (컴파일된 [[wiki-link]] 페이지들)
│   ├── index.md
│   ├── log.md
│   └── CLAUDE.md                      # 위키 스키마
└── .claude/skills/semi-design-wiki/   # 프로젝트 로컬 스킬
    ├── SKILL.md
    ├── scripts/init.sh, sync_index.py, lint_wiki.py
    └── references/page-templates.md, ingest-workflow.md, semiconductor-ontology.md
```

### 8.2 초기 wiki/ 페이지 세트 (MVP ≤20페이지)

| 범주 | 페이지 |
|---|---|
| 아키텍처 | `[[Gemmini-Parameters]]`, `[[Systolic-Array-Tradeoffs]]`, `[[Dataflow-Types-WS-OS-IS]]` |
| Flow 단계 | `[[RTL-to-GDSII-Pipeline]]`, `[[OpenLane2-Stages]]`, `[[STA-Sign-off-Checklist]]` |
| 오류 사전 | `[[DRC-Violation-Patterns]]`, `[[Timing-Closure-Recipes]]`, `[[Setup-Hold-Debug]]` |
| 워크로드 | `[[MLPerf-Tiny-Models]]`, `[[INT8-Quantization-Mapping]]` |
| 의사결정 | `[[DSE-Conservative-Moderate-Aggressive]]`, `[[Pareto-Selection-Heuristics]]` |

각 페이지 프론트매터: `type, tags, confidence, sources, last_ingested`. `lint_wiki.py`가 저신뢰 페이지·고아·끊어진 링크 점검.

### 8.3 에이전트 ↔ 위키 통합

모든 LLM 에이전트 시스템 프롬프트에 선행 단계 주입:
1. `wiki/index.md`에서 관련 페이지 2-3개 식별
2. 2-hop까지 읽어 맥락 확보
3. 답변에 `[[페이지]]` 인용
4. 위키에 없으면 "위키에 없음" 명시 후 `raw/` 참조

### 8.4 자기 강화 루프 (복리 효과)

각 이터레이션의 실패·성공 로그를 `wiki/raw/sessions/gen_{N}.md`로 저장 → 수동 `wiki ingest` → 오류 사전·recipe 페이지 업데이트 → 다음 이터레이션 에이전트가 더 똑똑해짐. 이 성숙도 곡선을 논문 figure로.

### 8.5 Scope 제한 (이터레이션 1)

- wiki 페이지 ≤20, 인덱스 라우팅만 (qmd/LanceDB 미도입)
- `wiki ingest`는 **수동** 트리거
- 스킬은 프로젝트 로컬(`.claude/skills/semi-design-wiki/`), 안정화 후 공개 검토

## 9. Step Functions Workflow

### 9.1 최상위

```
StartAt: ValidateSpec
  ValidateSpec         Lambda   spec.yaml 검증, DDB Runs 생성
  InitGeneration       Lambda   population.json 로드
  EvaluateCandidates   Map      conc=10, candidate 서브워크플로우
  AggregateGeneration  Lambda   Pareto 계산, DDB Generations 업데이트
  NotifyLocal          Event    EventBridge → 로컬 polling
  End
```

### 9.2 Map 내부 (1 candidate)

```
RtlBuild → Synth → PnR
                  └─(DrcFail/TimingFail)→ RecordFailure → end
                  └─ Parallel(Sim, SignOff) → RecordCandidate
```

### 9.3 실패·재시도 정책

| 실패 유형 | 처리 |
|---|---|
| Spot 회수 | Retry MaxAttempts=2, Interval=30s, BackoffRate=2 |
| OOM | Retry 1회 with 2x cpu/memory |
| DRC 위반 | Catch → RecordFailure → candidate 종료, 다음 계속 |
| STA 미달 | 동일, Evaluator가 다음 세대 주파수 제약 완화 제안 |
| 원인 불명 | Catch All → SQS DLQ → 로컬 알람 |

세대 내 실패율 > 50% 시 CircuitBreaker Lambda가 Abort → 세대 폐기.

### 9.4 CDK 스택 구성 (TypeScript)

```
cdk/
├── bin/semi-design.ts
├── lib/stacks/
│   ├── NetworkStack.ts        VPC + private subnets
│   ├── StorageStack.ts        S3, DDB 4개, KMS
│   ├── ContainerStack.ts      ECR 4개
│   ├── ComputeStack.ts        ECS cluster, Task Defs (Fargate Spot)
│   ├── WorkflowStack.ts       Step Functions, Lambdas, EventBridge
│   └── ObservabilityStack.ts  대시보드, 알람
└── lib/constructs/
    ├── FargateJobTask.ts
    └── AgentLambda.ts
```

IAM 최소 권한 원칙. `--context env=dev|prod`로 환경 분리.

## 10. 도구·버전 (재현성)

| 영역 | 선택 | 버전 |
|---|---|---|
| 가속기 템플릿 | Gemmini | `ucb-bar/gemmini@main` (Chipyard 통합) |
| SoC 프레임워크 | Chipyard | `1.13.x` |
| 합성 | Yosys | `0.44+` |
| P&R · Sign-off | OpenLane 2 | `efabless/openlane2@main` (Nix) |
| 시뮬레이터 | Verilator | `5.026+` |
| 테스트 프레임워크 | cocotb | `1.9+` |
| PDK | SkyWater sky130A | `google/skywater-pdk@main` |
| 벤치마크 | mlcommons/tiny | `v1.2+` |
| LLM (주) | Claude Code SDK | 최신 |
| LLM (RTL) | Codex SDK | 최신 |

### 10.1 Docker 이미지 (ECR)

| 리포 | 베이스 | 설치물 | 예상 크기 |
|---|---|---|---|
| `semi/rtl-build` | `debian:12-slim` | sbt, JDK 17, Chipyard | ~2.5GB |
| `semi/synth` | `debian:12-slim` | Yosys 0.44 | ~400MB |
| `semi/pnr` | OpenLane2 공식 Nix | OpenLane2 고정 커밋 | ~3GB |
| `semi/sim` | `debian:12-slim` | Verilator, cocotb, mlcommons/tiny | ~1.5GB |

모든 이미지는 `latest` 태그 금지·**SHA 디지스트 핀**. `shared/docker-digests.json`으로 재현성 확보.

### 10.2 Gemmini 탐색 공간 (이터레이션 1)

| 파라미터 | 값 |
|---|---|
| `meshRows × meshCols` | {4×4, 8×8, 16×16} |
| `tileRows × tileCols` | {1×1, 2×2} |
| `inputType` | {SInt(8), SInt(16)} |
| `accType` | {SInt(20), SInt(32)} |
| `dataflow` | {WS, OS, Both} |
| `scratchpad size` | {64KB, 128KB, 256KB} |
| `target freq` | {50, 100, 200 MHz} |

648 조합 → 세대당 10후보 × 10세대 = 100 평가로 Pareto 수렴 가능.

## 11. 평가 전략

### 11.1 워크로드

이터레이션 1 타깃: **MLPerf Tiny KWS (DS-CNN, 22K params)**.
이터레이션 2+: IC(MobileNetV1), VWW(ResNet-8), AD(AutoEncoder).

### 11.2 메트릭

```
MetricVector = {
  mlperf_accuracy,        # 기준 모델 대비 유지율 (목표 ≥90%)
  mlperf_latency_us,      # 시뮬 사이클 × 1/freq
  area_um2,               # post-PnR
  power_mw,               # OpenROAD 추정
  max_freq_mhz,           # STA WNS 역산
  energy_per_inference_uj,
  cost_usd,               # 이 후보 실행 AWS 비용
}
```

### 11.3 Pareto

3차원: (area_um2, energy_per_inference_uj, 1-accuracy). 세대별 frontier DDB 저장, 대시보드 overlay.

### 11.4 베이스라인

| ID | 의미 |
|---|---|
| B0 | 전문가 수작업 Gemmini 튜닝 1회 (상한 참조) |
| B1 | LLM 단일 호출, 위키 없음 |
| B2 | 에이전트 + 위키, cross-LLM 없음 |
| B3 | 제안 전체 시스템 |
| B4 | Random DSE (동일 예산) |

모두 동일 AWS 예산(~$30) 내 비교. "비용 대비 Pareto hypervolume"이 논문 대표 그림.

### 11.5 비용 개념 추정 (세대 1회)

| 항목 | 비용 |
|---|---|
| Fargate Spot (40 task × 12분 × 4 vCPU 8GB) | ~$2.5 |
| S3 storage | $0.05 |
| DDB 쓰기 | $0.01 |
| Step Functions transitions | $0.004 |
| Lambda + CloudWatch | $0.02 |
| **합계** | **~$2.6/세대** |

10세대 $25 내. Budget 알람 $50·$100.

## 12. 이터레이션 1 MVP 경계

### 12.1 Scope 동결 (포함)

- KWS 단일 워크로드, sky130A PDK
- Spec → Architecture → RTL → Synth → PnR → Sim → Sign-off → Evaluate 풀 루프
- Claude Code SDK + Codex SDK (RTL Agent만 cross-LLM consensus)
- Step Functions + Fargate Spot + DDB + S3 + CDK(TS)
- `wiki/` + `.claude/skills/semi-design-wiki/` + 초기 ≤20 페이지 (한글 포함)
- 10세대 × 10후보 1회 완주 + 베이스라인 B1·B4 비교

### 12.2 Scope 제외

- IC/VWW/AD, gf180mcu, FireSim, 실물 테이프아웃
- 자동 ingest·qmd·LanceDB
- 웹 대시보드 실시간 업데이트(정적만)

## 13. 성공 기준

| 축 | 지표 |
|---|---|
| 오픈소스 | GitHub 공개, `make run` 한 줄, $30 이하 재현 |
| 논문 | B1·B4 대비 비용당 Pareto hypervolume 우위 수치 |
| 기술 완결성 | KWS 정확도 ≥90% 유지, candidate 실패율(sign-off 미달 비율) <30%, clean sign-off 통과 후보 최소 1개 이상 |
| 교육 | JSONL 트레이스로 비전문가가 결정 맥락을 읽을 수 있음 |

## 14. 마일스톤 (솔로, 주 단위)

| 주 | 내용 |
|---|---|
| W1 | 위키 부트스트랩(raw 수집·초기 ≤20페이지·스킬), 로컬 Chipyard/Gemmini/OpenLane2 smoke test |
| W2 | CDK 스택 + ECR 이미지 4개 빌드·푸시, Fargate 단일 job 성공 |
| W3 | Step Functions Map 작동, candidate 1개 end-to-end 자동 완주 |
| W4 | 에이전트 스캐폴딩(Claude·Codex SDK), population 10 생성·평가 자동화 |
| W5 | 10세대 루프 완주, 대시보드·리포트 |
| W6 | 베이스라인 B1·B4 실행, 결과 정리, 논문 figure 초안 |
| W7-8 | README·튜토리얼, 리팩터, 공개 준비 |

총 **8주**.

## 15. 리스크·완화

| 리스크 | 완화 |
|---|---|
| OpenLane2 Nix가 Fargate에서 미가동 | W1 우선 검증, 실패 시 OpenLane1로 다운그레이드 |
| Chipyard 빌드가 Fargate 4vCPU에 너무 느림 | S3 빌드 캐시, 또는 사전 빌드 baseline 아티팩트 |
| MLPerf Tiny ↔ Verilator 연결 난이도 | W2 초반 PoC, 실패 시 정확도는 software 모델 대체 |
| Cross-LLM consensus 구현 복잡 | 이터레이션 1은 "둘 다 합성 시도, 통과한 쪽 선택" 단순 버전 |
| AWS 비용 폭주 | Budget 알람 $50·$100, 세대 시작 전 dry-run |
| Codex SDK 접근성·쿼터 | 초기 단계에 실사용 확인, 필요 시 RTL Agent도 Claude로 통일 |

## 16. 열린 결정 (이터레이션 1 수행 중 확정)

- Planner의 crossover 구체 알고리즘 (현재: LLM 제안 기반 단순 교차)
- Fargate Spot vs On-Demand 혼합 정책 (회수율이 높을 시)
- 위키 ingest 자동화 시점 판단 기준 (페이지 수, lint 경고 수 등)
- 대시보드 프레임워크 최종 (Next.js 정적 확정, 템플릿 미정)

## 17. 부록 — 주요 참고 리소스

- `roboco-io/research/serverless-autoresearch` (HUGI·population 패턴 원형)
- [CatIIIIIIII/RTL-LLM-Paper-List](https://github.com/CatIIIIIIII/RTL-LLM-Paper-List)
- [hkust-zhiyao/RTLLM](https://github.com/hkust-zhiyao/RTLLM)
- [ucb-bar/gemmini](https://github.com/ucb-bar/gemmini), [ucb-bar/chipyard](https://github.com/ucb-bar/chipyard)
- [efabless/openlane2](https://github.com/efabless/openlane2)
- [mlcommons/tiny](https://github.com/mlcommons/tiny)
- [google/skywater-pdk](https://github.com/google/skywater-pdk)
- Karpathy LLM Wiki gist (2026-04) — `gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`
- qmd 하이브리드 검색 — `github.com/tobi/qmd`
- Apple Embedding Atlas — `github.com/apple/embedding-atlas`
- LanceDB — `lancedb.com`
- EvolVE — arXiv:2601.18067
- OpenRTLSet (UIUC 2026)
