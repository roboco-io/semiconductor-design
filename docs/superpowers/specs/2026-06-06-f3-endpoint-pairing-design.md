# F3 — Endpoint 단위 다설계 Pairing 설계

> status: approved (2026-06-06, brainstorming) · 후속: 파서 수정 writing-plans
> 근거: `experiments/real-gcd/FINDINGS.md` (실제 gcd 검증의 F3 falsification)
> 영향: [`issues/002`](../../../issues/002-feature-set-composition.md) (OD-2, 소폭) · [`issues/003`](../../../issues/003-dataset-scale-label-count.md) (OD-3, 재설계) · [`issues/006`](../../../issues/006-eda-flow-execution-infra.md) (Fargate 병렬 정합)
> 불변: OD-1 = per-path timing slack 회귀 유지. `prepare.py` frozen (NFR-2).

## 1. 문제 (F3)

실제 gcd 검증에서 post-synth STA와 post-route(place) STA의 **critical path 집합이 disjoint** — resizer/optimizer가 worst path를 stage 간 재편. `join_paths`의 (startpoint, endpoint, path_group, path_type) 매칭이 **0 rows**. "같은 path를 두 시점에 관측"한다는 OD-2/OD-3 가정이 약함.

원인: **path(게이트 체인)는 stage 간 정체성이 불안정**하다. optimizer가 게이트·버퍼를 갈아치우면 path가 달라진다.

## 2. 핵심 통찰

**endpoint는 stage 간 안정적**이다 — register D핀 / output port는 netlist가 고정하는 sequential 원소라 합성→배치→라우팅 내내 존재한다. 따라서 샘플의 정체성을 path가 아니라 **endpoint**에 두면 두-시점 join이 보장된다. "endpoint에 도착하는 worst path"가 샘플 단위.

## 3. 설계

### 3.1 샘플 정의
- **샘플 = (design_id, endpoint)**. endpoint = register D핀 또는 output port.
- 각 endpoint의 **worst max-delay path 1개** = 1 회귀 샘플.
- **join 키 = (design_id, endpoint)**, `path_type = max`(setup) 필터.

### 3.2 feature / label (FR-1, OD-1 유지)
- **feature (post-synth STA)**: OD-2 v1 8개(`num_stages, synth_slack_ns, synth_arrival_ns, max_stage_delay_ns, mean_stage_delay_ns, startpoint_is_ff, endpoint_is_ff, path_group`)를 해당 endpoint의 **worst-to-EP path**에 대해 계산.
- **label (post-route STA)**: 같은 endpoint의 worst slack(ns). val 지표 = **MAE(ns)**.

### 3.3 스케일 (OD-3 재설계)
- N = **Σ(설계별 #endpoint)**. 단설계의 path 수천 대신 **다설계 × endpoint**로 규모 확보 (gcd → ibex → aes …). CircuitNet의 다설계 스케일과 동일 방향.
- "flow 1회"(FR-1)를 **다설계 batch**로 명시 완화.
- train/val 분할 = **design_id 단위 group-disjoint** (`group_key = design_id`). 같은 설계가 양쪽에 들어가지 않음.
- 다설계 실행은 [`issues/006`](../../../issues/006-eda-flow-execution-infra.md) **Fargate 병렬**이 값싸게 만든다 (F3 + OD-3 + 006 정합).

### 3.4 report 생성 (flow-side, frozen 파서 아님)
- **minimal `report_checks`** (no `-fields`) → `Delay Time` 2컬럼. endpoint별 worst path, 두 stage(post-synth, post-route).
- 정확한 OpenSTA 메커니즘(예: endpoint별 `-to`, 또는 endpoint-limited 단일 report)은 **flow 구현 detail** — 파서는 무관(텍스트만 소비).

### 3.5 frozen 파서 수정 (prepare.py, 별도 writing-plans)
- **F1**: 두-줄 `Startpoint:`/`Endpoint:` 헤더 — clock 주석이 둘째 줄로 wrap되는 실제 포맷 처리. `startpoint_is_ff`/`endpoint_is_ff`가 둘째 줄의 "flip-flop"을 본다.
- **stage 정규식**: Delay/Time 2컬럼 유지 (F2 미적용 — minimal 포맷).
- **join_paths 재키**: (sp,ep,group,type) → **(design_id, endpoint)** + `path_type=max` 필터 + 중복 endpoint 시 worst-slack 유지.
- **feature_set 불변** (OD-2 v1).

### 3.6 엣지 케이스
- retiming으로 endpoint 소멸/신설 → unmatched drop + 로그.
- positive-slack endpoint → 유효 샘플(회귀).
- unconstrained(클럭 미지정) endpoint → 제외.

### 3.7 테스트
- 파서 fixture를 **실제 두-줄-헤더 minimal 포맷**으로 교체(`experiments/real-gcd` 기반, minimal 재생성). endpoint-keyed join 테스트 추가(두 stage가 disjoint path여도 endpoint 공통이면 join됨을 검증).

## 4. OD 영향

| OD | 변화 |
|---|---|
| OD-1 | **불변** — per-path timing slack 회귀, val=MAE. (per-endpoint worst path는 여전히 per-path slack) |
| OD-2 | **소폭** — feature_set v1 8개 그대로, 계산 대상이 "critical path" → "endpoint별 worst-to-EP path"로 명시. |
| OD-3 | **재설계** — 샘플 단위 = (design, endpoint). 규모 = 다설계 batch. grouping = design_id. "flow 1회" → 다설계 batch 완화. |
| OD-6(006) | **정합** — Fargate 병렬이 다설계 실행을 값싸게 함. |

## 5. 비목표 (YAGNI)
- rich `-fields` feature(slew/cap/fanout)는 OD-2 v2로 연기(현 결정: minimal).
- near-worst k-path 다중 샘플(approach 2)은 path 정체성 불안정 재발로 기각.
- (sp,ep) 쌍 강제 enumerate(approach 3)는 report 생성 비용으로 기각.
