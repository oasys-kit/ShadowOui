import sys

from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerIn, ShadowPreProcessorData, \
    ShadowCompoundOpticalElement, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from orangecontrib.shadow.widgets.gui import ow_generic_element

class Lens(ow_generic_element.GenericElement):
    name = "Lens"
    description = "Shadow Compound OE: Lens"
    icon = "icons/lens.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
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

    CONTROL_AREA_HEIGHT = 440
    CONTROL_AREA_WIDTH = 500

    p = Setting(0.0)
    q = Setting(0.0)
    surface_shape = Setting(1)
    convex_to_the_beam = Setting(1)

    has_finite_diameter = Setting(0)
    diameter = Setting(0.0)

    is_cylinder = Setting(1)
    cylinder_angle = Setting(0.0)

    ri_calculation_mode = Setting(0)
    prerefl_file = Setting(NONE_SPECIFIED)
    refraction_index = Setting(1.0)
    attenuation_coefficient = Setting(0.0)

    radius = Setting(500e-2)
    interthickness = Setting(0.001)

    use_ccc = Setting(0)

    file_to_write_out = Setting(3)

    want_main_area = 1

    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = gui.tabWidget(self.controlArea)
        tabs_setting.setFixedWidth(495)
        #tabs_setting.setFixedHeight(650)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        lens_box = oasysgui.widgetBox(tab_bas, "Input Parameters", addSpace=False, orientation="vertical", height=600, width=480)

        oasysgui.lineEdit(lens_box, self, "p", "Distance Source-First lens interface (P) [cm]", labelWidth=350, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(lens_box, self, "q", "Distance Last lens interface-Image plane (Q) [cm]", labelWidth=350, valueType=float, orientation="horizontal")

        gui.comboBox(lens_box, self, "has_finite_diameter", label="Lens Diameter", labelWidth=350,
                     items=["Finite", "Infinite"], callback=self.set_diameter, sendSelectedValue=False, orientation="horizontal")

        self.diameter_box = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)
        self.diameter_box_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        oasysgui.lineEdit(self.diameter_box, self, "diameter", "Lens Diameter Value [cm]", labelWidth=350, valueType=float, orientation="horizontal")

        self.set_diameter()

        gui.separator(lens_box)

        gui.comboBox(lens_box, self, "surface_shape", label="Surface Shape", labelWidth=350,
                     items=["Sphere", "Paraboloid", "Plane"], callback=self.set_surface_shape, sendSelectedValue=False, orientation="horizontal")

        self.surface_shape_box = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)
        self.surface_shape_box_empty = oasysgui.widgetBox(lens_box, "", addSpace=False, orientation="vertical", height=20)

        oasysgui.lineEdit(self.surface_shape_box, self, "radius", "Curvature Radius [cm]", labelWidth=350, valueType=float, orientation="horizontal")

        self.set_surface_shape()

        oasysgui.lineEdit(lens_box, self, "interthickness", "Lens Thickness [cm]", labelWidth=350, valueType=float, orientation="horizontal")

        gui.comboBox(lens_box, self, "use_ccc", label="Use C.C.C.", labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(lens_box, self, "convex_to_the_beam", label="Convexity of the first interface exposed to the beam\n(the second interface has opposite convexity)",
                     labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.separator(lens_box)

        gui.comboBox(lens_box, self, "is_cylinder", label="Cylindrical", labelWidth=350,
                     items=["No", "Yes"], callback=self.set_cylindrical, sendSelectedValue=False, orientation="horizontal")

        self.box_cyl = oasysgui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=25)
        self.box_cyl_empty = oasysgui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=25)

        gui.comboBox(self.box_cyl, self, "cylinder_angle", label="Cylinder Angle (deg)", labelWidth=350,
                     items=["0 (Meridional)", "90 (Sagittal)"], sendSelectedValue=False, orientation="horizontal")

        self.set_cylindrical()

        gui.separator(lens_box)

        self.ri_calculation_mode_combo = gui.comboBox(lens_box, self, "ri_calculation_mode",
                                                      label="Refraction Index calculation mode", labelWidth=350,
                                                      items=["User Parameters", "Prerefl File"],
                                                      callback=self.set_ri_calculation_mode,
                                                      sendSelectedValue=False, orientation="horizontal")

        self.calculation_mode_1 = oasysgui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=50)
        oasysgui.lineEdit(self.calculation_mode_1, self, "refraction_index", "Refraction index", labelWidth=350, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.calculation_mode_1, self, "attenuation_coefficient", "Attenuation coefficient [cm-1]", labelWidth=350, valueType=float, orientation="horizontal")

        self.calculation_mode_2 = oasysgui.widgetBox(lens_box, "", addSpace=True, orientation="vertical", height=50)

        file_box = oasysgui.widgetBox(self.calculation_mode_2, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_prerefl = oasysgui.lineEdit(file_box, self, "prerefl_file", "File Prerefl", labelWidth=100, valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectFilePrerefl)

        self.set_ri_calculation_mode()

        adv_other_box = oasysgui.widgetBox(tab_adv, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=310,
                     items=["All", "Mirror", "Image", "None", "Debug (All + start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.controlArea, height=80)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

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
        super().callResetSettings()
        self.setupUI()

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def selectFilePrerefl(self):
        self.le_file_prerefl.setText(oasysgui.selectFileFromDialog(self, self.prerefl_file, "Select File Prerefl", file_extension_filter="*.dat"))

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

    def get_write_file_options(self):
        write_start_files = 0
        write_end_files = 0
        write_star_files = 0
        write_mirr_files = 0

        if self.file_to_write_out == 0:
            write_star_files = 1
            write_mirr_files = 1
        elif self.file_to_write_out == 1:
            write_star_files = 1
        elif self.file_to_write_out == 2:
            write_mirr_files = 1
        elif self.file_to_write_out == 4:
            write_start_files = 1
            write_end_files = 1
            write_star_files = 1
            write_mirr_files = 1

        return write_start_files, write_end_files, write_star_files, write_mirr_files

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
        shadow_oe._oe.append_lens(p=self.p,
                                 q=self.q,
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

    def doSpecificSetting(self, shadow_oe):
        pass

    def checkFields(self):
        congruence.checkPositiveNumber(self.p, "P")
        congruence.checkPositiveNumber(self.q, "Q")

        if self.has_finite_diameter == 0:
            congruence.checkStrictlyPositiveNumber(self.diameter, "Diameter")

        if self.ri_calculation_mode == 1:
            congruence.checkFile(self.prerefl_file)
        else:
            congruence.checkPositiveNumber(self.refraction_index, "Refraction Index")
            congruence.checkPositiveNumber(self.attenuation_coefficient, "Attenuation Coefficient")

        congruence.checkStrictlyPositiveNumber(self.radius, "Radius")
        congruence.checkPositiveNumber(self.interthickness, "Lens Thickness")

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

        write_start_files, write_end_files, write_star_files, write_mirr_files = self.get_write_file_options()

        beam_out = ShadowBeam.traceFromCompoundOE(self.input_beam,
                                                  shadow_oe,
                                                  write_start_files=write_start_files,
                                                  write_end_files=write_end_files,
                                                  write_star_files=write_star_files,
                                                  write_mirr_files=write_mirr_files
                                                  )

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
            #self.error(self.error_id)
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
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
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtGui.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

        self.progressBarFinished()

    def setBeam(self, beam):
        self.onReceivingInput()

        if ShadowCongruence.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.traceOpticalElement()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                self.prerefl_file = data.prerefl_data_file
                self.ri_calculation_mode = 1

                self.set_ri_calculation_mode()
            else:
                QtGui.QMessageBox.warning(self, "Warning",
                          "Incompatible Preprocessor Data",
                          QtGui.QMessageBox.Ok)

    def setupUI(self):
        self.set_surface_shape()
        self.set_diameter()
        self.set_cylindrical()
        self.set_ri_calculation_mode()
