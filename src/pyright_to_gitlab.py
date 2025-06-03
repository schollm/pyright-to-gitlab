"""Convert pyright.json output to GitLab Code Quality report format."""

import argparse
import hashlib
import json
import sys
import textwrap
from typing import TextIO, cast


def _pyright_to_gitlab(input_: TextIO, prefix: str = "") -> str:
    """Convert pyright.json output to GitLab Code Quality report format.

    :arg prefix: A string to prepend to each file path in the output.
        This is useful if the application is in a subdirectory of the repository.
    :return: JSON of issues in GitLab Code Quality report format.

    Pyright format at https://github.com/microsoft/pyright/blob/main/docs/command-line.md
    Gitlab format at https://docs.gitlab.com/ci/testing/code_quality/#code-quality-report-format
    """
    data = cast("dict", json.load(input_))

    issues = []
    for issue in data.get("generalDiagnostics", []):
        file = issue["file"]
        start, end = issue["range"]["start"], issue["range"]["end"]
        rule = "pyright: " + issue.get("rule", "")
        severity = "major" if issue["severity"] == "error" else "minor"
        # unique fingerprint
        fp_str = "--".join([str(start), str(end), rule])

        issues.append(
            {
                "description": issue["message"],
                "severity": severity,
                "fingerprint": hashlib.sha3_224(fp_str.encode()).hexdigest(),
                "check_name": rule,
                "location": {
                    "path": f"{prefix}{file}",
                    "positions": {
                        "begin": {"line": start["line"], "column": start["character"]},
                        "end": {"line": end["line"], "column": end["character"]},
                    },
                },
            }
        )
    return json.dumps(issues, indent=2)


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
