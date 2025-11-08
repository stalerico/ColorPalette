import sys
from PyQt5.QtWidgets import QDialog, QApplication
from colorpicker import Ui_colorPicker


class AppWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_colorPicker()
        self.ui.setupUi(self)
        self.show()


app = QApplication(sys.argv)
w = AppWindow()
w.show()
sys.exit(app.exec_())

