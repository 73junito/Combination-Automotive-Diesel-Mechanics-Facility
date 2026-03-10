# Archive policy for Drawings

When a drawing revision is released, follow this archive policy to ensure reproducible deliverables.

1. Create folder: `Drawings/Archive/<ProjectName>/<YYYY-MM-DD>_revNN/`
2. Copy into the folder:
   - Source native file(s) (DWG,CDX, etc.)
   - Exported DXF(s)
   - Flattened PDF(s)
   - `project-metadata.json` snapshot
   - `changelog.txt` describing changes
3. Add a brief release README with approver, date, and release notes.
4. Tag the commit in version control with `drawings/<ProjectName>/revNN` if using Git.

Access:
- Archive folders are read-only for general contributors. Only project leads may add archived releases.
