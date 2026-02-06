# Changelog

All notable changes to this repository will be documented in this file.

## v0.1.0 - 2026-01-27

Highlights:

- Argparse CLI rewrite for `auto_drawing_check.py` with clear positional arguments and help text.
- New `--strict` mode: treat missing inputs as errors and return explicit exit codes.
- Logging improvements: `--log-level` to control logging verbosity; logs go to stderr while JSON results remain on stdout.
- `--out` option: write JSON output to file for CI/automation consumption.
- Exception hygiene: replaced broad `except Exception` patterns with targeted exception handling in key scripts.
- Unit tests and CI: added pytest tests for CLI behavior and a GitHub Actions workflow to run tests on PRs and pushes.

Full details: see the merged PR `enhance/auto_drawing_cli` which contains the implementation and tests.

### Unreleased

- Scoped workspace autoApprove improvements: allow release/* branch pushes, -n=dev shortcuts, and prod PowerShell guards
