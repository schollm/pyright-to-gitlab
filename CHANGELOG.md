# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Upcoming]


## [1.3.1] - 2026-04-09
### Fixed
- Fix entry point: `pyright-to-gitlab` command was broken due to referencing non-existent `main` instead of `cli`.
## [1.3.0] - 2026-02-03

### Fixes
- Use Hash algorithm that is compatible with Python 3.8 and above, to support Python 3.7 up to 3.14.
- Documentation: Clarify that --prefix takes a path as an argument.
- Change hash algorithm to md5 for better compatibility.
## [1.2.0] - 2026-01-22

### Fixes
- Use 0 instead of (invalid) -1 as default line and column number for diagnostics without location.
- Treat missing json fields without crashing.

### Changes
- Minimum version is now 3.8.
- Use TypedDict for Pyright and Gitlab issue handling.
- Update test dependencies to latest.
- Add --input/--output file options

## [1.1.0] - 2025-06-03
### Added
- Support for -i/--input and -o/--output options to specify input and output files.

## [1.0.2] - 2025-06-02
### Added
- URLs and topics to pyproject.toml for PyPI metadata.
- Advertise the no-dependency in the README.md.

## [1.0.1] - 2025-06-02
- Support for custom path prefix with the `--prefix` option.
## [1.0.0] - 2025-06-02
Initial release.

