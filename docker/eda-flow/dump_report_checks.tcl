# minimal report_checks 덤프 (-fields 없음 → Delay/Time 2-col, prepare.py 파서 계약).
# 다수 max-path를 덤프하고 endpoint별 worst는 prepare.py가 dedup한다 (F3).
# 인자는 env로 전달 (OpenROAD는 cmd_file 뒤 트레일링 argv 미지원).
# report_checks는 값을 반환하지 않고 stdout에 출력 → entrypoint가 openroad stdout을 .rpt로 리다이렉트.
# 사용: ODB=.. LIB=.. SDC=.. openroad -no_init -exit dump_report_checks.tcl > out.rpt
set odb $env(ODB)
set lib $env(LIB)
set sdc $env(SDC)

read_db $odb
read_liberty $lib
read_sdc $sdc

report_checks -path_delay max -format full_clock_expanded -group_path_count 10000
