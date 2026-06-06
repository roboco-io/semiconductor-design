"""selection — 후보 중 최저 val_mae winner 선택 (순수 함수)."""

from __future__ import annotations


def select_winner(results):
    ranking = sorted(results, key=lambda rv: rv[1])
    if not ranking or ranking[0][1] == float("inf"):
        return None, float("inf"), ranking
    return ranking[0][0], ranking[0][1], ranking
