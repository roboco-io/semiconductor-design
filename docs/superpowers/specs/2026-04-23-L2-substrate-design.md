# L2 Substrate — Derived Spec

| | |
|---|---|
| 작성일 | 2026-04-23 |
| 작성자 | Jung Do Hyun (serithemage@gmail.com) |
| 상태 | Draft — Codex 3-round review 전 |
| Parent spec | `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` |
| Scope | L2 **Substrate** layer only. L1 Process · L3 Content는 별도 파생 spec |
| Authority 범위 | Overview spec §3.2 v2 L2 contracts / §5.3 canonical decision table / §7.3 promotion gate는 본 spec이 재정의하지 않는다. 본 spec은 §3.2 v2 contract를 **구체 schema·산식·운영 rule로 확장(additive)** 한다. Breaking change 금지. |
| Derived from | Codex 3-round review (overview spec v2) Round 1–3의 deferred items 4건: per-node freshness · `confidence_score` 산식 · ranking calibration · `L2.memory.recall` query semantics |
| K2 ε 근거 | `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` — Ahmed 2026 (Clinical AI GOLD/SILVER/BRONZE tier) · Rasmussen 2025 Zep (validity period) · Xu 2025 A-MEM (memory evolution) · Verga 2024 PoLL (evaluator separation) · Landis-Koch 1977 (Cohen's κ cutoff) · Han 2025 Judge's Verdict (agreement-based judge capability) |
| Reviews | (pending Codex 3-round — §7 계획) |

---

## 1. 목적 (Why L2 Derived Spec)

L2 Substrate는 overview §3.2 v2에서 3개 interface(`L2.memory.recall`, `L2.skill_library.query`, `L2.lint.check`)로 고정됐다. 이 spec은 overview Codex review에서 "**overview scope 밖**"으로 분류되어 deferred된 4개 항목을 구체 schema·산식·운영 rule로 정의한다.

L2 단독은 **overview §5.3 publish/kill 판정에 기여하지 않는다**. L2는 L1이 산출한 artifact와 L3 agent 사이의 **재현 가능한 evidence index**이며, 품질 지표(κ, freshness decay, tier 분포)는 §5.1 H3 falsifier와 §5.2-1 freeze-before-experiment 대상이다.

### 1.1 deferred items (범위 고정)

| # | Item | Codex source | 본 spec 섹션 |
|---|---|---|---|
| D-1 | per-node freshness 모델 (graph rebuild timestamp vs per-document decay 의미 gap) | R1-1 | §4 |
| D-2 | `confidence_score` 산식 — Ahmed 2026 GOLD/SILVER/BRONZE 차용 여부 + 산식 정의 | R1-1 | §3 |
| D-3 | ranking calibration — graphify BFS/DFS budget과 tier 조합 weight | R1-1 | §5.3 |
| D-4 | `L2.memory.recall` query semantics — `{query_text, k?, budget_tokens?}`의 k/budget 실제 의미 | R1-1 | §5.1 |

### 1.2 비범위 (out of scope — 다른 spec이 결정)

- **§5.3 canonical decision table**의 publish/reframed/kill 판정 규칙: overview §5.3 고정. 본 spec은 evidence bundle format만 정의.
- **L1.run(spec) 산출물 schema**: L1 derived spec(§3)이 결정.
- **L3 agent 내부 reasoning trace format**: L3 파생 spec 영역.
- **graphify 내부 알고리즘**(BFS/DFS 구현, tier assignment heuristic): graphify upstream 영역. 본 spec은 **호출 계약**만 정의.

---

## 2. K2 ε 근거 요약

6개 critical-read 논문이 본 spec의 설계 템플릿이다. 각 논문의 **본 spec 반영 포인트**만 요약한다.

### 2.1 Ahmed et al. 2026 — Clinical AI Provenance Gap (§3 core template)

- **확정값**: GOLD=0.95, SILVER=0.85, BRONZE=0.70 — 임상 TKG의 3-tier fixed confidence.
- **tier 정의**: GOLD = cross-tier confirmed (≥2 independent sources 교차 검증). SILVER = multi-model consensus (≥2 model 동의). BRONZE = single-source (재검증 대기).
- **본 spec 반영**: §3 tier 재도입 schema의 직접 템플릿. graphify의 EXTRACTED/INFERRED/AMBIGUOUS와의 **매핑은 §3.2 TODO(human)** 에서 결정.

### 2.2 Rasmussen et al. 2025 — Zep (§4 freshness 직접 모델)

- **핵심 패턴**: 각 fact에 `valid_from` + `valid_to` 필드. 사실이 바뀌어도 기존 fact는 삭제하지 않고 `valid_to = now()` 기록. Non-lossy dynamic update.
- **본 spec 반영**: §4.1 `last_ingested` + `valid_from` + `valid_to`를 per-node 메타 필드로 채택. DMR 벤치 94.8% (MemGPT 93.4%) evidence는 `k=10 budget_tokens=8000` 기본값 선정의 외부 근거.

### 2.3 Xu et al. 2025 — A-MEM (§4 memory evolution 보조)

- **핵심 패턴**: Zettelkasten 기반. 새 note가 생기면 기존 note의 `timestamp/context/keywords/tags/embedding` 속성을 update(삭제하지 않고 "진화"). per-node freshness가 node-creation event가 아니라 **link-event** 기준으로 갱신됨.
- **본 spec 반영**: §4.2 "node `last_touched` ≠ `last_ingested`" 구분 — `last_ingested`는 원본 source 갱신, `last_touched`는 cross-link rewrite 포함.

### 2.4 Verga et al. 2024 — PoLL (§6 evaluator separation)

- **핵심 패턴**: 단일 GPT-4 judge 대신 서로 다른 패밀리(Anthropic / OpenAI / Google / Meta)의 작은 LLM 다수로 patron panel. 6개 데이터셋에서 단일 대형 judge 대비 우수 + 7× 저렴 + intra-model bias 감소.
- **본 spec 반영**: §6.2 evaluator separation 규칙 — H3 evaluator는 **≥3 서로 다른 model family** 필수. 본 프로젝트에서는 Claude (Anthropic) + Codex(GPT-5.x) + Gemini (Google) 혼합 패널이 최소 구성.

### 2.5 Landis & Koch 1977 — Kappa statistics cutoff (§6 acceptance gate)

- **확정값**: κ < 0.20 = poor · 0.21–0.40 = fair · 0.41–0.60 = moderate · **0.61–0.80 = substantial** · 0.81–1.00 = almost perfect.
- **본 spec 반영**: §6.1 Cohen's κ ≥ 0.6 (substantial agreement) 를 evaluator 간 합의 cutoff로 채택. overview §5.1 H3 falsifier와 동일 임계선.

### 2.6 Han et al. 2025 — Judge's Verdict (§6 보강)

- **핵심 패턴**: judge capability를 "정답과의 거리"가 아니라 **human과의 agreement 분포**로 측정. 단순 accuracy보다 Cohen's κ 기반 평가가 judge 품질을 더 정확히 대변.
- **본 spec 반영**: §6.3 judge 교체 시 "accuracy 유지" 기준이 아니라 **"κ 유지"** 기준으로 회귀 검증.

---

## 3. Tier 재도입 schema

### 3.1 두 축의 구분

Overview spec §3.2 v2 "의미 gap 공지"의 핵심: graphify **tier**(EXTRACTED/INFERRED/AMBIGUOUS)는 **추출 신뢰도** gate, Ahmed 2026 **confidence**(GOLD/SILVER/BRONZE)는 **증거 지지 강도(evidence support strength)** gate. 두 축은 **의미적으로 독립**이다.

| 축 | 답하는 질문 | 값 | 누가 정하나 |
|---|---|---|---|
| graphify `tier` | "이 노드·엣지가 source에서 **안정적으로 추출**됐는가?" | EXTRACTED · INFERRED · AMBIGUOUS | graphify extraction algorithm |
| `confidence` (본 spec 도입) | "이 노드가 표상하는 fact가 **얼마나 provenance-backed support**를 가지는가?" (즉 얼마나 많은 독립 source가 뒷받침하는가) | GOLD(0.95) · SILVER(0.85) · BRONZE(0.70) | L2 promotion gate (§3.3) |

**중요한 언어 구분 (Codex R2 반영)**: `confidence`는 **evidence support strength**이지 **claim validity** (주장이 실제로 참인지)가 아니다. Ahmed 2026의 "cross-tier confirmed"도 "사실로 확정됨"이 아니라 "여러 독립 source가 이 fact를 언급함"을 의미. Claim validity 판정은 overview §5.3 canonical decision table(H1/H3 pass count)이 전담하며 본 spec은 그 판단에 직접 입력되지 않는다(§3.3 #5).

두 축이 독립이기 때문에 이론상 9조합(3×3)이 가능하나, 실무에서는 tier가 admissibility(하한)을 결정하고 confidence는 그 위의 **지지 강도**를 부여하는 **계층 구조**로 운영한다(§3.2 매핑 규칙).

### 3.2 Tier ↔ Confidence 매핑 (L2 promotion gate 입력)

<!-- RESOLVED(codex, 2026-04-23): 대안 B 채택 (2차원, Ahmed 2026 정신 보존). Codex 판단: "A는 provenance quality와 claim strength를 한 축으로 collapse해 손실 크고, C는 G2 bootstrap 전에 κ-weighted review ops를 미리 도입하는 premature optimization. B는 기존 tier contract 보존하면서 defensible additive claim-strength layer 제공". 산식은 `source_count`를 `graphify-out/graph.json`의 엣지 → source_file reverse mapping으로 계산 (`scripts/compute_confidence.py` 신설 예정, 본 spec 별 후속 이슈). -->

**대안 A — 1:1 매핑** (단순, 구현 쉬움, 의미 축소)

```
graphify tier      confidence    의미
EXTRACTED       → GOLD  (0.95)   추출 안정 → 최고 강도 부여
INFERRED        → SILVER (0.85)  LLM 추론 → 중간 강도
AMBIGUOUS       → BRONZE (0.70)  수동 리뷰 대기 → 최저 강도
```

**단점**: "2개 source에서 확인된 INFERRED" 같은 상황이 표현 불가. Ahmed 2026의 "cross-tier confirmed" (GOLD의 핵심 조건)이 항상 EXTRACTED에 귀속되어 정보 손실.

**대안 B — 2차원 (Ahmed 2026 정신 그대로)**

```
tier × source_count      confidence
EXTRACTED ∧ ≥2 source   → GOLD   (cross-tier confirmed)
EXTRACTED ∧  1 source   → SILVER (single-source structural match)
INFERRED  ∧ ≥2 source   → SILVER (multi-model consensus)
INFERRED  ∧  1 source   → BRONZE (single-source inference)
AMBIGUOUS ∧   *         → AMBIGUOUS (promotion gate 차단, confidence 부여 안 함)
```

`source_count`는 graphify `graph.json`의 엣지 → 원본 파일 reverse mapping으로 계산 가능(`graphify path "node" "*"` 결과의 unique source_file 수).

**단점**: graphify가 현재 node-level source_count를 직접 노출하지 않음 → `scripts/compute_confidence.py` 보조 계산 필요. AMBIGUOUS는 confidence 미부여가 되어 recall output schema에 `confidence: Optional[float]` 필요.

**대안 C — Orthogonal (두 축 독립 유지)**

```
tier와 confidence를 완전히 독립 메타데이터로 저장. promotion gate는 두 조건 AND.
  - tier ∈ {EXTRACTED, INFERRED} (overview §7.3 고정)
  - confidence ≥ SILVER (본 spec 추가 gate)

AMBIGUOUS 노드도 human review 후 "SILVER로 수동 승격" 가능 — graphify tier 재분류 없이.
```

`confidence`는 별도 산식(예: κ-weighted sum of review ratings)으로 계산. graphify extraction과 해지 · tier 갱신 cadence가 분리되어 ops 부담 증가, 대신 표현력 최대.

**단점**: `confidence` 산식을 별도 정의해야 하며 κ 측정 cost 발생. ops cadence가 graphify rebuild와 어긋나 staleness 관리 복잡.

---

**Chosen: Alternative B (2차원)**. Codex judgment reference: `docs/superpowers/specs/2026-04-23-L2-substrate-codex-review.md` §Design Judgment.

매핑 규칙 (canonical):

| graphify tier | source_count | → confidence | confidence_score |
|---|---|---|---|
| EXTRACTED | ≥ 2 | GOLD | 0.95 |
| EXTRACTED | 1 | SILVER | 0.85 |
| INFERRED | ≥ 2 | SILVER | 0.85 |
| INFERRED | 1 | BRONZE | 0.70 |
| AMBIGUOUS | * | *(미부여)* | null |

`source_count` 계산: `graphify-out/graph.json`의 특정 `node_id` 엣지를 BFS로 순회하여 도달 가능한 원본 `source_file` unique 개수. 동일 파일의 여러 chunk는 1회 카운트 (unique source_file identity 기준). 구현은 `scripts/compute_confidence.py` — 별도 후속 이슈.

**`EXTRACTED ∧ 1 source → SILVER` 전제 (Codex R2 명시)**: 이 매핑은 chunk들이 **auditable source identity를 보유하되** (source_file metadata가 각 chunk에 결측 없이 붙어 있어야 함) unique source_count가 1인 경우에만 적용된다. source_file identity 자체가 결측된 chunk만 있는 경우는 §3.3 #4에서 promotion gate가 차단한다.

AMBIGUOUS 노드에는 **confidence를 부여하지 않는다** (promotion gate에서 이미 차단되므로 score ranking에 기여할 필요 없음).

### 3.3 Promotion gate (overview §7.3 확장)

Overview §7.3 "Finding → canonical wiki page"는 `tier ∈ {EXTRACTED, INFERRED}`를 이미 요구. 본 spec은 alternative B 채택(§3.2)에 따라 다음 **5개 차단 기준**을 `L2.promotion_gate.check(node)` 내부에 추가한다 (Codex design judgment 직접 반영):

1. **`confidence` 재현성 불가 시 차단**: `source_count`가 bundle metadata (`graphify-out/graph.json` + 해당 노드의 엣지 정합) 만으로 재계산되지 않으면 promotion fail. 휴먼이 수동으로 수치를 입력하는 경로 금지.
2. **GOLD는 cross-source 필수**: `confidence = GOLD` 인데 `source_count = 1` 이면 즉시 차단. Ahmed 2026 "cross-tier confirmed" 정의를 강제하는 schema-level rule.
3. **AMBIGUOUS에 confidence 부여 금지**: graphify가 AMBIGUOUS로 분류한 노드에 promotion-confidence 값이 attached되면 fail. §3.2 매핑 표의 마지막 row를 schema-enforceable하게 강제.
4. **source_count / source identity 누락 시 차단**: `node.source_files[]`가 empty이거나 chunk들에 source_file metadata 자체가 결측되어 unique source identity를 산출할 수 없는 경우 fail. 동일 파일의 여러 chunk는 unique source_count=1로 산출되어 본 조건에서는 정상이다(SILVER 매핑 대상). 감사 불가능한 claim 차단.
5. **`confidence` 사용 범위 — ranking only, canonical decision forbidden**: 본 spec의 `confidence` / `confidence_score` 필드는 **L2 내부 evidence/promotion ranking + recall output ordering 전용**. overview §5.3 canonical decision table의 input schema(H1 pass count · H3 evaluator 집계 결과 · L1 sign-off boolean)에는 **어떤 우회 경로로도 입력되지 않는다**. 구체 강제:
   - 본 spec이 정의하는 어떤 interface(`L2.memory.recall`, `L2.skill_library.query`, `L2.lint.check`, `L2.promotion_gate.check`)도 §5.3 decision input에 `confidence*` 필드를 노출하지 않는다.
   - §5.3 decision agent 구현 시 input parser는 `confidence`·`confidence_score` 필드를 **명시적으로 drop**해야 한다 (본 spec 구현 이슈에서 assertion test로 회귀 방지).
   - §5.3 rubric 문구에 "confidence"·"support strength"·"GOLD/SILVER/BRONZE" 어느 것도 등장 금지 — §5.3 는 오로지 H1/H3 pass count·evaluator agreement·FM rubric만 언급.

위 5개는 overview §7.3 기존 조건(`tier ∈ {EXTRACTED, INFERRED}` + `L2.lint.check()` 경고 0 + evidence run ≥ 3건 + `derived_from_hypothesis` 연결)에 AND로 결합된다.

본 spec은 **publish/reframed/kill 기준을 선언하지 않는다** — overview §5.3 Canonical Decision Table이 유일. 위 차단 기준 #5가 이 방어선을 schema-level로 강화.

---

## 4. Freshness 모델 (D-1 해소)

(§3.2 확정 후 작성 — §4는 tier 매핑에 의존하지 않는 독립 설계라 §3 Learn by Doing 대기 없이 병렬 작성 가능)

### 4.1 Per-node metadata 필드

Zep(§2.2) validity period + A-MEM(§2.3) memory evolution을 합쳐 각 node에 다음 3개 timestamp를 유지한다:

| 필드 | 의미 | 갱신 trigger |
|---|---|---|
| `last_ingested` | 원본 source 파일의 `/graphify --update` 처리 시각 | source `.md` 파일 수정 + `/graphify --update` |
| `valid_from` | 해당 fact가 "true로 선언된" 시각 (default = `last_ingested`) | 신규 노드 생성 시 `last_ingested`와 동일, 수동 override 가능 |
| `valid_to` | 해당 fact가 무효화된 시각 (`null` = still valid) | 상위 fact에 의해 invalidate되거나 human review에서 명시적 expire 선언 |

graphify 내부는 이 3개 필드를 **node attribute로 저장**(extra metadata)하고, `L2.memory.recall` 호출 시 output에 포함한다(§5.2 schema).

### 4.2 Decay threshold

- **30일**: recall output의 `age_days` 파생 필드가 ≥ 30이면 소비자(L1/L3)가 "aging" 으로 해석 가능. 본 spec은 flag 필드를 추가하지 않음 (클라이언트 책임).
- **90일**: `L2.lint.check()` output schema는 건드리지 않음 — parent §3.2 v2의 `{ok, errors, metrics}` 3-field 구조 유지. 90일 초과 노드는 **별도 로그/metric**(CloudWatch custom metric 또는 stderr warning)으로 기록. `L2.lint.check()` fail 조건은 overview §3.2 v2 고정값(orphan=0, dangling=0, AMBIGUOUS≤0.3)만 유효.
- **180일** (hard limit): `/graphify --update`가 기계적으로 ingest 재수행 큐에 올림 (운영 cadence — Issue #4 SOP 영역과 경계). 여전히 `L2.lint.check()` 계약 외.

임계값 근거: Zep DMR 벤치 테스트 실험 기간이 ~30일, A-MEM Zettelkasten re-link cadence가 ~90일. 본 프로젝트는 EDA 도메인 paper 갱신 속도가 평균 3-6개월 (K2 ε 수집 간격)이라 180일 hard limit이 자연 cycle과 일치.

### 4.3 Graph rebuild timestamp (per-graph 단일값)

Overview §5.1 H3 system metrics: "graph rebuild 간 god-node top-N 변화율 + AMBIGUOUS 비율 trajectory (각각 독립 signal)". 본 spec §4.1의 per-node `last_ingested`는 **per-graph rebuild timestamp의 세분화**이며, 둘은 다음과 같이 공존:

- **per-graph** `graphify-out/manifest.json`의 `build_timestamp` — full rebuild 시각. `L2.memory.recall` `StaleGraph` 오류 판정 기준.
- **per-node** `last_ingested` — 개별 source의 마지막 처리 시각. per-graph보다 과거일 수 있음 (incremental update 시 미변경 source).

역할 분리: per-graph는 "graph 전체의 freshness 관문", per-node는 "특정 결과의 freshness 플래그".

---

## 5. API 구체화 (D-3, D-4 해소)

(§5 본문은 §3.2 Learn by Doing 완료 후 §4 참조 추가하여 확정)

### 5.1 `L2.memory.recall(query)` query semantics

Overview §3.2 v2 input signature: `{query_text, k?, budget_tokens?}`. 본 spec이 각 field의 **실제 의미**를 고정:

| Field | 타입 | 의미 | 기본값 | 제약 |
|---|---|---|---|---|
| `query_text` | str | Natural-language query. graphify 내부에서 embedding + tier filter로 BFS 시드 추출 | — | ≤ 500 chars. 초과 시 `QueryTooLong` |
| `k` | int | Return할 **top-k 노드 수** | 10 | 1 ≤ k ≤ 50. 초과 시 `KOutOfRange`. Zep §2.2 benchmark 결과가 k=10에서 plateau. |
| `budget_tokens` | int | graphify BFS/DFS가 **collecting 가능한 snippet 총 토큰 예산** (hop 수가 아니라 **payload size cap**) | 8000 | 500 ≤ budget ≤ 32000. 초과 시 `BudgetOutOfRange`. Claude 200k context의 4% 수준으로 per-recall 부담 제한 |

정밀한 해석: `k`는 ranking 끝판의 cut-off, `budget_tokens`는 collection 단계의 payload cap. `k=10, budget=8000`은 "노드 10개에 평균 800 tokens snippet" 기대값.

### 5.2 Recall output schema

Overview §3.2 v2 output: `[{node_id, label, source_file, tier, snippet?}]`. Alternative B 채택(§3.2)에 따라 **additive-only 확장**:

```
# Min required (overview §3.2 v2 parent contract 그대로):
#   node_id: str
#   label: str
#   source_file: str
#   tier: Literal["EXTRACTED", "INFERRED", "AMBIGUOUS"]
#   snippet: Optional[str] = None

# 본 spec이 additive 확장하는 신규 필드 (모두 Optional, default None):
{
  # === parent contract ===
  node_id: str,
  label: str,
  source_file: str,
  tier: Literal["EXTRACTED", "INFERRED", "AMBIGUOUS"],
  snippet: Optional[str] = None,

  # === ADDED — source provenance (§3.2 alternative B) ===
  source_files: Optional[list[str]] = None,                    # 모든 소스 파일
  source_count: Optional[int] = None,                          # len(unique(source_files))

  # === ADDED — claim strength (§3.2 alternative B) ===
  confidence: Optional[Literal["GOLD", "SILVER", "BRONZE"]] = None,   # AMBIGUOUS·미계산 → None
  confidence_score: Optional[float] = None,                          # 0.95 / 0.85 / 0.70 / None

  # === ADDED — freshness (§4 Zep + A-MEM 모델) ===
  last_ingested: Optional[str] = None,                         # ISO 8601
  valid_from: Optional[str] = None,
  valid_to: Optional[str] = None,
  age_days: Optional[int] = None,                              # now - last_ingested (파생 필드)
}
```

**Backward compatibility**: 신규 9개 필드 모두 `Optional[T] = None`. Parent §3.2 v2 min-required (node_id, label, source_file, tier, optional snippet)는 동일하게 유지된다. 소비자(L1/L3)가 본 spec 인지 전까지는 기존 5개 필드만 사용해도 호환이며, producer 측에서도 신규 필드 미제공 시 default None이 계약상 합법.

### 5.3 Ranking calibration (D-3 해소)

`k` 개 최종 결과의 ranking은 다음 weighted score로 결정:

```
score(node) = α · tier_weight(node.tier)
            + β · confidence_weight(node.confidence)      # §3.2 매핑에 따라
            + γ · freshness_weight(node.age_days)
            + δ · graph_centrality(node)                   # graphify god-node score
```

기본 weight (§5.2-1 freeze-before-experiment 대상):

- α = 0.30, β = 0.30, γ = 0.20, δ = 0.20 — 합 1.0
- `tier_weight`: EXTRACTED=1.0, INFERRED=0.7, AMBIGUOUS=0.0 — ranking에서 최하위를 부여하되 **schema상 반환은 허용** (AMBIGUOUS 노드 자체는 parent §3.2 v2 계약에 금지되지 않으므로 recall output에 포함될 수 있음. promotion gate §3.3은 별도 차단)
- `confidence_weight`: §3.2 alternative B 확정값 — GOLD=0.95 / SILVER=0.85 / BRONZE=0.70 / AMBIGUOUS=0.0
- `freshness_weight`: age≤30→1.0, age≤90→0.8, age≤180→0.6, age>180→0.3
- `graph_centrality`: `graphify-out/GRAPH_REPORT.md`의 god-node rank를 0–1로 정규화

변경 cadence: weight 4개 값은 `docs/superpowers/specs/2026-04-23-L2-substrate-design.md`의 본 spec 재승인 사항. 실험 중 변경 금지(§5.2-1 freeze).

---

## 6. Acceptance gate (§6.1 κ cutoff + §6.2 evaluator separation)

### 6.1 Cohen's κ ≥ 0.6 (Landis-Koch 1977 substantial)

- **적용 대상**: H3 evaluator 간 합의도 (overview §5.1 H3 falsifier).
- **측정 주기**: §5.1 H3 iteration N 종료 시마다 재측정. iteration 내 중간 측정 금지 (peeking bias).
- **Fail 시 반응**: κ < 0.6 → H3 iteration N 무효, 다음 iteration에서 evaluator rubric 재작성 후 재개.

### 6.2 Evaluator separation — N≥5 evaluators across ≥ 3 model families

Overview §4.3 / §5.3 / §5.4에 고정된 H3 평가자 수 **N ≥ 5**는 본 spec이 절대 하향하지 않는다. Verga 2024 PoLL(§2.4)의 "cross-family" 원칙은 그 **위에** 추가로 적용되는 다양성 규칙이다:

- **평가자 수**: 최소 5명. Human primary evaluator가 기본(overview §5.3 "human-reviewed claim").
- **Model family 다양성**: 5명 중 LLM 평가자가 포함될 경우 **≥ 3 model family**에 분산. 본 프로젝트 권장 패밀리:
  - **Anthropic**: Claude Opus 4.x 또는 Sonnet 4.x
  - **OpenAI / Codex**: GPT-5.x 계열
  - **Google**: Gemini 2.x 계열
- **Aggregation 방식**: 다수결(voting) 또는 κ-weighted aggregate 중 하나를 H3 iteration 개시 전 선택(§5.2-1 freeze). 두 방식 혼용 금지 (iteration 내에서).

**요약**: "5 evaluators selected across at least 3 families, with humans as primary evaluators." 본 spec의 §6.2는 overview의 N≥5 floor에 cross-family 조건을 **additive**로 얹는 rule이며, N을 건드리지 않는다.

### 6.3 Freeze-before-experiment + 변경 권한

Overview §5.2-1 원칙 준수 + 본 spec 확장 (freeze 대상):

- **§3.2 tier ↔ confidence 매핑 규칙** (§3.2)
- **§4.2 decay threshold** (30 / 90 / 180 days)
- **§5.1 `k`, `budget_tokens` 기본값** (10, 8000)
- **§5.3 ranking calibration weight** (α/β/γ/δ, tier_weight, confidence_weight, freshness_weight)
- **§6.1 κ cutoff** (0.6) 및 **§6.2 evaluator panel 구성**

→ H3 iteration 개시 전 git tag로 freeze. 중간 변경 시 iteration 무효 처리.

**변경 권한 (L2 spec-owner 전속)**: 위 freeze 대상 값의 변경은 **본 L2 derived spec의 spec-owner만이** 본 파일을 직접 수정하고 Codex 3-round review를 재통과시켜야 한다. L3 agent가 iteration 중 ranking weight · 매핑 규칙 · decay threshold · κ cutoff를 동적으로 변경하는 것은 **freeze 규칙 위반**이며, 그 iteration은 §5.3 decision 판정에서 자동 탈락 처리된다. L2 runtime (`L2.memory.recall`, `L2.skill_library.query` 구현체)는 freeze된 값을 **read-only**로 참조만 하며 mutation 경로를 노출하지 않아야 한다 — 이 rule은 본 spec 구현 이슈에서 assertion test로 인코딩.

### 6.4 L1 sign-off 역할 분리

Overview §5.3 "evidence origin = god-node + human-reviewed claim + L1 sign-off report". 본 spec의 명시:

- **L1 sign-off**: `.rpt` artifact가 `make kg-f-all`을 통과했음을 boolean assertion 하는 행위. "주장 타당성 판정 아님".
- **L3 evaluator**: H3 falsifier의 실제 판정자. L1 sign-off 통과한 `.rpt`를 input으로 받아 FM1~FM4 rubric으로 채점.
- **본 spec가 강제**: L1 sign-off agent와 L3 evaluator agent는 **동일 세션·동일 model instance에서 실행 금지** (role conflation 방지). 별도 subprocess 또는 별도 `codex exec` 호출이어야 함.

---

## 7. Codex 3-round review plan

`docs/superpowers/specs/2026-04-22-graphify-adoption-codex-review.md` 선례 따라 3-round 순차 실행. 각 round `< /dev/null` redirect 필수 (Codex CLI TTY hang 회피).

### 7.1 Round 1 — 구조/일관성 (overview §3.2 v2 호환성)

- 검증 대상: 본 spec §3-§5가 overview §3.2 v2 L2 contract를 **확장하는지**(additive) vs **수정하는지**(breaking)
- 예상 findings: `confidence` 필드 추가가 `L2.memory.recall` output `[{node_id, label, source_file, tier, snippet?}]` 계약을 breaking하지 않는가? (optional 필드 추가는 additive가 맞음)

### 7.2 Round 2 — 의미 gap 충분성 (tier ↔ confidence 축 분리)

- 검증 대상: §3.1의 두 축 구분이 overview §3.2 v2 "tier는 admissibility gate, NOT validity" 단서와 consistent한가.
- 예상 findings: `confidence`가 claim validity gate인 것처럼 해석될 여지 점검. Ahmed 2026의 "cross-tier confirmed" 표현이 tier와 confidence 중 어느 축에 귀속되는지 문구 애매성.

### 7.3 Round 3 — H3 falsifier 훼손 여부

- 검증 대상: §6.1 κ ≥ 0.6 + §6.2 evaluator separation + §6.4 role conflation 금지가 overview §5.1 H3 falsifier를 **약화시키지 않는지**.
- 예상 findings: `confidence` 점수가 §5.3 publish/kill 판정에 우회 입력되지 않는가? (본 spec은 §3.3에서 "publish/kill 기준을 선언하지 않는다"고 명시했으나 확인 필요)

### 7.4 Acceptance

- 3 rounds 모두 `ok` 또는 `needs-revision` (follow-up inline fix 가능): → 본 spec commit.
- ≥ 1 round `fail` after 3 iterations: → spec 재작성, L2 파생 spec v2로 재개시.

Codex review log는 `docs/superpowers/specs/2026-04-23-L2-substrate-codex-review.md`에 동일 format으로 기록.

---

## 8. 구현 이정표 (reference — 코드 변경은 본 spec 승인 후 별도 이슈)

본 spec은 **문서**이다. 코드 변경은 별도 이슈(예: "L2 derived spec 구현 Phase 1 — recall output schema 확장")로 진행.

예상 후속 issue 3건 (본 spec 승인 후 생성):

1. **schema 반영**: `L2.memory.recall` output 타입 정의 파일 신설(Pydantic v2 모델), graphify query wrapper 작성
2. **confidence 산식 구현**: §3.2 선택 매핑의 실제 코드 (alternatives 중 어느 쪽인지에 따라 `scripts/compute_confidence.py` 신설 또는 graphify attribute 확장)
3. **freshness metadata 주입**: `/graphify --update` hook으로 `last_ingested` / `valid_from` / `valid_to` 필드 ingest
