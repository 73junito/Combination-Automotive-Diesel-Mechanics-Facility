import zipfile, os

zip_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "portfolio_submission.zip")
zip_path = os.path.normpath(zip_path)
if not os.path.exists(zip_path):
    print("ZIP not found:", zip_path)
    raise SystemExit(1)
with zipfile.ZipFile(zip_path, "r") as z:
    infos = z.infolist()
    total = os.path.getsize(zip_path)
    print(f"ZIP: {zip_path}")
    print(f"Archive size (bytes): {total}")
    print("Contents:")
    for i in infos:
        print(f" - {i.filename}  ({i.file_size} bytes)")
