import sys

from orangewidget import gui
from PyQt4.QtGui import QApplication

import Shadow
from orangecontrib.shadow.widgets.gui import ow_plane_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class PlaneGrating(ow_plane_element.PlaneElement):

    name = "Plane Grating"
    description = "Shadow OE: Plane Grating"
    icon = "icons/plane_grating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 16
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_grating=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_plane_grating()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = PlaneGrating()
    ow.show()
    a.exec_()
    ow.saveSettings()