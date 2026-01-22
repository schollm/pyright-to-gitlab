"""Tests for the pyright_to_gitlab module."""

from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from pyright_to_gitlab import main

PYRIGHT = {
    "version": "1.1.385",
    "time": "1748865254393",
    "generalDiagnostics": [
        {
            "file": "test1.py",
            "severity": "error",
            "message": 'Message "foo"',
            "range": {
                "start": {"line": 101, "character": 27},
                "end": {"line": 101, "character": 35},
            },
            "rule": "reportGeneralTypeIssues",
        },
        {
            "file": "test2.py",
            "severity": "error",
            "message": "Message bar",
            "range": {
                "start": {"line": 130, "character": 18},
                "end": {"line": 130, "character": 24},
            },
            "rule": "reportInvalidTypeForm",
        },
    ],
    "summary": {
        "filesAnalyzed": 3,
        "errorCount": 2,
        "warningCount": 0,
        "informationCount": 0,
        "timeInSec": 0.200,
    },
}
GITLAB = [
    {
        "check_name": "pyright: reportGeneralTypeIssues",
        "description": 'Message "foo"',
        "fingerprint": "c07588a4b4ee16dee26d14c086857de5a86bb7034461cdad63f6397f",
        "location": {
            "path": "test1.py",
            "positions": {
                "begin": {"column": 27, "line": 101},
                "end": {"column": 35, "line": 101},
            },
        },
        "severity": "major",
    },
    {
        "check_name": "pyright: reportInvalidTypeForm",
        "description": "Message bar",
        "fingerprint": "d8bd498be79cb56d504196f52a1ba9bcd4e66635404629eda82e6be4",
        "location": {
            "path": "test2.py",
            "positions": {
                "begin": {"column": 18, "line": 130},
                "end": {"column": 24, "line": 130},
            },
        },
        "severity": "major",
    },
]


@pytest.mark.parametrize(
    ("pyright", "gitlab"),
    [
        ({}, []),  # Empty input should yield empty output
        (PYRIGHT, GITLAB),
    ],
)
def test(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    pyright: dict,
    gitlab: list[dict],
) -> None:
    """Test that the pyright.json is converted to GitLab Code Quality report format."""
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    assert json.loads(captured.out) == gitlab


@pytest.mark.parametrize(
    ("pyright", "gitlab"),
    [
        ({}, []),  # Empty input should yield empty output
        (PYRIGHT, GITLAB),
    ],
)
def test_input_output_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    pyright: dict,
    gitlab: list[dict],
) -> None:
    """Test that the pyright.json is converted to GitLab Code Quality report format."""
    input_file = tmp_path / "pyright.json"
    input_file.write_text(json.dumps(pyright))
    output_file = tmp_path / "gitlab.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "pyright_to_gitlab.py",
            "-i",
            input_file.as_posix(),
            "-o",
            output_file.as_posix(),
        ],
    )
    main()
    assert json.loads(output_file.read_text("utf-8")) == gitlab


@pytest.mark.parametrize(
    ("pyright", "gitlab"),
    [
        ({}, []),  # Empty input should yield empty output
        (PYRIGHT, GITLAB),
    ],
)
def test_prefix(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
    pyright: dict,
    gitlab: list[dict],
) -> None:
    """Test that the prefix is added to the file paths in the output."""
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py", "--prefix", "prefix/"])
    prefix = "prefix/"
    main()
    captured = capsys.readouterr()
    gitlab_with_prefix = [
        {
            **issue,
            "location": {
                **issue["location"],
                "path": f"{prefix}{issue['location']['path']}",
            },
        }
        for issue in gitlab
    ]
    assert json.loads(captured.out) == gitlab_with_prefix


def test_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that malformed JSON input raises TypeError."""
    monkeypatch.setattr("sys.stdin", io.StringIO("{invalid json"))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])

    with pytest.raises(TypeError, match="Invalid JSON input"):
        main()


def test_non_dict_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that non-dict JSON input raises TypeError."""
    monkeypatch.setattr("sys.stdin", io.StringIO("[]"))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])

    with pytest.raises(TypeError, match="Input must be a JSON object"):
        main()


def test_warning_severity(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that warning severity is mapped to 'minor'."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "warning",
                "message": "Test warning",
                "range": {
                    "start": {"line": 1, "character": 0},
                    "end": {"line": 1, "character": 5},
                },
                "rule": "testRule",
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["severity"] == "minor"


def test_information_severity(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that information severity is mapped to 'minor'."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "information",
                "message": "Test info",
                "range": {
                    "start": {"line": 1, "character": 0},
                    "end": {"line": 1, "character": 5},
                },
                "rule": "testRule",
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["severity"] == "minor"


def test_missing_rule(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing rule field is handled with default."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "error",
                "message": "Test error",
                "range": {
                    "start": {"line": 1, "character": 0},
                    "end": {"line": 1, "character": 5},
                },
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["check_name"] == "pyright: unknown"


def test_empty_diagnostics(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test handling of empty generalDiagnostics list."""
    pyright = {"generalDiagnostics": []}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result == []


def test_missing_general_diagnostics(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test handling when generalDiagnostics key is missing."""
    pyright = {"version": "1.0", "summary": {}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result == []


def test_missing_range_field(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing range field defaults to -1 for all positions."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "error",
                "message": "Test error",
                "rule": "testRule",
                # Missing 'range' field entirely
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["location"]["positions"]["begin"]["line"] == -1
    assert result[0]["location"]["positions"]["begin"]["column"] == -1
    assert result[0]["location"]["positions"]["end"]["line"] == -1
    assert result[0]["location"]["positions"]["end"]["column"] == -1


def test_missing_start_in_range(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing start field in range defaults to -1."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "error",
                "message": "Test error",
                "rule": "testRule",
                "range": {
                    # Missing 'start' field
                    "end": {"line": 10, "character": 20}
                },
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["location"]["positions"] == {
        "begin": {"line": -1, "column": -1},
        "end": {"line": 10, "column": 20},
    }


def test_missing_end_in_range(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing end field in range defaults to -1."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "error",
                "message": "Test error",
                "rule": "testRule",
                "range": {
                    "start": {"line": 5, "character": 10},
                    # Missing 'end' field
                },
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["location"]["positions"] == {
        "begin": {"line": 5, "column": 10},
        "end": {"line": -1, "column": -1},
    }


def test_missing_line_in_start(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing line field in start position defaults to -1."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "error",
                "message": "Test error",
                "rule": "testRule",
                "range": {
                    "start": {
                        # Missing 'line' field
                        "character": 10
                    },
                    "end": {"line": 10, "character": 20},
                },
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["location"]["positions"] == {
        "begin": {"line": -1, "column": 10},
        "end": {"line": 10, "column": 20},
    }


def test_missing_character_in_end(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing character field in end position defaults to -1."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "error",
                "message": "Test error",
                "rule": "testRule",
                "range": {
                    "start": {"line": 5, "character": 10},
                    "end": {
                        "line": 10,
                        # Missing 'character' field
                    },
                },
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["location"]["positions"]["end"] == {"line": 10, "column": -1}


def test_missing_file_field(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing file field defaults to '<anonymous>'."""
    pyright = {
        "generalDiagnostics": [
            {
                # Missing 'file' field
                "severity": "error",
                "message": "Test error",
                "rule": "testRule",
                "range": {
                    "start": {"line": 5, "character": 10},
                    "end": {"line": 10, "character": 20},
                },
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["location"]["path"] == "<anonymous>"


def test_missing_message_field(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that missing message field defaults to empty string."""
    pyright = {
        "generalDiagnostics": [
            {
                "file": "test.py",
                "severity": "error",
                # Missing 'message' field
                "rule": "testRule",
                "range": {
                    "start": {"line": 5, "character": 10},
                    "end": {"line": 10, "character": 20},
                },
            }
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert len(result) == 1
    assert result[0]["description"] == ""


def test_completely_empty_issue(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that a completely empty issue is handled with all defaults."""
    pyright = {
        "generalDiagnostics": [
            {}  # Completely empty issue
        ]
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(pyright)))
    monkeypatch.setattr("sys.argv", ["pyright_to_gitlab.py"])
    main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result == [
        {
            "check_name": "pyright: unknown",
            "description": "",
            "fingerprint": "751a157014b31820ec789f6f9cce28599122b8b56b628230f339ea2d",
            "severity": "minor",
            "location": {
                "path": "<anonymous>",
                "positions": {
                    "begin": {"line": -1, "column": -1},
                    "end": {"line": -1, "column": -1},
                },
            },
        }
    ]
