import sys

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

import Shadow
from orangecontrib.shadow.widgets.gui import ow_plane_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class PlaneCrystal(ow_plane_element.PlaneElement):

    name = "Plane Crystal"
    description = "Shadow OE: Plane Crystal"
    icon = "icons/plane_crystal.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 9
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_crystal=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_plane_crystal()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = PlaneCrystal()
    ow.show()
    a.exec_()
    ow.saveSettings()
