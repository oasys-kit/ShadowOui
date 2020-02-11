import os, copy

from PyQt5.QtWidgets import QWidget, QLabel, QMessageBox, QSizePolicy, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

import orangecanvas.resources as resources
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData
from orangecontrib.shadow.widgets.gui import ow_compound_optical_element

class Transfocator(ow_compound_optical_element.CompoundOpticalElement):
    name = "Transfocator"
    description = "Shadow Compound OE: Transfocator"
    icon = "icons/transfocator.png"
    priority = 2

    NONE_SPECIFIED = "NONE SPECIFIED"

    nlenses = Setting([4, 8])
    slots_empty = Setting([0, 0])
    thickness = Setting([625e-4, 625e-4])

    p = Setting([0.0, 0.0])
    q = Setting([0.0, 0.0])
    surface_shape = Setting([1, 1])
    convex_to_the_beam = Setting([1, 1])

    has_finite_diameter = Setting([0, 0])
    diameter = Setting([0.0, 0.0])

    is_cylinder = Setting([1, 1])
    cylinder_angle = Setting([0.0, 0.0])

    ri_calculation_mode = Setting([0, 0])
    prerefl_file = Setting([NONE_SPECIFIED, NONE_SPECIFIED])
    refraction_index = Setting([1.0, 1.0])
    attenuation_coefficient = Setting([0.0, 0.0])

    radius = Setting([500e-2, 500e-2])
    interthickness = Setting([0.001, 0.001])

    use_ccc = Setting([0, 0])

    help_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "crl_help.png")

    def __init__(self):
        super().__init__()

        tab_help = oasysgui.createTabPage(self.tabs_setting, "Help")
        tab_help.setStyleSheet("background-color: white;")

        help_box = oasysgui.widgetBox(tab_help, "", addSpace=True, orientation="horizontal", height=300)

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.help_path).scaledToWidth(self.CONTROL_AREA_WIDTH-20))

        help_box.layout().addWidget(label)

        tabs_button_box = oasysgui.widgetBox(self.tab_bas, "", addSpace=False, orientation="horizontal")

        btns = [gui.button(tabs_button_box, self, "Insert C.R.L. Before", callback=self.crl_insert_before),
                gui.button(tabs_button_box, self, "Insert C.R.L. After", callback=self.crl_insert_after),
                gui.button(tabs_button_box, self, "Remove C.R.L.", callback=self.crl_remove)]

        for btn in btns:
            btn.setFixedHeight(40)

        self.tab_crls = oasysgui.tabWidget(self.tab_bas)
        self.crl_box_array = []

        for index in range(len(self.p)):
            tab_crl = oasysgui.createTabPage(self.tab_crls, "C.R.L. " + str(index + 1))

            crl_box = CRLBox(transfocator=self,
                             parent=tab_crl,
                             nlenses=self.nlenses[index],
                             slots_empty=self.slots_empty[index],
                             thickness=self.thickness[index],
                             p=self.p[index],
                             q=self.q[index],
                             surface_shape=self.surface_shape[index],
                             convex_to_the_beam=self.convex_to_the_beam[index],
                             has_finite_diameter=self.has_finite_diameter[index],
                             diameter=self.diameter[index],
                             is_cylinder=self.is_cylinder[index],
                             cylinder_angle=self.cylinder_angle[index],
                             ri_calculation_mode=self.ri_calculation_mode[index],
                             prerefl_file=self.prerefl_file[index],
                             refraction_index=self.refraction_index[index],
                             attenuation_coefficient=self.attenuation_coefficient[index],
                             radius=self.radius[index],
                             interthickness=self.interthickness[index],
                             use_ccc=self.use_ccc[index])

            self.crl_box_array.append(crl_box)

    def after_change_workspace_units(self):
        for box in self.crl_box_array:
            box.after_change_workspace_units()

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?\n\nWarning: C.R.L. stack will be regenerated"):
            self.resetSettings()

            while self.tab_crls.count() > 0:
                self.tab_crls.removeTab(0)

            self.crl_box_array = []

            for index in range(len(self.p)):
                tab_crl = oasysgui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
                crl_box = CRLBox(transfocator=self,
                                 parent=tab_crl,
                                 nlenses=self.nlenses[index],
                                 slots_empty=self.slots_empty[index],
                                 thickness=self.thickness[index],
                                 p=self.p[index],
                                 q=self.q[index],
                                 surface_shape=self.surface_shape[index],
                                 convex_to_the_beam=self.convex_to_the_beam[index],
                                 has_finite_diameter=self.has_finite_diameter[index],
                                 diameter=self.diameter[index],
                                 is_cylinder=self.is_cylinder[index],
                                 cylinder_angle=self.cylinder_angle[index],
                                 ri_calculation_mode=self.ri_calculation_mode[index],
                                 prerefl_file=self.prerefl_file[index],
                                 refraction_index=self.refraction_index[index],
                                 attenuation_coefficient=self.attenuation_coefficient[index],
                                 radius=self.radius[index],
                                 interthickness=self.interthickness[index],
                                 use_ccc=self.use_ccc[index])

                self.tab_crls.addTab(tab_crl, "C.R.L " + str(index + 1))
                self.crl_box_array.append(crl_box)

            self.setupUI()


    def crl_insert_before(self):
        current_index = self.tab_crls.currentIndex()

        if ConfirmDialog.confirmed(parent=self, message="Confirm Insertion of a new element before " + self.tab_crls.tabText(current_index) + "?"):
            tab_crl = oasysgui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
            crl_box = CRLBox(transfocator=self, parent=tab_crl)
            crl_box.after_change_workspace_units()

            self.tab_crls.insertTab(current_index, tab_crl, "TEMP")
            self.crl_box_array.insert(current_index, crl_box)
            self.dumpSettings()

            for index in range(current_index, self.tab_crls.count()):
                self.tab_crls.setTabText(index, "C.R.L " + str(index + 1))

            self.tab_crls.setCurrentIndex(current_index)

    def crl_insert_after(self):
        current_index = self.tab_crls.currentIndex()

        if ConfirmDialog.confirmed(parent=self, message="Confirm Insertion of a new element after " + self.tab_crls.tabText(current_index) + "?"):
            tab_crl = oasysgui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
            crl_box = CRLBox(transfocator=self, parent=tab_crl)
            crl_box.after_change_workspace_units()

            if current_index == self.tab_crls.count() - 1:  # LAST
                self.tab_crls.addTab(tab_crl, "TEMP")
                self.crl_box_array.append(crl_box)
            else:
                self.tab_crls.insertTab(current_index + 1, tab_crl, "TEMP")
                self.crl_box_array.insert(current_index + 1, crl_box)

            self.dumpSettings()

            for index in range(current_index, self.tab_crls.count()):
                self.tab_crls.setTabText(index, "C.R.L " + str(index + 1))

            self.tab_crls.setCurrentIndex(current_index + 1)

    def crl_remove(self):
        if self.tab_crls.count() <= 1:
            QMessageBox.critical(self, "Error",
                                       "Remove not possible, transfocator needs at least 1 element",
                                       QMessageBox.Ok)
        else:
            current_index = self.tab_crls.currentIndex()

            if ConfirmDialog.confirmed(parent=self, message="Confirm Removal of " + self.tab_crls.tabText(current_index) + "?"):
                self.tab_crls.removeTab(current_index)
                self.crl_box_array.pop(current_index)
                self.dumpSettings()

                for index in range(current_index, self.tab_crls.count()):
                    self.tab_crls.setTabText(index, "C.R.L " + str(index + 1))

                self.tab_crls.setCurrentIndex(current_index)

    def dumpSettings(self):
        bkp_nlenses = copy.deepcopy(self.nlenses)
        bkp_slots_empty = copy.deepcopy(self.slots_empty)
        bkp_thickness = copy.deepcopy(self.thickness)
        bkp_p = copy.deepcopy(self.p)
        bkp_q = copy.deepcopy(self.q)
        bkp_surface_shape = copy.deepcopy(self.surface_shape)
        bkp_convex_to_the_beam = copy.deepcopy(self.convex_to_the_beam)
        bkp_has_finite_diameter = copy.deepcopy(self.has_finite_diameter)
        bkp_diameter = copy.deepcopy(self.diameter)
        bkp_is_cylinder = copy.deepcopy(self.is_cylinder)
        bkp_cylinder_angle = copy.deepcopy(self.cylinder_angle)
        bkp_ri_calculation_mode = copy.deepcopy(self.ri_calculation_mode)
        bkp_prerefl_file = copy.deepcopy(self.prerefl_file)
        bkp_refraction_index = copy.deepcopy(self.refraction_index)
        bkp_attenuation_coefficient = copy.deepcopy(self.attenuation_coefficient)
        bkp_radius = copy.deepcopy(self.radius)
        bkp_interthickness = copy.deepcopy(self.interthickness)
        bkp_use_ccc = copy.deepcopy(self.use_ccc)

        try:
            self.nlenses = []
            self.slots_empty = []
            self.thickness = []
            self.p = []
            self.q = []
            self.surface_shape = []
            self.convex_to_the_beam = []
            self.has_finite_diameter = []
            self.diameter = []
            self.is_cylinder = []
            self.cylinder_angle = []
            self.ri_calculation_mode = []
            self.prerefl_file = []
            self.refraction_index = []
            self.attenuation_coefficient = []
            self.radius = []
            self.interthickness = []
            self.use_ccc = []

            for index in range(len(self.crl_box_array)):
                self.nlenses.append(self.crl_box_array[index].nlenses)
                self.slots_empty.append(self.crl_box_array[index].slots_empty)
                self.thickness.append(self.crl_box_array[index].thickness)
                self.p.append(self.crl_box_array[index].p)
                self.q.append(self.crl_box_array[index].q)
                self.surface_shape.append(self.crl_box_array[index].surface_shape)
                self.convex_to_the_beam.append(self.crl_box_array[index].convex_to_the_beam)
                self.has_finite_diameter.append(self.crl_box_array[index].has_finite_diameter)
                self.diameter.append(self.crl_box_array[index].diameter)
                self.is_cylinder.append(self.crl_box_array[index].is_cylinder)
                self.cylinder_angle.append(self.crl_box_array[index].cylinder_angle)
                self.ri_calculation_mode.append(self.crl_box_array[index].ri_calculation_mode)
                self.prerefl_file.append(self.crl_box_array[index].prerefl_file)
                self.refraction_index.append(self.crl_box_array[index].refraction_index)
                self.attenuation_coefficient.append(self.crl_box_array[index].attenuation_coefficient)
                self.radius.append(self.crl_box_array[index].radius)
                self.interthickness.append(self.crl_box_array[index].interthickness)
                self.use_ccc.append(self.crl_box_array[index].use_ccc)
        except:
            self.nlenses = copy.deepcopy(bkp_nlenses)
            self.slots_empty = copy.deepcopy(bkp_slots_empty)
            self.thickness = copy.deepcopy(bkp_thickness)
            self.p = copy.deepcopy(bkp_p)
            self.q = copy.deepcopy(bkp_q)
            self.surface_shape = copy.deepcopy(bkp_surface_shape)
            self.convex_to_the_beam = copy.deepcopy(bkp_convex_to_the_beam)
            self.has_finite_diameter = copy.deepcopy(bkp_has_finite_diameter)
            self.diameter = copy.deepcopy(bkp_diameter)
            self.is_cylinder = copy.deepcopy(bkp_is_cylinder)
            self.cylinder_angle = copy.deepcopy(bkp_cylinder_angle)
            self.ri_calculation_mode = copy.deepcopy(bkp_ri_calculation_mode)
            self.prerefl_file = copy.deepcopy(bkp_prerefl_file)
            self.refraction_index = copy.deepcopy(bkp_refraction_index)
            self.attenuation_coefficient = copy.deepcopy(bkp_attenuation_coefficient)
            self.radius = copy.deepcopy(bkp_radius)
            self.interthickness = copy.deepcopy(bkp_interthickness)
            self.use_ccc = copy.deepcopy(bkp_use_ccc)



    ##############################
    # SINGLE FIELDS SIGNALS
    ##############################

    def dump_nlenses(self):
        bkp_nlenses = copy.deepcopy(self.nlenses)

        try:
            self.nlenses = []

            for index in range(len(self.crl_box_array)):
                self.nlenses.append(self.crl_box_array[index].nlenses)
        except:
            self.nlenses = copy.deepcopy(bkp_nlenses)

    def dump_slots_empty(self):
        bkp_slots_empty = copy.deepcopy(self.slots_empty)

        try:
            self.slots_empty = []

            for index in range(len(self.crl_box_array)):
                self.slots_empty.append(self.crl_box_array[index].slots_empty)
        except:
            self.slots_empty = copy.deepcopy(bkp_slots_empty)

    def dump_thickness(self):
        bkp_thickness = copy.deepcopy(self.thickness)

        try:
            self.thickness = []

            for index in range(len(self.crl_box_array)):
                self.thickness.append(self.crl_box_array[index].thickness)
        except:
            self.thickness = copy.deepcopy(bkp_thickness)

    def dump_p(self):
        bkp_p = copy.deepcopy(self.p)

        try:
            self.p = []

            for index in range(len(self.crl_box_array)):
                self.p.append(self.crl_box_array[index].p)
        except:
            self.p = copy.deepcopy(bkp_p)

    def dump_q(self):
        bkp_q = copy.deepcopy(self.q)

        try:
            self.q = []

            for index in range(len(self.crl_box_array)):
                self.q.append(self.crl_box_array[index].q)
        except:
            self.q = copy.deepcopy(bkp_q)

    def dump_surface_shape(self):
        bkp_surface_shape = copy.deepcopy(self.surface_shape)

        try:
            self.surface_shape = []

            for index in range(len(self.crl_box_array)):
                self.surface_shape.append(self.crl_box_array[index].surface_shape)
        except:
            self.surface_shape = copy.deepcopy(bkp_surface_shape)

    def dump_convex_to_the_beam(self):
        bkp_convex_to_the_beam = copy.deepcopy(self.convex_to_the_beam)

        try:
            self.convex_to_the_beam = []

            for index in range(len(self.crl_box_array)):
                self.convex_to_the_beam.append(self.crl_box_array[index].convex_to_the_beam)
        except:
            self.convex_to_the_beam = copy.deepcopy(bkp_convex_to_the_beam)

    def dump_has_finite_diameter(self):
        bkp_has_finite_diameter = copy.deepcopy(self.has_finite_diameter)

        try:
            self.has_finite_diameter = []

            for index in range(len(self.crl_box_array)):
                self.has_finite_diameter.append(self.crl_box_array[index].has_finite_diameter)
        except:
            self.has_finite_diameter = copy.deepcopy(bkp_has_finite_diameter)

    def dump_diameter(self):
        bkp_diameter = copy.deepcopy(self.diameter)

        try:
            self.diameter = []

            for index in range(len(self.crl_box_array)):
                self.diameter.append(self.crl_box_array[index].diameter)
        except:
            self.diameter = copy.deepcopy(bkp_diameter)

    def dump_is_cylinder(self):
        bkp_is_cylinder = copy.deepcopy(self.is_cylinder)

        try:
            self.is_cylinder = []

            for index in range(len(self.crl_box_array)):
                self.is_cylinder.append(self.crl_box_array[index].is_cylinder)
        except:
            self.is_cylinder = copy.deepcopy(bkp_is_cylinder)

    def dump_cylinder_angle(self):
        bkp_cylinder_angle = copy.deepcopy(self.cylinder_angle)

        try:
            self.cylinder_angle = []

            for index in range(len(self.crl_box_array)):
                self.cylinder_angle.append(self.crl_box_array[index].cylinder_angle)
        except:
            self.cylinder_angle = copy.deepcopy(bkp_cylinder_angle)

    def dump_ri_calculation_mode(self):
        bkp_ri_calculation_mode = copy.deepcopy(self.ri_calculation_mode)

        try:
            self.ri_calculation_mode = []

            for index in range(len(self.crl_box_array)):
                self.ri_calculation_mode.append(self.crl_box_array[index].ri_calculation_mode)
        except:
            self.ri_calculation_mode = copy.deepcopy(bkp_ri_calculation_mode)

    def dump_prerefl_file(self):
        bkp_prerefl_file = copy.deepcopy(self.prerefl_file)

        try:
            self.prerefl_file = []

            for index in range(len(self.crl_box_array)):
                self.prerefl_file.append(self.crl_box_array[index].prerefl_file)
        except:
            self.prerefl_file = copy.deepcopy(bkp_prerefl_file)

    def dump_refraction_index(self):
        bkp_refraction_index = copy.deepcopy(self.refraction_index)

        try:
            self.refraction_index = []

            for index in range(len(self.crl_box_array)):
                self.refraction_index.append(self.crl_box_array[index].refraction_index)
        except:
            self.refraction_index = copy.deepcopy(bkp_refraction_index)

    def dump_attenuation_coefficient(self):
        bkp_attenuation_coefficient = copy.deepcopy(self.attenuation_coefficient)

        try:
            self.attenuation_coefficient = []

            for index in range(len(self.crl_box_array)):
                self.attenuation_coefficient.append(self.crl_box_array[index].attenuation_coefficient)
        except:
            self.attenuation_coefficient = copy.deepcopy(bkp_attenuation_coefficient)

    def dump_radius(self):
        bkp_radius = copy.deepcopy(self.radius)

        try:
            self.radius = []

            for index in range(len(self.crl_box_array)):
                self.radius.append(self.crl_box_array[index].radius)
        except:
            self.radius = copy.deepcopy(bkp_radius)

    def dump_interthickness(self):
        bkp_interthickness = copy.deepcopy(self.interthickness)

        try:
            self.interthickness = []

            for index in range(len(self.crl_box_array)):
                self.interthickness.append(self.crl_box_array[index].interthickness)
        except:
            self.interthickness = copy.deepcopy(bkp_interthickness)

    def dump_use_ccc(self):
        bkp_use_ccc = copy.deepcopy(self.use_ccc)

        try:
            self.use_ccc = []

            for index in range(len(self.crl_box_array)):
                self.use_ccc.append(self.crl_box_array[index].use_ccc)
        except:
            self.use_ccc = copy.deepcopy(bkp_use_ccc)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################


    def populateFields(self, shadow_oe):
        self.dumpSettings()

        surface_shape_out = []
        diameter_out = []
        cylinder_angle_out = []
        prerefl_file_out = []

        for box in self.crl_box_array:
            surface_shape_out.append(box.get_surface_shape())
            diameter_out.append(box.get_diameter())
            cylinder_angle_out.append(box.get_cylinder_angle())
            prerefl_file_out.append(box.get_prerefl_file())

        shadow_oe._oe.append_transfocator(p0=self.p,
                                         q0=self.q,
                                         nlenses=self.nlenses,
                                         slots_empty=self.slots_empty,
                                         thickness=self.thickness,
                                         surface_shape=surface_shape_out,
                                         convex_to_the_beam=self.convex_to_the_beam,
                                         diameter=diameter_out,
                                         cylinder_angle=cylinder_angle_out,
                                         prerefl_file=prerefl_file_out,
                                         refraction_index=self.refraction_index,
                                         attenuation_coefficient=self.attenuation_coefficient,
                                         radius=self.radius,
                                         interthickness=self.interthickness,
                                         use_ccc=self.use_ccc)

    def checkFields(self):
        for box in self.crl_box_array:
            box.checkFields()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                for box in self.crl_box_array:
                    box.prerefl_file = data.prerefl_data_file
                    box.le_prerefl_file.setText(data.prerefl_data_file)
                    box.ri_calculation_mode = 1
                    box.ri_calculation_mode_combo.setCurrentIndex(1)

                    box.set_ri_calculation_mode()
            else:
                QMessageBox.warning(self, "Warning", "Incompatible Preprocessor Data", QMessageBox.Ok)

                self.dump_prerefl_file()

    def setupUI(self):
        for box in self.crl_box_array:
            box.setupUI()


class CRLBox(QWidget):
    nlenses = 30
    slots_empty = 0
    thickness = 625e-4

    p = 0.0
    q = 0.0
    surface_shape = 1
    convex_to_the_beam = 1

    has_finite_diameter = 0
    diameter = 0.0

    is_cylinder = 1
    cylinder_angle = 0.0

    ri_calculation_mode = 0
    prerefl_file = Transfocator.NONE_SPECIFIED
    refraction_index = 1.0
    attenuation_coefficient = 0.0

    radius = 500e-2
    interthickness = 0.001

    use_ccc = 0

    transfocator = None

    is_on_init = True

    def __init__(self,
                 transfocator=None,
                 parent=None,
                 nlenses=30,
                 slots_empty=0,
                 thickness=625e-4,
                 p=0.0,
                 q=0.0,
                 surface_shape=1,
                 convex_to_the_beam=1,
                 has_finite_diameter=0,
                 diameter=0.0,
                 is_cylinder=1,
                 cylinder_angle=0.0,
                 ri_calculation_mode=0,
                 prerefl_file=Transfocator.NONE_SPECIFIED,
                 refraction_index=1.0,
                 attenuation_coefficient=0.0,
                 radius=500e-2,
                 interthickness=0.001,
                 use_ccc=0):
        super().__init__(parent)

        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self.setFixedWidth(470)
        self.setFixedHeight(700)

        self.transfocator = transfocator

        self.nlenses = nlenses
        self.slots_empty = slots_empty
        self.thickness = thickness
        self.p = p
        self.q = q
        self.surface_shape = surface_shape
        self.convex_to_the_beam = convex_to_the_beam
        self.has_finite_diameter = has_finite_diameter
        self.diameter = diameter
        self.is_cylinder = is_cylinder
        self.cylinder_angle = cylinder_angle
        self.ri_calculation_mode = ri_calculation_mode
        self.prerefl_file = prerefl_file
        self.refraction_index = refraction_index
        self.attenuation_coefficient = attenuation_coefficient
        self.radius = radius
        self.interthickness = interthickness
        self.use_ccc = use_ccc

        tabs = oasysgui.tabWidget(self, height=420, width=self.transfocator.CONTROL_AREA_WIDTH-35)
        tab_1 = oasysgui.createTabPage(tabs, "C.R.L. Input Parameters")
        tab_2 = oasysgui.createTabPage(tabs, "Single Lens Input Parameters")

        crl_box = oasysgui.widgetBox(tab_1, "C.R.L. Input Parameters", addSpace=False, orientation="vertical", height=120, width=self.transfocator.CONTROL_AREA_WIDTH-45)

        oasysgui.lineEdit(crl_box, self, "nlenses", "Number of lenses", labelWidth=260, valueType=int, orientation="horizontal", callback=self.transfocator.dump_nlenses)
        oasysgui.lineEdit(crl_box, self, "slots_empty", "Number of empty slots", labelWidth=260, valueType=int, orientation="horizontal",
                           callback=self.transfocator.dump_slots_empty)
        self.le_thickness = oasysgui.lineEdit(crl_box, self, "thickness", "Piling thickness", labelWidth=260, valueType=float, orientation="horizontal", callback=self.transfocator.dump_thickness)

        lens_box = oasysgui.widgetBox(tab_2, "Single Lens Input Parameters", addSpace=False, orientation="vertical", height=380, width=self.transfocator.CONTROL_AREA_WIDTH-45)

        self.le_p = oasysgui.lineEdit(lens_box, self, "p", "Source Plane Distance to First Interface (P)", labelWidth=290, valueType=float, orientation="horizontal",
                                      callback=self.transfocator.dump_p)
        self.le_q = oasysgui.lineEdit(lens_box, self, "q", "Last Interface distance to Image plane (Q)"  , labelWidth=290, valueType=float, orientation="horizontal",
                                      callback=self.transfocator.dump_q)

        diameter_box_outer = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="horizontal")

        gui.comboBox(diameter_box_outer, self, "has_finite_diameter", label="Lens Diameter", labelWidth=110, #labelWidth=260,
                     items=["Finite", "Infinite"], sendSelectedValue=False, orientation="horizontal", callback=self.set_diameter)

        self.diameter_box = oasysgui.widgetBox(diameter_box_outer, "", addSpace=False, orientation="vertical")
        self.diameter_box_empty = oasysgui.widgetBox(diameter_box_outer, "", addSpace=False, orientation="vertical", height=20)

        self.le_diameter = oasysgui.lineEdit(self.diameter_box, self, "diameter", " Value", labelWidth=110, #labelWidth=260,
                                             valueType=float, orientation="horizontal", callback=self.transfocator.dump_diameter)

        self.set_diameter()

        surface_shape_box_outer = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="horizontal")

        gui.comboBox(surface_shape_box_outer, self, "surface_shape", label="Surface Shape", #labelWidth=260,
                     items=["Sphere", "Paraboloid", "Plane"], sendSelectedValue=False, orientation="horizontal", callback=self.set_surface_shape)

        self.surface_shape_box = oasysgui.widgetBox(surface_shape_box_outer, "", addSpace=False, orientation="vertical")
        self.surface_shape_box_empty = oasysgui.widgetBox(surface_shape_box_outer, "", addSpace=False, orientation="vertical")

        self.le_radius = oasysgui.lineEdit(self.surface_shape_box, self, "radius", " Curv. Radius", labelWidth=110, #labelWidth=260,
                                           valueType=float, orientation="horizontal", callback=self.transfocator.dump_radius)

        self.set_surface_shape()

        self.le_interthickness = oasysgui.lineEdit(lens_box, self, "interthickness", "Lens Thickness", labelWidth=260,
                                                   valueType=float, orientation="horizontal", callback=self.transfocator.dump_interthickness)

        gui.comboBox(lens_box, self, "use_ccc", label="Use C.C.C.", labelWidth=310,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.transfocator.dump_use_ccc)

        gui.comboBox(oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=40),
                     self, "convex_to_the_beam", label="Convexity of the 1st interface exposed to the\nbeam (the 2nd interface has opposite convexity)",
                            labelWidth=310,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.transfocator.dump_convex_to_the_beam)


        gui.comboBox(lens_box, self, "is_cylinder", label="Cylindrical", labelWidth=310,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_cylindrical)

        self.box_cyl = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")
        self.box_cyl_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        gui.comboBox(self.box_cyl, self, "cylinder_angle", label="Cylinder Angle (deg)", labelWidth=260,
                     items=["0 (Meridional)", "90 (Sagittal)"], sendSelectedValue=False, orientation="horizontal", callback=self.transfocator.dump_cylinder_angle)

        self.set_cylindrical()

        self.ri_calculation_mode_combo = gui.comboBox(lens_box, self, "ri_calculation_mode",
                                                      label="Refraction Index calculation mode", labelWidth=260,
                                                      items=["User Parameters", "Prerefl File"],
                                                      sendSelectedValue=False, orientation="horizontal",
                                                      callback=self.set_ri_calculation_mode)

        self.calculation_mode_1 = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.calculation_mode_1, self, "refraction_index", "Refraction index", labelWidth=260, valueType=float, orientation="horizontal",
                           callback=self.transfocator.dump_refraction_index)
        self.le_attenuation_coefficient = oasysgui.lineEdit(self.calculation_mode_1, self, "attenuation_coefficient", "Attenuation coefficient", labelWidth=260, valueType=float,
                           orientation="horizontal", callback=self.transfocator.dump_attenuation_coefficient)

        self.calculation_mode_2 = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.calculation_mode_2, "", addSpace=False, orientation="horizontal", height=20)

        self.le_prerefl_file = oasysgui.lineEdit(file_box, self, "prerefl_file", "File Prerefl", labelWidth=100, valueType=str, orientation="horizontal",
                                                  callback=self.transfocator.dump_prerefl_file)

        gui.button(file_box, self, "...", callback=self.selectFilePrerefl)

        self.set_ri_calculation_mode()

        self.is_on_init = False

    def after_change_workspace_units(self):
        label = self.le_thickness.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.transfocator.workspace_units_label + "]")
        label = self.le_p.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.transfocator.workspace_units_label + "]")
        label = self.le_q.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.transfocator.workspace_units_label + "]")
        label = self.le_diameter.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.transfocator.workspace_units_label + "]")
        label = self.le_radius.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.transfocator.workspace_units_label + "]")
        label = self.le_interthickness.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.transfocator.workspace_units_label + "]")
        label = self.le_attenuation_coefficient.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.transfocator.workspace_units_label + "-1]")

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def selectFilePrerefl(self):
        self.le_prerefl_file.setText(oasysgui.selectFileFromDialog(self, self.prerefl_file, "Select File Prerefl", file_extension_filter="Data Files (*.dat)"))

        self.prerefl_file = self.le_prerefl_file.text()
        self.transfocator.dump_prerefl_file()

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

        if not self.is_on_init: self.transfocator.dump_surface_shape()

    def set_diameter(self):
        self.diameter_box.setVisible(self.has_finite_diameter == 0)
        self.diameter_box_empty.setVisible(self.has_finite_diameter == 1)

        if not self.is_on_init: self.transfocator.dump_has_finite_diameter()

    def set_cylindrical(self):
        self.box_cyl.setVisible(self.is_cylinder == 1)
        self.box_cyl_empty.setVisible(self.is_cylinder == 0)
        if not self.is_on_init: self.transfocator.dump_is_cylinder()

    def set_ri_calculation_mode(self):
        self.calculation_mode_1.setVisible(self.ri_calculation_mode == 0)
        self.calculation_mode_2.setVisible(self.ri_calculation_mode == 1)

        if not self.is_on_init: self.transfocator.dump_ri_calculation_mode()

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

    def setupUI(self):
        self.set_surface_shape()
        self.set_diameter()
        self.set_cylindrical()
        self.set_ri_calculation_mode()
