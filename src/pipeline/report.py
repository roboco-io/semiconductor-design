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
