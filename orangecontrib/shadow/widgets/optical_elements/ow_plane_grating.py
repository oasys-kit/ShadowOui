import sys, copy

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_plane_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement
from orangecontrib.shadow.util.shadow_objects import VlsPgmPreProcessorData

class PlaneGrating(ow_plane_element.PlaneElement):

    name = "Plane Grating"
    description = "Shadow OE: Plane Grating"
    icon = "icons/plane_grating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 16
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = copy.deepcopy(ow_optical_element.OpticalElement.inputs)
    inputs.append(("VLS-PGM PreProcessor Data", VlsPgmPreProcessorData, "setVlsPgmPreProcessorData"))

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_grating=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_plane_grating()

    def setVlsPgmPreProcessorData(self, data):
        if data is not None:
            self.source_plane_distance = data.d_mirror_to_grating/2
            self.image_plane_distance = data.d_grating_to_exit_slits
            self.angles_respect_to = 0
            self.incidence_angle_deg = data.alpha
            self.reflection_angle_deg =data.beta
            self.mirror_orientation_angle = 2
            self.grating_diffraction_order = -1
            self.grating_auto_setting = 0
            self.grating_ruling_type = 4
            self.grating_ruling_density = data.shadow_coeff_0
            self.grating_poly_coeff_1 = data.shadow_coeff_1
            self.grating_poly_coeff_2 = data.shadow_coeff_2
            self.grating_poly_coeff_3 = data.shadow_coeff_3
            self.grating_poly_coeff_4 = 0.0
            self.grating_poly_signed_absolute = 1

            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()
            self.set_GratingAutosetting()
            self.set_GratingRulingType()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = PlaneGrating()
    ow.show()
    a.exec_()
    ow.saveSettings()
