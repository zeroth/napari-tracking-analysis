from napari_tracking_analysis.base import NLayerWidget, AppState
from napari_tracking_analysis.filter_widget import FilterWidget
from qtpy.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from qtpy.QtCore import Qt
from qtpy.QtGui import QIntValidator
from qtpy import uic
from pathlib import Path
from napari_tracking_analysis import utils
import pandas as pd
from napari.utils import progress
import numpy as np


class ResultWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'step_analysis_result_widget.ui')
        self.load_ui(UI_FILE)
        self.btnExport.setIcon(utils.get_icon('file-export'))
        self.data = data
        self.setup_ui()

    def load_ui(self, path):
        uic.loadUi(path, self)

    def setup_ui(self):
        step_meta: pd.DataFrame = self.data['steps_meta_df']
        step_info: pd.DataFrame = self.data['steps_df']
        data_dict = {}
        data_dict['step_count'] = step_meta['step_count'].to_numpy()
        data_dict['negetive_vs_positive'] = np.hstack([step_meta['negetive_steps'].to_numpy(),
                                                       step_meta['positive_steps'].to_numpy()])
        data_dict['single_step_height'] = np.abs(
            (step_meta[step_meta['step_count'] == 1]['step_height']).to_numpy())
        data_dict['max_intensity'] = step_meta['max_intensity'].to_numpy()
        data_dict['step_height'] = np.abs((self.data['steps_df']['step_height']).to_numpy())
        data_dict['track_length'] = step_meta['length'].to_numpy()

        # step length
        max_step_count = np.max(data_dict['step_count'])

        for i in range(1, max_step_count+1):
            track_ids = (step_meta[step_meta['step_count'] == i]['track_id']).to_list()
            tracks_group = step_info[step_info['track_id'].isin(track_ids)].groupby('track_id')
            for j in range(0, i):
                print(f"step_count_{i}_step_{j+1}_dwell_before")
                jth = tracks_group['dwell_before'].nth(j).to_numpy(dtype=np.float64)
                print(f"jth.dtype : {jth.dtype}, {jth.size}")
                data_dict[f'step_count_{i}_step_{j+1}_dwell_before'] = jth
                # data_dict[f'step_count_{i}_step_{j}_dwell_after'] = np.abs(
                #     tracks_group['dwell_after'].nth(j-1).to_numpy())
                # data_dict[f'step_count_{i}_step_{j}_step_height'] = np.abs(
                #     tracks_group['step_height'].nth(j-1).to_numpy())
                # data_dict[f'step_count_{i}_step_{j}_step_length'] = np.abs(
                #     tracks_group['dwell_before'].nth(j-1).to_numpy())

            # data_dict[f'step_count_{i}_step_length'] = np.abs((
            #     step_info[step_info['track_id'].isin(track_ids)]['dwell_before']).to_numpy())

        self.histogram.setData(data=data_dict)
        self.btnExport.clicked.connect(self.export)

    def export(self):
        file_path = QFileDialog.getSaveFileName(self,
                                                caption="Export step analysis results in csv",
                                                directory=str(Path.home()),
                                                filter="*.csv")
        if not len(file_path[0]):
            return

        print(file_path)
        df = self.data['steps_df']
        df.to_csv(file_path[0])
        # # temp
        # meta_path = file_path[0].replace('.csv', '_meta.csv')
        # self.data['steps_meta_df'].to_csv(meta_path)


class _step_analysis_ui(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'step_analysis_widget.ui')
        self.load_ui(UI_FILE)
        self.leWindowSize.setValidator(QIntValidator())

    def load_ui(self, path):
        uic.loadUi(path, self)


class StepAnalysisWidget(NLayerWidget):
    def __init__(self, app_state: AppState = None, parent=None):
        super().__init__(app_state=app_state, parent=parent)
        self.ui = _step_analysis_ui(self)
        self.layout().addWidget(self.ui)
        self.gbNapariLayers.setVisible(False)
        self.ui.resultWidget.clear()

        self.property_widget = FilterWidget(self.state, parent=self)

        def _call_setup_ui(key, val):
            if key == "tracking_model":
                print("_call_setup_ui")
                self.property_widget.setup_ui()
        self.state.objectAdded.connect(_call_setup_ui)
        self.state.objectUpdated.connect(_call_setup_ui)

        self.ui.filterTable.setLayout(QVBoxLayout())
        self.ui.filterTable.layout().addWidget(self.property_widget)

        self.property_widget.gbFilterControls.setVisible(False)
        self.property_widget.gbHistogram.setVisible(False)
        self.property_widget.tabWidget.setTabVisible(1, False)
        self.property_widget.proxySelectionChanged.connect(self.track_selected)
        # self.ui.resultWidget.setDocumentMode(True)

        def _reDrawPlot():
            if hasattr(self, "current_track"):
                self.track_selected(self.current_track)

        self.ui.sbThreshold.valueChanged.connect(_reDrawPlot)
        self.ui.leWindowSize.editingFinished.connect(_reDrawPlot)
        self.ui.fitAll.clicked.connect(self.apply_all)

        def _render_results(key, val):
            if key == 'stepanalysis_result':
                self.render_plots()
        self.state.dataAdded.connect(_render_results)
        self.state.dataUpdated.connect(_render_results)

        def _toggle_oriantation():
            if (self.ui.splitter.orientation() == Qt.Orientation.Horizontal):
                self.ui.splitter.setOrientation(Qt.Orientation.Vertical)
            else:
                self.ui.splitter.setOrientation(Qt.Orientation.Horizontal)

        self.state.toggleOriantation.connect(_toggle_oriantation)

    def track_selected(self, track_id):
        print(f"track_selected {track_id}")
        self.current_track = track_id
        tracks_df = self.state.data("tracking")
        all_tracks = tracks_df['tracks_df']
        if 'intensity_mean' in all_tracks.columns:
            track = all_tracks[all_tracks['track_id'] == track_id]
            intensity = track['intensity_mean'].to_numpy()
            if len(intensity) < 5:
                self.ui.intensityPlot.draw(intensity, [], f"Track {track_id}")
                return
            _, fitx, _ = utils.FindSteps(data=intensity,
                                         window=int(self.ui.leWindowSize.text()),
                                         threshold=self.ui.sbThreshold.value())
            self.ui.intensityPlot.draw(intensity, fitx, f"Track {track_id}")

    def apply_all(self):
        print("Step fitting started")
        models = self.state.object("tracking_model")
        proxy_model = models['proxy']

        dfs = self.state.data("tracking")
        all_tracks = dfs['tracks_df']
        step_meta = []
        steps_info = pd.DataFrame()
        rows = proxy_model.rowCount()
        window = int(self.ui.leWindowSize.text())
        threshold = self.ui.sbThreshold.value()
        print(f"Total number of rows {rows}")

        for row in progress(range(rows), desc="Analysing steps.."):
            index = proxy_model.index(row, 0, self.property_widget.filterView.rootIndex())
            track_id = int(proxy_model.data(index))
            track = all_tracks[all_tracks['track_id'] == track_id]
            intensity = track['intensity_mean'].to_numpy()
            steptable, fitx, _ = utils.FindSteps(data=intensity,
                                                 window=window,
                                                 threshold=threshold)

            # all_tracks.loc[all_tracks['track_id'] == track_id, 'fit'] = fitx
            # Detail step table
            steps_df = pd.DataFrame(steptable,
                                    columns=["step_index", "level_before", "level_after",
                                             "step_height", "dwell_before", "dwell_after", "measured_error"])
            steps_df['track_id'] = track_id
            steps_info = pd.concat([steps_info, steps_df], ignore_index=True)

            # single row description of step table
            meta_row = []
            # track id
            meta_row.append(track_id)
            # number of steps
            meta_row.append(len(steptable))
            # Negetive steps (steps going down)
            meta_row.append(-len(steps_df[steps_df['step_height'] < 0]))
            # Positive steps (steps going up or straight line)
            meta_row.append(len(steps_df[steps_df['step_height'] >= 0]))
            # Average step height
            meta_row.append(steps_df['step_height'].mean())
            # Max Intensity
            meta_row.append(np.max(intensity.ravel()))
            # Track length
            meta_row.append(len(intensity.ravel()))

            step_meta.append(meta_row)

        print("\n\rStep fitting done")

        step_meta_df = pd.DataFrame(data=step_meta,
                                    columns=['track_id', 'step_count', 'negetive_steps',
                                             'positive_steps', 'step_height', 'max_intensity', 'length'])
        _result = {'steps_df': steps_info,
                   'steps_meta_df': step_meta_df,
                   'track_filter': proxy_model.properties,
                   'parameters': {'window': window, 'threshold': threshold}}
        result_title = f"{window}_{threshold}_1"
        result = {}
        if self.state.hasData('stepanalysis_result'):
            sr = self.state.data('stepanalysis_result')
            print("total current results ", len(sr.keys()))
            print(f"\t {sr.keys()}")
            result_title = f"{window}_{threshold:.3f}_{len(sr.keys())+1}"
            result = sr

        result[result_title] = _result
        self.state.setData("stepanalysis_result", result)

        # steps_info.to_csv('step_info.csv')
        # step_meta_df.to_csv('step_meta.csv')

    def render_plots(self):
        # ['track_id', 'step_count', 'negetive_steps','positive_steps', 'step_height', 'max_intensity']
        result_obj = self.state.data("stepanalysis_result")

        # TODO check if the tab exist
        results = list(result_obj.keys())
        current_tabs = []
        for i in range(self.ui.resultWidget.count()):
            tab_title = self.ui.resultWidget.tabText(i)
            current_tabs.append(tab_title)

        new_tabs = list(set(results) - set(current_tabs))
        for new_tab in new_tabs:
            stepanalysis_data = result_obj[new_tab]
            resutl_widget = ResultWidget(data=stepanalysis_data)
            self.ui.resultWidget.addTab(resutl_widget, f"Results {new_tab}")


def _qt_main():
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = QWidget()
    # widget.setIcon(utils.get_icon('file-export'))
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    _qt_main()
