#!/usr/bin/env bash
# ORFS gcd 완주 → 두-시점 report_checks 덤프 → S3 적재.
# env: ARTIFACT_BUCKET, DESIGN(=gcd), RUN_ID(optional)
set -euo pipefail

DESIGN="${DESIGN:-gcd}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
FLOW=/OpenROAD-flow-scripts/flow
WORK=/tmp/eda-out
mkdir -p "$WORK"

cd "$FLOW"
# 1) ORFS 완주 (native x86 → CTS/route 성공)
make DESIGN_CONFIG="./designs/sky130hd/${DESIGN}/config.mk"

RES="results/sky130hd/${DESIGN}/base"
SYNTH_ODB="${RES}/1_synth.odb"
ROUTE_ODB="$(ls -1 ${RES}/*_final.odb 2>/dev/null | head -1 || true)"
[ -n "$ROUTE_ODB" ] || ROUTE_ODB="$(ls -1 ${RES}/6_*.odb | tail -1)"

# 2) 두 stage report_checks (minimal 포맷, -fields 없음 → prepare.py 파서 계약)
openroad -no_init -exit -log "$WORK/synth.log" \
  -metrics "$WORK/synth.json" \
  /opt/eda/dump_report_checks.tcl "$SYNTH_ODB" "$WORK/synth.rpt"
openroad -no_init -exit -log "$WORK/route.log" \
  -metrics "$WORK/route.json" \
  /opt/eda/dump_report_checks.tcl "$ROUTE_ODB" "$WORK/route.rpt"

# 3) versions + lockfile
{ echo "design: $DESIGN"; echo "run_id: $RUN_ID";
  echo "image_digest: sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69";
  openroad -version 2>/dev/null | head -1 | sed 's/^/openroad: /' || true;
  yosys -V 2>/dev/null | head -1 | sed 's/^/yosys: /' || true; } > "$WORK/versions.txt"

# 4) S3 적재
DEST="s3://${ARTIFACT_BUCKET}/runs/${DESIGN}/${RUN_ID}"
aws s3 cp "$WORK/synth.rpt"   "$DEST/synth.rpt"
aws s3 cp "$WORK/route.rpt"   "$DEST/route.rpt"
aws s3 cp "$WORK/versions.txt" "$DEST/versions.txt"
echo "uploaded → $DEST"
