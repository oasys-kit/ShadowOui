import sys, numpy

from PyQt5.QtWidgets import QApplication

from orangewidget.settings import Setting
from orangewidget import gui

from . import ow_optical_element, ow_curved_element


class EllipsoidElement(ow_curved_element.CurvedElement):

    add_acceptance_slits = Setting(0)

    def __init__(self, graphical_options=ow_optical_element.GraphicalOptions()):

        graphical_options.is_ellipsoidal=True

        super().__init__(graphical_options)

        gui.comboBox(self.orientation_box, self, "add_acceptance_slits", label="Add Acceptance Slit", labelWidth=390,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

    # add cleaning slit to fix Shadow Bug

    def completeOperations(self, shadow_oe):
        if self.add_acceptance_slits==1:
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

            rx_slit[0] = 1.1*(self.dim_x_plus + self.dim_x_minus)
            rz_slit[0] = 2.0*numpy.abs((self.dim_y_plus + self.dim_y_minus)*numpy.sin(self.incidence_angle_mrad*1e-3))
            cx_slit[0] = (self.dim_x_plus-self.dim_x_minus)/2
            cz_slit[0] = (self.dim_y_plus-self.dim_y_minus)/2

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

        super(EllipsoidElement, self).completeOperations(shadow_oe)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = EllipsoidElement()
    ow.show()
    a.exec_()
    ow.saveSettings()
