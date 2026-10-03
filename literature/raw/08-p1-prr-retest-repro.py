"""P1 첫 재현: Semi-ATE/STDF PRR.to_atdf()의 재시험 필드 위치 (EXPLORATORY).

실행: PYTHONPATH=<Semi-ATE/STDF 체크아웃 또는 압축 해제 경로> python3 08-p1-prr-retest-repro.py
기대(불변식): 같은 레코드 유형의 ATDF 필드 수는 PART_FLG 재시험 비트 값과 무관하게 같아야 한다.
"""
from Semi_ATE.STDF import PRR

CASES = {
    "no retest": ["0"] * 8,
    "retest I (bit0)": ["1"] + ["0"] * 7,
    "retest C (bit1)": ["0", "1"] + ["0"] * 6,
}

for name, flg in CASES.items():
    r = PRR()
    r.set_value("PART_FLG", flg)
    s = r.to_atdf()
    print(f"{name:16} fields={s.count('|') + 1:2} {s!r}")
