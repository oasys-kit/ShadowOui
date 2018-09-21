import sys
from numpy import array

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_spheric_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class SphericMirror(ow_spheric_element.SphericElement):

    name = "Spherical Mirror"
    description = "Shadow OE: Spherical Mirror"
    icon = "icons/spherical_mirror.png"
    # icon = "icons/courbe_2.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 3
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_mirror=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    ################################################################
    #
    #  SHADOW MANAGEMENT
    #
    ################################################################

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_spherical_mirror()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = SphericMirror()
    ow.show()
    a.exec_()
    ow.saveSettings()
