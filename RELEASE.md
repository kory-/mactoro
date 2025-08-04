# Release Process

This document describes the process for releasing new versions of Mactoro.

## Pre-release Checklist

1. **Update Version Numbers**
   - Update version in `pyproject.toml`
   - Update version in `setup.py`
   - Update version in `mactoro/__init__.py`

2. **Update Documentation**
   - Update CHANGELOG.md with release notes
   - Update README.md if needed
   - Check all documentation is up to date

3. **Run Tests**
   ```bash
   pytest
   black --check mactoro tests
   ruff check mactoro tests
   mypy mactoro
   ```

4. **Build and Test Package**
   ```bash
   python -m build
   pip install dist/mactoro-*.whl
   mactoro --version
   ```

## Release to PyPI

1. **Test Release (Optional)**
   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ mactoro
   ```

2. **Production Release**
   ```bash
   twine upload dist/*
   ```

## GitHub Release

1. **Create Git Tag**
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. **Create GitHub Release**
   - Go to https://github.com/kory-/mactoro/releases
   - Click "Create a new release"
   - Select the tag
   - Add release notes from CHANGELOG.md
   - Upload built wheels and source distribution

## Update Homebrew Formula

1. **Calculate SHA256**
   ```bash
   curl -L https://github.com/kory-/mactoro/archive/v0.1.0.tar.gz | sha256sum
   ```

2. **Update Formula**
   - Update `mactoro.rb` with new version and SHA256
   - Test locally:
     ```bash
     brew install --build-from-source mactoro.rb
     ```

3. **Submit to Homebrew**
   - Fork homebrew-core
   - Update formula
   - Submit pull request

## Post-release

1. **Announce Release**
   - Update project website/blog if applicable
   - Post on social media if desired

2. **Start Next Development Cycle**
   - Update version to next development version (e.g., 0.2.0.dev0)
   - Add new "Unreleased" section to CHANGELOG.md