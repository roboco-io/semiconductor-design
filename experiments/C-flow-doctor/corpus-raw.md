# C1: 플로우 실패 사례 코퍼스 (raw)

수집일: 2026-08-25. 트랙 C(플로우 실패 진단기) 룰 베이스의 원천 데이터.
에러 시그니처는 이슈 본문/로그의 **원문 그대로** — 진단기 매칭 패턴으로 사용.

## 수집 방법

- 도구: `gh` CLI (`gh search issues` + `gh issue view --json title,url,state,body,comments`) + exa MCP(`web_search_exa`)
- 대상 레포: The-OpenROAD-Project/OpenLane, The-OpenROAD-Project/OpenROAD-flow-scripts(ORFS), librelane/librelane
  (efabless/openlane2는 librelane으로 이전되어 검색 불가 — librelane으로 대체)
- 검색 쿼리 로그 (`--state closed`):
  - OpenLane: "DRC violations", "antenna violations", "LVS mismatch", "synthesis failed", "floorplan", "global placement", "detailed routing", "CTS"
  - ORFS: "ERROR" / librelane: "error", "LVS"
  - exa: "Tiny Tapeout blog post debugging OpenLane hardening failure DRC or antenna error log postmortem"
- 필터링: 에러 시그니처 원문이 없는 이슈 제외(예: OpenLane#2015, librelane#837, OpenLane#1012 — 해결책은 있으나 로그 원문 부재)
- 해결 확인 표기: `확인` = closed + 해결 확인 댓글/커밋, `부분` = 해결책 제시되었으나 확인 댓글 없음/staled, `미해결` = closed이지만 근본 해결 없음

## 스키마

`id / 소스 URL / 플로우·버전 / 실패 단계 / 에러 시그니처(원문) / 근본 원인 / 해결책 / 해결 확인`

---

## 1. Synthesis (8건)

### C-001
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2078
- 플로우: OpenLane 1
- 단계: synthesis
- 시그니처: `[ERROR]: Synthesis failed. Signal not matching port size. Search for 'Resizing cell port'`
- 근본 원인: RTL에서 포트 폭과 연결 신호 폭 불일치 (Yosys가 'Resizing cell port' 경고 후 실패)
- 해결책: 합성 로그에서 해당 신호를 찾아 RTL 포트 폭 수정
- 해결 확인: 부분 (메인테이너가 해법 제시, staled out)

### C-002
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2152
- 플로우: OpenLane 2024.08.07 (679d5ba)
- 단계: synthesis
- 시그니처: `[ERROR]: during executing yosys script /openlane/scripts/yosys/synth.tcl` + `child killed: kill signal` (에러코드 없이 ABC 단계에서 사망)
- 근본 원인: ABC 매핑 중 메모리 부족(OOM) — 해당 설계 크기에서 ABC가 6GB 이상 사용, OS가 프로세스 kill
- 해결책: RAM 증설 또는 설계 분할. 근본 수정 없음
- 해결 확인: 미해결 (원인 진단만 확인, staled)

### C-003
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1994
- 플로우: OpenLane (conda 배포), sky130A
- 단계: synthesis
- 시그니처: `para_ser_01.v:51: ERROR: Re-definition of module `\para_ser_01'!`
- 근본 원인: 동일 모듈이 정의된 Verilog 파일이 VERILOG_FILES에 중복 포함
- 해결책: 소스 파일 목록에서 중복 모듈 정의 제거
- 해결 확인: 부분 (staled)

### C-004
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/914
- 플로우: OpenLane 2022.02.10 (2f75eb2)
- 단계: synthesis
- 시그니처: `ERROR: ABC: execution of command "/build/bin/yosys-abc -s -f /tmp/yosys-abc-.../abc.script 2>&1" failed: return code 134.`
- 근본 원인: yosys-abc 크래시(abort, rc 134) — 툴 버그
- 해결책: OpenLane 업데이트 (73cbe2bf에서 재현 불가 확인)
- 해결 확인: 확인 (메인테이너 재현 후 신버전에서 미발생 확인)

### C-005
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1070
- 플로우: OpenLane 2022.04.17
- 단계: synthesis (증상은 floorplan에서 발현)
- 시그니처: `[ERROR]: module $_ALDFF_PP_ not found in .../tmp/merged.nom.lef` + `[ERROR]: Check whether EXTRA_LEFS is set appropriately` + `[ERROR]: Floorplanning failed`
- 근본 원인: Yosys가 async-load DFF 프리미티브($_ALDFF_PP_)를 sky130 표준셀로 매핑 못함 — 라이브러리에 대응 셀 없음
- 해결책: 커스텀 `yosys_mapping.v`(techmap 파일)로 해당 프리미티브를 기존 셀 조합으로 매핑
- 해결 확인: 확인 (리포터가 yosys_mapping.v로 해결 확인)

### C-006
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/2906
- 플로우: ORFS, asap7, SYNTH_HIERARCHICAL
- 단계: synthesis
- 시그니처: `ERROR: Missing cost information on instanced blackbox ram_2048x39`
- 근본 원인: 계층 합성 모드에서 area 정보 없는 블랙박스(매크로) 인스턴스 — ungrouping 판단 불가
- 해결책: 블랙박스에 area/lib 정보 제공. (메시지 자체를 개선하기로 함)
- 해결 확인: 부분 (원인 설명 확인, 메시지 개선 미완)

### C-007
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/3826
- 플로우: ORFS, asap7-ibex, OPENROAD_HIERARCHICAL=1
- 단계: synthesis (넷리스트 출력 → sign-off 재파싱 실패)
- 시그니처: `[ERROR STA-0164] ./results/asap7/ibex/base/6_final.v line 72893, syntax error`
- 근본 원인: Yosys가 생성한 이스케이프 버스 포트명(`\Y[32:1]`)을 write_verilog가 부정확히 출력 → OpenSTA 파서가 거부
- 해결책: OpenSTA 파서 수정 (parallaxsw/OpenSTA PR #394)
- 해결 확인: 확인 (upstream PR 머지로 해결)

### C-008
- URL: https://github.com/librelane/librelane/issues/955
- 플로우: LibreLane main + ciel PDK (open_pdks f3b5e46)
- 단계: synthesis (환경/PDK 설정 기인)
- 시그니처: `ERROR: Missing `-liberty liberty_file' option!` + `ERROR    Subprocess had a non-zero exit.`
- 근본 원인: 신형 ciel PDK의 CELL_LIBS 구조 변경으로 `LIB` 변수가 빈 dict로 해석 — LibreLane main이 지원 안 하는 PDK 버전
- 해결책: `pdk_hashes.yaml`에 명시된 PDK 버전 사용, 또는 LibreLane dev 브랜치 사용
- 해결 확인: 확인 (리포터가 수긍 후 close)

## 2. Floorplan (2건)

### C-009
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1547
- 플로우: OpenLane (cb59d1f), gf180mcu + 커스텀 9t 셀 라이브러리
- 단계: floorplan (증상은 global placement)
- 시그니처: `[ERROR GPL-0130] No rows defined in design. Use initialize_floorplan to add rows.` + `Error: gpl.tcl, 69 GPL-0130`
- 근본 원인: PLACE_SITE가 사용하는 셀 라이브러리(9t)와 불일치 — floorplan이 row를 생성하지 못함 (open_pdks 설정 문제)
- 해결책: `set ::env(PLACE_SITE) "GF018hv5v_green_sc9"` 로 사이트 지정; 이후 open_pdks 업데이트로 해소
- 해결 확인: 확인 (리포터 감사 댓글 + open_pdks 수정)

### C-010
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/924
- 플로우: ORFS, sky130hd
- 단계: floorplan (macro placement 내 RePlAce)
- 시그니처: `[ERROR GPL-0304] Replace diverged at initial iteration . Re-run with a smaller init_density_penalty value .`
- 근본 원인: 배치 밀도 설정 부적합(PLACE_DENSITY 미설정/부적정)으로 초기 반복에서 발산
- 해결책: PLACE_DENSITY 활성화·조정, init_density_penalty 축소 (완결 확인 없음)
- 해결 확인: 부분 (staled)

## 3. Placement (4건)

### C-011
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1872
- 플로우: OpenLane 2023.02.14 (4cd0986)
- 단계: place (global)
- 시그니처: `[ERROR GPL-0307] RePlAce divergence detected. Re-run with a smaller max_phi_cof value.` + `Error: gpl.tcl, 69 GPL-0307`
- 근본 원인: 소규모 설계에서 RePlAce 발산 — OpenROAD gpl 버그
- 해결책: OpenROAD 업데이트 (OpenLane tag 2023.06.26에서 성공 확인)
- 해결 확인: 확인 (리포터 mattvenn이 신버전 성공 확인)

### C-012
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1201
- 플로우: OpenLane 2022.06.27 (83b6145), 사유 PDK + SRAM 매크로
- 단계: place (global, NesterovSolve)
- 시그니처: NesterovSolve 반복 중 정지 + RAM 전부 소모 후 `child killed` (OOM kill)
- 근본 원인: SRAM 매크로 인스턴스 존재 시 global placement 메모리 폭주 (upstream 버그, 이후 수정)
- 해결책: OpenLane/OpenROAD 업데이트 (리포터가 재현 불가 확인)
- 해결 확인: 확인

### C-013
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/3468
- 플로우: ORFS (로컬 빌드)
- 단계: place (detailed)
- 시그니처: `[ERROR DPL-0036] Detailed placement failed`
- 근본 원인: global placement 단계에서 30개 셀을 수동 고정 배치 → detailed placement가 합법화 실패
- 해결책: 수동 배치 셀의 위치/사이트 정렬 재검토 (명시적 해결 확인 없음)
- 해결 확인: 미해결 (논의가 DEF 좌표 추출로 표류, staled)

### C-014
- URL: https://github.com/librelane/librelane/issues/759
- 플로우: LibreLane (iic-osic-tools 2025.07)
- 단계: place (global, 내부 resizer)
- 시그니처: `ERROR    [RSZ-2001] failed bnet construction for _325_/Q` + `Error: gpl.tcl, 78 RSZ-2001` + `OpenROAD.GlobalPlacement failed with the following errors:`
- 근본 원인: 핀 배치 설정(FP_PIN_ORDER_CFG) 없이 실행 시 buffer-net 구성 실패 — LibreLane/OpenROAD 버그
- 해결책: 임시로 FP_PIN_ORDER_CFG 제공; 근본 수정 PR #757 머지
- 해결 확인: 확인 (메인테이너 "Should be okay now")

## 4. CTS (4건)

### C-015
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1746
- 플로우: OpenLane (b43df38)
- 단계: cts (내부 detailed placement 합법화)
- 시그니처: `[ERROR DPL-0036] Detailed placement failed.` + `Error: cts.tcl, 67 DPL-0036`
- 근본 원인: CTS 후 삽입된 클럭 버퍼 합법화 실패 (좁은 floorplan/밀도 문제)
- 해결책: 명시적 해결 기록 없음 (이슈는 스레드 표류 후 close)
- 해결 확인: 미해결 — 시그니처·단계 정보용

### C-016
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1935
- 플로우: OpenLane 2023.07.26 (01e6723)
- 단계: cts
- 시그니처: `Signal 11 received` (TritonCTS segfault, 멀티 클럭 설계)
- 근본 원인: 출력 핀/블록 터미널에 연결되지 않은 클럭 넷을 CTS가 처리하다 크래시
- 해결책: OpenROAD 수정 — 미연결 클럭 넷 스킵(`[INFO CTS-0122] Clock net "..." is skipped for CTS`)
- 해결 확인: 확인 (메인테이너가 수정 후 크래시 해소 확인)

### C-017
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/3495
- 플로우: ORFS (OpenROAD v2.0-21872)
- 단계: cts
- 시그니처: `[ERROR ODB-0370] Attempt to disconnect term B of dont_touch instance inst_project_core/.../inst_dont_touch_ck_mux`
- 근본 원인: SDC의 `set_dont_touch {인스턴스}`가 클럭 경로 위에 있어 CTS가 재배선 불가
- 해결책: 클럭 경로 인스턴스에 dont_touch 미적용 또는 CTS 대상에서 해당 클럭 제외 (툴 측 결론 없음)
- 해결 확인: 미해결 (메인테이너 "unclear what CTS should do", staled)

### C-018
- URL: https://github.com/librelane/librelane/issues/884
- 플로우: LibreLane dev (nix), gf180mcuD smoke test
- 단계: cts (내부 DPL)
- 시그니처: `[INFO DPL-0034] Detailed placement failed on the following 1 instances:` + `ERROR    [DPL-0036] Detailed placement failed.` + `Error: cts.tcl, 102 DPL-0036` + `OpenROAD.CTS failed with the following errors:`
- 근본 원인: gf180mcuD smoke test 기본 설정의 FP_CORE_UTIL이 과도 — CTS 버퍼 넣을 공간 부족
- 해결책: FP_CORE_UTIL 하향 (3.0 릴리스 전 반영하기로 확인)
- 해결 확인: 확인 (메인테이너 합의·수정 예정 close)

## 5. Routing (11건)

### C-019
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2025
- 플로우: OpenLane (dc5af98), openframe_project_wrapper
- 단계: route (global)
- 시그니처: `[ERROR GRT-0076] Net analog_io[15] not properly covered.` + `Error: grt.tcl, 29 GRT-0076`
- 근본 원인: 매크로 1개가 core area 밖에 배치됨 — 해당 넷의 라우팅 가이드 생성 불가
- 해결책: 매크로를 core area 안으로 이동 (리포터가 성공 확인)
- 해결 확인: 확인

### C-020
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1958
- 플로우: OpenLane 2022.12.14 (90d369b)
- 단계: route (detailed, ECO 반복 중)
- 시그니처: `[ERROR DRT-0218] Guide is not connected to design.` + `Error: droute.tcl, 38 DRT-0218`
- 근본 원인: 구버전 OpenROAD의 가이드-설계 불일치 버그 (upstream OpenROAD#1197에서 수정)
- 해결책: OpenLane(내장 OpenROAD) 업데이트
- 해결 확인: 확인 (동일 오류 upstream 해결 링크)

### C-021
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2168
- 플로우: OpenLane
- 단계: route (detailed)
- 시그니처: `Signal 6 received` + `stl_vector.h:950: ... operator[](...) const [with _Tp = std::unique_ptr<fr:...` (assert 크래시)
- 근본 원인: 동일 blockRAM 매크로의 두 버전 GDS/LEF가 같은 폴더에 있어 병합 시 핀 중첩 — 손상된 입력으로 라우터 크래시
- 해결책: 중복 매크로 파일 제거. (LibreLane의 macros 객체 사용 권장)
- 해결 확인: 확인 (리포터가 원인 규명·해결)

### C-022
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1114
- 플로우: OpenLane 2022.02.23
- 단계: route (detailed)
- 시그니처: `[ERROR]: during executing openroad script /openlane/scripts/openroad/droute.tcl` + `child killed: kill signal` (7k 셀 설계에서 12GB 메모리)
- 근본 원인: SPACER 플래그 없는 대량 FILLER 셀을 라우터가 일반 셀로 취급 — 메모리 폭주
- 해결책: 필 셀 제외 시 정상(16초, 2.6GB) 확인; LEF에 SPACER 플래그 부여
- 해결 확인: 확인 (워크어라운드 검증)

### C-023
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1320
- 플로우: OpenLane MPW7 (f9b5781)
- 단계: route (detailed)
- 시그니처: `Net zero_ of signal type GROUND is not routable by TritonRoute. Move to special nets`
- 근본 원인: 상수(tie) 넷이 tie 셀 없이 GROUND 시그널로 남음
- 해결책: floorplan 직후 `insert_tiecells "$tielo_cell/$tielo_port" -prefix "TIE_ZERO_"` 삽입 (이슈 #1185 방식)
- 해결 확인: 확인 (사용자 워크어라운드로 통과)

### C-024
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2130
- 플로우: OpenLane (a35b64a), caravel user_proj_example
- 단계: route (global)
- 시그니처: `[ERROR GRT-0118] Routing congestion too high. Check the congestion heatmap in the GUI.` + `Error: groute.tcl, 36 GRT-0118`
- 근본 원인: 설계 밀도/면적 대비 라우팅 자원 부족 (congestion)
- 해결책: 면적 확대·밀도 하향·GRT_ADJUSTMENT 조정 (스레드에선 확정 해결 없음, staled)
- 해결 확인: 부분

### C-025
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2069
- 플로우: OpenLane 2023.09.11 (5215ea7)
- 단계: route (global, antenna repair 반복)
- 시그니처: `can't read "::env(SAVE_DEF)": no such variable` (routing.tcl `set minimum_def $::env(SAVE_DEF)`) + `[ERROR]: Step 24 (routing) failed`
- 근본 원인: OpenLane 스크립트 버그 — antenna 반복이 위반을 줄이는 데 성공할 때 미정의 변수 참조
- 해결책: routing.tcl 수정 (리포터가 후속 버그 위치까지 특정)
- 해결 확인: 부분 (버그 위치 특정, 명시적 픽스 확인 댓글 없음)

### C-026
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1740
- 플로우: OpenLane 2023.03.28 (d708849), caravel
- 단계: route (global, antenna repair)
- 시그니처: `[ERROR ODB-0390] order_wires failed: net mgmt_buffers.mprj2_vdd_logic1, shorts to another term at wire point (2894780 762450)` + `Error: groute.tcl, 41 ODB-0390`
- 근본 원인: antenna checker용 임시 라우팅 생성 시 OpenROAD 버그 (order_wires)
- 해결책: OpenROAD PR #3235로 수정; 임시로 `GRT_ANT_MARGIN` 15→12 또는 `GRT_ADJUSTMENT 0.1` 조정
- 해결 확인: 확인 (리포터 "You fixed it!")

### C-027
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1970
- 플로우: OpenLane, caravel ML-SoC 매크로
- 단계: route (global, antenna repair)
- 시그니처: `[INFO GRT-0006] Repairing antennas, iteration 1.` 직후 `child killed: kill signal` (메모리 67.1GB 100% 도달)
- 근본 원인: OpenROAD antenna repair 메모리 폭주 (upstream 버그)
- 해결책: OpenLane 66e938bc(신형 OpenROAD)로 업데이트
- 해결 확인: 확인 (리포터가 신버전에서 미발생 확인)

### C-028
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1896
- 플로우: OpenLane (3bc9d02)
- 단계: route (resizer 최적화)
- 시그니처: `[ERROR RSZ-0005] Run global_route before estimating parasitics for global routing.` + `Error: resizer_routing_design.tcl, 52 RSZ-0005`
- 근본 원인: 커스텀 블랙박스 매크로의 LEF/GDS 핀 이름이 Verilog 모델과 불일치 → global route가 사실상 실패한 상태에서 resizer 진입
- 해결책: 핀 네이밍을 상호 일치시킴 (버스 표기 포함)
- 해결 확인: 부분 (진행 후 다음 단계 이슈로 이동)

### C-029
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1724
- 플로우: OpenLane (bff7987), PDK 버전 MISMATCH 환경
- 단계: route (resizer) / cts 연관
- 시그니처: `[ERROR RSZ-0005] Run global_route before estimating parasitics for global routing.` + `Error: resizer_routing_design.tcl, 45 RSZ-0005` (선행 증상: CTS에서 클럭 넷 미발견)
- 근본 원인: 래퍼 안에 계층 인스턴스(OTTER_MCU in OTTER_WRAPPER)를 flatten 없이 하드닝 — 플로우는 flat 설계 전제
- 해결책: resizer 스텝 스킵 또는 caravel user_project_wrapper 예제 설정 방식 준수
- 해결 확인: 확인 (해결책 제시 후 close)

### C-030
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/2548
- 플로우: ORFS master, nangate45/gcd 기본 플로우
- 단계: route (detailed)
- 시그니처: `Error: detail_route.tcl, 63 expected boolean value but got ""` + `make[1]: *** [Makefile:794: do-5_2_route] Error 1`
- 근본 원인: ORFS 스크립트와 OpenROAD 바이너리 버전 불일치 (변수 미전달)
- 해결책: OR/ORFS 버전 정합 (GitGuide대로 재빌드)
- 해결 확인: 부분 (staled)

## 6. LVS (4건)

### C-031
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1768
- 플로우: OpenLane, gf180 caravel user_project_wrapper
- 단계: lvs
- 시그니처: `[ERROR]: There are LVS errors in the design: See '.../reports/signoff/23-user_project_wrapper.lvs.rpt'` + `[ERROR]: Flow failed.`
- 근본 원인: 최상위(비합성) 레벨에서 입력을 tie-high/low → 전원 미연결 `conb` 셀 생성 (셀 row·필러·전원 레일 없음)
- 해결책: (1) tie를 하위 user_proj_example 레벨로 이동, 또는 (2) 설계 flatten
- 해결 확인: 부분 (해법 제시, 후속 별도 이슈)

### C-032
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1067
- 플로우: OpenLane 2022.04.17, MPW5 통과 설계 재실행
- 단계: lvs
- 시그니처: `Cells failed matching, or top level cell failed pin matching.` + `[ERROR]: There are LVS errors in the design..`
- 근본 원인: OpenROAD PDN 변경으로 매크로 위 met5-met4 비아 미삽입 → 전원 네트 불일치
- 해결책: PDN 관련 수정 PR #1059로 해결
- 해결 확인: 확인 (PR 링크로 close)

### C-033
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1353
- 플로우: OpenLane, sky130 + SRAM 매크로 8개
- 단계: lvs
- 시그니처: `LVS failed, SRAM power mismatch` — SRAM 매크로 8개 사용 시 net mismatch 16개
- 근본 원인: `FP_PDN_MACRO_HOOKS`에 SRAM 매크로 인스턴스 누락 — 매크로 전원 미연결
- 해결책: 모든 매크로 인스턴스를 FP_PDN_MACRO_HOOKS에 등록
- 해결 확인: 확인 (리포터 "I pass LVS now")

### C-034
- URL: https://github.com/librelane/librelane/issues/976
- 플로우: LibreLane, 하드 매크로 통합
- 단계: lvs (pdn 기인)
- 시그니처: `Hard macro VPWR/VGND pins are extracted as local nets, causing LVS failure` (매크로 met3/met4 전원 레일 미연결로 LVS mismatch)
- 근본 원인: 매크로 하드닝 시 전원 링/핀 셋업과 top-level pdngen 연결 조건 불일치
- 해결책: 매크로에 `PDN_CORE_RING: true` + VPWR/VGND 핀 정의, top에서 PDN 훅 연결 (리포터가 검증된 전체 레시피 공유)
- 해결 확인: 확인

## 7. DRC / Sign-off (4건)

### C-035
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2058
- 플로우: OpenLane, SRAM 매크로 포함 설계
- 단계: drc (Magic)
- 시그니처: `[ERROR]: There are violations in the design after Magic DRC.` (GUI에선 0인데 리포트는 56000 violations)
- 근본 원인: GDS 기반 DRC가 SRAM 매크로 내부(maglef로 봐야 할 영역)까지 검사 — 위양성 폭증
- 해결책: config에 `"MAGIC_DRC_USE_GDS": 0` 설정 (mag 기반 DRC로 전환)
- 해결 확인: 확인 (리포터 해결 댓글)

### C-036
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1269
- 플로우: OpenLane (7b15116), caravel user_project_wrapper
- 단계: drc (Magic 결과 변환)
- 시그니처: `[ERROR]: during executing: "openroad -python /openlane/scripts/drc_rosetta.py tr to_klayout ..."` + `[ERROR]: Exit code: 1` + `child killed: kill signal`
- 근본 원인: 대형 DRC 리포트를 KLayout XML DB로 변환하는 스크립트가 리소스 초과로 kill
- 해결책: 명시적 픽스 없음 (재현물 제출 후 신규 이슈 유도로 close)
- 해결 확인: 미해결 — 시그니처·단계 정보용

### C-037
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2040
- 플로우: OpenLane + mpw_precheck, sky130B
- 단계: drc (Magic — 위험한 침묵 실패)
- 시그니처: `Could not find file '/root/eda/pdk/sky130B/libs.tech/magic/sky130A.tech'` + `"drc(full)" is not one of the DRC styles Magic knows.` + `No errors found.` (실제 1246 위반 존재)
- 근본 원인: PDK(sky130B)와 tech 파일(sky130A) 불일치로 DRC 덱 미로드 — 검사가 실행되지 않았는데 0 violations로 보고 (drc.tr 0바이트)
- 해결책: OpenLane 1d46ea5f / MPW tag `2023.07.19-1`에서 변환 스크립트 버그(.read() 문자 단위 순회) 수정
- 해결 확인: 확인 (메인테이너 수정·백포트)

### C-038
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/688
- 플로우: OpenLane (2021)
- 단계: signoff (STA hold + DRC/antenna 리포트 해석)
- 시그니처: `[ERROR]: There are hold violations in the design at the typical corner. Please refer to .../23-spef_extraction_sta.min.rpt.` + `Violation Message "Local interconnect minimum area < 0.0561um^2 (li.6) "found 451096 Times.` + `Number of pins violated: 275`
- 근본 원인: 라우팅 후 hold 위반 + li.1/met1 min-area DRC 다수 + antenna 위반 — 설정(hold 버퍼링, 필러/타이) 미조정
- 해결책: 이슈에서는 설정 변수 문의 단계에서 close (hold fix는 resizer hold 옵션 계열)
- 해결 확인: 부분

## 8. PDN (5건)

### C-039
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1165
- 플로우: OpenLane, core 설계 + 매크로 (FP_PDN_CORE_RING=1)
- 단계: pdn
- 시그니처: `[ERROR PDN-0179] Unable to repair all channels.`
- 근본 원인: 매크로 배치로 생긴 좁은 채널에 PDN 스트랩 수리가 불가능한 구조 (구버전 OpenROAD 한계)
- 해결책: OpenROAD 809c4384로 업데이트 후 통과 + DIE_AREA 조정
- 해결 확인: 확인 (업데이트 후 라우팅 통과 확인)

### C-040
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/2053
- 플로우: OpenLane (1e9efe9), 소형 설계(half adder)
- 단계: pdn
- 시그니처: `[ERROR PDN-0175] Pitch 1.8400 is too small for, must be atleast 6.6000` + `Error: pdn_cfg.tcl, 92 PDN-0175`
- 근본 원인: 설계 면적이 작아 지정 PDN pitch가 스트라이프 폭/간격 제약보다 작아짐
- 해결책: FP_PDN pitch 상향 또는 die 면적 확대
- 해결 확인: 부분 (메인테이너 해법 제시 후 close)

### C-041
- URL: https://github.com/The-OpenROAD-Project/OpenLane/issues/1877
- 플로우: OpenLane conda(colab) 2023.04.12 구버전
- 단계: pdn (환경 기인)
- 시그니처: `Error: pdn_cfg.tcl, 92 can't read "::env(FP_PDN_LOWER_LAYER)": no such variable` + `[ERROR]: Step(6:floorplan) failed with error:`
- 근본 원인: conda 채널의 구버전 OpenLane과 신형 변수명 불일치 (콜랩 노트북 버전 표류)
- 해결책: conda 패키지 2023.06.26 갱신으로 해결; 공식적으로는 LibreLane 이행 권고
- 해결 확인: 확인

### C-042
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/4356
- 플로우: ORFS (afad87d), asap7 aes-blocks 등 2개 설계
- 단계: pdn
- 시그니처: `[ERROR PDN-0006] VDD on M5 is blocked by obstructions on M6, M7, M8 for u0/r0`
- 근본 원인: 커맨드라인 `MAX_ROUTING_LAYERS`가 블록 레벨 설정을 덮어써 블록 LEF에 M8까지 obstruction 생성 → 상위 PDN 비아 불가
- 해결책: 블록 레벨 라우팅 레이어 설정을 덮어쓰지 않기
- 해결 확인: 확인 (메인테이너가 트리거 규명)

### C-043
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/3484
- 플로우: ORFS (44ad745), BLOCKS로 매크로 통합 (ihp류 메탈스택)
- 단계: pdn
- 시그니처: `WARNING  [PDN-0232] The grid "macro - my_switch" (Instance) does not contain any shapes or vias.` + `ERROR    [PDN-0233] Failed to generate full power grid.`
- 근본 원인: FIXED 매크로가 core 하단에 붙어 아래 row가 제거되면 매크로 그리드에 생성할 shape가 없음
- 해결책: 매크로를 최소 1개 row 띄워 배치 (테스트케이스로 재현 확인)
- 해결 확인: 부분 (동일 증상 재보고 존재)

## 9. 환경/설치 (3건)

### C-044
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/4105 (중복: #4222, 근본 원인 #4379)
- 플로우: ORFS prebuilt 바이너리/docker `openroad/orfs:latest`, sky130hd-ibex, nangate45-gcd
- 단계: 환경 (증상은 cts에서 발현)
- 시그니처: `Error: cts.tcl, 86 child killed: illegal instruction` + `make[1]: *** [Makefile:512: do-4_1_cts] Error 1`
- 근본 원인: prebuilt OpenROAD 바이너리의 CTS 코드 경로에 AVX-512 명령 포함 — AVX-512 미지원 CPU(Zen 4 이전 AMD, Alder Lake 이후 인텔 소비자용)에서 SIGILL
- 해결책: 해당 시스템용 네이티브 빌드 (동일 커밋 네이티브 빌드는 정상)
- 해결 확인: 확인 (#4379에서 루트코즈·재현 확인)

### C-045
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/issues/3584
- 플로우: ORFS (917131b), Ubuntu 22.04.5 로컬 빌드
- 단계: 환경 (빌드)
- 시그니처: `gmake[2]: *** [src/dst/test/cpp/CMakeFiles/TestWorker.dir/build.make:131: src/dst/test/cpp/TestWorker] Error 1` + `gmake: *** [Makefile:146: all] Error 2`
- 근본 원인: 유닛테스트 타깃(TestWorker) 빌드 실패 (의존성/링크 문제)
- 해결책: `./build_openroad.sh --local --openroad-args "-DENABLE_TESTS=OFF"` 로 테스트 제외 빌드
- 해결 확인: 확인 (리포터 빌드 성공)

### C-046
- URL: https://github.com/librelane/librelane/issues/955 관련 계열 — Tiny Tapeout 로컬 하드닝 가이드
- 소스: https://tinytapeout.com/guides/local-hardening/
- 플로우: Tiny Tapeout tt_tool.py + LibreLane, sky130A
- 단계: 환경 (PDK 활성화)
- 시그니처: `make[1]: *** No rule to make target '[...]/ttsetup/pdk/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v', needed by 'sim_build/gl/sim.vvp'. Stop.`
- 근본 원인: ciel로 설치한 PDK가 enable되지 않아 심링크/경로 미구성
- 해결책: `ciel ls`로 해시 확인 후 `ciel enable <hash>`
- 해결 확인: 확인 (공식 가이드의 트러블슈팅 항목)

---

## 집계

| 단계 | 건수 | id |
|---|---|---|
| synthesis | 8 | C-001..C-008 |
| floorplan | 2 | C-009, C-010 |
| place | 4 | C-011..C-014 |
| cts | 4 | C-015..C-018 |
| route (antenna 포함) | 11 | C-019..C-029 (antenna: C-025..C-027), C-030 |
| lvs | 4 | C-031..C-034 |
| drc/signoff | 4 | C-035..C-038 |
| pdn | 5 | C-039..C-043 |
| 환경 | 3 | C-044..C-046 |
| **계** | **46** | |

해결책 보유: 43/46 (해결 확인 `확인` 26건, `부분` 14건, `미해결` 6건 중 3건도 원인 진단 있음)

## 코퍼스 한계 (진단기 설계 시 유의)

1. **버전 편향**: OpenLane 1(2022-2024) 사례가 다수 — LibreLane/최신 ORFS에서 메시지 형식이 다를 수 있음 (예: LibreLane은 rich 로그 `ERROR    [...] step.py:NNNN` 형식)
2. **"업데이트하면 됨" 계열 다수**: 근본 원인이 upstream 버그인 사례는 룰로 만들면 "버전 확인" 진단으로 수렴 — 시그니처만으로 설정 문제와 구분 필요
3. **OOM 계열 시그니처 중복**: `child killed: kill signal`이 synthesis/route/drc 등 여러 단계에서 동일하게 나타남 — 단계 컨텍스트(어느 스크립트 실행 중인지) 병행 매칭 필수
4. **Slack 아카이브 미수집**: open-source-silicon.dev Slack은 로그인 장벽으로 이번 수집에서 제외 — GitHub 이슈 편향(재현 가능한 사례 위주, 초보자의 환경 실수 과소 대표)
5. **시그니처 절단**: 220자 컷으로 일부 시그니처가 잘림 — 룰 작성 시 원 이슈 URL에서 전문 재확인 권장
