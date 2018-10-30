import sys

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_spheric_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class SphericGrating(ow_spheric_element.SphericElement):

    name = "Spherical Grating"
    description = "Shadow OE: Spherical Grating"
    icon = "icons/spherical_grating.png"
    # icon = "icons/reseau_courbe_2.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 17
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_grating=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_spherical_grating()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SphericGrating()
    ow.show()
    a.exec_()
    ow.saveSettings()
