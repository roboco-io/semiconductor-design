import json

from semi_design_runner.trace import TraceLogger


def test_trace_logger_appends_jsonl(tmp_path):
    log = TraceLogger(trace_dir=tmp_path, run_id="abc")
    log.emit(event="submit", payload={"arn": "x"})
    log.emit(event="poll", payload={"status": "RUNNING"})

    content = (tmp_path / "abc.jsonl").read_text().splitlines()
    assert len(content) == 2
    assert json.loads(content[0])["event"] == "submit"
    assert json.loads(content[1])["payload"]["status"] == "RUNNING"


def test_trace_logger_timestamps_each_line(tmp_path):
    log = TraceLogger(trace_dir=tmp_path, run_id="t")
    log.emit(event="e", payload={})
    line = (tmp_path / "t.jsonl").read_text().strip()
    assert "ts" in json.loads(line)
