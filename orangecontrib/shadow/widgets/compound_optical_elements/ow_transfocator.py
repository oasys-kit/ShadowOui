import sys, copy

from Orange.widgets import gui
from Orange.widgets.settings import Setting
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui import ow_generic_element
from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerIn, ShadowPreProcessorData, \
    ShadowCompoundOpticalElement, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowGui, ConfirmDialog

class Transfocator(ow_generic_element.GenericElement):
    name = "Transfocator"
    description = "Shadow Compound OE: Transfocator"
    icon = "icons/transfocator.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 2
    category = "Compound Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("PreProcessor Data", ShadowPreProcessorData, "setPreProcessorData")]

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"},
               {"name": "Trigger",
                "type": ShadowTriggerIn,
                "doc": "Feedback signal to start a new beam simulation",
                "id": "Trigger"}]

    input_beam = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    CONTROL_AREA_WIDTH = 500

    # nlenses = [4, 8]
    # slots_empty = [0, 0]
    # thickness = [625e-4, 625e-4]
    #
    # p = [0.0, 0.0]
    # q = [0.0, 0.0]
    # surface_shape = [1, 1]
    # convex_to_the_beam = [1, 1]
    #
    # has_finite_diameter = [0, 0]
    # diameter = [0.0, 0.0]
    #
    # is_cylinder = [1, 1]
    # cylinder_angle = [0.0, 0.0]
    #
    # ri_calculation_mode = [0, 0]
    # prerefl_file = [NONE_SPECIFIED, NONE_SPECIFIED]
    # refraction_index = [1.0, 1.0]
    # attenuation_coefficient = [0.0, 0.0]
    #
    # radius = [500e-2, 500e-2]
    # interthickness = [0.001, 0.001]
    #
    # use_ccc = [0, 0]
    #
    # file_to_write_out = 3


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

    file_to_write_out = Setting(3)

    want_main_area = 1

    def __init__(self):
        super().__init__()

        # self.resetSettings()

        #################################
        # FIX A WEIRD BEHAVIOUR AFTER DISPLAY
        # THE WIDGET: PROBABLY ON SIGNAL MANAGER
        self.dumpSettings()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = gui.tabWidget(self.controlArea)
        tabs_setting.setFixedWidth(495)
        tabs_setting.setFixedHeight(750)

        tab_bas = ShadowGui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = ShadowGui.createTabPage(tabs_setting, "Advanced Setting")

        tabs_button_box = ShadowGui.widgetBox(tab_bas, "", addSpace=False, orientation="horizontal")

        gui.separator(tabs_button_box)

        gui.button(tabs_button_box, self, "Insert C.R.L. Before", callback=self.crl_insert_before)
        gui.button(tabs_button_box, self, "Insert C.R.L. After", callback=self.crl_insert_after)
        gui.button(tabs_button_box, self, "Remove C.R.L.", callback=self.crl_remove)

        gui.separator(tabs_button_box)

        self.tab_crls = gui.tabWidget(tab_bas)
        self.crl_box_array = []

        for index in range(len(self.p)):
            tab_crl = ShadowGui.createTabPage(self.tab_crls, "C.R.L. " + str(index + 1))

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

        adv_other_box = ShadowGui.widgetBox(tab_adv, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=310,
                     items=["All", "Mirror", "Image", "None"],
                     sendSelectedValue=False, orientation="horizontal")

        button_box = ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/trace", callback=self.traceOpticalElement)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(100)

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?\n\nWarning: C.R.L. stack will be regenerated"):
            self.resetSettings()

            while self.tab_crls.count() > 0:
                self.tab_crls.removeTab(0)

            self.crl_box_array = []

            for index in range(len(self.p)):
                tab_crl = ShadowGui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
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
            tab_crl = ShadowGui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
            crl_box = CRLBox(transfocator=self, parent=tab_crl)

            self.tab_crls.insertTab(current_index, tab_crl, "TEMP")
            self.crl_box_array.insert(current_index, crl_box)
            self.dumpSettings()

            for index in range(current_index, self.tab_crls.count()):
                self.tab_crls.setTabText(index, "C.R.L " + str(index + 1))

            self.tab_crls.setCurrentIndex(current_index)

    def crl_insert_after(self):
        current_index = self.tab_crls.currentIndex()

        if ConfirmDialog.confirmed(parent=self, message="Confirm Insertion of a new element after " + self.tab_crls.tabText(current_index) + "?"):
            tab_crl = ShadowGui.widgetBox(self.tab_crls, addToLayout=0, margin=4)
            crl_box = CRLBox(transfocator=self, parent=tab_crl)

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
            QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                       "Remove not possible, transfocator needs at least 1 element",
                                       QtGui.QMessageBox.Ok)
        else:
            current_index = self.tab_crls.currentIndex()

            if ConfirmDialog.confirmed(parent=self, message="Confirm Removal of " + self.tab_crls.tabText(current_index) + "?"):
                self.tab_crls.removeTab(current_index)
                self.crl_box_array.pop(current_index)
                self.dumpSettings()

                for index in range(current_index, self.tab_crls.count()):
                    self.tab_crls.setTabText(index, "C.R.L " + str(index + 1))

                self.tab_crls.setCurrentIndex(current_index)

    def get_write_file_options(self):
        write_star_files = 0
        write_mirr_files = 0

        if self.file_to_write_out == 0:
            write_star_files = 1
            write_mirr_files = 1
        elif self.file_to_write_out == 1:
            write_star_files = 1
        elif self.file_to_write_out == 2:
            write_mirr_files = 1

        return write_star_files, write_mirr_files

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

        for index in range(len(self.crl_box_array)):
            surface_shape_out.append(self.crl_box_array[index].get_surface_shape())
            diameter_out.append(self.crl_box_array[index].get_diameter())
            cylinder_angle_out.append(self.crl_box_array[index].get_cylinder_angle())
            prerefl_file_out.append(self.crl_box_array[index].get_prerefl_file())

        shadow_oe.oe.append_transfocator(p0=self.p,
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



    def doSpecificSetting(self, shadow_oe):
        pass

    def checkFields(self):
        for index in range(len(self.crl_box_array)):
            self.crl_box_array[index].checkFields()

    def completeOperations(self, shadow_oe=None):
        self.setStatusMessage("Running SHADOW")

        if self.trace_shadow:
            grabber = TTYGrabber()
            grabber.start()

        self.progressBarSet(50)

        ###########################################
        # TODO: TO BE ADDED JUST IN CASE OF BROKEN
        #       ENVIRONMENT: MUST BE FOUND A PROPER WAY
        #       TO TEST SHADOW
        self.fixWeirdShadowBug()
        ###########################################

        write_star_files, write_mirr_files = self.get_write_file_options()

        beam_out = ShadowBeam.traceFromCompoundOE(self.input_beam,
                                                  shadow_oe,
                                                  write_star_files=write_star_files,
                                                  write_mirr_files=write_mirr_files)

        if self.trace_shadow:
            grabber.stop()

            for row in grabber.ttyData:
                self.writeStdOut(row)

        self.setStatusMessage("Plotting Results")

        self.plot_results(beam_out)

        self.setStatusMessage("")

        self.send("Beam", beam_out)
        self.send("Trigger", ShadowTriggerIn(new_beam=True))

    def traceOpticalElement(self):
        try:
            self.error(self.error_id)
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowGui.checkEmptyBeam(self.input_beam):
                if ShadowGui.checkGoodBeam(self.input_beam):
                    sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                    self.checkFields()

                    shadow_oe = ShadowCompoundOpticalElement.create_compound_oe()

                    self.populateFields(shadow_oe)

                    self.doSpecificSetting(shadow_oe)

                    self.progressBarSet(10)

                    self.completeOperations(shadow_oe)
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                       str(exception),
                                       QtGui.QMessageBox.Ok)

            self.error_id = self.error_id + 1
            self.error(self.error_id, "Exception occurred: " + str(exception))

        self.progressBarFinished()

    def setBeam(self, beam):
        self.onReceivingInput()

        if ShadowGui.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.traceOpticalElement()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                for index in range(len(self.crl_box_array)):
                    self.crl_box_array[index].prerefl_file = data.prerefl_data_file
                    self.crl_box_array[index].le_prerefl_file.setText(data.prerefl_data_file)

                self.dump_prerefl_file()

    def setupUI(self):
        for index in range(len(self.crl_box_array)):
            self.crl_box_array[index].setupUI()


class CRLBox(QtGui.QWidget):
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

        self.setLayout(QtGui.QVBoxLayout())
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

        crl_box = ShadowGui.widgetBox(self, "C.R.L. Input Parameters", addSpace=False, orientation="vertical", height=100, width=460)

        ShadowGui.lineEdit(crl_box, self, "nlenses", "Number of lenses", labelWidth=350, valueType=int, orientation="horizontal", callback=self.transfocator.dump_nlenses)
        ShadowGui.lineEdit(crl_box, self, "slots_empty", "Number of empty slots", labelWidth=350, valueType=int, orientation="horizontal",
                           callback=self.transfocator.dump_slots_empty)
        ShadowGui.lineEdit(crl_box, self, "thickness", "Piling thickness [cm]", labelWidth=350, valueType=float, orientation="horizontal", callback=self.transfocator.dump_thickness)

        lens_box = ShadowGui.widgetBox(self, "Single Lens Input Parameters", addSpace=False, orientation="vertical", height=510, width=460)

        ShadowGui.lineEdit(lens_box, self, "p", "Distance Source-First lens interface (P) [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.transfocator.dump_p)
        ShadowGui.lineEdit(lens_box, self, "q", "Distance Last lens interface-Image plane (Q) [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.transfocator.dump_q)

        gui.separator(lens_box)

        gui.comboBox(lens_box, self, "has_finite_diameter", label="Lens Diameter", labelWidth=350,
                     items=["Finite", "Infinite"], sendSelectedValue=False, orientation="horizontal", callback=self.set_diameter)

        self.diameter_box = ShadowGui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)
        self.diameter_box_empty = ShadowGui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        ShadowGui.lineEdit(self.diameter_box, self, "diameter", "Lens Diameter Value [cm]", labelWidth=350, valueType=float,
                           orientation="horizontal", callback=self.transfocator.dump_diameter)

        self.set_diameter()

        gui.separator(lens_box)

        gui.comboBox(lens_box, self, "surface_shape", label="Surface Shape", labelWidth=350,
                     items=["Sphere", "Paraboloid", "Plane"], sendSelectedValue=False, orientation="horizontal", callback=self.set_surface_shape)

        self.surface_shape_box = ShadowGui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)
        self.surface_shape_box_empty = ShadowGui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        ShadowGui.lineEdit(self.surface_shape_box, self, "radius", "Curvature Radius [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.transfocator.dump_radius)

        self.set_surface_shape()

        ShadowGui.lineEdit(lens_box, self, "interthickness", "Lens Thickness [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.transfocator.dump_interthickness)

        gui.comboBox(lens_box, self, "use_ccc", label="Use C.C.C.", labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.transfocator.dump_use_ccc)

        gui.comboBox(lens_box, self, "convex_to_the_beam", label="Convexity of the first interface exposed to the beam\n(the second interface has opposite convexity)",
                            labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.transfocator.dump_convex_to_the_beam)

        gui.separator(lens_box)

        gui.comboBox(lens_box, self, "is_cylinder", label="Cylindrical", labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_cylindrical)

        self.box_cyl = ShadowGui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=25)
        self.box_cyl_empty = ShadowGui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=25)

        gui.comboBox(self.box_cyl, self, "cylinder_angle", label="Cylinder Angle (deg)", labelWidth=350,
                     items=["0 (Meridional)", "90 (Sagittal)"], sendSelectedValue=False, orientation="horizontal", callback=self.transfocator.dump_cylinder_angle)

        self.set_cylindrical()

        gui.separator(lens_box)

        gui.comboBox(lens_box, self, "ri_calculation_mode", label="Refraction Index calculation mode", labelWidth=350,
                     items=["User Parameters", "Prerefl File"], sendSelectedValue=False, orientation="horizontal", callback=self.set_ri_calculation_mode)

        self.calculation_mode_1 = ShadowGui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=50)

        ShadowGui.lineEdit(self.calculation_mode_1, self, "refraction_index", "Refraction index", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.transfocator.dump_refraction_index)
        ShadowGui.lineEdit(self.calculation_mode_1, self, "attenuation_coefficient", "Attenuation coefficient [cm-1]", labelWidth=350, valueType=float,
                           orientation="horizontal", callback=self.transfocator.dump_attenuation_coefficient)

        self.calculation_mode_2 = ShadowGui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=50)

        self.le_prerefl_file = ShadowGui.lineEdit(self.calculation_mode_2, self, "prerefl_file", "File Prerefl", labelWidth=150, valueType=str, orientation="horizontal",
                                                  callback=self.transfocator.dump_prerefl_file)

        self.set_ri_calculation_mode()

        self.is_on_init = False

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

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
        if self.has_finite_diameter:
            return self.diameter
        else:
            return None

    def get_prerefl_file(self):
        if self.ri_calculation_mode == 1:
            return self.prerefl_file
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
        ShadowGui.checkPositiveNumber(self.nlenses, "Number of lenses")
        ShadowGui.checkPositiveNumber(self.slots_empty, "Number of empty slots")
        ShadowGui.checkPositiveNumber(self.thickness, "Piling thickness")

        ShadowGui.checkPositiveNumber(self.p, "P")
        ShadowGui.checkPositiveNumber(self.q, "Q")

        if self.has_finite_diameter:
            ShadowGui.checkStrictlyPositiveNumber(self.diameter, "Diameter")

        if self.ri_calculation_mode == 1:
            ShadowGui.checkFile(self.prerefl_file)
        else:
            ShadowGui.checkStrictlyPositiveNumber(self.refraction_index, "Refraction Index")
            ShadowGui.checkStrictlyPositiveNumber(self.attenuation_coefficient, "Attenuation Coefficient")

        ShadowGui.checkStrictlyPositiveNumber(self.radius, "Radius")
        ShadowGui.checkPositiveNumber(self.interthickness, "Lens Thickness")

    def setupUI(self):
        self.set_surface_shape()
        self.set_diameter()
        self.set_cylindrical()
        self.set_ri_calculation_mode()
