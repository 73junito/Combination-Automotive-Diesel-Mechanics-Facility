import importlib.util
from pathlib import Path
import json
import pytest


def load_module():
    tests_dir = Path(__file__).resolve().parent
    module_path = tests_dir.parent / "scripts" / "auto_drawing_check.py"
    spec = importlib.util.spec_from_file_location("auto_drawing_check", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_help_shows_strict(capsys):
    mod = load_module()
    with pytest.raises(SystemExit) as se:
        mod.main(["--help"])
    captured = capsys.readouterr()
    assert "--strict" in captured.out
    assert se.value.code == 0


def test_missing_inputs_non_strict_warns_and_returns_ok(tmp_path, capsys):
    mod = load_module()
    # create a dummy dxf path that does not exist to simulate missing PDF and DXF
    pdf = str(tmp_path / "nope.pdf")
    dxf = str(tmp_path / "nope.dxf")
    rc = mod.main([pdf, dxf])
    captured = capsys.readouterr()
    assert rc == mod.EXIT_OK
    assert "WARNING: PDF not found" in captured.err or "WARN: PDF not found" in captured.err


def test_missing_inputs_strict_errors(tmp_path, capsys):
    mod = load_module()
    pdf = str(tmp_path / "nope.pdf")
    dxf = str(tmp_path / "nope.dxf")
    rc = mod.main(["--strict", pdf, dxf])
    captured = capsys.readouterr()
    assert rc == mod.EXIT_INPUT
    assert "ERROR: PDF not found" in captured.err


def test_out_writes_json_when_dxf_exists(tmp_path):
    mod = load_module()
    # Create a minimal dummy DXF file so dxf_exists becomes True; leave PDF missing
    dxf_file = tmp_path / "dummy.dxf"
    dxf_file.write_text("0\nSECTION\n2\nTABLES\n0\nENDSEC\n0\nEOF\n")
    out_file = tmp_path / "result.json"
    rc = mod.main([str(tmp_path / "nope.pdf"), str(dxf_file), "--out", str(out_file)])
    assert rc == mod.EXIT_OK
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data.get("dxf_exists") is True
