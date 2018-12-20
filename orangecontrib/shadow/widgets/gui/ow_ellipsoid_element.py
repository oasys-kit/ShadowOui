import sys, numpy

from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, \
    ShadowOpticalElement, ShadowBeam, ShadowFile

from . import ow_optical_element, ow_curved_element


class EllipsoidElement(ow_curved_element.CurvedElement):

    def __init__(self, graphical_options=ow_optical_element.GraphicalOptions()):

        graphical_options.is_ellipsoidal=True

        super().__init__(graphical_options)

    # add cleaning slit to fix Shadow Bug
    def completeOperations(self, shadow_oe):
        empty_oe = ShadowOpticalElement.create_empty_oe()
        empty_oe._oe.DUMMY = self.workspace_units_to_cm # Issue #3 : Global User's Unit
        empty_oe._oe.T_SOURCE     = self.source_plane_distance
        empty_oe._oe.T_IMAGE      = 0.0
        empty_oe._oe.T_INCIDENCE  = 0.0
        empty_oe._oe.T_REFLECTION = 180.0
        empty_oe._oe.ALPHA        = 0.0

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

        i_screen[0] = 1
        i_slit[0] = 1

        if self.mirror_orientation_angle == 0 or self.mirror_orientation_angle == 2: # 0, 180
            rx_slit[0] = 1.1*(self.dim_x_plus + self.dim_x_minus)
            rz_slit[0] = 2.5*numpy.abs((self.dim_y_plus + self.dim_y_minus)*numpy.sin(self.incidence_angle_mrad*1e-3))
            cx_slit[0] = (self.dim_x_plus-self.dim_x_minus)/2
            cz_slit[0] = (self.dim_y_plus-self.dim_y_minus)/2
        else:
            rx_slit[0] = 2.5*numpy.abs((self.dim_y_plus + self.dim_y_minus)*numpy.sin(self.incidence_angle_mrad*1e-3))
            rz_slit[0] = 1.1*(self.dim_x_plus + self.dim_x_minus)
            cx_slit[0] = (self.dim_y_plus-self.dim_y_minus)/2
            cz_slit[0] = (self.dim_x_plus-self.dim_x_minus)/2

        empty_oe._oe.set_screens(n_screen,
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

        self.input_beam = ShadowBeam.traceFromOE(self.input_beam, empty_oe, widget_class_name=type(self).__name__)

        shadow_oe._oe.T_SOURCE = 0.0

        super(EllipsoidElement, self).completeOperations(shadow_oe)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = EllipsoidElement()
    ow.show()
    a.exec_()
    ow.saveSettings()
