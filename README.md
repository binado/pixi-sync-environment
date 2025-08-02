# pixi-sync-environment

Pre-commit hook to sync a pixi environment with a traditional conda environment.yml.
Useful tool if you want to keep an up-to-date `environment.yml`  in your project.

Easily customize the environment name, prefix, conda channels,
and whether to export pip packages or build names.


## Installation

To use it, register the hook in your `.pre-commit-config.yml`:

```yaml
repos:
  - repo: https://github.com/binado/pixi-sync-environment
    rev: v0.1.0
    hooks:
      - id: pixi-sync-environment
        args: []
```

## Optional arguments:

You may specify additional arguments in the `args` property:

```bash
Compare and update conda environment files using pixi manifest

positional arguments:
  input_files           Path to configuration files
                        (pixi.toml/pyproject.toml/environment.yml/pixi.lock)

options:
  -h, --help            show this help message and exit
  --environment-file ENVIRONMENT_FILE
                        Name of the environment file (default:
                        environment.yml)
  --explicit            Use explicit package specifications (default: False)
  --name NAME           Environment name (optional) (default: None)
  --prefix PREFIX       Environment prefix path (optional) (default: None)
  --include-pip-packages
                        Include pip packages in the environment (default:
                        False)
  --include-conda-channels
                        Include conda channels from the environment (default:
                        True)
  --include-build       Include build information (default: False)
```
