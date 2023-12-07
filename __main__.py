# launch_napari.py
from napari import Viewer, run
# import tifffile
# from qtpy.uic import compileUi
# from pathlib import Path
# from pprint import pprint


# def build():
#     UI_DIR = Path(__file__).resolve().parent.joinpath('src', 'napari_tracking_analysis', 'ui')
#     UI_FILES = UI_DIR.glob("*.ui")
#     for uifile in UI_FILES:
#         pyfile_name = f"ui_{uifile.stem}.py"
#         pyfile = open(uifile.with_name(pyfile_name), 'wt', encoding='utf8')
#         compileUi(uifile, pyfile)  # from_imports=True, import_from='qtpy'
#         pprint(pyfile)


def launch():
    viewer = Viewer()
    dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
        "napari-tracking-analysis", "Step Detection"
    )
    # viewer.add_image(tifffile.imread("image.tif"))
    # viewer.add_labels(tifffile.imread("mask.tif"))

    run()


if __name__ == "__main__":
    launch()
