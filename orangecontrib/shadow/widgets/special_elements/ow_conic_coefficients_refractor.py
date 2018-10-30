import sys
from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_conic_coefficients_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement, ShadowBeam, ShadowPreProcessorData

class ConicCoefficientsRefractor(ow_conic_coefficients_element.ConicCoefficientsElement):

    name = "Refractor Interface"
    description = "Shadow OE: Refractor Interface"
    icon = "icons/refractor_interface.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 2
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("OBJECT Side Data", ShadowPreProcessorData, "setPreProcessorDataObject"),
              ("IMAGE Side Data", ShadowPreProcessorData, "setPreProcessorDataImage")]


    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_refractor=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    ################################################################
    #
    #  SHADOW MANAGEMENT
    #
    ################################################################

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_conic_coefficients_refractor()

    def setPreProcessorDataObject(self, data):
        self.setPreProcessorData(data, side=0)

    def setPreProcessorDataImage(self, data):
        self.setPreProcessorData(data, side=1)

    def setPreProcessorData(self, data, side=0):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                if side == 0: # object
                    if self.optical_constants_refraction_index == 0: # CONSTANT
                        self.optical_constants_refraction_index = 1
                    elif self.optical_constants_refraction_index != 1: # IMAGE OR BOTH
                        self.optical_constants_refraction_index = 3 # BOTH
                    self.file_prerefl_for_object_medium=data.prerefl_data_file
                elif side == 1: # image
                    if self.optical_constants_refraction_index == 0: # CONSTANT
                        self.optical_constants_refraction_index = 2
                    elif self.optical_constants_refraction_index != 2: # OBJECT OR BOTH
                        self.optical_constants_refraction_index = 3 # BOTH
                    self.file_prerefl_for_image_medium=data.prerefl_data_file

                self.set_RefrectorOpticalConstants()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ConicCoefficientsRefractor()
    ow.show()
    a.exec_()
    ow.saveSettings()
