import sys, copy

from orangewidget import gui
from PyQt5.QtWidgets import QApplication

from oasys.widgets.exchange import DataExchangeObject

from orangecontrib.shadow.widgets.gui import ow_plane_element, ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement, ShadowBeam, ShadowPreProcessorData
from orangecontrib.shadow.util.shadow_objects import VlsPgmPreProcessorData


class PlaneMirror(ow_plane_element.PlaneElement):

    name = "Plane Mirror"
    description = "Shadow OE: Plane Mirror"
    icon = "icons/plane_mirror.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 2
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = copy.deepcopy(ow_optical_element.OpticalElement.inputs)
    inputs.append(("VLS-PGM PreProcessor Data", VlsPgmPreProcessorData, "setVlsPgmPreProcessorData"))

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_mirror=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_plane_mirror()

    def setVlsPgmPreProcessorData(self, data):
        if data is not None:
            self.source_plane_distance = data.d_source_plane_to_mirror
            self.image_plane_distance =  data.d_mirror_to_grating/2
            self.angles_respect_to = 0
            self.incidence_angle_deg  = (data.alpha + data.beta)/2
            self.reflection_angle_deg = (data.alpha + data.beta)/2

            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = PlaneMirror()
    ow.show()
    a.exec_()
    ow.saveSettings()
