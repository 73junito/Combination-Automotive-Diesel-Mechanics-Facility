collect_updated_files.ps1
=========================

Purpose
-------
Small helper to copy recently modified PDF and PNG files from the project `outputs` folder into the scripts `outputs` folder, and optionally create a zip for quick upload or review.

Usage
-----
Open PowerShell in the repository root and run (adjust paths if your layout differs):

```powershell
# collect PDF/PNG changed in last 24 hours and create visuals_bundle.zip
.\Python_Workflow\scripts\collect_updated_files.ps1 -SinceMinutes 1440 -ZipName visuals_bundle.zip -Force

# collect files changed in last 60 minutes without zipping
.\Python_Workflow\scripts\collect_updated_files.ps1 -SinceMinutes 60
```

Parameters
----------
- `-SourceDir` : relative path (from script) to search for updated files. Default: `..\..\Python_Workflow\outputs`.
- `-TargetDir` : relative path (from script) to copy files into. Default: `./outputs` (under the scripts folder).
- `-SinceMinutes` : look-back window in minutes (default 1440).
- `-IncludeExtensions` : file patterns to include (default `*.pdf, *.png`).
- `-ZipName` : optional zip filename to create inside the `TargetDir`.
- `-Force` : overwrite existing files and zip if present.

Notes
-----
- The script resolves paths relative to its location in `Python_Workflow/scripts` so it works whether you run it from the repo root or from inside the scripts folder.
- Use `-Force` when re-running to overwrite previous copies or zip.

Note: When `-AutoZip` is used with the main pipeline wrapper, updated PDF/PNG outputs are automatically collected and zipped.
