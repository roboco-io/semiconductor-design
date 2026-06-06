# minimal report_checks 덤프 (-fields 없음 → Delay/Time 2-col, prepare.py 파서 계약).
# 다수 max-path를 덤프하고 endpoint별 worst는 prepare.py가 dedup한다 (F3).
# 인자는 env로 전달 (OpenROAD는 cmd_file 뒤 트레일링 argv 미지원).
# 사용: ODB=.. LIB=.. SDC=.. OUT=.. openroad -no_init -exit dump_report_checks.tcl
set odb $env(ODB)
set lib $env(LIB)
set sdc $env(SDC)
set out $env(OUT)

read_db $odb
read_liberty $lib
read_sdc $sdc

set fh [open $out w]
puts $fh [report_checks -path_delay max -format full_clock_expanded -group_path_count 10000]
close $fh
