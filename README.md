# pyright to gitlab

[![PyPI version](https://img.shields.io/pypi/v/pyright-to-gitlab.svg)](https://pypi.org/project/pyright-to-gitlab)
[![Python versions](https://img.shields.io/pypi/pyversions/pyright-to-gitlab.svg)](https://pypi.org/project/pyright-to-gitlab)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Typing: typed](https://img.shields.io/badge/typing-typed-blue.svg)](https://github.com/python/mypy)

Simple Python tool to convert Pyright JSON output to GitLab Code Quality report format.

**Zero runtime dependencies** - Pure Python implementation using only the standard library.


## Usage
Run the script with the path to the pyright output file:
```shell
$ pip install pyright-to-gitlab
$  pyright . --outputjson | pyright-to-gitlab > code-quality.json 
```

Alternatively, the module can be called:
```shell
$ pip install pyright-to-gitlab
$  pyright . --outputjson | python -m pyright_to_gitlab > code-quality.json 
```
### Custom path prefix
The `--prefix` option adds a custom prefix to the file paths in the output. This is
useful if the paths in the pyright output are not relative to the root of the repository.


```shell
$  pyright . --outputjson | pyright-to-gitlab --prefix my-app/ > code-quality.json 
```

## Testing
To run the tests, execute
```shell
$ uv run pytest tests/
```
