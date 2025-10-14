# pixi-sync-environment

[![Test](https://github.com/binado/pixi-sync-environment/actions/workflows/test.yml/badge.svg)](https://github.com/binado/pixi-sync-environment/actions/workflows/test.yml)

Pre-commit hook and CLI tool to sync a pixi environment with a traditional conda `environment.yml`.

**Why use this?** Keep an up-to-date `environment.yml` in your pixi projects for compatibility with traditional conda workflows. Easily customize the environment name, prefix, conda channels, and whether to export pip packages or build information.

## Features

- **Automatic Synchronization**: Automatically updates `environment.yml` when pixi manifest changes
- **Check Mode**: Verify sync status without modifying files (CI-friendly)
- **Flexible Configuration**: Customize environment name, channels, pip packages, and more
- **Fast**: Pure Python implementation with minimal dependencies
- **Multiple Use Cases**: Works as pre-commit hook or standalone CLI tool

## Installation

### As a Pre-commit Hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      - id: pixi-sync-environment
```

### As a Standalone Tool

Install with pip or uv:

```bash
pip install pixi-sync-environment
# or
uv tool install pixi-sync-environment
```

## Usage

### Pre-commit Hook

The hook automatically runs when `pixi.toml`, `pyproject.toml`, `pixi.lock`, or `environment.yml` changes:

```yaml
# Basic usage - sync with default settings
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      - id: pixi-sync-environment

# With custom environment name and pip packages
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      - id: pixi-sync-environment
        args: [--name, myproject, --include-pip-packages]

# Sync specific pixi environment to custom file
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      - id: pixi-sync-environment
        args: [--environment, dev, --environment-file, environment-dev.yml]

# Check-only mode (validate without modifying files)
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      - id: pixi-sync-check
```

### Standalone CLI Tool

#### Basic Sync

```bash
# Sync pixi environment to environment.yml
pixi_sync_environment pixi.toml

# Sync with custom environment name
pixi_sync_environment --name myproject pixi.toml

# Sync specific pixi environment
pixi_sync_environment --environment dev --environment-file environment-dev.yml pixi.toml
```

#### Check Mode (Read-Only)

Verify that files are in sync without modifying them. Useful for CI/CD:

```bash
# Check if environment.yml is in sync with pixi manifest
pixi_sync_environment --check pixi.toml

# Exit code 0: Files are in sync
# Exit code 1: Files are out of sync (shows diff)
```

Example in CI:

```yaml
# .github/workflows/ci.yml
- name: Verify environment.yml is up to date
  run: pixi_sync_environment --check pixi.toml
```

#### Advanced Options

```bash
# Include pip packages in environment.yml
pixi_sync_environment --include-pip-packages pixi.toml

# Include build strings for exact reproducibility
pixi_sync_environment --include-build pixi.toml

# Only include explicitly listed packages (no dependencies)
pixi_sync_environment --explicit pixi.toml

# Combine multiple options
pixi_sync_environment \
  --name myproject \
  --environment dev \
  --environment-file environment-dev.yml \
  --include-pip-packages \
  --include-build \
  pixi.toml
```

## Command-Line Options

```
positional arguments:
  input_files           Path to configuration files
                        (pixi.toml/pyproject.toml/environment.yml/pixi.lock)

options:
  -h, --help            Show this help message and exit

  --environment-file ENVIRONMENT_FILE
                        Name of the environment file (default: environment.yml)

  --environment ENVIRONMENT
                        Name of pixi environment to sync (default: default)

  --name NAME           Environment name to set in environment.yml (optional)

  --prefix PREFIX       Environment prefix path (optional)

  --explicit            Use explicit package specifications (exclude dependencies)
                        (default: False)

  --include-pip-packages
                        Include pip packages in the environment file
                        (default: False)

  --no-include-conda-channels
                        Exclude conda channels from the environment file
                        (default: includes channels)

  --include-build       Include build strings for exact reproducibility
                        (default: False)

  --check               Check if files are in sync without modifying them
                        Exits with code 1 if out of sync (default: False)
```

## Examples

### Example 1: Basic Project Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      - id: pixi-sync-environment
```

This will create/update `environment.yml` whenever your pixi files change.

### Example 2: Multiple Environments

Sync different pixi environments to different files:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      # Production environment
      - id: pixi-sync-environment
        name: Sync production environment
        args: [--environment, default, --environment-file, environment.yml]

      # Development environment with pip packages
      - id: pixi-sync-environment
        name: Sync dev environment
        args: [--environment, dev, --environment-file, environment-dev.yml, --include-pip-packages]
```

### Example 3: CI/CD Validation

Ensure `environment.yml` stays in sync in your CI pipeline:

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install pixi
        uses: prefix-dev/setup-pixi@v0.8.1

      - name: Check environment.yml is up to date
        run: |
          pip install pixi-sync-environment
          pixi_sync_environment --check pixi.toml
```

### Example 4: Check-Only Hook (Validation)

Use the check-only hook to validate without automatically syncing:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.3
    hooks:
      - id: pixi-sync-check
```

This fails the pre-commit check if files are out of sync, prompting you to run the sync manually. Useful when you want explicit control over when files are updated.

### Example 5: Exact Reproducibility

For maximum reproducibility, include build strings:

```bash
pixi_sync_environment --include-build --explicit pixi.toml
```

This generates `environment.yml` with exact package versions and build strings:

```yaml
dependencies:
  - python=3.10.12=h4499717_0_cpython
  - numpy=1.24.3=py310h8deb116_1
  - pandas=2.0.2=py310h8deb116_0
```

## How It Works

1. **Reads** your pixi manifest (`pixi.toml` or `pyproject.toml`)
2. **Executes** `pixi list --json` to get the current environment packages
3. **Parses** the package information (conda and PyPI packages)
4. **Generates** a conda-compatible `environment.yml`
5. **Compares** with existing file (if any)
6. **Updates** the file only if changed (or shows diff in check mode)

## Manifest File Support

The tool automatically detects and uses your pixi manifest:

- **`pixi.toml`**: Preferred, used if present
- **`pyproject.toml`**: Used if `pixi.toml` not found (must have `[tool.pixi]` section)

## Use Cases

### For Conda Users

Transitioning to pixi but need to maintain `environment.yml` for teammates still using conda:

```bash
pixi_sync_environment --name my-project pixi.toml
```

### For CI/CD Pipelines

Many CI services support conda but not pixi yet. Keep `environment.yml` in sync:

```yaml
- name: Setup conda
  uses: conda-incubator/setup-miniconda@v3
  with:
    environment-file: environment.yml
```

### For Documentation

Keep environment files up-to-date in your documentation:

```bash
pixi_sync_environment --include-pip-packages pixi.toml
```

### For Reproducibility

Archive exact package versions for long-term reproducibility:

```bash
pixi_sync_environment --include-build --explicit pixi.toml
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/binado/pixi-sync-environment
cd pixi-sync-environment

# Install dependencies with uv
uv sync --group test --group lint

# Or with pixi
pixi install
```

### Testing

```bash
# Run tests
uv run pytest tests/ -v

# Run linting
uv run ruff check .

# Run formatting
uv run ruff format .
```

See [TESTS.md](TESTS.md) for detailed testing documentation.

### Documentation

- [CLAUDE.md](CLAUDE.md): Architecture and development guide
- [TESTS.md](TESTS.md): Testing structure and practices
- [IMPROVEMENTS.md](IMPROVEMENTS.md): Planned features and improvements

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `uv run pytest tests/`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [pixi](https://github.com/prefix-dev/pixi) - Package management made easy
- [conda](https://github.com/conda/conda) - Package, dependency and environment management
- [pre-commit](https://pre-commit.com/) - A framework for managing git pre-commit hooks
