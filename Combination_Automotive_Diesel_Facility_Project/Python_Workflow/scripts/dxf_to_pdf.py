import os
import sys
import traceback

try:
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib.pyplot as plt
except ImportError as e:
    print("Required libraries (ezdxf, matplotlib) not available in current environment: {}".format(e))
    raise


def render_doc_to_figure(doc, figsize=(11, 8.5)):
    msp = doc.modelspace()
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, msp).draw(out)
    ax.set_axis_off()
    return fig


def main(in_path: str, out_pdf: str, out_png: str):
    print(f"Loading DXF: {in_path}")
    doc = ezdxf.readfile(in_path)
    fig = render_doc_to_figure(doc)
    print(f"Saving PDF: {out_pdf}")
    fig.savefig(out_pdf, dpi=300, bbox_inches="tight", pad_inches=0)
    print(f"Saving PNG fallback: {out_png}")
    fig.savefig(out_png, dpi=300, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


if __name__ == "__main__":
    try:
        base = os.path.join(
            "Combination_Automotive_Diesel_Facility_Project",
            "Python_Workflow",
            "outputs",
        )
        default_input = os.path.join(base, "facility_layout_engineering.dxf")
        in_path = sys.argv[1] if len(sys.argv) > 1 else default_input
        if not os.path.exists(in_path):
            print(f"Input DXF not found: {in_path}")
            sys.exit(2)
        out_pdf = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(in_path)[0] + ".pdf"
        out_png = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(in_path)[0] + ".png"
        main(in_path, out_pdf, out_png)
        print("Export complete.")
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
