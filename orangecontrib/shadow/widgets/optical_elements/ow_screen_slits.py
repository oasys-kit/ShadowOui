import sys
import numpy

from orangewidget import gui
from oasys.widgets import congruence
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui.ow_optical_element import OpticalElement, GraphicalOptions
from orangecontrib.shadow.util import ShadowOpticalElement
from orangewidget.settings import Setting

class ScreenSlits(OpticalElement):

    name = "Screen-Slits"
    description = "Shadow OE: Screen/Slits"
    icon = "icons/screen_slits.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    file_to_write_out = Setting(3) # None

    def __init__(self):
        graphical_Options=GraphicalOptions(is_screen_slit=True)

        super().__init__(graphical_Options)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_screen_slit()

    def doSpecificSetting(self, shadow_oe):

        n_screen = 1
        i_screen = numpy.zeros(10)  # after
        i_abs = numpy.zeros(10)
        i_slit = numpy.zeros(10)
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = ['', '', '', '', '', '', '', '', '', '']
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = ['', '', '', '', '', '', '', '', '', '']
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        i_abs[0] = self.absorption
        i_slit[0] = self.aperturing

        if self.aperturing == 1:
            i_stop[0] = self.open_slit_solid_stop
            k_slit[0] = self.aperture_shape

            if self.aperture_shape == 2:
                file_scr_ext[0] = bytes(congruence.checkFileName(self.external_file_with_coordinate), 'utf-8')
            else:
                rx_slit[0] = self.slit_width_xaxis
                rz_slit[0] = self.slit_height_zaxis
                cx_slit[0] = self.slit_center_xaxis
                cz_slit[0] = self.slit_center_zaxis

        if self.absorption == 1:
            thick[0] = self.thickness

            file_abs[0] = bytes(congruence.checkFileName(self.opt_const_file_name), 'utf-8')

        shadow_oe._oe.set_screens(n_screen,
                                  i_screen,
                                  i_abs,
                                  sl_dis,
                                  i_slit,
                                  i_stop,
                                  k_slit,
                                  thick,
                                  numpy.array(file_abs),
                                  rx_slit,
                                  rz_slit,
                                  cx_slit,
                                  cz_slit,
                                  numpy.array(file_scr_ext))



if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ScreenSlits()
    ow.show()
    a.exec_()
    ow.saveSettings()
