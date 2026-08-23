# Safe AutoResearch Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Isolate generated candidate runs, make promotion fail-safe, add bounded local concurrency, and align test/documentation claims with the implementation.

**Architecture:** `pipeline.runner` owns temporary-workspace execution and candidate-level concurrency. `pipeline.operator_gate` owns Git preflight and rollback, while the orchestrator converts promotion exceptions into an explicit terminal status. Documentation distinguishes local concurrent evaluation from unimplemented remote Spot training.

**Tech Stack:** Python 3.12 standard library, pytest, Click, Git CLI, Ruff, Make, CDK/Jest.

## Global Constraints

- Preserve `prepare.py`, dataset schemas, gate thresholds, and the `train.py` CLI contract.
- Preserve all pre-existing untracked experiment and training artifacts.
- Add no mandatory runtime dependency beyond the Python standard library.
- Do not claim the process workspace is a hostile-code security boundary.
- Follow test-first RED → GREEN for every behavior change.

---

### Task 1: Isolated Candidate Execution

**Files:**
- Modify: `src/pipeline/runner.py`
- Modify: `tests/pipeline/test_runner.py`

**Interfaces:**
- Preserve: `run_candidate(train_py: Path, dataset: Path, out_dir: Path, seed: int = 0, timeout: int = 300) -> float`
- Produce: private `_safe_env(tmpdir: Path) -> dict[str, str]`

- [ ] **Step 1: Write failing isolation and finite-result tests**

Add tests whose candidate writes `Path.cwd()` and selected environment keys into its output model file. Assert the observed cwd is not the repository/candidate source directory, `AWS_SECRET_ACCESS_KEY` is absent, a successful artifact is copied to `out_dir`, and `NaN`/`Infinity` metrics return `inf` without publishing artifacts.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/pipeline/test_runner.py -k 'isolated or non_finite' -v`

Expected: FAIL because the current subprocess inherits cwd/environment and accepts non-finite floats.

- [ ] **Step 3: Implement the isolated workspace**

Use `tempfile.TemporaryDirectory`, `shutil.copy2/copytree`, `cwd=workspace`, and an environment allowlist containing only `PATH`, locale, temp, and required Python variables. Parse a finite `val_mae` with `math.isfinite`; copy the temporary artifact directory to the requested destination only on success. Persist captured stdout/stderr as diagnostic files in successful artifacts.

- [ ] **Step 4: Verify GREEN and regression**

Run: `uv run pytest tests/pipeline/test_runner.py -v`

Expected: all runner tests pass.

### Task 2: Bounded Candidate Concurrency

**Files:**
- Modify: `src/pipeline/runner.py`
- Modify: `src/pipeline/orchestrator.py`
- Modify: `tests/pipeline/test_runner.py`
- Modify: `tests/pipeline/test_orchestrator.py`

**Interfaces:**
- Change: `run_all(candidates, dataset: Path, out_root: Path, seeds=(...), max_workers: int = 1)`
- Change: `run_generation(..., max_workers=1, ...)`
- Add CLI option: `--max-workers`, integer greater than zero.

- [ ] **Step 1: Write failing concurrency tests**

Monkeypatch `run_candidate_multiseed` with a barrier-controlled function. Assert two candidates overlap when `max_workers=2`, returned results retain input order, `max_workers=1` remains sequential, and CLI rejects zero.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/pipeline/test_runner.py tests/pipeline/test_orchestrator.py -k 'workers or concurrent' -v`

Expected: FAIL because `max_workers` is not accepted.

- [ ] **Step 3: Implement bounded concurrency**

Use `ThreadPoolExecutor(max_workers=max_workers)` at candidate granularity. Store each future's input index and reconstruct results in input order. Validate `max_workers >= 1`; pass the value through `run_generation` and Click.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/pipeline/test_runner.py tests/pipeline/test_orchestrator.py -v`

Expected: all targeted tests pass.

### Task 3: Transactional Git Promotion

**Files:**
- Modify: `src/pipeline/operator_gate.py`
- Modify: `tests/pipeline/test_operator_gate.py`

**Interfaces:**
- Preserve: `promote(winner_src: Path, baseline: Path, gen_no: int, approved: bool, do_git: bool = True) -> bool`
- Produce: `PromotionError(RuntimeError)` for failed preflight or rollback-safe Git operations.

- [ ] **Step 1: Write failing Git safety tests**

Create temporary Git repositories and assert promotion rejects a dirty baseline, any staged unrelated file, and an existing `gen-NNN-best` tag. Inject a failing Git command after atomic baseline replacement and assert the original baseline content and HEAD are restored. Assert `do_git=False` still atomically replaces only the baseline.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/pipeline/test_operator_gate.py -v`

Expected: FAIL because current promotion force-moves tags, includes staged files, and lacks rollback.

- [ ] **Step 3: Implement preflight, atomic replacement, and rollback**

Resolve repository root with `git rev-parse --show-toplevel`. Check `git diff --quiet -- baseline`, `git diff --cached --quiet`, and `git rev-parse --verify refs/tags/<tag>`. Save original bytes and HEAD, atomically replace via a sibling `NamedTemporaryFile` plus `os.replace`, commit with `git commit --only -- baseline`, then create a non-forced tag. On failure, restore bytes atomically; if a new commit was created, reset only that commit with `git reset --soft <old-head>` followed by unstage/restore of the baseline, then raise `PromotionError`.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/pipeline/test_operator_gate.py -v`

Expected: all promotion tests pass.

### Task 4: Explicit Promotion Failure State

**Files:**
- Modify: `src/pipeline/orchestrator.py`
- Modify: `tests/pipeline/test_orchestrator.py`

**Interfaces:**
- Consume: `operator_gate.PromotionError`
- Produce generation status: `promotion_failed`; include `promotion_error` in `generation.json`.

- [ ] **Step 1: Write failing orchestrator test**

Monkeypatch `operator_gate.promote` to raise `PromotionError("tag exists")`. Drive LODO, T1, and reviewer mocks through approval. Assert the run returns normally, baseline is unchanged, and `generation.json` records `promotion_failed` plus the error message.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -k promotion_failed -v`

Expected: FAIL because the exception currently escapes and no generation record is written.

- [ ] **Step 3: Implement failure-state handling**

Catch only `PromotionError` around promotion, set the explicit status/error, continue report and generation metadata emission, and never label the candidate promoted.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -v`

Expected: all orchestrator tests pass.

### Task 5: Fast and Slow Test Tiers

**Files:**
- Modify: `pyproject.toml`
- Modify: `Makefile`
- Modify: expensive test modules identified with `uv run pytest --durations=25`
- Modify: `tests/README.md`

**Interfaces:**
- `make test`: `pytest -m 'not slow'`
- `make test-slow`: `pytest -m slow`
- `make test-all`: complete pytest suite.

- [ ] **Step 1: Measure and identify slow tests**

Run: `uv run pytest --durations=25 -q`

Expected: obtain concrete duration evidence; interrupt only if a single test exceeds five minutes and record it as slow.

- [ ] **Step 2: Add marker configuration and test targets**

Register `slow: estimator training or repeated subprocess/model evaluation`, mark only measured expensive modules/tests, and add Make targets with the exact selection expressions above.

- [ ] **Step 3: Verify both tiers collect correctly**

Run: `uv run pytest --collect-only -q -m 'not slow'` and `uv run pytest --collect-only -q -m slow`

Expected: both selections are non-empty and their union equals `uv run pytest --collect-only -q`.

### Task 6: Documentation Reconciliation

**Files:**
- Modify: `README.md`
- Modify: `INTENT.md`
- Modify: `PRD.md`
- Modify: `src/pipeline/README.md`
- Modify: `Makefile`

**Interfaces:** None; documentation must describe implemented behavior exactly.

- [ ] **Step 1: Inventory contradictory claims**

Run: `rg -n 'Spot|병렬|전환 중|미구현|skeleton|awaiting_operator|자동 승격' README.md INTENT.md PRD.md src/pipeline/README.md Makefile`

Expected: list every status statement to reconcile.

- [ ] **Step 2: Update status and safety language**

State that candidate evaluation is bounded local concurrency; AWS Fargate generates EDA datasets; remote Spot candidate training is not implemented. State that `--auto` enables the four-stage gate while default mode remains manual. Document process-workspace isolation as defense-in-depth and require container/VM execution for hostile candidates. Remove obsolete skeleton and auto-gate-transition text.

- [ ] **Step 3: Verify contradiction scan**

Re-run the inventory command and manually confirm remaining occurrences are historical records or explicit non-implementation statements.

### Task 7: Full Verification

**Files:** No production edits expected.

- [ ] **Step 1: Run static checks**

Run: `make lint`

Expected: exit 0.

- [ ] **Step 2: Run fast tests**

Run: `make test`

Expected: exit 0 with zero failures.

- [ ] **Step 3: Run slow tests**

Run: `make test-slow`

Expected: exit 0 with zero failures.

- [ ] **Step 4: Run CDK tests**

Run: `cd cdk && npm test -- --runInBand`

Expected: 4 tests pass.

- [ ] **Step 5: Inspect scope and whitespace**

Run: `git diff --check`, `git status --short`, and `git diff --stat`.

Expected: no whitespace errors; only planned source, test, and documentation changes plus the user's pre-existing untracked artifacts.
