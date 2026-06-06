# 최소 runner: prebuilt openroad/orfs(native x86)에 awscli + 스크립트만 얹는다.
# digest-pin으로 재현성(NFR-2) — 로컬 검증과 동일 이미지.
FROM openroad/orfs@sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69

USER root
# awscli v2 번들 설치 (자체 런타임) — apt awscli는 이미지의 urllib3 2.x와 충돌(DEFAULT_CIPHERS).
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip \
 && unzip -q /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install \
 && rm -rf /tmp/aws /tmp/awscliv2.zip

COPY eda-flow/entrypoint.sh /opt/eda/entrypoint.sh
COPY eda-flow/dump_report_checks.tcl /opt/eda/dump_report_checks.tcl
RUN chmod +x /opt/eda/entrypoint.sh

ENTRYPOINT ["/opt/eda/entrypoint.sh"]
