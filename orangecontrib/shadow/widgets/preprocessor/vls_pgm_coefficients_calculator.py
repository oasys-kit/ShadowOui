import os, sys, numpy

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from PyQt5.QtGui import QTextCursor, QPixmap

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow.util.shadow_objects import VlsPgmPreProcessorData
from orangecontrib.shadow.util.shadow_util import ShadowPhysics

class OWVlsPgmCoefficientsCalculator(OWWidget):
    name = "VLS PGM Coefficients Calculator"
    id = "VlsPgmCoefficientsCalculator"
    description = "Calculation of coefficients for VLS PGM"
    icon = "icons/vls_pgm.png"
    author = "Luca Rebuffi"
    maintainer_email = "lrebuffi@anl.gov"
    priority = 10
    category = ""
    keywords = ["oasys", "vls", "pgm"]

    outputs = [{"name":"PreProcessor_Data",
                "type":VlsPgmPreProcessorData,
                "doc":"PreProcessor Data",
                "id":"PreProcessor_Data"}]

    want_main_area = True

    last_element_distance = Setting(0.0)

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
    new_c_value = Setting(1.2222)
    new_c_flag = Setting(0)

    image_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "vls_pgm_layout.png")
    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "vls_pgm_usage.png")

    design_alpha = 0.0
    design_beta = 0.0

    b2 = 0.0
    b3 = 0.0
    b4 = 0.0

    shadow_coeff_0 = 0.0
    shadow_coeff_1 = 0.0
    shadow_coeff_2 = 0.0
    shadow_coeff_3 = 0.0

    d_source_to_mirror = 0.0
    d_source_plane_to_mirror = 0.0
    d_mirror_to_grating = 0.0

    raytracing_alpha = 0.0
    raytracing_beta = 0.0

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(1170)
        self.setFixedHeight(500)

        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "", orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(425)

        tab_step_1 = oasysgui.createTabPage(tabs_setting, "Line Density Calculation")
        tab_step_2 = oasysgui.createTabPage(tabs_setting, "Angles Calculation")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        box = oasysgui.widgetBox(tab_step_1, "VLS-PGM Layout Parameters", orientation="vertical")

        self.le_r_a = oasysgui.lineEdit(box, self, "r_a", "Distance Source-Grating", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_r_b = oasysgui.lineEdit(box, self, "r_b", "Distance Grating-Exit Slits", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_h = oasysgui.lineEdit(box, self, "h", "Vertical Distance Mirror-Grating", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_l_e = oasysgui.lineEdit(box, self, "last_element_distance", "Distance Source-Last Image Plane\nbefore Mirror (if present)", labelWidth=260, valueType=float, orientation="horizontal")

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


        gui.comboBox(box_3, self, "new_c_flag", label="C factor for angles calculation", labelWidth=260,
                     items=["the same as for line density", "new one"],
                     callback=self.set_CfactorNew, sendSelectedValue=False, orientation="horizontal")

        self.c_box_new = oasysgui.widgetBox(box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.c_box_new, self, "new_c_value", "new C for angles calculation", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_CfactorNew()


        tabs_out = oasysgui.tabWidget(self.mainArea)

        tab_out_1 = oasysgui.createTabPage(tabs_out, "Calculation Results")
        tab_out_2 = oasysgui.createTabPage(tabs_out, "Output")

        figure_box_1 = oasysgui.widgetBox(tab_out_1, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setPixmap(QPixmap(self.image_path))

        figure_box_1.layout().addWidget(label)

        output_box = oasysgui.widgetBox(tab_out_1, "", addSpace=True, orientation="horizontal")

        output_box_1 = oasysgui.widgetBox(output_box, "Design Ouput", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(output_box_1, self, "design_alpha", "Alpha [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_1, self, "design_beta", "Beta [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        gui.separator(output_box_1)
        self.le_shadow_coeff_0 = oasysgui.lineEdit(output_box_1, self, "shadow_coeff_0", "Line Density 0-coeff.", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_shadow_coeff_1 = oasysgui.lineEdit(output_box_1, self, "shadow_coeff_1", "Line Density 1-coeff.", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_shadow_coeff_2 = oasysgui.lineEdit(output_box_1, self, "shadow_coeff_2", "Line Density 2-coeff.", labelWidth=220, valueType=float, orientation="horizontal")
        self.le_shadow_coeff_3 = oasysgui.lineEdit(output_box_1, self, "shadow_coeff_3", "Line Density 3-coeff.", labelWidth=220, valueType=float, orientation="horizontal")

        output_box_2 = oasysgui.widgetBox(output_box, "Ray-Tracing Ouput", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(output_box_2, self, "raytracing_alpha", "Alpha [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_box_2, self, "raytracing_beta", "Beta [deg]", labelWidth=220, valueType=float, orientation="horizontal")
        gui.separator(output_box_2)
        self.le_d_source_to_mirror = oasysgui.lineEdit(output_box_2, self, "d_source_to_mirror", "Source to Mirror distance", labelWidth=230, valueType=float, orientation="horizontal")
        self.le_d_source_plane_to_mirror = oasysgui.lineEdit(output_box_2, self, "d_source_plane_to_mirror", "Source Plane to Mirror distance", labelWidth=230, valueType=float, orientation="horizontal")
        self.le_d_mirror_to_grating = oasysgui.lineEdit(output_box_2, self, "d_mirror_to_grating", "Mirror to Grating distance", labelWidth=230, valueType=float, orientation="horizontal")


        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out_2, "System Output", addSpace=True, orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

    def after_change_workspace_units(self):
        label = self.le_r_a.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_r_b.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_l_e.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_k.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [Lines/" + self.workspace_units_label + "]")
        label = self.le_d_source_to_mirror.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_d_source_plane_to_mirror.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_d_mirror_to_grating.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_shadow_coeff_0.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [Lines." + self.workspace_units_label + "-1]")
        label = self.le_shadow_coeff_1.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [Lines." + self.workspace_units_label + "-2]")
        label = self.le_shadow_coeff_2.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [Lines." + self.workspace_units_label + "-3]")
        label = self.le_shadow_coeff_3.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [Lines." + self.workspace_units_label + "-4]")

    def set_UnitsInUse(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def set_UnitsInUse2(self):
        self.autosetting_box_units_3.setVisible(self.new_units_in_use == 0)
        self.autosetting_box_units_4.setVisible(self.new_units_in_use == 1)

    def set_CfactorNew(self):
        self.c_box_new.setVisible(self.new_c_flag == 1)


    def compute(self):
        try:
            self.shadow_output.setText("")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            m = -self.grating_diffraction_order

            if self.units_in_use == 0:
                wavelength =  ShadowPhysics.getWavelengthFromEnergy(self.photon_energy)/self.workspace_units_to_m*1e-10
            elif self.units_in_use == 1:
                wavelength = self.photon_wavelength/self.workspace_units_to_m*1e-10

            sin_alpha = (-m*self.k*wavelength/(self.c**2 - 1)) + \
                        numpy.sqrt(1 + (m*m*self.c*self.c*self.k*self.k*wavelength*wavelength)/((self.c**2 - 1)**2))

            alpha = numpy.arcsin(sin_alpha)
            beta = numpy.arcsin(sin_alpha-m*self.k*wavelength)

            self.design_alpha =  round(numpy.degrees(alpha), 3)
            self.design_beta = round(numpy.degrees(beta), 3)
            #_beta = numpy.arccos(self.c*numpy.cos(alpha))

            print("####################################################")
            print("# DESIGN PHASE")
            print("####################################################\n")

            print("Photon Wavelength:", wavelength, self.workspace_units_label)
            print("Design ALPHA     :", self.design_alpha, "deg")
            print("Design BETA      :", self.design_beta, "deg")

            self.b2 = (((numpy.cos(alpha)**2)/self.r_a) + ((numpy.cos(beta)**2)/self.r_b))/(-2*m*self.k*wavelength)
            self.b3 = ((numpy.sin(alpha)*numpy.cos(alpha)**2)/self.r_a**2 - \
                      (numpy.sin(beta)*numpy.cos(beta)**2)/self.r_b**2)/(-2*m*self.k*wavelength)
            self.b4 = (((4*numpy.sin(alpha)**2 - numpy.cos(alpha)**2)*numpy.cos(alpha)**2)/self.r_a**3 + \
                      ((4*numpy.sin(beta)**2 - numpy.cos(beta)**2)*numpy.cos(beta)**2)/self.r_b**3)/(-8*m*self.k*wavelength)

            print("\nb2:", self.b2)
            print("b3:", self.b3)
            print("b4:", self.b4)

            self.shadow_coeff_0 = round(self.k, 8)
            self.shadow_coeff_1 = round(-2*self.k*self.b2, 8)
            self.shadow_coeff_2 = round(3*self.k*self.b3, 8)
            self.shadow_coeff_3 = round(-4*self.k*self.b4, 8)

            print("\nshadow_coeff_0:", self.shadow_coeff_0)
            print("shadow_coeff_1:", self.shadow_coeff_1)
            print("shadow_coeff_2:", self.shadow_coeff_2)
            print("shadow_coeff_3:", self.shadow_coeff_3)

            ############################################
            #
            # 1 - in case of mirror recalculate real ray tracing distance (r_a') from initial r_a and vertical distance
            #     between grating and mirror (h)
            #

            gamma = (alpha + beta)/2

            d_source_to_mirror = self.r_a - (self.h/numpy.abs(numpy.tan(numpy.pi-2*gamma)))
            d_mirror_to_grating = self.h/numpy.abs(numpy.sin(numpy.pi-2*gamma))

            r_a_first = d_source_to_mirror + d_mirror_to_grating

            print("\ngamma                   :", numpy.degrees(gamma), "deg")
            print("Source to Mirror distance :", d_source_to_mirror, self.workspace_units_label)
            print("Mirror to Grating distance:", d_mirror_to_grating, self.workspace_units_label)
            print("R_a'                      :", r_a_first, self.workspace_units_label)

            ############################################

            if self.new_units_in_use == 0:
                newwavelength =  ShadowPhysics.getWavelengthFromEnergy(self.new_photon_energy)/self.workspace_units_to_m*1e-10
            elif self.new_units_in_use == 1:
                newwavelength = self.new_photon_wavelength/self.workspace_units_to_m*1e-10

            r = self.r_b/r_a_first

            A0 = self.k*newwavelength
            A2 = self.k*newwavelength*self.r_b*self.b2

            new_c_num = 2*A2 + 4*(A2/A0)**2 + \
                        (4 + 2*A2 - A0**2)*r - \
                        4*(A2/A0)*numpy.sqrt((1 + r)**2 + 2*A2*(1 + r) - r*A0**2)

            new_c_den = -4 + A0**2 - 4*A2 + 4*(A2/A0)**2

            new_c = numpy.sqrt(new_c_num/new_c_den)

            if self.new_c_flag == 1:
                new_c = self.new_c_value

            new_sin_alpha = (-m*self.k*newwavelength/(new_c**2 - 1)) + \
                        numpy.sqrt(1 + (m*m*new_c*new_c*self.k*self.k*newwavelength*newwavelength)/((new_c**2 - 1)**2))

            new_alpha =  numpy.arcsin(new_sin_alpha)
            new_beta  = numpy.arcsin(new_sin_alpha-m*self.k*newwavelength)

            self.raytracing_alpha = round(numpy.degrees(new_alpha), 6)
            self.raytracing_beta  = round(numpy.degrees(new_beta), 6)
            #_new_beta = numpy.arccos(new_c*numpy.cos(new_alpha))

            print("####################################################")
            print("# RAY-TRACING PHASE")
            print("####################################################\n")

            print("Ray-Tracing Wavelength:", newwavelength, self.workspace_units_label)
            print("Ray-Tracing C         :", new_c)
            print("Ray-Tracing ALPHA     :", self.raytracing_alpha, "deg")
            print("Ray-Tracing BETA      :", self.raytracing_beta, "deg")

            gamma = (new_alpha + new_beta)/2

            self.d_source_to_mirror  = self.r_a - (self.h/numpy.abs(numpy.tan(numpy.pi-2*gamma)))
            self.d_mirror_to_grating = self.h/numpy.abs(numpy.sin(numpy.pi-2*gamma))

            r_a_first = self.d_source_to_mirror + self.d_mirror_to_grating

            self.d_source_to_mirror  = round(self.d_source_to_mirror , 3)
            self.d_source_plane_to_mirror = round(self.d_source_to_mirror - self.last_element_distance, 3)
            self.d_mirror_to_grating = round(self.d_mirror_to_grating, 3)

            print("\ngamma                         :", numpy.degrees(gamma), "deg")
            print("Source to Mirror distance       :", self.d_source_to_mirror, self.workspace_units_label)
            print("Source Plane to Mirror distance :", self.d_source_plane_to_mirror, self.workspace_units_label)
            print("Mirror to Grating distance      :", self.d_mirror_to_grating, self.workspace_units_label)
            print("R_a'                            :", r_a_first, self.workspace_units_label)

            self.send("PreProcessor_Data", VlsPgmPreProcessorData(shadow_coeff_0 = self.shadow_coeff_0,
                                                                  shadow_coeff_1 = self.shadow_coeff_1,
                                                                  shadow_coeff_2 = self.shadow_coeff_2,
                                                                  shadow_coeff_3 = self.shadow_coeff_3,
                                                                  d_source_plane_to_mirror= self.d_source_plane_to_mirror,
                                                                  d_mirror_to_grating = self.d_mirror_to_grating,
                                                                  d_grating_to_exit_slits = self.r_b,
                                                                  alpha = self.raytracing_alpha,
                                                                  beta= self.raytracing_beta))
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

    def checkFields(self):
        self.r_a = congruence.checkPositiveNumber(self.r_a, "Distance Source-Grating")
        self.r_b = congruence.checkPositiveNumber(self.r_b, "Distance Grating-Exit Slits")
        self.last_element_distance = congruence.checkPositiveNumber(self.last_element_distance, "Distance Source-Last Image Plane before Mirror")
        congruence.checkLessOrEqualThan(self.last_element_distance, self.r_a, "Distance Source-Last Image Plane before Mirror", "Distance Source-Grating")
        self.k = congruence.checkStrictlyPositiveNumber(self.k, "Line Density")

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
    w.workspace_units_to_m = 1.0
    w.workspace_units_label = "m"
    w.show()
    app.exec()
    w.saveSettings()
