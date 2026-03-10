Export script scaffold

Usage:

1. Install or obtain a command-line converter (e.g., ODA File Converter, vendor CLI).
2. Set environment variable `CAD_EXPORT_CMD` to a command template that accepts `{src}` and `{dst}`.
   Example (Windows PowerShell):

   ```powershell
   $env:CAD_EXPORT_CMD = 'ODAFileConverter.exe "{src}" "{dst}"'
   ```

3. Dry-run to review commands:

   ```powershell
   python scripts\export_dxf.py --dry-run
   ```

4. Run actual conversion once configured:

   ```powershell
   python scripts\export_dxf.py
   ```

Notes:
...

Docker fallback

If contributors or CI runners don't have a native converter, you can use the included Docker image.

Build the converter locally:

```bash
docker build -t cad-converter docker/cad-converter
```

Run conversion inside Docker (example):

```bash
./scripts/docker_export.sh --src "Drawings/CAD/Project/CAF-Lab-Floorplan-DWG001_rev02.dwg" --add-git
```

On CI the workflow will automatically build the Docker image and use it as a fallback when `CAD_EXPORT_CMD` is not set.
Export script scaffold

Usage:

1. Install or obtain a command-line converter (e.g., ODA File Converter, vendor CLI).
2. Set environment variable `CAD_EXPORT_CMD` to a command template that accepts `{src}` and `{dst}`.
   Example (Windows PowerShell):

```powershell
$env:CAD_EXPORT_CMD = 'ODAFileConverter.exe "{src}" "{dst}"'
```

3. Dry-run to review commands:

```powershell
python scripts\export_dxf.py --dry-run
```

4. Run actual conversion once configured:

```powershell
python scripts\export_dxf.py
```

Notes:
- The script is intentionally minimal and delegates actual conversion to an external tool.
- You can adapt the script to call vendor SDKs if available.

CI verification

Add the GitHub Actions workflow at `.github/workflows/cad-exports.yml`. The workflow expects `CAD_EXPORT_CMD` to be configured in the environment (repo variables or runner). On PRs it runs `python scripts/export_dxf.py --check-only` and then fails the job if `git diff --exit-code` reports changes. This ensures exports are present and up-to-date.

Git hook:

1. Copy `.githooks/pre-commit` to your repo's `.git/hooks/pre-commit` and make it executable:

```powershell
copy .githooks\pre-commit .git\hooks\pre-commit
```

On Unix/macOS:

```bash
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

2. The hook runs `python scripts/pre_commit_checks.py` which validates filenames, checks for `project-metadata.json` with `units`, warns about missing title blocks for text-based drawing sources, and warns if exported PDFs are out of date.

Adjust the script as needed for stricter/looser policies.
