from pathlib import Path
from qtpy import uic
import napari
from qtpy.QtWidgets import QWidget, QFormLayout, QComboBox, QLabel
from napari_tracking_analysis.base import AppState


class NLayerWidget(QWidget):
    def __init__(self, app_state: AppState = None, parent: QWidget = None):
        super().__init__(parent)
        # self.viewer = napari_viewer
        self.state = app_state
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'base_widget.ui')
        self.load_ui(UI_FILE)

        self.nLayersLayout = QFormLayout()
        self.layersWidget.setLayout(self.nLayersLayout)
        self.msg_label = QLabel("Open Image and Label to get started")
        self.nLayersLayout.addRow(self.msg_label)

        self.layers_combo_container = {}
        self.layer_filter = {"Image": napari.layers.Image,
                             "Label": napari.layers.Labels}

        self.layers_hooks = []
        if self.state:
            self.state.nLayerInserted.connect(
                self.viewer_layer_updated)
            self.state.nLayerRemoved.connect(
                self.viewer_layer_updated)

    def load_ui(self, path):
        uic.loadUi(path, self)

    def viewer_layer_updated(self, event):
        for name, dtype in self.layer_filter.items():
            if isinstance(event.value, dtype):
                self.update_combo(name, dtype)
        for f in self.layers_hooks:
            f(event)

    def update_combo(self, name, dtype, is_internal=False):
        combo_box = self.layers_combo_container.get(name, QComboBox())
        combo_box.clear()
        for i, l in enumerate(self.state.getLayers()):
            if isinstance(l, dtype):
                combo_box.addItem(l.name, i)

        if combo_box.count() == 0:  # All the layer of dtype has been removed
            self.nLayersLayout.removeRow(combo_box)
            del combo_box
            del self.layers_combo_container[name]
            return

        if not (name in self.layers_combo_container):
            self.nLayersLayout.addRow(name, combo_box)
            self.layers_combo_container[name] = combo_box

        if self.nLayersLayout.rowCount():
            self.msg_label.setVisible(False)
        else:
            self.msg_label.setVisible(True)

    def get_layer(self, name):
        combo = self.layers_combo_container.get(name, None)
        if combo is None:
            return None
        return self.state.getLayer(combo.currentText())

    def get_layer_name(self, name):
        combo = self.layers_combo_container.get(name, None)
        if combo is None:
            return None
        return combo.currentText()
