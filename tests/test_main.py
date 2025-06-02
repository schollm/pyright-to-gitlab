"""Tests for the pyright_to_gitlab module."""

import io
import json

import pytest

from pyright_to_gitlab import _pyright_to_gitlab, main

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
        "fingerprint": "636af0d195f1115a2100087f399ea9759e20a6bf30494b881653eb7b",
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
        "fingerprint": "b0678d27f9d033a7176fcaf13dcfd449a7ec9cff211484ff730b32b2",
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
