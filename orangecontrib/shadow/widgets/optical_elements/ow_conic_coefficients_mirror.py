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
            verbose = 0

            if verbose:
                print("\nReceived data....")
                print("\n********************Data before, new: ")

                print("title", data.title)
                print("conic_coefficient_0",      self.conic_coefficient_0, data.conic_coefficient_0)
                print("conic_coefficient_1",      self.conic_coefficient_1, data.conic_coefficient_1)
                print("conic_coefficient_2",      self.conic_coefficient_2, data.conic_coefficient_2)
                print("conic_coefficient_3",      self.conic_coefficient_3, data.conic_coefficient_3)
                print("conic_coefficient_4",      self.conic_coefficient_4, data.conic_coefficient_4)
                print("conic_coefficient_5",      self.conic_coefficient_5, data.conic_coefficient_5)
                print("conic_coefficient_6",      self.conic_coefficient_6, data.conic_coefficient_6)
                print("conic_coefficient_7",      self.conic_coefficient_7, data.conic_coefficient_7)
                print("conic_coefficient_8",      self.conic_coefficient_8, data.conic_coefficient_8)
                print("conic_coefficient_9",      self.conic_coefficient_9, data.conic_coefficient_9)
                print("source_plane_distance",    self.source_plane_distance, data.source_plane_distance)
                print("image_plane_distance",     self.image_plane_distance, data.image_plane_distance)
                print("angles_respect_to",        self.angles_respect_to, data.angles_respect_to)
                print("incidence_angle_deg",      self.incidence_angle_deg, data.incidence_angle_deg)
                print("reflection_angle_deg",     self.reflection_angle_deg, data.reflection_angle_deg)
                print("mirror_orientation_angle", self.mirror_orientation_angle, data.mirror_orientation_angle)

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

            if data.source_plane_distance    is not None: self.source_plane_distance    = data.source_plane_distance
            if data.image_plane_distance     is not None: self.image_plane_distance     = data.image_plane_distance
            if data.angles_respect_to        is not None: self.angles_respect_to        = data.angles_respect_to
            if data.incidence_angle_deg      is not None: self.incidence_angle_deg      = data.incidence_angle_deg
            if data.reflection_angle_deg     is not None: self.reflection_angle_deg     = data.reflection_angle_deg
            if data.mirror_orientation_angle is not None: self.mirror_orientation_angle = data.mirror_orientation_angle

            if verbose:
                print("\n********************Data after: ")

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
                print("source_plane_distance",    self.source_plane_distance)
                print("image_plane_distance",     self.image_plane_distance)
                print("angles_respect_to",        self.angles_respect_to)
                print("incidence_angle_deg",      self.incidence_angle_deg)
                print("reflection_angle_deg",     self.reflection_angle_deg)
                print("mirror_orientation_angle", self.mirror_orientation_angle)


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ConicCoefficientsMirror()
    ow.show()
    a.exec_()
    ow.saveSettings()
