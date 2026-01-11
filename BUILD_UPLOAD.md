# Building and Uploading to PyPI

This guide explains how to build and upload the `icloudpdlp` package to PyPI.

## Prerequisites

Install the required build tools:

```bash
pip install build twine
```

## Building the Package

1. Make sure all your code is ready and tested
2. Update the version number in `pyproject.toml` and `src/icloudpdlp/__init__.py`
3. Build the distribution packages:

```bash
python -m build
```

This creates two files in the `dist/` directory:
- A source distribution (`.tar.gz`)
- A wheel distribution (`.whl`)

## Testing the Build

Before uploading to PyPI, test your package locally:

```bash
pip install dist/icloudpdlp-0.1.0-py3-none-any.whl
icloudpdlp --help
```

## Uploading to PyPI

### Test PyPI (Recommended First)

1. Create an account at https://test.pypi.org
2. Upload to Test PyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

3. Test installation from Test PyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ icloudpdlp
```

### Production PyPI

1. Create an account at https://pypi.org
2. Upload to PyPI:

```bash
python -m twine upload dist/*
```

3. Your package will be available at: https://pypi.org/project/icloudpdlp/

## Using API Tokens (Recommended)

For security, use API tokens instead of passwords:

1. Go to your PyPI account settings
2. Create an API token
3. When prompted for username, enter `__token__`
4. When prompted for password, enter your token (including the `pypi-` prefix)

Or configure in `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
username = __token__
password = pypi-your-test-token-here
```

## Workflow Summary

1. Update version numbers
2. Run tests: `pytest`
3. Build: `python -m build`
4. Upload to Test PyPI: `python -m twine upload --repository testpypi dist/*`
5. Test installation from Test PyPI
6. Upload to PyPI: `python -m twine upload dist/*`

## Clean Build

To start fresh, remove old builds:

```bash
rm -rf build/ dist/ src/*.egg-info
```
