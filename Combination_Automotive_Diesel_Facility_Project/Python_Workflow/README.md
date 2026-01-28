Python Workflow for Combination Automotive/Diesel Facility

Setup

1. Create and activate the virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

1. VS Code will pick up the interpreter at `.venv/Scripts/python.exe`.
2. The CadQuery source is included in the workspace at `CadQuery 2.6.1 source code` and is added to `python.analysis.extraPaths` in `.vscode/settings.json` for completion.

Notes

- If you prefer to install `cadquery` from PyPI, uncomment or add `cadquery==2.6.1` to `requirements.txt`.
- To run scripts, use the workspace interpreter explicitly if needed:

```powershell
.\.venv\Scripts\python.exe scripts\your_script.py
```
