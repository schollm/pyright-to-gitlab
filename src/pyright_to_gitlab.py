"""Convert pyright.json output to GitLab Code Quality report format."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import textwrap
from typing import Literal, TextIO, TypedDict


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
def _pyright_to_gitlab(input_: TextIO, prefix: str = "") -> str:
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
        data = json.load(input_)
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
    # Unique fingerprint including file path to prevent collisions across files
    # (This takes advantage of stable dict order).
    fp_str = f"{issue.get('file', '<anonymous>')}--{range_}--{rule}"

    return GitlabIssue(
        description=issue.get("message", ""),
        # Map 'error' to 'major', all others, including empty, to 'minor'
        severity="major" if issue.get("severity") == "error" else "minor",
        # Any hash function really works, does not have to be cryptographic.
        fingerprint=hashlib.md5(fp_str.encode(), usedforsecurity=False).hexdigest(),
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


def main() -> None:
    """Parse arguments and call the conversion function."""
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
        Convert pyright.json to GitLab Code Quality report.
        By default, reads from stdin and writes to stdout."""),
        epilog=textwrap.dedent(
            """

        Example usage:
        > python pyright . --outputjson | pyright-to-gitlab > gitlab_code_quality.json
        > pyright-to-gitlab -i pyright.json -o gitlab_code_quality.json
        """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Input file (default: stdin)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        help="Prefix to add to each file entry. This can be used if pyright is run"
        " from a subdirectory of the repository. (default: empty string)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()
    args.output.write(_pyright_to_gitlab(input_=args.input, prefix=args.prefix))


if __name__ == "__main__":  # pragma: no cover
    main()
