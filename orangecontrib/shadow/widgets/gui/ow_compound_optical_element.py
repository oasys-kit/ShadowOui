__author__ = 'labx'

import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream, TTYGrabber, TriggerIn, TriggerOut

from orangecontrib.shadow.widgets.gui import ow_generic_element
from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, ShadowBeam, ShadowCompoundOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class CompoundOpticalElement(ow_generic_element.GenericElement):
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    category = "Compound Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("Trigger", TriggerOut, "sendNewBeam"),
              ("PreProcessor Data", ShadowPreProcessorData, "setPreProcessorData")]

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"},
               {"name": "Trigger",
                "type": TriggerIn,
                "doc": "Feedback signal to start a new beam simulation",
                "id": "Trigger"}]

    input_beam = None

    TABS_AREA_HEIGHT = 560
    CONTROL_AREA_WIDTH = 405

    file_to_write_out = Setting(3)

    not_interactive = False

    want_main_area = 1

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box=show_automatic_box)

        self.runaction = widget.OWAction("Run Shadow/Trace", self)
        self.runaction.triggered.connect(self.traceOpticalElement)
        self.addAction(self.runaction)

        #################################
        # FIX A WEIRD BEHAVIOUR AFTER DISPLAY
        # THE WIDGET: PROBABLY ON SIGNAL MANAGER
        self.dumpSettings()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        self.button_trace = gui.button(button_box, self, "Run Shadow/Trace", callback=self.traceOpticalElement)
        font = QFont(self.button_trace.font())
        font.setBold(True)
        self.button_trace.setFont(font)
        palette = QPalette(self.button_trace.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        self.button_trace.setPalette(palette) # assign new palette
        self.button_trace.setFixedHeight(45)

        self.button_reset = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(self.button_reset.font())
        font.setItalic(True)
        self.button_reset.setFont(font)
        palette = QPalette(self.button_reset.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        self.button_reset.setPalette(palette) # assign new palette
        self.button_reset.setFixedHeight(45)
        self.button_reset.setFixedWidth(150)

        gui.separator(self.controlArea)
        
        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT-5)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_bas = oasysgui.createTabPage(self.tabs_setting, "Basic Setting")
        self.tab_adv = oasysgui.createTabPage(self.tabs_setting, "Advanced Setting")

        adv_other_box = oasysgui.widgetBox(self.tab_adv, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=150,
                     items=["All", "Mirror", "Image", "None", "Debug (All + start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal")


    def sendNewBeam(self, trigger):
        try:
            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    if trigger and trigger.new_object == True:
                        if trigger.has_additional_parameter("variable_name"):
                            variable_name = trigger.get_additional_parameter("variable_name").strip()
                            variable_display_name = trigger.get_additional_parameter("variable_display_name").strip()
                            variable_value = trigger.get_additional_parameter("variable_value")
                            variable_um = trigger.get_additional_parameter("variable_um")

                            def check_options(variable_name):
                                pass
                                '''
                                if variable_name in ["mm_mirror_offset_x",
                                                     "mm_mirror_rotation_x",
                                                     "mm_mirror_offset_y",
                                                     "mm_mirror_rotation_y",
                                                     "mm_mirror_offset_z",
                                                     "mm_mirror_rotation_z"]:
                                    self.mirror_movement = 1
                                    self.set_MirrorMovement()
                                elif variable_name in ["sm_offset_x_mirr_ref_frame",
                                                       "sm_offset_y_mirr_ref_frame",
                                                       "sm_offset_z_mirr_ref_frame",
                                                       "sm_rotation_around_x",
                                                       "sm_rotation_around_y",
                                                       "sm_rotation_around_z"]:
                                    self.source_movement = 1
                                    self.set_SourceMovement()
                                elif variable_name == "mirror_orientation_angle_user_value":
                                    self.mirror_orientation_angle = 4
                                    self.mirror_orientation_angle_user()
                                elif variable_name == "incidence_angle_deg":
                                    self.calculate_incidence_angle_mrad()
                                elif variable_name == "incidence_angle_mrad":
                                    self.calculate_incidence_angle_deg()
                                elif variable_name == "reflection_angle_deg":
                                    self.calculate_reflection_angle_mrad()
                                elif variable_name == "reflection_angle_mrad":
                                    self.calculate_reflection_angle_deg()
                                elif variable_name in ["object_side_focal_distance", "image_side_focal_distance"]:
                                    self.surface_shape_parameters = 0
                                    self.focii_and_continuation_plane = 1
                                    self.set_IntExt_Parameters()
                                elif variable_name == "user_defined_bragg_angle":
                                    self.diffraction_calculation = 1
                                    self.set_UserDefinedBraggAngle()
                                    self.set_DiffractionCalculation()
                                elif variable_name in ["slit_width_xaxis", "slit_height_zaxis"]:
                                    self.aperturing = 1
                                    self.set_Aperturing()
                                elif variable_name in ["thickness"]:
                                    self.absorption = 1
                                    self.set_Absorption()
                                 '''
                            def check_number(x):
                                try:    return float(x)
                                except: return x

                            if "," in variable_name:
                                variable_names = variable_name.split(",")

                                if isinstance(variable_value, str) and "," in variable_value:
                                    variable_values = variable_value.split(",")
                                    for variable_name, variable_value in zip(variable_names, variable_values):
                                        setattr(self, variable_name.strip(), check_number(variable_value))
                                        check_options(variable_name)
                                else:
                                    for variable_name in variable_names:
                                        setattr(self, variable_name.strip(), check_number(variable_value))
                                        check_options(variable_name)
                            else:
                                setattr(self, variable_name, check_number(variable_value))
                                check_options(variable_name)

                            self.input_beam.setScanningData(ShadowBeam.ScanningData(variable_name, variable_value, variable_display_name, variable_um))

                        self.traceOpticalElement()
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception), QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception


    def traceOpticalElement(self):
        try:
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                    self.checkFields()

                    shadow_oe = ShadowCompoundOpticalElement.create_compound_oe(workspace_units_to_cm=self.workspace_units_to_cm)

                    self.populateFields(shadow_oe)

                    self.doSpecificSetting(shadow_oe)

                    self.progressBarSet(10)

                    self.completeOperations(shadow_oe)
                else:
                    if self.not_interactive: self.sendEmptyBeam()
                    else: raise Exception("Input Beam with no good rays")
            else:
                if self.not_interactive: self.sendEmptyBeam()
                else: raise Exception("Empty Input Beam")

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtWidgets.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    def doSpecificSetting(self, shadow_oe):
        pass

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
                                                  write_mirr_files=write_mirr_files,
                                                  widget_class_name=type(self).__name__
                                                  )

        if self.trace_shadow:
            grabber.stop()

            for row in grabber.ttyData:
                self.writeStdOut(row)

        self.setStatusMessage("Plotting Results")

        self.plot_results(beam_out)

        self.setStatusMessage("")

        self.send("Beam", beam_out)
        self.send("Trigger", TriggerIn(new_object=True))

    def setBeam(self, beam):
        self.not_interactive = self.check_not_interactive_conditions(beam)

        self.onReceivingInput()

        if ShadowCongruence.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.traceOpticalElement()


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

    def dumpSettings(self):
        pass

    def callResetSettings(self):
        super().callResetSettings()
        self.setupUI()

    def setupUI(self):
        pass
