import sys, copy

from orangewidget import gui
from orangewidget.settings import Setting

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui import ow_generic_element
from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerIn, ShadowPreProcessorData, \
    ShadowCompoundOpticalElement, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowGui, ConfirmDialog


class DCM(ow_generic_element.GenericElement):
    name = "Double-Crystal Monochromator"
    description = "Shadow Compound OE: Double-Crystal Monochromator"
    icon = "icons/dcm.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 5
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

    p = Setting(0.0)
    q = Setting(0.0)
    photon_energy_ev = Setting(14000.0)
    separation = Setting(100.0)
    reflectivity_file = Setting(NONE_SPECIFIED)

    has_finite_dimensions = Setting([0, 0])
    dimensions = Setting([[0.0, 0.0], [0.0, 0.0]])

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

        ShadowGui.lineEdit(tab_bas, self, "p", "Distance Source - DCM center (P) [cm]", labelWidth=350, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(tab_bas, self, "q", "Distance DCM center - Image plane (Q) [cm]", labelWidth=350, valueType=float, orientation="horizontal")

        ShadowGui.lineEdit(tab_bas, self, "separation", "Separation between the Crystals [cm]\n(from center of 1st C. to center of 2nd C.) ", labelWidth=350, valueType=float,
                           orientation="horizontal")

        ShadowGui.lineEdit(tab_bas, self, "photon_energy_ev", "Photon Eneergy [eV]", labelWidth=350, valueType=float, orientation="horizontal")


        file_box = ShadowGui.widgetBox(tab_bas, "", addSpace=True, orientation="horizontal", height=25)

        self.le_reflectivity_file = ShadowGui.lineEdit(file_box, self, "reflectivity_file", "Reflectivity File", labelWidth=150, valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectFilePrerefl)

        gui.separator(tab_bas, height=10)

        self.tab_crystals = gui.tabWidget(tab_bas)

        tab_first_crystal = ShadowGui.createTabPage(self.tab_crystals, "First Crystal")
        tab_second_crystal = ShadowGui.createTabPage(self.tab_crystals, "Second Crystal")

        self.crystal_1_box = CrystalBox(dcm=self,
                                        parent=tab_first_crystal,
                                        has_finite_dimensions=self.has_finite_dimensions[0],
                                        dimensions=self.dimensions[0])

        self.crystal_2_box = CrystalBox(dcm=self,
                                        parent=tab_second_crystal,
                                        has_finite_dimensions=self.has_finite_dimensions[1],
                                        dimensions=self.dimensions[1])

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

    def selectFilePrerefl(self):
        self.le_reflectivity_file.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select Reflectivity File", ".", "*.dat"))

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            self.resetSettings()

            while self.tab_crystals.count() > 0:
                self.tab_crystals.removeTab(0)

            tab_first_crystal = ShadowGui.widgetBox(self.tab_crystals, addToLayout=0, margin=4)
            tab_second_crystal = ShadowGui.widgetBox(self.tab_crystals, addToLayout=0, margin=4)

            self.crystal_1_box = CrystalBox(dcm=self,
                                            parent=tab_first_crystal,
                                            has_finite_dimensions=self.has_finite_dimensions[0],
                                            dimensions=self.dimensions[0])

            self.crystal_2_box = CrystalBox(dcm=self,
                                            parent=tab_second_crystal,
                                            has_finite_dimensions=self.has_finite_dimensions[1],
                                            dimensions=self.dimensions[1])

            self.tab_crystals.addTab(tab_first_crystal, "First Crystal")
            self.tab_crystals.addTab(tab_second_crystal, "Second Crystal")

            self.setupUI()

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
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.has_finite_dimensions = []
            self.dimensions = []

            self.has_finite_dimensions.append(self.crystal_1_box.has_finite_dimensions)
            self.dimensions.append([self.crystal_1_box.mirror_width, self.crystal_1_box.mirror_length])

            self.has_finite_dimensions.append(self.crystal_2_box.has_finite_dimensions)
            self.dimensions.append([self.crystal_2_box.mirror_width, self.crystal_2_box.mirror_length])

        except:
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)
            self.dimensions = copy.deepcopy(bkp_dimensions)

    ##############################
    # SINGLE FIELDS SIGNALS
    ##############################

    def dump_has_finite_dimensions(self):
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)

        try:
            self.has_finite_dimensions = []

            self.has_finite_dimensions.append(self.crystal_1_box.has_finite_dimensions)
            self.has_finite_dimensions.append(self.crystal_2_box.has_finite_dimensions)
        except:
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)

    def dump_dimensions_0(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[0] = [self.crystal_1_box.mirror_width, self.crystal_1_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    def dump_dimensions_1(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[1] = [self.crystal_2_box.mirror_width, self.crystal_2_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def populateFields(self, shadow_oe):
        self.dumpSettings()

        dimension1_out = self.crystal_1_box.get_dimensions()
        dimension2_out = self.crystal_2_box.get_dimensions()

        shadow_oe._oe.append_monochromator_double_crystal(p0=self.p,
                                                         q0=self.q,
                                                         photon_energy_ev=self.photon_energy_ev,
                                                         separation=self.separation,
                                                         dimensions1=dimension1_out,
                                                         dimensions2=dimension2_out,
                                                         reflectivity_file=self.reflectivity_file)

    def doSpecificSetting(self, shadow_oe):
        pass

    def checkFields(self):
        ShadowGui.checkPositiveNumber(self.p, "Distance Source - KB center")
        ShadowGui.checkPositiveNumber(self.q, "Distance KB center - Image plane")

        ShadowGui.checkPositiveNumber(self.separation, "Separation between the Mirrors")
        ShadowGui.checkStrictlyPositiveNumber(self.photon_energy_ev, "Photon Energy")

        ShadowGui.checkFile(self.reflectivity_file)

        self.crystal_1_box.checkFields()
        self.crystal_2_box.checkFields()

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
            if data.bragg_data_file != ShadowPreProcessorData.NONE:
                self.reflectivity_file = data.bragg_data_file
                self.le_reflectivity_file.setText(data.bragg_data_file)

    def setupUI(self):
        self.set_use_different_focal_positions()

        self.crystal_1_box.setupUI()
        self.crystal_2_box.setupUI()


class CrystalBox(QtGui.QWidget):
    has_finite_dimensions = 0
    mirror_width = 0.0
    mirror_length = 0.0

    dcm = None

    is_on_init = True

    def __init__(self,
                 dcm=None,
                 parent=None,
                 has_finite_dimensions=0,
                 dimensions=[0.0, 0.0]):
        super().__init__(parent)

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self.setFixedWidth(470)
        self.setFixedHeight(400)

        self.dcm = dcm

        self.has_finite_dimensions = has_finite_dimensions
        self.mirror_width = dimensions[0]
        self.mirror_length = dimensions[1]

        mirror_box = ShadowGui.widgetBox(self, "Crystal Input Parameters", addSpace=False, orientation="vertical", height=330, width=460)

        gui.comboBox(mirror_box, self, "has_finite_dimensions", label="Dimensions", labelWidth=350,
                     items=["Finite", "Infinite"], sendSelectedValue=False, orientation="horizontal", callback=self.set_dimensions)

        self.dimension_box = ShadowGui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=50)
        self.dimension_box_empty = ShadowGui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=50)

        ShadowGui.lineEdit(self.dimension_box, self, "mirror_width", "Crystal Width [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.dcm.dump_dimensions_0)

        ShadowGui.lineEdit(self.dimension_box, self, "mirror_length", "Crystal Length [cm]", labelWidth=350, valueType=float, orientation="horizontal",
                           callback=self.dcm.dump_dimensions_1)

        self.set_dimensions()

        self.is_on_init = False

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def get_dimensions(self):
        if self.has_finite_dimensions == 0:
            return [self.mirror_width, self.mirror_length]
        elif self.has_finite_dimensions == 0:
            return [0.0, 0.0]
        else:
            raise ValueError("Dimensions")

    def set_dimensions(self):
        self.dimension_box.setVisible(self.has_finite_dimensions == 0)
        self.dimension_box_empty.setVisible(self.has_finite_dimensions != 0)

        if not self.is_on_init: self.dcm.dump_has_finite_dimensions()

    def checkFields(self):
        if self.has_finite_dimensions == 0:
            ShadowGui.checkStrictlyPositiveNumber(self.mirror_width, "Mirror Width")
            ShadowGui.checkStrictlyPositiveNumber(self.mirror_length, "Mirror Length")

    def setupUI(self):
        self.set_dimensions()
