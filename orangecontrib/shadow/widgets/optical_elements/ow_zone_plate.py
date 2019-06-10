import sys, numpy, copy

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream, TTYGrabber, TriggerIn

from orangecontrib.shadow.util.shadow_objects import ShadowOpticalElement, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPhysics, ShadowMath
from orangecontrib.shadow.widgets.gui.ow_generic_element import GenericElement

import xraylib
from oasys.util.oasys_util import ChemicalFormulaParser


AMPLITUDE_ZP = 0
PHASE_ZP = 1

GOOD = 1
LOST_ZP = -191919
GOOD_ZP = 191919

COLLIMATED_SOURCE_LIMIT = 1e4 # m



class ZonePlate(GenericElement):

    name = "Zone Plate"
    description = "Shadow OE: Zone Plate"
    icon = "icons/zone_plate.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 23
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"},
               {"name":"Trigger",
                "type": TriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    input_beam = None
    output_beam = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    ONE_ROW_HEIGHT = 65
    TWO_ROW_HEIGHT = 110
    THREE_ROW_HEIGHT = 170

    INNER_BOX_WIDTH_L3=322
    INNER_BOX_WIDTH_L2=335
    INNER_BOX_WIDTH_L1=358
    INNER_BOX_WIDTH_L0=375

    source_plane_distance = Setting(10.0)
    image_plane_distance = Setting(20.0)

    delta_rn = Setting(25) # nm
    diameter = Setting(618) # micron
    source_distance_flag = Setting(0)
    source_distance = Setting(0.0)

    type_of_zp = Setting(1)

    zone_plate_material = Setting("Au")
    zone_plate_thickness = Setting(200) # nm
    substrate_material = Setting("Si3N4")
    substrate_thickness = Setting(50) # nm

    avg_wavelength  = 0.0
    number_of_zones = 0
    focal_distance = 0.0
    image_position = 0.0
    magnification  = 0.0
    efficiency     = 0.0
    max_efficiency  = 0.0
    thickness_max_efficiency     = 0.0
    predicted_focal_size_zp = 0.0
    predicted_focal_size_ss = 0.0
    predicted_focal_size_de = 0.0
    predicted_focal_size_total = 0.0

    automatically_set_image_plane = Setting(0)

    energy_plot = Setting(0)
    thickness_plot = Setting(0)
    energy_from = Setting(0)
    energy_to = Setting(0)
    thickness_from = Setting(0)
    thickness_to = Setting(0)

    ##################################################

    mirror_movement = Setting(0)

    mm_mirror_offset_x = Setting(0.0)
    mm_mirror_rotation_x = Setting(0.0)
    mm_mirror_offset_y = Setting(0.0)
    mm_mirror_rotation_y = Setting(0.0)
    mm_mirror_offset_z = Setting(0.0)
    mm_mirror_rotation_z = Setting(0.0)

    #####

    source_movement = Setting(0)
    sm_angle_of_incidence = Setting(0.0)
    sm_distance_from_mirror = Setting(0.0)
    sm_z_rotation = Setting(0.0)
    sm_offset_x_mirr_ref_frame = Setting(0.0)
    sm_offset_y_mirr_ref_frame = Setting(0.0)
    sm_offset_z_mirr_ref_frame = Setting(0.0)
    sm_offset_x_source_ref_frame = Setting(0.0)
    sm_offset_y_source_ref_frame = Setting(0.0)
    sm_offset_z_source_ref_frame = Setting(0.0)
    sm_rotation_around_x = Setting(0.0)
    sm_rotation_around_y = Setting(0.0)
    sm_rotation_around_z = Setting(0.0)

    #####

    file_to_write_out = Setting(3) # Mirror: users found difficoult to activate the "Footprint" option.
    write_out_inc_ref_angles = Setting(0)

    def __init__(self):
        super(ZonePlate, self).__init__()

        self.runaction = widget.OWAction("Run Shadow/Trace", self)
        self.runaction.triggered.connect(self.traceOpticalElement)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/Trace", callback=self.traceOpticalElement)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_pos = oasysgui.createTabPage(tabs_setting, "Position")

        upper_box = oasysgui.widgetBox(tab_pos, "Optical Element Orientation", addSpace=True, orientation="vertical")

        self.le_source_plane_distance = oasysgui.lineEdit(upper_box, self, "source_plane_distance", "Source Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_image_plane_distance  = oasysgui.lineEdit(upper_box, self, "image_plane_distance", "Image Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        ##########################################
        ##########################################
        # BASIC SETTINGS
        ##########################################
        ##########################################

        tabs_basic_setting = oasysgui.tabWidget(tab_bas)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT-5)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_zone_plate_1 = oasysgui.createTabPage(tabs_basic_setting, "Zone Plate Input Parameters")
        tab_zone_plate_2 = oasysgui.createTabPage(tabs_basic_setting, "Zone Plate Output Parameters")

        zp_box = oasysgui.widgetBox(tab_zone_plate_1, "Input Parameters", addSpace=False, orientation="vertical", height=290)

        oasysgui.lineEdit(zp_box, self, "delta_rn",  u"\u03B4" + "rn [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(zp_box, self, "diameter", "Z.P. Diameter [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(zp_box, self, "source_distance_flag", label="Source Distance", labelWidth=350,
                     items=["Same as Source Plane", "Different"],
                     callback=self.set_SourceDistanceFlag, sendSelectedValue=False, orientation="horizontal")

        self.zp_box_1 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=30)
        self.zp_box_2 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical", height=30)

        self.le_source_distance = oasysgui.lineEdit(self.zp_box_1, self, "source_distance", "Source Distance", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_SourceDistanceFlag()

        gui.comboBox(zp_box, self, "type_of_zp", label="Type of Zone Plate", labelWidth=350,
                     items=["Amplitude", "Phase"],
                     callback=self.set_TypeOfZP, sendSelectedValue=False, orientation="horizontal")

        gui.separator(zp_box, height=5)

        self.zp_box_3 = oasysgui.widgetBox(zp_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.zp_box_3, self, "zone_plate_material",  "Zone Plate Material", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.zp_box_3, self, "zone_plate_thickness",  "Zone Plate Thickness [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zp_box_3, self, "substrate_material", "Substrate Material", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.zp_box_3, self, "substrate_thickness",  "Substrate Thickness [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_TypeOfZP()

        zp_out_box = oasysgui.widgetBox(tab_zone_plate_2, "Output Parameters", addSpace=False, orientation="vertical", height=270)

        self.le_avg_wavelength = oasysgui.lineEdit(zp_out_box, self, "avg_wavelength", "Average Wavelenght [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_avg_wavelength.setReadOnly(True)
        font = QFont(self.le_avg_wavelength.font())
        font.setBold(True)
        self.le_avg_wavelength.setFont(font)
        palette = QPalette(self.le_avg_wavelength.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_avg_wavelength.setPalette(palette)

        self.le_number_of_zones = oasysgui.lineEdit(zp_out_box, self, "number_of_zones", "Number of Zones", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_number_of_zones.setReadOnly(True)
        font = QFont(self.le_number_of_zones.font())
        font.setBold(True)
        self.le_number_of_zones.setFont(font)
        palette = QPalette(self.le_number_of_zones.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_number_of_zones.setPalette(palette)

        self.le_focal_distance = oasysgui.lineEdit(zp_out_box, self, "focal_distance", "Focal Distance", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_focal_distance.setReadOnly(True)
        font = QFont(self.le_focal_distance.font())
        font.setBold(True)
        self.le_focal_distance.setFont(font)
        palette = QPalette(self.le_focal_distance.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_focal_distance.setPalette(palette)

        self.le_image_position = oasysgui.lineEdit(zp_out_box, self, "image_position", "Image Position (Q)", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_image_position.setReadOnly(True)
        font = QFont(self.le_image_position.font())
        font.setBold(True)
        self.le_image_position.setFont(font)
        palette = QPalette(self.le_image_position.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_image_position.setPalette(palette)

        self.le_magnification = oasysgui.lineEdit(zp_out_box, self, "magnification", "Magnification", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_magnification.setReadOnly(True)
        font = QFont(self.le_magnification.font())
        font.setBold(True)
        self.le_magnification.setFont(font)
        palette = QPalette(self.le_magnification.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_magnification.setPalette(palette)

        self.le_efficiency = oasysgui.lineEdit(zp_out_box, self, "efficiency", "Efficiency % (Avg. Wavelength)", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_efficiency.setReadOnly(True)
        font = QFont(self.le_efficiency.font())
        font.setBold(True)
        self.le_efficiency.setFont(font)
        palette = QPalette(self.le_efficiency.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_efficiency.setPalette(palette)

        self.le_max_efficiency = oasysgui.lineEdit(zp_out_box, self, "max_efficiency", "Max Possible Efficiency %", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_max_efficiency.setReadOnly(True)
        font = QFont(self.le_max_efficiency.font())
        font.setBold(True)
        self.le_max_efficiency.setFont(font)
        palette = QPalette(self.le_max_efficiency.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_max_efficiency.setPalette(palette)

        self.le_thickness_max_efficiency = oasysgui.lineEdit(zp_out_box, self, "thickness_max_efficiency", "Max Efficiency Thickness [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_thickness_max_efficiency.setReadOnly(True)
        font = QFont(self.le_thickness_max_efficiency.font())
        font.setBold(True)
        self.le_thickness_max_efficiency.setFont(font)
        palette = QPalette(self.le_thickness_max_efficiency.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_thickness_max_efficiency.setPalette(palette)

        gui.comboBox(zp_out_box, self, "automatically_set_image_plane", label="Automatically set Image Plane Distance", labelWidth=350,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        zp_out_box_2 = oasysgui.widgetBox(tab_zone_plate_2, "Efficiency Plot", addSpace=False, orientation="vertical", height=200)

        gui.comboBox(zp_out_box_2, self, "energy_plot", label="Plot Efficiency vs. Energy", labelWidth=350,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_EnergyPlot)

        self.zp_out_box_2_1 = oasysgui.widgetBox(zp_out_box_2, "", addSpace=False, orientation="vertical", height=50)
        self.zp_out_box_2_2 = oasysgui.widgetBox(zp_out_box_2, "", addSpace=False, orientation="vertical", height=50)

        oasysgui.lineEdit(self.zp_out_box_2_1, self, "energy_from",  "Energy From [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zp_out_box_2_1, self, "energy_to",  "Energy To [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(zp_out_box_2, self, "thickness_plot", label="Plot Efficiency vs. Thickness", labelWidth=350,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_ThicknessPlot)

        self.zp_out_box_2_3 = oasysgui.widgetBox(zp_out_box_2, "", addSpace=False, orientation="vertical", height=50)
        self.zp_out_box_2_4 = oasysgui.widgetBox(zp_out_box_2, "", addSpace=False, orientation="vertical", height=50)

        oasysgui.lineEdit(self.zp_out_box_2_3, self, "thickness_from",  "Thickness From [nm]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.zp_out_box_2_3, self, "thickness_to",  "Thickness To [nm]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_EnergyPlot()
        self.set_ThicknessPlot()

        ##########################################
        ##########################################
        # ADVANCED SETTINGS
        ##########################################
        ##########################################

        tabs_advanced_setting = oasysgui.tabWidget(tab_adv)

        tab_adv_mir_mov = oasysgui.createTabPage(tabs_advanced_setting, "O.E. Movement")
        tab_adv_sou_mov = oasysgui.createTabPage(tabs_advanced_setting, "Source Movement")
        tab_adv_misc = oasysgui.createTabPage(tabs_advanced_setting, "Output Files")


        ##########################################
        #
        # TAB 2.2 - Mirror Movement
        #
        ##########################################

        mir_mov_box = oasysgui.widgetBox(tab_adv_mir_mov, "O.E. Movement Parameters", addSpace=False, orientation="vertical", height=230)

        gui.comboBox(mir_mov_box, self, "mirror_movement", label="O.E. Movement", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_MirrorMovement, sendSelectedValue=False, orientation="horizontal")

        gui.separator(mir_mov_box, height=10)

        self.mir_mov_box_1 = oasysgui.widgetBox(mir_mov_box, "", addSpace=False, orientation="vertical")

        self.le_mm_mirror_offset_x = oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_x", "O.E. Offset X", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_x", "O.E. Rotation X [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_mm_mirror_offset_y = oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_y", "O.E. Offset Y", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_y", "O.E. Rotation Y [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_mm_mirror_offset_z = oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_z", "O.E. Offset Z", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_z", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_MirrorMovement()

       ##########################################
        #
        # TAB 2.3 - Source Movement
        #
        ##########################################

        sou_mov_box = oasysgui.widgetBox(tab_adv_sou_mov, "Source Movement Parameters", addSpace=False, orientation="vertical", height=400)

        gui.comboBox(sou_mov_box, self, "source_movement", label="Source Movement", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_SourceMovement, sendSelectedValue=False, orientation="horizontal")

        gui.separator(sou_mov_box, height=10)

        self.sou_mov_box_1 = oasysgui.widgetBox(sou_mov_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_angle_of_incidence", "Angle of Incidence [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_distance_from_mirror = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_distance_from_mirror", "Distance from O.E.", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_z_rotation", "Z-rotation [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_x_mirr_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_mirr_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_y_mirr_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_mirr_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_z_mirr_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_mirr_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_x_source_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_source_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_y_source_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_source_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_sm_offset_z_source_ref_frame = oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_source_ref_frame", "--", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_x", "rotation [CCW, deg] around X", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_y", "rotation [CCW, deg] around Y", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_z", "rotation [CCW, deg] around Z", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_SourceMovement()

        ##########################################
        #
        # TAB 2.4 - Other
        #
        ##########################################

        adv_other_box = oasysgui.widgetBox(tab_adv_misc, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=150,
                     items=["All", "Mirror", "Image", "None", "Debug (All + start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(adv_other_box, self, "write_out_inc_ref_angles", label="Write out Incident/Reflected angles [angle.xx]", labelWidth=300,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")


        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def set_EnergyPlot(self):
        self.zp_out_box_2_1.setVisible(self.energy_plot==1)
        self.zp_out_box_2_2.setVisible(self.energy_plot==0)

    def set_ThicknessPlot(self):
        self.zp_out_box_2_3.setVisible(self.thickness_plot==1)
        self.zp_out_box_2_4.setVisible(self.thickness_plot==0)


    def isFootprintEnabled(self):
        return False

    def enableFootprint(self, enabled=False):
        pass

    def traceOpticalElement(self):
        try:
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    self.checkFields()

                    sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                    if self.trace_shadow:
                        grabber = TTYGrabber()
                        grabber.start()

                    ###########################################
                    # TODO: TO BE ADDED JUST IN CASE OF BROKEN
                    #       ENVIRONMENT: MUST BE FOUND A PROPER WAY
                    #       TO TEST SHADOW
                    self.fixWeirdShadowBug()
                    ###########################################

                    self.progressBarSet(10)

                    if self.source_distance_flag == 0:
                        self.source_distance = self.source_plane_distance

                    zone_plate_beam = self.get_zone_plate_beam()

                    go = numpy.where(zone_plate_beam._beam.rays[:, 9] == GOOD)

                    self.avg_wavelength = ShadowPhysics.getWavelengthFromShadowK(numpy.average(zone_plate_beam._beam.rays[go, 10]))*1e-1 #ANGSTROM->nm

                    self.focal_distance = (self.delta_rn*(self.diameter*1000)/self.avg_wavelength)* (1e-9/self.workspace_units_to_m)       # WS Units
                    self.image_position = self.focal_distance*self.source_distance/(self.source_distance-self.focal_distance)              # WS Units
                    self.magnification = numpy.abs(self.image_position/self.source_distance)

                    self.avg_wavelength = numpy.round(self.avg_wavelength, 6)      # nm
                    self.focal_distance = numpy.round(self.focal_distance, 6)
                    self.image_position = numpy.round(self.image_position, 6)
                    self.magnification = numpy.round(self.magnification, 6)

                    if self.automatically_set_image_plane == 1:
                        self.image_plane_distance = self.image_position

                    self.progressBarSet(30)

                    if self.type_of_zp == PHASE_ZP:
                        efficiency, max_efficiency, thickness_max_efficiency = ZonePlate.calculate_efficiency(self.avg_wavelength, # Angstrom
                                                                                                              self.zone_plate_material,
                                                                                                              self.zone_plate_thickness)

                        self.efficiency = numpy.round(100*efficiency, 3)
                        self.max_efficiency = numpy.round(100*max_efficiency, 3)
                        self.thickness_max_efficiency =  thickness_max_efficiency
                    else:
                        self.efficiency = numpy.round(100/(numpy.pi**2), 3)
                        self.max_efficiency = numpy.nan
                        self.thickness_max_efficiency =  numpy.nan

                    focused_beam, \
                    self.number_of_zones = ZonePlate.apply_fresnel_zone_plate(zone_plate_beam,  # WS Units
                                                                              self.type_of_zp,
                                                                              self.diameter,  # micron
                                                                              self.delta_rn, # nm
                                                                              self.substrate_material,
                                                                              self.substrate_thickness,
                                                                              self.zone_plate_material,
                                                                              self.zone_plate_thickness,
                                                                              self.source_distance, # WS Units
                                                                              self.workspace_units_to_m)

                    self.progressBarSet(60)

                    beam_out = self.get_output_beam(focused_beam)

                    self.progressBarSet(80)

                    if self.trace_shadow:
                        grabber.stop()

                        for row in grabber.ttyData:
                           self.writeStdOut(row)

                    self.setStatusMessage("Plotting Results")

                    self.plot_results(beam_out)
                    self.plot_efficiency()

                    self.setStatusMessage("")

                    beam_out.setScanningData(self.input_beam.scanned_variable_data)

                    self.send("Beam", beam_out)
                    self.send("Trigger", TriggerIn(new_object=True))
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                       str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()


    def plot_efficiency(self):
        if self.type_of_zp == PHASE_ZP:
            if self.energy_plot == 1:
                if self.plot_canvas[5] is None:
                    self.plot_canvas[5] = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=False)
                    self.tab[5].layout().addWidget(self.plot_canvas[5] )

                self.plot_canvas[5].clear()

                self.plot_canvas[5].setDefaultPlotLines(True)
                self.plot_canvas[5].setActiveCurveColor(color='blue')
    
                self.plot_canvas[5].setGraphTitle('Thickness: ' + str(self.zone_plate_thickness) + " nm")
                self.plot_canvas[5].getXAxis().setLabel('Energy [eV]')
                self.plot_canvas[5].getYAxis().setLabel('Efficiency [%]')
    
                x_values = numpy.linspace(self.energy_from, self.energy_to, 100)
                y_values = numpy.zeros(100)
    
                for index in range(len(x_values)):
                    y_values[index], _, _ = ZonePlate.calculate_efficiency(ShadowPhysics.getWavelengthFromEnergy(x_values[index])/10,
                                                                           self.zone_plate_material,
                                                                           self.zone_plate_thickness)
                y_values = numpy.round(100.0*y_values, 3)
    
                self.plot_canvas[5].addCurve(x_values, y_values, "Efficiency vs Energy", symbol='', color='blue', replace=True)
            else:
                if not self.plot_canvas[5] is None: self.plot_canvas[5].clear()

            if self.thickness_plot == 1:
                if self.plot_canvas[6] is None:
                    self.plot_canvas[6] = oasysgui.plotWindow(roi=False, control=False, position=True, logScale=False)
                    self.tab[6].layout().addWidget(self.plot_canvas[6] )
    
                self.plot_canvas[6].setDefaultPlotLines(True)
                self.plot_canvas[6].setActiveCurveColor(color='blue')
    
                self.plot_canvas[6].setGraphTitle('Energy: ' + str(round(ShadowPhysics.getEnergyFromWavelength(self.avg_wavelength*10), 3)) + " eV")
                self.plot_canvas[6].getXAxis().setLabel('Thickness [nm]')
                self.plot_canvas[6].getYAxis().setLabel('Efficiency [%]')
    
                x_values = numpy.linspace(self.thickness_from, self.thickness_to, 100)
                y_values = numpy.zeros(100)
    
                for index in range(len(x_values)):
                    y_values[index], _, _ = ZonePlate.calculate_efficiency(self.avg_wavelength,
                                                                           self.zone_plate_material,
                                                                           x_values[index])
                y_values = numpy.round(100*y_values, 3)
    
                self.plot_canvas[6].addCurve(x_values, y_values, "Efficiency vs Thickness", symbol='', color='blue', replace=True)
            else:
                if not self.plot_canvas[6] is None: self.plot_canvas[6].clear()

        else:
            if not self.plot_canvas[5] is None: self.plot_canvas[5].clear()
            if not self.plot_canvas[6] is None: self.plot_canvas[6].clear()

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.traceOpticalElement()

    def checkFields(self):
        self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
        self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

        congruence.checkStrictlyPositiveNumber(self.delta_rn, u"\u03B4" + "rn" )
        congruence.checkStrictlyPositiveNumber(self.diameter, "Z.P. Diameter")
        if (self.source_distance_flag == 1):
            congruence.checkPositiveNumber(self.source_distance, "Source Distance" )

        if self.type_of_zp == PHASE_ZP:
            congruence.checkEmptyString(self.zone_plate_material, "Zone Plate Material")
            congruence.checkStrictlyPositiveNumber(self.zone_plate_thickness, "Zone Plate Thickness")
            congruence.checkEmptyString(self.substrate_material, "Substrate Material")
            congruence.checkStrictlyPositiveNumber(self.substrate_thickness, "Substrate Thickness")
            
  
    def after_change_workspace_units(self):
        label = self.le_source_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_image_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        label = self.le_source_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_focal_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_image_position.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        # ADVANCED SETTINGS
        # MIRROR MOVEMENTS
        label = self.le_mm_mirror_offset_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_mm_mirror_offset_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_mm_mirror_offset_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        # SOURCE MOVEMENTS
        label = self.le_sm_distance_from_mirror.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_sm_offset_x_mirr_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset X [" + self.workspace_units_label + "] in O.E. reference frame")
        label = self.le_sm_offset_y_mirr_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Y [" + self.workspace_units_label + "] in O.E. reference frame")
        label = self.le_sm_offset_z_mirr_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Z [" + self.workspace_units_label + "] in O.E. reference frame")
        label = self.le_sm_offset_x_source_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset X [" + self.workspace_units_label + "] in SOURCE reference frame")
        label = self.le_sm_offset_y_source_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Y [" + self.workspace_units_label + "] in SOURCE reference frame")
        label = self.le_sm_offset_z_source_ref_frame.parent().layout().itemAt(0).widget()
        label.setText("offset Z [" + self.workspace_units_label + "] in SOURCE reference frame")

    def callResetSettings(self):
        super().callResetSettings()
        self.setupUI()

    def set_SourceMovement(self):
        self.sou_mov_box_1.setVisible(self.source_movement == 1)

    def set_MirrorMovement(self):
        self.mir_mov_box_1.setVisible(self.mirror_movement == 1)

    def set_SourceDistanceFlag(self):
        self.zp_box_1.setVisible(self.source_distance_flag == 1)
        self.zp_box_2.setVisible(self.source_distance_flag == 0)

    def set_TypeOfZP(self):
        self.zp_box_3.setVisible(self.type_of_zp == PHASE_ZP)


    ######################################################################
    # ZONE PLATE CALCULATION
    ######################################################################

    def get_zone_plate_beam(self):       # WS Units

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element._oe.DUMMY        = self.workspace_units_to_cm
        empty_element._oe.T_SOURCE     = self.source_plane_distance
        empty_element._oe.T_IMAGE      = 0.0
        empty_element._oe.T_INCIDENCE  = 0.0
        empty_element._oe.T_REFLECTION = 180.0
        empty_element._oe.ALPHA        = 0.0

        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = 0.0
        rx_slit[0] = self.diameter*1e-6/self.workspace_units_to_m
        rz_slit[0] = self.diameter*1e-6/self.workspace_units_to_m
        cx_slit[0] = 0.0
        cz_slit[0] = 0.0

        empty_element._oe.set_screens(n_screen,
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
                                      file_scr_ext)

        output_beam = ShadowBeam.traceFromOE(self.input_beam, empty_element, history=True)

        go = numpy.where(output_beam._beam.rays[:, 9] == GOOD)
        lo = numpy.where(output_beam._beam.rays[:, 9] != GOOD)

        print("Zone Plate Beam: ", "GO", len(go[0]), "LO", len(lo[0]))

        return output_beam

    def get_output_beam(self, focused_beam):

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element._oe.DUMMY = 1.0 # self.workspace_units_to_cm

        empty_element._oe.T_SOURCE     = 0.0
        empty_element._oe.T_IMAGE      = self.image_plane_distance
        empty_element._oe.T_INCIDENCE  = 0.0
        empty_element._oe.T_REFLECTION = 180.0
        empty_element._oe.ALPHA        = 0.0

        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0

        return ShadowBeam.traceFromOE(focused_beam, empty_element, history=True)

    # ALGORITHM EXTRACTED FROM webAbsorb.py by 11BM - Argonne National Laboratory
    @classmethod
    def get_material_density(cls, material):
        elements = ChemicalFormulaParser.parse_formula(material)
        
        mass = 0.0
        volume = 0.0
        
        for element in elements:
            mass += element._molecular_weight*element._n_atoms
            volume += 10.*element._n_atoms
                    
        rho = mass/(0.602*volume) 
    
        return rho
    
    @classmethod  
    def get_material_weight_factor(cls, shadow_rays, material, thickness):
        mu = numpy.zeros(len(shadow_rays))
        
        for i in range(0, len(mu)):
            mu[i] = xraylib.CS_Total_CP(material, ShadowPhysics.getEnergyFromShadowK(shadow_rays[i, 10])/1000) # energy in KeV
        
        rho = ZonePlate.get_material_density(material)
                    
        return numpy.sqrt(numpy.exp(-mu*rho*thickness*1e-7)) # thickness in CM
        
    
    @classmethod  
    def get_delta_beta(cls, shadow_rays, material):
        beta = numpy.zeros(len(shadow_rays))
        delta = numpy.zeros(len(shadow_rays))
        density = xraylib.ElementDensity(xraylib.SymbolToAtomicNumber(material))
    
        for i in range(0, len(shadow_rays)):
            energy_in_KeV = ShadowPhysics.getEnergyFromShadowK(shadow_rays[i, 10])/1000
            delta[i] = (1-xraylib.Refractive_Index_Re(material, energy_in_KeV, density))
            beta[i]  = xraylib.Refractive_Index_Im(material, energy_in_KeV, density)
    
        return delta, beta 
    
    @classmethod
    def analyze_zone(cls, zones, focused_beam, p_zp, workspace_units_to_m):
        to_analyze = numpy.where(focused_beam._beam.rays[:, 9] == LOST_ZP)

        candidate_rays = copy.deepcopy(focused_beam._beam.rays[to_analyze])

        if len(candidate_rays) > 0:
            xp = candidate_rays[:, 3]
            zp = candidate_rays[:, 5]

            is_collimated = (numpy.max(numpy.abs(xp)) < 1e-9 and numpy.max(numpy.abs(zp)) < 1e-9)

            if is_collimated and not p_zp*workspace_units_to_m > COLLIMATED_SOURCE_LIMIT:
                raise ValueError("Beam is collimated, Source Distance should be set to infinite ('Different' and > 10 Km)")

            r = numpy.sqrt(candidate_rays[:, 0]**2 + candidate_rays[:, 2]**2)

            for zone in zones:
                t = numpy.where(numpy.logical_and(r >= zone[0], r <= zone[1]))

                intercepted_rays_f = candidate_rays[t]

                if len(intercepted_rays_f) > 0:
                    xp_int = intercepted_rays_f[:, 3]
                    zp_int = intercepted_rays_f[:, 5]

                    k_mod_int = intercepted_rays_f[:, 10] # CM-1

                    k_x_int = k_mod_int*xp_int # CM-1
                    k_z_int = k_mod_int*zp_int # CM-1

                    # (see formulas in A.G. Michette, "X-ray science and technology"
                    #  Institute of Physics Publishing (1993))
                    # par. 8.6, pg. 332-337
                    x_int_f = intercepted_rays_f[:, 0] # WS Units
                    z_int_f = intercepted_rays_f[:, 2] # WS Units

                    r_int = numpy.sqrt((x_int_f)**2 + (z_int_f)**2) # WS Units

                    d = (zone[1] - zone[0])*workspace_units_to_m*100  # to CM

                    # computing G (the "grating" wavevector in workspace units^-1)
                    gx = -(numpy.pi / d) * x_int_f/r_int
                    gz = -(numpy.pi / d) * z_int_f/r_int

                    k_x_out = k_x_int + gx
                    k_z_out = k_z_int + gz

                    k_y_out = numpy.sqrt(k_mod_int**2 - (k_z_out**2 + k_x_out**2)) # keep energy of the photon constant

                    xp_out = k_x_out / k_mod_int
                    yp_out = k_y_out / k_mod_int
                    zp_out = k_z_out / k_mod_int

                    candidate_rays[t, 3] = xp_out
                    candidate_rays[t, 4] = yp_out
                    candidate_rays[t, 5] = zp_out
                    candidate_rays[t, 9] = GOOD_ZP

            focused_beam._beam.rays[to_analyze] = candidate_rays

    @classmethod
    def apply_fresnel_zone_plate(cls, 
                                 zone_plate_beam,
                                 type_of_zp, 
                                 diameter, 
                                 delta_rn,                              
                                 substrate_material, 
                                 substrate_thickness,
                                 zone_plate_material,
                                 zone_plate_thickness,
                                 source_distance,
                                 workspace_units_to_m):
        
        max_zones_number = int(diameter*1000/(4*delta_rn))

        focused_beam = zone_plate_beam.duplicate(history=True)

        go = numpy.where(focused_beam._beam.rays[:, 9] == GOOD)

        if type_of_zp == PHASE_ZP: 
            substrate_weight_factor = ZonePlate.get_material_weight_factor(focused_beam._beam.rays[go], substrate_material, substrate_thickness)
        
            focused_beam._beam.rays[go, 6] = focused_beam._beam.rays[go, 6]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 7] = focused_beam._beam.rays[go, 7]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 8] = focused_beam._beam.rays[go, 8]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 15] = focused_beam._beam.rays[go, 15]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 16] = focused_beam._beam.rays[go, 16]*substrate_weight_factor[:]
            focused_beam._beam.rays[go, 17] = focused_beam._beam.rays[go, 17]*substrate_weight_factor[:]
        
        clear_zones = []
        dark_zones = []
        r_zone_i_previous = 0.0
        for i in range(1, max_zones_number+1):
            r_zone_i = numpy.sqrt(i*diameter*1e-6*delta_rn*1e-9)/workspace_units_to_m # to workspace unit
            if i % 2 == 0: clear_zones.append([r_zone_i_previous, r_zone_i])
            else: dark_zones.append([r_zone_i_previous, r_zone_i])
            r_zone_i_previous = r_zone_i
               
        focused_beam._beam.rays[go, 9] = LOST_ZP
        
        ZonePlate.analyze_zone(clear_zones, focused_beam, source_distance, workspace_units_to_m)
        if type_of_zp == PHASE_ZP: ZonePlate.analyze_zone(dark_zones, focused_beam, source_distance, workspace_units_to_m)
    
        go_2 = numpy.where(focused_beam._beam.rays[:, 9] == GOOD_ZP)

        intensity_go_2 = numpy.sum(focused_beam._beam.rays[go_2, 6] ** 2 + focused_beam._beam.rays[go_2, 7] ** 2 + focused_beam._beam.rays[go_2, 8] ** 2 + \
                                   focused_beam._beam.rays[go_2, 15] ** 2 + focused_beam._beam.rays[go_2, 16] ** 2 + focused_beam._beam.rays[go_2, 17] ** 2)

        if type_of_zp == PHASE_ZP:
            wavelength = ShadowPhysics.getWavelengthFromShadowK(focused_beam._beam.rays[go_2, 10])*1e-1 # nm
            delta, beta = ZonePlate.get_delta_beta(focused_beam._beam.rays[go_2], zone_plate_material)
            
            phi = 2*numpy.pi*zone_plate_thickness*delta/wavelength
            rho = beta/delta
               
            efficiency_zp = (1/(numpy.pi**2))*(1 + numpy.exp(-2*rho*phi) - (2*numpy.exp(-rho*phi)*numpy.cos(phi)))
            efficiency_weight_factor = numpy.sqrt(efficiency_zp)

        elif type_of_zp == AMPLITUDE_ZP:
            lo_2 = numpy.where(focused_beam._beam.rays[:, 9] == LOST_ZP)

            intensity_lo_2 = numpy.sum(focused_beam._beam.rays[lo_2, 6] ** 2 + focused_beam._beam.rays[lo_2, 7] ** 2 + focused_beam._beam.rays[lo_2, 8] ** 2 + \
                                       focused_beam._beam.rays[lo_2, 15] ** 2 + focused_beam._beam.rays[lo_2, 16] ** 2 + focused_beam._beam.rays[lo_2, 17] ** 2)

            efficiency_zp = numpy.ones(len(focused_beam._beam.rays[go_2]))/(numpy.pi**2)
            efficiency_weight_factor = numpy.sqrt(efficiency_zp*(1 + (intensity_lo_2/intensity_go_2)))

        focused_beam._beam.rays[go_2, 6]  = focused_beam._beam.rays[go_2, 6]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 7]  = focused_beam._beam.rays[go_2, 7]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 8]  = focused_beam._beam.rays[go_2, 8]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 15] = focused_beam._beam.rays[go_2, 15]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 16] = focused_beam._beam.rays[go_2, 16]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 17] = focused_beam._beam.rays[go_2, 17]*efficiency_weight_factor[:]
        focused_beam._beam.rays[go_2, 9] = GOOD

        return focused_beam, max_zones_number

    @classmethod
    def calculate_efficiency(cls, wavelength, zone_plate_material, zone_plate_thickness):
        energy_in_KeV = ShadowPhysics.getEnergyFromWavelength(wavelength*10)/1000

        density = xraylib.ElementDensity(xraylib.SymbolToAtomicNumber(zone_plate_material))
        delta   = (1-xraylib.Refractive_Index_Re(zone_plate_material, energy_in_KeV, density))
        beta    = xraylib.Refractive_Index_Im(zone_plate_material, energy_in_KeV, density)
        phi     = 2*numpy.pi*zone_plate_thickness*delta/wavelength
        rho     = beta/delta

        efficiency     = (1/(numpy.pi**2))*(1 + numpy.exp(-2*rho*phi)      - (2*numpy.exp(-rho*phi)*numpy.cos(phi)))
        max_efficiency = (1/(numpy.pi**2))*(1 + numpy.exp(-2*rho*numpy.pi) + (2*numpy.exp(-rho*numpy.pi)))
        thickness_max_efficiency = numpy.round(wavelength/(2*delta), 2)

        return efficiency, max_efficiency, thickness_max_efficiency

    def getTitles(self):
        titles = super().getTitles()
        titles.append("Efficiency vs. Energy")
        titles.append("Efficiency vs. Thickness")

        return titles
