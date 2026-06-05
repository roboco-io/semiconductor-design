# real-gcd — prepare.py 파서 현실 검증 findings (2026-06-05)

> openroad/orfs:latest (digest b19fe0a5…) gcd sky130hd, macOS arm64 QEMU(linux/amd64) emulation.
> 목적: prepare.py 파서/feature_set을 **합성 fixture가 아닌 진짜 `report_checks`로 falsify**.
> 결론: **3겹 falsification** — frozen 계약(parser + 두-시점 pairing)을 train.py 전에 수정해야 함.

## 산출 (실제 tool 출력, fixture로 보존)
- `synth.rpt` — `1_synth.odb` (post-Yosys, 진짜 post-synthesis STA). 25 path.
- `route.rpt` — `3_place.odb` (post-placement). ⚠️ **진짜 post-route 아님** — QEMU에서 CTS(cts.tcl)가 illegal instruction으로 사망, route 미실행. Elmore RC 추정.
- `versions.txt` — 도구·이미지·stage 매핑.

## F1. 파서 — 두-줄 헤더 (실제, -fields 무관)
실제 OpenSTA는 긴 instance 이름의 clock 주석을 둘째 줄로 wrap:
```
Startpoint: dpath.b_reg.out[2]$_DFFE_PP_
            (rising edge-triggered flip-flop clocked by core_clock)
```
`_is_ff()`의 단일 줄 `^Startpoint:.*$` 매칭이 "flip-flop"을 못 봐 **startpoint_is_ff=False (전 path)**. → 2줄 span 매칭 필요.

## F2. 파서 — 가변 leading 컬럼 (report 생성 선택에 의존)
본 리포트는 `report_checks -fields {slew cap input net fanout}`로 생성 → stage 줄이 `Fanout Cap Slew Delay Time` (출력핀 5컬럼) + 별도 `(net)` 줄. 파서 `_STAGE_RE`는 `Delay Time` 2컬럼만 가정 → **stages=0 (전 path)**.
- 단, **리포트 포맷은 frozen flow의 *우리 선택***이다. default(no -fields)면 `Delay Time` 2컬럼에 가까워져 현 파서와 정합. rich -fields면 fanout/slew/cap을 *공짜로* 얻음(= OD-2가 "v2"로 미룬 feature) — 단 파서가 multi-line/가변컬럼 처리 필요.

## F3. 데이터 설계 — 두-시점 critical path 불일치 (가장 큰 발견)
`synth.rpt`(1_synth)와 `route.rpt`(3_place)의 critical path 집합이 **disjoint** — resizer/optimizer가 worst path를 stage 간 재편. `join_paths` (startpoint,endpoint,group,type) 매칭 = **0 rows (n_samples=0)**.
- 파서 버그 아님 — "같은 path를 두 시점에 관측"한다는 OD-2/OD-3 설계 가정 자체가 약함.
- 해결 후보: (a) stage당 path 대량 dump(`-group_path_count 500`)로 overlap↑, (b) 공통 endpoint 집합을 고정해 `report_checks -to <ep>`로 양 시점 enumerate, (c) feature/label을 path-id가 아니라 endpoint(FF) 단위로 pairing.

## F4. 인프라 — QEMU는 CTS/route 불가
arm64에서 amd64 emulation은 CTS에서 deterministic illegal instruction. **진짜 post-route label은 native amd64**(클라우드 또는 비-emulation 머신) 필요. → "EDA flow 실행 위치" open decision과 연결.

## 정합 — `arrival_ns`, `slack_ns`는 실제 출력에서 정상 파싱됨.

## Operator 결정 필요 (train.py 전)
1. 파서 포맷: default 최소 포맷 pin(F2 회피) + F1 수정 vs rich -fields 수용(feature 업그레이드) + 파서 보강.
2. 두-시점 pairing 전략(F3) — OD-2/OD-3 "resolved" 부분 재설계.
3. 진짜 post-route 인프라(F4) — 지금 연기 vs native amd64 확보.
