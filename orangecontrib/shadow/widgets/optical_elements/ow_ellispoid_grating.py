import sys
from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_ellipsoid_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class EllipsoidGrating(ow_ellipsoid_element.EllipsoidElement):

    name = "Ellipsoid Grating"
    description = "Shadow OE: Ellipsoid Grating"
    icon = "icons/ellipsoid_grating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 20
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_grating=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    ################################################################
    #
    #  SHADOW MANAGEMENT
    #
    ################################################################

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_ellipsoid_grating()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = EllipsoidGrating()
    ow.show()
    a.exec_()
    ow.saveSettings()
