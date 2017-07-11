import sys
import numpy

from orangewidget import gui
from oasys.widgets import congruence
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui.ow_optical_element import OpticalElement, GraphicalOptions
from orangecontrib.shadow.util import ShadowOpticalElement
from orangewidget.settings import Setting

from syned.widget.widget_decorator import WidgetDecorator

import syned.beamline.beamline as synedb
from syned.beamline.optical_elements.absorbers import beam_stopper, slit, filter
from syned.beamline.optical_elements.ideal_elements import screen
from syned.beamline.shape import Rectangle, Ellipse

class ScreenSlits(OpticalElement, WidgetDecorator):

    name = "Screen-Slits"
    description = "Shadow OE: Screen/Slits"
    icon = "icons/screen_slits.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    file_to_write_out = Setting(3) # None

    OpticalElement.inputs.append(WidgetDecorator.syned_input_data()[0])

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


    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                beamline_element = data.get_beamline_element_at(-1)

                optical_element = beamline_element.get_optical_element()
                coordinates = beamline_element.get_coordinates()

                if not optical_element is None:
                    if isinstance(optical_element, beam_stopper.BeamStopper) or \
                       isinstance(optical_element, slit.Slit):
                        self.absorption = 0
                        self.aperturing = 1
                        self.open_slit_solid_stop = 0 if isinstance(optical_element, slit.Slit) else 1

                        if isinstance(optical_element._boundary_shape, Rectangle):
                            self.aperture_shape = 0

                        elif isinstance(optical_element._boundary_shape, Ellipse):
                            self.aperture_shape = 1

                        left, right, bottom, top = optical_element._boundary_shape.get_boundaries()

                        self.slit_width_xaxis = numpy.abs(right - left)
                        self.slit_height_zaxis = numpy.abs(top - bottom)
                        self.slit_center_xaxis = (right + left) / 2
                        self.slit_center_zaxis = (top + bottom) / 2

                    elif isinstance(optical_element, filter.Filter):
                        self.absorption = 1
                        self.aperturing = 0

                        self.thickness = optical_element._thickness / self.workspace_units_to_m
                        self.opt_const_file_name = "<File for " + optical_element._material + ">"
                    elif isinstance(optical_element, screen.Screen):
                        self.absorption = 0
                        self.aperturing = 0
                    else:
                        raise ValueError("1 - Syned data not correct")

                    self.source_plane_distance = coordinates.p() / self.workspace_units_to_m
                    self.image_plane_distance = coordinates.q() / self.workspace_units_to_m


                    self.set_Aperturing()
                    self.set_Absorption()
                else:
                    raise ValueError("2 - Syned data not correct")
            else:
                raise ValueError("3 - Syned data not correct")

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ScreenSlits()
    ow.show()
    a.exec_()
    ow.saveSettings()