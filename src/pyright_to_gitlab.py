"""Convert pyright.json output to GitLab Code Quality report format."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import textwrap
from pathlib import Path
from typing import Literal, TypedDict

VERSION = "1.3.2"  # do not use importlib to allow for direct script download.


### Typing for PyRight Issue
class PyrightRangeElement(TypedDict, total=False):
    """Pyright Range Element (part of Range)."""

    line: int
    character: int


class PyrightRange(TypedDict, total=False):
    """Pyright Range (Part of Issue)."""

    start: PyrightRangeElement
    end: PyrightRangeElement


class PyrightIssue(TypedDict, total=False):
    """Single Pyright Issue.

    Note: total=False makes all fields optional. Runtime code handles this with
    defensive .get() calls.
    """

    file: str
    severity: Literal["error", "warning", "information"]
    message: str
    rule: str  # Optional in practice, handled via .get() at runtime
    range: PyrightRange


### Typing for Gitlab Issue
class GitlabIssuePositionLocation(TypedDict):
    """Single Gitlab Position (Part of Position)."""

    line: int
    column: int


class GitlabIssuePositions(TypedDict):
    """Gitlab ranged Position within a file (Part of Location)."""

    begin: GitlabIssuePositionLocation
    end: GitlabIssuePositionLocation


class GitlabIssueLocation(TypedDict):
    """Gitlab location (Part of Issue)."""

    path: str
    positions: GitlabIssuePositions


class GitlabIssue(TypedDict):
    """Single Gitlab Issue."""

    description: str
    severity: Literal["major", "minor"]
    fingerprint: str
    check_name: str
    location: GitlabIssueLocation


### Functions
def _pyright_to_gitlab(input_: str, prefix: str = "") -> str:
    """Convert pyright.json output to GitLab Code Quality report format.

    Line numbers from Pyright are passed through unchanged (0-based per LSP spec).
    GitLab expects the same format, so no conversion is needed.

    :arg prefix: A path to prepend to each file path in the output.
        This is useful if the application is in a subdirectory of the repository.
    :return: JSON of issues in GitLab Code Quality report format.
    :raises ValueError: If input is not a JSON object.
    :raises TypeError: If input JSON is not an object.

    Pyright format at https://github.com/microsoft/pyright/blob/main/docs/command-line.md
    Gitlab format at https://docs.gitlab.com/ci/testing/code_quality/#code-quality-report-format
    """
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    try:
        data_raw = (
            sys.stdin.read()
            if input_ == "-"
            else Path(input_).read_text(encoding="utf-8")
        )
        data = json.loads(data_raw)
    except (OSError, UnicodeError) as e:
        source = "stdin" if input_ == "-" else input_
        err_msg = f"Unable to read input from {source!r}: {e}"
        raise ValueError(err_msg) from e
    except json.JSONDecodeError as e:
        err_msg = f"Invalid JSON input: {e}"
        raise ValueError(err_msg) from e

    if not isinstance(data, dict):
        err_msg = "Input must be a JSON object"
        raise TypeError(err_msg)

    return json.dumps(
        [
            _pyright_issue_to_gitlab(issue, prefix)
            for issue in data.get("generalDiagnostics", [])
        ],
        indent=2,
    )


def _pyright_issue_to_gitlab(issue: PyrightIssue, prefix: str) -> GitlabIssue:
    """Convert a single issue to gitlab.

    Uses defensive .get() with defaults to handle missing optional fields.
    File path defaults to '<anonymous>' and missing rule to 'unknown'.

    :param issue: A pyright single issue.
    :param prefix: The path prefix.
    :returns: A gitlab single issue.
    """
    range_ = issue.get("range", {})
    start, end = (range_.get("start", {}), range_.get("end", {}))
    rule = "pyright: " + issue.get("rule", "unknown")
    # Hash input must contain file, location and rule to generate a unique fingerprint.
    # (This takes advantage of stable dict order).
    fingerprint = f"{issue.get('file', '<anonymous>')}--{range_}--{rule}"

    return GitlabIssue(
        description=issue.get("message", ""),
        # Map 'error' to 'major', all others, including empty, to 'minor'
        severity="major" if issue.get("severity") == "error" else "minor",
        # Any hash function really works, does not have to be cryptographic.
        fingerprint=_hash(fingerprint),
        check_name=rule,
        location=GitlabIssueLocation(
            path=f"{prefix}{issue.get('file', '<anonymous>')}",
            positions=GitlabIssuePositions(
                begin=GitlabIssuePositionLocation(
                    line=start.get("line", 0), column=start.get("character", 0)
                ),
                end=GitlabIssuePositionLocation(
                    line=end.get("line", 0), column=end.get("character", 0)
                ),
            ),
        ),
    )


def _hash(data: str) -> str:
    """Generate a (non-secure) hash of the given data string.

    :param data: The input string to hash.
    :returns: The hexadecimal representation of the MD5 hash.
    """
    return hashlib.new("md5", data.encode(), usedforsecurity=False).hexdigest()


def cli() -> None:
    """Parse arguments and call the conversion function."""
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
            Convert Pyright JSON output to a GitLab Code Quality report.

            Input defaults to stdin and output defaults to stdout.
            Use '-' explicitly for stdin/stdout when mixing with file paths."""),
        epilog=textwrap.dedent(
            """
            Examples:
              pyright . --outputjson | pyright-to-gitlab > gl-code-quality.json
              pyright-to-gitlab -i pyright.json -o gl-code-quality.json
              pyright-to-gitlab --prefix backend/ -i pyright.json -o -
              pyright-to-gitlab -i pyright.json --indent 0
            """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        metavar="INPUT",
        default="-",
        help="Path to Pyright JSON input (default: -). Use - to read from stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="-",
        metavar="OUTPUT",
        help="Path for GitLab Code Quality JSON (default: -)."
        " Use - to write to stdout.",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        metavar="PATH_PREFIX",
        default="",
        help="Prefix added to each reported file path, e.g. 'backend/' for monorepos.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    args = parser.parse_args()
    try:
        res = _pyright_to_gitlab(input_=args.input, prefix=args.prefix)
        if args.output == "-":
            sys.stdout.write(res)
        else:
            Path(args.output).write_text(res, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        parser.error(str(exc))


if __name__ == "__main__":  # pragma: no cover
    cli()
