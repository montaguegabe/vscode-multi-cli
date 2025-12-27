# Contributing

Thank you for your interest in contributing to Multi!

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Clone the Repository

```bash
git clone https://github.com/gabemontague/multi.git
cd multi/multi-cli
```

### Install Dependencies

Using uv (recommended):

```bash
uv sync --extra dev
```

Using pip:

```bash
pip install -e ".[dev]"
```

### Verify Setup

```bash
# Run the CLI
multi --help

# Run tests
pytest
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=multi --cov-report=html

# Run specific test file
pytest tests/test_sync.py

# Run tests matching a pattern
pytest -k "test_init"
```

### Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

The project uses Python type hints. Ensure your code includes appropriate type annotations.

## Project Structure

```
multi-cli/
├── multi/              # Main package
│   ├── cli.py          # CLI entry point and command registration
│   ├── cli_helpers.py  # Command wrapper and utilities
│   ├── init.py         # init command implementation
│   ├── sync.py         # sync command implementation
│   ├── sync_vscode*.py # VS Code config merging
│   ├── sync_claude.py  # CLAUDE.md generation
│   ├── git_*.py        # Git operations
│   ├── repos.py        # Repository management
│   ├── settings.py     # Configuration handling
│   └── ...
├── tests/              # Test files
├── docs/               # Documentation
├── pyproject.toml      # Project configuration
└── zensical.toml       # Documentation config
```

## Making Changes

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for new functionality

4. **Run the test suite** to ensure everything passes:
   ```bash
   pytest
   ruff check .
   ```

5. **Commit your changes** with a descriptive message

6. **Push and create a pull request**

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update documentation if needed
- Ensure all tests pass
- Follow the existing code style

## Building Documentation

To preview documentation locally:

```bash
# Install docs dependencies
uv sync --extra dev

# Serve documentation locally
zensical serve
```

Then open http://localhost:8000 in your browser.

## Reporting Issues

Found a bug or have a feature request? Please [open an issue](https://github.com/gabemontague/multi/issues) on GitHub.

When reporting bugs, please include:

- Your Python version
- Your operating system
- Steps to reproduce the issue
- Expected vs actual behavior
