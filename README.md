# pyright to gitlab
Simple zero-dependency Python script to convert a pyright --outputjson to a gitlab 
code-quality report.

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
