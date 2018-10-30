import sys
from numpy import array

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_paraboloid_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class ParaboloidCrystal(ow_paraboloid_element.ParaboloidElement):

    name = "Paraboloid Crystal"
    description = "Shadow OE: Paraboloid Crystal"
    icon = "icons/paraboloid_crystal.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 12
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_crystal=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    ################################################################
    #
    #  SHADOW MANAGEMENT
    #
    ################################################################

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_paraboloid_crystal()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ParaboloidCrystal()
    ow.show()
    a.exec_()
    ow.saveSettings()
