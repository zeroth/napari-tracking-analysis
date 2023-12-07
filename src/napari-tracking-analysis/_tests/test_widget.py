from qtpy.QtWidgets import QWidget, QTabWidget, QPushButton, QVBoxLayout, QLabel, QTabBar
from qtpy.QtCore import Signal, Qt
from napari_tracking_analysis import utils


class ExportButton(QWidget):
    exportClicked = Signal(str)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.btn = QPushButton(title)
        # self.setMaximumWidth(32)
        # self.setMaximumHeight(32)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.btn)
        self._title = title
        print("ExportButton connecting")
        self.btn.clicked.connect(self.btnClicked)

    def setIcon(self, icon):
        self.btn.setIcon(icon)

    def btnClicked(self):
        print("ExportButton emiting")
        self.exportClicked.emit(self.title())

    def setTitle(self, text):
        self._title = text

    def title(self):
        return self._title


class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabWidget = QTabWidget()
        self.tabWidget.clear()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.tabWidget)

        self.addTabs()

    def addTabs(self):
        for i in range(5):
            index = self.tabWidget.addTab(QLabel(str(i)), f"tab {i}")
            tab_bar = self.tabWidget.tabBar()
            btn_export = ExportButton(str(index))
            # btn_export.setIcon(utils.get_icon('file-export'))
            # btn_export.clicked.connect(lambda: print(f"exporting"))
            btn_export.exportClicked.connect(lambda x: print(f"exporting {x}"))
            tab_bar.setTabButton(index, QTabBar.LeftSide, btn_export)


def _qt_main():
    from qtpy.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    widget = MyWidget()
    # widget.setIcon(utils.get_icon('file-export'))
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    _qt_main()
