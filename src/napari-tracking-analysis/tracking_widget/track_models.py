from qtpy.QtCore import (Signal, QAbstractTableModel, Qt, QModelIndex, QVariant, QObject, QSortFilterProxyModel)
import pandas as pd


class TrackMetaModel(QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame = pd.DataFrame(),
                 track_id_column_name: str = 'track_id', parent: QObject = None) -> None:
        super().__init__(parent)
        self.beginResetModel()
        self.dataframe = dataframe
        self.endResetModel()
        self.track_id_column_name = track_id_column_name

    def setDataframe(self, dataframe: pd.DataFrame):
        self.beginResetModel()
        self.dataframe = dataframe
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return self.dataframe.shape[0]

    def columnCount(self, parent=QModelIndex()) -> int:
        return self.dataframe.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole) -> QVariant:
        if (not index.isValid()):
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.dataframe.iat[index.row(), index.column()])

        if role == Qt.ItemDataRole.UserRole+1:
            # print("DataFrameModel User Role: ", self.dataframe.iat[index.row(), 0])
            return float(self.dataframe.iat[index.row(), index.column()])

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> QVariant:
        if role == Qt.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.dataframe.columns[section]
            return str(section)


class TrackMetaModelProxy(QSortFilterProxyModel):
    filterUpdated = Signal(str, tuple)

    def __init__(self, parent: QObject = None):
        super(TrackMetaModelProxy, self).__init__(parent)
        self.properties = {}
        self.sourceModelChanged.connect(self.update_prperties)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if (not hasattr(self, 'properties')) or (not self.properties):
            return True
        conditions = []
        for i, (k, v) in enumerate(self.properties.items()):
            if str(k).strip() == self.track_model.track_id_column_name.strip():
                continue
            # print(i, k, v)
            index = self.sourceModel().index(source_row, i+1, source_parent)
            conditions.append((float(self.sourceModel().data(index)) >= v['min'])
                              and (float(self.sourceModel().data(index)) <= v['max']))

        # AND LOGIC
        if all(conditions):
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        return self.sourceModel().headerData(section, orientation, role)

    def setTrackModel(self, model: TrackMetaModel):
        self.track_model = model
        self.setSourceModel(model)

    def update_prperties(self):
        for property in self.track_model.dataframe.columns:
            property = str(property).strip()
            if property == self.track_model.track_id_column_name.strip():
                continue
            _min = self.track_model.dataframe[property].to_numpy().min()
            _max = self.track_model.dataframe[property].to_numpy().max()
            self.properties[property] = {'min': float(_min), 'max': float(_max)}

    def property_filter_updated(self, property_name, vrange):
        print(f"property_filter_updated {property_name}, {vrange}")
        self.properties[property_name] = {'min': vrange[0], 'max': vrange[1]}
        self.filterUpdated.emit(property_name, vrange)
        self.invalidateFilter()
