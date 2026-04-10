# pyright to gitlab

[![PyPI version](https://img.shields.io/pypi/v/pyright-to-gitlab.svg)](https://pypi.org/project/pyright-to-gitlab)
[![Python versions](https://img.shields.io/pypi/pyversions/pyright-to-gitlab.svg)](https://pypi.org/project/pyright-to-gitlab)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Typing: typed](https://img.shields.io/badge/typing-typed-blue.svg)](https://github.com/python/mypy)

Simple Python tool to convert Pyright JSON output to GitLab Code Quality report format.

**Zero runtime dependencies** - Pure Python implementation using only the standard library.

## Install
You can install the package from PyPI using pip:
```shell
pip install pyright-to-gitlab
```

Or make it available globally:
* via `pipx`: 
  ```shell
  pipx install pyright-to-gitlab
  ```
* via `uv`: 
  ```shell
  uv tool install pyright-to-gitlab
  ```
As a one-time use, you can also run it directly with `uvx`:
```shell
uvx pyright-to-gitlab --help
```

Or download the single source file and run it with Python:
```shell
wget https://raw.githubusercontent.com/schollm/pyright-to-gitlab/refs/heads/main/src/pyright_to_gitlab.py -O pyright_to_gitlab.py
python pyright_to_gitlab.py --help
```

## Usage

```text
pyright-to-gitlab --help
usage: pyright-to-gitlab [-h] [-i INPUT] [-o OUTPUT] [--prefix PATH_PREFIX] [--version]

Convert Pyright JSON output to a GitLab Code Quality report.

Input defaults to stdin and output defaults to stdout.
Use '-' explicitly for stdin/stdout when mixing with file paths.

options:
  -h, --help            show this help message and exit
  -i, --input INPUT     Path to Pyright JSON input (default: -). Use - to read from stdin.
  -o, --output OUTPUT   Path for GitLab Code Quality JSON (default: -). Use - to write to stdout.
  --prefix PATH_PREFIX  Prefix added to each reported file path, e.g. 'backend/' for monorepos.
  --version             show program's version number and exit

Examples:
  pyright . --outputjson | pyright-to-gitlab > gl-code-quality.json
  pyright-to-gitlab -i pyright.json -o gl-code-quality.json
  pyright-to-gitlab --prefix backend/ -i pyright.json -o -
  pyright-to-gitlab -i pyright.json
```

Convert from stdin to stdout (typical pipeline):
```shell
pyright . --outputjson | pyright-to-gitlab > code-quality.json
```

Convert from file to file:
```shell
pyright-to-gitlab -i pyright.json -o code-quality.json
```

Run as a module:
```shell
pyright . --outputjson | python -m pyright_to_gitlab > code-quality.json
```

### Custom path prefix
The `--prefix` option adds a custom prefix path to the file paths in the output. This is
useful for mono-repos, where the paths in the pyright output are not the repository root.


```shell
pyright . --outputjson | pyright-to-gitlab --prefix my-app > code-quality.json
```
## Development
### Testing
To run the tests, execute
```shell
uv run poe check
```
