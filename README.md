# pre-commit-check-office-metadata
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pre-commit-check-office-metadata/0.7.0?logo=python&logoColor=FFD43B)](https://pypi.org/project/pre-commit-check-office-metadata/)
[![PyPI](https://img.shields.io/pypi/v/pre-commit-check-office-metadata?logo=Python&logoColor=FFD43B)](https://pypi.org/project/pre-commit-check-office-metadata/)
[![PyPI - License](https://img.shields.io/pypi/l/pre-commit-check-office-metadata?color=magenta)](https://github.com/sco1/pre-commit-check-office-metadata/blob/main/LICENSE)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sco1/pre-commit-check-office-metadata/main.svg)](https://results.pre-commit.ci/latest/github/sco1/pre-commit-check-office-metadata/main)

Check for the presence of identifying metadata in modern Office files

## Using `pre-commit-check-office-metadata` with pre-commit
Add this to your `.pre-commit-config.yaml`

```yaml
-   repo: https://github.com/sco1/pre-commit-check-office-metadata
    rev: v0.1.0
    hooks:
    - id: check-metadata
```

## Hooks
### `check-metadata`
...

## Python Version Support
A best attempt is made to support Python versions until they reach EOL, after which support will be formally dropped by the next minor or major release of this package, whichever arrives first. The status of Python versions can be found [here](https://devguide.python.org/versions/).