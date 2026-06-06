# minimal report_checks 덤프 (-fields 없음 → Delay/Time 2-col, prepare.py 파서 계약).
# 다수 max-path를 덤프하고 endpoint별 worst는 prepare.py가 dedup한다 (F3).
# 사용: openroad ... dump_report_checks.tcl <odb> <out.rpt>
set odb  [lindex $argv 0]
set out  [lindex $argv 1]
read_db $odb
set fh [open $out w]
puts $fh [report_checks -path_delay max -format full_clock_expanded -group_path_count 10000]
close $fh
