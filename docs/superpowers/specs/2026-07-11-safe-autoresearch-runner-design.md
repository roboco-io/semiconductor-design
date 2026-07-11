# Safe AutoResearch Runner Design

## Goal

Close the review findings without changing the frozen dataset or model-comparison contracts:
isolate generated candidate execution, make promotion transactional, run candidates concurrently,
align documentation with reality, and separate fast tests from expensive ML tests.

## Scope and constraints

- Preserve `prepare.py`, dataset schemas, gate thresholds, and the `train.py` CLI contract.
- Preserve untracked experiment and training artifacts.
- Add no mandatory runtime dependency beyond the Python standard library.
- Candidate execution must not use the repository as its working directory or inherit the full host
  environment. This is process isolation, not an OS security boundary; production/untrusted operation
  still requires a container or VM sandbox.
- Existing sequential behavior remains available with concurrency `1`.

## Candidate execution isolation

`pipeline.runner` creates a fresh temporary workspace for each invocation. It copies only the candidate
script and dataset into that workspace, creates the output directory there, runs with that workspace as
`cwd`, and supplies an allowlisted environment (`PATH`, locale, temporary-directory variables, and
Python runtime variables required by `uv`). Artifact output is copied to the requested destination only
after a successful process exit and valid finite `val_mae` result.

The runner rejects non-finite metrics. It also records stderr/stdout in the candidate artifact directory
for diagnosis without echoing secrets to the orchestration console. This prevents accidental relative-path
writes into the repository and limits ambient credential exposure. It does not claim protection against
host-level malicious Python; documentation explicitly requires Docker/VM isolation for untrusted models.

## Concurrent evaluation

`run_all` accepts `max_workers`. Candidate-level evaluations run through `ThreadPoolExecutor`; each
candidate retains sequential seed evaluation so a failed seed short-circuits deterministically. Results
are restored to input order before selection/reporting. The CLI exposes `--max-workers`, with a conservative
default based on candidate count and CPU availability.

Documentation calls this local concurrent execution, not Spot execution. AWS EDA data generation remains
Fargate-based; remote candidate training is not represented as implemented.

## Transactional promotion

Promotion performs preflight checks before changing `train.py`:

1. reject a dirty baseline path;
2. reject any pre-existing staged changes;
3. reject an existing generation tag rather than force-moving it;
4. copy the winner to a temporary sibling file and atomically replace the baseline;
5. stage only the baseline using a pathspec and commit with `--only`;
6. create the immutable generation tag.

If commit or tag creation fails, restore the original baseline and remove any partial commit/tag where it
is safe to do so. `do_git=False` keeps the existing test/in-memory mode and uses atomic replacement only.
Promotion errors propagate, and the orchestrator writes `promotion_failed` rather than claiming success.

## Documentation and test tiers

README, INTENT, PRD, pipeline documentation, and Makefile use one status statement: local candidate
generation/evaluation and the four-stage auto-gate are implemented; remote Spot candidate training is not.
The default `make test` runs the fast suite. Expensive estimator/subprocess tests receive `slow` markers and
run through `make test-all` or `make test-slow`. Existing CDK tests remain separate.

## Testing

Regression tests prove:

- candidate `cwd` is outside the repository and ambient fake credentials are absent;
- invalid/non-finite results do not copy artifacts;
- concurrent evaluation overlaps work and preserves input order;
- staged unrelated files prevent promotion and remain untouched;
- existing tags cannot be moved;
- promotion failure restores the baseline;
- orchestrator reports promotion failure;
- pytest marker selection keeps the default suite fast.

Ruff, the fast Python suite, targeted slow tests, and CDK Jest tests form the completion gate.

## Non-goals

- Building a full hostile-code sandbox without containers/VMs.
- Implementing SageMaker/Spot candidate training.
- Changing scientific gate statistics, encoder decisions, or historical experiment artifacts.
