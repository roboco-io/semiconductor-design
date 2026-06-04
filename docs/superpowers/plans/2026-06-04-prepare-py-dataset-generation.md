# prepare.py Dataset Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the frozen, deterministic core of `prepare.py` — two OpenSTA `report_checks` reports (post-synth + post-route) → a per-path timing-slack surrogate dataset (feature rows + DATASET manifest), fully TDD'd against fixture `.rpt` files with no EDA tools required.

**Architecture:** Pure functions in `src/prepare_lib/` (parser → transforms → dataset assembler), wired by a thin `prepare.py` CLI at repo root. The parser's `PathRecord` output schema + the dataset row schema are the **frozen contract** (NFR-2) that `train.py` consumes. Actual EDA flow execution is out of scope — reports are inputs.

**Tech Stack:** Python 3.12, uv, click (CLI), stdlib `dataclasses`/`hashlib`/`json`/`re`, pytest (`tmp_path`, fixtures), ruff (100 char, py312).

**Decision lineage:** OD-1 resolved = per-path timing slack regression ([`issues/001`](../../../issues/001-surrogate-metric-definition.md)). This plan also concretely resolves OD-2 (feature_set) and OD-3 (grouping) — see Task 7.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/prepare_lib/__init__.py` | package marker |
| `src/prepare_lib/report.py` | `Stage`, `PathRecord` dataclasses + `parse_report(text)` |
| `src/prepare_lib/transform.py` | `extract_features`, `FEATURE_NAMES`, `extract_label`, `join_paths`, `group_key` (pure row transforms) |
| `src/prepare_lib/dataset.py` | `flow_lockfile_sha`, `build_dataset`, `write_dataset` (sha + assembly + manifest + I/O) |
| `prepare.py` | click CLI wiring the above (frozen entry point) |
| `tests/prepare/fixtures/{synth.rpt,route.rpt,lockfile.yaml}` | static fixtures |
| `tests/prepare/test_report.py` / `test_transform.py` / `test_dataset.py` | unit tests |

Import path: `pyproject.toml` has `pythonpath = ["src", "."]`, so `from prepare_lib.report import parse_report` works without packaging.

## Frozen data contract (NFR-2)

```
Stage(cell: str, pin: str, delay_ns: float, arrival_ns: float)
PathRecord(startpoint, endpoint, path_group, path_type, slack_ns, arrival_ns,
           stages: tuple[Stage,...], startpoint_is_ff: bool, endpoint_is_ff: bool)

FEATURE_NAMES = ["num_stages", "synth_slack_ns", "synth_arrival_ns",
                 "max_stage_delay_ns", "mean_stage_delay_ns",
                 "startpoint_is_ff", "endpoint_is_ff", "path_group"]
label = "post_route_slack_ns"
row = {startpoint, endpoint, path_group, group_key, **features, post_route_slack_ns}
manifest = {id, source_design, feature_set, label_metric, flow_lockfile_sha, n_samples}
```

A "stage" = a path line annotated with a sky130 library cell (lines `(in)`/`(out)` excluded). `num_stages` is the count of such stages (logic-depth proxy). Slew/Load/fanout features require `report_checks -fields` and are deferred to a v2 feature_set (Task 7 note).

---

### Task 1: Report parser (`report.py`)

**Files:**
- Create: `src/prepare_lib/__init__.py` (empty)
- Create: `src/prepare_lib/report.py`
- Create: `tests/prepare/fixtures/synth.rpt`
- Test: `tests/prepare/test_report.py`

- [ ] **Step 1: Create the fixture `tests/prepare/fixtures/synth.rpt`**

```
Startpoint: _0_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: _1_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

   Delay    Time   Description
-----------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00   clock network delay (ideal)
   0.00    0.00 ^ _0_/CLK (sky130_fd_sc_hd__dfxtp_1)
   0.36    0.36 ^ _0_/Q (sky130_fd_sc_hd__dfxtp_1)
   0.21    0.57 v _2_/Y (sky130_fd_sc_hd__nand2_1)
   0.15    0.72 ^ _1_/D (sky130_fd_sc_hd__dfxtp_1)
           0.72   data arrival time
           2.00   data required time
   ---------------------------------------------------------
           1.28   slack (MET)


Startpoint: _3_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: _4_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

   Delay    Time   Description
-----------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.00    0.00 ^ _3_/CLK (sky130_fd_sc_hd__dfxtp_1)
   0.38    0.38 ^ _3_/Q (sky130_fd_sc_hd__dfxtp_1)
   0.25    0.63 v _6_/Y (sky130_fd_sc_hd__or3_1)
   0.30    0.93 v _7_/Y (sky130_fd_sc_hd__nand3_1)
   0.16    1.09 ^ _4_/D (sky130_fd_sc_hd__dfxtp_1)
           1.09   data arrival time
           2.00   data required time
   ---------------------------------------------------------
           0.91   slack (MET)


Startpoint: inp_a (input port clocked by clk)
Endpoint: _5_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

   Delay    Time   Description
-----------------------------------------------------------
   0.00    0.00   clock clk (rise edge)
   0.10    0.10 v inp_a (in)
   0.22    0.32 ^ _8_/Y (sky130_fd_sc_hd__buf_1)
   0.14    0.46 ^ _5_/D (sky130_fd_sc_hd__dfxtp_1)
           0.46   data arrival time
           2.00   data required time
   ---------------------------------------------------------
           1.54   slack (MET)
```

- [ ] **Step 2: Write the failing test**

```python
# tests/prepare/test_report.py
from pathlib import Path

from prepare_lib.report import PathRecord, Stage, parse_report

FIX = Path(__file__).parent / "fixtures"


def _parse(name: str) -> list[PathRecord]:
    return parse_report((FIX / name).read_text())


def test_parses_three_paths():
    paths = _parse("synth.rpt")
    assert len(paths) == 3


def test_first_path_header_fields():
    p = _parse("synth.rpt")[0]
    assert p.startpoint == "_0_"
    assert p.endpoint == "_1_"
    assert p.path_group == "clk"
    assert p.path_type == "max"
    assert p.slack_ns == 1.28
    assert p.arrival_ns == 0.72
    assert p.startpoint_is_ff is True
    assert p.endpoint_is_ff is True


def test_stages_exclude_non_library_lines():
    # only sky130 library cells count as stages
    p0 = _parse("synth.rpt")[0]
    assert len(p0.stages) == 4
    assert isinstance(p0.stages[0], Stage)
    assert p0.stages[2].cell == "sky130_fd_sc_hd__nand2_1"
    assert p0.stages[2].pin == "_2_/Y"
    assert p0.stages[2].delay_ns == 0.21


def test_input_port_startpoint_not_ff():
    port_path = _parse("synth.rpt")[2]
    assert port_path.startpoint == "inp_a"
    assert port_path.startpoint_is_ff is False
    assert len(port_path.stages) == 2  # buf + dfxtp, the (in) line excluded
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/prepare/test_report.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'prepare_lib.report'`

- [ ] **Step 4: Write minimal implementation**

```python
# src/prepare_lib/report.py
"""OpenSTA report_checks 텍스트 → PathRecord (frozen 파서, NFR-2)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_STAGE_RE = re.compile(
    r"^\s*([\d.]+)\s+([\d.]+)\s+[v^]\s+(\S+)\s+\((sky130\S+)\)\s*$"
)
_SLACK_RE = re.compile(r"^\s*(-?[\d.]+)\s+slack", re.MULTILINE)
_ARRIVAL_RE = re.compile(r"^\s*([\d.]+)\s+data arrival time", re.MULTILINE)


@dataclass(frozen=True)
class Stage:
    cell: str
    pin: str
    delay_ns: float
    arrival_ns: float


@dataclass(frozen=True)
class PathRecord:
    startpoint: str
    endpoint: str
    path_group: str
    path_type: str
    slack_ns: float
    arrival_ns: float
    stages: tuple[Stage, ...]
    startpoint_is_ff: bool
    endpoint_is_ff: bool


def _field(block: str, label: str) -> str:
    m = re.search(rf"^{label}:\s+(\S+)", block, re.MULTILINE)
    if m is None:
        raise ValueError(f"missing '{label}' in path block")
    return m.group(1)


def _is_ff(block: str, label: str) -> bool:
    m = re.search(rf"^{label}:.*$", block, re.MULTILINE)
    return m is not None and "flip-flop" in m.group(0)


def _stages(block: str) -> tuple[Stage, ...]:
    out = []
    for line in block.splitlines():
        m = _STAGE_RE.match(line)
        if m:
            out.append(Stage(cell=m.group(4), pin=m.group(3),
                             delay_ns=float(m.group(1)), arrival_ns=float(m.group(2))))
    return tuple(out)


def parse_report(text: str) -> list[PathRecord]:
    blocks = re.split(r"(?=^Startpoint:)", text, flags=re.MULTILINE)
    records: list[PathRecord] = []
    for block in blocks:
        if not block.lstrip().startswith("Startpoint:"):
            continue
        slack = _SLACK_RE.search(block)
        arrival = _ARRIVAL_RE.search(block)
        if slack is None or arrival is None:
            raise ValueError("path block missing slack or arrival line")
        records.append(
            PathRecord(
                startpoint=_field(block, "Startpoint"),
                endpoint=_field(block, "Endpoint"),
                path_group=_field(block, "Path Group"),
                path_type=_field(block, "Path Type"),
                slack_ns=float(slack.group(1)),
                arrival_ns=float(arrival.group(1)),
                stages=_stages(block),
                startpoint_is_ff=_is_ff(block, "Startpoint"),
                endpoint_is_ff=_is_ff(block, "Endpoint"),
            )
        )
    return records
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/prepare/test_report.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/prepare_lib/__init__.py src/prepare_lib/report.py tests/prepare/
git commit -m "feat(prepare): OpenSTA report_checks 파서 (PathRecord)"
```

---

### Task 2: Feature extraction (`transform.py`)

**Files:**
- Create: `src/prepare_lib/transform.py`
- Test: `tests/prepare/test_transform.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/prepare/test_transform.py
from pathlib import Path

from prepare_lib.report import parse_report
from prepare_lib.transform import FEATURE_NAMES, extract_features

FIX = Path(__file__).parent / "fixtures"


def _synth():
    return parse_report((FIX / "synth.rpt").read_text())


def test_feature_names_frozen_order():
    assert FEATURE_NAMES == [
        "num_stages", "synth_slack_ns", "synth_arrival_ns",
        "max_stage_delay_ns", "mean_stage_delay_ns",
        "startpoint_is_ff", "endpoint_is_ff", "path_group",
    ]


def test_extract_features_first_path():
    f = extract_features(_synth()[0])
    assert f["num_stages"] == 4
    assert f["synth_slack_ns"] == 1.28
    assert f["synth_arrival_ns"] == 0.72
    assert f["max_stage_delay_ns"] == 0.36
    assert f["mean_stage_delay_ns"] == 0.18
    assert f["startpoint_is_ff"] == 1
    assert f["endpoint_is_ff"] == 1
    assert f["path_group"] == "clk"


def test_features_cover_exactly_feature_names():
    f = extract_features(_synth()[0])
    assert set(f.keys()) == set(FEATURE_NAMES)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/prepare/test_transform.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'prepare_lib.transform'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/prepare_lib/transform.py
"""PathRecord → feature/label row 변환 (순수 함수, frozen 계약)."""

from __future__ import annotations

from prepare_lib.report import PathRecord

FEATURE_NAMES = [
    "num_stages",
    "synth_slack_ns",
    "synth_arrival_ns",
    "max_stage_delay_ns",
    "mean_stage_delay_ns",
    "startpoint_is_ff",
    "endpoint_is_ff",
    "path_group",
]

LABEL_NAME = "post_route_slack_ns"


def extract_features(p: PathRecord) -> dict:
    delays = [s.delay_ns for s in p.stages]
    n = len(delays)
    return {
        "num_stages": n,
        "synth_slack_ns": p.slack_ns,
        "synth_arrival_ns": p.arrival_ns,
        "max_stage_delay_ns": max(delays) if delays else 0.0,
        "mean_stage_delay_ns": round(sum(delays) / n, 6) if n else 0.0,
        "startpoint_is_ff": int(p.startpoint_is_ff),
        "endpoint_is_ff": int(p.endpoint_is_ff),
        "path_group": p.path_group,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/prepare/test_transform.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/prepare_lib/transform.py tests/prepare/test_transform.py
git commit -m "feat(prepare): OD-2 path feature 추출 (feature_set v1)"
```

---

### Task 3: Label + join (`transform.py`)

**Files:**
- Modify: `src/prepare_lib/transform.py`
- Create: `tests/prepare/fixtures/route.rpt`
- Modify: `tests/prepare/test_transform.py`

- [ ] **Step 1: Create the fixture `tests/prepare/fixtures/route.rpt`**

`_0_→_1_` and `_3_→_4_` match synth (slack degraded post-route); `inp_a→_5_` omitted (tests drop); `_9_→_10_` is route-only (tests drop from synth side).

```
Startpoint: _0_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: _1_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

   Delay    Time   Description
-----------------------------------------------------------
   0.00    0.00 ^ _0_/CLK (sky130_fd_sc_hd__dfxtp_1)
   0.40    0.40 ^ _0_/Q (sky130_fd_sc_hd__dfxtp_1)
   0.55    0.95 v _2_/Y (sky130_fd_sc_hd__nand2_1)
   0.20    1.15 ^ _1_/D (sky130_fd_sc_hd__dfxtp_1)
           1.15   data arrival time
           2.00   data required time
   ---------------------------------------------------------
           0.85   slack (MET)


Startpoint: _3_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: _4_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

   Delay    Time   Description
-----------------------------------------------------------
   0.00    0.00 ^ _3_/CLK (sky130_fd_sc_hd__dfxtp_1)
   0.42    0.42 ^ _3_/Q (sky130_fd_sc_hd__dfxtp_1)
   0.70    1.12 v _6_/Y (sky130_fd_sc_hd__or3_1)
   0.28    1.40 v _7_/Y (sky130_fd_sc_hd__nand3_1)
   0.20    1.60 ^ _4_/D (sky130_fd_sc_hd__dfxtp_1)
           1.60   data arrival time
           2.00   data required time
   ---------------------------------------------------------
           0.40   slack (MET)


Startpoint: _9_ (rising edge-triggered flip-flop clocked by clk)
Endpoint: _10_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max

   Delay    Time   Description
-----------------------------------------------------------
   0.00    0.00 ^ _9_/CLK (sky130_fd_sc_hd__dfxtp_1)
   0.33    0.33 ^ _9_/Q (sky130_fd_sc_hd__dfxtp_1)
   0.19    0.52 ^ _10_/D (sky130_fd_sc_hd__dfxtp_1)
           0.52   data arrival time
           2.00   data required time
   ---------------------------------------------------------
           1.48   slack (MET)
```

- [ ] **Step 2: Write the failing test**

```python
# append to tests/prepare/test_transform.py
from prepare_lib.transform import extract_label, group_key, join_paths


def _route():
    return parse_report((FIX / "route.rpt").read_text())


def test_extract_label_is_route_slack():
    assert extract_label(_route()[0]) == 0.85


def test_join_keeps_only_matched_paths():
    rows = join_paths(_synth(), _route())
    keys = {(r["startpoint"], r["endpoint"]) for r in rows}
    assert keys == {("_0_", "_1_"), ("_3_", "_4_")}  # inp_a & _9_ dropped


def test_join_row_has_features_and_label():
    rows = join_paths(_synth(), _route())
    row = next(r for r in rows if r["startpoint"] == "_0_")
    assert row["num_stages"] == 4
    assert row["synth_slack_ns"] == 1.28
    assert row["post_route_slack_ns"] == 0.85


def test_group_key_prefixes_design_id():
    assert group_key("clk", "gcd") == "gcd:clk"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/prepare/test_transform.py -v`
Expected: FAIL with `ImportError: cannot import name 'extract_label'`

- [ ] **Step 4: Write minimal implementation (append to `transform.py`)**

```python
def extract_label(p: PathRecord) -> float:
    return p.slack_ns


def group_key(path_group: str, design_id: str) -> str:
    return f"{design_id}:{path_group}"


def join_paths(synth: list[PathRecord], route: list[PathRecord]) -> list[dict]:
    route_by_key = {(p.startpoint, p.endpoint, p.path_group): p for p in route}
    rows: list[dict] = []
    for sp in synth:
        key = (sp.startpoint, sp.endpoint, sp.path_group)
        rp = route_by_key.get(key)
        if rp is None:
            continue  # unmatched synth path dropped (no post-route label)
        rows.append(
            {
                "startpoint": sp.startpoint,
                "endpoint": sp.endpoint,
                "path_group": sp.path_group,
                **extract_features(sp),
                LABEL_NAME: extract_label(rp),
            }
        )
    return rows
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/prepare/test_transform.py -v`
Expected: PASS (7 tests total)

- [ ] **Step 6: Commit**

```bash
git add src/prepare_lib/transform.py tests/prepare/
git commit -m "feat(prepare): post-route slack label + (startpoint,endpoint,clock) join + OD-3 group_key"
```

---

### Task 4: Lockfile SHA anchor (`dataset.py`)

**Files:**
- Create: `src/prepare_lib/dataset.py`
- Create: `tests/prepare/fixtures/lockfile.yaml`
- Create: `tests/prepare/test_dataset.py`

- [ ] **Step 1: Create the fixture `tests/prepare/fixtures/lockfile.yaml`**

```yaml
# fixture flow lockfile (재현성 앵커 대상)
flow: openroad-flow-scripts
design: gcd
pdk: sky130A
tools:
  yosys: "0.44"
  openroad: "2.0"
```

- [ ] **Step 2: Write the failing test**

```python
# tests/prepare/test_dataset.py
import hashlib
from pathlib import Path

from prepare_lib.dataset import flow_lockfile_sha

FIX = Path(__file__).parent / "fixtures"


def test_flow_lockfile_sha_matches_sha256():
    path = FIX / "lockfile.yaml"
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert flow_lockfile_sha(path) == expected
    assert len(flow_lockfile_sha(path)) == 64


def test_flow_lockfile_sha_is_deterministic():
    path = FIX / "lockfile.yaml"
    assert flow_lockfile_sha(path) == flow_lockfile_sha(path)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/prepare/test_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'prepare_lib.dataset'`

- [ ] **Step 4: Write minimal implementation**

```python
# src/prepare_lib/dataset.py
"""데이터셋 조립 + manifest + I/O (flow_lockfile_sha 재현성 앵커)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def flow_lockfile_sha(lockfile_path: str | Path) -> str:
    return hashlib.sha256(Path(lockfile_path).read_bytes()).hexdigest()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/prepare/test_dataset.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add src/prepare_lib/dataset.py tests/prepare/fixtures/lockfile.yaml tests/prepare/test_dataset.py
git commit -m "feat(prepare): flow_lockfile_sha 재현성 앵커 (DATASET.flow_lockfile_sha)"
```

---

### Task 5: Build + write dataset (`dataset.py`)

**Files:**
- Modify: `src/prepare_lib/dataset.py`
- Modify: `tests/prepare/test_dataset.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/prepare/test_dataset.py
import json as _json

from prepare_lib.dataset import build_dataset, write_dataset
from prepare_lib.transform import FEATURE_NAMES


def test_build_dataset_rows_and_manifest():
    rows, manifest = build_dataset(
        synth_report=FIX / "synth.rpt",
        route_report=FIX / "route.rpt",
        lockfile=FIX / "lockfile.yaml",
        design_id="gcd",
    )
    assert len(rows) == 2  # _0_ and _3_ matched
    assert all(r["group_key"] == "gcd:clk" for r in rows)
    assert manifest["source_design"] == "gcd"
    assert manifest["feature_set"] == FEATURE_NAMES
    assert manifest["label_metric"] == "post_route_slack_ns"
    assert manifest["n_samples"] == 2
    assert len(manifest["flow_lockfile_sha"]) == 64
    assert manifest["id"].startswith("gcd-")


def test_write_dataset_emits_jsonl_and_manifest(tmp_path):
    rows, manifest = build_dataset(
        synth_report=FIX / "synth.rpt",
        route_report=FIX / "route.rpt",
        lockfile=FIX / "lockfile.yaml",
        design_id="gcd",
    )
    write_dataset(rows, manifest, tmp_path)
    lines = (tmp_path / "dataset.jsonl").read_text().splitlines()
    assert len(lines) == 2
    first = _json.loads(lines[0])
    assert "post_route_slack_ns" in first and "group_key" in first
    written_manifest = _json.loads((tmp_path / "manifest.json").read_text())
    assert written_manifest["n_samples"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/prepare/test_dataset.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_dataset'`

- [ ] **Step 3: Write minimal implementation (append to `dataset.py`)**

```python
from prepare_lib.report import parse_report
from prepare_lib.transform import FEATURE_NAMES, LABEL_NAME, group_key, join_paths


def build_dataset(
    synth_report: str | Path,
    route_report: str | Path,
    lockfile: str | Path,
    design_id: str,
) -> tuple[list[dict], dict]:
    synth = parse_report(Path(synth_report).read_text())
    route = parse_report(Path(route_report).read_text())
    rows = join_paths(synth, route)
    for r in rows:
        r["group_key"] = group_key(r["path_group"], design_id)
    sha = flow_lockfile_sha(lockfile)
    manifest = {
        "id": f"{design_id}-{sha[:12]}",
        "source_design": design_id,
        "feature_set": FEATURE_NAMES,
        "label_metric": LABEL_NAME,
        "flow_lockfile_sha": sha,
        "n_samples": len(rows),
    }
    return rows, manifest


def write_dataset(rows: list[dict], manifest: dict, out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "dataset.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/prepare/test_dataset.py -v`
Expected: PASS (4 tests total)

- [ ] **Step 5: Commit**

```bash
git add src/prepare_lib/dataset.py tests/prepare/test_dataset.py
git commit -m "feat(prepare): build_dataset + write_dataset + DATASET manifest"
```

---

### Task 6: CLI wiring (`prepare.py`) + Makefile

**Files:**
- Modify: `prepare.py` (replace NotImplementedError skeleton)
- Modify: `Makefile`
- Test: `tests/prepare/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/prepare/test_cli.py
import json
from pathlib import Path

from click.testing import CliRunner

import prepare

FIX = Path(__file__).parent / "fixtures"


def test_cli_writes_dataset(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        prepare.main,
        [
            "--synth", str(FIX / "synth.rpt"),
            "--route", str(FIX / "route.rpt"),
            "--lockfile", str(FIX / "lockfile.yaml"),
            "--design-id", "gcd",
            "--out-dir", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["n_samples"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/prepare/test_cli.py -v`
Expected: FAIL — `prepare.main` does not exist (current `prepare.py` raises `NotImplementedError` at import)

- [ ] **Step 3: Replace `prepare.py` with the CLI**

```python
# prepare.py
"""prepare.py — EDA surrogate 데이터셋 준비 (frozen, 사람 유지 / NFR-2).

OD-1=per-path timing slack. 같은 flow 1회의 합성 후·라우팅 후 STA report_checks
두 리포트 → per-path feature + post-route slack label 데이터셋. 에이전트 변경 금지.
설계: docs/superpowers/plans/2026-06-04-prepare-py-dataset-generation.md
"""

from __future__ import annotations

import click

from prepare_lib.dataset import build_dataset, write_dataset


@click.command()
@click.option("--synth", required=True, type=click.Path(exists=True), help="합성 후 STA report_checks")
@click.option("--route", required=True, type=click.Path(exists=True), help="라우팅 후 STA report_checks")
@click.option("--lockfile", required=True, type=click.Path(exists=True), help="flow lockfile (sha 앵커)")
@click.option("--design-id", required=True, help="source design 식별자")
@click.option("--out-dir", required=True, type=click.Path(), help="dataset.jsonl + manifest.json 출력 디렉터리")
def main(synth: str, route: str, lockfile: str, design_id: str, out_dir: str) -> None:
    rows, manifest = build_dataset(synth, route, lockfile, design_id)
    write_dataset(rows, manifest, out_dir)
    click.echo(f"{manifest['n_samples']} samples → {out_dir} (sha {manifest['flow_lockfile_sha'][:12]})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add Makefile target**

Insert after the `clean:` block in `Makefile`:

```makefile
prepare:
	uv run python prepare.py --synth $(SYNTH) --route $(ROUTE) --lockfile $(LOCKFILE) --design-id $(DESIGN) --out-dir $(OUT)
```

And add `prepare` to the `.PHONY` line:

```makefile
.PHONY: install test lint fmt clean prepare
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/prepare/test_cli.py -v`
Expected: PASS

- [ ] **Step 6: Run full suite + lint**

Run: `uv run pytest -v && uv run ruff check src tests`
Expected: all PASS, ruff clean

- [ ] **Step 7: Commit**

```bash
git add prepare.py Makefile tests/prepare/test_cli.py
git commit -m "feat(prepare): click CLI + make prepare 타깃"
```

---

### Task 7: Resolve OD-2 / OD-3 + close the loop

**Files:**
- Modify: `issues/002-feature-set-composition.md`, `issues/003-dataset-scale-label-count.md`, `issues/README.md`
- Modify: `PRD.md` (§10 OD-2/OD-3 status)

- [ ] **Step 1: Add Resolution to `issues/002`**

Set frontmatter `status: resolved`. Append:

```markdown
## Resolution (2026-06-04, prepare.py 구현)

feature_set v1 (default `report_checks` 포맷에서 파싱 가능한 필드만):
`num_stages, synth_slack_ns, synth_arrival_ns, max_stage_delay_ns, mean_stage_delay_ns, startpoint_is_ff, endpoint_is_ff, path_group`.

누수 배제: label(post-route slack)에서 역산 가능한 필드 없음. **Slew/Load/fanout은 default 포맷에 없어 제외** — `report_checks -fields {slew cap}` 필요, v2 feature_set으로 연기. (초안의 fanout_sum/fanout_max는 실제 report 컬럼 부재로 철회 — 추측 vs grep 검증 invariant.)
```

- [ ] **Step 2: Add Resolution to `issues/003`**

Set frontmatter `status: resolved`. Append:

```markdown
## Resolution (2026-06-04, prepare.py 구현)

per-path라 1 설계 1회 실행으로 수천 path 샘플. 누수 차단: `group_key = f"{design_id}:{path_group}"` 컬럼을 부여, train/val 분할은 **group-disjoint**(같은 design:clock 그룹이 양쪽에 들어가지 않음). join 키 = (startpoint, endpoint, path_group), 미매칭 path는 drop. 실제 라벨 수 충분성은 real-flow 실행 시 경험적으로 재확인(현재 fixture-first).
```

- [ ] **Step 3: Update `issues/README.md` table** — set 002·003 rows to `✅ resolved (2026-06-04)`.

- [ ] **Step 4: Update `PRD.md` §10** — mark OD-2·OD-3 resolved with one-line pointers (mirror the OD-1 resolved style).

- [ ] **Step 5: Commit**

```bash
git add issues/ PRD.md
git commit -m "docs: OD-2(feature_set v1)·OD-3(group-disjoint) resolved via prepare.py 구현"
```

---

## Self-Review

**Spec coverage:** parse_report (Task 1) · OD-2 features (Task 2) · label+join+OD-3 group (Task 3) · flow_lockfile_sha (Task 4) · build/write+manifest=DATASET (Task 5) · frozen CLI prepare.py (Task 6) · OD-2/OD-3 resolution (Task 7). FR-1 "flow 1회 → feature+label 쌍 + lockfile_sha 앵커" fully covered. Real flow execution explicitly deferred (out of scope, stated in Goal).

**Placeholder scan:** none — every step ships complete code/fixtures/commands.

**Type consistency:** `PathRecord`/`Stage` fields used identically across Tasks 1-5. `FEATURE_NAMES` defined Task 2, reused Tasks 3/5. `LABEL_NAME="post_route_slack_ns"` consistent in transform/dataset/tests. `build_dataset(synth_report, route_report, lockfile, design_id)` signature matches CLI call in Task 6. `group_key(path_group, design_id)` arg order consistent Task 3 ↔ Task 5.

**Frozen-contract note:** `prepare.py` + `src/prepare_lib/` are NFR-2 frozen; agents mutate only `train.py` (future). The dataset row + manifest schema is the train.py input contract.
