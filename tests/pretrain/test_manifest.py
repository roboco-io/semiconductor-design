from pathlib import Path

import pytest

from pretrain_lib.manifest import load_manifest

GOOD = """\
version: 1
pdk_family: sky130
orfs_image_digest: "sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69"
designs:
  - {name: gcd, platform: sky130hd}
  - {name: aes, platform: sky130hd}
  - {name: riscv32i, platform: sky130hd}
  - {name: chameleon, platform: sky130hd}
encoder_val_designs: [riscv32i, chameleon]
label_designs: [gcd, aes, ibex, jpeg]
exclusion_rules:
  - "yosys synth exit code != 0"
  - "extracted endpoints < 10"
exclusions: []
"""


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "corpus_manifest.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_manifest_ok(tmp_path):
    m = load_manifest(_write(tmp_path, GOOD))
    assert m["orfs_image_digest"].startswith("sha256:")
    assert {d["name"] for d in m["designs"]} >= {"gcd", "riscv32i"}


def test_encoder_val_must_be_in_designs(tmp_path):
    bad = GOOD.replace("encoder_val_designs: [riscv32i, chameleon]",
                       "encoder_val_designs: [riscv32i, notexist]")
    with pytest.raises(ValueError, match="encoder_val"):
        load_manifest(_write(tmp_path, bad))


def test_encoder_val_disjoint_from_label_designs(tmp_path):
    bad = GOOD.replace("encoder_val_designs: [riscv32i, chameleon]",
                       "encoder_val_designs: [riscv32i, gcd]")
    with pytest.raises(ValueError, match="label"):
        load_manifest(_write(tmp_path, bad))


def test_exclusion_rules_are_fixed(tmp_path):
    bad = GOOD.replace('  - "extracted endpoints < 10"', '  - "operator judgement"')
    with pytest.raises(ValueError, match="exclusion_rules"):
        load_manifest(_write(tmp_path, bad))


def test_exclusion_reason_must_be_fixed_rule(tmp_path):
    bad = GOOD.replace(
        "exclusions: []",
        'exclusions: [{design: gcd, reason: "operator judgement"}]',
    )
    with pytest.raises(ValueError, match="exclusions"):
        load_manifest(_write(tmp_path, bad))


def test_exclusion_with_fixed_reason_passes(tmp_path):
    ok = GOOD.replace(
        "exclusions: []",
        'exclusions: [{design: gcd, reason: "yosys synth exit code != 0"}]',
    )
    m = load_manifest(_write(tmp_path, ok))
    assert m["exclusions"][0]["design"] == "gcd"
