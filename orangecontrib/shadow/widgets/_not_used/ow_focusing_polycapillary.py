import sys, numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui import ow_generic_element
from oasys.util.oasys_util import EmittingStream, TTYGrabber, TriggerOut, TriggerIn
from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, ShadowBeam, ShadowOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowMath


class FocusingPolycapillary(ow_generic_element.GenericElement):
    name = "Focusing Polycapillary Lens"
    description = "User Defined: Focusing Polycapillary Lens"
    icon = "icons/focusing_polycapillary.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 7
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"},
               {"name": "Trigger",
                "type": TriggerIn,
                "doc": "Feedback signal to start a new beam simulation",
                "id": "Trigger"}]

    input_beam = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    CONTROL_AREA_HEIGHT = 440
    CONTROL_AREA_WIDTH = 470

    input_diameter = Setting(0.5)
    inner_diameter = Setting(1.5)
    output_diameter = Setting(0.5)

    angular_acceptance = Setting(20.0)
    focal_length = Setting(10.0)
    focus_dimension = Setting(100)

    lens_length = Setting(10.0)

    source_plane_distance = Setting(0.0)
    image_plane_distance = Setting(0)

    transmittance = Setting(40.0)

    file_to_write_out = Setting(3)

    want_main_area = 1

    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = gui.tabWidget(self.controlArea)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        lens_box = oasysgui.widgetBox(tab_bas, "Input Parameters", addSpace=False, orientation="vertical", height=600, width=450)

        self.le_source_plane_distance = oasysgui.lineEdit(lens_box, self, "source_plane_distance", "Source Plane Distance", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_image_plane_distance = oasysgui.lineEdit(lens_box, self, "image_plane_distance", "Image Plane Distance", labelWidth=350, valueType=float, orientation="horizontal")

        gui.separator(lens_box)

        self.le_input_diameter = oasysgui.lineEdit(lens_box, self, "input_diameter", "Input Diameter", labelWidth=350, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(lens_box, self, "angular_acceptance", "Angular Acceptance [deg]", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_inner_diameter = oasysgui.lineEdit(lens_box, self, "inner_diameter", "Central Diameter", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_output_diameter = oasysgui.lineEdit(lens_box, self, "output_diameter", "Output Diameter", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_focal_length = oasysgui.lineEdit(lens_box, self, "focal_length", "Focal Length", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_focus_dimension = oasysgui.lineEdit(lens_box, self, "focus_dimension", "Approximate focus dimension", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_lens_length = oasysgui.lineEdit(lens_box, self, "lens_length", "Lens Total Length", labelWidth=350, valueType=float, orientation="horizontal")

        gui.separator(lens_box)

        oasysgui.lineEdit(lens_box, self, "transmittance", "Lens Transmittance [%]", labelWidth=350, valueType=float, orientation="horizontal")

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

    def after_change_workspace_units(self):
        label = self.le_source_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_image_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_input_diameter.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_inner_diameter.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_output_diameter.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        label = self.le_focal_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_focus_dimension.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        label = self.le_lens_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def get_ray_rotation_angle(self, x, z):
        return numpy.tan(numpy.sqrt(x ** 2 + z ** 2) / self.focal_length)

    def get_first_slits_distance(self):
        return (0.5 * (self.inner_diameter - self.input_diameter)) / numpy.tan(numpy.radians(0.5 * self.angular_acceptance))

    def get_second_slits_distance(self):
        return (0.5 * (self.inner_diameter - self.output_diameter)) / numpy.tan(0.5 * self.output_diameter / self.focal_length)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def adjust_first_divergence(self, beam_out):
        for index in range(len(beam_out._beam.rays)):
            if beam_out._beam.rays[index, 9] == 1:
                beam_out._beam.rays[index, 3] = 0.0
                beam_out._beam.rays[index, 4] = 1.0
                beam_out._beam.rays[index, 5] = 0.0

        return beam_out

    def adjust_second_divergence_and_intensity(self, beam_out):
        reduction_factor = numpy.sqrt(self.transmittance / 100)

        for index in range(len(beam_out._beam.rays)):
            if beam_out._beam.rays[index, 9] == 1:
                beam_out._beam.rays[index, 6] = beam_out._beam.rays[index, 6] * reduction_factor
                beam_out._beam.rays[index, 7] = beam_out._beam.rays[index, 7] * reduction_factor
                beam_out._beam.rays[index, 8] = beam_out._beam.rays[index, 8] * reduction_factor
                beam_out._beam.rays[index, 15] = beam_out._beam.rays[index, 15] * reduction_factor
                beam_out._beam.rays[index, 16] = beam_out._beam.rays[index, 16] * reduction_factor
                beam_out._beam.rays[index, 17] = beam_out._beam.rays[index, 17] * reduction_factor

                x_ray = beam_out._beam.rays[index, 0]
                z_ray = beam_out._beam.rays[index, 2]

                sigma = self.focus_dimension * 1e-4

                distance = numpy.random.normal(scale=sigma)

                x_spot = numpy.random.random() * distance * self.get_random_sign()
                z_spot = numpy.sqrt(distance ** 2 - x_spot ** 2) * self.get_random_sign()

                v_director = ShadowMath.vector_difference([x_ray, 0.0, z_ray], [x_spot, self.focal_length + self.get_second_slits_distance(), z_spot])
                v_director = v_director / ShadowMath.vector_modulus(v_director)  # versor

                beam_out._beam.rays[index, 3] = v_director[0]
                beam_out._beam.rays[index, 4] = v_director[1]
                beam_out._beam.rays[index, 5] = v_director[2]

        return beam_out

    def get_random_sign(self):
        random = numpy.random.random()

        if random < 0.5:
            return 1.0
        else:
            return -1.0

    def populateFields_1(self, shadow_oe):
        slits_distance = self.get_first_slits_distance()

        shadow_oe._oe.T_SOURCE = self.source_plane_distance
        shadow_oe._oe.T_IMAGE = slits_distance
        shadow_oe._oe.T_INCIDENCE = 0.0
        shadow_oe._oe.T_REFLECTION = 180.0
        shadow_oe._oe.ALPHA = 0.0

        n_screen = 2
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # after
        i_abs = numpy.zeros(10)  # not absorbing
        i_slit = numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])  # slit
        i_stop = numpy.zeros(10)  # aperture
        k_slit = numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])  # ellipse
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_src_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = 0.0
        rx_slit[0] = self.input_diameter
        rz_slit[0] = self.input_diameter

        sl_dis[1] = slits_distance
        rx_slit[1] = self.inner_diameter
        rz_slit[1] = self.inner_diameter

        shadow_oe._oe.set_screens(n_screen,
                                 i_screen,
                                 i_abs,
                                 sl_dis,
                                 i_slit,
                                 i_stop,
                                 k_slit,
                                 thick,
                                 file_abs,
                                 rx_slit,
                                 rz_slit,
                                 cx_slit,
                                 cz_slit,
                                 file_src_ext)

    def populateFields_2(self, shadow_oe):
        slits_distance = self.lens_length - (self.get_first_slits_distance() - self.get_second_slits_distance())

        shadow_oe._oe.T_SOURCE = 0.0
        shadow_oe._oe.T_IMAGE = slits_distance
        shadow_oe._oe.T_INCIDENCE = 0.0
        shadow_oe._oe.T_REFLECTION = 180.0
        shadow_oe._oe.ALPHA = 0.0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # after
        i_abs = numpy.zeros(10)  # not absorbing
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # slit
        i_stop = numpy.zeros(10)  # aperture
        k_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # ellipse
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_src_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = slits_distance
        rx_slit[0] = self.inner_diameter
        rz_slit[0] = self.inner_diameter

        shadow_oe._oe.set_screens(n_screen,
                                 i_screen,
                                 i_abs,
                                 sl_dis,
                                 i_slit,
                                 i_stop,
                                 k_slit,
                                 thick,
                                 file_abs,
                                 rx_slit,
                                 rz_slit,
                                 cx_slit,
                                 cz_slit,
                                 file_src_ext)

    def populateFields_3(self, shadow_oe):
        slits_distance = self.get_second_slits_distance()

        shadow_oe._oe.T_SOURCE = 0.0
        shadow_oe._oe.T_IMAGE = slits_distance + self.image_plane_distance
        shadow_oe._oe.T_INCIDENCE = 0.0
        shadow_oe._oe.T_REFLECTION = 180.0
        shadow_oe._oe.ALPHA = 0.0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # after
        i_abs = numpy.zeros(10)  # not absorbing
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # slit
        i_stop = numpy.zeros(10)  # aperture
        k_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # ellipse
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_src_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = slits_distance
        rx_slit[0] = self.output_diameter
        rz_slit[0] = self.output_diameter

        shadow_oe._oe.set_screens(n_screen,
                                 i_screen,
                                 i_abs,
                                 sl_dis,
                                 i_slit,
                                 i_stop,
                                 k_slit,
                                 thick,
                                 file_abs,
                                 rx_slit,
                                 rz_slit,
                                 cx_slit,
                                 cz_slit,
                                 file_src_ext)

    def checkFields(self):
        congruence.checkPositiveNumber(self.source_plane_distance, "Distance from Source")
        congruence.checkPositiveNumber(self.image_plane_distance, "Image Plane Distance")
        congruence.checkStrictlyPositiveNumber(self.input_diameter, "Input Diameter")
        congruence.checkStrictlyPositiveAngle(self.angular_acceptance, "Angular Acceptance")
        congruence.checkStrictlyPositiveNumber(self.output_diameter, "Output Diameter")
        congruence.checkStrictlyPositiveNumber(self.inner_diameter, "Central Diameter")
        congruence.checkStrictlyPositiveNumber(self.focal_length, "Focal Length")
        congruence.checkStrictlyPositiveNumber(self.focus_dimension, "Focus Dimension")
        congruence.checkStrictlyPositiveNumber(self.lens_length, "Lens Total Length")

        if self.inner_diameter <= self.input_diameter:
            raise Exception("Central Diameter should be greater than Input diameter")

        if self.inner_diameter <= self.output_diameter:
            raise Exception("Central Diameter should be greater than Output diameter")

        if self.focal_length < self.output_diameter:
            raise Exception("Focal Length should be greater than or equal to Output diameter")

        first_slit_distance = self.get_first_slits_distance()
        second_slit_distance = self.get_second_slits_distance()

        slit_distance = first_slit_distance + second_slit_distance

        if self.lens_length < slit_distance:
            raise Exception("Lens total Length should be greater than or equal to " + str(slit_distance))

        congruence.checkStrictlyPositiveNumber(self.transmittance, "Lens Transmittance")

    def traceOpticalElement(self):
        try:
            self.error(self.error_id)
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                    self.progressBarSet(10)

                    self.checkFields()

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

                    shadow_oe_1 = ShadowOpticalElement.create_screen_slit()
                    self.populateFields_1(shadow_oe_1)

                    beam_out = ShadowBeam.traceFromOE(self.input_beam, shadow_oe_1)

                    self.adjust_first_divergence(beam_out)

                    self.progressBarSet(60)

                    shadow_oe_2 = ShadowOpticalElement.create_screen_slit()
                    self.populateFields_2(shadow_oe_2)

                    beam_out = ShadowBeam.traceFromOE(beam_out, shadow_oe_2)

                    self.adjust_second_divergence_and_intensity(beam_out)

                    self.progressBarSet(70)

                    shadow_oe_3 = ShadowOpticalElement.create_screen_slit()
                    self.populateFields_3(shadow_oe_3)

                    beam_out = ShadowBeam.traceFromOE(beam_out, shadow_oe_3)

                    if self.trace_shadow:
                        grabber.stop()

                        for row in grabber.ttyData:
                            self.writeStdOut(row)

                    self.setStatusMessage("Plotting Results")

                    self.plot_results(beam_out)

                    self.setStatusMessage("")

                    self.send("Beam", beam_out)
                    self.send("Trigger", TriggerIn(new_object=True))
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "QMessageBox.critical()",
                                       str(exception),
                                       QtWidgets.QMessageBox.Ok)

            self.error_id = self.error_id + 1
            self.error(self.error_id, "Exception occurred: " + str(exception))

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

    def setupUI(self):
        self.set_surface_shape()
        self.set_diameter()
        self.set_cylindrical()
        self.set_ri_calculation_mode()
