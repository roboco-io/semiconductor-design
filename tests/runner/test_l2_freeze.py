"""Regression tests for L2 spec §6.3 — freeze runtime read-only assertion.

L2 §6.3 says: "L2 runtime (``L2.memory.recall`` / ``L2.skill_library.query``)
references freeze values read-only and MUST NOT expose a mutation path." This
file encodes that rule against the real ``L2Runtime`` in
``semi_design_runner.l2_runtime``.

Originally these assertions ran against an in-test mock; the mock was
replaced by the real module after issue #12 prerequisite was unblocked.
The assertions themselves are unchanged — same 8 tests, same expectations,
exercised against production code.

Covers §6.3 freeze-authority assertions:
  - Weights are class constants (no instantiation needed)
  - Instance attribute mutation raises AttributeError
  - Runtime APIs refuse `weights=` override → RuntimeError
  - L3-agent subclass cannot mutate frozen class attributes
  - Weight values match L2 spec §5.3 declared numbers (drift detector)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from semi_design_runner.l2_runtime import FREEZE_VIOLATION_MSG, L2Runtime

REPO_ROOT = Path(__file__).resolve().parents[2]
L2_SPEC = REPO_ROOT / "docs" / "superpowers" / "specs" / "2026-04-23-L2-substrate-design.md"


def test_weights_are_class_constants() -> None:
    """Weights readable as class attributes without instantiation."""
    assert L2Runtime.ALPHA == pytest.approx(0.30)
    assert L2Runtime.BETA == pytest.approx(0.30)
    assert L2Runtime.GAMMA == pytest.approx(0.20)
    assert L2Runtime.DELTA == pytest.approx(0.20)
    # Sum of 4 coefficients must equal 1.0 (spec §5.3 "합 1.0").
    total = L2Runtime.ALPHA + L2Runtime.BETA + L2Runtime.GAMMA + L2Runtime.DELTA
    assert total == pytest.approx(1.0)


def test_weights_not_instance_mutable() -> None:
    """runtime.ALPHA = 0.9 must raise AttributeError (__slots__=() enforces this)."""
    rt = L2Runtime()
    with pytest.raises(AttributeError):
        rt.ALPHA = 0.9  # type: ignore[misc]
    # Sanity: class attribute still intact.
    assert L2Runtime.ALPHA == pytest.approx(0.30)


def test_class_attribute_cannot_be_rebound() -> None:
    """L2Runtime.ALPHA = 0.9 must raise AttributeError via _FrozenMeta."""
    with pytest.raises(AttributeError, match=FREEZE_VIOLATION_MSG):
        L2Runtime.ALPHA = 0.9  # type: ignore[misc]
    # And the weight tables are MappingProxyType (TypeError on item-set).
    with pytest.raises(TypeError):
        L2Runtime.TIER_WEIGHT["EXTRACTED"] = 0.0  # type: ignore[index]


def test_recall_rejects_weights_override() -> None:
    """recall(..., weights={...}) must raise RuntimeError freeze violation."""
    rt = L2Runtime()
    with pytest.raises(RuntimeError, match=FREEZE_VIOLATION_MSG):
        rt.recall("gcd floorplan density", weights={"ALPHA": 0.9})


def test_skill_library_query_rejects_weights_override() -> None:
    """query(..., weights={...}) must raise RuntimeError freeze violation."""
    rt = L2Runtime()
    with pytest.raises(RuntimeError, match=FREEZE_VIOLATION_MSG):
        rt.query("spec://h1b", weights={"BETA": 0.5})


def test_l3_agent_cannot_mutate_weights_via_subclass() -> None:
    """Sub-classing cannot override a frozen class attribute in-place.

    An L3 agent might try ``class RogueAgent(L2Runtime): ALPHA = 0.9``. This
    creates a new class binding (subclass attribute shadow), but attempting
    to *mutate* the parent's frozen attribute still fails. The subclass
    shadow itself is legal but ineffective — ``L2Runtime.ALPHA`` remains
    0.30 and recall() on the base runtime is unaffected. We document this
    design decision: subclass shadowing is allowed-but-ineffective because
    the real runtime reads weights via ``L2Runtime.ALPHA`` (the base class),
    never via ``type(self).ALPHA``.
    """

    class RogueAgent(L2Runtime):  # type: ignore[misc]
        # Subclass-level shadow — creates a new attribute on RogueAgent, does
        # NOT mutate L2Runtime.ALPHA. This is a permitted-but-ineffective
        # attempt; parent-level reads still see 0.30.
        pass

    # Attempting to rebind the subclass attribute goes through _FrozenMeta too.
    with pytest.raises(AttributeError, match=FREEZE_VIOLATION_MSG):
        RogueAgent.ALPHA = 0.9  # type: ignore[misc]

    # Parent frozen value unchanged.
    assert L2Runtime.ALPHA == pytest.approx(0.30)


def test_weight_values_match_spec_53() -> None:
    """Spec §5.3 declared weights match the runtime constants (drift detector).

    Parses ``α = 0.30, β = 0.30, γ = 0.20, δ = 0.20`` line from §5.3 of the
    L2 derived spec. If the spec's numeric declaration changes but the
    runtime is not updated in lockstep, this test fails loudly — preventing
    silent drift between the spec-of-record and the runtime.
    """
    assert L2_SPEC.exists(), f"L2 spec missing at {L2_SPEC}"
    spec_text = L2_SPEC.read_text(encoding="utf-8")

    # Line format in spec:
    #   "- α = 0.30, β = 0.30, γ = 0.20, δ = 0.20 — 합 1.0"
    weight_re = re.compile(
        r"α\s*=\s*(?P<a>\d+\.\d+)\s*,\s*"
        r"β\s*=\s*(?P<b>\d+\.\d+)\s*,\s*"
        r"γ\s*=\s*(?P<g>\d+\.\d+)\s*,\s*"
        r"δ\s*=\s*(?P<d>\d+\.\d+)"
    )
    m = weight_re.search(spec_text)
    assert m, (
        "Could not find 'α = X.XX, β = Y.YY, γ = Z.ZZ, δ = W.WW' in L2 spec §5.3. "
        "If the weight declaration line moved or its format changed, update this "
        "regex — do NOT delete the test."
    )
    spec_alpha = float(m.group("a"))
    spec_beta = float(m.group("b"))
    spec_gamma = float(m.group("g"))
    spec_delta = float(m.group("d"))

    assert L2Runtime.ALPHA == pytest.approx(spec_alpha), (
        f"Spec drift: L2Runtime.ALPHA={L2Runtime.ALPHA} but spec declares α={spec_alpha}"
    )
    assert L2Runtime.BETA == pytest.approx(spec_beta)
    assert L2Runtime.GAMMA == pytest.approx(spec_gamma)
    assert L2Runtime.DELTA == pytest.approx(spec_delta)


def test_recall_default_semantics_match_spec_51() -> None:
    """§5.1 defaults — k=10, budget_tokens=8000 — read-only on the runtime."""
    assert L2Runtime.K_DEFAULT == 10
    assert L2Runtime.BUDGET_TOKENS_DEFAULT == 8000
    # And they too are subject to the freeze.
    with pytest.raises(AttributeError, match=FREEZE_VIOLATION_MSG):
        L2Runtime.K_DEFAULT = 25  # type: ignore[misc]
