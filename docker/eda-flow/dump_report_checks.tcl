# minimal report_checks 덤프 (-fields 없음 → Delay/Time 2-col, prepare.py 파서 계약).
# 다수 max-path를 덤프하고 endpoint별 worst는 prepare.py가 dedup한다 (F3).
# 사용: openroad ... dump_report_checks.tcl <odb> <lib> <sdc> <out.rpt>
set odb [lindex $argv 0]
set lib [lindex $argv 1]
set sdc [lindex $argv 2]
set out [lindex $argv 3]

read_liberty $lib
read_db $odb
read_sdc $sdc

set fh [open $out w]
puts $fh [report_checks -path_delay max -format full_clock_expanded -group_path_count 10000]
close $fh
