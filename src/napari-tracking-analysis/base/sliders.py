from qtpy import uic
from pathlib import Path
from qtpy.QtWidgets import QWidget, QHBoxLayout
from qtpy.QtCore import Signal
from qtpy.QtGui import QIntValidator


class _h_slider_ui(QWidget):
    valueChanged = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        UI_FILE = Path(__file__).resolve().parent.parent.joinpath(
            'ui', 'h_range_slider.ui')
        self.load_ui(UI_FILE)
        self.leMin.setStyleSheet("background:transparent; border: 0;")
        self.leMax.setStyleSheet("background:transparent; border: 0;")

        self.leMin.setValidator(QIntValidator())
        self.leMax.setValidator(QIntValidator())
        self.hSlider.valueChanged.connect(self._update_labels)
        self.hSlider.valueChanged.connect(self.valueChanged)
        self.leMin.editingFinished.connect(self._update_min)
        self.leMax.editingFinished.connect(self._update_max)

    def load_ui(self, path):
        uic.loadUi(path, self)

    def setRange(self, vrange):
        vmin, vmax = vrange
        if vmin == vmax:
            vmax = vmin+1
        self.leMin.setText(str(vmin))
        self.leMax.setText(str(vmax))
        self.hSlider.setRange(vmin, vmax)

    def range(self):
        return (self.hSlider.minimum(), self.hSlider.maximum())

    def setValue(self, vrange):
        if vrange[0] == vrange[1]:
            vrange = (vrange[0], vrange[0]+1)
        self.hSlider.setValue(vrange)

    def value(self):
        return self.hSlider.value()

    def _update_labels(self, vrange):
        vmin, vmax = vrange
        self.leMin.setText(str(vmin))
        self.leMax.setText(str(vmax))

    def _update_min(self):
        text = self.leMin.text()
        vmin, vmax = self.hSlider.value()
        rmin, _ = self.hSlider.minimum(), self.hSlider.maximum()
        val = int(text) if text else rmin

        if val >= vmax:
            val = vmax - 1
        if val < rmin:
            val = rmin
        self.setValue((val, vmax))

    def _update_max(self):
        text = self.leMax.text()
        vmin, vmax = self.hSlider.value()
        _, rmax = self.hSlider.minimum(), self.hSlider.maximum()
        val = int(text) if text else rmax

        if val <= vmin:
            val = vmin + 1
        if val > rmax:
            val = rmax
        self.setValue((vmin, val))

    def setTracking(self, state: bool):
        self.hSlider.setTracking(state)

    def tracking(self):
        return self.hSlider.tracking()


class HRangeSlider(QWidget):
    """
    Horizontal slider
    """
    valueChanged = Signal(tuple)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout()
        self.ui = _h_slider_ui(self)
        layout.addWidget(self.ui)
        self.setLayout(layout)
        self.setTracking(False)
        self.ui.valueChanged.connect(self.valueChanged)

    def setRange(self, vrange):
        self.ui.setRange(vrange)

    def setValue(self, vrange):
        self.ui.setValue(vrange)

    def value(self):
        return self.ui.value()

    def range(self):
        return self.ui.range()

    def setTracking(self, state: bool):
        self.ui.setTracking(state)

    def setTitle(self, title):
        self.ui.group.setTitle(f"{title}")


class HFilterSlider(HRangeSlider):
    valueChangedTitled = Signal(str, tuple)

    def __init__(self, title: str = 'untitled', parent: QWidget = None) -> None:
        super().__init__(parent)
        self.title = title
        self.valueChanged.connect(self.valueUpdated)

    def setTitle(self, title):
        self.title = title
        return super().setTitle(f"Filter - {title}")

    def valueUpdated(self, vrange):
        self.valueChangedTitled.emit(self.title, vrange)


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = HRangeSlider()
    widget.setRange((0, 100))
    widget.setValue((0, 100))
    widget.show()
    sys.exit(app.exec())
