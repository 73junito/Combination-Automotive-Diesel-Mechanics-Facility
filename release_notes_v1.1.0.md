Features:
- Replaced manual argv parsing with argparse
- Added --strict flag: missing PDF/DXF triggers exit 2 (EXIT_INPUT)
- Added --log-level (DEBUG, INFO, WARN, ERROR), logs go to stderr
- Added --out <file> to write JSON results to disk; write errors trigger EXIT_VALIDATION
- Preserved default behavior: missing files without --strict return EXIT_OK

Improvements:
- Replaced prints with structured logging
- Exception hygiene: narrowed broad excepts in high-value scripts
- Smoke-tested CLI and unit-tested argparse, logging, strict mode, and output file writing
