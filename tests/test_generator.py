import ast
import json
import pytest
from traceforge.generator import generate_tests

def test_generate_tests_creates_valid_standalone_python(tmp_path):
    directory = tmp_path / "fixtures"
    directory.mkdir()
    fixture = {
        "schema_version":1,"id":"fixture-001",
        "request":{"method":"GET","path":"/health","headers":{},"body":None},
        "response":{"status_code":200,"headers":{"content-type":"application/json"},"body":{"status":"ok"}},
    }
    (directory / "one.json").write_text(json.dumps(fixture), encoding="utf-8")
    output = generate_tests(directory, tmp_path / "generated" / "test_regression.py")
    source = output.read_text(encoding="utf-8")
    ast.parse(source)
    assert "test_recorded_api_behavior" in source
    assert "fixture-001" in source
    assert "TRACEFORGE_TARGET_URL" in source

def test_generator_requires_at_least_one_fixture(tmp_path):
    with pytest.raises(ValueError, match="No valid JSON fixtures"):
        generate_tests(tmp_path / "empty", tmp_path / "out.py")
