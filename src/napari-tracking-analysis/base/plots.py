import numpy as np
from typing import Optional, Any, List
from matplotlib.backends.backend_qtagg import (
    FigureCanvas,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from qtpy.QtWidgets import QVBoxLayout, QWidget, QAbstractItemView
from qtpy.QtCore import QModelIndex, Qt, QRect, QPoint, Signal
from qtpy.QtGui import QRegion, QIntValidator
from qtpy import uic
from pathlib import Path
from napari_tracking_analysis import utils

import warnings
# from warnings import RuntimeWarning
warnings.filterwarnings('ignore', category=RuntimeWarning)

# colors = dict(
#     COLOR_1="#DC267F",
#     COLOR_2="#648FFF",
#     COLOR_3="#785EF0",
#     COLOR_4="#FE6100",
#     COLOR_5="#FFB000")

colors = list([
    "#DC267F",
    "#648FFF",
    "#785EF0",
    "#FE6100",
    "#FFB000"])


class HistogramBinSize(QWidget):
    editingFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'histogram_bin_control_widget.ui')
        self.load_ui(UI_FILE)
        self.leControl.editingFinished.connect(self.editingFinished)
        self.leControl.setValidator(QIntValidator())

    def setTitle(self, text):
        self.lbTitle.setText(text)

    def title(self):
        return self.lbTitle.text()

    def setValue(self, val):
        self.leControl.setText(str(val))

    def value(self):
        return int(self.leControl.text()) if self.leControl.text() else 0

    def load_ui(self, path):
        uic.loadUi(path, self)


class BaseMPLWidget(QWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        self.canvas = FigureCanvas()
        self.toolbar = NavigationToolbar2QT(
            self.canvas, parent=self, coordinates=False
        )

        self.canvas.figure.set_layout_engine("constrained")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

    @property
    def figure(self) -> Figure:
        """Matplotlib figure."""
        return self.canvas.figure

    def add_single_axes(self) -> None:
        """
        Add a single Axes to the figure.

        The Axes is saved on the ``.axes`` attribute for later access.
        """
        self.axes = self.figure.subplots()

    def add_multiple_axes(self, count) -> None:
        """
        Add multiple Axes to the figure using count.
        The Axes is saved on the ``.axes`` attribute for later access.
        """
        self.count = count
        self.col = 2
        self.row = int(np.ceil(self.count/self.col))
        # print("add_multiple_axes", self.row, self.col)
        self.grid_space = self.figure.add_gridspec(ncols=self.col, nrows=self.row)
        # print("add_multiple_axes", self.grid_space)

    def clear(self) -> None:
        """
        Clear any previously drawn figures.

        This is a no-op, and is intended for derived classes to override.
        """
        self.axes.clear()


class IntensityStepPlots(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        # self._setup_callbacks()
        self.add_single_axes()

    def draw(self, intensity, fitx, title) -> None:
        self.clear()

        if len(intensity):
            _intensity = np.array(intensity)
            self.axes.plot(_intensity.ravel(), label="Intensity", color=colors[0])

        if len(fitx):
            _fitx = np.array(fitx)
            self.axes.plot(_fitx.ravel(), label="Steps", color=colors[1])

        self.axes.legend(loc='upper right')
        self.axes.set_title(label=title)

        # needed
        self.canvas.draw()


class Histogram(BaseMPLWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)

        # self._setup_callbacks()
        self.add_single_axes()
        self.data = []
        self.label = None
        self.color = colors[0]
        self.control = HistogramBinSize()
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.control)
        self.control.setTitle("Bin Size")
        self.control.setValue(5)
        if hasattr(self.toolbar, "coordinates"):
            self.toolbar.coordinates = False

    def _get_dict_length(self, data):
        _size = []
        if isinstance(data, dict):
            for k, v in data.items():
                _size.append(len(v))
            return np.max(_size)

    def setData(self, data, title):
        if isinstance(data, dict):
            self.data = data
        else:
            self.data = np.array(data).ravel()
            self.control.setValue(5 if len(data) > 5 else 2)

        self.label = title
        self.control.editingFinished.connect(self.draw)

    def setColor(self, color):
        self.color = color

    def draw(self) -> None:
        self.clear()

        if isinstance(self.data, dict):
            n_colors = len(colors)
            for i, (p, v) in enumerate(self.data.items()):
                print("Checking the isnan fail", type(v), len(v))
                color = colors[int(i % n_colors)]
                value = np.array(v).ravel()
                # hist, _bin_e = np.histogram(value, bins=int(len(value)*0.1))
                # self.axes.plot(hist, color=color, label=p, alpha=0.5)
                hist, bins, binsize = utils.histogram(value, self.control.value())
                # self.control.setValue(binsize)
                self.axes.hist(value, bins=bins, edgecolor='black', linewidth=0.5, color=color, label=p, alpha=0.5)
                self.axes.legend(loc='upper right')
        else:
            if len(self.data):
                hist, bins, binsize = utils.histogram(self.data, self.control.value())
                # self.control.setValue(binsize)
                self.axes.hist(self.data, bins=bins, edgecolor='black',
                               linewidth=0.5, color=self.color, label=self.label)
                self.axes.set_title(label=self.label)
                self.axes.legend(loc='upper right')

        # needed
        self.canvas.draw()

