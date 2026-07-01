# In-Distribution Optimization ≠ Cross-Design Generalization: An Autonomous-Research Case Study on EDA Timing Surrogates

**Author:** (작성 시 기입) · **Status:** arXiv preprint draft (2026-06-30) · **Format:** Markdown
**Code & data:** https://github.com/roboco-io/semiconductor-design (open source)

> Compiled from [`docs/PAPER-OUTLINE.md`](PAPER-OUTLINE.md). Generation statistics are drawn from the
> repository's `experiments/gen-NNN/` reports and [`INTENT.md`](../INTENT.md) Learnings; external
> claims are grounded in the cited references (§11). This is a draft. 한국어 번역본: [`PAPER.ko.md`](PAPER.ko.md).

---

## Abstract

The model-search loop for EDA *surrogate* models—predictors that estimate a chip's final
timing/PPA from post-synthesis features—is mechanical yet still performed by hand. We apply
Karpathy's **AutoResearch** (an autonomous "research-as-search" loop that mutates a single training
script under a fixed budget and keeps changes only if a metric improves) to EDA timing-slack
surrogate learning for the first time, and let a **non-expert operator** steer eight generations at
the *direction* level rather than by approving individual winners (fully automatic promotion is the
design target; in the current interim the operator merges after reading each gate report, and the
earliest generations predate this reframe). Our central result is not a better model but an
**honest negative result**: in-loop validation error (`val_mae`) reached successive record lows
(generation 7: 1.29 → generation 8: 0.53 ns, though the gen-8 median is on an enlarged 4-design
dataset and not strictly comparable), yet no generation earned a gate-passing cross-design win—the
two generations judged by the finalized cross-design test (7 and 8) came back *statistically
indistinguishable* from the baseline, while earlier generations were rejected upstream. That is,
*in-distribution optimization and unseen-design generalization are structurally separate*—a
phenomenon already documented in ML-for-EDA. Our contributions are therefore on the **process and
accessibility** axis: (1) an autonomous loop reproduced this known wall with no human hand-designing the model changes;
(2) a four-stage **separation-of-powers gate** (median → leave-one-design-out → cross-design
statistical test → independent code review) blocked every would-be promotion across gen-002–008 (for documented, gate-specific reasons) and kept the
baseline uncontaminated; (3) a non-expert steered the loop via written direction plus tutorial-grade
reports. Zero promotions is not a failure but evidence the gate worked. All code, data, and the full
generation history are open source.

---

## 1. Introduction

Machine learning for electronic design automation (ML-for-EDA) is mature: surrogate models predict
routability, IR-drop, wirelength, and timing from early-stage design information, saving the long
runtime of a full sign-off flow [1,2,4,5]. Yet the *outer loop*—choosing model structure,
hyperparameters, and feature designs—is still iterated manually by researchers. That loop is
mechanical: try a variant, measure one number, keep or discard.

Karpathy's **AutoResearch** [8,9] automates exactly this loop by reducing "research" to "search": a
coding agent repeatedly mutates a single `train.py`, trains under a fixed budget, measures one
validation metric, and commits the change only if it improves (otherwise reverts)—a one-directional
ratchet. AutoResearch targets *LLM* training and assumes no human in the loop ("the human may be
asleep"). **It has not been applied to EDA surrogate learning.**

We close that gap, but our distinguishing axis is not the technical substrate. It is (a)
**non-expert empowerment with comprehensibility**—can a non-specialist steer an autonomous loop into
a specialist domain using direction and big-picture understanding alone?—and (b) an **honest
negative result**: the loop autonomously reproduced a known generalization wall, and an objective
gate caught the false positives along the way.

**Contributions.**
1. **First application of AutoResearch to EDA surrogate learning** (single-file `train.py` mutation,
   fixed budget, population + median selection).
2. **A four-stage separation-of-powers gate** (median → LODO → cross-design T1 → independent Codex
   review) that blocked every would-be promotion across gen-002–008 (single-seed luck, evaluation leakage, cross-design regression, and a gate misalignment its own winner exposed) and *self-evolved* across
   generations.
3. **An honest negative result**: "in-loop `val_mae` ↓ ≠ cross-design generalization," reproduced by
   the autonomous loop across generations (clearest at gen-007/008, the generations judged by the
   finalized cross-design test), explicitly positioned as a *known* ML-for-EDA phenomenon rather
   than a new discovery.
4. **Non-expert empowerment and co-evolution**: a non-expert operator steered the loop by direction
   and tutorials; we document the operator-learning ↔ project-evolution cycle by date.

## 2. Background and Related Work

**RTL-to-GDSII and timing slack.** A chip is compiled from RTL (Verilog) through logic synthesis
(Yosys), placement and routing (OpenROAD), and static timing analysis (OpenSTA), to a GDSII layout
[1]. The quantity of interest here is **timing slack**: the margin between a signal's required and
arrival time (positive = meets the clock; negative = too slow). We predict the *final* (post-route)
slack from *post-synthesis* features.

**ML-for-EDA surrogates.** RouteNet predicts routability/DRC hotspots from placement features [2];
Net2 predicts net wirelength from graph structure; CircuitNet 2.0 is an open dataset (20k+ samples)
for routability/IR-drop/timing [4]; MasterRTL predicts pre-synthesis PPA from a bit-level operator
graph [5]; "Circuit as a Set of Points" treats placement as a point cloud for congestion/DRC
prediction [6]. Our surrogate uses tabular tree ensembles, not a GNN, for reasons given in the repo.

**AutoResearch and evolutionary ML search.** AutoResearch [8,9] mutates one training script under a
fixed budget with a git-ratchet accept/revert rule, in the lineage of population-based training and
black-box optimization, but searching open-endedly in *code space* rather than a predefined space.

**Cross-design generalization and distribution shift.** It is *well documented* that ML-for-EDA
models degrade on unseen/out-of-distribution designs [10,11]; leave-one-design-out (LODO) and
zero-shot OOD testing are standard protocols; congestion predictors can swing up to 90% under a 1%
adversarial cell shift [12]; benchmarks such as EDALearn exist to measure cross-design/cross-node
transfer [13]. **Our negative result is positioned squarely inside this body of work**: we do not
claim novelty for the phenomenon, only for its autonomous reproduction and capture.

## 3. System and Method

The system separates a **frozen substrate** from a **mutable script**:

- **`prepare.py` (frozen).** Builds the feature+label dataset from STA reports and defines the
  evaluation protocol. The agent may **not** modify it—this guarantees that every candidate is judged
  on identical data and rules.
- **`train.py` (mutable, single file).** The agent's only target. No new dependencies; a fixed
  training budget (inherited from AutoResearch's constraints).
- **Evolution loop (`src/pipeline/`).** Per generation: `candidate_gen` (Claude and Codex each
  propose mutations) → `runner` (each candidate trained on 5 seeds) → **median** selection (lowest
  median `val_mae` wins) → the gate.

**The four-stage separation-of-powers gate** (generator ≠ judge). A winner must pass all four; any
failure keeps the baseline:

1. **median (5-seed):** rejects single-split luck.
2. **LODO (leave-one-design-out):** holds out an entire design and asks whether the winner beats the
   baseline on *more* held-out designs (a *directional* probe).
3. **Cross-design T1:** repeats leave-one-design-out across seeds and applies a paired Wilcoxon test
   with bootstrap confidence intervals—asking whether the directional gap is *statistically
   significant*.
4. **Codex review:** a *different* LLM reads the candidate's code for evaluation leakage or metric
   gaming that statistics cannot see.

Exact statistical thresholds are owned by the design spec; this paper cites observed values, not
threshold definitions. **Operator-in-loop:** the design target is that the operator sets direction
(`program.md`) and follows each generation through tutorial-grade reports rather than approving
individual winners. In the current interim (auto-gate not yet implemented, see §7) the operator
still merges after reading the gate report; the earliest generations (1–2) predate this reframe and
involved operator approval/rejection.

## 4. Experimental Setup

**Datasets.** Real ORFS flows (run on AWS Fargate) produced four designs: gcd (53 rows), aes (691),
ibex (2040), and jpeg (4410), combined into a **7194-row** dataset. A `flow_lockfile_sha` anchors
reproducibility. Note that jpeg alone is ~61% of the data—this dominance matters in §8.

**Metric and baselines.** Path-slack prediction MAE in nanoseconds (lower is better). Baselines: a
*naive* predictor (use synthesis slack as the final slack) and the human-written `train.py`.

## 5. Results

The eight generations are summarized below (statistics from the per-generation reports):

| Gen | What was tested | Outcome | What the gate caught / finding |
|---|---|---|---|
| 1 | agent vs. human baseline | **promoted** | H-A confirmed *within-design*: winner 0.148 vs human 0.194 ns, dz = −1.27, p < 0.001 (naive = 1.41) |
| 2 | single-seed selection | rejected | single-seed winner (0.0992) was the median *worst*; the prior baseline (0.0865) was lowest → median harness introduced |
| 3 | stricter scoring | rejected_codex | Codex caught validation-set cherry-picking (post-selection leakage) that the statistical test missed |
| 4–5 | mixed designs + LODO | rejected_lodo | median-best winners regressed on held-out designs for two straight generations |
| 6 | stronger generation hints | rejected_t1 | first LODO pass, but mixed-fold T1 said *worse* → exposed an LODO↔T1 conflict; T1 redefined as a cross-design test |
| 7 | new four-stage chain | rejected_t1 | record-low median (1.29) and LODO pass, but cross-design T1 indistinguishable (mean diff +0.36, p = 0.655, dz = 0.10); lost on ibex |
| 8 | fourth design (jpeg) | rejected_t1 | record-low median (0.53), 2–2 split over four designs → indistinguishable (mean diff +0.018, p = 0.666); jpeg bias confirmed |

**The wall.** From gen-004 to gen-008 the in-loop median `val_mae` fell to successive record lows
(with the caveat that gen-008's median is on an enlarged 4-design dataset, so the medians are not
strictly like-for-like), yet no winner earned a gate-passing cross-design win. The rejection
mechanism differed by generation: gen-004/005 failed the earlier LODO stage and never reached T1;
gen-006 exposed the LODO↔T1 conflict that forced us to redefine T1 as a cross-design test (its
retroactive cross-design re-evaluation was in fact *distinguishable*, which motivated the
redefinition); and gen-007 and gen-008—the two generations judged by the finalized cross-design
T1—both returned *indistinguishable* despite record-low medians. The key figure (in the repository,
`tutorial/assets/the-wall.svg`) plots the descending in-loop curve against the flat cross-design outcome.

## 6. Discussion

**Structural separation.** Lowering in-distribution validation error and generalizing to unseen
designs are *different abilities*. This held across successive generations, three different selection
levers (more data, stronger hints, a fourth design), and both agent families.

**The gate's value is false-positive prevention.** Had we trusted the median alone, the record-low
winners that did not generalize (gen-004/005 regressed on held-out designs; gen-007/008 were
cross-design indistinguishable), plus the single-seed false positive at gen-002, would have
contaminated the baseline; gen-006 was a different case—blocked by the gate misalignment its own
winner exposed, not by failing to generalize. A gate proves its worth not when it promotes, but when
it refuses to be fooled by an optimistic in-loop number. Gen-003 is
the sharpest case: a candidate selected the best model *on the validation fold itself* (dz = −1.51,
which fooled the statistical gate), and only the independent code reviewer blocked it.

**Autonomous reproduction of a known phenomenon (honesty).** Our finding is not new science; it
restates what SwiftCTS [11] and EDALearn [13] report. The loop and gates were human-designed and
human-evolved; what no human hand-designed was the *candidate trajectory*, which converged on this
wall under that loop while the gate captured the false positives. The contribution is
reproduction-plus-capture, not discovery.

**Co-evolution.** Operational friction drove the method: a false positive (gen-002) produced the
median harness; an LODO↔T1 contradiction (gen-006) produced the cross-design statistical gate. Each
fix made the conclusion firmer—operator learning ↔ project evolution, both directions.

**jpeg bias.** The largest design (61%) dominated training, so the winner improved only
near-distribution transfer—pointing directly at the next lever.

## 7. Limitations

- **Few designs (4)** limit LODO/T1 statistical power; more designs are needed.
- **jpeg dominance (61%)**—no design-balanced sampling yet.
- **Auto-gate not yet implemented**: the operator currently merges after reading the gate report (an
  interim step), though the design intent is fully automatic promotion.
- **Single PDK/flow** (sky130/ORFS)—cross-node transfer untested.
- **Surrogate ≠ sign-off**: predictions are approximate and make no functional-correctness claim.

## 8. Conclusion and Future Work

An autonomous research loop plus an objective gate produced an *honest negative result*: quantitative
tweaks (re-sampling, more data) do not break the cross-design wall. We define **success** not as an
agent beating the baseline on generalization, but as the conjunction of three conditions, all met
here: (defense) the gate blocked false positives and kept the baseline intact; (finding) the
in-loop ≠ cross-design separation reproduced across generations under a pre-fixed gate; (accessibility)
a non-expert steered the loop and could follow every verdict through tutorials.

**Future work**: a *qualitative* shift—explicitly inducing design-invariant representations—or
**design-balanced sampling** to remove the jpeg bias (tracked as an open decision in the repo). A
deferred reasoning-trace evidence plane would further strengthen comprehensibility.

## 9. Reproducibility

All EDA tooling is open source (OpenROAD/Yosys); the repository is public; datasets are anchored by
`flow_lockfile_sha`; the gate is covered by 123 tests. Every generation's candidates, scores, and
gate reports are committed under `experiments/`.

## 10. Acknowledgements

This project is a **non-expert's learning and proof-of-concept** effort; see the repository
disclaimer. Contributions and corrections are welcome.

## 11. References

1. OpenROAD Project. https://en.wikipedia.org/wiki/OpenROAD_Project
2. Z. Xie et al., "Intelligent Circuit Design with ML" (RouteNet, Net2). https://arxiv.org/abs/2206.03032v1
3. OpenROAD-flow-scripts tutorial. https://openroad-flow-scripts.readthedocs.io/en/latest/tutorials/FlowTutorial.html
4. CircuitNet 2.0 (ICLR 2024). https://openreview.net/pdf/18243659a4c68baa73e34792453c17d63e6f68a3.pdf
5. MasterRTL (ICCAD 2023). https://arxiv.org/abs/2311.08441
6. "Circuit as a Set of Points" (NeurIPS 2023). https://proceedings.neurips.cc/paper_files/paper/2023/file/6697bb267dc517379bc8aa326e844f8d-Paper-Conference.pdf
7. CircuitNet dataset. https://circuitnet.github.io
8. AutoResearch — explainer. https://www.verdent.ai/guides/what-is-autoresearch-karpathy
9. AutoResearch — engineering deep-dive. https://www.snackonai.com/p/autoresearch-the-engineering-behind-karpathy-s-autonomous-ml-experiment-loop
10. Z. Xie, "ML Applications in EDA" (cross-design estimator). https://zhiyaoxie.com/files/chapter_route.pdf
11. SwiftCTS (2026, OOD/LODO cross-design). https://arxiv.org/pdf/2606.11348v1.pdf
12. "On Robustness and Generalization of ML-Based EDA" (NSF). https://par.nsf.gov/servlets/purl/10626479
13. EDALearn (cross-design/cross-node transfer benchmark). https://arxiv.org/pdf/2312.01674.pdf
