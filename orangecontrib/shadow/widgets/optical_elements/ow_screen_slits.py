import sys
from numpy import array, zeros
import Orange

from Orange.widgets import widget, gui
from Orange.widgets.settings import Setting
from PyQt4.QtGui import QApplication

import Shadow
from orangecontrib.shadow.util.shadow_util import ShadowGui
from orangecontrib.shadow.widgets.gui.ow_optical_element import OpticalElement, GraphicalOptions
from orangecontrib.shadow.util import ShadowOpticalElement


class ScreenSlits(OpticalElement):

    name = "Screen-Slits"
    description = "Shadow OE: Screen/Slits"
    icon = "icons/screen_slits.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=GraphicalOptions(is_screen_slit=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_screen_slit()

    def doSpecificSetting(self, shadow_oe):

        n_screen = 1
        i_screen = array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # after
        i_abs = zeros(10)
        i_slit = zeros(10)
        i_stop = zeros(10)
        k_slit = zeros(10)
        thick = zeros(10)
        file_abs = array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = zeros(10)
        rz_slit = zeros(10)
        sl_dis = zeros(10)
        file_src_ext = array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = zeros(10)
        cz_slit = zeros(10)

        i_abs[0] = self.absorption
        i_slit[0] = self.aperturing

        if self.aperturing == 1:
            i_stop[0] = self.open_slit_solid_stop
            k_slit[0] = self.aperture_shape

            if self.aperture_shape == 2:
                file_src_ext[0] = bytes(self.external_file_with_coordinate, 'utf-8')
            else:
                rx_slit[0] = self.slit_width_xaxis
                rz_slit[0] = self.slit_height_zaxis
                cx_slit[0] = self.slit_center_xaxis
                cz_slit[0] = self.slit_center_zaxis

        if self.absorption == 1:
            thick[0] = self.thickness
            file_abs[0] = bytes(self.opt_const_file_name, 'utf-8')

        shadow_oe.oe.set_screens(n_screen,
                                i_screen,
                                i_abs,
                                sl_dis,
                                i_slit,
                                i_stop,
                                k_slit,
                                thick,
                                file_abs,
                                rx_slit,
                                rz_slit,
                                cx_slit,
                                cz_slit,
                                file_src_ext)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ScreenSlits()
    ow.show()
    a.exec_()
    ow.saveSettings()