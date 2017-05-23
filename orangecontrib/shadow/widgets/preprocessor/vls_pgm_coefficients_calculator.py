import sys, numpy

from PyQt5.QtWidgets import QTextEdit, QApplication, QMessageBox
from PyQt5.QtGui import QTextCursor

from oasys.widgets.widget import OWWidget
from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData
from orangecontrib.shadow.util.shadow_util import ShadowPhysics

raise Exception("not yet released")

class OWVlsPgmCoefficientsCalculator(OWWidget):
    name = "VlsPgmCoefficientsCalculator"
    id = "VlsPgmCoefficientsCalculator"
    description = "Calculation of coefficients for VLS PGM"
    icon = "icons/vls_pgm.png"
    author = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi@elettra.eu"
    priority = 10
    category = ""
    keywords = ["oasys", "vls", "pgm"]

    outputs = [{"name":"PreProcessor_Data",
                "type":ShadowPreProcessorData,
                "doc":"PreProcessor Data",
                "id":"PreProcessor_Data"}]

    want_main_area = False

    r_a = Setting(0.0)
    r_b = Setting(0.0)
    k = Setting(1000)

    h = Setting(20)

    units_in_use = Setting(0)
    photon_wavelength = Setting(25.0)
    photon_energy = Setting(500.0)

    c = Setting(1.2)
    grating_diffraction_order = Setting(-1)

    new_units_in_use = Setting(0)
    new_photon_wavelength = Setting(25.0)
    new_photon_energy = Setting(500.0)

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(500)
        self.setFixedHeight(520)

        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "",orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)

        tabs_setting = oasysgui.tabWidget(self.controlArea)

        tab_step_1 = oasysgui.createTabPage(tabs_setting, "Line Density")
        tab_step_2 = oasysgui.createTabPage(tabs_setting, "Angles")

        box = oasysgui.widgetBox(tab_step_1, "VLS-PGM Parameters", orientation="vertical")


        self.le_r_a = oasysgui.lineEdit(box, self, "r_a", "Distance Source-Grating", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_r_b = oasysgui.lineEdit(box, self, "r_b", "Distance Grating-Exit Slits", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_h = oasysgui.lineEdit(box, self, "h", "Vertical Distance Mirror-Grating", labelWidth=260, valueType=float, orientation="horizontal")

        self.le_k   = oasysgui.lineEdit(box, self, "k", "Line Density (0th coeff.)", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(box)


        box_2 = oasysgui.widgetBox(tab_step_1, "Grating Design Parameters", orientation="vertical")


        gui.comboBox(box_2, self, "units_in_use", label="Units in use", labelWidth=260,
                     items=["eV", "Angstroms"],
                     callback=self.set_UnitsInUse, sendSelectedValue=False, orientation="horizontal")

        self.autosetting_box_units_1 = oasysgui.widgetBox(box_2, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        self.autosetting_box_units_2 = oasysgui.widgetBox(box_2, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_UnitsInUse()

        oasysgui.lineEdit(box_2, self, "c", "C factor for optimized energy", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "grating_diffraction_order", "Diffraction Order (- for inside orders)", labelWidth=260, valueType=int, orientation="horizontal")

        ##################################


        box_3 = oasysgui.widgetBox(tab_step_2, "Ray-Tracing Parameter", orientation="vertical")

        gui.comboBox(box_3, self, "new_units_in_use", label="Units in use", labelWidth=260,
                     items=["eV", "Angstroms"],
                     callback=self.set_UnitsInUse2, sendSelectedValue=False, orientation="horizontal")

        self.autosetting_box_units_3 = oasysgui.widgetBox(box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_3, self, "new_photon_energy", "New photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        self.autosetting_box_units_4 = oasysgui.widgetBox(box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.autosetting_box_units_4, self, "new_photon_wavelength", "New wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_UnitsInUse2()


        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = oasysgui.widgetBox(self.controlArea, "System Output", addSpace=True, orientation="horizontal", height=150)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)


    def after_change_workspace_units(self):
        label = self.le_r_a.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_r_b.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_k.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [Lines/" + self.workspace_units_label + "]")

    def set_UnitsInUse(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def set_UnitsInUse2(self):
        self.autosetting_box_units_3.setVisible(self.new_units_in_use == 0)
        self.autosetting_box_units_4.setVisible(self.new_units_in_use == 1)


    def compute(self):
        try:
            self.shadow_output.setText("")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            m = -self.grating_diffraction_order

            if self.units_in_use == 0:
                _lambda =  ShadowPhysics.getWavelengthFromEnergy(self.photon_energy)/self.workspace_units_to_m*1e-10
            elif self.units_in_use == 1:
                _lambda = self.photon_wavelength/self.workspace_units_to_m*1e-10

            sin_alpha = (-m*self.k*_lambda/(self.c**2 - 1)) + \
                        numpy.sqrt(1 + (m*m*self.c*self.c*self.k*self.k*_lambda*_lambda)/((self.c**2 - 1)**2))
            alpha =  numpy.arcsin(sin_alpha)

            beta = numpy.arcsin(sin_alpha-m*self.k*_lambda)
            _beta = numpy.arccos(self.c*numpy.cos(alpha))

            print("Lambda:", _lambda, self.workspace_units_label)
            print("ALPHA:", numpy.degrees(alpha), "deg")
            print("BETA:", numpy.degrees(beta), numpy.degrees(_beta), "deg")

            b2 = (((numpy.cos(alpha)**2)/self.r_a) + ((numpy.cos(beta)**2)/self.r_b))/(-2*m*self.k*_lambda)
            b3 = ((numpy.sin(alpha)*numpy.cos(alpha)**2)/self.r_a**2 - \
                  (numpy.sin(beta)*numpy.cos(beta)**2)/self.r_b**2)/(-2*m*self.k*_lambda)
            b4 = (((4*numpy.sin(alpha)**2 - numpy.cos(alpha)**2)*numpy.cos(alpha)**2)/self.r_a**3 + \
                  ((4*numpy.sin(beta)**2 - numpy.cos(beta)**2)*numpy.cos(beta)**2)/self.r_b**3)/(-8*m*self.k*_lambda)

            print("\nb2", b2)
            print("b3", b3)
            print("b4", b4)


            shadow_coeff_0 = self.k
            shadow_coeff_1 = -2*self.k*b2
            shadow_coeff_2 = 3*self.k*b3
            shadow_coeff_3 = -4*self.k*b4


            print("\nshadow_coeff_0", shadow_coeff_0)
            print("shadow_coeff_1", shadow_coeff_1)
            print("shadow_coeff_2", shadow_coeff_2)
            print("shadow_coeff_3", shadow_coeff_3)


            ############################################
            #
            # 1 - in case of mirror recalculate real ray tracing distance (r_a') from initial r_a and vertical distance
            #     between grating and mirror (h)
            #

            gamma = (alpha + beta)/2

            d_source_to_mirror = self.r_a - (self.h/numpy.abs(numpy.tan(numpy.pi-2*gamma)))
            d_mirror_to_grating = self.h/numpy.abs(numpy.sin(numpy.pi-2*gamma))

            r_a_first = d_source_to_mirror + d_mirror_to_grating

            print("\ngamma", numpy.degrees(gamma))
            print("d_source_to_mirror", d_source_to_mirror, self.workspace_units_label)
            print("d_mirror_to_grating", d_mirror_to_grating, self.workspace_units_label)
            print("r_a_first", r_a_first, self.workspace_units_label)

            ############################################

            if self.new_units_in_use == 0:
                new_lambda =  ShadowPhysics.getWavelengthFromEnergy(self.new_photon_energy)/self.workspace_units_to_m*1e-10
            elif self.new_units_in_use == 1:
                new_lambda = self.new_photon_wavelength/self.workspace_units_to_m*1e-10

            r = self.r_b/r_a_first

            A0 = self.k*new_lambda
            A2 = self.k*new_lambda*self.r_b*b2

            new_c_num = 2*A2 + 4*(A2/A0)**2 + \
                        (4 + 2*A2 - A0**2)*r - \
                        4*(A2/A0)*numpy.sqrt((1 + r)**2 + 2*A2*(1 + r) - r*A0**2)

            new_c_den = -4 + A0**2 - 4*A2 + 4*(A2/A0)**2

            new_c = numpy.sqrt(new_c_num/new_c_den)

            new_sin_alpha = (-m*self.k*new_lambda/(new_c**2 - 1)) + \
                        numpy.sqrt(1 + (m*m*new_c*new_c*self.k*self.k*new_lambda*new_lambda)/((new_c**2 - 1)**2))

            new_alpha =  numpy.arcsin(new_sin_alpha)
            new_beta = numpy.arcsin(new_sin_alpha-m*self.k*new_lambda)
            _new_beta = numpy.arccos(new_c*numpy.cos(new_alpha))


            print("New Lambda:", new_lambda, self.workspace_units_label)
            print("New C:", new_c)
            print("NEW ALPHA:", numpy.degrees(new_alpha), "deg")
            print("NEW BETA:", numpy.degrees(new_beta), numpy.degrees(_new_beta), "deg")


            gamma = (new_alpha + new_beta)/2

            d_source_to_mirror = self.r_a - (self.h/numpy.abs(numpy.tan(numpy.pi-2*gamma)))
            d_mirror_to_grating = self.h/numpy.abs(numpy.sin(numpy.pi-2*gamma))

            r_a_first = d_source_to_mirror + d_mirror_to_grating

            print("\ngamma", numpy.degrees(gamma))
            print("d_source_to_mirror", d_source_to_mirror, self.workspace_units_label)
            print("d_mirror_to_grating", d_mirror_to_grating, self.workspace_units_label)
            print("r_a_first", r_a_first, self.workspace_units_label)


            self.send("PreProcessor_Data", ShadowPreProcessorData())
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

    def checkFields(self):
        self.r_a = congruence.checkPositiveNumber(self.r_a, "Distance Source-Grating")
        self.r_b = congruence.checkPositiveNumber(self.r_b, "Distance Grating-Exit Slits")
        self.k = congruence.checkStrictlyPositiveNumber(self.k, "Line Densityg")

        if self.units_in_use == 0:
            self.photon_energy = congruence.checkPositiveNumber(self.photon_energy, "Photon Energy")
        elif self.units_in_use == 1:
            self.photon_wavelength = congruence.checkPositiveNumber(self.photon_wavelength, "Photon Wavelength")



    def defaults(self):
         self.resetSettings()

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWVlsPgmCoefficientsCalculator()
    w.show()
    app.exec()
    w.saveSettings()
