# auto-gate + Codex 승격 심사관 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 자율 진화 루프가 winner를 **median → T1 통계 게이트 → Codex 심사관**(AND)으로 자동 판정해, 통과 시 무인 commit/tag로 승격하고 튜토리얼식 리포트를 남긴다.

**Architecture:** `validation.py`를 정직하게 보강(T1-fix), 신규 `promotion_reviewer.py`(주입형 Codex 심사)·`report.py`(순수 리포트 렌더)를 추가하고, `orchestrator.run_generation`에 `auto`/`gate_fn`/`reviewer_fn` 주입형 자동 승격 경로를 통합한다. `operator_gate.promote`를 재사용해 git 실행. 생성≠판정≠심사의 권력분립. `train.py`·`prepare.py`·`dataset` frozen 무변경.

**Tech Stack:** Python 3.12, 기존 `pipeline.validation`/`operator_gate`/`runner`, subprocess(codex CLI, sdk 패턴), pytest/ruff.

**Spec:** `docs/superpowers/specs/2026-06-08-autogate-codex-promotion-reviewer-design.md`

**핵심 계약(확인됨):**
- `validation.run_validation_gate(winner_train_py, baseline_train_py, rows, workdir, k=5, repeats=10, base_seed=0, n_boot=10000) -> dict` — `verdict_vs_baseline ∈ {distinguishable, indistinguishable, worse}`.
- `validation.render_validation_report(res) -> str`.
- `operator_gate.promote(winner_src, baseline, gen_no, approved, do_git=True) -> bool` — approved=True일 때만 `shutil.copyfile` + git add/commit/tag.
- `candidate_gen.Candidate`: `.id .strategy .sdk .src_path .patch_ref`.
- `sdk.py` 패턴: `subprocess.run(["codex","exec","--skip-git-repo-check", prompt], capture_output=True, text=True, timeout=900)`.

---

### Task 1: T1-fix — paired_comparison 길이 assert + 리포트 caveat + 서술 정정

**Files:**
- Modify: `src/pipeline/validation.py`
- Test: `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_validation.py` 끝에 추가

```python
import pytest
from pipeline.validation import paired_comparison, render_validation_report


def test_paired_comparison_length_mismatch_raises():
    with pytest.raises(ValueError):
        paired_comparison([0.1, 0.2, 0.3], [0.1, 0.2], n_boot=100, seed=0)


def test_report_has_statistical_dependence_caveat():
    res = {
        "winner_folds": [0.10, 0.11], "baseline_folds": [0.12, 0.13],
        "naive_folds": [1.40, 1.42], "n_failed_winner": 0, "n_failed_baseline": 0,
        "n_folds": 2, "single_design": True,
        "winner_vs_baseline": {"mean_diff": -0.02, "ci_low": -0.03, "ci_high": -0.01,
                               "wilcoxon_p": 0.04, "effect_size": -1.2, "n_valid": 2},
        "winner_vs_naive": {"mean_diff": -1.30, "ci_low": -1.35, "ci_high": -1.25,
                            "wilcoxon_p": 0.04, "effect_size": -8.0, "n_valid": 2},
        "verdict_vs_baseline": "distinguishable",
    }
    md = render_validation_report(res)
    assert "상관" in md and ("낙관" in md or "과신" in md)  # 반복 fold 상관 → CI 낙관 caveat
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k "length_mismatch or dependence_caveat" -v`
Expected: FAIL (assert 없음 / 예외 미발생)

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`

`paired_comparison` 함수 본문 첫 줄에 길이 검증 추가:
```python
def paired_comparison(a: list[float], b: list[float], n_boot: int = 10000, seed: int = 0) -> dict:
    if len(a) != len(b):
        raise ValueError(f"paired_comparison: 길이 불일치 a={len(a)} b={len(b)}")
    diffs = np.array([x - y for x, y in zip(a, b)], dtype=float)
    ...  # (이하 기존 본문 유지)
```

`candidate_fold_maes` docstring을 정정(frozen train.py 내부분할 명시):
```python
def candidate_fold_maes(train_py, rows: list[dict], splits, workdir: Path) -> list[float]:
    """후보 train.py를 각 fold의 train으로 학습하고, 같은 fold의 val에서 paired MAE를 잰다.

    주의(정직한 서술): train.py(frozen)는 받은 fold-train을 *다시* 내부 0.75 분할하므로 모델은
    fold-train 100%가 아닌 ~75%로 학습된다. 즉 clean K-fold가 아니라 train.py 내부분할을 포함한
    nested resampling이다. fold-val은 train.py가 전혀 보지 않은 완전 held-out이라 paired 비교는 유효.
    train.py가 어떤 fold에서 실패하면 그 fold MAE = inf.
    """
```

`render_validation_report`의 단일설계 경고 블록 바로 앞(또는 뒤)에 통계 caveat 한 줄 추가:
```python
    L.append("> ⚠️ 반복 K-fold는 train/val 중첩으로 fold 점수들이 **상관**된다 — bootstrap CI·Wilcoxon p는")
    L.append("> 독립 표본 가정보다 **낙관적**(불확실성 과소평가)일 수 있다. verdict는 보수적으로 해석.")
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -v`
Expected: 모든 validation 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "fix(validation): paired 길이 assert + 통계 상관 caveat + nested resampling 정직 서술 (T1-fix)"
```

---

### Task 2: promotion_reviewer.py — Codex 심사 (주입형)

**Files:**
- Create: `src/pipeline/promotion_reviewer.py`
- Test: `tests/pipeline/test_promotion_reviewer.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_promotion_reviewer.py`

```python
# tests/pipeline/test_promotion_reviewer.py
from pipeline.promotion_reviewer import build_review_prompt, review_promotion


def test_prompt_includes_winner_and_report():
    p = build_review_prompt("WINNER_SRC_X", "BASELINE_SRC_Y", "T1_REPORT_Z")
    assert "WINNER_SRC_X" in p and "BASELINE_SRC_Y" in p and "T1_REPORT_Z" in p
    assert "approve" in p  # JSON 출력 계약 안내


def test_review_approve():
    def fake(prompt):
        return '결론: {"approve": true, "reasons": "계약 준수, 누수 없음"}'
    out = review_promotion("w", "b", "r", reviewer_fn=fake)
    assert out["approve"] is True and "누수" in out["reasons"]


def test_review_block():
    def fake(prompt):
        return '{"approve": false, "reasons": "synth_slack를 라벨로 누수"}'
    out = review_promotion("w", "b", "r", reviewer_fn=fake)
    assert out["approve"] is False


def test_review_failure_is_block():
    def boom(prompt):
        raise RuntimeError("codex timeout")
    out = review_promotion("w", "b", "r", reviewer_fn=boom)
    assert out["approve"] is False and "실패" in out["reasons"]


def test_review_unparseable_is_block():
    def fake(prompt):
        return "그냥 산문, JSON 없음"
    out = review_promotion("w", "b", "r", reviewer_fn=fake)
    assert out["approve"] is False
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_promotion_reviewer.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: 구현** — `src/pipeline/promotion_reviewer.py`

```python
"""promotion_reviewer — Codex 승격 심사관 (자율 게이트의 소프트 게이트).

생성≠판정(T1)≠심사(Codex) 권력분립. 무결성·안전 + 품질을 심사해 승격을 막을 수 있다.
실패=block(보수적). reviewer_fn 주입형 — 테스트는 mock, 실제는 sdk.codex_review_fn.
설계: docs/superpowers/specs/2026-06-08-autogate-codex-promotion-reviewer-design.md
"""

from __future__ import annotations

import json
import re

_JSON = re.compile(r"\{.*?\"approve\".*?\}", re.DOTALL)


def build_review_prompt(winner_src: str, baseline_src: str, validation_report: str) -> str:
    return (
        "너는 AutoResearch EDA surrogate 루프의 **승격 심사관**이다. 아래 winner train.py를 baseline "
        "대비 승격할지 심사하라. 통계적 우열은 T1 리포트가 이미 판정했다 — 너는 통계가 못 잡는 것을 본다.\n"
        "차단 사유(하나라도 해당 시 approve=false): 데이터 누수(label·미래정보 사용) · frozen 계약 위반"
        "(단일 파일/신규 의존성/`--data,--out,--seed` CLI·8 FEATURE_NAMES·stdout {\"val_mae\"} 변경) · "
        "metric gaming(val만 좋게 하는 꼼수) · 수상한 side-effect(파일/네트워크) · 과적합 징후 · 개선이 "
        "타당하지 않음.\n"
        "출력: 설명 후 **마지막 줄에 JSON 한 줄** `{\"approve\": <bool>, \"reasons\": \"<간결한 근거>\"}`.\n\n"
        f"=== T1 검증 리포트 ===\n{validation_report}\n\n"
        f"=== baseline train.py ===\n{baseline_src}\n\n"
        f"=== winner train.py ===\n{winner_src}\n"
    )


def review_promotion(winner_src, baseline_src, validation_report, *, reviewer_fn) -> dict:
    """reviewer_fn(prompt)->raw text. JSON {approve,reasons} 파싱. 실패/미파싱=block."""
    prompt = build_review_prompt(winner_src, baseline_src, validation_report)
    try:
        raw = reviewer_fn(prompt)
    except Exception as e:  # noqa: BLE001 — 어떤 실패든 보수적 block
        return {"approve": False, "reasons": f"Codex 심사 실패: {e}"}
    m = _JSON.search(raw or "")
    if not m:
        return {"approve": False, "reasons": "Codex 심사 응답에서 JSON 미발견 — block(보수적)"}
    try:
        obj = json.loads(m.group(0))
    except ValueError:
        return {"approve": False, "reasons": "Codex 심사 JSON 파싱 실패 — block(보수적)"}
    return {"approve": bool(obj.get("approve", False)), "reasons": str(obj.get("reasons", ""))}
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_promotion_reviewer.py -v`
Expected: 5 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/promotion_reviewer.py tests/pipeline/test_promotion_reviewer.py
git commit -m "feat(promotion_reviewer): Codex 승격 심사관 — 주입형, 실패=block"
```

---

### Task 3: report.py — 튜토리얼식 generation 리포트 (순수)

**Files:**
- Create: `src/pipeline/report.py`
- Test: `tests/pipeline/test_report.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_report.py`

```python
# tests/pipeline/test_report.py
from pipeline.report import render_generation_report


def test_report_contains_all_sections():
    md = render_generation_report(
        gen_no=3,
        ranking=[("cand-001", "codex", "moderate", 0.099), ("cand-000", "claude", "conservative", 0.102)],
        winner_id="cand-001",
        t1_report="T1: verdict distinguishable",
        codex_verdict={"approve": True, "reasons": "계약 준수"},
        decision="promoted",
    )
    assert "gen-003" in md or "003" in md
    assert "cand-001" in md and "cand-000" in md       # 후보 순위
    assert "distinguishable" in md                       # T1
    assert "계약 준수" in md                              # Codex 사유
    assert "promoted" in md                              # 결정
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_report.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: 구현** — `src/pipeline/report.py`

```python
"""report — 세대 튜토리얼식 리포트 (이해가능성 산출물). 순수 함수.

INTENT 품질기준: 비전문가가 각 세대의 큰 흐름을 따라갈 수 있어야 한다.
"""

from __future__ import annotations


def render_generation_report(gen_no, ranking, winner_id, t1_report, codex_verdict, decision) -> str:
    """ranking: [(id, sdk, strategy, median_val_mae), ...] (낮을수록 좋음, 정렬됨)."""
    L = [f"# gen-{gen_no:03d} 리포트 (자율 승격 게이트)", ""]
    L.append(f"**최종 결정: {decision}**  ·  winner: `{winner_id}`")
    L.append("")
    L.append("## 1) 후보 순위 (median val_mae, 낮을수록 좋음)")
    L.append("| 후보 | sdk | 전략 | median_val_mae |")
    L.append("|---|---|---|---|")
    for cid, sdk, strat, mae in ranking:
        mark = " ⭐" if cid == winner_id else ""
        L.append(f"| {cid}{mark} | {sdk} | {strat} | {mae:.4f} |")
    L.append("")
    L.append("## 2) T1 통계 게이트 (winner vs 현 baseline)")
    L.append(t1_report)
    L.append("")
    L.append("## 3) Codex 승격 심사관 (무결성·안전·품질)")
    L.append(f"- approve: **{codex_verdict.get('approve')}**")
    L.append(f"- 사유: {codex_verdict.get('reasons', '')}")
    L.append("")
    L.append("## 4) 승격 규칙")
    L.append("median 선택 → T1 `distinguishable` **AND** Codex `approve` → 자동 승격(train.py·tag).")
    L.append("사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗).")
    return "\n".join(L)
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_report.py -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/report.py tests/pipeline/test_report.py
git commit -m "feat(report): 세대 튜토리얼식 리포트 렌더 (이해가능성 산출물)"
```

---

### Task 4: orchestrator auto-gate 통합 (T1 ∧ Codex AND)

**Files:**
- Modify: `src/pipeline/orchestrator.py` (`run_generation`)
- Test: `tests/pipeline/test_orchestrator.py`

먼저 **현재 `run_generation`을 읽어** 실제 시그니처/본문을 확인하라(아래는 통합 후 목표). 기존 results.tsv·generation.json 작성 로직은 보존하고, select_winner 다음에 auto-gate 블록을 끼운다.

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_orchestrator.py` 끝에 추가 (기존 `_mock_gen`·`_dataset`·`REPO` 재사용)

```python
import shutil


def _stub_gate(verdict):
    def gate(winner_train_py, baseline_train_py, rows, workdir, **kw):
        return {"verdict_vs_baseline": verdict, "winner_folds": [0.1], "baseline_folds": [0.1],
                "naive_folds": [1.4], "n_failed_winner": 0, "n_failed_baseline": 0, "n_folds": 1,
                "single_design": True, "winner_vs_baseline": None, "winner_vs_naive": None}
    return gate


def _tmp_baseline(tmp_path):
    # 실제 train.py를 건드리지 않도록 tmp 복사본을 baseline으로 사용 (promote가 이걸 덮어씀).
    b = tmp_path / "baseline_train.py"
    shutil.copyfile(REPO / "train.py", b)
    return b


def test_auto_gate_promoted(tmp_path):
    baseline = _tmp_baseline(tmp_path)
    run_generation(
        gen_no=3, dataset=_dataset(tmp_path), baseline_train_py=baseline,
        program_md="opt", n=2, gen_fn=_mock_gen, out_root=tmp_path / "g",
        auto=True, gate_fn=_stub_gate("distinguishable"),
        reviewer_fn=lambda prompt: '{"approve": true, "reasons": "ok"}',
        do_git=False,
    )
    gen = json.loads((tmp_path / "g" / "gen-003" / "generation.json").read_text())
    assert gen["status"] == "promoted"
    assert (tmp_path / "g" / "gen-003" / "report.md").exists()


def test_auto_gate_rejected_codex(tmp_path):
    baseline = _tmp_baseline(tmp_path)
    before = baseline.read_bytes()
    run_generation(
        gen_no=3, dataset=_dataset(tmp_path), baseline_train_py=baseline,
        program_md="opt", n=2, gen_fn=_mock_gen, out_root=tmp_path / "g2",
        auto=True, gate_fn=_stub_gate("distinguishable"),
        reviewer_fn=lambda prompt: '{"approve": false, "reasons": "누수 의심"}',
        do_git=False,
    )
    gen = json.loads((tmp_path / "g2" / "gen-003" / "generation.json").read_text())
    assert gen["status"] == "rejected_codex"
    assert baseline.read_bytes() == before  # 승격 안 됨 → baseline 불변


def test_auto_gate_rejected_t1(tmp_path):
    calls = []
    run_generation(
        gen_no=3, dataset=_dataset(tmp_path), baseline_train_py=_tmp_baseline(tmp_path),
        program_md="opt", n=2, gen_fn=_mock_gen, out_root=tmp_path / "g3",
        auto=True, gate_fn=_stub_gate("indistinguishable"),
        reviewer_fn=lambda prompt: calls.append(1) or '{"approve": true, "reasons": "x"}',
        do_git=False,
    )
    gen = json.loads((tmp_path / "g3" / "gen-003" / "generation.json").read_text())
    assert gen["status"] == "rejected_t1"
    assert calls == []  # T1 미달 → Codex 미호출


def test_auto_false_keeps_awaiting_operator(tmp_path):
    run_generation(
        gen_no=1, dataset=_dataset(tmp_path), baseline_train_py=_tmp_baseline(tmp_path),
        program_md="opt", n=2, gen_fn=_mock_gen, out_root=tmp_path / "g4", auto=False,
    )
    gen = json.loads((tmp_path / "g4" / "gen-001" / "generation.json").read_text())
    assert gen["status"] == "awaiting_operator"
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -k "auto_gate or auto_false" -v`
Expected: FAIL — `run_generation() got an unexpected keyword argument 'auto'`

- [ ] **Step 3: 구현** — `run_generation`에 import + 파라미터 + auto-gate 블록 추가

orchestrator.py 상단 import에 추가:
```python
from pipeline import operator_gate
from pipeline.promotion_reviewer import review_promotion
from pipeline.report import render_generation_report
from pipeline.validation import render_validation_report, run_validation_gate
```

시그니처 확장(기존 파라미터 뒤에 keyword-only 추가):
```python
def run_generation(gen_no, dataset, baseline_train_py, program_md, n, gen_fn, out_root,
                   seeds=(0, 1, 2, 3, 4), *, auto=False, gate_fn=None, reviewer_fn=None,
                   do_git=True):
```

`select_winner` 및 results.tsv 작성 이후, `generation` dict의 `status`를 결정하는 부분을 다음 블록으로 교체(기존 status="awaiting_operator" 고정 대신):
```python
    status = "awaiting_operator"
    if auto and winner is not None:
        import json as _json
        rows = [_json.loads(line) for line in Path(dataset).read_text().splitlines() if line.strip()]
        gate = gate_fn or run_validation_gate
        t1 = gate(Path(winner.src_path), Path(baseline_train_py), rows, gdir / "t1")
        t1_report = render_validation_report(t1)
        verdict = t1.get("verdict_vs_baseline")
        codex_verdict = {"approve": False, "reasons": "T1 미통과 — 심사 생략"}
        if verdict == "distinguishable":
            winner_src = Path(winner.src_path).read_text(encoding="utf-8")
            baseline_src_now = Path(baseline_train_py).read_text(encoding="utf-8")
            rfn = reviewer_fn
            if rfn is None:
                from pipeline.sdk import codex_review_fn as rfn  # 실제 Codex (비용)
            codex_verdict = review_promotion(winner_src, baseline_src_now, t1_report, reviewer_fn=rfn)
            if codex_verdict["approve"]:
                operator_gate.promote(Path(winner.src_path), Path(baseline_train_py), gen_no,
                                      approved=True, do_git=do_git)
                status = "promoted"
            else:
                status = "rejected_codex"
        else:
            status = "rejected_t1"
        report_md = render_generation_report(
            gen_no,
            [(c.id, c.sdk, c.strategy, v) for c, v, _ps in ranking],
            winner.id, t1_report, codex_verdict, status,
        )
        (gdir / "report.md").write_text(report_md, encoding="utf-8")
```

그리고 `generation` dict의 `"status": "awaiting_operator"`를 `"status": status`로 바꾼다.

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_orchestrator.py -v`
Expected: 모든 orchestrator 테스트 PASS (기존 + 신규 4)

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/orchestrator.py tests/pipeline/test_orchestrator.py
git commit -m "feat(orchestrator): auto-gate 통합 — T1 ∧ Codex AND 자동 승격 + report.md"
```

---

### Task 5: 실제 Codex 심사 함수 wiring (sdk.py) + orchestrator CLI

**Files:**
- Modify: `src/pipeline/sdk.py` (codex_review_fn 추가)
- Modify: `src/pipeline/orchestrator.py` (CLI main: --auto 플래그)
- Test: 없음 (sdk는 테스트가 import 안 함 — 기존 규약)

- [ ] **Step 1: `sdk.py`에 codex_review_fn 추가**

```python
def codex_review_fn(prompt: str) -> str:
    """승격 심사 prompt를 Codex CLI로 보내 raw 응답을 반환 (비용). 실패 시 빈 문자열 → reviewer가 block."""
    try:
        proc = subprocess.run(
            ["codex", "exec", "--skip-git-repo-check", prompt],
            capture_output=True, text=True, timeout=900,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""
    return proc.stdout if proc.returncode == 0 else ""
```

- [ ] **Step 2: orchestrator CLI에 `--auto` 옵션 추가** — `main`의 click 옵션과 `run_generation` 호출에 `auto` 전달

```python
@click.option("--auto", is_flag=True, default=False, help="자동 승격 게이트(median+T1+Codex) 활성")
def main(gen_no, dataset, n, out_root, program_md, auto):
    ...
    res = run_generation(gen_no, dataset, baseline, Path(program_md).read_text(),
                         n, claude_codex_gen_fn, out_root, auto=auto)
    ...
```
(기존 main 본문을 읽고 `--auto`만 추가; reviewer_fn은 None → sdk.codex_review_fn 사용.)

- [ ] **Step 3: 게이트 — 전체 테스트 green**

Run: `uv run pytest -q`
Expected: 모든 테스트 PASS (기존 59 + 신규 ~14).

- [ ] **Step 4: 커밋**

```bash
git add src/pipeline/sdk.py src/pipeline/orchestrator.py
git commit -m "feat(sdk): codex_review_fn + orchestrator --auto CLI 플래그"
```

---

### Task 6: doc 정합 cleanup (번들 tidy)

**Files:**
- Modify: `program.md`, `PRD.md`, `src/pipeline/README.md`, `docs/TUTORIAL.md`

- [ ] **Step 1: `program.md`** — "winner 선택·머지는 항상 사람" 류 문구를 자동 게이트로 정정

`program.md`의 Operator 감독 문단을 읽고, winner 승격이 **자동 게이트(median + T1 + Codex 심사관)** 로 판정됨을 반영. 에이전트는 여전히 *생성*만 담당.

- [ ] **Step 2: `PRD.md`** — prepare.py placeholder 정정

`PRD.md`에서 prepare.py를 "placeholder/미구현"으로 표기한 행(§9 구현표 등)을 "구현됨(frozen)"으로 정정.

- [ ] **Step 3: `src/pipeline/README.md`** — skeleton·없는 모듈 제거

존재하지 않는 `batch_launcher`/`result_collector` 언급 제거, 실제 모듈
(candidate_gen·runner·selection·holdout·operator_gate·orchestrator·validation·promotion_reviewer·report) 반영.

- [ ] **Step 4: `docs/TUTORIAL.md` 모델 설명 정정** — §2

```
구체적으로 **sklearn의 Gradient Boosting**(결정 트리 여러 개를 합치는 방법)을 씁니다.
```
를 다음으로:
```
구체적으로 **sklearn 트리 앙상블**(현재 baseline = `VotingRegressor`로 HistGradientBoosting +
ExtraTrees를 투표 결합)을 씁니다.
```

- [ ] **Step 5: 게이트 + 커밋**

Run: `uv run pytest -q`  (문서만 — green 유지 확인)
```bash
git add program.md PRD.md src/pipeline/README.md docs/TUTORIAL.md
git commit -m "docs: 코드-문서 정합 cleanup (program/PRD/pipeline README/TUTORIAL 모델설명)"
```

---

### Task 7: 전체 회귀 + ruff

- [ ] **Step 1: 전체 테스트**

Run: `uv run pytest -q`
Expected: 모든 테스트 PASS.

- [ ] **Step 2: ruff**

Run: `make lint && make fmt`
Expected: 통과. `make fmt`가 frozen 파일(train.py/prepare.py/src/prepare_lib) 재포맷 시 `git restore` 후 in-scope만 커밋.

- [ ] **Step 3: 정리 커밋(있으면)**

```bash
git add src/pipeline tests/pipeline && git commit -m "chore: ruff format auto-gate 모듈" || echo "nothing to format"
```

---

## Self-Review

- **Spec coverage**: D1 자동판정(Task4) · D2 AND 게이트(Task4: distinguishable ∧ approve) · D3 Codex 심사(Task2) · D4 무결성+품질 차단(Task2 프롬프트) · D5 완전무인 git(Task4 promote) · D6 실패=block(Task2 test_review_failure) · D7 T1-fix 재서술+견고성(Task1) · D8 튜토리얼식 리포트(Task3·Task4 report.md). doc cleanup §3.4=Task6. ✓
- **Placeholder scan**: 없음 — 모든 코드 step에 실제 코드. Task4/Task5/Task6는 "현재 파일을 읽고 통합/정정"을 명시(기존 본문 보존 위함)하되 삽입 코드는 전량 제공. ✓
- **Type consistency**: `review_promotion(...,reviewer_fn=)->{"approve","reasons"}`, `reviewer_fn(prompt)->str`, `run_validation_gate(...)->dict[verdict_vs_baseline]`, `render_generation_report(gen_no, ranking[(id,sdk,strat,mae)], winner_id, t1_report, codex_verdict, decision)->str`, orchestrator가 `(c.id,c.sdk,c.strategy,v)`로 ranking 변환 — 일관. `promote(winner_src, baseline, gen_no, approved, do_git)` 기존 시그니처 일치. ✓
- **frozen 주의**: validation은 읽기·임시분할만; Task7 ruff가 frozen 건드리면 restore. train.py/prepare.py/dataset 무변경. ✓
- **테스트 격리**: auto_gate_promoted 테스트가 실제 baseline(train.py)을 덮어쓰므로 `do_git=False` + read_bytes/write_bytes로 원복. (실데이터 미사용, tmp_path dataset.) ✓
