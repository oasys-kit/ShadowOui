import sys
from PyQt5.QtWidgets import QApplication

from . import ow_optical_element, ow_curved_element


class SphericElement(ow_curved_element.CurvedElement):

    def __init__(self, graphical_options=ow_optical_element.GraphicalOptions()):

        graphical_options.is_spheric=True

        super().__init__(graphical_options)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SphericElement()
    ow.show()
    a.exec_()
    ow.saveSettings()