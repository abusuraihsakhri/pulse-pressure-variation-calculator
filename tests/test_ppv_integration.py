"""Integration and regression tests for measurement, API and audit integrity."""
import json

import pytest
from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail, SecurityException
from cli import main as cli_main
from ppv import main as ppv_main, process_csv


def test_api_ppv():
    client = TestClient(app)
    response = client.post("/api/ppv", json={"pp_max": 42, "pp_min": 38})
    assert response.status_code == 200
    assert response.json()["ppv_percent"] == 10.0


@pytest.mark.parametrize("payload", [
    {"pp_max": 0, "pp_min": 0},
    {"pp_max": 20, "pp_min": 25},
    {"sbp_max": 100, "dbp_max": 100, "sbp_min": 118, "dbp_min": 80},
    {"pp_max": 10},
])
def test_api_ppv_rejects_invalid_values(payload):
    response = TestClient(app).post("/api/ppv", json=payload)
    assert response.status_code == 422


def test_cli_ppv(capsys):
    assert cli_main(["ppv", "--pp-max", "42", "--pp-min", "38"]) == 0
    assert json.loads(capsys.readouterr().out)["ppv_percent"] == 10
    assert ppv_main(["ppv", "--pp-max", "42", "--pp-min", "38"]) == 0
    assert json.loads(capsys.readouterr().out)["ppv_percent"] == 10


def test_csv_ppv(tmp_path):
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("pp_max,pp_min\n42,38\n", encoding="utf-8")
    rows = process_csv(str(source), str(target))
    assert rows[0]["ppv_percent"] == "10.0"
    assert "ppv_percent" in target.read_text(encoding="utf-8")


def test_empty_csv_header_error(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        process_csv(str(source), str(tmp_path / "out.csv"))


def test_audit_rejects_tampering():
    audit = AuditTrail(secret_key="test-only-key")
    audit.log("tester", "test", "RUN", {"status": "ok"})
    audit.log("tester", "test", "RUN", {"status": "next"})
    assert audit.verify_integrity()
    audit.logs[0]["event_type"] = "FORGED"
    assert audit.verify_integrity() is False
    audit.logs[0]["event_type"] = "RUN"
    audit.logs[0]["current_hash"] = "0" * 64
    assert audit.verify_integrity() is False


def test_api_audit_phi_guard_422():
    response = TestClient(app).post("/api/audit", json={
        "task_id": "Patient MRN-999999",
        "target_identifier": "KEY-1",
        "primary_metric": 5
    })
    assert response.status_code == 422
    assert "pattern" not in response.text


def test_api_audit_rejects_nonfinite_metric():
    response = TestClient(app).post("/api/audit", json={
        "task_id": "T1", "target_identifier": "KEY-1", "primary_metric": "NaN"
    })
    assert response.status_code == 422


def test_cli_batch_false_not_critical(tmp_path, capsys):
    source = tmp_path / "batch.csv"
    output = tmp_path / "results.csv"
    source.write_text("task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\nT1,KEY1,12,4,NOMINAL,False\n")
    assert cli_main(["batch", "-i", str(source), "-o", str(output)]) == 0
    import csv
    with output.open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["overall_urgency"] == "ROUTINE"
