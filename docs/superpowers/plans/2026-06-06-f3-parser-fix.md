# F3 Parser Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the frozen `prepare.py` parser/join to handle REAL OpenSTA output and the F3 endpoint-pairing design — two-line `Startpoint:`/`Endpoint:` headers (F1) and endpoint-keyed join across stages (F3).

**Architecture:** Three surgical changes to existing pure functions: (1) `report.py` `_is_ff` spans the two-line header; (2) `transform.py` `join_paths` re-keys from `(startpoint, endpoint, group, type)` to **endpoint** (max-path, worst-per-endpoint); (3) `dataset.py` `group_key` becomes `design_id`. Fixtures gain two-line headers for realism. `parse_report`/`PathRecord`/`FEATURE_NAMES` unchanged.

**Tech Stack:** Python 3.12, uv, stdlib `re`, pytest (`tmp_path`, fixtures + inline strings), ruff (100 char, py312).

**Spec:** `docs/superpowers/specs/2026-06-06-f3-endpoint-pairing-design.md`. **Evidence:** `experiments/real-gcd/FINDINGS.md` (F1/F3 falsification). OD-1 unchanged; OD-2 features unchanged; OD-3 grouping = `design_id`.

---

## Files

| File | Change |
|---|---|
| `src/prepare_lib/report.py` | `_is_ff` → two-line clause match (F1). Nothing else. |
| `src/prepare_lib/transform.py` | `join_paths` → endpoint-keyed + max filter + worst-per-endpoint. Remove `group_key` helper. |
| `src/prepare_lib/dataset.py` | `group_key` import removed; `r["group_key"] = design_id`. |
| `tests/prepare/test_report.py` | + two-line header tests. |
| `tests/prepare/test_transform.py` | join tests → endpoint semantics; + disjoint-endpoint + worst-per-endpoint; remove group_key test. |
| `tests/prepare/test_dataset.py` | `group_key` assertion `gcd:clk` → `gcd`. |
| `tests/prepare/fixtures/{synth,route}.rpt` | headers → two-line (no numeric change). |

**Frozen-contract note:** the dataset row now keys on endpoint and `group_key=design_id`; row fields stay `{endpoint, startpoint, <8 features incl path_group>, post_route_slack_ns, group_key}`. No `train.py` consumes it yet, so evolving the contract now is safe and intended.

---

### Task 1: F1 — two-line `Startpoint:`/`Endpoint:` header (`report.py`)

**Files:**
- Modify: `src/prepare_lib/report.py:44-47` (`_is_ff`)
- Test: `tests/prepare/test_report.py`

- [ ] **Step 1: Write the failing tests** (append to `tests/prepare/test_report.py`)

```python
def test_two_line_startpoint_header_is_ff():
    block = (
        "Startpoint: dpath.b_reg.out[2]$_DFFE_PP_\n"
        "            (rising edge-triggered flip-flop clocked by core_clock)\n"
        "Endpoint: dpath.b_reg.out[0]$_DFFE_PP_\n"
        "          (rising edge-triggered flip-flop clocked by core_clock)\n"
        "Path Group: core_clock\nPath Type: max\n"
        "   0.38    0.38 v dpath.b_reg.out[2]$_DFFE_PP_/Q (sky130_fd_sc_hd__edfxtp_1)\n"
        "           0.38   data arrival time\n           0.55   slack (MET)"
    )
    p = parse_report(block)[0]
    assert p.startpoint == "dpath.b_reg.out[2]$_DFFE_PP_"
    assert p.endpoint == "dpath.b_reg.out[0]$_DFFE_PP_"
    assert p.path_group == "core_clock"
    assert p.startpoint_is_ff is True
    assert p.endpoint_is_ff is True


def test_two_line_input_port_not_ff():
    block = (
        "Startpoint: io_in[3]\n"
        "            (input port clocked by core_clock)\n"
        "Endpoint: dpath.x_reg$_DFFE_PP_\n"
        "          (rising edge-triggered flip-flop clocked by core_clock)\n"
        "Path Group: core_clock\nPath Type: max\n"
        "   0.20    0.20 ^ dpath.x_reg$_DFFE_PP_/D (sky130_fd_sc_hd__edfxtp_1)\n"
        "           0.20   data arrival time\n           0.30   slack (MET)"
    )
    p = parse_report(block)[0]
    assert p.startpoint == "io_in[3]"
    assert p.startpoint_is_ff is False
    assert p.endpoint_is_ff is True
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/prepare/test_report.py::test_two_line_startpoint_header_is_ff -v`
Expected: FAIL — `startpoint_is_ff` is False (single-line `_is_ff` misses the wrapped clock line).

- [ ] **Step 3: Replace `_is_ff` in `src/prepare_lib/report.py`**

```python
def _is_ff(block: str, label: str) -> bool:
    # clock 주석은 긴 instance 이름에서 둘째 줄로 wrap된다 (실제 OpenSTA 포맷, F1).
    # label 줄부터 다음 헤더 직전까지의 clause를 떠서 "flip-flop"을 본다 — 단/두-줄 모두 처리.
    m = re.search(
        rf"^{label}:(.*?)(?=^Startpoint:|^Endpoint:|^Path Group:)",
        block,
        re.MULTILINE | re.DOTALL,
    )
    clause = m.group(1) if m else ""
    return "flip-flop" in clause
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/prepare/test_report.py -v`
Expected: PASS (existing single-line tests + 2 new two-line tests).

- [ ] **Step 5: Commit**

```bash
git add src/prepare_lib/report.py tests/prepare/test_report.py
git commit -m "fix(prepare): F1 두-줄 Startpoint/Endpoint 헤더 파싱 (실제 OpenSTA 포맷)"
```

---

### Task 2: F3 — endpoint-keyed join (`transform.py`)

**Files:**
- Modify: `src/prepare_lib/transform.py:44-64` (`join_paths`)
- Test: `tests/prepare/test_transform.py`

- [ ] **Step 1: Write the new/updated tests**

In `tests/prepare/test_transform.py`, REPLACE `test_join_keeps_only_matched_paths` and `test_join_row_has_features_and_label` with the endpoint-semantics versions below, and ADD the two new tests:

```python
def test_join_matches_on_endpoint_not_path():
    # 기존 fixture: 공통 endpoint = _1_, _4_ (inp_a→_5_, _9_→_10_ 는 한쪽만)
    rows = join_paths(_synth(), _route())
    assert {r["endpoint"] for r in rows} == {"_1_", "_4_"}


def test_join_row_has_features_and_label():
    rows = join_paths(_synth(), _route())
    row = next(r for r in rows if r["endpoint"] == "_1_")
    assert row["startpoint"] == "_0_"  # synth-stage worst path's startpoint
    assert row["num_stages"] == 4
    assert row["synth_slack_ns"] == 1.28
    assert row["post_route_slack_ns"] == 0.85
    assert row["path_group"] == "clk"


def test_join_matches_on_endpoint_despite_disjoint_paths():
    # F3 핵심: synth worst path(via a)와 route worst path(via x)의 내부 게이트가 달라도
    # endpoint b가 공통이면 join된다. (sp,ep) 키였으면 0 rows였을 시나리오.
    synth = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.40    0.40 ^ a/Q (sky130_fd_sc_hd__dfxtp_1)\n"
        "   0.30    0.70 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.70   data arrival time\n           0.30   slack (MET)"
    )
    route = (
        "Startpoint: x (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.55    0.55 ^ x/Q (sky130_fd_sc_hd__dfxtp_1)\n"
        "   0.40    0.95 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.95   data arrival time\n           0.05   slack (MET)"
    )
    rows = join_paths(parse_report(synth), parse_report(route))
    assert len(rows) == 1
    assert rows[0]["endpoint"] == "b"
    assert rows[0]["startpoint"] == "a"
    assert rows[0]["post_route_slack_ns"] == 0.05


def test_join_keeps_worst_slack_per_endpoint():
    # endpoint b로 가는 synth max path 2개 중 worst(min slack=0.10)가 feature가 된다.
    synth = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.30    0.30 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.30   data arrival time\n           0.50   slack (MET)\n\n"
        "Startpoint: c (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.60    0.60 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.60   data arrival time\n           0.10   slack (MET)"
    )
    route = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.30    0.30 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.30   data arrival time\n           0.20   slack (MET)"
    )
    rows = join_paths(parse_report(synth), parse_report(route))
    assert len(rows) == 1
    assert rows[0]["synth_slack_ns"] == 0.10
```

Keep `test_join_drops_path_type_mismatch` as-is (synth=max only, route=min only → route has no max endpoint → 0 rows; still valid under the new max filter).

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/prepare/test_transform.py::test_join_matches_on_endpoint_despite_disjoint_paths -v`
Expected: FAIL — current `(startpoint,endpoint,group,type)` key gives 0 rows for disjoint startpoints.

- [ ] **Step 3: Replace `join_paths` in `src/prepare_lib/transform.py`**

Replace the whole `join_paths` function (lines 44-64) with:

```python
def _worst_max_by_endpoint(paths: list[PathRecord]) -> dict[str, PathRecord]:
    # endpoint는 stage 간 안정적 (F3). max(setup) path만, endpoint당 worst(min slack)를 남긴다.
    best: dict[str, PathRecord] = {}
    for p in paths:
        if p.path_type != "max":
            continue
        cur = best.get(p.endpoint)
        if cur is None or p.slack_ns < cur.slack_ns:
            best[p.endpoint] = p
    return best


def join_paths(synth: list[PathRecord], route: list[PathRecord]) -> list[dict]:
    # endpoint 단위 join (F3): path 정체성은 stage 간 불안정하므로 안정점인 endpoint로 묶는다.
    synth_by_ep = _worst_max_by_endpoint(synth)
    route_by_ep = _worst_max_by_endpoint(route)
    rows: list[dict] = []
    for ep, sp in synth_by_ep.items():
        rp = route_by_ep.get(ep)
        if rp is None:
            continue  # route 시점에 없는 endpoint (retiming 등) drop
        rows.append(
            {
                "endpoint": ep,
                "startpoint": sp.startpoint,
                # path_group은 extract_features가 채운다 (** 언팩).
                **extract_features(sp),
                LABEL_NAME: extract_label(rp),
            }
        )
    return rows
```

Also DELETE the now-unused `group_key` function (lines 40-41).

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/prepare/test_transform.py -v`
Expected: FAIL — `test_group_key_prefixes_design_id` and the import of `group_key` now error (handled in Task 3). The four join tests PASS. (If the import error blocks collection, proceed to Task 3 which removes it; you may run `uv run pytest tests/prepare/test_transform.py -k join -v` to confirm the join tests pass in isolation first.)

- [ ] **Step 5: Commit**

```bash
git add src/prepare_lib/transform.py tests/prepare/test_transform.py
git commit -m "fix(prepare): F3 endpoint 단위 join (disjoint path 두-시점 매칭)"
```

---

### Task 3: `group_key = design_id` (`dataset.py` + test cleanup)

**Files:**
- Modify: `src/prepare_lib/dataset.py:10,27`
- Modify: `tests/prepare/test_transform.py` (remove group_key test + import)
- Modify: `tests/prepare/test_dataset.py:38`

- [ ] **Step 1: Update tests**

In `tests/prepare/test_transform.py`: remove `group_key` from the import on line 4 (so it reads `from prepare_lib.transform import FEATURE_NAMES, extract_features, extract_label, join_paths`) and DELETE `test_group_key_prefixes_design_id`.

In `tests/prepare/test_dataset.py`: change line 38 from
`    assert all(r["group_key"] == "gcd:clk" for r in rows)`
to
`    assert all(r["group_key"] == "gcd" for r in rows)`

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/prepare/test_dataset.py::test_build_dataset_rows_and_manifest -v`
Expected: FAIL — `group_key` is still `gcd:clk` (build_dataset uses the old helper).

- [ ] **Step 3: Update `src/prepare_lib/dataset.py`**

Change the import on line 10 from
`from prepare_lib.transform import FEATURE_NAMES, LABEL_NAME, group_key, join_paths`
to
`from prepare_lib.transform import FEATURE_NAMES, LABEL_NAME, join_paths`

Change the loop on lines 26-27 from
```python
    for r in rows:
        r["group_key"] = group_key(r["path_group"], design_id)
```
to
```python
    for r in rows:
        r["group_key"] = design_id  # OD-3 재설계: design 단위 group-disjoint
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/prepare/test_dataset.py tests/prepare/test_transform.py -v`
Expected: PASS (all dataset + transform tests).

- [ ] **Step 5: Commit**

```bash
git add src/prepare_lib/dataset.py tests/prepare/test_transform.py tests/prepare/test_dataset.py
git commit -m "fix(prepare): OD-3 group_key=design_id (design 단위 grouping)"
```

---

### Task 4: Convert fixtures to two-line headers (realism)

**Files:**
- Modify: `tests/prepare/fixtures/synth.rpt`, `tests/prepare/fixtures/route.rpt`

Two-line headers do not change any feature/label number, so all numeric assertions stay valid — this only makes the fixtures match real OpenSTA output (spec §3.7).

- [ ] **Step 1: Rewrite header lines in `tests/prepare/fixtures/synth.rpt`**

For EACH path block, replace the single-line `Startpoint:`/`Endpoint:` lines with two-line form. Example for the first block — change:
```
Startpoint: _0_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: _1_ (rising edge-triggered flip-flop clocked by clk)
```
to:
```
Startpoint: _0_
            (rising edge-triggered flip-flop clocked by clk)
Endpoint: _1_
          (rising edge-triggered flip-flop clocked by clk)
```
Apply the same wrap to all three blocks. For the input-port block, change `Startpoint: inp_a (input port clocked by clk)` to:
```
Startpoint: inp_a
            (input port clocked by clk)
```
Leave every other line (Path Group, Path Type, stage table, arrival, slack) untouched.

- [ ] **Step 2: Rewrite header lines in `tests/prepare/fixtures/route.rpt`** the same way (all three blocks: `_0_→_1_`, `_3_→_4_`, `_9_→_10_`).

- [ ] **Step 3: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS, same counts as before the fixture edit (header wrap changes no numbers; endpoints `_1_`/`_4_` still match → `n_samples=2`).

- [ ] **Step 4: Commit**

```bash
git add tests/prepare/fixtures/synth.rpt tests/prepare/fixtures/route.rpt
git commit -m "test(prepare): fixture 헤더를 실제 두-줄 포맷으로 (realism)"
```

---

### Task 5: Final verification + FINDINGS note

**Files:**
- Modify: `experiments/real-gcd/FINDINGS.md`

- [ ] **Step 1: Append an implementation note to `experiments/real-gcd/FINDINGS.md`**

Add at the end of the file:

```markdown
## 구현 반영 (2026-06-06)

- **F1** 두-줄 헤더 파싱 — `report.py` `_is_ff` clause 매칭으로 수정. ✅
- **F3** endpoint 단위 join — `transform.py` `join_paths` 재키((design_id, endpoint), max 필터, worst-per-endpoint). ✅ (설계: `docs/superpowers/specs/2026-06-06-f3-endpoint-pairing-design.md`)
- **F2** rich `-fields`는 미적용 — minimal `report_checks` 포맷 채택(OD-2 v2 연기).
- **F4** 진짜 post-route(native amd64)는 `issues/006`에서 — fixture는 여전히 post-placement 기반.
```

- [ ] **Step 2: Run the full verification (suite + lint + script smoke)**

Run:
```bash
uv run pytest -q && uv run ruff check src tests prepare.py && \
rm -rf /tmp/f3-ds && uv run python prepare.py \
  --synth tests/prepare/fixtures/synth.rpt --route tests/prepare/fixtures/route.rpt \
  --lockfile tests/prepare/fixtures/lockfile.yaml --design-id gcd --out-dir /tmp/f3-ds && \
cat /tmp/f3-ds/manifest.json
```
Expected: all tests PASS, ruff clean, CLI prints `2 samples → ...`, manifest `n_samples: 2`, rows carry `group_key: "gcd"`.

- [ ] **Step 3: Commit**

```bash
git add experiments/real-gcd/FINDINGS.md
git commit -m "docs(real-gcd): F1/F3 구현 반영 노트"
```

---

## Self-Review

**Spec coverage:** F1 two-line header (Task 1) · F3 endpoint join + max filter + worst-per-endpoint (Task 2) · OD-3 `group_key=design_id` (Task 3) · spec §3.7 two-line fixtures (Task 4) · evidence note + end-to-end smoke (Task 5). minimal-format / `parse_report` / `FEATURE_NAMES` / OD-1 explicitly unchanged.

**Placeholder scan:** none — every step ships complete code/edits/commands.

**Type consistency:** `join_paths(synth, route) -> list[dict]` signature unchanged; `_worst_max_by_endpoint` returns `dict[str, PathRecord]`. Row keys (`endpoint`, `startpoint`, 8 features incl `path_group`, `post_route_slack_ns`, later `group_key`) consistent across Tasks 2-3 and tests. `extract_features`/`extract_label`/`LABEL_NAME` untouched. `group_key` helper removed in Task 2 and its last consumer (dataset.py import, test) removed in Task 3 — no dangling reference after Task 3.

**Ordering note:** after Task 2, `test_group_key_prefixes_design_id` and the `group_key` import are temporarily broken; Task 3 removes them. The two tasks are committed separately but Task 3 must follow Task 2 to restore a green suite. Run order is sequential.
