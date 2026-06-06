# 다중 seed median selection harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** selection harness를 단일 seed=0 → 5개 고정 seed의 median 집계로 바꿔, 노이즈 큰 53샘플에서 위양성 winner 선택을 막는다.

**Architecture:** `runner.run_candidate`(단일 seed subprocess 실행)는 그대로 두고, 그 위에 `run_candidate_multiseed`(5 seed median + inf 단락)를 신설. `run_all`이 후보당 `(candidate, median_val, per_seed_vals)` 3-튜플을 반환하고, `select_winner`는 인덱스 1(median) 기준 정렬이라 무변경. `orchestrator`는 3-튜플 언패킹 + per-seed 기록 + `generation.json`에 프로토콜 출처(`eval_seeds`·`metric`)를 남긴다.

**Tech Stack:** Python 3.12, stdlib `statistics.median`, pytest, ruff. 신규 의존성 없음.

**Spec:** `docs/superpowers/specs/2026-06-06-multiseed-median-selection-design.md`

---

### Task 1: `run_candidate_multiseed` — 5 seed median + inf 단락

**Files:**
- Modify: `src/pipeline/runner.py` (신규 함수 추가, `run_candidate`는 무변경)
- Test: `tests/pipeline/test_runner.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_runner.py` 끝에 추가

```python
from pipeline.runner import run_candidate_multiseed


def test_multiseed_returns_median_and_per_seed(tmp_path):
    agg, per_seed = run_candidate_multiseed(
        REPO / "train.py", _dataset(tmp_path), tmp_path / "ms", seeds=(0, 1, 2)
    )
    assert isinstance(agg, float) and agg >= 0.0
    assert len(per_seed) == 3 and all(v >= 0.0 for v in per_seed)
    assert agg == sorted(per_seed)[1]  # 3개의 median == 가운데 값


def test_multiseed_any_inf_disqualifies(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")  # 모든 seed에서 즉시 실패
    agg, per_seed = run_candidate_multiseed(
        broken, _dataset(tmp_path), tmp_path / "ms2", seeds=(0, 1, 2, 3, 4)
    )
    assert agg == float("inf")
    assert per_seed[-1] == float("inf")  # 실패 seed가 기록에 보임


def test_multiseed_short_circuits_on_first_inf(tmp_path, monkeypatch):
    import pipeline.runner as R
    calls = []

    def fake_run_candidate(train_py, dataset, out_dir, seed=0, timeout=300):
        calls.append(seed)
        return float("inf") if seed == 1 else 0.2

    monkeypatch.setattr(R, "run_candidate", fake_run_candidate)
    agg, per_seed = R.run_candidate_multiseed(
        Path("/x/train.py"), Path("/x/ds.jsonl"), tmp_path / "ms3", seeds=(0, 1, 2, 3, 4)
    )
    assert agg == float("inf")
    assert calls == [0, 1]  # seed 1에서 단락 — 2,3,4는 호출 안 됨
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_runner.py -k multiseed -v`
Expected: FAIL — `ImportError: cannot import name 'run_candidate_multiseed'`

- [ ] **Step 3: 최소 구현** — `src/pipeline/runner.py` 상단 import에 `import statistics` 추가, 파일 끝(`run_all` 앞)에 함수 추가

```python
def run_candidate_multiseed(train_py: Path, dataset: Path, out_dir: Path,
                            seeds=(0, 1, 2, 3, 4), timeout: int = 300):
    """후보를 여러 고정 seed로 평가하고 (median, per_seed_vals)를 반환.

    어느 seed든 inf(subprocess 실패/timeout)면 즉시 단락하여 (inf, 평가된 값들+inf)을 반환한다
    — "재현·안정 코드만 승격" 기준 (spec D3).
    """
    vals: list[float] = []
    for s in seeds:
        v = run_candidate(train_py, dataset, Path(out_dir) / f"seed-{s}",
                          seed=s, timeout=timeout)
        if v == float("inf"):
            return float("inf"), vals + [float("inf")]
        vals.append(v)
    return statistics.median(vals), vals
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_runner.py -k multiseed -v`
Expected: 3 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/runner.py tests/pipeline/test_runner.py
git commit -m "feat(runner): run_candidate_multiseed — 5 seed median + inf 단락"
```

---

### Task 2: `run_all` 3-튜플 반환 (median + per-seed)

**Files:**
- Modify: `src/pipeline/runner.py:39-45` (`run_all`)
- Test: `tests/pipeline/test_runner.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_runner.py` 끝에 추가

```python
from pipeline.candidate_gen import Candidate
from pipeline.runner import run_all


def test_run_all_returns_median_triples(tmp_path):
    ds = _dataset(tmp_path)
    src = REPO / "train.py"
    cands = [Candidate("cand-0", "moderate", "claude", str(src), "diff")]
    results = run_all(cands, ds, tmp_path / "root", seeds=(0, 1, 2))
    assert len(results) == 1
    c, median_val, per_seed = results[0]  # 3-튜플
    assert c.id == "cand-0"
    assert isinstance(median_val, float) and median_val >= 0.0
    assert len(per_seed) == 3
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_runner.py::test_run_all_returns_median_triples -v`
Expected: FAIL — `ValueError: too many values to unpack` 또는 `TypeError` (현 run_all은 2-튜플 반환 + `seeds` 인자 없음)

- [ ] **Step 3: 구현** — `run_all`을 다음으로 교체

```python
def run_all(candidates, dataset: Path, out_root: Path, seeds=(0, 1, 2, 3, 4)):
    results = []
    for c in candidates:
        art = Path(out_root) / c.id / "art"
        median_val, per_seed = run_candidate_multiseed(
            Path(c.src_path), dataset, art, seeds=seeds)
        results.append((c, median_val, per_seed))
    return results
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_runner.py -v`
Expected: 모든 runner 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/runner.py tests/pipeline/test_runner.py
git commit -m "feat(runner): run_all이 (cand, median, per_seed) 3-튜플 반환"
```

---

### Task 3: selection이 3-튜플의 3번째 원소를 무시함을 고정

**Files:**
- Test: `tests/pipeline/test_selection.py` (selection.py는 무변경 — 회귀 가드만 추가)

- [ ] **Step 1: 가드 테스트 작성** — `tests/pipeline/test_selection.py` 끝에 추가

```python
def test_select_winner_ignores_per_seed_third_element():
    # run_all이 (cand, median, per_seed) 3-튜플을 주어도 median 기준 정렬
    results = [
        (_c(0), 0.5, [0.4, 0.5, 0.6]),
        (_c(1), 0.2, [0.1, 0.2, 0.9]),
        (_c(2), float("inf"), [0.1, float("inf")]),
    ]
    winner, val, ranking = select_winner(results)
    assert winner.id == "cand-1" and val == 0.2
    assert ranking[0][0].id == "cand-1"
    assert ranking[0][2] == [0.1, 0.2, 0.9]  # per_seed 보존
```

- [ ] **Step 2: 실행 — 무변경으로 통과해야 함 (selection은 인덱스 1만 사용)**

Run: `uv run pytest tests/pipeline/test_selection.py -v`
Expected: 3 PASS (기존 2 + 신규 1). 만약 FAIL이면 `select_winner`가 튜플 폭을 가정하는 버그 — `rv[1]`만 쓰는지 확인.

- [ ] **Step 3: 커밋**

```bash
git add tests/pipeline/test_selection.py
git commit -m "test(selection): 3-튜플 입력에서 median 정렬 회귀 가드"
```

---

### Task 4: orchestrator — 3-튜플 언패킹 + per-seed 기록 + 프로토콜 메타

**Files:**
- Modify: `src/pipeline/orchestrator.py:16-43` (`run_generation`)
- Test: `tests/pipeline/test_orchestrator.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_orchestrator.py`의 `test_run_generation_end_to_end_mock` 끝(파일 마지막 `assert len(rows) == 3` 다음)에 추가

```python
    # 프로토콜 메타: generation.json에 집계법·seed 기록
    gen_meta = json.loads((gdir / "generation.json").read_text())
    assert gen_meta["metric"] == "median_val_mae"
    assert gen_meta["eval_seeds"] == [0, 1, 2, 3, 4]
    # results.tsv 헤더에 median_val_mae + per_seed_vals 컬럼
    header = rows[0].split("\t")
    assert "median_val_mae" in header
    assert "per_seed_vals" in header
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -v`
Expected: FAIL — 현 `run_generation`은 `for c, v in ranking` 언패킹이 3-튜플에서 깨지거나, `metric`/`eval_seeds` 키 부재

- [ ] **Step 3: 구현** — `run_generation`을 다음으로 교체 (시그니처에 `seeds` 추가)

```python
def run_generation(gen_no, dataset, baseline_train_py, program_md, n, gen_fn,
                   out_root, seeds=(0, 1, 2, 3, 4)):
    gdir = Path(out_root) / f"gen-{gen_no:03d}"
    cdir = gdir / "candidates"
    cdir.mkdir(parents=True, exist_ok=True)
    baseline_src = Path(baseline_train_py).read_text(encoding="utf-8")

    cands = generate_candidates(baseline_src, program_md, cdir, n, gen_fn)
    results = run_all(cands, Path(dataset), cdir, seeds=seeds)
    winner, val, ranking = select_winner(results)

    with (gdir / "results.tsv").open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["id", "sdk", "strategy", "median_val_mae", "per_seed_vals",
                    "is_winner", "patch_ref"])
        for c, v, per_seed in ranking:
            w.writerow([c.id, c.sdk, c.strategy, v, json.dumps(per_seed),
                        c is winner,
                        c.patch_ref.splitlines()[0] if c.patch_ref else ""])

    generation = {
        "gen_no": gen_no,
        "baseline_ref": str(baseline_train_py),
        "dataset": str(dataset),
        "metric": "median_val_mae",
        "eval_seeds": list(seeds),
        "winner_candidate_id": winner.id if winner else None,
        # float("inf") is not valid RFC 8259 — store null when no valid winner.
        "winner_val_mae": val if val != float("inf") else None,
        "status": "awaiting_operator",
    }
    (gdir / "generation.json").write_text(json.dumps(generation, indent=2))
    return {"winner_id": winner.id if winner else None, "val_mae": val,
            "gen_dir": str(gdir)}
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -v`
Expected: PASS (winner·status·baseline 불변·메타·컬럼 모두 검증)

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/orchestrator.py tests/pipeline/test_orchestrator.py
git commit -m "feat(orchestrator): median selection + per-seed/eval_seeds 기록"
```

---

### Task 5: 전체 회귀 + ruff green 게이트

**Files:** 없음 (검증만)

- [ ] **Step 1: 전체 테스트**

Run: `uv run pytest -q`
Expected: 모든 테스트 PASS (기존 39 + 신규 ~5). FAIL 시 해당 task로 복귀.

- [ ] **Step 2: ruff**

Run: `make lint && make fmt`
Expected: ruff 통과 (100 char). 위반 시 수정 후 재실행.

- [ ] **Step 3: 정리 커밋 (변경 있으면)**

```bash
git add -A && git commit -m "chore: ruff format multiseed harness" || echo "nothing to format"
```

---

### Task 6: gen-002 재판정 (새 harness로 공정 재평가)

**Files:**
- Create: `experiments/gen-002/rejudge.md` (재판정 결과 기록)
- Modify: `experiments/gen-002/generation.json` (status 갱신 — Operator 승인 후에만)

- [ ] **Step 1: 새 프로토콜로 baseline vs gen-002 후보 median 측정**

Run:
```bash
cd /Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design
uv run python - <<'PY'
from pathlib import Path
from pipeline.runner import run_candidate_multiseed
import sys; sys.path.insert(0, "src")
DS = Path("experiments/real-gcd-fargate/dataset/dataset.jsonl")
seeds = (0, 1, 2, 3, 4)
targets = {
    "baseline(train.py)": Path("train.py"),
    "cand-000": Path("experiments/gen-002/candidates/cand-000/train.py"),
    "cand-001": Path("experiments/gen-002/candidates/cand-001/train.py"),
}
for name, p in targets.items():
    med, per = run_candidate_multiseed(p, DS, Path("/tmp/rejudge")/name, seeds=seeds)
    print(f"{name:22s} median={med:.4f}  per_seed={[round(v,4) for v in per]}")
PY
```
Expected: 세 줄 출력. baseline median이 가장 낮으면(§1 분석 일치) gen-002는 reject 대상.

- [ ] **Step 2: 결과를 `experiments/gen-002/rejudge.md`에 기록** (관측된 median 표 + 판정)

- [ ] **Step 3: Operator 게이트 — 승격/reject 판단을 Operator에게 보고** (자율 머지 금지, H-B)

승격이면 train.py 교체 + MAE 핀 재핀 + `git tag gen-002-best`.
reject면 `generation.json` status `awaiting_operator`→`rejected`, train.py 불변.
**어느 쪽이든 Operator 명시 승인 후에만 파일 변경/커밋.**

- [ ] **Step 4: INTENT.md Learnings에 negative result 기록** (Operator 승인 후)

co-evolution 신호: "단일 seed selection이 위양성 winner 생성 → median harness로 프로세스 진화".

---

## Self-Review

- **Spec coverage**: D1 median(Task1 Step3), D2 5 seed 기본값(Task1·2·4 시그니처), D3 inf 단락(Task1 test+impl), D4 per-seed 기록(Task4). §3.1~3.4 전부 task 매핑됨. §8 재판정=Task6. ✓
- **Placeholder scan**: 없음 — 모든 코드 step에 실제 코드 포함. ✓
- **Type consistency**: `run_candidate_multiseed`→`(float, list)`, `run_all`→`list[(c, float, list)]`, `select_winner`는 인덱스 1만 사용(무변경), orchestrator는 `for c, v, per_seed in ranking`. 전 task 일관. ✓
- **하위호환 주의**: `run_all`의 `seed` 인자 제거 — 호출처는 orchestrator뿐(seed 미전달)이라 안전. 단일 seed 검증이 필요하면 `seeds=(0,)` 명시. ✓
