#!/usr/bin/env bash
# ORFS gcd 완주 → 두-시점 report_checks 덤프 → S3 적재.
# env: ARTIFACT_BUCKET, DESIGN(=gcd), RUN_ID(optional)
set -euo pipefail

DESIGN="${DESIGN:-gcd}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
FLOW=/OpenROAD-flow-scripts/flow
WORK=/tmp/eda-out
mkdir -p "$WORK"

# openroad/yosys를 PATH에 올린다 (직접 호출용 — make는 내부 env로 동작하지만 직접 openroad는 PATH 필요).
set +u
# shellcheck disable=SC1091
source /OpenROAD-flow-scripts/env.sh
set -u

cd "$FLOW"
# 1) ORFS 완주 (native x86 → CTS/route 성공)
make DESIGN_CONFIG="./designs/sky130hd/${DESIGN}/config.mk"

RES="results/sky130hd/${DESIGN}/base"
SYNTH_ODB="${RES}/1_synth.odb"
ROUTE_ODB="$(ls -1 ${RES}/*_final.odb 2>/dev/null | head -1 || true)"
[ -n "$ROUTE_ODB" ] || ROUTE_ODB="$(ls -1 ${RES}/6_*.odb | tail -1)"

# timing 환경: liberty(tt 코너) + 단계별 SDC. report_checks는 odb만으론 부족.
LIB="$(ls -1 "${FLOW}"/platforms/sky130hd/lib/*tt_025C_1v80*.lib 2>/dev/null | head -1)"
SYNTH_SDC="${RES}/1_synth.sdc"
ROUTE_SDC="$(ls -1 ${RES}/6_final.sdc ${RES}/5_*.sdc 2>/dev/null | head -1)"
echo "LIB=$LIB SYNTH_SDC=$SYNTH_SDC ROUTE_SDC=$ROUTE_SDC ROUTE_ODB=$ROUTE_ODB"

# 2) 두 stage report_checks (minimal 포맷, -fields 없음 → prepare.py 파서 계약)
openroad -no_init -exit /opt/eda/dump_report_checks.tcl \
  "$SYNTH_ODB" "$LIB" "$SYNTH_SDC" "$WORK/synth.rpt" > "$WORK/synth.log" 2>&1
openroad -no_init -exit /opt/eda/dump_report_checks.tcl \
  "$ROUTE_ODB" "$LIB" "$ROUTE_SDC" "$WORK/route.rpt" > "$WORK/route.log" 2>&1
echo "synth.rpt lines: $(wc -l < "$WORK/synth.rpt")  route.rpt lines: $(wc -l < "$WORK/route.rpt")"

# 3) versions + lockfile
{ echo "design: $DESIGN"; echo "run_id: $RUN_ID";
  echo "image_digest: sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69";
  openroad -version 2>/dev/null | head -1 | sed 's/^/openroad: /' || true;
  yosys -V 2>/dev/null | head -1 | sed 's/^/yosys: /' || true; } > "$WORK/versions.txt"

# 4) S3 적재 (로그도 함께 — 디버깅용)
DEST="s3://${ARTIFACT_BUCKET}/runs/${DESIGN}/${RUN_ID}"
aws s3 cp "$WORK/synth.rpt"    "$DEST/synth.rpt"
aws s3 cp "$WORK/route.rpt"    "$DEST/route.rpt"
aws s3 cp "$WORK/versions.txt" "$DEST/versions.txt"
aws s3 cp "$WORK/synth.log"    "$DEST/synth.log"
aws s3 cp "$WORK/route.log"    "$DEST/route.log"
echo "uploaded → $DEST"
