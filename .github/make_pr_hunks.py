import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/assemble_facility.py",
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/write_labels_to_dxf.py",
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/append_legend_to_pdf.py",
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/generate_legend_pdf.py",
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/equipment_bay_mapper.py",
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/replace_labels_with_blocks.py",
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/compute_model_bounds_and_sizes.py",
    "Combination_Automotive_Diesel_Facility_Project/Python_Workflow/scripts/print_step_components.py",
]


def git_fetch():
    # capture output for debugging
    res = subprocess.run(
        ["git", "fetch", "origin", "main"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    dbg = REPO_ROOT / ".github" / "make_pr_hunks_debug.log"
    with dbg.open("a", encoding="utf-8") as fh:
        fh.write("\n--- git fetch output ---\n")
        fh.write(res.stdout or "")
        fh.write("\n--- git fetch stderr ---\n")
        fh.write(res.stderr or "")


def get_diff():
    cmd = ["git", "diff", "origin/main...HEAD", "--unified=0", "--"] + FILES
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    dbg = REPO_ROOT / ".github" / "make_pr_hunks_debug.log"
    with dbg.open("a", encoding="utf-8") as fh:
        fh.write("\n--- git diff cmd: " + " ".join(cmd) + " ---\n")
        fh.write(res.stdout or "")
        fh.write("\n--- git diff stderr ---\n")
        fh.write(res.stderr or "")
    return res.stdout


def parse_hunks(diff_text: str):
    hunks = {p: [] for p in FILES}
    current_file = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            current_file = path
            continue
        if not current_file:
            continue
        m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            start = int(m.group(1))
            cnt = int(m.group(2)) if m.group(2) else 1
            end = start + cnt - 1
            # normalize path to repository-relative
            rel = current_file
            if rel in hunks:
                hunks[rel].append((start, end))
    # fallback: if a file has no hunks, link entire file
    for p in FILES:
        if not hunks[p]:
            fp = REPO_ROOT / p
            if fp.exists():
                lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
                if lines:
                    hunks[p].append((1, len(lines)))
                else:
                    hunks[p].append((1, 1))
            else:
                hunks[p].append((1, 1))
    return hunks


def build_pr_body(hunks):
    template = (REPO_ROOT / ".github" / "pr_body_clean.md").read_text(encoding="utf-8")
    marker = "### Reviewer highlights"
    if marker not in template:
        return template
    before, after = template.split(marker, 1)
    # after may contain existing bullets; replace until next '---' or end
    parts = after.split("---", 1)
    rest = parts[1] if len(parts) > 1 else ""
    new_highlights = [
        "### Reviewer highlights",
        "\nDirect links to the most meaningful changes:\n",
    ]
    for p in FILES:
        display = Path(p).name
        for s, e in hunks[p]:
            new_highlights.append(f"- [{display}]({p}#L{s}-L{e})")
    new_body = before + "\n".join(new_highlights) + "\n\n---\n" + rest
    return new_body


def main():
    # run fetch and diff, writing debug info
    git_fetch()
    diff = get_diff()
    hunks = parse_hunks(diff)
    body = build_pr_body(hunks)
    out = REPO_ROOT / ".github" / "pr_body_with_hunks.md"
    out.write_text(body, encoding="utf-8")
    print(f"Wrote {out}")
    # also append a short summary to debug log
    dbg = REPO_ROOT / ".github" / "make_pr_hunks_debug.log"
    with dbg.open("a", encoding="utf-8") as fh:
        fh.write(f"\nWROTE: {out}\n")


if __name__ == "__main__":
    main()
