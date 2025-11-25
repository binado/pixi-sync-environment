# pixi-sync-environment

[![Test](https://github.com/binado/pixi-sync-environment/actions/workflows/test.yml/badge.svg)](https://github.com/binado/pixi-sync-environment/actions/workflows/test.yml)

A pre-commit hook and CLI tool that generates conda `environment.yml` files from pixi projects using `pixi workspace export conda-environment`. Useful for maintaining compatibility with conda-based workflows and CI systems that don't support pixi.

The tool compares the generated environment with an existing `environment.yml` file (if present) and updates it only when changes are detected. In check mode, it reports differences without modifying files.

## Installation

```bash
pip install pixi-sync-environment
```

## CLI Usage

```bash
# Sync pixi environment to environment.yml
pixi_sync_environment pixi.toml

# Sync a specific pixi environment
pixi_sync_environment --environment dev pixi.toml

# Check mode (exits with code 1 if out of sync)
pixi_sync_environment --check pixi.toml
```

### Options

```
positional arguments:
  input_files                    Path to pixi.toml, pyproject.toml, environment.yml, or pixi.lock

options:
  --environment-file FILE        Output file name (default: environment.yml)
  --environment ENV              Pixi environment to export (default: default)
  --name NAME                    Environment name in output file
  --check                        Verify sync status without modifying files
```

## Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.3.0
    hooks:
      - id: pixi-sync-environment
        # args: [--environment, dev, --environment-file, environment-dev.yml]
```

For check-only validation (useful in CI):

```yaml
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.3.0
    hooks:
      - id: pixi-sync-check
```

## License

MIT
