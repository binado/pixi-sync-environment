## v0.3.0 (2025-11-24)

### Feat

- refactor code to use native pixi workspace export command (#6)

## v0.2.1 (2025-11-23)

### Fix

- pypi package version pinning is broken in generated environment file (#2)

## v0.2.0 (2025-10-13)

### Feat

- add --check flag to cli script that does not update files

### Fix

- **hook**: update pre-commit hook config
- remove explicit logging config
- add better error handling when interacting with pixi commands

### Refactor

- move main entrypoint to a dedicated cli module
- add better type hints and docstrings

## v0.1.3 (2025-08-12)

### Fix

- fix typo in argument name
- update usage instructions with correct version in README

## v0.1.2 (2025-08-12)

### Fix

- update include-conda-channels flag to default to positive
- update executable in entry property of hook config

## v0.1.1 (2025-08-12)

### Feat

- add option to specify environment flag for pixi list
- add source code

### Fix

- rename package
- pass explicit manifest-path parameter to pixi list
- admit config file as positional argument
- trigger hook with pixi.toml or environment.yml as well
- rewrite program description
- remove unused requirements.txt file
- remove old workflow ci job
