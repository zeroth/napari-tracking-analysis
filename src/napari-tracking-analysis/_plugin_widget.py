from qtpy.QtWidgets import QVBoxLayout, QWidget, QTabWidget, QToolButton, QStyle, QHBoxLayout, QFileDialog
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap, QIcon
from napari_tracking_analysis.segmentation_widget import SegmentationWidget
from napari_tracking_analysis.tracking_widget import TrackingWidget
from napari_tracking_analysis.filter_widget import PropertyFilter
from napari_tracking_analysis.base import AppState
from napari_tracking_analysis.step_analysis_widget import StepAnalysisWidget
from napari_tracking_analysis import utils
import napari
import os
from pathlib import Path


class PluginWidget(QWidget):

    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.app_state = AppState(napari_viewer=napari_viewer)
        self.setLayout(QVBoxLayout())
        self.tabs = QTabWidget()
        self.layout().addWidget(self.tabs)

        self.segmentation_widget = SegmentationWidget(app_state=self.app_state)
        self.tabs.addTab(self.segmentation_widget, "Segmentation")

        self.tracking_widget = TrackingWidget(app_state=self.app_state)
        self.property_filter_widget = PropertyFilter(app_state=self.app_state)
        self.stepanalysis_widget = StepAnalysisWidget(app_state=self.app_state)
        self.tabs.addTab(self.tracking_widget, "Tracking")
        self.tabs.addTab(self.property_filter_widget, "Properties Filter")
        self.tabs.addTab(self.stepanalysis_widget, "Step Analysis")

        # self.tabs.setTabVisible(1, False)
        # self.tabs.setTabVisible(2, False)
        # self.tabs.setTabVisible(3, False)

        # def _track_layer_added(event):
        #     if isinstance(event.value, napari.layers.Tracks):
        #         if hasattr(event.value, 'metadata') and ('all_meta' in event.value.metadata):
        #             self._track_added()

        # self.app_state.nLayerInserted.connect(_track_layer_added)
        # def _track_data_added(key, val):
        #     if key == "tracking":
        #         self._track_added()
        # self.app_state.dataAdded.connect(_track_data_added)

        # setup the top left Action Menu
        self.btn_save = QToolButton()
        self.btn_save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.btn_save.setMinimumWidth(20)
        self.btn_save.setMinimumHeight(20)

        def _save_clicked():
            file_path = QFileDialog.getSaveFileName(self,
                                                    caption="Save Track State Project",
                                                    directory=str(Path.home()),
                                                    filter="*.tracks")
            if len(file_path[0]):
                print(file_path)
                self.app_state.save(file_path[0])
        self.btn_save.clicked.connect(_save_clicked)

        self.btn_open = QToolButton()
        self.btn_open.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.btn_open.setMinimumWidth(20)
        self.btn_open.setMinimumHeight(20)

        def _open_clicked():
            file_path = QFileDialog.getOpenFileName(self,
                                                    caption="Open Track State Project",
                                                    directory=str(Path.home()),
                                                    filter="*.tracks")
            if len(file_path[0]):
                print(file_path)
                self.app_state.open(file_path[0])
        self.btn_open.clicked.connect(_open_clicked)
        # self.btn_open.clicked.connect(self.app_state.open)

        # left corner
        corner_widget = QWidget()
        corner_widget.setLayout(QHBoxLayout())
        corner_widget.layout().setContentsMargins(0, 0, 0, 0)
        corner_widget.layout().setSpacing(1)
        corner_widget.layout().addWidget(self.btn_save)
        corner_widget.layout().addWidget(self.btn_open)
        corner_widget.setMinimumWidth(41)
        corner_widget.setMinimumHeight(21)

        # right corner
        self.btn_oriantation = QToolButton()
        self.btn_oriantation.setIcon(utils.get_icon('rotate'))
        self.btn_oriantation.clicked.connect(self.app_state.toggleOriantation)

        self.tabs.setCornerWidget(corner_widget, Qt.Corner.TopLeftCorner)
        self.tabs.setCornerWidget(self.btn_oriantation, Qt.Corner.TopRightCorner)

        # Test
        self.app_state.toggleOriantation.connect(lambda: print("Toggled clicked"))

    def _track_added(self):
        # self.tabs.setTabVisible(1, True)
        self.tabs.setTabVisible(2, True)
        self.tabs.setTabVisible(3, True)


def _napari_main():
    import napari
    viewer = napari.Viewer()
    win = PluginWidget(viewer)
    viewer.window.add_dock_widget(win, name="Plugin", area="right")
    napari.run()


if __name__ == "__main__":
    _napari_main()
