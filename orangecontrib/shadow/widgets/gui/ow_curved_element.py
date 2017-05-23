import sys
from PyQt5.QtWidgets import QApplication

from . import ow_optical_element


class CurvedElement(ow_optical_element.OpticalElement):

    def __init__(self, graphical_options=ow_optical_element.GraphicalOptions()):

        graphical_options.is_curved=True

        super().__init__(graphical_options)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = CurvedElement()
    ow.show()
    a.exec_()
    ow.saveSettings()