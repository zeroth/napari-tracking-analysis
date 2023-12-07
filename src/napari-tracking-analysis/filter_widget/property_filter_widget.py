from pathlib import Path
from qtpy import uic
import pandas as pd
from napari_tracking_analysis.base import (NLayerWidget, AppState, HFilterSlider)
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Signal, Qt


class FilterWidget(QWidget):
    propertyUpdated = Signal(str, tuple)
    proxySelectionChanged = Signal(int)

    def __init__(self, app_state: AppState = None, include_properties=None, parent: QWidget = None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'filter_widget.ui')
        self.load_ui(UI_FILE)

        self.state = app_state
        self.track_id_column_name = 'track_id'
        self.property_sliders = {}
        if include_properties is None:
            self.include_properties = []
        else:
            self.include_properties = include_properties

        self.setup_ui()

        # def _call_setup_ui(key, val):
        #     if key == "tracking_model":
        #         print("_call_setup_ui")
        #         self.setup_ui()
        # self.state.objectAdded.connect(_call_setup_ui)

    def load_ui(self, path):
        uic.loadUi(path, self)

    def setup_ui(self):
        if not self.state.hasObject("tracking_model"):
            return
        dfs = self.state.data('tracking')

        models = self.state.object("tracking_model")
        self.allView.setModel(models['model'])
        self.filterView.setModel(models['proxy'])

        self.allView.setSelectionModel(models['model_selection'])
        self.filterView.setSelectionModel(models['proxy_selection'])
        models['proxy_selection'].currentChanged.connect(self.current_proxy_selection_changed)

        self.filterPlots.include_properties = self.include_properties

        self.filterPlots.set_data_source(dfs['meta_df'])

        self.propertyUpdated.connect(models['proxy'].property_filter_updated)
        self.propertyUpdated.connect(self.filterPlots.property_filter_updated)

        track_meta = dfs['meta_df']
        self.add_controls(track_meta)

        def _update_property_sliders(name, vrange):
            if name in self.property_sliders:
                slider = self.property_sliders[name]
                if slider.value() == vrange:
                    return
                slider.setValue(vrange)

        # models['proxy'].filterUpdated.connect(_update_property_sliders)

    def current_proxy_selection_changed(self, current, previous):
        print("current_proxy_selection_changed in")
        if (not current.isValid()):
            return
        print("current_proxy_selection_changed valid")
        track_id_index = self.filterView.model().index(current.row(), 0, current.parent())
        track_id = int(self.filterView.model().data(track_id_index, role=Qt.ItemDataRole.DisplayRole))
        print(f"current_proxy_selection_changed emit {track_id}")
        self.proxySelectionChanged.emit(track_id)

    def add_controls(self, track_meta: pd.DataFrame):
        # if len(self.property_sliders):
        #     for k, v in self.property_sliders.items():
        #         del v
        #     del self.property_sliders
        #     self.property_sliders = {}

        if not self.filterControls.layout():
            self.filterControls.setLayout(QVBoxLayout())
            self.filterControls.layout().setContentsMargins(0, 0, 0, 0)
            self.filterControls.layout().setSpacing(2)
        for p in track_meta.columns:
            if p == self.track_id_column_name:
                continue
            if (len(self.include_properties)) and (p not in self.include_properties):
                continue
            if p in self.property_sliders:
                _slider = self.property_sliders[p]
            else:
                _slider = HFilterSlider()
                _slider.setTitle(p)
                _slider.valueChangedTitled.connect(self.propertyUpdated)
                self.property_sliders[p] = _slider
                self.filterControls.layout().addWidget(_slider)

            _p_np = track_meta[p].dropna().to_numpy()
            _vrange = (_p_np.min(), _p_np.max())
            if p == "step_count":
                print(track_meta[p])
                print(track_meta.head(n=5))

            print(p, _vrange)
            _slider.setRange(_vrange)
            _slider.setValue(_vrange)

    def get_current_track_layer(self):
        return self.get_layer("Tracks")

    def get_current_image_data(self):
        return None if self.get_current_track_layer() is None else self.get_current_track_layer().data


class PropertyFilter(NLayerWidget):

    def __init__(self, app_state: AppState = None, parent: QWidget = None, include_properties=None):
        super().__init__(app_state=app_state, parent=parent)
        self.ui = FilterWidget(app_state=self.state, include_properties=include_properties, parent=self)
        self.layout().addWidget(self.ui)
        self.gbNapariLayers.setVisible(False)

        def _call_setup_ui(key, val):
            if key == "tracking_model":
                print("_call_setup_ui")
                self.ui.setup_ui()
        self.state.objectAdded.connect(_call_setup_ui)
        self.state.objectUpdated.connect(_call_setup_ui)
