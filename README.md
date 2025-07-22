# pre-commit-pixi-environment-file

Pre-commit hook to sync a pixi environment with a traditional conda environment.yml.
Useful tool if you want to keep an up-to-date `environment.yml`  in your project.

Easily customize the environment name, prefix, conda channels,
and whether to export pip packages or build names.


## Installation

To use it, register the hook in your `.pre-commit-config.yml`:

```yaml
repos:
  - repo: https://github.com/binado/pre-commit-pixi-environment-file
    rev: v0.1.0
    hooks:
      - id: sync-environments
        args: []

```

## Optional arguments:

You may specify additional arguments in the `args` property:

```bash
  --root-dir ROOT_DIR   Path to the root directory (default: .)
  --environment-file ENVIRONMENT_FILE
                        Name of the environment file (default:
                        environment.yml)
  --explicit            Use explicit package specifications (default: False)
  --name NAME           Environment name (optional) (default: None)
  --prefix PREFIX       Environment prefix path (optional) (default: None)
  --include-pip-packages
                        Include pip packages in the environment (default:
                        False)
  --no-include-conda-channels
                        Exclude conda channels from the environment (default:
                        include channels) (default: True)
  --include-build       Include build information (default: False)
```
