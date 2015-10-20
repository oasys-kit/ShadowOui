import copy
import sys

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerIn, ShadowPreProcessorData, \
    ShadowCompoundOpticalElement, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from orangecontrib.shadow.widgets.gui import ow_generic_element


class KB(ow_generic_element.GenericElement):
    name = "Kirkpatrick-Baez Mirror"
    description = "Shadow Compound OE: Kirkpatrick-Baez Mirror"
    icon = "icons/kb.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Compound Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("Vertical Focusing PreProcessor Data #1", ShadowPreProcessorData, "setPreProcessorDataV"),
              ("Vertical Focusing PreProcessor Data #2", ShadowPreProcessorData, "setPreProcessorDataV"),
              ("Horizontal Focusing PreProcessor Data #1", ShadowPreProcessorData, "setPreProcessorDataH"),
              ("Horizontal Focusing PreProcessor Data #2", ShadowPreProcessorData, "setPreProcessorDataH")]

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

    p = Setting(0.0)
    q = Setting(0.0)
    separation = Setting(100.0)
    mirror_orientation_angle = Setting(0)
    use_different_focal_positions = Setting(0)
    focal_positions_p = Setting(0.0)
    focal_positions_q = Setting(0.0)

    grazing_angles_mrad = Setting([3.0, 3.0])
    shape = Setting([1, 1])
    has_finite_dimensions = Setting([0, 0])
    dimensions = Setting([[0.0, 0.0], [0.0, 0.0]])
    reflectivity_kind = Setting([0, 0])
    reflectivity_files = Setting([NONE_SPECIFIED, NONE_SPECIFIED])
    has_surface_error = Setting([0, 0])
    surface_error_files = Setting([NONE_SPECIFIED, NONE_SPECIFIED])

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

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        oasysgui.lineEdit(tab_bas, self, "p", "Distance Source - KB center (P) [cm]", labelWidth=350, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(tab_bas, self, "q", "Distance KB center - Image plane (Q) [cm]", labelWidth=350, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(tab_bas, self, "separation", "Separation between the Mirrors [cm]\n(from center of V.F.M. to center of H.F.M.) ", labelWidth=350, valueType=float,
                           orientation="horizontal")
        oasysgui.lineEdit(tab_bas, self, "mirror_orientation_angle", "Mirror orientation angle [deg]\n(with respect to the previous o.e. for the first mirror)", labelWidth=350,
                           valueType=float, orientation="horizontal")

        gui.comboBox(tab_bas, self, "use_different_focal_positions", label="Different Focal Positions", labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_use_different_focal_positions)

        self.focal_positions_box = oasysgui.widgetBox(tab_bas, "", addSpace=False, orientation="vertical", height=45)
        self.focal_positions_empty = oasysgui.widgetBox(tab_bas, "", addSpace=False, orientation="vertical", height=45)

        oasysgui.lineEdit(self.focal_positions_box, self, "focal_positions_p", "Focal Position P [cm]", labelWidth=350, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.focal_positions_box, self, "focal_positions_q", "Focal Position Q [cm]", labelWidth=350, valueType=float, orientation="horizontal")

        self.set_use_different_focal_positions()

        gui.separator(tab_bas, height=10)

        self.tab_mirrors = gui.tabWidget(tab_bas)

        tab_vertical = oasysgui.createTabPage(self.tab_mirrors, "Vertical Focusing Mirror")
        tab_horizontal = oasysgui.createTabPage(self.tab_mirrors, "Horizontal Focusing Mirror")

        self.v_box = MirrorBox(kb=self,
                               parent=tab_vertical,
                               grazing_angles_mrad=self.grazing_angles_mrad[0],
                               shape=self.shape[0],
                               has_finite_dimensions=self.has_finite_dimensions[0],
                               dimensions=self.dimensions[0],
                               reflectivity_kind=self.reflectivity_kind[0],
                               reflectivity_files=self.reflectivity_files[0],
                               has_surface_error=self.has_surface_error[0],
                               surface_error_files=self.surface_error_files[0])

        self.h_box = MirrorBox(kb=self,
                               parent=tab_horizontal,
                               grazing_angles_mrad=self.grazing_angles_mrad[1],
                               shape=self.shape[1],
                               has_finite_dimensions=self.has_finite_dimensions[1],
                               dimensions=self.dimensions[1],
                               reflectivity_kind=self.reflectivity_kind[1],
                               reflectivity_files=self.reflectivity_files[1],
                               has_surface_error=self.has_surface_error[1],
                               surface_error_files=self.surface_error_files[1])

        adv_other_box = oasysgui.widgetBox(tab_adv, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=310,
                     items=["All", "Mirror", "Image", "None"],
                     sendSelectedValue=False, orientation="horizontal")

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
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            self.resetSettings()

            while self.tab_mirrors.count() > 0:
                self.tab_mirrors.removeTab(0)

            tab_vertical = oasysgui.widgetBox(self.tab_mirrors, addToLayout=0, margin=4)
            tab_horizontal = oasysgui.widgetBox(self.tab_mirrors, addToLayout=0, margin=4)

            self.v_box = MirrorBox(kb=self,
                                   parent=tab_vertical,
                                   grazing_angles_mrad=self.grazing_angles_mrad[0],
                                   shape=self.shape[0],
                                   has_finite_dimensions=self.has_finite_dimensions[0],
                                   dimensions=self.dimensions[0],
                                   reflectivity_kind=self.reflectivity_kind[0],
                                   reflectivity_files=self.reflectivity_files[0],
                                   has_surface_error=self.has_surface_error[0],
                                   surface_error_files=self.surface_error_files[0])

            self.h_box = MirrorBox(kb=self,
                                   parent=tab_horizontal,
                                   grazing_angles_mrad=self.grazing_angles_mrad[1],
                                   shape=self.shape[1],
                                   has_finite_dimensions=self.has_finite_dimensions[1],
                                   dimensions=self.dimensions[1],
                                   reflectivity_kind=self.reflectivity_kind[1],
                                   reflectivity_files=self.reflectivity_files[1],
                                   has_surface_error=self.has_surface_error[1],
                                   surface_error_files=self.surface_error_files[1])

            self.tab_mirrors.addTab(tab_vertical, "Vertical Focusing Mirror")
            self.tab_mirrors.addTab(tab_horizontal, "Horizontal Focusing Mirror")

            self.setupUI()

    def set_use_different_focal_positions(self):
        self.focal_positions_box.setVisible(self.use_different_focal_positions == 1)
        self.focal_positions_empty.setVisible(self.use_different_focal_positions == 0)

    def get_focal_positions(self):
        if self.use_different_focal_positions == 0:
            return [0.0, 0.0]
        else:
            return [self.focal_positions_p, self.focal_positions_q]

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
        bkp_grazing_angles_mrad = copy.deepcopy(self.grazing_angles_mrad)
        bkp_shape = copy.deepcopy(self.shape)
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)
        bkp_dimensions = copy.deepcopy(self.dimensions)
        bkp_reflectivity_kind = copy.deepcopy(self.reflectivity_kind)
        bkp_reflectivity_files = copy.deepcopy(self.reflectivity_files)
        bkp_has_surface_error = copy.deepcopy(self.has_surface_error)
        bkp_surface_error_files = copy.deepcopy(self.surface_error_files)

        try:
            self.grazing_angles_mrad = []
            self.shape = []
            self.has_finite_dimensions = []
            self.dimensions = []
            self.reflectivity_kind = []
            self.reflectivity_files = []
            self.has_surface_error = []
            self.surface_error_files = []

            self.grazing_angles_mrad.append(self.v_box.grazing_angles_mrad)
            self.shape.append(self.v_box.shape)
            self.has_finite_dimensions.append(self.v_box.has_finite_dimensions)
            self.dimensions.append([self.v_box.mirror_width, self.v_box.mirror_length])
            self.reflectivity_kind.append(self.v_box.reflectivity_kind)
            self.reflectivity_files.append(self.v_box.reflectivity_files)
            self.has_surface_error.append(self.v_box.has_surface_error)
            self.surface_error_files.append(self.v_box.surface_error_files)

            self.grazing_angles_mrad.append(self.h_box.grazing_angles_mrad)
            self.shape.append(self.h_box.shape)
            self.has_finite_dimensions.append(self.h_box.has_finite_dimensions)
            self.dimensions.append([self.h_box.mirror_width, self.h_box.mirror_length])
            self.reflectivity_kind.append(self.h_box.reflectivity_kind)
            self.reflectivity_files.append(self.h_box.reflectivity_files)
            self.has_surface_error.append(self.h_box.has_surface_error)
            self.surface_error_files.append(self.h_box.surface_error_files)

        except:
            self.grazing_angles_mrad = copy.deepcopy(bkp_grazing_angles_mrad)
            self.shape = copy.deepcopy(bkp_shape)
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)
            self.dimensions = copy.deepcopy(bkp_dimensions)
            self.reflectivity_kind = copy.deepcopy(bkp_reflectivity_kind)
            self.reflectivity_files = copy.deepcopy(bkp_reflectivity_files)
            self.has_surface_error = copy.deepcopy(bkp_has_surface_error)
            self.surface_error_files = copy.deepcopy(bkp_surface_error_files)

    ##############################
    # SINGLE FIELDS SIGNALS
    ##############################

    def dump_grazing_angles_mrad(self):
        bkp_grazing_angles_mrad = copy.deepcopy(self.grazing_angles_mrad)

        try:
            self.grazing_angles_mrad = []

            self.grazing_angles_mrad.append(self.v_box.grazing_angles_mrad)
            self.grazing_angles_mrad.append(self.h_box.grazing_angles_mrad)
        except:
            self.grazing_angles_mrad = copy.deepcopy(bkp_grazing_angles_mrad)

    def dump_shape(self):
        bkp_shape = copy.deepcopy(self.shape)

        try:
            self.shape = []

            self.shape.append(self.v_box.shape)
            self.shape.append(self.h_box.shape)
        except:
            self.shape = copy.deepcopy(bkp_shape)

    def dump_has_finite_dimensions(self):
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)

        try:
            self.has_finite_dimensions = []

            self.has_finite_dimensions.append(self.v_box.has_finite_dimensions)
            self.has_finite_dimensions.append(self.h_box.has_finite_dimensions)
        except:
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)

    def dump_dimensions_0(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[0] = [self.v_box.mirror_width, self.v_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    def dump_dimensions_1(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[1] = [self.h_box.mirror_width, self.h_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    def dump_reflectivity_kind(self):
        bkp_reflectivity_kind = copy.deepcopy(self.reflectivity_kind)

        try:
            self.reflectivity_kind = []

            self.reflectivity_kind.append(self.v_box.reflectivity_kind)
            self.reflectivity_kind.append(self.h_box.reflectivity_kind)
        except:
            self.reflectivity_kind = copy.deepcopy(bkp_reflectivity_kind)

    def dump_reflectivity_files(self):
        bkp_reflectivity_files = copy.deepcopy(self.reflectivity_files)

        try:
            self.reflectivity_files = []

            self.reflectivity_files.append(self.v_box.reflectivity_files)
            self.reflectivity_files.append(self.h_box.reflectivity_files)
        except:
            self.reflectivity_files = copy.deepcopy(bkp_reflectivity_files)

    def dump_has_surface_error(self):
        bkp_has_surface_error = copy.deepcopy(self.has_surface_error)

        try:
            self.has_surface_error = []

            self.has_surface_error.append(self.v_box.has_surface_error)
            self.has_surface_error.append(self.h_box.has_surface_error)
        except:
            self.has_surface_error = copy.deepcopy(bkp_has_surface_error)

    def dump_surface_error_files(self):
        bkp_surface_error_files = copy.deepcopy(self.surface_error_files)

        try:
            self.surface_error_files = []

            self.surface_error_files.append(self.v_box.surface_error_files)
            self.surface_error_files.append(self.h_box.surface_error_files)
        except:
            self.surface_error_files = copy.deepcopy(bkp_surface_error_files)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def populateFields(self, shadow_oe):
        self.dumpSettings()

        shape_out = []
        shape_out.append(self.v_box.get_shape())
        shape_out.append(self.h_box.get_shape())

        surface_error_files_out = []
        surface_error_files_out.append(self.v_box.get_surface_error_files())
        surface_error_files_out.append(self.h_box.get_surface_error_files())

        dimension1_out = self.v_box.get_dimensions()
        dimension2_out = self.h_box.get_dimensions()

        shadow_oe._oe.append_kb(p0=self.p,
                               q0=self.q,
                               grazing_angles_mrad=self.grazing_angles_mrad,
                               separation=self.separation,
                               mirror_orientation_angle=self.mirror_orientation_angle,
                               focal_positions=self.get_focal_positions(),
                               shape=shape_out,
                               dimensions1=dimension1_out,
                               dimensions2=dimension2_out,
                               reflectivity_kind=self.reflectivity_kind,
                               reflectivity_files=self.reflectivity_files,
                               surface_error_files=surface_error_files_out)

    def doSpecificSetting(self, shadow_oe):
        pass

    def checkFields(self):
        congruence.checkPositiveNumber(self.p, "Distance Source - KB center")
        congruence.checkPositiveNumber(self.q, "Distance KB center - Image plane")

        congruence.checkPositiveNumber(self.separation, "Separation between the Mirrors")
        congruence.checkPositiveAngle(self.mirror_orientation_angle, "Mirror orientation angle")

        if self.use_different_focal_positions == 1:
            congruence.checkPositiveNumber(self.focal_positions_p, "Focal Position P")
            congruence.checkPositiveNumber(self.focal_positions_q, "Focal Position Q")

        self.v_box.checkFields()
        self.h_box.checkFields()

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
            #self.error(self.error_id)
            #self.setStatusMessage("")
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

    def setPreProcessorDataV(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                self.v_box.reflectivity_files = data.prerefl_data_file
                self.v_box.le_reflectivity_files.setText(data.prerefl_data_file)

                self.dump_reflectivity_files()

            if data.m_layer_data_file_dat != ShadowPreProcessorData.NONE:
                self.v_box.reflectivity_files = data.m_layer_data_file_dat
                self.v_box.le_reflectivity_files.setText(data.m_layer_data_file_dat)

                self.dump_reflectivity_files()

            if data.waviness_data_file != ShadowPreProcessorData.NONE:
                self.v_box.surface_error_files = data.waviness_data_file
                self.v_box.le_surface_error_files.setText(data.waviness_data_file)

                self.dump_surface_error_files()

    def setPreProcessorDataH(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                self.h_box.reflectivity_files = data.prerefl_data_file
                self.h_box.le_reflectivity_files.setText(data.prerefl_data_file)

                self.dump_reflectivity_files()

            if data.m_layer_data_file_dat != ShadowPreProcessorData.NONE:
                self.h_box.reflectivity_files = data.m_layer_data_file_dat
                self.h_box.le_reflectivity_files.setText(data.m_layer_data_file_dat)

            if data.waviness_data_file != ShadowPreProcessorData.NONE:
                self.h_box.surface_error_files = data.waviness_data_file
                self.h_box.le_surface_error_files.setText(data.waviness_data_file)

                self.dump_surface_error_files()

    def setupUI(self):
        self.set_use_different_focal_positions()

        self.v_box.setupUI()
        self.h_box.setupUI()


class MirrorBox(QtGui.QWidget):
    grazing_angles_mrad = 3.0
    shape = 1
    has_finite_dimensions = 0
    mirror_width = 0.0
    mirror_length = 0.0
    reflectivity_kind = 0
    reflectivity_files = KB.NONE_SPECIFIED
    has_surface_error = 0
    surface_error_files = KB.NONE_SPECIFIED

    kb = None

    is_on_init = True

    def __init__(self,
                 kb=None,
                 parent=None,
                 grazing_angles_mrad=3.0,
                 shape=1,
                 has_finite_dimensions=0,
                 dimensions=[0.0, 0.0],
                 reflectivity_kind=0,
                 reflectivity_files=KB.NONE_SPECIFIED,
                 has_surface_error=0,
                 surface_error_files=KB.NONE_SPECIFIED):
        super().__init__(parent)

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self.setFixedWidth(470)
        self.setFixedHeight(400)

        self.kb = kb

        self.grazing_angles_mrad = grazing_angles_mrad
        self.shape = shape
        self.has_finite_dimensions = has_finite_dimensions
        self.mirror_width = dimensions[0]
        self.mirror_length = dimensions[1]
        self.reflectivity_kind = reflectivity_kind
        self.reflectivity_files = reflectivity_files
        self.has_surface_error = has_surface_error
        self.surface_error_files = surface_error_files

        mirror_box = oasysgui.widgetBox(self, "Mirror Input Parameters", addSpace=False, orientation="vertical", height=330, width=460)

        oasysgui.lineEdit(mirror_box, self, "grazing_angles_mrad", "Grazing Angle [mrad]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.kb.dump_grazing_angles_mrad)

        gui.separator(mirror_box)

        gui.comboBox(mirror_box, self, "shape", label="Surface Shape", labelWidth=350,
                     items=["Sphere", "Ellipse"], sendSelectedValue=False, orientation="horizontal", callback=self.kb.dump_shape)

        gui.separator(mirror_box)

        gui.comboBox(mirror_box, self, "has_finite_dimensions", label="Dimensions", labelWidth=350,
                     items=["Finite", "Infinite"], sendSelectedValue=False, orientation="horizontal", callback=self.set_dimensions)

        self.dimension_box = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=50)
        self.dimension_box_empty = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=50)

        oasysgui.lineEdit(self.dimension_box, self, "mirror_width", "Mirror Width [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.kb.dump_dimensions_0)

        oasysgui.lineEdit(self.dimension_box, self, "mirror_length", "Mirror Length [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.kb.dump_dimensions_1)

        self.set_dimensions()

        gui.separator(mirror_box, height=10)

        gui.comboBox(mirror_box, self, "reflectivity_kind", label="Reflectivity Kind", labelWidth=350,
                     items=["Ideal Reflector", "Mirror", "Multilayer"], sendSelectedValue=False, orientation="horizontal", callback=self.set_reflectivity_kind)

        self.reflectivity_box = oasysgui.widgetBox(mirror_box, "", addSpace=True, orientation="vertical", height=25)
        self.reflectivity_box_empty = oasysgui.widgetBox(mirror_box, "", addSpace=True, orientation="vertical", height=25)

        file_box = oasysgui.widgetBox(self.reflectivity_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_reflectivity_files = oasysgui.lineEdit(file_box, self, "reflectivity_files", "Reflectivity File", labelWidth=150, valueType=str,
                                                        orientation="horizontal", callback=self.kb.dump_reflectivity_files)

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectFilePrerefl)


        self.set_reflectivity_kind()

        gui.separator(mirror_box)

        gui.comboBox(mirror_box, self, "has_surface_error", label="Surface Error", labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_has_surface_error)

        self.surface_error_box = oasysgui.widgetBox(mirror_box, "", addSpace=True, orientation="vertical", height=25)
        self.surface_error_box_empty = oasysgui.widgetBox(mirror_box, "", addSpace=True, orientation="vertical", height=25)


        file_box = oasysgui.widgetBox(self.surface_error_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_surface_error_files = oasysgui.lineEdit(file_box, self, "surface_error_files", "Surface Error File", labelWidth=150, valueType=str,
                                                         orientation="horizontal",
                                                         callback=self.kb.dump_surface_error_files)

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectFileSurfaceError)

        self.set_has_surface_error()

        self.is_on_init = False

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def selectFilePrerefl(self):
        self.le_reflectivity_files.setText(oasysgui.selectFileFromDialog(self, self.reflectivity_files, "Select Reflectivity File", file_extension_filter="*.dat"))

        self.reflectivity_files = self.le_reflectivity_files.text()
        self.kb.dump_reflectivity_files()

    def selectFileSurfaceError(self):
        self.le_surface_error_files.setText(oasysgui.selectFileFromDialog(self, self.surface_error_files, "Surface Error File", file_extension_filter="*.dat; *.sha"))

        self.surface_error_files = self.le_surface_error_files.text()
        self.kb.dump_surface_error_files()

    def get_shape(self):
        if self.shape == 0:
            return 1
        elif self.shape == 1:
            return 2
        else:
            raise ValueError("Surface Shape")

    def get_dimensions(self):
        if self.has_finite_dimensions == 0:
            return [self.mirror_width, self.mirror_length]
        elif self.has_finite_dimensions == 0:
            return [0.0, 0.0]
        else:
            raise ValueError("Dimensions")

    def get_surface_error_files(self):
        if self.has_surface_error == 1:
            return self.surface_error_files
        else:
            return ""

    def set_dimensions(self):
        self.dimension_box.setVisible(self.has_finite_dimensions == 0)
        self.dimension_box_empty.setVisible(self.has_finite_dimensions != 0)

        if not self.is_on_init: self.kb.dump_has_finite_dimensions()

    def set_reflectivity_kind(self):
        self.reflectivity_box.setVisible(self.reflectivity_kind != 0)
        self.reflectivity_box_empty.setVisible(self.reflectivity_kind == 0)

        if not self.is_on_init: self.kb.dump_reflectivity_kind()

    def set_has_surface_error(self):
        self.surface_error_box.setVisible(self.has_surface_error != 0)
        self.surface_error_box_empty.setVisible(self.has_surface_error == 0)

        if not self.is_on_init: self.kb.dump_has_surface_error()

    def checkFields(self):
        congruence.checkPositiveNumber(self.grazing_angles_mrad, "Grazing Angle")

        if self.has_finite_dimensions == 0:
            congruence.checkStrictlyPositiveNumber(self.mirror_width, "Mirror Width")
            congruence.checkStrictlyPositiveNumber(self.mirror_length, "Mirror Length")

        if self.reflectivity_kind != 0:
            congruence.checkFile(self.reflectivity_files)

        if self.has_surface_error == 1:
            congruence.checkFile(self.surface_error_files)

    def setupUI(self):
        self.set_dimensions()
        self.set_reflectivity_kind()
        self.set_has_surface_error()
