import hashlib
from pathlib import Path

from prepare_lib.dataset import flow_lockfile_sha

FIX = Path(__file__).parent / "fixtures"


def test_flow_lockfile_sha_matches_sha256():
    path = FIX / "lockfile.yaml"
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert flow_lockfile_sha(path) == expected
    assert len(flow_lockfile_sha(path)) == 64


def test_flow_lockfile_sha_is_deterministic():
    path = FIX / "lockfile.yaml"
    assert flow_lockfile_sha(path) == flow_lockfile_sha(path)
