import json
from pathlib import Path

from click.testing import CliRunner

import prepare

FIX = Path(__file__).parent / "fixtures"


def test_cli_writes_dataset(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        prepare.main,
        [
            "--synth", str(FIX / "synth.rpt"),
            "--route", str(FIX / "route.rpt"),
            "--lockfile", str(FIX / "lockfile.yaml"),
            "--design-id", "gcd",
            "--out-dir", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["n_samples"] == 2
