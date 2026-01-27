import os
import zipfile


def recreate_zip(outputs_dir: str, zip_name: str = "portfolio_submission.zip"):
    zip_path = os.path.join(outputs_dir, zip_name)
    # Overwrite existing zip
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(outputs_dir):
            for fname in files:
                if fname == zip_name:
                    continue
                # add file with relative path inside zip
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, outputs_dir)
                zf.write(abs_path, arcname=rel_path)
    return zip_path


if __name__ == "__main__":
    base = os.path.join(
        "Combination_Automotive_Diesel_Facility_Project",
        "Python_Workflow",
        "outputs",
    )
    if not os.path.exists(base):
        print("Outputs folder not found:", base)
        raise SystemExit(2)
    out = recreate_zip(base)
    print("Recreated ZIP:", out)
