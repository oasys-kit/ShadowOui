import sys, numpy

from PyQt5.QtWidgets import QApplication

from orangewidget.settings import Setting
from orangewidget import gui
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from . import ow_optical_element, ow_curved_element


class EllipsoidElement(ow_curved_element.CurvedElement):

    add_acceptance_slits  = Setting(0)
    acceptance_slits_mode = Setting(0)

    auto_slit_width_xaxis  = Setting(0.0)
    auto_slit_height_zaxis = Setting(0.0)
    auto_slit_center_xaxis = Setting(0.0)
    auto_slit_center_zaxis = Setting(0.0)

    def __init__(self, graphical_options=ow_optical_element.GraphicalOptions()):

        graphical_options.is_ellipsoidal=True

        super().__init__(graphical_options)

        gui.comboBox(self.orientation_box, self, "add_acceptance_slits", label="Add Acceptance Slit", labelWidth=390,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_AddAcceptanceSlits)

        self.orientation_box_1 = oasysgui.widgetBox(self.orientation_box, "", addSpace=False, orientation="vertical", height=140)

        self.cb_acceptance_slits_mode = gui.comboBox(self.orientation_box_1, self, "acceptance_slits_mode", label="Mode", labelWidth=260,
                     items=["Automatic", "Manual"], sendSelectedValue=False, orientation="horizontal", callback=self.set_AcceptanceSlitsMode)

        self.le_auto_slit_width_xaxis  = oasysgui.lineEdit(self.orientation_box_1, self, "auto_slit_width_xaxis", "Slit width/x-axis", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_auto_slit_height_zaxis = oasysgui.lineEdit(self.orientation_box_1, self, "auto_slit_height_zaxis", "Slit height/z-axis", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_auto_slit_center_xaxis = oasysgui.lineEdit(self.orientation_box_1, self, "auto_slit_center_xaxis", "Slit center/x-axis", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_auto_slit_center_zaxis = oasysgui.lineEdit(self.orientation_box_1, self, "auto_slit_center_zaxis", "Slit center/z-axis", labelWidth=260, valueType=float, orientation="horizontal")

        self.orientation_box_2 = oasysgui.widgetBox(self.orientation_box, "", addSpace=False, orientation="vertical", height=140)

        self.set_AddAcceptanceSlits()

        self.le_dim_x_plus.textChanged.connect(self.compute_auto_slits)
        self.le_dim_x_minus.textChanged.connect(self.compute_auto_slits)
        self.le_dim_y_plus.textChanged.connect(self.compute_auto_slits)
        self.le_dim_y_minus.textChanged.connect(self.compute_auto_slits)

        self.set_Dim_Parameters()

    def set_AddAcceptanceSlits(self):
        self.orientation_box_1.setVisible(self.add_acceptance_slits==1)
        self.orientation_box_2.setVisible(self.add_acceptance_slits==0)

        if self.is_infinite == 0:
            self.acceptance_slits_mode=1
            self.cb_acceptance_slits_mode.setEnabled(False)

        self.set_AcceptanceSlitsMode()

    def set_AcceptanceSlitsMode(self):
        self.le_auto_slit_width_xaxis .setEnabled(self.acceptance_slits_mode==1)
        self.le_auto_slit_height_zaxis.setEnabled(self.acceptance_slits_mode==1)
        self.le_auto_slit_center_xaxis.setEnabled(self.acceptance_slits_mode==1)
        self.le_auto_slit_center_zaxis.setEnabled(self.acceptance_slits_mode==1)

        self.compute_auto_slits()

    def after_change_workspace_units(self):
        super(EllipsoidElement, self).after_change_workspace_units()

        label = self.le_auto_slit_width_xaxis.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_auto_slit_height_zaxis.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_auto_slit_center_xaxis.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_auto_slit_center_zaxis.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    # add cleaning slit to fix Shadow Bug

    def set_Dim_Parameters(self):
        super(EllipsoidElement, self).set_Dim_Parameters()

        if hasattr(self, "add_acceptance_slits") and \
                hasattr(self, "acceptance_slits_mode") and \
                hasattr(self, "cb_acceptance_slits_mode"):
            if self.add_acceptance_slits==1:
                if self.is_infinite==0: #infinite
                    self.acceptance_slits_mode = 1
                    self.cb_acceptance_slits_mode.setEnabled(False)
                else:
                    self.cb_acceptance_slits_mode.setEnabled(True)

                self.set_AcceptanceSlitsMode()

    def compute_auto_slits(self):
        if self.acceptance_slits_mode==0: #auto slits
            self.auto_slit_width_xaxis  = round(1.1*(self.dim_x_plus + self.dim_x_minus), 3)
            self.auto_slit_height_zaxis = round(2.0*numpy.abs((self.dim_y_plus + self.dim_y_minus)*numpy.sin(self.incidence_angle_mrad*1e-3)), 3)
            self.auto_slit_center_xaxis = round((self.dim_x_plus-self.dim_x_minus)/2, 3)
            self.auto_slit_center_zaxis = round((self.dim_y_plus-self.dim_y_minus)/2, 3)

    def manage_acceptance_slits(self, shadow_oe):
        if self.add_acceptance_slits==1:
            congruence.checkStrictlyPositiveNumber(self.auto_slit_width_xaxis, "Slit width/x-axis")
            congruence.checkStrictlyPositiveNumber(self.auto_slit_height_zaxis, "Slit height/z-axis")

            shadow_oe.add_acceptance_slits(self.auto_slit_width_xaxis,
                                           self.auto_slit_height_zaxis,
                                           self.auto_slit_center_xaxis,
                                           self.auto_slit_center_zaxis)

    def completeOperations(self, shadow_oe):
        self.manage_acceptance_slits(shadow_oe)

        super(EllipsoidElement, self).completeOperations(shadow_oe)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = EllipsoidElement()
    ow.show()
    a.exec_()
    ow.saveSettings()
