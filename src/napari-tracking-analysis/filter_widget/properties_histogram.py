from napari_tracking_analysis.base.plots import Histogram
from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import QTimer
import pandas as pd


class PropertiesHistogram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.is_dirty = True
        self.row_count = 0
        self.setLayout(QVBoxLayout())
        self.plot = Histogram()
        self.layout().addWidget(self.plot)
        self.track_id_column_name = 'track_id'
        self.include_properties = []
        self.properties = {}

    def draw(self):
        self.plot.clear()
        _df = self.dataframe
        data = {}
        for _property, val in self.properties.items():
            if (len(self.include_properties)) and (_property not in self.include_properties):
                continue
            _df = _df[(_df[_property] >= val['min']) & (_df[_property] <= val['max'])]

        for _property, val in self.properties.items():
            if (len(self.include_properties)) and (_property not in self.include_properties):
                continue
            data[_property] = _df[_property].to_numpy()

        self.plot.setData(data=data, title="Filtered View")
        self.plot.draw()

    def set_data_source(self, source: pd.DataFrame):
        self.dataframe = source
        self.nrows = self.dataframe.shape[0]
        self.ncols = self.dataframe.shape[1]
        self.update_prperties()
        self.draw()

    def property_filter_updated(self, property_name, vrange):
        print(f"plots property_filter_updated {property_name}, {vrange}")
        self.properties[property_name] = {'min': vrange[0], 'max': vrange[1]}
        QTimer.singleShot(10, self.draw)

    def update_prperties(self):
        for property in self.dataframe.columns:
            property = str(property).strip()
            if property == self.track_id_column_name.strip():
                continue
            _min = self.dataframe[property].to_numpy().min()
            _max = self.dataframe[property].to_numpy().max()
            self.properties[property] = {'min': float(_min), 'max': float(_max)}
