import sys
from numpy import array

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_paraboloid_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class ParaboloidGrating(ow_paraboloid_element.ParaboloidElement):

    name = "Paraboloid Grating"
    description = "Shadow OE: Paraboloid Grating"
    icon = "icons/paraboloid_grating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 19
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
        return ShadowOpticalElement.create_paraboloid_grating()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ParaboloidGrating()
    ow.show()
    a.exec_()
    ow.saveSettings()
