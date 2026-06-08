# src/pipeline/ — AutoResearch 진화 루프 오케스트레이션

serverless-autoresearch `src/pipeline/` 아날로그. 4-step generation cycle을 구동한다:

1. **candidate_gen** — baseline `train.py`에서 N개 변형 후보 생성 (전략 다양화)
2. **runner** — 후보를 로컬에서 고정 seed 세트로 실행해 val_mae 산출 (median 기반 선택)
3. **selection** — 최저 median val_mae winner 식별
4. **validation** — T1 repeated K-fold paired 통계 게이트 (winner vs baseline)
5. **promotion_reviewer** — Codex 승격 심사관 (무결성·안전·품질 소프트 게이트, 주입형)
6. **report** — 세대 튜토리얼식 리포트 렌더 (이해가능성 산출물)
7. **operator_gate** — git commit/tag 실행 (approve=True 시)
8. **holdout** — holdout 채점 (score_holdout)
9. **orchestrator** — 위 단계를 세대 루프로 묶음 (auto-gate 통합: T1 ∧ Codex AND)
10. **sdk** — 실제 Claude/Codex CLI 호출 gen_fn + codex_review_fn (비용, Operator-gated)

## auto-gate 흐름 (orchestrator `--auto`)

```
후보 생성 → run_all(median) → winner
  → T1: run_validation_gate(winner vs baseline) → verdict
      ├ indistinguishable/worse → status rejected_t1
      └ distinguishable → Codex: review_promotion → {approve, reasons}
            ├ block → status rejected_codex
            └ approve → operator_gate.promote → status promoted
  → gen-NNN/report.md (튜토리얼식 리포트)
```

ERD 매핑: GENERATION·CANDIDATE·JOB 엔티티의 라이프사이클 관리.
