"""Convert pyright.json output to GitLab Code Quality report format."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import textwrap
from typing import Any, TextIO, TypedDict, cast


### Typing for PyRight Issue
class PyrightRangeElement(TypedDict):
    """Pyright Range Element (part of Range)."""

    line: int
    character: int


class PyrightRange(TypedDict):
    """Pyright Range (Part of Issue)."""

    start: PyrightRangeElement
    end: PyrightRangeElement


class PyrightIssue(TypedDict):
    """Single Pyright Issue."""

    file: str
    severity: str
    message: str
    rule: str
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
    severity: str
    fingerprint: str
    check_name: str
    location: GitlabIssueLocation


### Functions
def _pyright_to_gitlab(input_: TextIO, prefix: str = "") -> str:
    """Convert pyright.json output to GitLab Code Quality report format.

    :arg prefix: A string to prepend to each file path in the output.
        This is useful if the application is in a subdirectory of the repository.
    :return: JSON of issues in GitLab Code Quality report format.

    Pyright format at https://github.com/microsoft/pyright/blob/main/docs/command-line.md
    Gitlab format at https://docs.gitlab.com/ci/testing/code_quality/#code-quality-report-format
    """
    data = cast("dict", json.load(input_))
    return json.dumps(
        [
            _pyright_issue_to_gitlab(issue, prefix)
            for issue in data.get("generalDiagnostics", [])
        ],
        indent=2,
    )


def _pyright_issue_to_gitlab(issue: PyrightIssue, prefix: str) -> GitlabIssue:
    """Convert a single issue to gitlab.

    :param issue: A pyright single issue.
    :param prefix: The path prefix.
    :returns: A gitlab single issue.
    """
    start, end = issue["range"]["start"], issue["range"]["end"]
    rule = "pyright: " + issue.get("rule", "")
    # unique fingerprint
    fp_str = "--".join([str(start), str(end), rule])

    return GitlabIssue(
        description=issue["message"],
        severity="major" if issue["severity"] == "error" else "minor",
        fingerprint=hashlib.sha3_224(fp_str.encode()).hexdigest(),
        check_name=rule,
        location=GitlabIssueLocation(
            path=f"{prefix}{issue['file']}",
            positions=GitlabIssuePositions(
                begin=GitlabIssuePositionLocation(
                    line=start["line"], column=start["character"]
                ),
                end=GitlabIssuePositionLocation(
                    line=end["line"], column=end["character"]
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
    args = parser.parse_args()
    args.output.write(_pyright_to_gitlab(input_=args.input, prefix=args.prefix))


if __name__ == "__main__":  # pragma: no cover
    main()
