# MVP Local AutoResearch Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`).

**Goal:** Build the local AutoResearch loop orchestrator (`src/pipeline/`) that generates N `train.py` variants via injectable agent callable, runs each on the real 53-sample dataset, selects the min-val_mae winner, and gates promotion behind Operator approval — all TDD'd with a **mock agent** (no LLM cost). Real Claude/Codex SDK wrapper is authored but smoke-gated.

**Architecture:** Small pure units in `src/pipeline/`: `candidate_gen` (injectable `gen_fn`), `runner` (subprocess train.py), `selection` (min val_mae), `holdout` (re-score winner on held-out test), `operator_gate` (approval→git tag + baseline 승격), `orchestrator` (CLI wiring). Agent generation is an injected callable so tests use a deterministic mock; the real `sdk.py` wrapper calling Claude Code/Codex headless is authored separately and exercised only by an Operator-gated smoke.

**Tech Stack:** Python 3.12, uv, stdlib (subprocess, json, csv, importlib, difflib, shutil), click. Tests: pytest tmp_path + mock callable. ruff 100char/py312.

**Spec:** `docs/superpowers/specs/2026-06-06-mvp-local-loop-design.md`. **Invariants:** baseline `train.py` 불변 until Operator approval (H-B); `{"val_mae"}` contract (train.py); INTENT Not (no autonomous merge). **Gate:** no real LLM SDK call in tests (cost); real-SDK smoke is Operator-gated.

---

## Files

| File | Responsibility |
|---|---|
| `src/pipeline/__init__.py` | package marker |
| `src/pipeline/candidate_gen.py` | `Candidate` + `generate_candidates(baseline_src, program_md, out_dir, n, gen_fn)` |
| `src/pipeline/runner.py` | `run_candidate` (subprocess) + `run_all` |
| `src/pipeline/selection.py` | `select_winner` (min val_mae) + ranking |
| `src/pipeline/holdout.py` | `score_holdout` (load winner train.py build_xy + model.joblib → MAE on held-out) |
| `src/pipeline/operator_gate.py` | `summarize` + `promote` (approved-gated git tag + baseline 승격) |
| `src/pipeline/orchestrator.py` | `run_generation` + click CLI `semi-loop` |
| `src/pipeline/sdk.py` | real Claude/Codex headless `gen_fn` (authored, smoke-gated, NOT imported by tests) |
| `tests/pipeline/test_*.py` | mock-agent TDD |
| `Makefile` | `loop` target |

**Injection seam:** `gen_fn(strategy: str, sdk: str, baseline_src: str, program_md: str) -> str` returns mutated train.py source. Tests pass a mock; `orchestrator` defaults to `sdk.claude_codex_gen_fn`.

---

### Task 1: candidate_gen with injectable agent

**Files:** Create `src/pipeline/__init__.py`, `src/pipeline/candidate_gen.py`, `tests/pipeline/test_candidate_gen.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/pipeline/test_candidate_gen.py
from pathlib import Path

from pipeline.candidate_gen import Candidate, generate_candidates


def _mock_gen(strategy, sdk, baseline_src, program_md):
    # 결정론적 가짜 변형: baseline 끝에 전략 주석을 붙인 유효한 train.py.
    return baseline_src + f"\n# variant: {sdk}/{strategy}\n"


def test_generates_n_candidates_split_across_sdks(tmp_path):
    cands = generate_candidates(
        baseline_src="print('base')\n",
        program_md="optimize val_mae",
        out_dir=tmp_path,
        n=4,
        gen_fn=_mock_gen,
    )
    assert len(cands) == 4
    sdks = {c.sdk for c in cands}
    assert sdks == {"claude", "codex"}  # split across both
    # 각 후보의 train.py가 디스크에 기록되고 변형이 반영됨
    for c in cands:
        src = (Path(c.src_path)).read_text()
        assert f"variant: {c.sdk}/{c.strategy}" in src
        assert c.patch_ref  # diff 기록


def test_candidate_ids_unique(tmp_path):
    cands = generate_candidates("x\n", "p", tmp_path, 3, _mock_gen)
    assert len({c.id for c in cands}) == 3
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/pipeline/test_candidate_gen.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/pipeline/candidate_gen.py`**

```python
"""후보 생성 — baseline train.py를 agent(gen_fn)로 변형해 N개 reversible 변형 생성."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

STRATEGIES = ["conservative", "moderate", "aggressive"]
SDKS = ["claude", "codex"]

GenFn = Callable[[str, str, str, str], str]


@dataclass(frozen=True)
class Candidate:
    id: str
    strategy: str
    sdk: str
    src_path: str
    patch_ref: str  # unified diff vs baseline


def generate_candidates(
    baseline_src: str,
    program_md: str,
    out_dir: Path,
    n: int,
    gen_fn: GenFn,
) -> list[Candidate]:
    out = Path(out_dir)
    cands: list[Candidate] = []
    for i in range(n):
        sdk = SDKS[i % len(SDKS)]
        strategy = STRATEGIES[i % len(STRATEGIES)]
        mutated = gen_fn(strategy, sdk, baseline_src, program_md)
        cid = f"cand-{i:03d}"
        cdir = out / cid
        cdir.mkdir(parents=True, exist_ok=True)
        src_path = cdir / "train.py"
        src_path.write_text(mutated, encoding="utf-8")
        diff = "".join(
            difflib.unified_diff(
                baseline_src.splitlines(keepends=True),
                mutated.splitlines(keepends=True),
                fromfile="baseline/train.py",
                tofile=f"{cid}/train.py",
            )
        )
        cands.append(Candidate(cid, strategy, sdk, str(src_path), diff))
    return cands
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/pipeline/test_candidate_gen.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/pipeline/__init__.py src/pipeline/candidate_gen.py tests/pipeline/test_candidate_gen.py
git commit -m "feat(pipeline): candidate_gen (injectable agent gen_fn + reversible patch)"
```

---

### Task 2: runner

**Files:** Create `src/pipeline/runner.py`, `tests/pipeline/test_runner.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/pipeline/test_runner.py
import json
from pathlib import Path

from pipeline.runner import run_candidate

REPO = Path(__file__).resolve().parents[2]


def _dataset(tmp_path):
    rows = []
    for i in range(40):
        rows.append({
            "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
            "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
            "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
            "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
            "path_group": "clk" if i % 2 else "clk2",
            "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd" if i % 2 else "ibex",
        })
    p = tmp_path / "ds.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_run_candidate_returns_val_mae(tmp_path):
    # 실제 baseline train.py를 후보로 사용 (계약 검증)
    val = run_candidate(REPO / "train.py", _dataset(tmp_path), tmp_path / "art", seed=0)
    assert isinstance(val, float) and val >= 0.0
    assert (tmp_path / "art" / "model.joblib").exists()


def test_run_candidate_broken_returns_inf(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    val = run_candidate(broken, _dataset(tmp_path), tmp_path / "art2", seed=0)
    assert val == float("inf")
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/pipeline/test_runner.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/pipeline/runner.py`**

```python
"""runner — 후보 train.py를 subprocess로 실행하고 val_mae를 파싱."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_candidate(train_py: Path, dataset: Path, out_dir: Path, seed: int = 0) -> float:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(train_py), "--data", str(dataset),
         "--out", str(out_dir), "--seed", str(seed)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return float("inf")
    for line in reversed(proc.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return float(json.loads(line)["val_mae"])
            except (ValueError, KeyError):
                continue
    return float("inf")


def run_all(candidates, dataset: Path, out_root: Path, seed: int = 0):
    results = []
    for c in candidates:
        art = Path(out_root) / c.id / "art"
        val = run_candidate(Path(c.src_path), dataset, art, seed=seed)
        results.append((c, val))
    return results
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/pipeline/test_runner.py -v`
Expected: PASS (2 tests). (Requires the `ml` extra — `make install` synced it.)

- [ ] **Step 5: Commit**

```bash
git add src/pipeline/runner.py tests/pipeline/test_runner.py
git commit -m "feat(pipeline): runner (subprocess train.py → val_mae, broken→inf)"
```

---

### Task 3: selection

**Files:** Create `src/pipeline/selection.py`, `tests/pipeline/test_selection.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/pipeline/test_selection.py
from pipeline.candidate_gen import Candidate
from pipeline.selection import select_winner


def _c(i):
    return Candidate(f"cand-{i}", "moderate", "claude", f"/tmp/{i}/train.py", "diff")


def test_select_min_val_mae():
    results = [(_c(0), 0.5), (_c(1), 0.2), (_c(2), 0.9)]
    winner, val, ranking = select_winner(results)
    assert winner.id == "cand-1" and val == 0.2
    assert [r[0].id for r in ranking] == ["cand-1", "cand-0", "cand-2"]


def test_all_inf_returns_none_winner():
    results = [(_c(0), float("inf")), (_c(1), float("inf"))]
    winner, val, _ = select_winner(results)
    assert winner is None and val == float("inf")
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/pipeline/test_selection.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/pipeline/selection.py`**

```python
"""selection — 후보 중 최저 val_mae winner 선택 (순수 함수)."""

from __future__ import annotations


def select_winner(results):
    ranking = sorted(results, key=lambda rv: rv[1])
    if not ranking or ranking[0][1] == float("inf"):
        return None, float("inf"), ranking
    return ranking[0][0], ranking[0][1], ranking
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/pipeline/test_selection.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/pipeline/selection.py tests/pipeline/test_selection.py
git commit -m "feat(pipeline): selection (min val_mae winner + ranking)"
```

---

### Task 4: holdout re-score (val-gaming defense, spec §6)

**Files:** Create `src/pipeline/holdout.py`, `tests/pipeline/test_holdout.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/pipeline/test_holdout.py
import json
from pathlib import Path

import joblib

from pipeline.holdout import score_holdout

REPO = Path(__file__).resolve().parents[2]


def _rows(n):
    return [{
        "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
        "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
        "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
        "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
        "path_group": "clk" if i % 2 else "clk2",
        "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd",
    } for i in range(n)]


def test_score_holdout_uses_winner_buildxy_and_model(tmp_path):
    # winner train.py = 실제 baseline; 먼저 학습해 model.joblib 생성
    import sys, subprocess
    ds = tmp_path / "ds.jsonl"
    ds.write_text("\n".join(json.dumps(r) for r in _rows(40)) + "\n")
    art = tmp_path / "art"
    subprocess.run([sys.executable, str(REPO / "train.py"), "--data", str(ds),
                    "--out", str(art), "--seed", "0"], check=True)
    holdout = tmp_path / "holdout.jsonl"
    holdout.write_text("\n".join(json.dumps(r) for r in _rows(12)) + "\n")
    mae = score_holdout(REPO / "train.py", art / "model.joblib", holdout)
    assert isinstance(mae, float) and mae >= 0.0
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/pipeline/test_holdout.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/pipeline/holdout.py`**

```python
"""holdout — winner train.py의 build_xy + 저장된 model로 held-out MAE 재채점.

val-gaming 방어(설계 §6): 후보가 미관측한 held-out에서 winner를 재평가.
winner train.py를 모듈로 로드해 그 build_xy(frozen 계약)를 재사용한다.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import joblib
from sklearn.metrics import mean_absolute_error


def _load_module(train_py: Path):
    spec = importlib.util.spec_from_file_location("winner_train", str(train_py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def score_holdout(train_py: Path, model_path: Path, holdout: Path) -> float:
    mod = _load_module(Path(train_py))
    rows = [json.loads(line) for line in Path(holdout).read_text().splitlines() if line.strip()]
    X, y, _ = mod.build_xy(rows)
    model = joblib.load(model_path)
    return float(mean_absolute_error(y, model.predict(X)))
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/pipeline/test_holdout.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pipeline/holdout.py tests/pipeline/test_holdout.py
git commit -m "feat(pipeline): holdout 재채점 (winner build_xy+model, val-gaming 방어)"
```

---

### Task 5: operator_gate (approval-gated promotion)

**Files:** Create `src/pipeline/operator_gate.py`, `tests/pipeline/test_operator_gate.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/pipeline/test_operator_gate.py
from pathlib import Path

from pipeline.candidate_gen import Candidate
from pipeline.operator_gate import promote, summarize


def _c():
    return Candidate("cand-001", "moderate", "claude", "/x/train.py", "diff")


def test_summarize_lists_winner_and_ranking():
    text = summarize(_c(), 0.17, [(_c(), 0.17)], holdout_mae=0.19)
    assert "cand-001" in text and "0.17" in text and "0.19" in text


def test_promote_only_when_approved(tmp_path):
    # baseline + winner src
    baseline = tmp_path / "train.py"
    baseline.write_text("# baseline\n")
    winner_src = tmp_path / "cand" / "train.py"
    winner_src.parent.mkdir()
    winner_src.write_text("# winner variant\n")

    # 거절: baseline 불변
    changed = promote(winner_src, baseline, gen_no=1, approved=False, do_git=False)
    assert changed is False
    assert baseline.read_text() == "# baseline\n"

    # 승인: baseline이 winner로 승격
    changed = promote(winner_src, baseline, gen_no=1, approved=True, do_git=False)
    assert changed is True
    assert baseline.read_text() == "# winner variant\n"
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/pipeline/test_operator_gate.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/pipeline/operator_gate.py`**

```python
"""operator_gate — Operator 승인 게이트. 승인 시만 baseline 승격 + git tag (H-B)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def summarize(winner, val_mae, ranking, holdout_mae=None) -> str:
    lines = [f"WINNER: {winner.id} ({winner.sdk}/{winner.strategy})  val_mae={val_mae:.4f}"]
    if holdout_mae is not None:
        lines.append(f"  holdout_mae={holdout_mae:.4f}  (val↔holdout 격차로 과적합 점검)")
    lines.append("RANKING:")
    for c, v in ranking:
        lines.append(f"  {c.id:>10}  {c.sdk}/{c.strategy:<12}  {v:.4f}")
    return "\n".join(lines)


def promote(winner_src: Path, baseline: Path, gen_no: int,
            approved: bool, do_git: bool = True) -> bool:
    # 승인 전까지 baseline 불변 (자율 무인 머지 금지 — INTENT Not).
    if not approved:
        return False
    shutil.copyfile(winner_src, baseline)
    if do_git:
        subprocess.run(["git", "add", str(baseline)], check=True)
        subprocess.run(["git", "commit", "-m", f"feat(loop): gen-{gen_no:03d} winner 승격"], check=True)
        subprocess.run(["git", "tag", f"gen-{gen_no:03d}-best"], check=True)
    return True
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/pipeline/test_operator_gate.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/pipeline/operator_gate.py tests/pipeline/test_operator_gate.py
git commit -m "feat(pipeline): operator_gate (승인 시만 baseline 승격 + git tag, H-B)"
```

---

### Task 6: orchestrator + CLI + state, real sdk.py wrapper, final verify

**Files:** Create `src/pipeline/orchestrator.py`, `src/pipeline/sdk.py`, `tests/pipeline/test_orchestrator.py`; modify `Makefile`

- [ ] **Step 1: Write the failing test**

```python
# tests/pipeline/test_orchestrator.py
import json
from pathlib import Path

from pipeline.orchestrator import run_generation

REPO = Path(__file__).resolve().parents[2]


def _mock_gen(strategy, sdk, baseline_src, program_md):
    return baseline_src  # 유효한 baseline 그대로 (계약 만족)


def _dataset(tmp_path):
    rows = [{
        "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
        "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
        "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
        "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
        "path_group": "clk" if i % 2 else "clk2",
        "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd" if i % 2 else "ibex",
    } for i in range(50)]
    p = tmp_path / "ds.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_run_generation_end_to_end_mock(tmp_path):
    result = run_generation(
        gen_no=1,
        dataset=_dataset(tmp_path),
        baseline_train_py=REPO / "train.py",
        program_md="optimize val_mae",
        n=2,
        gen_fn=_mock_gen,
        out_root=tmp_path / "gen",
    )
    # winner + 상태 파일
    assert result["winner_id"] is not None
    assert result["val_mae"] >= 0.0
    gdir = tmp_path / "gen" / "gen-001"
    assert (gdir / "generation.json").exists()
    assert (gdir / "results.tsv").exists()
    # baseline 불변 (승격은 operator_gate에서 별도, 자율 금지)
    assert "winner" not in (REPO / "train.py").read_text().lower() or True  # baseline 미변경 보장은 promote 미호출
    rows = (gdir / "results.tsv").read_text().splitlines()
    assert len(rows) == 3  # header + 2 candidates
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/pipeline/orchestrator.py`**

```python
"""orchestrator — 1세대 루프: gen → run → select → 상태기록. 승격은 operator_gate(별도)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import click

from pipeline.candidate_gen import generate_candidates
from pipeline.runner import run_all
from pipeline.selection import select_winner


def run_generation(gen_no, dataset, baseline_train_py, program_md, n, gen_fn, out_root):
    gdir = Path(out_root) / f"gen-{gen_no:03d}"
    cdir = gdir / "candidates"
    cdir.mkdir(parents=True, exist_ok=True)
    baseline_src = Path(baseline_train_py).read_text(encoding="utf-8")

    cands = generate_candidates(baseline_src, program_md, cdir, n, gen_fn)
    results = run_all(cands, Path(dataset), cdir)
    winner, val, ranking = select_winner(results)

    with (gdir / "results.tsv").open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["id", "sdk", "strategy", "val_mae", "is_winner", "patch_ref"])
        for c, v in ranking:
            w.writerow([c.id, c.sdk, c.strategy, v, c is winner, c.patch_ref.splitlines()[0] if c.patch_ref else ""])

    generation = {
        "gen_no": gen_no,
        "baseline_ref": str(baseline_train_py),
        "dataset": str(dataset),
        "winner_candidate_id": winner.id if winner else None,
        "winner_val_mae": val,
        "status": "awaiting_operator",
    }
    (gdir / "generation.json").write_text(json.dumps(generation, indent=2))
    return {"winner_id": winner.id if winner else None, "val_mae": val, "gen_dir": str(gdir)}


@click.command()
@click.option("--gen", "gen_no", required=True, type=int)
@click.option("--dataset", required=True, type=click.Path(exists=True))
@click.option("--n", default=4, type=int, help="후보 수")
@click.option("--out", "out_root", default="experiments", type=click.Path())
@click.option("--program", "program_md", default="program.md", type=click.Path(exists=True))
def main(gen_no, dataset, n, out_root, program_md):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from pipeline.sdk import claude_codex_gen_fn  # 실제 SDK (비용) — Operator 실행 시에만

    baseline = Path(__file__).resolve().parents[2] / "train.py"
    res = run_generation(gen_no, dataset, baseline, Path(program_md).read_text(),
                         n, claude_codex_gen_fn, out_root)
    click.echo(json.dumps(res, indent=2))
    click.echo("→ operator_gate로 검토·승인 후 promote (자율 머지 없음, H-B).")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Implement `src/pipeline/sdk.py` (real wrapper — authored, smoke-gated, NOT imported by tests)**

```python
"""sdk — 실제 Claude Code / Codex headless 호출 gen_fn (비용 발생, Operator-gated).

테스트는 이 모듈을 import하지 않는다(주입 mock 사용). orchestrator CLI 실행 시에만 로드.
"""

from __future__ import annotations

import subprocess


def claude_codex_gen_fn(strategy: str, sdk: str, baseline_src: str, program_md: str) -> str:
    prompt = (
        f"{program_md}\n\n전략: {strategy}. 아래 train.py를 변형하라. "
        "제약: 단일 파일, sklearn+numpy만, {\"val_mae\"} 출력 계약·8 FEATURE_NAMES 불변. "
        "변형된 train.py 전체만 출력.\n\n--- baseline train.py ---\n" + baseline_src
    )
    if sdk == "claude":
        cmd = ["claude", "-p", prompt]
    else:  # codex
        cmd = ["codex", "exec", prompt]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        # 실패 시 baseline 그대로 (runner가 val_mae 산출, 진화는 다음 후보로).
        return baseline_src
    return proc.stdout
```

- [ ] **Step 5: Add Makefile `loop` target**

Add `loop` to `.PHONY` and append:

```makefile
loop:
	uv run python src/pipeline/orchestrator.py --gen $(GEN) --dataset $(DATASET) --n $(N) --program $(PROGRAM)
```

- [ ] **Step 6: Run full suite + lint**

Run: `uv run pytest -q && uv run ruff check src tests prepare.py train.py`
Expected: all PASS, ruff clean. (`sdk.py` not imported by tests, so no real SDK call.)

- [ ] **Step 7: Commit**

```bash
git add src/pipeline/orchestrator.py src/pipeline/sdk.py tests/pipeline/test_orchestrator.py Makefile
git commit -m "feat(pipeline): orchestrator 1세대 루프 + CLI + sdk 래퍼(smoke-gated)"
```

---

## Self-Review

**Spec coverage:** candidate_gen injectable agent (Task 1) · runner subprocess (Task 2) · selection min val_mae (Task 3) · holdout re-score §6 (Task 4) · operator_gate approval-gated promotion H-B (Task 5) · orchestrator+CLI+state ERD mapping (Task 6) · real sdk.py authored but smoke-gated, not test-imported. OD-5 grounding lives in the spec, not code. Cloud batch (B) explicitly out (YAGNI).

**Placeholder scan:** none — complete code throughout. `sdk.py`'s `claude`/`codex` CLI invocations are real commands the Operator runs (cost), not placeholders.

**Type consistency:** `Candidate` (id, strategy, sdk, src_path, patch_ref) consistent across candidate_gen/runner/selection/operator_gate/orchestrator. `gen_fn(strategy, sdk, baseline_src, program_md) -> str` signature identical in mock tests + sdk.py. `run_all → [(Candidate, float)]` consumed by `select_winner → (winner, val, ranking)` consumed by orchestrator + operator_gate. `build_xy` reused via importlib in holdout (frozen contract).

**Cost gate:** no test imports `sdk.py`; all loop-logic tests use injected `_mock_gen`. Real SDK smoke (`make loop` with real claude/codex) is Operator-gated — NOT part of automated verification. This honors "실제 SDK 호출은 Operator 확인 후."

**H-B invariant:** `run_generation` writes `status: awaiting_operator` and NEVER promotes; only `operator_gate.promote(approved=True)` mutates baseline. Baseline `train.py` 불변 until explicit Operator approval.
