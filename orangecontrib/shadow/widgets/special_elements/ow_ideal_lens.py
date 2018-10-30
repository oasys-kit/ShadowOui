import sys
import numpy

from orangewidget import gui
from oasys.widgets import congruence
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui.ow_optical_element import OpticalElement, GraphicalOptions
from orangecontrib.shadow.util import ShadowOpticalElement
from orangewidget.settings import Setting

class IdealLens(OpticalElement):

    name = "Ideal Lens"
    description = "Shadow OE: Ideal Lens"
    icon = "icons/ideal_lens.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 3
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=GraphicalOptions(is_ideal_lens=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_ideal_lens()


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = IdealLens()
    ow.show()
    a.exec_()
    ow.saveSettings()
