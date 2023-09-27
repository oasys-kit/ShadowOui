import sys
from orangewidget import gui
from PyQt5.QtWidgets import QApplication, QMessageBox

from orangecontrib.shadow.widgets.gui import ow_conic_coefficients_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement, ShadowBeam, ShadowPreProcessorData
from oasys.util.oasys_util import TriggerOut
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

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
              ("Trigger", TriggerOut, "sendNewBeam"),
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


    def sendNewBeam(self, trigger):
        try:
            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    if trigger and trigger.new_object == True:
                        if trigger.has_additional_parameter("variable_name"):
                            variable_name = trigger.get_additional_parameter("variable_name").strip()
                            variable_display_name = trigger.get_additional_parameter("variable_display_name").strip()
                            variable_value = trigger.get_additional_parameter("variable_value")
                            variable_um = trigger.get_additional_parameter("variable_um")

                            def check_options(variable_name):
                                if variable_name in ["mm_mirror_offset_x",
                                                     "mm_mirror_rotation_x",
                                                     "mm_mirror_offset_y",
                                                     "mm_mirror_rotation_y",
                                                     "mm_mirror_offset_z",
                                                     "mm_mirror_rotation_z"]:
                                    self.mirror_movement = 1
                                    self.set_MirrorMovement()
                                elif variable_name in ["sm_offset_x_mirr_ref_frame",
                                                       "sm_offset_y_mirr_ref_frame",
                                                       "sm_offset_z_mirr_ref_frame",
                                                       "sm_rotation_around_x",
                                                       "sm_rotation_around_y",
                                                       "sm_rotation_around_z"]:
                                    self.source_movement = 1
                                    self.set_SourceMovement()
                                elif variable_name == "mirror_orientation_angle_user_value":
                                    self.mirror_orientation_angle = 4
                                    self.mirror_orientation_angle_user()
                                elif variable_name == "incidence_angle_deg":
                                    self.calculate_incidence_angle_mrad()
                                elif variable_name == "incidence_angle_mrad":
                                    self.calculate_incidence_angle_deg()
                                elif variable_name == "reflection_angle_deg":
                                    self.calculate_reflection_angle_mrad()
                                elif variable_name == "reflection_angle_mrad":
                                    self.calculate_reflection_angle_deg()

                            def check_number(x):
                                try:    return float(x)
                                except: return x

                            if "," in variable_name:
                                variable_names = variable_name.split(",")

                                if isinstance(variable_value, str) and "," in variable_value:
                                    variable_values = variable_value.split(",")
                                    for variable_name, variable_value in zip(variable_names, variable_values):
                                        setattr(self, variable_name.strip(), check_number(variable_value))
                                        check_options(variable_name)
                                else:
                                    for variable_name in variable_names:
                                        setattr(self, variable_name.strip(), check_number(variable_value))
                                        check_options(variable_name)
                            else:
                                setattr(self, variable_name, check_number(variable_value))
                                check_options(variable_name)

                            self.input_beam.setScanningData(ShadowBeam.ScanningData(variable_name, variable_value, variable_display_name, variable_um))

                        self.traceOpticalElement()
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception



if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ConicCoefficientsRefractor()
    ow.show()
    a.exec_()
    ow.saveSettings()
