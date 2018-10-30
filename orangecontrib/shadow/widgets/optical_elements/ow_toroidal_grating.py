import sys
from numpy import array

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_toroidal_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class ToroidalGrating(ow_toroidal_element.ToroidalElement):

    name = "Toroidal Grating"
    description = "Shadow OE: Toroidal Grating"
    icon = "icons/toroidal_grating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 18
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
        return ShadowOpticalElement.create_toroidal_grating()

    def doSpecificSetting(self, shadow_oe):
        return None

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ToroidalGrating()
    ow.show()
    a.exec_()
    ow.saveSettings()
