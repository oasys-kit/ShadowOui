import os

from PyQt5.QtWidgets import QLabel, QMessageBox, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import orangecanvas.resources as resources
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData
from orangecontrib.shadow.widgets.gui import ow_compound_optical_element

class CRL(ow_compound_optical_element.CompoundOpticalElement):
    name = "Compound Refractive Lens"
    description = "Shadow Compound OE: Compound Refractive Lens"
    icon = "icons/crl.png"
    priority = 2

    nlenses = Setting(30)
    slots_empty = Setting(0)
    thickness = Setting(2.5)

    p = Setting(0.0)
    q = Setting(0.0)
    surface_shape = Setting(1)
    convex_to_the_beam = Setting(0)

    has_finite_diameter = Setting(0)
    diameter = Setting(0.0)

    is_cylinder = Setting(0)
    cylinder_angle = Setting(0.0)

    ri_calculation_mode = Setting(0)
    prerefl_file = Setting("NONE SPECIFIED")
    refraction_index = Setting(1.0)
    attenuation_coefficient = Setting(0.0)

    radius = Setting(0.1)
    interthickness = Setting(0.03)

    use_ccc = Setting(0)

    help_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "crl_help.png")

    def __init__(self):
        super().__init__()

        tabs = oasysgui.tabWidget(self.tab_bas)
        tab_1 = oasysgui.createTabPage(tabs, "C.R.L. Input Parameters")
        tab_2 = oasysgui.createTabPage(tabs, "Single Lens Input Parameters")

        tab_help = oasysgui.createTabPage(self.tabs_setting, "Help")
        tab_help.setStyleSheet("background-color: white;")

        help_box = oasysgui.widgetBox(tab_help, "", addSpace=True, orientation="horizontal", height=300)

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.help_path).scaledToWidth(self.CONTROL_AREA_WIDTH-20))

        help_box.layout().addWidget(label)

        crl_box = oasysgui.widgetBox(tab_1, "C.R.L. Input Parameters", addSpace=False, orientation="vertical", height=120)

        oasysgui.lineEdit(crl_box, self, "nlenses", "Number of lenses", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(crl_box, self, "slots_empty", "Number of empty slots", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_thickness = oasysgui.lineEdit(crl_box, self, "thickness", "Piling thickness", labelWidth=260, valueType=float, orientation="horizontal")

        lens_box = oasysgui.widgetBox(tab_2, "Single Lens Input Parameters", addSpace=False, orientation="vertical", height=450)

        self.le_p = oasysgui.lineEdit(lens_box, self, "p", "Source Plane Distance to First Interface (P)", labelWidth=290, valueType=float, orientation="horizontal")
        self.le_q = oasysgui.lineEdit(lens_box, self, "q", "Last Interface Distance to Image Plane (Q)"  , labelWidth=290, valueType=float, orientation="horizontal")

        gui.comboBox(lens_box, self, "has_finite_diameter", label="Lens Diameter", labelWidth=260,
                     items=["Finite", "Infinite"], callback=self.set_diameter, sendSelectedValue=False, orientation="horizontal")

        self.diameter_box = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.diameter_box_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        self.le_diameter = oasysgui.lineEdit(self.diameter_box, self, "diameter", "Lens Diameter Value", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_diameter()

        gui.comboBox(lens_box, self, "surface_shape", label="Surface Shape", labelWidth=260,
                     items=["Sphere", "Paraboloid", "Plane"], callback=self.set_surface_shape, sendSelectedValue=False, orientation="horizontal")

        self.surface_shape_box = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.surface_shape_box_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        self.le_radius = oasysgui.lineEdit(self.surface_shape_box, self, "radius", "Curvature Radius", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_surface_shape()

        self.le_interthickness = oasysgui.lineEdit(lens_box, self, "interthickness", "Lens Thickness", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(lens_box, self, "use_ccc", label="Use C.C.C.", labelWidth=310,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=40),
                     self, "convex_to_the_beam", label="Convexity of 1st interface exposed to the\nbeam (2nd interface has opposite convexity)",
                     labelWidth=310,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(lens_box, self, "is_cylinder", label="Cylindrical", labelWidth=310,
                     items=["No", "Yes"], callback=self.set_cylindrical, sendSelectedValue=False, orientation="horizontal")

        self.box_cyl = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.box_cyl_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        gui.comboBox(self.box_cyl, self, "cylinder_angle", label="Cylinder Angle (deg)", labelWidth=260,
                     items=["0 (Meridional)", "90 (Sagittal)"], sendSelectedValue=False, orientation="horizontal")

        self.set_cylindrical()

        gui.comboBox(lens_box, self, "ri_calculation_mode", label="Refraction Index calculation mode", labelWidth=260,
                     items=["User Parameters", "Prerefl File"], callback=self.set_ri_calculation_mode, sendSelectedValue=False, orientation="horizontal")

        self.calculation_mode_1 = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.calculation_mode_1, self, "refraction_index", "Refraction index", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.calculation_mode_1, self, "attenuation_coefficient", "Attenuation coefficient [cm-1]", labelWidth=260, valueType=float, orientation="horizontal")

        self.calculation_mode_2 = oasysgui.widgetBox(lens_box, "", addSpace=True, orientation="vertical")

        file_box = oasysgui.widgetBox(self.calculation_mode_2, "", addSpace=True, orientation="horizontal", height=20)

        self.le_file_prerefl = oasysgui.lineEdit(file_box, self, "prerefl_file", "File Prerefl", labelWidth=100, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectFilePrerefl)

        self.set_ri_calculation_mode()

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def after_change_workspace_units(self):
        label = self.le_thickness.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_p.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_q.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_diameter.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_radius.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_interthickness.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def selectFilePrerefl(self):
        self.le_file_prerefl.setText(oasysgui.selectFileFromDialog(self, self.prerefl_file, "Select File Prerefl", file_extension_filter="Data Files (*.dat)"))

    def get_surface_shape(self):
        if self.surface_shape == 0:
            return 1
        elif self.surface_shape == 1:
            return 4
        elif self.surface_shape == 2:
            return 5
        else:
            raise ValueError("Surface Shape")

    def get_cylinder_angle(self):
        if self.is_cylinder:
            if self.cylinder_angle == 0:
                return 0.0
            elif self.cylinder_angle == 1:
                return 90.0
            else:
                raise ValueError("Cylinder Angle")
        else:
            return None

    def get_diameter(self):
        if self.has_finite_diameter == 0:
            return self.diameter
        else:
            return None

    def get_prerefl_file(self):
        if self.ri_calculation_mode == 1:
            return congruence.checkFileName(self.prerefl_file)
        else:
            return None

    def set_surface_shape(self):
        self.surface_shape_box.setVisible(self.surface_shape != 2)
        self.surface_shape_box_empty.setVisible(self.surface_shape == 2)

    def set_diameter(self):
        self.diameter_box.setVisible(self.has_finite_diameter == 0)
        self.diameter_box_empty.setVisible(self.has_finite_diameter == 1)

    def set_cylindrical(self):
        self.box_cyl.setVisible(self.is_cylinder == 1)
        self.box_cyl_empty.setVisible(self.is_cylinder == 0)

    def set_ri_calculation_mode(self):
        self.calculation_mode_1.setVisible(self.ri_calculation_mode == 0)
        self.calculation_mode_2.setVisible(self.ri_calculation_mode == 1)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def populateFields(self, shadow_oe):
        if self.nlenses > 0:
            shadow_oe._oe.append_crl(p0=self.p,
                                     q0=self.q,
                                     nlenses=self.nlenses,
                                     slots_empty=self.slots_empty,
                                     thickness=self.thickness,
                                     surface_shape=self.get_surface_shape(),
                                     convex_to_the_beam=self.convex_to_the_beam,
                                     diameter=self.get_diameter(),
                                     cylinder_angle=self.get_cylinder_angle(),
                                     prerefl_file=self.get_prerefl_file(),
                                     refraction_index=self.refraction_index,
                                     attenuation_coefficient=self.attenuation_coefficient,
                                     radius=self.radius,
                                     interthickness=self.interthickness,
                                     use_ccc=self.use_ccc)

    def checkFields(self):
        congruence.checkPositiveNumber(self.nlenses, "Number of lenses")
        congruence.checkPositiveNumber(self.slots_empty, "Number of empty slots")
        congruence.checkPositiveNumber(self.thickness, "Piling thickness")

        congruence.checkNumber(self.p, "P")
        congruence.checkNumber(self.q, "Q")

        if self.has_finite_diameter == 0:
            congruence.checkStrictlyPositiveNumber(self.diameter, "Diameter")

        if self.ri_calculation_mode == 1:
            congruence.checkFile(self.prerefl_file)
        else:
            congruence.checkPositiveNumber(self.refraction_index, "Refraction Index")
            congruence.checkPositiveNumber(self.attenuation_coefficient, "Attenuation Coefficient")

        congruence.checkStrictlyPositiveNumber(self.radius, "Radius")
        congruence.checkPositiveNumber(self.interthickness, "Lens Thickness")

    def setPreProcessorData(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                self.prerefl_file = data.prerefl_data_file
                self.ri_calculation_mode = 1

                self.set_ri_calculation_mode()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible Preprocessor Data", QMessageBox.Ok)


    def setupUI(self):
        self.set_surface_shape()
        self.set_diameter()
        self.set_cylindrical()
        self.set_ri_calculation_mode()
