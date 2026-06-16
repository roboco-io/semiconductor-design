"""report — 세대 튜토리얼식 리포트 (이해가능성 산출물). 순수 함수.

INTENT 품질기준: 비전문가가 각 세대의 큰 흐름을 따라갈 수 있어야 한다.
"""

from __future__ import annotations


def render_generation_report(
    gen_no, ranking, winner_id, t1_report, codex_verdict, decision,
    lodo_report=None, comparability_note=None
) -> str:
    """ranking: [(id, sdk, strategy, median_val_mae), ...] (낮을수록 좋음, 정렬됨).

    lodo_report 가 주어지면 교차설계 LODO 게이트 섹션을 T1 섹션 앞에 삽입한다(게이트 순서와 동일).
    None 이면 생략(하위 호환). comparability_note 가 주어지면 결정 줄 아래에 경고로 명기한다
    (gen-004+ 다설계 dataset의 val_mae 비교성 — spec §6).
    """
    rank_lines = ["| 후보 | sdk | 전략 | median_val_mae |", "|---|---|---|---|"]
    for cid, sdk, strat, mae in ranking:
        mark = " ⭐" if cid == winner_id else ""
        rank_lines.append(f"| {cid}{mark} | {sdk} | {strat} | {mae:.4f} |")
    codex_body = (
        f"- approve: **{codex_verdict.get('approve')}**\n"
        f"- 사유: {codex_verdict.get('reasons', '')}"
    )
    rule_body = (
        "median 선택 → LODO 통과 → T1 `distinguishable` **AND** Codex `approve` → "
        "자동 승격(train.py·tag).\n"
        "사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗)."
    )
    sections = [("후보 순위 (median val_mae, 낮을수록 좋음)", "\n".join(rank_lines))]
    if lodo_report is not None:
        sections.append(("교차설계 LODO 게이트 (held-out 설계 일반화)", lodo_report))
    sections += [
        ("T1 통계 게이트 (winner vs 현 baseline)", t1_report),
        ("Codex 승격 심사관 (무결성·안전·품질)", codex_body),
        ("승격 규칙", rule_body),
    ]
    L = [
        f"# gen-{gen_no:03d} 리포트 (자율 승격 게이트)",
        "",
        f"**최종 결정: {decision}**  ·  winner: `{winner_id}`",
        "",
    ]
    if comparability_note is not None:
        L.append(f"> {comparability_note}")
        L.append("")
    for i, (title, body) in enumerate(sections, 1):
        L.append(f"## {i}) {title}")
        L.append(body)
        L.append("")
    return "\n".join(L).rstrip("\n")
