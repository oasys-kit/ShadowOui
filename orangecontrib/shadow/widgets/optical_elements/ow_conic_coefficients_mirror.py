import sys
from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_conic_coefficients_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement

import copy
from orangecontrib.shadow.util.shadow_objects import ConicCoefficientsPreProcessorData

class ConicCoefficientsMirror(ow_conic_coefficients_element.ConicCoefficientsElement):

    name = "Conic Coefficients Mirror"
    description = "Shadow OE: Conic Coefficients Mirror"
    icon = "icons/conic_coefficients_mirror.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 8
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = copy.deepcopy(ow_optical_element.OpticalElement.inputs)
    inputs.append(("ConicCoeff_PreProcessor Data", ConicCoefficientsPreProcessorData, "SetConicCoeffPreProcessorData"))


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
        return ShadowOpticalElement.create_conic_coefficients_mirror()

    def SetConicCoeffPreProcessorData(self, data):
        if data is not None:
            print("Received data....")
            print("Data before: ")

            print("conic_coefficient_0", self.conic_coefficient_0)
            print("conic_coefficient_1", self.conic_coefficient_1)
            print("conic_coefficient_2", self.conic_coefficient_2)
            print("conic_coefficient_3", self.conic_coefficient_3)
            print("conic_coefficient_4", self.conic_coefficient_4)
            print("conic_coefficient_5", self.conic_coefficient_5)
            print("conic_coefficient_6", self.conic_coefficient_6)
            print("conic_coefficient_7", self.conic_coefficient_7)
            print("conic_coefficient_8", self.conic_coefficient_8)
            print("conic_coefficient_9", self.conic_coefficient_9)

            self.conic_coefficient_0 = data.conic_coefficient_0
            self.conic_coefficient_1 = data.conic_coefficient_1
            self.conic_coefficient_2 = data.conic_coefficient_2
            self.conic_coefficient_3 = data.conic_coefficient_3
            self.conic_coefficient_4 = data.conic_coefficient_4
            self.conic_coefficient_5 = data.conic_coefficient_5
            self.conic_coefficient_6 = data.conic_coefficient_6
            self.conic_coefficient_7 = data.conic_coefficient_7
            self.conic_coefficient_8 = data.conic_coefficient_8
            self.conic_coefficient_9 = data.conic_coefficient_9

            print("Data after: ")
            print("conic_coefficient_0", self.conic_coefficient_0)
            print("conic_coefficient_1", self.conic_coefficient_1)
            print("conic_coefficient_2", self.conic_coefficient_2)
            print("conic_coefficient_3", self.conic_coefficient_3)
            print("conic_coefficient_4", self.conic_coefficient_4)
            print("conic_coefficient_5", self.conic_coefficient_5)
            print("conic_coefficient_6", self.conic_coefficient_6)
            print("conic_coefficient_7", self.conic_coefficient_7)
            print("conic_coefficient_8", self.conic_coefficient_8)
            print("conic_coefficient_9", self.conic_coefficient_9)



            # self.conic_coefficient_0 = float(shadow_file.getProperty("CCC(1)"))
            # self.conic_coefficient_1 = float(shadow_file.getProperty("CCC(2)"))
            # self.conic_coefficient_2 = float(shadow_file.getProperty("CCC(3)"))
            # self.conic_coefficient_3 = float(shadow_file.getProperty("CCC(4)"))
            # self.conic_coefficient_4 = float(shadow_file.getProperty("CCC(5)"))
            # self.conic_coefficient_5 = float(shadow_file.getProperty("CCC(6)"))
            # self.conic_coefficient_6 = float(shadow_file.getProperty("CCC(7)"))
            # self.conic_coefficient_7 = float(shadow_file.getProperty("CCC(8)"))
            # self.conic_coefficient_8 = float(shadow_file.getProperty("CCC(9)"))
            # self.conic_coefficient_9 = float(shadow_file.getProperty("CCC(10)"))

            # self.source_plane_distance = data.d_source_plane_to_mirror
            # self.image_plane_distance =  data.d_mirror_to_grating/2
            # self.angles_respect_to = 0
            # self.incidence_angle_deg  = (data.alpha + data.beta)/2
            # self.reflection_angle_deg = (data.alpha + data.beta)/2
            #
            # self.calculate_incidence_angle_mrad()
            # self.calculate_reflection_angle_mrad()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ConicCoefficientsMirror()
    ow.show()
    a.exec_()
    ow.saveSettings()
