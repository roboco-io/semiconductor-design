# 최소 runner: prebuilt openroad/orfs(native x86)에 awscli + 스크립트만 얹는다.
# digest-pin으로 재현성(NFR-2) — 로컬 검증과 동일 이미지.
FROM openroad/orfs@sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69

USER root
RUN apt-get update && apt-get install -y --no-install-recommends awscli \
 && rm -rf /var/lib/apt/lists/*

COPY eda-flow/entrypoint.sh /opt/eda/entrypoint.sh
COPY eda-flow/dump_report_checks.tcl /opt/eda/dump_report_checks.tcl
RUN chmod +x /opt/eda/entrypoint.sh

ENTRYPOINT ["/opt/eda/entrypoint.sh"]
