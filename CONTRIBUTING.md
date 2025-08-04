# Contributing to Mactoro

Thank you for your interest in contributing to Mactoro! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept responsibility for mistakes

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

1. **Clear title and description**
2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **System information** (macOS version, Python version)
6. **Screenshots** if applicable
7. **Error messages** and stack traces

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

1. **Clear title and description**
2. **Use case** - why is this enhancement needed?
3. **Proposed solution**
4. **Alternative solutions** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the code style** - use Black for formatting
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Ensure tests pass** before submitting
6. **Write a clear PR description**

## Development Setup

1. Clone your fork:
```bash
git clone https://github.com/your-username/mactoro.git
cd mactoro
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking

Run these tools before committing:

```bash
black mactoro tests
ruff check mactoro tests
mypy mactoro
```

Or use pre-commit to run automatically:
```bash
pre-commit run --all-files
```

## Testing

We use pytest for testing. Run tests with:

```bash
pytest
```

For coverage report:
```bash
pytest --cov=mactoro --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow the naming convention: `test_*.py`
- Write descriptive test names that explain what is being tested
- Use fixtures for common test data
- Mock external dependencies (especially macOS APIs)

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions and classes
- Update CLI help text when adding/changing commands
- Include examples in documentation

### Docstring Format

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception is raised
    """
```

## Commit Messages

Follow these guidelines for commit messages:

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 50 characters
- Reference issues and pull requests
- Use conventional commits format when possible:
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation changes
  - `style:` Code style changes (formatting, etc.)
  - `refactor:` Code changes that neither fix bugs nor add features
  - `test:` Adding or updating tests
  - `chore:` Maintenance tasks

Example:
```
feat: Add window filtering by application name

- Add --app flag to window list command
- Support partial name matching
- Update documentation

Fixes #123
```

## Release Process

1. Update version in `pyproject.toml`, `setup.py`, and `mactoro/__init__.py`
2. Update CHANGELOG.md
3. Create a pull request with these changes
4. After merging, create a GitHub release
5. Build and publish to PyPI

## Questions?

If you have questions, feel free to:

1. Check existing issues and discussions
2. Create a new issue with the "question" label
3. Reach out to maintainers

Thank you for contributing to Mactoro!