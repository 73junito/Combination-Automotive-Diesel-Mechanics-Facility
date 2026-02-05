#!/usr/bin/env python
"""Load workbench STL and render a PNG preview using trimesh + matplotlib fallback.

Saves to: Combination_Automotive_Diesel_Facility_Project/Python_Workflow/outputs/previews/workbench_preview.png
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
stl_path = (
    ROOT
    / "Combination_Automotive_Diesel_Facility_Project"
    / "Python_Workflow"
    / "outputs"
    / "models"
    / "stl"
    / "workbench.stl"
)
out_dir = (
    ROOT
    / "Combination_Automotive_Diesel_Facility_Project"
    / "Python_Workflow"
    / "outputs"
    / "previews"
)
out_dir.mkdir(parents=True, exist_ok=True)
out_png = out_dir / "workbench_preview.png"


def main():
    try:
        import trimesh
    except Exception:
        print("trimesh not installed")
        sys.exit(2)

    if not stl_path.exists():
        print("STL not found:", stl_path)
        sys.exit(3)

    mesh = trimesh.load_mesh(str(stl_path))
    scene = mesh.scene()

    try:
        # prefer built-in renderer
        img = scene.save_image(resolution=(800, 600), visible=True)
        if img is None:
            raise RuntimeError("Renderer returned no image")
        with open(out_png, "wb") as f:
            f.write(img)
        print("Preview written to", out_png)
        return 0
    except Exception as e:
        print("Trimesh renderer failed:", e)
        # fallback: render simple orthographic projection via matplotlib
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        fig = plt.figure(figsize=(6, 4), dpi=150)
        ax = fig.add_subplot(111, projection="3d")

        faces = mesh.faces
        verts = mesh.vertices
        mesh_collection = Poly3DCollection(verts[faces], linewidths=0.05, alpha=1.0)
        mesh_collection.set_facecolor((0.7, 0.7, 0.9))
        ax.add_collection3d(mesh_collection)

        scale = verts.flatten()
        ax.auto_scale_xyz(scale, scale, scale)
        ax.axis("off")
        plt.tight_layout()
        fig.savefig(out_png, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        print("Fallback preview written to", out_png)
        return 0
    except Exception as e:
        print("Fallback renderer failed:", e)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
