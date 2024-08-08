
import os
import sys
from scipy.optimize import root

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QDialog, QWidget, QLabel, QSizePolicy, QFileDialog
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap

from matplotlib import cm
from oasys.widgets.gui import FigureCanvas3D
from matplotlib.figure import Figure
try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

import xraylib

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.exchange import DataExchangeObject
from oasys.util.oasys_util import EmittingStream, TTYGrabber, TriggerIn, TriggerOut
import oasys.util.oasys_util as OU
import orangecanvas.resources as resources

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, ShadowOpticalElement, ShadowBeam, ShadowFile
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPhysics, ShadowPreProcessor
from orangecontrib.shadow.widgets.gui import ow_generic_element
from srxraylib.metrology import profiles_simulation

from syned.widget.widget_decorator import WidgetDecorator

import syned.beamline.beamline as synedb
from syned.beamline.optical_elements.absorbers import beam_stopper, slit, filter
from syned.beamline.optical_elements.ideal_elements import screen
from syned.beamline.optical_elements.mirrors import mirror
from syned.beamline.optical_elements.crystals import crystal
from syned.beamline.optical_elements.gratings import grating
from syned.beamline.shape import *

from Shadow import ShadowTools as ST

shadow_oe_to_copy = None

class GraphicalOptions:
    is_empty = False
    is_curved = False
    is_mirror=False
    is_screen_slit=False
    is_crystal=False
    is_grating=False
    is_spheric= False
    is_ellipsoidal=False
    is_toroidal=False
    is_paraboloid=False
    is_hyperboloid=False
    is_cone=False
    is_codling_slit=False
    is_polynomial=False
    is_conic_coefficients=False
    is_refractor=False
    is_ideal_lens = False

    def __init__(self,
                 is_empty = False,
                 is_curved=False,
                 is_mirror=False,
                 is_crystal=False,
                 is_grating=False,
                 is_screen_slit=False,
                 is_spheric=False,
                 is_ellipsoidal=False,
                 is_toroidal=False,
                 is_paraboloid=False,
                 is_hyperboloid=False,
                 is_cone=False,
                 is_codling_slit=False,
                 is_polynomial=False,
                 is_conic_coefficients=False,
                 is_refractor=False,
                 is_ideal_lens=False):
        self.is_empty = is_empty
        self.is_curved = is_curved
        self.is_mirror=is_mirror
        self.is_crystal=is_crystal
        self.is_grating=is_grating
        self.is_screen_slit=is_screen_slit
        self.is_spheric=is_spheric
        self.is_ellipsoidal=is_ellipsoidal
        self.is_toroidal=is_toroidal
        self.is_paraboloid=is_paraboloid
        self.is_hyperboloid=is_hyperboloid
        self.is_cone=is_cone
        self.is_codling_slit=is_codling_slit
        self.is_polynomial=is_polynomial
        self.is_conic_coefficients=is_conic_coefficients
        self.is_refractor=is_refractor
        self.is_ideal_lens=is_ideal_lens

class OpticalElement(ow_generic_element.GenericElement, WidgetDecorator):

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("Trigger", TriggerOut, "sendNewBeam"),
              ("PreProcessor Data #1", ShadowPreProcessorData, "setPreProcessorData"),
              ("PreProcessor Data #2", ShadowPreProcessorData, "setPreProcessorData"),
              ("ExchangeData", DataExchangeObject, "acceptExchangeData")
             ]

    WidgetDecorator.append_syned_input_data(inputs)

    send_footprint_beam = QSettings().value("output/send-footprint", 0, int) == 1

    if send_footprint_beam:
        outputs = [{"name":"Beam",
                    "type":ShadowBeam,
                    "doc":"Shadow Beam",
                    "id":"beam"},
                   {"name":"Footprint",
                    "type":list,
                    "doc":"Footprint",
                    "id":"beam"},
                   {"name":"Trigger",
                    "type": TriggerIn,
                    "doc":"Feedback signal to start a new beam simulation",
                    "id":"Trigger"}]
    else:
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

    graphical_options=None

    source_plane_distance = Setting(10.0)
    image_plane_distance = Setting(20.0)

    angles_respect_to = Setting(0)

    incidence_angle_deg = Setting(88.0)
    incidence_angle_mrad = Setting(0.0)
    reflection_angle_deg = Setting(88.0)
    reflection_angle_mrad = Setting(0.0)
    mirror_orientation_angle = Setting(0)
    mirror_orientation_angle_user_value = Setting(0.0)

    ##########################################
    # BASIC SETTING
    ##########################################

    conic_coefficient_0 = Setting(0.0)
    conic_coefficient_1 = Setting(0.0)
    conic_coefficient_2 = Setting(0.0)
    conic_coefficient_3 = Setting(0.0)
    conic_coefficient_4 = Setting(0.0)
    conic_coefficient_5 = Setting(0.0)
    conic_coefficient_6 = Setting(0.0)
    conic_coefficient_7 = Setting(0.0)
    conic_coefficient_8 = Setting(0.0)
    conic_coefficient_9 = Setting(0.0)

    surface_shape_parameters = Setting(0)
    spherical_radius = Setting(0.0)

    torus_major_radius = Setting(0.0)
    torus_minor_radius = Setting(0.0)
    toroidal_mirror_pole_location=Setting(0)

    ellipse_hyperbola_semi_major_axis=Setting(0.0)
    ellipse_hyperbola_semi_minor_axis=Setting(0.0)
    angle_of_majax_and_pole=Setting(0.0)

    paraboloid_parameter=Setting(0.0)
    focus_location=Setting(0.0)

    focii_and_continuation_plane = Setting(0)

    object_side_focal_distance = Setting(0.0)
    image_side_focal_distance = Setting(0.0)

    incidence_angle_respect_to_normal_type = Setting(0)
    incidence_angle_respect_to_normal = Setting(0.0)

    surface_curvature = Setting(0)
    is_cylinder = Setting(1)
    cylinder_orientation = Setting(0)
    reflectivity_type = Setting(0)
    source_of_reflectivity = Setting(0)
    file_prerefl = Setting("reflec.dat")
    alpha = Setting(0.0)
    gamma = Setting(0.0)
    file_prerefl_m = Setting("reflec.dat")
    m_layer_tickness = Setting(0.0)

    file_reflectivity      = Setting("reflectivity.dat")
    user_defined_file_type = Setting(0)
    user_defined_angle_units = Setting(0)
    user_defined_energy_units = Setting(0)

    is_infinite = Setting(0)
    mirror_shape = Setting(0)
    dim_x_plus = Setting(0.0)
    dim_x_minus = Setting(0.0)
    dim_y_plus = Setting(0.0)
    dim_y_minus = Setting(0.0)

    diffraction_geometry = Setting(0)
    diffraction_calculation = Setting(0)
    file_diffraction_profile = Setting("diffraction_profile.dat")

    CRYSTALS = xraylib.Crystal_GetCrystalsList()

    user_defined_bragg_angle = Setting(14.223)
    user_defined_crystal = Setting(32)
    user_defined_h = Setting(1)
    user_defined_k = Setting(1)
    user_defined_l = Setting(1)
    user_defined_asymmetry_angle = Setting(0.0)
    file_crystal_parameters = Setting("bragg.dat")
    crystal_auto_setting = Setting(0)
    units_in_use = Setting(0)
    photon_energy = Setting(5.0)
    photon_wavelength = Setting(5000.0)

    mosaic_crystal = Setting(0)
    angle_spread_FWHM = Setting(0.0)
    thickness = Setting(0.0)
    seed_for_mosaic = Setting(1626261131)

    johansson_geometry = Setting(0)
    johansson_radius = Setting(0.0)

    asymmetric_cut = Setting(0)
    planes_angle = Setting(0.0)
    below_onto_bragg_planes = Setting(-1)

    grating_diffraction_order = Setting(-1)
    grating_auto_setting = Setting(0)
    grating_units_in_use = Setting(0)
    grating_photon_energy = Setting(5.0)
    grating_photon_wavelength = Setting(5000.0)

    grating_ruling_type = Setting(0)
    grating_ruling_density = Setting(12000.0)

    grating_holo_left_distance = Setting(300.0)
    grating_holo_left_incidence_angle = Setting(-20.0)
    grating_holo_left_azimuth_from_y = Setting(0.0)
    grating_holo_right_distance = Setting(300.0)
    grating_holo_right_incidence_angle = Setting(-20.0)
    grating_holo_right_azimuth_from_y = Setting(0.0)
    grating_holo_pattern_type = Setting(0)
    grating_holo_source_type = Setting(0)
    grating_holo_cylindrical_source = Setting(0)
    grating_holo_recording_wavelength = Setting(4879.86)

    grating_groove_pole_distance = Setting(0.0)
    grating_groove_pole_azimuth_from_y = Setting(0.0)
    grating_coma_correction_factor = Setting(0.0)

    grating_poly_coeff_1 = Setting(0.0)
    grating_poly_coeff_2 = Setting(0.0)
    grating_poly_coeff_3 = Setting(0.0)
    grating_poly_coeff_4 = Setting(0.0)
    grating_poly_signed_absolute = Setting(1)

    grating_mount_type = Setting(0)

    grating_hunter_blaze_angle = Setting(0.0)
    grating_hunter_grating_selected = Setting(0)
    grating_hunter_monochromator_length = Setting(0.0)
    grating_hunter_distance_between_beams = Setting(0.0)

    grating_use_efficiency = Setting(0)
    grating_file_efficiency = Setting("efficiency.dat")

    optical_constants_refraction_index = Setting(0)
    refractive_index_in_object_medium = Setting(0.0)
    attenuation_in_object_medium = Setting(0.0)
    file_prerefl_for_object_medium = Setting("NONE SPECIFIED")
    refractive_index_in_image_medium = Setting(0.0)
    attenuation_in_image_medium = Setting(0.0)
    file_prerefl_for_image_medium = Setting("NONE SPECIFIED")

    ##########################################
    # ADVANCED SETTING
    ##########################################

    modified_surface = Setting(0)

    # surface error
    ms_type_of_defect = Setting(0)
    ms_defect_file_name = Setting(NONE_SPECIFIED)
    ms_ripple_wavel_x = Setting(0.0)
    ms_ripple_wavel_y = Setting(0.0)
    ms_ripple_ampli_x = Setting(0.0)
    ms_ripple_ampli_y = Setting(0.0)
    ms_ripple_phase_x = Setting(0.0)
    ms_ripple_phase_y = Setting(0.0)

    # faceted surface
    ms_file_facet_descr = Setting(NONE_SPECIFIED)
    ms_lattice_type = Setting(0)
    ms_orientation = Setting(0)
    ms_intercept_to_use = Setting(0)
    ms_facet_width_x = Setting(10.0)
    ms_facet_phase_x = Setting(0.0)
    ms_dead_width_x_minus = Setting(0.0)
    ms_dead_width_x_plus = Setting(0.0)
    ms_facet_width_y = Setting(10.0)
    ms_facet_phase_y = Setting(0.0)
    ms_dead_width_y_minus = Setting(0.0)
    ms_dead_width_y_plus = Setting(0.0)

    # surface roughness
    ms_file_surf_roughness = Setting(NONE_SPECIFIED)
    ms_roughness_rms_x = Setting(0.0)
    ms_roughness_rms_y = Setting(0.0)

    # kumakhov lens
    ms_specify_rz2 = Setting(0)
    ms_file_with_parameters_rz = Setting(NONE_SPECIFIED)
    ms_file_with_parameters_rz2 = Setting(NONE_SPECIFIED)
    ms_save_intercept_bounces = Setting(0)

    # segmented mirror
    ms_number_of_segments_x = Setting(1)
    ms_number_of_segments_y = Setting(1)
    ms_length_of_segments_x = Setting(0.0)
    ms_length_of_segments_y = Setting(0.0)
    ms_file_orientations = Setting(NONE_SPECIFIED)
    ms_file_polynomial = Setting(NONE_SPECIFIED)

    #####

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

    file_to_write_out = Setting(1) # Mirror: users found difficoult to activate the "Footprint" option.
    write_out_inc_ref_angles = Setting(0)

    ##########################################
    # DCM UTILITY
    ##########################################

    vertical_quote = Setting(0.0)
    total_distance = Setting(0.0)
    twotheta_bragg = Setting(0.0)

    d_1 = 0.0
    d_2 = 0.0

    image_path              = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "distances.png")
    bragg_user_defined_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "bragg_user_defined.png")

    ##########################################
    # SCREEN/SLIT SETTING
    ##########################################

    aperturing = Setting(0)
    open_slit_solid_stop = Setting(0)
    aperture_shape = Setting(0)
    slit_width_xaxis = Setting(0.0)
    slit_height_zaxis = Setting(0.0)
    slit_center_xaxis = Setting(0.0)
    slit_center_zaxis = Setting(0.0)
    external_file_with_coordinate=Setting(NONE_SPECIFIED)
    absorption = Setting(0)
    thickness = Setting(0.0)
    opt_const_file_name = Setting(NONE_SPECIFIED)


    not_interactive = False

    ##########################################
    # IDEAL LENS SETTING
    ##########################################

    focal_x = Setting(0.0)
    focal_z = Setting(0.0)

    want_main_area=1

    def __init__(self, graphical_options = GraphicalOptions()):
        super().__init__()

        self.runaction = widget.OWAction("Copy O.E. Parameters", self)
        self.runaction.triggered.connect(self.copy_oe_parameters)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Paste O.E. Parameters", self)
        self.runaction.triggered.connect(self.paste_oe_parameters)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Run Shadow/Trace", self)
        self.runaction.triggered.connect(self.traceOpticalElement)
        self.addAction(self.runaction)

        self.graphical_options = graphical_options

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
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT-5)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_pos = oasysgui.createTabPage(tabs_setting, "Position")

        self.orientation_box = oasysgui.widgetBox(tab_pos, "Optical Element Orientation", addSpace=False, orientation="vertical")

        self.le_source_plane_distance = oasysgui.lineEdit(self.orientation_box, self, "source_plane_distance", "Source Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_image_plane_distance  = oasysgui.lineEdit(self.orientation_box, self, "image_plane_distance", "Image Plane Distance", labelWidth=260, valueType=float, orientation="horizontal")

        # graph tab
        if not self.graphical_options.is_empty:
            tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        if not self.graphical_options.is_ideal_lens:
            tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        ##########################################
        ##########################################
        # ADVANCED SETTINGS
        ##########################################
        ##########################################

        if not self.graphical_options.is_ideal_lens:
            tabs_advanced_setting = oasysgui.tabWidget(tab_adv)

            if not (self.graphical_options.is_empty or self.graphical_options.is_screen_slit):
                tab_adv_mod_surf = oasysgui.createTabPage(tabs_advanced_setting, "Modified Surface")

                ##########################################
                #
                # TAB 2.2 - Mirror Movement
                #
                ##########################################

                tab_adv_mir_mov = oasysgui.createTabPage(tabs_advanced_setting, "O.E. Movement")

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

            tab_adv_sou_mov = oasysgui.createTabPage(tabs_advanced_setting, "Source Movement")

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
            tab_adv_misc = oasysgui.createTabPage(tabs_advanced_setting, "Output Files")

            adv_other_box = oasysgui.widgetBox(tab_adv_misc, "Optional file output", addSpace=False, orientation="vertical")

            gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=150,
                         items=["All", "Mirror", "Image", "None", "Debug (All + start.xx/end.xx)"],
                         sendSelectedValue=False, orientation="horizontal", callback=self.set_Footprint)

            gui.comboBox(adv_other_box, self, "write_out_inc_ref_angles", label="Write out Incident/Reflected angles [angle.xx]", labelWidth=300,
                         items=["No", "Yes"],
                         sendSelectedValue=False, orientation="horizontal")

        self.set_Footprint()


        if self.graphical_options.is_screen_slit:
            box_aperturing = oasysgui.widgetBox(tab_bas, "Screen/Slit Shape", addSpace=False, orientation="vertical", height=240)

            gui.comboBox(box_aperturing, self, "aperturing", label="Aperturing", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_Aperturing, sendSelectedValue=False, orientation="horizontal")

            gui.separator(box_aperturing, width=self.INNER_BOX_WIDTH_L0)

            self.box_aperturing_shape = oasysgui.widgetBox(box_aperturing, "", addSpace=False, orientation="vertical")

            gui.comboBox(self.box_aperturing_shape, self, "open_slit_solid_stop", label="Open slit/Solid stop", labelWidth=260,
                         items=["aperture/slit", "obstruction/stop"],
                         sendSelectedValue=False, orientation="horizontal")

            gui.comboBox(self.box_aperturing_shape, self, "aperture_shape", label="Aperture shape", labelWidth=260,
                         items=["Rectangular", "Ellipse", "External"],
                         callback=self.set_ApertureShape, sendSelectedValue=False, orientation="horizontal")


            self.box_aperturing_shape_1 = oasysgui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="horizontal")


            self.le_external_file_with_coordinate = oasysgui.lineEdit(self.box_aperturing_shape_1, self, "external_file_with_coordinate", "External file with coordinate", labelWidth=185, valueType=str, orientation="horizontal")

            gui.button(self.box_aperturing_shape_1, self, "...", callback=self.selectExternalFileWithCoordinate)

            self.box_aperturing_shape_2 = oasysgui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="vertical")

            self.le_slit_width_xaxis  = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_width_xaxis", "Slit width/x-axis", labelWidth=260, valueType=float, orientation="horizontal")
            self.le_slit_height_zaxis = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_height_zaxis", "Slit height/z-axis", labelWidth=260, valueType=float, orientation="horizontal")
            self.le_slit_center_xaxis = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_center_xaxis", "Slit center/x-axis", labelWidth=260, valueType=float, orientation="horizontal")
            self.le_slit_center_zaxis = oasysgui.lineEdit(self.box_aperturing_shape_2, self, "slit_center_zaxis", "Slit center/z-axis", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_Aperturing()

            box_absorption = oasysgui.widgetBox(tab_bas, "Absorption Parameters", addSpace=False, orientation="vertical", height=130)

            gui.comboBox(box_absorption, self, "absorption", label="Absorption", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_Absorption, sendSelectedValue=False, orientation="horizontal")

            gui.separator(box_absorption, width=self.INNER_BOX_WIDTH_L0)

            self.box_absorption_1 = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")
            self.box_absorption_1_empty = oasysgui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")

            self.le_thickness = oasysgui.lineEdit(self.box_absorption_1, self, "thickness", "Thickness", labelWidth=300, valueType=float, orientation="horizontal")

            file_box = oasysgui.widgetBox(self.box_absorption_1, "", addSpace=False, orientation="horizontal", height=25)

            self.le_opt_const_file_name = oasysgui.lineEdit(file_box, self, "opt_const_file_name", "Opt. const. file name", labelWidth=130, valueType=str, orientation="horizontal")

            gui.button(file_box, self, "...", callback=self.selectOptConstFileName)

            self.set_Absorption()
        elif self.graphical_options.is_ideal_lens:
            box_focus = oasysgui.widgetBox(tab_bas, "Ideal Lens Setting", addSpace=False, orientation="vertical")

            self.le_focal_x = oasysgui.lineEdit(box_focus, self, "focal_x", "Focal Distance X", labelWidth=260, valueType=float, orientation="horizontal")
            self.le_focal_z = oasysgui.lineEdit(box_focus, self, "focal_z", "Focal Distance Z", labelWidth=260, valueType=float, orientation="horizontal")
        else:
            gui.comboBox(self.orientation_box, self, "angles_respect_to", label="Angles in [deg] with respect to the", labelWidth=250,
                         items=["Normal", "Surface"],
                         callback=self.set_AnglesRespectTo,
                         sendSelectedValue=False, orientation="horizontal")

            self.incidence_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_deg", "Incident Angle\nwith respect to the Normal [deg]", labelWidth=220, callback=self.calculate_incidence_angle_mrad, valueType=float, orientation="horizontal")
            self.incidence_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "incidence_angle_mrad", "Incident Angle\nwith respect to the surface [mrad]", labelWidth=220, callback=self.calculate_incidence_angle_deg, valueType=float, orientation="horizontal")
            self.reflection_angle_deg_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_deg", "Reflection Angle\nwith respect to the Normal [deg]", labelWidth=220, callback=self.calculate_reflection_angle_mrad, valueType=float, orientation="horizontal")
            self.reflection_angle_rad_le = oasysgui.lineEdit(self.orientation_box, self, "reflection_angle_mrad", "Reflection Angle\nwith respect to the surface [mrad]", labelWidth=220, callback=self.calculate_reflection_angle_deg, valueType=float, orientation="horizontal")

            self.set_AnglesRespectTo()

            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            if self.graphical_options.is_mirror:
                self.reflection_angle_deg_le.setEnabled(False)
                self.reflection_angle_rad_le.setEnabled(False)

            gui.comboBox(self.orientation_box, self, "mirror_orientation_angle", label="O.E. Orientation Angle [deg]", labelWidth=390,
                         items=[0, 90, 180, 270, "Other value..."],
                         valueType=float,
                         sendSelectedValue=False, orientation="horizontal",callback=self.mirror_orientation_angle_user,)
            self.mirror_orientation_angle_user_value_le = oasysgui.widgetBox(self.orientation_box, "", addSpace=False, orientation="vertical")
            oasysgui.lineEdit(self.mirror_orientation_angle_user_value_le, self, "mirror_orientation_angle_user_value",
                                                             "O.E. Orientation Angle [deg]",
                                                             labelWidth=220,
                                                             valueType=float, orientation="horizontal")

            if not self.graphical_options.is_empty:
                if self.graphical_options.is_crystal:
                    tab_dcm = oasysgui.createTabPage(tabs_setting, "D.C.M. Utility")

                self.tabs_basic_setting = oasysgui.tabWidget(tab_bas)

                tabs_basic_setting = self.tabs_basic_setting

                if self.graphical_options.is_curved: tab_bas_shape = oasysgui.createTabPage(tabs_basic_setting, "Surface Shape")
                if self.graphical_options.is_mirror: tab_bas_refl = oasysgui.createTabPage(tabs_basic_setting, "Reflectivity")
                elif self.graphical_options.is_crystal: tab_bas_crystal = oasysgui.createTabPage(tabs_basic_setting, "Crystal")
                elif self.graphical_options.is_grating: tab_bas_grating = oasysgui.createTabPage(tabs_basic_setting, "Grating")
                elif self.graphical_options.is_refractor: tab_bas_refractor = oasysgui.createTabPage(tabs_basic_setting, "Refractor")
                tab_bas_dim = oasysgui.createTabPage(tabs_basic_setting, "Dimensions")

                ##########################################
                #
                # TAB 1.1 - SURFACE SHAPE
                #
                ##########################################


                if self.graphical_options.is_curved:
                    surface_box = oasysgui.widgetBox(tab_bas_shape, "Surface Shape Parameter", addSpace=False, orientation="vertical")

                    if self.graphical_options.is_conic_coefficients:
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_0", "c[1]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_1", "c[2]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_2", "c[3]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_3", "c[4]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_4", "c[5]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_5", "c[6]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_6", "c[7]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_7", "c[8]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_8", "c[9]", labelWidth=260, valueType=float, orientation="horizontal")
                        oasysgui.lineEdit(surface_box, self, "conic_coefficient_9", "c[10]", labelWidth=260, valueType=float, orientation="horizontal")
                    else:
                        gui.comboBox(surface_box, self, "surface_shape_parameters", label="Type", items=["internal/calculated", "external/user_defined"], labelWidth=240,
                                     callback=self.set_IntExt_Parameters, sendSelectedValue=False, orientation="horizontal")

                        self.surface_box_ext = oasysgui.widgetBox(surface_box, "", addSpace=False, orientation="vertical", height=150)
                        gui.separator(self.surface_box_ext)

                        if self.graphical_options.is_spheric:
                            self.le_spherical_radius = oasysgui.lineEdit(self.surface_box_ext, self, "spherical_radius", "Spherical Radius", labelWidth=260, valueType=float, orientation="horizontal")
                        elif self.graphical_options.is_toroidal:
                            self.le_torus_major_radius = oasysgui.lineEdit(self.surface_box_ext, self, "torus_major_radius", "Torus Major Radius", labelWidth=260, valueType=float, orientation="horizontal")
                            self.le_torus_minor_radius = oasysgui.lineEdit(self.surface_box_ext, self, "torus_minor_radius", "Torus Minor Radius", labelWidth=260, valueType=float, orientation="horizontal")
                        elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                            self.le_ellipse_hyperbola_semi_major_axis = oasysgui.lineEdit(self.surface_box_ext, self, "ellipse_hyperbola_semi_major_axis", "Ellipse/Hyperbola semi-major Axis",  labelWidth=260, valueType=float, orientation="horizontal")
                            self.le_ellipse_hyperbola_semi_minor_axis = oasysgui.lineEdit(self.surface_box_ext, self, "ellipse_hyperbola_semi_minor_axis", "Ellipse/Hyperbola semi-minor Axis", labelWidth=260, valueType=float, orientation="horizontal")
                            oasysgui.lineEdit(self.surface_box_ext, self, "angle_of_majax_and_pole", "Angle of MajAx and Pole [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
                        elif self.graphical_options.is_paraboloid:
                            self.le_paraboloid_parameter = oasysgui.lineEdit(self.surface_box_ext, self, "paraboloid_parameter", "Paraboloid parameter", labelWidth=260, valueType=float, orientation="horizontal")

                        self.surface_box_int = oasysgui.widgetBox(surface_box, "", addSpace=False, orientation="vertical", height=150)

                        gui.comboBox(self.surface_box_int, self, "focii_and_continuation_plane", label="Focii and Continuation Plane", labelWidth=280,
                                     items=["Coincident", "Different"], callback=self.set_FociiCont_Parameters, sendSelectedValue=False, orientation="horizontal")

                        self.surface_box_int_2 = oasysgui.widgetBox(self.surface_box_int, "", addSpace=False, orientation="vertical", width=self.INNER_BOX_WIDTH_L1-5)
                        self.surface_box_int_2_empty = oasysgui.widgetBox(self.surface_box_int, "", addSpace=False, orientation="vertical", width=self.INNER_BOX_WIDTH_L1-5)

                        self.w_object_side_focal_distance = oasysgui.lineEdit(self.surface_box_int_2, self, "object_side_focal_distance", "Object Side Focal Distance", labelWidth=260, valueType=float, orientation="horizontal")
                        self.w_image_side_focal_distance = oasysgui.lineEdit(self.surface_box_int_2, self, "image_side_focal_distance", "Image Side Focal Distance", labelWidth=260, valueType=float, orientation="horizontal")

                        gui.comboBox(self.surface_box_int_2, self, "incidence_angle_respect_to_normal_type", label="Incidence Angle", labelWidth=260,
                                         items=["Copied from position",
                                                "User value"],
                                         sendSelectedValue=False, orientation="horizontal", callback=self.set_incidenceAngleRespectToNormal)

                        self.surface_box_int_3 = oasysgui.widgetBox(self.surface_box_int_2, "", addSpace=False, orientation="vertical", height=25, width=self.INNER_BOX_WIDTH_L1-5)
                        self.surface_box_int_3_empty = oasysgui.widgetBox(self.surface_box_int_2, "", addSpace=False, orientation="vertical", height=25, width=self.INNER_BOX_WIDTH_L1-5)

                        self.w_incidence_angle_respect_to_normal = oasysgui.lineEdit(self.surface_box_int_3, self, "incidence_angle_respect_to_normal", "Incidence Angle Respect to Normal [deg]", labelWidth=260, valueType=float, orientation="horizontal")

                        self.set_incidenceAngleRespectToNormal()

                        if self.graphical_options.is_paraboloid:
                            gui.comboBox(self.surface_box_int, self, "focus_location", label="Focus location", labelWidth=220, items=["Image is at Infinity", "Source is at Infinity"], sendSelectedValue=False, orientation="horizontal")

                        if self.graphical_options.is_toroidal:
                            surface_box_thorus = oasysgui.widgetBox(surface_box, "", addSpace=False, orientation="vertical")

                            gui.comboBox(surface_box_thorus, self, "toroidal_mirror_pole_location", label="Torus pole location", labelWidth=145,
                                         items=["lower/outer (concave/concave)",
                                                "lower/inner (concave/convex)",
                                                "upper/inner (convex/concave)",
                                                "upper/outer (convex/convex)"],
                                         sendSelectedValue=False, orientation="horizontal")

                        if not self.graphical_options.is_toroidal:
                            surface_box_2 = oasysgui.widgetBox(tab_bas_shape, "Cylinder Parameter", addSpace=False, orientation="vertical", height=125)

                            gui.comboBox(surface_box_2, self, "surface_curvature", label="Surface Curvature", items=["Concave", "Convex"], labelWidth=280, sendSelectedValue=False, orientation="horizontal")
                            gui.comboBox(surface_box_2, self, "is_cylinder", label="Cylindrical", items=["No", "Yes"],  labelWidth=350, callback=self.set_isCyl_Parameters, sendSelectedValue=False, orientation="horizontal")

                            self.surface_box_cyl = oasysgui.widgetBox(surface_box_2, "", addSpace=False, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                            self.surface_box_cyl_empty = oasysgui.widgetBox(surface_box_2, "", addSpace=False, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                            gui.comboBox(self.surface_box_cyl, self, "cylinder_orientation", label="Cylinder Orientation (deg) [CCW from X axis]", labelWidth=350,
                                         items=[0, 90],
                                         valueType=float,
                                         sendSelectedValue=False, orientation="horizontal")

                            self.set_isCyl_Parameters()

                    view_shape_box = oasysgui.widgetBox(tab_bas_shape, "Calculated Surface Shape", addSpace=False, orientation="vertical")

                    if not self.graphical_options.is_conic_coefficients:
                        if self.graphical_options.is_spheric:
                            self.le_spherical_radius_2 = oasysgui.lineEdit(view_shape_box, self, "spherical_radius", "Radius", labelWidth=170, valueType=float, orientation="horizontal")
                            self.le_spherical_radius_2.setReadOnly(True)
                        elif self.graphical_options.is_toroidal:
                            self.le_torus_major_radius_2 = oasysgui.lineEdit(view_shape_box, self, "torus_major_radius", "Major Radius", labelWidth=170, valueType=float, orientation="horizontal")
                            self.le_torus_minor_radius_2 = oasysgui.lineEdit(view_shape_box, self, "torus_minor_radius", "Minor Radius", labelWidth=170, valueType=float, orientation="horizontal")
                            self.le_torus_major_radius_2.setReadOnly(True)
                            self.le_torus_minor_radius_2.setReadOnly(True)
                        elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                            self.le_ellipse_hyperbola_semi_major_axis_2 = oasysgui.lineEdit(view_shape_box, self, "ellipse_hyperbola_semi_major_axis", "Semi-major Axis",  labelWidth=170, valueType=float, orientation="horizontal")
                            self.le_ellipse_hyperbola_semi_minor_axis_2 = oasysgui.lineEdit(view_shape_box, self, "ellipse_hyperbola_semi_minor_axis", "Semi-minor Axis", labelWidth=170, valueType=float, orientation="horizontal")
                            self.le_ellipse_hyperbola_semi_major_axis_2.setReadOnly(True)
                            self.le_ellipse_hyperbola_semi_minor_axis_2.setReadOnly(True)
                        elif self.graphical_options.is_paraboloid:
                            self.le_paraboloid_parameter_2 = oasysgui.lineEdit(view_shape_box, self, "paraboloid_parameter", "Paraboloid Parameter", labelWidth=170, valueType=float, orientation="horizontal")
                            self.le_paraboloid_parameter_2.setReadOnly(True)

                    #if not self.graphical_options.is_toroidal:
                    self.render_surface_button = gui.button(view_shape_box, self, "Render Surface Shape", callback=self.viewSurfaceShape)

                    if not self.graphical_options.is_conic_coefficients:
                        self.set_IntExt_Parameters()


                ##########################################
                #
                # TAB 1.2 - REFLECTIVITY/CRYSTAL
                #
                ##########################################

                if self.graphical_options.is_mirror:
                    refl_box = oasysgui.widgetBox(tab_bas_refl, "Reflectivity Parameter", addSpace=False, orientation="vertical", height=230)

                    gui.comboBox(refl_box, self, "reflectivity_type", label="Reflectivity", labelWidth=150,
                                 items=["Not considered", "Full Polarization dependence", "No Polarization dependence (scalar)"],
                                 callback=self.set_Refl_Parameters, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(refl_box, width=self.INNER_BOX_WIDTH_L2, height=10)

                    self.refl_box_pol = oasysgui.widgetBox(refl_box, "", addSpace=False, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                    self.refl_box_pol_empty = oasysgui.widgetBox(refl_box, "", addSpace=False, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                    gui.comboBox(self.refl_box_pol, self, "source_of_reflectivity", label="Source of Reflectivity", labelWidth=150,
                                 items=["file generated by PREREFL", "electric susceptibility", "file generated by pre_mlayer", "user defined file"],
                                 callback=self.set_ReflSource_Parameters, sendSelectedValue=False, orientation="horizontal")

                    self.refl_box_pol_1 = oasysgui.widgetBox(self.refl_box_pol, "", addSpace=False, orientation="vertical")

                    gui.separator(self.refl_box_pol_1, width=self.INNER_BOX_WIDTH_L1)

                    file_box = oasysgui.widgetBox(self.refl_box_pol_1, "", addSpace=False, orientation="horizontal", height=25)

                    self.le_file_prerefl = oasysgui.lineEdit(file_box, self, "file_prerefl", "File Name", labelWidth=100, valueType=str, orientation="horizontal")

                    gui.button(file_box, self, "...", callback=self.selectFilePrerefl)

                    self.refl_box_pol_2 = gui.widgetBox(self.refl_box_pol, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.refl_box_pol_2, self, "alpha", "Alpha [epsilon=(1-alpha)+i gamma]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.refl_box_pol_2, self, "gamma", "Gamma [epsilon=(1-alpha)+i gamma]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.refl_box_pol_3 = gui.widgetBox(self.refl_box_pol, "", addSpace=False, orientation="vertical")

                    file_box = oasysgui.widgetBox(self.refl_box_pol_3, "", addSpace=False, orientation="horizontal", height=25)

                    self.le_file_prerefl_m = oasysgui.lineEdit(file_box, self, "file_prerefl_m", "File Name", labelWidth=100, valueType=str, orientation="horizontal")

                    gui.button(file_box, self, "...", callback=self.selectFilePrereflM)

                    gui.comboBox(self.refl_box_pol_3, self, "m_layer_tickness", label="Mlayer thickness vary as cosine", labelWidth=350,
                                 items=["No", "Yes"],
                                 sendSelectedValue=False, orientation="horizontal")

                    self.refl_box_pol_4 = gui.widgetBox(self.refl_box_pol, "", addSpace=False, orientation="vertical")

                    file_box = oasysgui.widgetBox(self.refl_box_pol_4, "", addSpace=False, orientation="horizontal", height=115)

                    gui.comboBox(self.refl_box_pol_4, self, "user_defined_file_type", label="Distribution", labelWidth=100,
                                 items=["1D - Angle vs. Reflectivity", "1D - Energy vs. Reflectivity", "2D - Energy vs. Angle vs Reflectivity"],
                                 sendSelectedValue=False, orientation="horizontal", callback=self.set_UserDefinedFileType)

                    self.cb_energy_units_box = oasysgui.widgetBox(self.refl_box_pol_4, "", addSpace=False, orientation="horizontal")
                    self.cb_angle_units_box = oasysgui.widgetBox(self.refl_box_pol_4, "", addSpace=False, orientation="horizontal")
                    self.cb_empty_units_box = oasysgui.widgetBox(self.refl_box_pol_4, "", addSpace=False, orientation="horizontal", height=25)

                    gui.comboBox(self.cb_angle_units_box, self, "user_defined_angle_units", label="Angle Units", labelWidth=350,
                                 items=["mrad", "deg"], sendSelectedValue=False, orientation="horizontal")

                    gui.comboBox(self.cb_energy_units_box, self, "user_defined_energy_units", label="Energy Units", labelWidth=350,
                                 items=["eV", "KeV"], sendSelectedValue=False, orientation="horizontal")

                    self.le_file_reflectivity = oasysgui.lineEdit(file_box, self, "file_reflectivity", "File Name", labelWidth=100, valueType=str, orientation="horizontal")

                    gui.button(file_box, self, "...", callback=self.selectFileReflectivity)

                    self.set_Refl_Parameters()
                elif self.graphical_options.is_crystal:

                    dcm_box = oasysgui.widgetBox(tab_dcm, "Optical Parameters", addSpace=False, orientation="vertical")

                    figure_box = oasysgui.widgetBox(dcm_box, "", addSpace=False, orientation="horizontal")

                    label = QtWidgets.QLabel("")
                    label.setPixmap(QtGui.QPixmap(self.image_path))

                    figure_box.layout().addWidget(label)

                    self.le_vertical_quote = oasysgui.lineEdit(dcm_box, self, "vertical_quote", "H (Vertical Distance)", labelWidth=260, valueType=float, orientation="horizontal", callback=self.calculate_dcm_distances)
                    self.le_total_distance = oasysgui.lineEdit(dcm_box, self, "total_distance", "D (First Crystal to Next O.E.)", labelWidth=260, valueType=float, orientation="horizontal", callback=self.calculate_dcm_distances)

                    dcm_box_1 = oasysgui.widgetBox(dcm_box, "", addSpace=False, orientation="horizontal", width=(self.INNER_BOX_WIDTH_L0+3))
                    oasysgui.lineEdit(dcm_box_1, self, "twotheta_bragg", "Bragg Angle [deg]",
                                       labelWidth=190, valueType=float, orientation="horizontal", callback=self.calculate_dcm_distances)

                    dcm_button1 = gui.button(dcm_box_1, self, "from O.E.", callback=self.grab_dcm_value_from_oe)

                    gui.separator(dcm_box_1)

                    dcm_box_2 = oasysgui.widgetBox(dcm_box, "", addSpace=False, orientation="horizontal")

                    self.le_d_1 = oasysgui.lineEdit(dcm_box_2, self, "d_1", "d_1", labelWidth=100, valueType=float, orientation="horizontal")
                    self.le_d_1.setReadOnly(True)
                    font = QtGui.QFont(self.le_d_1.font())
                    font.setBold(True)
                    self.le_d_1.setFont(font)
                    palette = QtGui.QPalette(self.le_d_1.palette()) # make a copy of the palette
                    palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
                    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
                    self.le_d_1.setPalette(palette)

                    dcm_button2_1 = gui.button(dcm_box_2, self, "set as S.P.", callback=self.set_d1_as_source_plane)

                    dcm_button2_2 = gui.button(dcm_box_2, self, "set as I.P.", callback=self.set_d1_as_image_plane)

                    dcm_box_3 = oasysgui.widgetBox(dcm_box, "", addSpace=False, orientation="horizontal")

                    self.le_d_2 = oasysgui.lineEdit(dcm_box_3, self, "d_2", "d_2", labelWidth=100, valueType=float, orientation="horizontal")
                    self.le_d_2.setReadOnly(True)
                    font = QtGui.QFont(self.le_d_2.font())
                    font.setBold(True)
                    self.le_d_2.setFont(font)
                    palette = QtGui.QPalette(self.le_d_2.palette()) # make a copy of the palette
                    palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
                    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
                    self.le_d_2.setPalette(palette)

                    dcm_button3_1 = gui.button(dcm_box_3, self, "set as S.P.", callback=self.set_d2_as_source_plane)

                    dcm_button3_2 = gui.button(dcm_box_3, self, "set as I.P.", callback=self.set_d2_as_image_plane)

                    self.grab_dcm_value_from_oe()
                    self.calculate_dcm_distances()

                    ####################################

                    tabs_crystal_setting = oasysgui.tabWidget(tab_bas_crystal)

                    self.tab_cryst_1 = oasysgui.createTabPage(tabs_crystal_setting, "Diffraction Settings")
                    self.tab_cryst_2 = oasysgui.createTabPage(tabs_crystal_setting, "Geometric Setting")

                    crystal_box = oasysgui.widgetBox(self.tab_cryst_1, "Diffraction Parameters", addSpace=True,
                                                      orientation="vertical", height=435)

                    gui.comboBox(crystal_box, self, "diffraction_geometry", label="Diffraction Geometry", labelWidth=250,
                                 items=["Bragg", "Laue"],
                                 sendSelectedValue=False, orientation="horizontal", callback=self.set_BraggLaue)

                    gui.comboBox(crystal_box, self, "diffraction_calculation", label="Diffraction Profile", labelWidth=250,
                                 items=["Calculated", "User Defined"],
                                 sendSelectedValue=False, orientation="horizontal",
                                 callback=self.set_DiffractionCalculation)

                    gui.separator(crystal_box)

                    self.crystal_box_1 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical", height=340)

                    file_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False, orientation="horizontal", height=30)

                    self.le_file_crystal_parameters = oasysgui.lineEdit(file_box, self, "file_crystal_parameters", "File with crystal\nparameters",
                                       labelWidth=150, valueType=str, orientation="horizontal")

                    gui.button(file_box, self, "...", callback=self.selectFileCrystalParameters)

                    gui.comboBox(self.crystal_box_1, self, "crystal_auto_setting", label="Auto setting", labelWidth=350,
                                 items=["No", "Yes"],
                                 callback=self.set_Autosetting, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(self.crystal_box_1, height=10)

                    self.autosetting_box = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False,
                                                               orientation="vertical")
                    self.autosetting_box_empty = oasysgui.widgetBox(self.crystal_box_1, "", addSpace=False,
                                                                     orientation="vertical")

                    self.autosetting_box_units = oasysgui.widgetBox(self.autosetting_box, "", addSpace=False, orientation="vertical")

                    gui.comboBox(self.autosetting_box_units, self, "units_in_use", label="Units in use", labelWidth=260,
                                 items=["eV", "Angstroms"],
                                 callback=self.set_UnitsInUse, sendSelectedValue=False, orientation="horizontal")

                    self.autosetting_box_units_1 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Set photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.autosetting_box_units_2 = oasysgui.widgetBox(self.autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Set wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.crystal_box_2 = oasysgui.widgetBox(crystal_box, "", addSpace=False, orientation="vertical", height=340)

                    crystal_box_2_1 = oasysgui.widgetBox(self.crystal_box_2, "", addSpace=False, orientation="horizontal")

                    self.le_file_diffraction_profile = oasysgui.lineEdit(crystal_box_2_1, self, "file_diffraction_profile",
                                       "File with Diffraction\nProfile (XOP format)", labelWidth=120, valueType=str,
                                       orientation="horizontal")

                    gui.button(crystal_box_2_1, self, "...", callback=self.selectFileDiffractionProfile)

                    gui.comboBox(self.crystal_box_2, self, "user_defined_crystal", label="Crystal", addSpace=True, items=self.CRYSTALS, sendSelectedValue=False, orientation="horizontal", labelWidth=260)

                    box_miller = oasysgui.widgetBox(self.crystal_box_2, "", orientation="horizontal", width=350)
                    oasysgui.lineEdit(box_miller, self, "user_defined_h", label="Miller Indices [h k l]", addSpace=True, valueType=int, labelWidth=200, orientation="horizontal")
                    oasysgui.lineEdit(box_miller, self, "user_defined_k", addSpace=True, valueType=int, orientation="horizontal")
                    oasysgui.lineEdit(box_miller, self, "user_defined_l", addSpace=True, valueType=int, orientation="horizontal")

                    oasysgui.lineEdit(self.crystal_box_2, self, "user_defined_bragg_angle", "Bragg Angle respect to the surface [deg]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.set_UserDefinedBraggAngle)
                    oasysgui.lineEdit(self.crystal_box_2, self, "user_defined_asymmetry_angle", "Asymmetry angle [deg]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.set_UserDefinedBraggAngle)

                    bragg_user_defined_box = oasysgui.widgetBox(self.crystal_box_2, "", addSpace=True, orientation="horizontal")

                    label = QLabel("")
                    label.setAlignment(Qt.AlignCenter)
                    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    label.setPixmap(QPixmap(self.bragg_user_defined_path))

                    bragg_user_defined_box.layout().addWidget(label)

                    self.set_UserDefinedBraggAngle()
                    self.set_DiffractionCalculation()

                    mosaic_box = oasysgui.widgetBox(self.tab_cryst_2, "Geometric Parameters", addSpace=False, orientation="vertical", height=350)

                    gui.comboBox(mosaic_box, self, "mosaic_crystal", label="Mosaic Crystal", labelWidth=355,
                                 items=["No", "Yes"],
                                 callback=self.set_Mosaic, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(mosaic_box, height=10)

                    self.mosaic_box_1 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

                    self.asymmetric_cut_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=110)

                    self.asymmetric_cut_combo = gui.comboBox(self.asymmetric_cut_box, self, "asymmetric_cut", label="Asymmetric cut", labelWidth=355,
                                 items=["No", "Yes"],
                                 callback=self.set_AsymmetricCut, sendSelectedValue=False, orientation="horizontal")

                    self.asymmetric_cut_box_1 = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")
                    self.asymmetric_cut_box_1_empty = oasysgui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.asymmetric_cut_box_1, self, "planes_angle", "Planes angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.asymmetric_cut_box_1_order = oasysgui.widgetBox(self.asymmetric_cut_box_1, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.asymmetric_cut_box_1_order, self, "below_onto_bragg_planes", "Below[-1]/onto[1] bragg planes",  labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_thickness_1 = oasysgui.lineEdit(self.asymmetric_cut_box_1_order, self, "thickness", "Thickness", valueType=float, labelWidth=260, orientation="horizontal")

                    self.set_BraggLaue()

                    gui.separator(self.mosaic_box_1)

                    self.johansson_box = oasysgui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=100)

                    gui.comboBox(self.johansson_box, self, "johansson_geometry", label="Johansson Geometry", labelWidth=355,
                                 items=["No", "Yes"],
                                 callback=self.set_JohanssonGeometry, sendSelectedValue=False, orientation="horizontal")

                    self.johansson_box_1 = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
                    self.johansson_box_1_empty = oasysgui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")

                    self.le_johansson_radius = oasysgui.lineEdit(self.johansson_box_1, self, "johansson_radius", "Johansson radius", labelWidth=260, valueType=float, orientation="horizontal")

                    self.mosaic_box_2 = oasysgui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.mosaic_box_2, self, "angle_spread_FWHM", "Angle spread FWHM [deg]",  labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_thickness_2 = oasysgui.lineEdit(self.mosaic_box_2, self, "thickness", "Thickness", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.mosaic_box_2, self, "seed_for_mosaic", "Seed for mosaic [>10^5]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.set_Mosaic()
                elif self.graphical_options.is_grating:
                    tabs_grating_setting = oasysgui.tabWidget(tab_bas_grating)

                    tab_grating_2 = oasysgui.createTabPage(tabs_grating_setting, "Ruling Setting")
                    tab_grating_1 = oasysgui.createTabPage(tabs_grating_setting, "Diffraction Settings")

                    grating_box = oasysgui.widgetBox(tab_grating_1, "Diffraction Parameters", addSpace=False, orientation="vertical", height=350)

                    oasysgui.lineEdit(grating_box, self, "grating_diffraction_order", "Diffraction Order (- for inside orders)", labelWidth=260, valueType=int, orientation="horizontal")

                    gui.comboBox(grating_box, self, "grating_auto_setting", label="Auto setting", labelWidth=350,
                                 items=["No", "Yes"],
                                 callback=self.set_GratingAutosetting, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(grating_box, height=10)

                    self.grating_autosetting_box = oasysgui.widgetBox(grating_box, "", addSpace=False, orientation="vertical")
                    self.grating_autosetting_box_empty = oasysgui.widgetBox(grating_box, "", addSpace=False, orientation="vertical")

                    self.grating_autosetting_box_units = oasysgui.widgetBox(self.grating_autosetting_box, "", addSpace=False, orientation="vertical")

                    gui.comboBox(self.grating_autosetting_box_units, self, "grating_units_in_use", label="Units in use", labelWidth=260,
                                 items=["eV", "Angstroms"],
                                 callback=self.set_GratingUnitsInUse, sendSelectedValue=False, orientation="horizontal")

                    self.grating_autosetting_box_units_1 = oasysgui.widgetBox(self.grating_autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.grating_autosetting_box_units_1, self, "grating_photon_energy", "Set photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.grating_autosetting_box_units_2 = oasysgui.widgetBox(self.grating_autosetting_box_units, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.grating_autosetting_box_units_2, self, "grating_photon_wavelength", "Set wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.grating_mount_box = oasysgui.widgetBox(grating_box, "", addSpace=False, orientation="vertical")

                    gui.comboBox(self.grating_mount_box, self, "grating_mount_type", label="Mount Type", labelWidth=155,
                                 items=["TGM/Seya", "ERG", "Constant Incidence Angle", "Costant Diffraction Angle", "Hunter"],
                                 callback=self.set_GratingMountType, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(self.grating_mount_box)

                    self.grating_mount_box_1 = oasysgui.widgetBox(self.grating_mount_box, "", addSpace=False, orientation="vertical")

                    oasysgui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_blaze_angle", "Blaze angle [deg]", labelWidth=250, valueType=float, orientation="horizontal")
                    gui.comboBox(self.grating_mount_box_1, self, "grating_hunter_grating_selected", label="Grating selected", labelWidth=250,
                                 items=["First", "Second"], sendSelectedValue=False, orientation="horizontal")
                    self.le_grating_hunter_monochromator_length = oasysgui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_monochromator_length", "Monochromator Length", labelWidth=250, valueType=float, orientation="horizontal")
                    self.le_grating_hunter_distance_between_beams = oasysgui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_distance_between_beams", "Distance between beams", labelWidth=250, valueType=float, orientation="horizontal")

                    self.set_GratingAutosetting()

                    efficiency_box = oasysgui.widgetBox(tab_grating_1, "Efficiency Parameters", addSpace=False, orientation="vertical")


                    gui.comboBox(efficiency_box, self, "grating_use_efficiency", label="Use Efficiency", labelWidth=250,
                                 items=["No", "User File"], sendSelectedValue=False, orientation="horizontal", callback=self.set_Efficiency)

                    self.efficiency_box_1 = oasysgui.widgetBox(efficiency_box, "", addSpace=False, orientation="horizontal", height=30)
                    self.efficiency_box_empty = oasysgui.widgetBox(efficiency_box, "", addSpace=False, orientation="horizontal", height=30, width=400)

                    self.le_grating_file_efficiency = oasysgui.lineEdit(self.efficiency_box_1, self, "grating_file_efficiency", "File Name\n(Energy vs. Effic.)",
                                                                        labelWidth=110, valueType=str, orientation="horizontal")

                    gui.button(self.efficiency_box_1, self, "...", callback=self.selectFileEfficiency)

                    self.set_Efficiency()

                    ################

                    ruling_box = oasysgui.widgetBox(tab_grating_2, "Ruling Parameters", addSpace=False, orientation="vertical", height=380)

                    gui.comboBox(ruling_box, self, "grating_ruling_type", label="Ruling Type", labelWidth=150,
                                 items=["Constant on X-Y Plane", "Constant on Mirror Surface", "Holographic", "Fan Type", "Polynomial Line Density"],
                                 callback=self.set_GratingRulingType, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(ruling_box)

                    self.ruling_box_1 = oasysgui.widgetBox(ruling_box, "", addSpace=False, orientation="horizontal")

                    self.ruling_density_label = gui.widgetLabel(self.ruling_box_1, "Ruling Density at origin", labelWidth=260)
                    oasysgui.lineEdit(self.ruling_box_1, self, "grating_ruling_density", "", labelWidth=1, valueType=float, orientation="horizontal")

                    self.ruling_box_2 = oasysgui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                    self.le_grating_holo_left_distance = oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_left_distance", "\"Left\" distance", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_left_incidence_angle", "\"Left\" incidence angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_left_azimuth_from_y", "\"Left\" azimuth from +Y (CCW) [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_holo_right_distance = oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_right_distance", "\"Right\" distance", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_right_incidence_angle", "\"Right\" incidence angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_right_azimuth_from_y", "\"Right\" azimuth from +Y (CCW) [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    gui.comboBox(self.ruling_box_2, self, "grating_holo_pattern_type", label="Pattern Type", labelWidth=185,
                                 items=["Spherical/Spherical", "Plane/Spherical", "Spherical/Plane", "Plane/Plane"], sendSelectedValue=False, orientation="horizontal")
                    gui.comboBox(self.ruling_box_2, self, "grating_holo_source_type", label="Source Type", labelWidth=250,
                                 items=["Real/Real", "Real/Virtual", "Virtual/Real", "Real/Real"], sendSelectedValue=False, orientation="horizontal")
                    gui.comboBox(self.ruling_box_2, self, "grating_holo_cylindrical_source", label="Cylindrical Source", labelWidth=250,
                                 items=["Spherical/Spherical", "Cylindrical/Spherical", "Spherical/Cylindrical", "Cylindrical/Cylindrical"], sendSelectedValue=False, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_2, self, "grating_holo_recording_wavelength", "Recording wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                    self.ruling_box_3 = oasysgui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                    self.le_grating_groove_pole_distance = oasysgui.lineEdit(self.ruling_box_3, self, "grating_groove_pole_distance", "Groove pole distance", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_3, self, "grating_groove_pole_azimuth_from_y", "Groove pole azimuth from +Y (CCW) [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                    oasysgui.lineEdit(self.ruling_box_3, self, "grating_coma_correction_factor", "Coma correction factor", labelWidth=260, valueType=float, orientation="horizontal")

                    self.ruling_box_4 = oasysgui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                    self.le_grating_poly_coeff_1 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_1", "Polyn. Line Density coeff.: 1st", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_poly_coeff_2 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_2", "Polyn. Line Density coeff.: 2nd", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_poly_coeff_3 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_3", "Polyn. Line Density coeff.: 3rd", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_grating_poly_coeff_4 = oasysgui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_4", "Polyn. Line Density coeff.: 4th", labelWidth=260, valueType=float, orientation="horizontal")
                    gui.comboBox(self.ruling_box_4, self, "grating_poly_signed_absolute", label="Line density absolute/signed from origin", labelWidth=265,
                                 items=["Absolute", "Signed"], sendSelectedValue=False, orientation="horizontal")

                    self.set_GratingRulingType()

                elif self.graphical_options.is_refractor:
                    refractor_box = oasysgui.widgetBox(tab_bas_refractor, "Optical Constants - Refractive Index", addSpace=False, orientation="vertical", height=320)

                    gui.comboBox(refractor_box, self, "optical_constants_refraction_index", label="optical constants\n/refraction index", labelWidth=120,
                                 items=["constant in both media",
                                        "from prerefl in OBJECT media",
                                        "from prerefl in IMAGE media",
                                        "from prerefl in both media"],
                                 callback=self.set_RefrectorOpticalConstants, sendSelectedValue=False, orientation="horizontal")

                    gui.separator(refractor_box, height=10)
                    self.refractor_object_box_1 = oasysgui.widgetBox(refractor_box, "OBJECT side", addSpace=False, orientation="vertical", height=100)
                    oasysgui.lineEdit(self.refractor_object_box_1, self, "refractive_index_in_object_medium", "refractive index in object medium", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_attenuation_in_object_medium = oasysgui.lineEdit(self.refractor_object_box_1, self, "attenuation_in_object_medium", "attenuation in object medium", labelWidth=260, valueType=float, orientation="horizontal")

                    self.refractor_object_box_2 = oasysgui.widgetBox(refractor_box, "OBJECT side", addSpace=False, orientation="horizontal", height=100)
                    self.le_file_prerefl_for_object_medium = oasysgui.lineEdit(self.refractor_object_box_2, self, "file_prerefl_for_object_medium",
                                                                                "file prerefl for\nobject medium", labelWidth=120, valueType=str, orientation="horizontal")

                    gui.button(self.refractor_object_box_2, self, "...", callback=self.selectPrereflObjectFileName)

                    self.refractor_image_box_1 = oasysgui.widgetBox(refractor_box, "IMAGE side", addSpace=False, orientation="vertical", height=100)
                    oasysgui.lineEdit(self.refractor_image_box_1, self, "refractive_index_in_image_medium", "refractive index in image medium", labelWidth=260, valueType=float, orientation="horizontal")
                    self.le_attenuation_in_image_medium = oasysgui.lineEdit(self.refractor_image_box_1, self, "attenuation_in_image_medium", "attenuation in image medium", labelWidth=260, valueType=float, orientation="horizontal")

                    self.refractor_image_box_2 = oasysgui.widgetBox(refractor_box, "IMAGE side", addSpace=False, orientation="horizontal", height=100)
                    self.le_file_prerefl_for_image_medium = oasysgui.lineEdit(self.refractor_image_box_2, self, "file_prerefl_for_image_medium",
                                                                               "file prerefl for\nimage medium", labelWidth=120, valueType=str, orientation="horizontal")

                    gui.button(self.refractor_image_box_2, self, "...", callback=self.selectPrereflImageFileName)

                    self.set_RefrectorOpticalConstants()

                ##########################################
                #
                # TAB 1.3 - DIMENSIONS
                #
                ##########################################

                dimension_box = oasysgui.widgetBox(tab_bas_dim, "Dimensions", addSpace=False, orientation="vertical", height=210)

                gui.comboBox(dimension_box, self, "is_infinite", label="Limits Check",
                             items=["Infinite o.e. dimensions", "Finite o.e. dimensions"],
                             callback=self.set_Dim_Parameters, sendSelectedValue=False, orientation="horizontal")

                gui.separator(dimension_box, width=self.INNER_BOX_WIDTH_L2, height=10)

                self.dimdet_box = oasysgui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")
                self.dimdet_box_empty = oasysgui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")

                gui.comboBox(self.dimdet_box, self, "mirror_shape", label="Shape selected", labelWidth=260,
                             items=["Rectangular", "Full ellipse", "Ellipse with hole"],
                             sendSelectedValue=False, orientation="horizontal")

                self.le_dim_x_plus  = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_plus", "X(+) Half Width / Int Maj Ax", labelWidth=260, valueType=float, orientation="horizontal")
                self.le_dim_x_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_x_minus", "X(-) Half Width / Int Maj Ax", labelWidth=260, valueType=float, orientation="horizontal")
                self.le_dim_y_plus  = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_plus", "Y(+) Half Width / Int Min Ax", labelWidth=260, valueType=float, orientation="horizontal")
                self.le_dim_y_minus = oasysgui.lineEdit(self.dimdet_box, self, "dim_y_minus", "Y(-) Half Width / Int Min Ax", labelWidth=260, valueType=float, orientation="horizontal")

                self.set_Dim_Parameters()


                ##########################################
                #
                # TAB 2.1 - Modified Surface
                #
                ##########################################

                mod_surf_box = oasysgui.widgetBox(tab_adv_mod_surf, "Modified Surface Parameters", addSpace=False, orientation="vertical", height=390)

                gui.comboBox(mod_surf_box, self, "modified_surface", label="Modification Type", labelWidth=260,
                             items=["None", "Surface Error", "Faceted Surface", "Surface Roughness", "Kumakhov Lens", "Segmented Mirror"],
                             callback=self.set_ModifiedSurface, sendSelectedValue=False, orientation="horizontal")

                gui.separator(mod_surf_box, height=10)

                # SURFACE ERROR

                self.surface_error_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                type_of_defect_box = oasysgui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="vertical")

                gui.comboBox(type_of_defect_box, self, "ms_type_of_defect", label="Type of Defect", labelWidth=260,
                             items=["sinusoidal", "gaussian", "external spline"],
                             callback=self.set_TypeOfDefect, sendSelectedValue=False, orientation="horizontal")

                self.mod_surf_err_box_1 = oasysgui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="horizontal")

                self.le_ms_defect_file_name = oasysgui.lineEdit(self.mod_surf_err_box_1, self, "ms_defect_file_name", "File name", labelWidth=80, valueType=str, orientation="horizontal")

                gui.button(self.mod_surf_err_box_1, self, "...", callback=self.selectDefectFileName)
                gui.button(self.mod_surf_err_box_1, self, "View", callback=self.viewDefectFileName)

                self.mod_surf_err_box_2 = oasysgui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="vertical")

                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_wavel_x", "Ripple Wavel. X", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_wavel_y", "Ripple Wavel. Y", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_ampli_x", "Ripple Ampli. X", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_ampli_y", "Ripple Ampli. Y", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_phase_x", "Ripple Phase X", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_phase_y", "Ripple Phase Y", labelWidth=260, valueType=float, orientation="horizontal")

                # FACETED SURFACE

                self.faceted_surface_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                file_box = oasysgui.widgetBox(self.faceted_surface_box, "", addSpace=False, orientation="horizontal", height=25)

                self.le_ms_file_facet_descr = oasysgui.lineEdit(file_box, self, "ms_file_facet_descr", "File w/ facet descr.", labelWidth=125, valueType=str, orientation="horizontal")

                gui.button(file_box, self, "...", callback=self.selectFileFacetDescr)

                gui.comboBox(self.faceted_surface_box, self, "ms_lattice_type", label="Lattice Type", labelWidth=260,
                             items=["rectangle", "hexagonal"], sendSelectedValue=False, orientation="horizontal")

                gui.comboBox(self.faceted_surface_box, self, "ms_orientation", label="Orientation", labelWidth=260,
                             items=["y-axis", "other"], sendSelectedValue=False, orientation="horizontal")

                gui.comboBox(self.faceted_surface_box, self, "ms_intercept_to_use", label="Intercept to use", labelWidth=260,
                             items=["2nd first", "2nd closest", "closest", "farthest"], sendSelectedValue=False, orientation="horizontal")

                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_width_x", "Facet width (in X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_phase_x", "Facet phase in X (0-360)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_x_minus", "Dead width (abs, for -X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_x_plus", "Dead width (abs, for +X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_width_y", "Facet width (in Y)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_facet_phase_y", "Facet phase in Y (0-360)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_y_minus", "Dead width (abs, for -Y)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_y_plus", "Dead width (abs, for +Y)", labelWidth=260, valueType=float, orientation="horizontal")

                # SURFACE ROUGHNESS

                self.surface_roughness_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")


                file_box = oasysgui.widgetBox(self.surface_roughness_box, "", addSpace=False, orientation="horizontal", height=25)

                self.le_ms_file_surf_roughness = oasysgui.lineEdit(file_box, self, "ms_file_surf_roughness", "Surf. Rough. File w/ PSD fn", valueType=str, orientation="horizontal")

                gui.button(file_box, self, "...", callback=self.selectFileSurfRoughness)

                oasysgui.lineEdit(self.surface_roughness_box, self, "ms_roughness_rms_y", "Roughness RMS in Y (Å)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.surface_roughness_box, self, "ms_roughness_rms_x", "Roughness RMS in X (Å)", labelWidth=260, valueType=float, orientation="horizontal")

                # KUMAKHOV LENS

                self.kumakhov_lens_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                gui.comboBox(self.kumakhov_lens_box, self, "ms_specify_rz2", label="Specify r(z)\u00b2", labelWidth=350,
                             items=["No", "Yes"], callback=self.set_SpecifyRz2, sendSelectedValue=False, orientation="horizontal")

                self.kumakhov_lens_box_1 =  oasysgui.widgetBox(self.kumakhov_lens_box, box="", addSpace=False, orientation="vertical")
                self.kumakhov_lens_box_2 =  oasysgui.widgetBox(self.kumakhov_lens_box, box="", addSpace=False, orientation="vertical")

                file_box = oasysgui.widgetBox(self.kumakhov_lens_box_1, "", addSpace=False, orientation="horizontal", height=25)

                self.le_ms_file_with_parameters_rz = oasysgui.lineEdit(file_box, self, "ms_file_with_parameters_rz", "File with parameters (r(z))", labelWidth=185, valueType=str, orientation="horizontal")

                gui.button(file_box, self, "...", callback=self.selectFileWithParametersRz)

                file_box = oasysgui.widgetBox(self.kumakhov_lens_box_2, "", addSpace=False, orientation="horizontal", height=25)

                self.le_ms_file_with_parameters_rz2 = oasysgui.lineEdit(file_box, self, "ms_file_with_parameters_rz2", "File with parameters (r(z)\u00b2)", labelWidth=185, valueType=str, orientation="horizontal")

                gui.button(file_box, self, "...", callback=self.selectFileWithParametersRz2)

                gui.comboBox(self.kumakhov_lens_box, self, "ms_save_intercept_bounces", label="Save intercept and bounces", labelWidth=350,
                             items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

                # SEGMENTED MIRROR

                self.segmented_mirror_box =  oasysgui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_number_of_segments_x", "Number of segments (X)", labelWidth=260, valueType=int, orientation="horizontal")
                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_length_of_segments_x", "Length of segments (X)", labelWidth=260, valueType=float, orientation="horizontal")
                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_number_of_segments_y", "Number of segments (Y)", labelWidth=260, valueType=int, orientation="horizontal")
                oasysgui.lineEdit(self.segmented_mirror_box, self, "ms_length_of_segments_y", "Length of segments (Y)", labelWidth=260, valueType=float, orientation="horizontal")


                file_box = oasysgui.widgetBox(self.segmented_mirror_box, "", addSpace=False, orientation="horizontal", height=25)

                self.le_ms_file_orientations = oasysgui.lineEdit(file_box, self, "ms_file_orientations", "File w/ orientations", labelWidth=155, valueType=str, orientation="horizontal")

                gui.button(file_box, self, "...", callback=self.selectFileOrientations)

                file_box = oasysgui.widgetBox(self.segmented_mirror_box, "", addSpace=False, orientation="horizontal", height=25)

                self.le_ms_file_polynomial = oasysgui.lineEdit(file_box, self, "ms_file_polynomial", "File w/ polynomial", labelWidth=155, valueType=str, orientation="horizontal")

                gui.button(file_box, self, "...", callback=self.selectFilePolynomial)

                self.set_ModifiedSurface()


            self.mirror_orientation_angle_user()


    def after_change_workspace_units(self):
        label = self.le_source_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_image_plane_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        if self.graphical_options.is_screen_slit:
            label = self.le_slit_width_xaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_slit_height_zaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_slit_center_xaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_slit_center_zaxis.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_thickness.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
        elif self.graphical_options.is_ideal_lens:
            label = self.le_focal_x.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
            label = self.le_focal_z.parent().layout().itemAt(0).widget()
            label.setText(label.text() + " [" + self.workspace_units_label + "]")
        else:
            if self.graphical_options.is_curved:
                if not self.graphical_options.is_conic_coefficients:
                    if self.graphical_options.is_spheric:
                        label = self.le_spherical_radius.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_spherical_radius_2.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    elif self.graphical_options.is_toroidal:
                        label = self.le_torus_major_radius.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_torus_minor_radius.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_torus_major_radius_2.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_torus_minor_radius_2.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                        label = self.le_ellipse_hyperbola_semi_major_axis.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_ellipse_hyperbola_semi_minor_axis.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_ellipse_hyperbola_semi_major_axis_2.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_ellipse_hyperbola_semi_minor_axis_2.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    elif self.graphical_options.is_paraboloid:
                        label = self.le_paraboloid_parameter.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")
                        label = self.le_paraboloid_parameter_2.parent().layout().itemAt(0).widget()
                        label.setText(label.text() + " [" + self.workspace_units_label + "]")

                    label = self.w_object_side_focal_distance.parent().layout().itemAt(0).widget()
                    label.setText(label.text() + " [" + self.workspace_units_label + "]")
                    label = self.w_image_side_focal_distance.parent().layout().itemAt(0).widget()
                    label.setText(label.text() + " [" + self.workspace_units_label + "]")

            if self.graphical_options.is_crystal:
                label = self.le_johansson_radius.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_vertical_quote.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_total_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_d_1.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_d_2.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_thickness_1.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_thickness_2.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")

            elif self.graphical_options.is_grating:
                label = self.le_grating_hunter_monochromator_length.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_grating_hunter_distance_between_beams.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                self.ruling_density_label.setText(self.ruling_density_label.text() + "  [Lines/" + self.workspace_units_label + "]")
                label = self.le_grating_poly_coeff_1.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines/" + self.workspace_units_label + "\u00b2]")
                label = self.le_grating_poly_coeff_2.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines/" + self.workspace_units_label + "\u00b3]")
                label = self.le_grating_poly_coeff_3.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines/" + self.workspace_units_label + "\u2074]")
                label = self.le_grating_poly_coeff_4.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [Lines/" + self.workspace_units_label + "\u2075]")

                label = self.le_grating_holo_left_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_grating_holo_right_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_grating_groove_pole_distance.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
            elif self.graphical_options.is_refractor:
                label = self.le_attenuation_in_object_medium.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "-1]")
                label = self.le_attenuation_in_image_medium.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "-1]")

            if not self.graphical_options.is_empty:
                # DIMENSIONS
                label = self.le_dim_x_plus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_dim_x_minus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_dim_y_plus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")
                label = self.le_dim_y_minus.parent().layout().itemAt(0).widget()
                label.setText(label.text() + " [" + self.workspace_units_label + "]")

        if not (self.graphical_options.is_ideal_lens):
            # ADVANCED SETTINGS
            # MIRROR MOVEMENTS
            if not (self.graphical_options.is_screen_slit or self.graphical_options.is_empty ):
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


    def set_Footprint(self):
        if self.file_to_write_out == 0 or self.file_to_write_out == 1 or self.file_to_write_out == 4:
            self.enableFootprint(not (self.graphical_options.is_screen_slit or self.graphical_options.is_ideal_lens or self.graphical_options.is_empty))
        else:
            self.enableFootprint(False)

    def callResetSettings(self):
        super().callResetSettings()
        self.setupUI()

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def set_UserDefinedBraggAngle(self):
        if self.diffraction_calculation == 1:
            if self.angles_respect_to == 0:
                self.incidence_angle_deg  = 90.0 - (self.user_defined_bragg_angle - self.user_defined_asymmetry_angle)
                self.reflection_angle_deg = 90.0 - (self.user_defined_bragg_angle + self.user_defined_asymmetry_angle)
            else:
                self.incidence_angle_deg  = self.user_defined_bragg_angle - self.user_defined_asymmetry_angle
                self.reflection_angle_deg = self.user_defined_bragg_angle + self.user_defined_asymmetry_angle

            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

    def set_AnglesRespectTo(self):
        label_1 = self.incidence_angle_deg_le.parent().layout().itemAt(0).widget()
        label_2 = self.reflection_angle_deg_le.parent().layout().itemAt(0).widget()

        if self.angles_respect_to == 0:
            label_1.setText("Incident Angle\nwith respect to the normal [deg]")
            label_2.setText("Reflection Angle\nwith respect to the normal [deg]")
        else:
            label_1.setText("Incident Angle\nwith respect to the surface [deg]")
            label_2.setText("Reflection Angle\nwith respect to the surface [deg]")

        self.calculate_incidence_angle_mrad()
        self.calculate_reflection_angle_mrad()
    # TAB 1.1

    def set_IntExt_Parameters(self):
        self.surface_box_int.setVisible(self.surface_shape_parameters == 0)
        self.surface_box_ext.setVisible(self.surface_shape_parameters == 1)
        if self.surface_shape_parameters == 0: self.set_FociiCont_Parameters()

        if not self.graphical_options.is_toroidal:
            self.render_surface_button.setEnabled(self.surface_shape_parameters == 0)

    def set_FociiCont_Parameters(self):
        self.surface_box_int_2.setVisible(self.focii_and_continuation_plane == 1)
        self.surface_box_int_2_empty.setVisible(self.focii_and_continuation_plane == 0)

    def set_incidenceAngleRespectToNormal(self):
        self.surface_box_int_3.setVisible(self.incidence_angle_respect_to_normal_type==1)
        self.surface_box_int_3_empty.setVisible(self.incidence_angle_respect_to_normal_type==0)

        self.calculate_incidence_angle_mrad()

    def set_isCyl_Parameters(self):
        self.surface_box_cyl.setVisible(self.is_cylinder == 1)
        self.surface_box_cyl_empty.setVisible(self.is_cylinder == 0)

    # TAB 1.2

    def set_Refl_Parameters(self):
        self.refl_box_pol.setVisible(self.reflectivity_type != 0)
        self.refl_box_pol_empty.setVisible(self.reflectivity_type == 0)
        if self.reflectivity_type != 0: self.set_ReflSource_Parameters()

    def set_ReflSource_Parameters(self):
        self.refl_box_pol_1.setVisible(self.source_of_reflectivity == 0)
        self.refl_box_pol_2.setVisible(self.source_of_reflectivity == 1)
        self.refl_box_pol_3.setVisible(self.source_of_reflectivity == 2)
        self.refl_box_pol_4.setVisible(self.source_of_reflectivity == 3)
        if self.source_of_reflectivity == 3: self.set_UserDefinedFileType()

    def set_UserDefinedFileType(self):
        self.cb_empty_units_box.setVisible(self.user_defined_file_type in [0, 1])
        self.cb_angle_units_box.setVisible(self.user_defined_file_type in [0, 2])
        self.cb_energy_units_box.setVisible(self.user_defined_file_type in [1, 2])

    def set_Autosetting(self):
        self.autosetting_box_empty.setVisible(self.crystal_auto_setting == 0)
        self.autosetting_box.setVisible(self.crystal_auto_setting == 1)

        if self.crystal_auto_setting == 0:
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.incidence_angle_deg_le.setEnabled(False)
            self.incidence_angle_rad_le.setEnabled(False)
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)
            self.set_UnitsInUse()

    def set_DiffractionCalculation(self):
        self.tab_cryst_2.setEnabled(self.diffraction_calculation == 0)

        self.crystal_box_1.setVisible(self.diffraction_calculation == 0)
        self.crystal_box_2.setVisible(self.diffraction_calculation == 1)

        if (self.diffraction_calculation == 1):
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.set_Autosetting()

    def set_BraggLaue(self):
        self.asymmetric_cut_box_1_order.setVisible(self.diffraction_geometry==1) #LAUE
        if self.diffraction_geometry==1:
            self.asymmetric_cut = 1
            self.set_AsymmetricCut()
            self.asymmetric_cut_combo.setEnabled(False)
        else:
            self.asymmetric_cut_combo.setEnabled(True)

    def set_UnitsInUse(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def set_Mosaic(self):
        self.mosaic_box_1.setVisible(self.mosaic_crystal == 0)
        self.mosaic_box_2.setVisible(self.mosaic_crystal == 1)

        if self.mosaic_crystal == 0:
            self.set_AsymmetricCut()
            self.set_JohanssonGeometry()

    def set_AsymmetricCut(self):
        self.asymmetric_cut_box_1.setVisible(self.asymmetric_cut == 1)
        self.asymmetric_cut_box_1_empty.setVisible(self.asymmetric_cut == 0)

    def set_JohanssonGeometry(self):
        self.johansson_box_1.setVisible(self.johansson_geometry == 1)
        self.johansson_box_1_empty.setVisible(self.johansson_geometry == 0)

    def set_GratingAutosetting(self):
        self.grating_autosetting_box_empty.setVisible(self.grating_auto_setting == 0)
        self.grating_autosetting_box.setVisible(self.grating_auto_setting == 1)
        self.grating_mount_box.setVisible(self.grating_auto_setting == 1)

        if self.grating_auto_setting == 0:
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)
            self.set_GratingUnitsInUse()
            self.set_GratingMountType()

    def set_Efficiency(self):
        self.efficiency_box_1.setVisible(self.grating_use_efficiency == 1)
        self.efficiency_box_empty.setVisible(self.grating_use_efficiency == 0)

    def set_GratingUnitsInUse(self):
        self.grating_autosetting_box_units_1.setVisible(self.grating_units_in_use == 0)
        self.grating_autosetting_box_units_2.setVisible(self.grating_units_in_use == 1)

    def set_GratingRulingType(self):
        self.ruling_box_1.setVisible(self.grating_ruling_type != 2)
        self.ruling_box_2.setVisible(self.grating_ruling_type == 2)
        self.ruling_box_3.setVisible(self.grating_ruling_type == 3)
        self.ruling_box_4.setVisible(self.grating_ruling_type == 4)

        if (self.grating_ruling_type == 0 or \
                self.grating_ruling_type == 1): self.ruling_density_label.setText("Ruling Density at origin")
        elif (self.grating_ruling_type == 3):   self.ruling_density_label.setText("Ruling Density at center")
        elif (self.grating_ruling_type == 4):   self.ruling_density_label.setText("Polyn. Line Density coeff.: 0th")

        if hasattr(self, "workspace_units_label"): self.ruling_density_label.setText(self.ruling_density_label.text() + "  [Lines/" + self.workspace_units_label + "]")

    def set_GratingMountType(self):
        self.grating_mount_box_1.setVisible(self.grating_mount_type == 4)

    def set_RefrectorOpticalConstants(self):
        self.refractor_object_box_1.setVisible(self.optical_constants_refraction_index == 0 or self.optical_constants_refraction_index == 2)
        self.refractor_object_box_2.setVisible(self.optical_constants_refraction_index == 1 or self.optical_constants_refraction_index == 3)
        self.refractor_image_box_1.setVisible(self.optical_constants_refraction_index == 0 or self.optical_constants_refraction_index == 1)
        self.refractor_image_box_2.setVisible(self.optical_constants_refraction_index == 2 or self.optical_constants_refraction_index == 3)

    # TAB 1.3

    def set_Dim_Parameters(self):
        self.dimdet_box.setVisible(self.is_infinite == 1)
        self.dimdet_box_empty.setVisible(self.is_infinite == 0)

    # TAB 2

    def set_SourceMovement(self):
        self.sou_mov_box_1.setVisible(self.source_movement == 1)

    def set_MirrorMovement(self):
        self.mir_mov_box_1.setVisible(self.mirror_movement == 1)

    def set_TypeOfDefect(self):
        self.mod_surf_err_box_1.setVisible(self.ms_type_of_defect != 0)
        self.mod_surf_err_box_2.setVisible(self.ms_type_of_defect == 0)

    def set_ModifiedSurface(self):
        self.surface_error_box.setVisible(self.modified_surface == 1)
        self.faceted_surface_box.setVisible(self.modified_surface == 2)
        self.surface_roughness_box.setVisible(self.modified_surface == 3)
        self.kumakhov_lens_box.setVisible(self.modified_surface == 4)
        self.segmented_mirror_box.setVisible(self.modified_surface == 5)
        if self.modified_surface == 1: self.set_TypeOfDefect()
        if self.modified_surface == 4: self.set_SpecifyRz2()

    def set_SpecifyRz2(self):
        self.kumakhov_lens_box_1.setVisible(self.ms_specify_rz2 == 0)
        self.kumakhov_lens_box_2.setVisible(self.ms_specify_rz2 == 1)


    def set_ApertureShape(self):
        self.box_aperturing_shape_1.setVisible(self.aperture_shape == 2)
        self.box_aperturing_shape_2.setVisible(self.aperture_shape != 2)

    def set_Aperturing(self):
            self.box_aperturing_shape.setVisible(self.aperturing == 1)

            if self.aperturing == 1: self.set_ApertureShape()

    def set_Absorption(self):
        self.box_absorption_1_empty.setVisible(self.absorption == 0)
        self.box_absorption_1.setVisible(self.absorption == 1)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def selectExternalFileWithCoordinate(self):
        self.le_external_file_with_coordinate.setText(oasysgui.selectFileFromDialog(self, self.external_file_with_coordinate, "Open External File With Coordinate"))

    def selectOptConstFileName(self):
        self.le_opt_const_file_name.setText(oasysgui.selectFileFromDialog(self, self.opt_const_file_name, "Open Opt. Const. File"))

    def selectFilePrerefl(self):
        self.le_file_prerefl.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl, "Select File Prerefl", file_extension_filter="Data Files (*.dat)"))

    def selectFilePrereflM(self):
        self.le_file_prerefl_m.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_m, "Select File Premlayer", file_extension_filter="Data Files (*.dat)"))

    def selectFileReflectivity(self):
        self.le_file_reflectivity.setText(oasysgui.selectFileFromDialog(self, self.file_reflectivity, "Select Reflectivity File"))

    def selectFileEfficiency(self):
        self.le_grating_file_efficiency.setText(oasysgui.selectFileFromDialog(self, self.grating_file_efficiency, "Select Grating Efficiency File"))

    def selectFileCrystalParameters(self):
        self.le_file_crystal_parameters.setText(oasysgui.selectFileFromDialog(self, self.file_crystal_parameters, "Select File With Crystal Parameters"))

    def selectFileDiffractionProfile(self):
        self.le_file_diffraction_profile.setText(oasysgui.selectFileFromDialog(self, self.file_diffraction_profile, "Select File With User Defined Diffraction Profile"))

    def selectDefectFileName(self):
        self.le_ms_defect_file_name.setText(oasysgui.selectFileFromDialog(self, self.ms_defect_file_name, "Select Defect File Name", file_extension_filter="Data Files (*.dat *.sha)"))

    class ShowDefectFileDialog(QDialog):

        def __init__(self, parent=None, filename=""):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Defect File - Surface Error Profile')

            self.setFixedHeight(700)

            layout = QtWidgets.QGridLayout(self)

            figure = Figure(figsize=(8, 7))
            figure.patch.set_facecolor('white')

            axis = figure.add_subplot(111, projection='3d')

            axis.set_xlabel("X [" + parent.workspace_units_label + "]")
            axis.set_ylabel("Y [" + parent.workspace_units_label + "]")
            axis.set_zlabel("Z [nm]")

            figure_canvas = FigureCanvas3D(ax=axis, fig=figure, show_legend=False, show_buttons=False)
            figure_canvas.setFixedWidth(500)
            figure_canvas.setFixedHeight(645)

            self.x_coords, self.y_coords, self.z_values = ShadowPreProcessor.read_surface_error_file(filename)

            x_to_plot, y_to_plot = numpy.meshgrid(self.x_coords, self.y_coords)
            z_to_plot = self.z_values.T

            axis.plot_surface(x_to_plot, y_to_plot, (z_to_plot*parent.workspace_units_to_m*1e9),
                              rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            sloperms = profiles_simulation.slopes(self.z_values, self.x_coords, self.y_coords, return_only_rms=1)

            title = ' Slope error rms in X direction: %f $\mu$rad' % (sloperms[0]*1e6) + '\n' + \
                    ' Slope error rms in Y direction: %f $\mu$rad' % (sloperms[1]*1e6) + '\n' + \
                    ' Figure error rms in X direction: %f nm' % (round(self.z_values[:, 0].std()*parent.workspace_units_to_m*1e9, 6)) + '\n' + \
                    ' Figure error rms in Y direction: %f nm' % (round(self.z_values[0, :].std()*parent.workspace_units_to_m*1e9, 6))

            axis.set_title(title)

            figure_canvas.draw()

            axis.mouse_init()

            widget = QWidget(parent=self)

            container = oasysgui.widgetBox(widget, "", addSpace=False, orientation="horizontal", width=500)

            gui.button(container, self, "Export Surface (.dat)", callback=self.save_shadow_surface)
            gui.button(container, self, "Export Surface (.hdf5)", callback=self.save_oasys_surface)
            gui.button(container, self, "Close", callback=self.accept)

            layout.addWidget(figure_canvas, 0, 0)
            layout.addWidget(widget, 1, 0)

            self.setLayout(layout)

        def save_shadow_surface(self):
            try:
                file_path = QFileDialog.getSaveFileName(self, "Save Surface in Shadow (dat) Format", ".", "Shadow format (*.dat)")[0]

                if not file_path is None and not file_path.strip() == "":
                    ST.write_shadow_surface(self.z_values.T, numpy.round(self.x_coords, 6), numpy.round(self.y_coords, 6), file_path)
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)

        def save_oasys_surface(self):
            try:
                file_path = QFileDialog.getSaveFileName(self, "Save Surface in Oasys (hdf5) Format", ".", "HDF5 format (*.hdf5)")[0]

                if not file_path is None and not file_path.strip() == "":
                    conv = self.parent().workspace_units_to_m

                    OU.write_surface_file(self.z_values.T*conv, numpy.round(self.x_coords*conv, 8), numpy.round(self.y_coords*conv, 8), file_path)
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)

    def viewDefectFileName(self):
        try:
            dialog = OpticalElement.ShowDefectFileDialog(parent=self,
                                                         filename=self.ms_defect_file_name)
            dialog.show()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception), QtWidgets.QMessageBox.Ok)

    class ShowSurfaceShapeDialog(QDialog):

        c1  = 0.0
        c2  = 0.0
        c3  = 0.0
        c4  = 0.0
        c5  = 0.0
        c6  = 0.0
        c7  = 0.0
        c8  = 0.0
        c9  = 0.0
        c10 = 0.0

        torus_major_radius = 0.0
        torus_minor_radius = 0.0

        xx = None
        yy = None
        zz = None

        bin_x = 100
        bin_y = 1000

        def __init__(self, parent=None):
            QDialog.__init__(self, parent)
            self.setWindowTitle('O.E. Surface Shape')

            self.setFixedWidth(750)

            layout = QtWidgets.QGridLayout(self)

            figure = Figure(figsize=(100, 100))
            figure.patch.set_facecolor('white')

            axis = figure.add_subplot(111, projection='3d')

            axis.set_xlabel("X [" + parent.workspace_units_label + "]")
            axis.set_ylabel("Y [" + parent.workspace_units_label + "]")
            axis.set_zlabel("Z [" + parent.workspace_units_label + "]")

            figure_canvas = FigureCanvas3D(ax=axis, fig=figure, show_legend=False, show_buttons=False)
            figure_canvas.setFixedWidth(500)
            figure_canvas.setFixedHeight(500)

            X, Y, z_values = self.calculate_surface(parent, 100, 100)

            axis.plot_surface(X, Y, z_values,
                              rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            if parent.graphical_options.is_toroidal:
                axis.set_title("Surface from Torus equation:\n" +
                               "[(Z + R + r)" + u"\u00B2" +
                               " + Y" + u"\u00B2" +
                               " + X" + u"\u00B2" +
                               " + R" + u"\u00B2" +
                               " - r" + u"\u00B2"
                               + "]" + u"\u00B2" +
                               "= 4R" + u"\u00B2" + "[(Z + R + r)" + u"\u00B2" + " + Y" + u"\u00B2" + "]")
            else:
                title_head = "Surface from generated conic coefficients:\n"
                title = ""
                max_dim = 40

                if self.c1 != 0: title +=       str(self.c1) + u"\u00B7" + "X" + u"\u00B2"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c2 < 0 or (self.c2 > 0 and title == ""): title +=       str(self.c2) + u"\u00B7" + "Y" + u"\u00B2"
                elif self.c2 > 0                                 : title += "+" + str(self.c2) + u"\u00B7" + "Y" + u"\u00B2"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c3 < 0 or (self.c3 > 0 and title == ""): title +=       str(self.c3) + u"\u00B7" + "Z" + u"\u00B2"
                elif self.c3 > 0                                 : title += "+" + str(self.c3) + u"\u00B7" + "Z" + u"\u00B2"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c4 < 0 or (self.c4 > 0 and title == ""): title +=       str(self.c4) + u"\u00B7" + "XY"
                elif self.c4 > 0                                 : title += "+" + str(self.c4) + u"\u00B7" + "XY"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c5 < 0 or (self.c5 > 0 and title == ""): title +=       str(self.c5) + u"\u00B7" + "YZ"
                elif self.c5 > 0                                 : title += "+" + str(self.c5) + u"\u00B7" + "YZ"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c6 < 0 or (self.c6 > 0 and title == ""): title +=       str(self.c6) + u"\u00B7" + "XZ"
                elif self.c6 > 0                                 : title += "+" + str(self.c6) + u"\u00B7" + "XZ"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c7 < 0 or (self.c7 > 0 and title == ""): title +=       str(self.c7) + u"\u00B7" + "X"
                elif self.c7 > 0                                 : title += "+" + str(self.c7) + u"\u00B7" + "X"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c8 < 0 or (self.c8 > 0 and title == ""): title +=       str(self.c8) + u"\u00B7" + "Y"
                elif self.c8 > 0                                 : title += "+" + str(self.c8) + u"\u00B7" + "Y"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c9 < 0 or (self.c9 > 0 and title == ""): title +=       str(self.c9) + u"\u00B7" + "Z"
                elif self.c9 > 0                                 : title += "+" + str(self.c9) + u"\u00B7" + "Z"
                if len(title) >=  max_dim:
                    title_head += title + "\n"
                    title = ""
                if self.c10< 0 or (self.c10> 0 and title == ""): title +=       str(self.c10)
                elif self.c10> 0                                 : title += "+" + str(self.c10)

                axis.set_title(title_head + title + " = 0")

            figure_canvas.draw()

            axis.mouse_init()

            widget = QWidget(parent=self)

            container = oasysgui.widgetBox(widget, "", addSpace=False, orientation="vertical", width=220)

            if parent.graphical_options.is_toroidal:
                surface_box = oasysgui.widgetBox(container, "Torus Parameters", addSpace=False, orientation="vertical", width=220, height=375)

                le_torus_major_radius = oasysgui.lineEdit(surface_box, self, "torus_major_radius" , "R" , labelWidth=60, valueType=float, orientation="horizontal")
                le_torus_minor_radius = oasysgui.lineEdit(surface_box, self, "torus_minor_radius" , "r" , labelWidth=60, valueType=float, orientation="horizontal")

                le_torus_major_radius.setReadOnly(True)
                le_torus_minor_radius.setReadOnly(True)
            else:
                surface_box = oasysgui.widgetBox(container, "Conic Coefficients", addSpace=False, orientation="vertical", width=220, height=375)

                label  = "c[1]" + u"\u00B7" + "X" + u"\u00B2" + " + c[2]" + u"\u00B7" + "Y" + u"\u00B2" + " + c[3]" + u"\u00B7" + "Z" + u"\u00B2" + " +\n"
                label += "c[4]" + u"\u00B7" + "XY" + " + c[5]" + u"\u00B7" + "YZ" + " + c[6]" + u"\u00B7" + "XZ" + " +\n"
                label += "c[7]" + u"\u00B7" + "X" + " + c[8]" + u"\u00B7" + "Y" + " + c[9]" + u"\u00B7" + "Z" + " + c[10] = 0"

                gui.label(surface_box, self, label)

                gui.separator(surface_box, 10)

                le_0 = oasysgui.lineEdit(surface_box, self, "c1" , "c[1]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_1 = oasysgui.lineEdit(surface_box, self, "c2" , "c[2]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_2 = oasysgui.lineEdit(surface_box, self, "c3" , "c[3]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_3 = oasysgui.lineEdit(surface_box, self, "c4" , "c[4]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_4 = oasysgui.lineEdit(surface_box, self, "c5" , "c[5]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_5 = oasysgui.lineEdit(surface_box, self, "c6" , "c[6]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_6 = oasysgui.lineEdit(surface_box, self, "c7" , "c[7]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_7 = oasysgui.lineEdit(surface_box, self, "c8" , "c[8]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_8 = oasysgui.lineEdit(surface_box, self, "c9" , "c[9]" , labelWidth=60, valueType=float, orientation="horizontal")
                le_9 = oasysgui.lineEdit(surface_box, self, "c10", "c[10]", labelWidth=60, valueType=float, orientation="horizontal")

                le_0.setReadOnly(True)
                le_1.setReadOnly(True)
                le_2.setReadOnly(True)
                le_3.setReadOnly(True)
                le_4.setReadOnly(True)
                le_5.setReadOnly(True)
                le_6.setReadOnly(True)
                le_7.setReadOnly(True)
                le_8.setReadOnly(True)
                le_9.setReadOnly(True)

            export_box = oasysgui.widgetBox(container, "Export", addSpace=False, orientation="vertical", width=220)

            bin_box = oasysgui.widgetBox(export_box, "", addSpace=False, orientation="horizontal")

            oasysgui.lineEdit(bin_box, self, "bin_x" , "Bins X" , labelWidth=40, valueType=float, orientation="horizontal")
            oasysgui.lineEdit(bin_box, self, "bin_y" , " x Y" , labelWidth=30, valueType=float, orientation="horizontal")

            gui.button(export_box, self, "Export Surface (.dat)", callback=self.save_shadow_surface)
            gui.button(export_box, self, "Export Surface (.hdf5)", callback=self.save_oasys_surface)

            bbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)

            bbox.accepted.connect(self.accept)
            layout.addWidget(figure_canvas, 0, 0)
            layout.addWidget(widget, 0, 1)
            layout.addWidget(bbox, 1, 0, 1, 2)

            self.setLayout(layout)

        def calculate_surface(self, parent, bin_x=100, bin_y=100):
            if parent.is_infinite == 0:
                x_min = -10
                x_max = 10
                y_min = -10
                y_max = 10
            else:
                x_min = -parent.dim_x_minus
                x_max = parent.dim_x_plus
                y_min = -parent.dim_y_minus
                y_max = parent.dim_y_plus

            self.xx = numpy.linspace(x_min, x_max, bin_x + 1)
            self.yy = numpy.linspace(y_min, y_max, bin_y + 1)

            X, Y = numpy.meshgrid(self.xx, self.yy)

            if parent.graphical_options.is_toroidal:
                self.torus_major_radius = parent.torus_major_radius
                self.torus_minor_radius = parent.torus_minor_radius

                sign = -1 if parent.toroidal_mirror_pole_location <= 1 else 1

                z_values = sign*(numpy.sqrt((self.torus_major_radius
                                             + numpy.sqrt(self.torus_minor_radius**2-X**2))**2
                                            - Y**2)
                                - self.torus_major_radius - self.torus_minor_radius)
                z_values[numpy.where(numpy.isnan(z_values))] = 0.0
            else:
                self.c1 = round(parent.conic_coefficient_0, 10)
                self.c2 = round(parent.conic_coefficient_1, 10)
                self.c3 = round(parent.conic_coefficient_2, 10)
                self.c4 = round(parent.conic_coefficient_3, 10)
                self.c5 = round(parent.conic_coefficient_4, 10)
                self.c6 = round(parent.conic_coefficient_5, 10)
                self.c7 = round(parent.conic_coefficient_6, 10)
                self.c8 = round(parent.conic_coefficient_7, 10)
                self.c9 = round(parent.conic_coefficient_8, 10)
                self.c10= round(parent.conic_coefficient_9, 10)

                def equation_to_solve(Z):
                    return self.c1*(X**2) + self.c2*(Y**2) + self.c3*(Z**2) + self.c4*X*Y + self.c5*Y*Z + self.c6*X*Z + self.c7*X + self.c8*Y + self.c9*Z + self.c10

                z_start = numpy.zeros((bin_x + 1, bin_y + 1))
                result = root(equation_to_solve, z_start.T, method='df-sane', tol=None)

                z_values = result.x if result.success else z_start

            self.zz = z_values

            return X, Y, z_values

        def check_values(self):
            congruence.checkStrictlyPositiveNumber(self.bin_x, "Bins X")
            congruence.checkStrictlyPositiveNumber(self.bin_y, "Bins Y")

        def save_shadow_surface(self):
            try:
                file_path = QFileDialog.getSaveFileName(self, "Save Surface in Shadow (dat) Format", ".", "Shadow format (*.dat)")[0]

                if not file_path is None and not file_path.strip() == "":
                    self.check_values()

                    self.calculate_surface(self.parent(), int(self.bin_x), int(self.bin_y))

                    ST.write_shadow_surface(self.zz, numpy.round(self.xx, 6), numpy.round(self.yy, 6), file_path)
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)

                if self.parent().IS_DEVELOP: raise exception


        def save_oasys_surface(self):
            try:
                file_path = QFileDialog.getSaveFileName(self, "Save Surface in Oasys (hdf5) Format", ".", "HDF5 format (*.hdf5)")[0]

                if not file_path is None and not file_path.strip() == "":
                    self.check_values()

                    self.calculate_surface(self.parent(), int(self.bin_x), int(self.bin_y))

                    conv = self.parent().workspace_units_to_m

                    OU.write_surface_file(self.zz*conv, numpy.round(self.xx*conv, 8), numpy.round(self.yy*conv, 8), file_path)
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)

                if self.parent().IS_DEVELOP: raise exception

    def viewSurfaceShape(self):
        try:
            dialog = OpticalElement.ShowSurfaceShapeDialog(parent=self)
            dialog.show()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception), QtWidgets.QMessageBox.Ok)

            if self.parent().IS_DEVELOP: raise exception

    def selectFileFacetDescr(self):
        self.le_ms_file_facet_descr.setText(oasysgui.selectFileFromDialog(self, self.ms_file_facet_descr, "Select File with Facet Description"))

    def selectFileSurfRoughness(self):
        self.le_ms_file_surf_roughness.setText(oasysgui.selectFileFromDialog(self, self.ms_file_surf_roughness, "Select Surface Roughness File with PSD fn"))

    def selectFileWithParametersRz(self):
        self.le_ms_file_with_parameters_rz.setText(oasysgui.selectFileFromDialog(self, self.ms_file_with_parameters_rz, "Select File with parameters (r(z))"))

    def selectFileWithParametersRz2(self):
        self.le_ms_file_with_parameters_rz2.setText(oasysgui.selectFileFromDialog(self, self.ms_file_with_parameters_rz2, "Select File with parameters (r(z)\u00b2)"))

    def selectFileOrientations(self):
        self.le_ms_file_orientations.setText(oasysgui.selectFileFromDialog(self, self.ms_file_orientations, "Select File with Orientations"))

    def selectFilePolynomial(self):
        self.le_ms_file_polynomial.setText(oasysgui.selectFileFromDialog(self, self.ms_file_polynomial, "Select File with Polynomial"))

    def selectPrereflObjectFileName(self):
        self.le_file_prerefl_for_object_medium.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_for_object_medium, "Select File Prerefl for Object Medium"))

    def selectPrereflImageFileName(self):
        self.le_file_prerefl_for_image_medium.setText(oasysgui.selectFileFromDialog(self, self.file_prerefl_for_image_medium, "Select File Prerefl for Image Medium"))

    def calculate_incidence_angle_mrad(self):
        digits = 7

        if self.angles_respect_to == 0: self.incidence_angle_mrad = round(numpy.radians(90-self.incidence_angle_deg)*1000, digits)
        else:                           self.incidence_angle_mrad = round(numpy.radians(self.incidence_angle_deg)*1000, digits)

        if self.graphical_options.is_curved and not self.graphical_options.is_conic_coefficients:
            if self.incidence_angle_respect_to_normal_type == 0:
                if self.angles_respect_to == 0: self.incidence_angle_respect_to_normal = self.incidence_angle_deg
                else:                           self.incidence_angle_respect_to_normal = round(90 - self.incidence_angle_deg, 10)

        if self.graphical_options.is_mirror:
            self.reflection_angle_deg  = self.incidence_angle_deg
            self.reflection_angle_mrad = self.incidence_angle_mrad

    def calculate_reflection_angle_mrad(self):
        digits = 7

        if self.angles_respect_to == 0: self.reflection_angle_mrad = round(numpy.radians(90 - self.reflection_angle_deg)*1000, digits)
        else:                           self.reflection_angle_mrad = round(numpy.radians(self.reflection_angle_deg)*1000, digits)

    def calculate_incidence_angle_deg(self):
        digits = 10

        if self.angles_respect_to == 0: self.incidence_angle_deg = round(numpy.degrees(0.5 * numpy.pi - (self.incidence_angle_mrad / 1000)), digits)
        else:                           self.incidence_angle_deg = round(numpy.degrees(self.incidence_angle_mrad / 1000), digits)

        if self.graphical_options.is_mirror:
            self.reflection_angle_deg = self.incidence_angle_deg
            self.reflection_angle_mrad = self.incidence_angle_mrad

        if self.graphical_options.is_curved and not self.graphical_options.is_conic_coefficients:
            if self.incidence_angle_respect_to_normal_type == 0:
                if self.angles_respect_to == 0: self.incidence_angle_respect_to_normal = self.incidence_angle_deg
                else:                           self.incidence_angle_respect_to_normal = round(90 - self.incidence_angle_deg, digits)

    def calculate_reflection_angle_deg(self):
        digits = 10

        if self.angles_respect_to == 0: self.reflection_angle_deg = round(numpy.degrees(0.5*numpy.pi-(self.reflection_angle_mrad/1000)), digits)
        else:                           self.reflection_angle_deg = round(numpy.degrees(self.reflection_angle_mrad/1000), digits)

    def grab_dcm_value_from_oe(self):
        self.twotheta_bragg = self.incidence_angle_deg
        self.calculate_dcm_distances()

    def set_d1_as_source_plane(self):
        self.source_plane_distance = self.d_1

    def set_d1_as_image_plane(self):
        self.image_plane_distance = self.d_1

    def set_d2_as_source_plane(self):
        self.source_plane_distance = self.d_2

    def set_d2_as_image_plane(self):
        self.image_plane_distance = self.d_2

    def calculate_dcm_distances(self):
        if self.twotheta_bragg >= 45.0:
            twotheta = numpy.radians(2*(90-self.twotheta_bragg))

            self.d_1 = round(self.vertical_quote/numpy.sin(twotheta), 3)
            self.d_2 = round(self.total_distance - self.vertical_quote/numpy.tan(twotheta), 3)
        else:
            self.d_1 = numpy.nan
            self.d_2 = numpy.nan

    def populateFields(self, shadow_oe = ShadowOpticalElement.create_empty_oe()):
        if self.graphical_options.is_ideal_lens:
            shadow_oe._oe.user_units_to_cm = self.workspace_units_to_cm
        else:
            shadow_oe._oe.DUMMY = self.workspace_units_to_cm # Issue #3 : Global User's Unit

        shadow_oe._oe.T_SOURCE = self.source_plane_distance
        shadow_oe._oe.T_IMAGE = self.image_plane_distance

        if self.graphical_options.is_screen_slit:
            shadow_oe._oe.T_INCIDENCE  = 0.0
            shadow_oe._oe.T_REFLECTION = 180.0
            shadow_oe._oe.ALPHA        = 0.0
        elif self.graphical_options.is_ideal_lens:
            shadow_oe._oe.focal_x      = self.focal_x
            shadow_oe._oe.focal_z      = self.focal_z
        elif self.graphical_options.is_empty:
            shadow_oe._oe.T_INCIDENCE  = self.incidence_angle_deg
            shadow_oe._oe.T_REFLECTION = self.reflection_angle_deg
            if self.mirror_orientation_angle < 4:    shadow_oe._oe.ALPHA = 90*self.mirror_orientation_angle
            elif self.mirror_orientation_angle == 4: shadow_oe._oe.ALPHA = self.mirror_orientation_angle_user_value
        else:
            if self.angles_respect_to == 0:
                shadow_oe._oe.T_INCIDENCE  = self.incidence_angle_deg
                shadow_oe._oe.T_REFLECTION = self.reflection_angle_deg
            else:
                shadow_oe._oe.T_INCIDENCE  = 90-self.incidence_angle_deg
                shadow_oe._oe.T_REFLECTION = 90-self.reflection_angle_deg

            if self.mirror_orientation_angle < 4:
                shadow_oe._oe.ALPHA        = 90*self.mirror_orientation_angle
            else:
                shadow_oe._oe.ALPHA = self.mirror_orientation_angle_user_value
            #####################################
            # BASIC SETTING
            #####################################

            if self.graphical_options.is_curved:
                if self.graphical_options.is_toroidal or self.graphical_options.is_conic_coefficients:
                   shadow_oe._oe.FCYL = 0
                elif self.is_cylinder==1:
                   shadow_oe._oe.FCYL = 1
                   shadow_oe._oe.CIL_ANG=90*self.cylinder_orientation
                else:
                   shadow_oe._oe.FCYL = 0

                if self.graphical_options.is_conic_coefficients:
                    conic_coefficients = [self.conic_coefficient_0,
                                          self.conic_coefficient_1,
                                          self.conic_coefficient_2,
                                          self.conic_coefficient_3,
                                          self.conic_coefficient_4,
                                          self.conic_coefficient_5,
                                          self.conic_coefficient_6,
                                          self.conic_coefficient_7,
                                          self.conic_coefficient_8,
                                          self.conic_coefficient_9]

                    shadow_oe._oe.F_EXT = 1
                    shadow_oe._oe.CCC[:] = conic_coefficients[:]
                elif self.graphical_options.is_hyperboloid and \
                        self.surface_shape_parameters == 0 and \
                        self.focii_and_continuation_plane == 1 \
                        and self.object_side_focal_distance < 0:
                    conic_coefficients = self.set_hyperboloid_from_focal_distances()

                    if self.is_cylinder == 1: self.set_hyperboloid_cylindrical(conic_coefficients)

                    shadow_oe._oe.FMIRR = 10 # conic coefficients
                    shadow_oe._oe.F_EXT = 1
                    shadow_oe._oe.FCYL  = 0
                    shadow_oe._oe.CCC[:] = conic_coefficients[:]
                else:
                    if self.surface_shape_parameters == 0:
                       if (self.is_cylinder==1 and self.cylinder_orientation==1 and self.graphical_options.is_spheric):
                           shadow_oe._oe.F_EXT=1

                           #IMPLEMENTATION OF THE AUTOMATIC CALCULATION OF THE SAGITTAL FOCUSING FOR SPHERICAL CYLINDERS
                           # RADIUS = (2 F1 F2 sin (theta)) /( F1+F2)
                           if self.focii_and_continuation_plane == 0:
                              self.spherical_radius = ((2*self.source_plane_distance*self.image_plane_distance)/(self.source_plane_distance+self.image_plane_distance))*numpy.sin(self.reflection_angle_mrad*1e-3)
                           else:
                              self.spherical_radius = ((2*self.object_side_focal_distance*self.image_side_focal_distance)/(self.object_side_focal_distance+self.image_side_focal_distance))*numpy.sin(numpy.radians(90-self.incidence_angle_respect_to_normal))

                           shadow_oe._oe.RMIRR = self.spherical_radius
                       else:
                           shadow_oe._oe.F_EXT = 0

                           if self.focii_and_continuation_plane == 0:
                              shadow_oe._oe.F_DEFAULT=1
                           else:
                              shadow_oe._oe.F_DEFAULT=0
                              shadow_oe._oe.SSOUR = self.object_side_focal_distance
                              shadow_oe._oe.SIMAG = self.image_side_focal_distance
                              shadow_oe._oe.THETA = self.incidence_angle_respect_to_normal

                           if self.graphical_options.is_paraboloid: shadow_oe._oe.F_SIDE=self.focus_location
                    else:
                       shadow_oe._oe.F_EXT=1
                       if self.graphical_options.is_spheric:
                           shadow_oe._oe.RMIRR = self.spherical_radius
                       elif self.graphical_options.is_toroidal:
                           shadow_oe._oe.R_MAJ=self.torus_major_radius
                           shadow_oe._oe.R_MIN=self.torus_minor_radius
                       elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                           shadow_oe._oe.AXMAJ=self.ellipse_hyperbola_semi_major_axis
                           shadow_oe._oe.AXMIN=self.ellipse_hyperbola_semi_minor_axis
                           shadow_oe._oe.ELL_THE=self.angle_of_majax_and_pole
                       elif self.graphical_options.is_paraboloid:
                           shadow_oe._oe.PARAM=self.paraboloid_parameter

                    if self.graphical_options.is_toroidal:
                        shadow_oe._oe.F_TORUS=self.toroidal_mirror_pole_location
                    else:
                        if self.surface_curvature == 0:
                           shadow_oe._oe.F_CONVEX=0
                        else:
                           shadow_oe._oe.F_CONVEX=1
            else:
               shadow_oe._oe.FCYL = 0

            if self.graphical_options.is_mirror:
                if self.reflectivity_type == 0:
                   shadow_oe._oe.F_REFLEC = 0
                elif self.reflectivity_type == 1:
                    if self.source_of_reflectivity == 0:
                        shadow_oe._oe.F_REFLEC = 1
                        shadow_oe._oe.F_REFL = 0
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 1:
                        shadow_oe._oe.F_REFLEC = 1
                        shadow_oe._oe.F_REFL = 1
                        shadow_oe._oe.FILE_REFL = 'GAAS.SHA'
                        shadow_oe._oe.ALFA = self.alpha
                        shadow_oe._oe.GAMMA = self.gamma
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 2:
                        shadow_oe._oe.F_REFLEC = 1
                        shadow_oe._oe.F_REFL = 2
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl_m), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = self.m_layer_tickness
                elif self.reflectivity_type == 2:
                    if self.source_of_reflectivity == 0:
                        shadow_oe._oe.F_REFLEC = 2
                        shadow_oe._oe.F_REFL = 0
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 1:
                        shadow_oe._oe.F_REFLEC = 2
                        shadow_oe._oe.F_REFL = 1
                        shadow_oe._oe.FILE_REFL = 'GAAS.SHA'
                        shadow_oe._oe.ALFA = self.alpha
                        shadow_oe._oe.GAMMA = self.gamma
                        shadow_oe._oe.F_THICK = 0
                    elif self.source_of_reflectivity == 2:
                        shadow_oe._oe.F_REFLEC = 2
                        shadow_oe._oe.F_REFL = 2
                        shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_prerefl_m), 'utf-8')
                        shadow_oe._oe.ALFA = 0.0
                        shadow_oe._oe.GAMMA = 0.0
                        shadow_oe._oe.F_THICK = self.m_layer_tickness
            elif self.graphical_options.is_crystal:
                shadow_oe._oe.F_REFLEC = 0

                if self.diffraction_calculation == 1:
                    shadow_oe._oe.F_CRYSTAL = 0  # user defined profile -> simulated as mirror with no reflectivity
                else:
                    shadow_oe._oe.F_CRYSTAL = 1
                    shadow_oe._oe.FILE_REFL = bytes(congruence.checkFileName(self.file_crystal_parameters), 'utf-8')
                    shadow_oe._oe.F_REFLECT = 0
                    shadow_oe._oe.F_BRAGG_A = 0
                    shadow_oe._oe.A_BRAGG = 0.0
                    shadow_oe._oe.F_REFRACT = 0

                    shadow_oe._oe.F_REFRAC = self.diffraction_geometry

                    if self.crystal_auto_setting == 0:
                        shadow_oe._oe.F_CENTRAL = 0
                    else:
                        shadow_oe._oe.F_CENTRAL = 1
                        shadow_oe._oe.F_PHOT_CENT = self.units_in_use
                        shadow_oe._oe.PHOT_CENT = self.photon_energy
                        shadow_oe._oe.R_LAMBDA = self.photon_wavelength

                    if self.mosaic_crystal == 1:
                        shadow_oe._oe.F_MOSAIC = 1
                        shadow_oe._oe.MOSAIC_SEED = self.seed_for_mosaic
                        shadow_oe._oe.SPREAD_MOS = self.angle_spread_FWHM
                        shadow_oe._oe.THICKNESS = self.thickness
                    else:
                        if self.asymmetric_cut == 1:
                            shadow_oe._oe.F_BRAGG_A = 1
                            shadow_oe._oe.A_BRAGG = self.planes_angle
                            shadow_oe._oe.ORDER = self.below_onto_bragg_planes
                            shadow_oe._oe.THICKNESS = self.thickness
                        if self.johansson_geometry == 1:
                            shadow_oe._oe.F_JOHANSSON = 1
                            shadow_oe._oe.F_EXT = 1
                            shadow_oe._oe.R_JOHANSSON = self.johansson_radius
            elif self.graphical_options.is_grating:
                shadow_oe._oe.F_REFLEC = 0

                if self.grating_ruling_type == 0 or self.grating_ruling_type == 1:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = self.grating_ruling_type
                    shadow_oe._oe.RULING = self.grating_ruling_density
                elif self.grating_ruling_type == 2:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = 2
                    shadow_oe._oe.HOLO_R1  = self.grating_holo_left_distance
                    shadow_oe._oe.HOLO_R2  = self.grating_holo_right_distance
                    shadow_oe._oe.HOLO_DEL = self.grating_holo_left_incidence_angle
                    shadow_oe._oe.HOLO_GAM = self.grating_holo_right_incidence_angle
                    shadow_oe._oe.HOLO_W   = self.grating_holo_recording_wavelength
                    shadow_oe._oe.HOLO_RT1 = self.grating_holo_left_azimuth_from_y
                    shadow_oe._oe.HOLO_RT2 = self.grating_holo_right_azimuth_from_y
                    shadow_oe._oe.F_PW = self.grating_holo_pattern_type
                    shadow_oe._oe.F_PW_C = self.grating_holo_cylindrical_source
                    shadow_oe._oe.F_VIRTUAL = self.grating_holo_source_type
                elif self.grating_ruling_type == 3:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = 3
                    shadow_oe._oe.AZIM_FAN = self.grating_groove_pole_azimuth_from_y
                    shadow_oe._oe.DIST_FAN = self.grating_groove_pole_distance
                    shadow_oe._oe.COMA_FAC = self.grating_coma_correction_factor
                elif self.grating_ruling_type == 4:
                    shadow_oe._oe.F_GRATING = 1
                    shadow_oe._oe.F_RULING = 5
                    shadow_oe._oe.F_RUL_ABS = self.grating_poly_signed_absolute
                    shadow_oe._oe.RULING = self.grating_ruling_density
                    shadow_oe._oe.RUL_A1 = self.grating_poly_coeff_1
                    shadow_oe._oe.RUL_A2 = self.grating_poly_coeff_2
                    shadow_oe._oe.RUL_A3 = self.grating_poly_coeff_3
                    shadow_oe._oe.RUL_A4 = self.grating_poly_coeff_4

                shadow_oe._oe.ORDER = self.grating_diffraction_order

                if self.grating_auto_setting == 0:
                    shadow_oe._oe.F_CENTRAL=0
                else:
                    shadow_oe._oe.F_CENTRAL = 1
                    shadow_oe._oe.F_PHOT_CENT = self.grating_units_in_use
                    shadow_oe._oe.PHOT_CENT = self.grating_photon_energy
                    shadow_oe._oe.R_LAMBDA = self.grating_photon_wavelength
                    shadow_oe._oe.F_MONO = self.grating_mount_type

                    if self.grating_mount_type != 4:
                        shadow_oe._oe.F_HUNT = 1
                        shadow_oe._oe.HUNT_H = 0.0
                        shadow_oe._oe.HUNT_L = 0.0
                        shadow_oe._oe.BLAZE = 0.0
                    else:
                        shadow_oe._oe.F_HUNT = self.grating_hunter_grating_selected+1
                        shadow_oe._oe.HUNT_H = self.grating_hunter_distance_between_beams
                        shadow_oe._oe.HUNT_L = self.grating_hunter_monochromator_length
                        shadow_oe._oe.BLAZE = self.grating_hunter_blaze_angle
            elif self.graphical_options.is_refractor:
                shadow_oe._oe.F_R_IND =  self.optical_constants_refraction_index

                if self.optical_constants_refraction_index == 0:
                    shadow_oe._oe.R_IND_OBJ = self.refractive_index_in_object_medium
                    shadow_oe._oe.R_ATTENUATION_OBJ = self.attenuation_in_object_medium
                    shadow_oe._oe.R_IND_IMA =self.refractive_index_in_image_medium
                    shadow_oe._oe.R_ATTENUATION_IMA = self.attenuation_in_image_medium
                elif self.optical_constants_refraction_index == 1:
                    shadow_oe._oe.FILE_R_IND_OBJ = bytes(congruence.checkFileName(self.file_prerefl_for_object_medium), 'utf-8')
                    shadow_oe._oe.R_IND_IMA = self.refractive_index_in_image_medium
                    shadow_oe._oe.R_ATTENUATION_IMA = self.attenuation_in_image_medium
                elif self.optical_constants_refraction_index == 2:
                    shadow_oe._oe.R_IND_OBJ = self.refractive_index_in_object_medium
                    shadow_oe._oe.R_ATTENUATION_OBJ = self.attenuation_in_object_medium
                    shadow_oe._oe.FILE_R_IND_IMA = bytes(congruence.checkFileName(self.file_prerefl_for_image_medium), 'utf-8')
                elif self.optical_constants_refraction_index == 3:
                    shadow_oe._oe.FILE_R_IND_OBJ = bytes(congruence.checkFileName(self.file_prerefl_for_object_medium), 'utf-8')
                    shadow_oe._oe.FILE_R_IND_IMA = bytes(congruence.checkFileName(self.file_prerefl_for_image_medium), 'utf-8')

            if self.is_infinite == 0:
                shadow_oe._oe.FHIT_C = 0
            else:
                shadow_oe._oe.FHIT_C = 1
                shadow_oe._oe.FSHAPE = (self.mirror_shape+1)
                shadow_oe._oe.RLEN1  = self.dim_y_plus
                shadow_oe._oe.RLEN2  = self.dim_y_minus
                shadow_oe._oe.RWIDX1 = self.dim_x_plus
                shadow_oe._oe.RWIDX2 = self.dim_x_minus

            #####################################
            # ADVANCED SETTING
            #####################################

            if self.modified_surface == 1:
                 if self.ms_type_of_defect == 0:
                     shadow_oe._oe.F_RIPPLE = 1
                     shadow_oe._oe.F_G_S = 0
                     shadow_oe._oe.X_RIP_AMP = self.ms_ripple_ampli_x
                     shadow_oe._oe.X_RIP_WAV = self.ms_ripple_wavel_x
                     shadow_oe._oe.X_PHASE   = self.ms_ripple_phase_x
                     shadow_oe._oe.Y_RIP_AMP = self.ms_ripple_ampli_y
                     shadow_oe._oe.Y_RIP_WAV = self.ms_ripple_wavel_y
                     shadow_oe._oe.Y_PHASE   = self.ms_ripple_phase_y
                     shadow_oe._oe.FILE_RIP  = b''
                 else:
                     shadow_oe._oe.F_RIPPLE = 1
                     shadow_oe._oe.F_G_S = self.ms_type_of_defect
                     shadow_oe._oe.X_RIP_AMP = 0.0
                     shadow_oe._oe.X_RIP_WAV = 0.0
                     shadow_oe._oe.X_PHASE   = 0.0
                     shadow_oe._oe.Y_RIP_AMP = 0.0
                     shadow_oe._oe.Y_RIP_WAV = 0.0
                     shadow_oe._oe.Y_PHASE   = 0.0
                     shadow_oe._oe.FILE_RIP  = bytes(congruence.checkFileName(self.ms_defect_file_name), 'utf-8')

            elif self.modified_surface == 2:
                shadow_oe._oe.F_FACET = 1
                shadow_oe._oe.FILE_FAC=bytes(congruence.checkFileName(self.ms_file_facet_descr), 'utf-8')
                shadow_oe._oe.F_FAC_LATT=self.ms_lattice_type
                shadow_oe._oe.F_FAC_ORIENT=self.ms_orientation
                shadow_oe._oe.F_POLSEL=self.ms_lattice_type+1
                shadow_oe._oe.RFAC_LENX=self.ms_facet_width_x
                shadow_oe._oe.RFAC_PHAX=self.ms_facet_phase_x
                shadow_oe._oe.RFAC_DELX1=self.ms_dead_width_x_minus
                shadow_oe._oe.RFAC_DELX2=self.ms_dead_width_x_plus
                shadow_oe._oe.RFAC_LENY=self.ms_facet_width_y
                shadow_oe._oe.RFAC_PHAY=self.ms_facet_phase_y
                shadow_oe._oe.RFAC_DELY1=self.ms_dead_width_y_minus
                shadow_oe._oe.RFAC_DELY2=self.ms_dead_width_y_plus
            elif self.modified_surface == 3:
                shadow_oe._oe.F_ROUGHNESS = 1
                shadow_oe._oe.FILE_ROUGH=bytes(congruence.checkFileName(self.ms_file_surf_roughness), 'utf-8')
                shadow_oe._oe.ROUGH_X=self.ms_roughness_rms_x
                shadow_oe._oe.ROUGH_Y=self.ms_roughness_rms_y
            elif self.modified_surface == 4:
                shadow_oe._oe.F_KOMA = 1
                shadow_oe._oe.F_KOMA_CA=self.ms_specify_rz2
                shadow_oe._oe.FILE_KOMA=bytes(congruence.checkFileName(self.ms_file_with_parameters_rz), 'utf-8')
                shadow_oe._oe.FILE_KOMA_CA=bytes(congruence.checkFileName(self.ms_file_with_parameters_rz2), 'utf-8')
                shadow_oe._oe.F_KOMA_BOUNCE=self.ms_save_intercept_bounces
            elif self.modified_surface == 5:
                shadow_oe._oe.F_SEGMENT = 1
                shadow_oe._oe.ISEG_XNUM=self.ms_number_of_segments_x
                shadow_oe._oe.ISEG_YNUM=self.ms_number_of_segments_y
                shadow_oe._oe.SEG_LENX=self.ms_length_of_segments_x
                shadow_oe._oe.SEG_LENY=self.ms_length_of_segments_y
                shadow_oe._oe.FILE_SEGMENT=bytes(congruence.checkFileName(self.ms_file_orientations), 'utf-8')
                shadow_oe._oe.FILE_SEGP=bytes(congruence.checkFileName(self.ms_file_polynomial), 'utf-8')

        if not self.graphical_options.is_ideal_lens:
            if not (self.graphical_options.is_empty or self.graphical_options.is_screen_slit):
                if self.mirror_movement == 1:
                     shadow_oe._oe.F_MOVE=1
                     shadow_oe._oe.OFFX=self.mm_mirror_offset_x
                     shadow_oe._oe.OFFY=self.mm_mirror_offset_y
                     shadow_oe._oe.OFFZ=self.mm_mirror_offset_z
                     shadow_oe._oe.X_ROT=self.mm_mirror_rotation_x
                     shadow_oe._oe.Y_ROT=self.mm_mirror_rotation_y
                     shadow_oe._oe.Z_ROT=self.mm_mirror_rotation_z

            if self.source_movement == 1:
                 shadow_oe._oe.FSTAT=1
                 shadow_oe._oe.RTHETA=self.sm_angle_of_incidence
                 shadow_oe._oe.RDSOUR=self.sm_distance_from_mirror
                 shadow_oe._oe.ALPHA_S=self.sm_z_rotation
                 shadow_oe._oe.OFF_SOUX=self.sm_offset_x_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUY=self.sm_offset_y_mirr_ref_frame
                 shadow_oe._oe.OFF_SOUZ=self.sm_offset_z_mirr_ref_frame
                 shadow_oe._oe.X_SOUR=self.sm_offset_x_source_ref_frame
                 shadow_oe._oe.Y_SOUR=self.sm_offset_y_source_ref_frame
                 shadow_oe._oe.Z_SOUR=self.sm_offset_z_source_ref_frame
                 shadow_oe._oe.X_SOUR_ROT=self.sm_rotation_around_x
                 shadow_oe._oe.Y_SOUR_ROT=self.sm_rotation_around_y
                 shadow_oe._oe.Z_SOUR_ROT=self.sm_rotation_around_z

        if self.file_to_write_out == 4:
            shadow_oe._oe.FWRITE=0
        else:
            shadow_oe._oe.FWRITE=self.file_to_write_out

        if self.graphical_options.is_crystal and self.diffraction_calculation == 1:
            shadow_oe._oe.F_ANGLE = 1
        elif self.graphical_options.is_mirror and self.reflectivity_type > 0 and self.source_of_reflectivity == 3:
            shadow_oe._oe.F_ANGLE = 1
        else:
            shadow_oe._oe.F_ANGLE = self.write_out_inc_ref_angles

    import numpy

    def set_hyperboloid_from_focal_distances(self):
        ccc = numpy.zeros(10)

        theta = numpy.radians(self.incidence_angle_respect_to_normal)
        SSOUR = self.object_side_focal_distance
        SIMAG = self.image_side_focal_distance

        AXMAJ = -(SSOUR + SIMAG) / 2
        # ;C
        # ;C If AXMAJ > 0, then we are on the left branch of the hyp. Else we
        # ;C are onto the right one. We have to discriminate between the two cases
        # ;C In particular, if AXMAJ.LT.0 then the hiperb. will be convex.
        # ;C
        AFOCI = 0.5 * numpy.sqrt(SSOUR ** 2 + SIMAG ** 2 - 2 * SSOUR * SIMAG * numpy.cos(2 * theta))
        AXMIN = numpy.sqrt(AFOCI ** 2 - AXMAJ ** 2)

        ECCENT = AFOCI / AXMAJ

        # ;C
        # ;C Computes the center coordinates in the hiperbola RF.
        # ;C
        YCEN = (SSOUR + AXMAJ) / ECCENT

        ZCEN_ARG = numpy.abs(YCEN ** 2 / AXMAJ ** 2 - 1.0)
        ZCEN     = AXMIN * numpy.sqrt(ZCEN_ARG)  # < 0

        # ;C
        # ;C Computes now the normal in the same RF. The signs are forced to
        # ;C suit our RF.
        # ;C

        RNCEN = numpy.zeros(3)
        RNCEN[1 - 1] = 0.0
        RNCEN[2 - 1] = YCEN / AXMAJ ** 2  # < 0
        RNCEN[3 - 1] = ZCEN / AXMIN ** 2  # > 0

        RNCEN = RNCEN / numpy.sqrt((RNCEN ** 2).sum())
        # ;C
        # ;C Computes the tangent in the same RF
        # ;C
        # ;C
        # ;C Coefficients of the canonical form
        # ;C
        A = 1 / AXMIN ** 2
        B = - 1 / AXMAJ ** 2
        C = A
        # ;C
        # ;C Rotate now in the mirror RF. The equations are the same as for the
        # ;C ellipse case.
        # ;C
        ccc[0] = A
        ccc[1] = B * RNCEN[3 - 1] ** 2 + C * RNCEN[2 - 1] ** 2
        ccc[2] = B * RNCEN[2 - 1] ** 2 + C * RNCEN[3 - 1] ** 2
        ccc[3] = 0.0
        ccc[4] = 2 * (B * RNCEN[2 - 1] * RNCEN[3 - 1] - C * RNCEN[3 - 1] * RNCEN[2 - 1])
        ccc[5] = 0.0
        ccc[6] = 0.0
        ccc[7] = 0.0
        ccc[8] = -2 * (B * YCEN * RNCEN[2 - 1] + C * ZCEN * RNCEN[3 - 1])
        ccc[9] = 0.0

        return ccc

    def set_hyperboloid_cylindrical(self, ccc):
        CIL_ANG = self.cylinder_orientation * 0.5 * numpy.pi
        COS_CIL = numpy.cos(CIL_ANG)
        SIN_CIL = numpy.sin(CIL_ANG)

        A_1 =  ccc[0]
        A_2 =  ccc[1]
        A_3 =  ccc[2]
        A_4 =  ccc[3]
        A_5 =  ccc[4]
        A_6 =  ccc[5]
        A_7 =  ccc[6]
        A_8 =  ccc[7]
        A_9 =  ccc[8]
        A_10 = ccc[9]

        ccc[0] = A_1 * SIN_CIL ** 4 + A_2 * COS_CIL ** 2 * SIN_CIL ** 2 - A_4 * COS_CIL * SIN_CIL ** 3
        ccc[1] = A_2 * COS_CIL ** 4 + A_1 * COS_CIL ** 2 * SIN_CIL ** 2 - A_4 * COS_CIL ** 3 * SIN_CIL
        ccc[2] = A_3  # Z^2
        ccc[3] = - 2 * A_1 * COS_CIL * SIN_CIL ** 3 - 2 * A_2 * COS_CIL ** 3 * SIN_CIL + 2 * A_4 * COS_CIL ** 2 * SIN_CIL ** 2  # X Y
        ccc[4] = A_5 * COS_CIL ** 2 - A_6 * COS_CIL * SIN_CIL  # Y Z
        ccc[5] = A_6 * SIN_CIL ** 2 - A_5 * COS_CIL * SIN_CIL  # X Z
        ccc[6] = A_7 * SIN_CIL ** 2 - A_8 * COS_CIL * SIN_CIL  # X
        ccc[7] = A_8 * COS_CIL ** 2 - A_7 * COS_CIL * SIN_CIL  # Y
        ccc[8] = A_9  # Z
        ccc[9] = A_10

    def doSpecificSetting(self, shadow_oe):
        pass

    def checkFields(self):
        if self.graphical_options.is_screen_slit:
            self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

            if self.source_movement == 1:
                self.sm_distance_from_mirror = congruence.checkNumber(self.sm_distance_from_mirror, "Source Movement: Distance from O.E.")

            if self.aperturing == 1:
                if self.aperture_shape == 2:
                    congruence.checkFile(self.external_file_with_coordinate)

            if self.absorption == 1:
                self.thickness = congruence.checkPositiveNumber(self.thickness, "Absorption: thickness")

                ShadowCongruence.checkPreReflFile(congruence.checkFile(self.opt_const_file_name))
        elif self.graphical_options.is_ideal_lens:
            if self.focal_x == 0.0: raise  Exception("Focal Distance X should be <> 0")
            if self.focal_z == 0.0: raise  Exception("Focal Distance Z should be <> 0")
        elif self.graphical_options.is_empty:
            self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

            if self.source_movement == 1:
                self.sm_distance_from_mirror = congruence.checkNumber(self.sm_distance_from_mirror, "Source Movement: Distance from O.E.")
        else:
            self.source_plane_distance = congruence.checkNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = congruence.checkNumber(self.image_plane_distance, "Image plane distance")

            if self.graphical_options.is_curved:
                if self.surface_shape_parameters == 0:
                   if not self.focii_and_continuation_plane == 0:
                        self.object_side_focal_distance = congruence.checkNumber(self.object_side_focal_distance, "Object side focal distance")
                        self.image_side_focal_distance = congruence.checkNumber(self.image_side_focal_distance, "Image side focal distance")

                   if self.graphical_options.is_paraboloid:
                        self.focus_location = congruence.checkNumber(self.focus_location, "Focus location")
                else:
                   if self.graphical_options.is_spheric:
                       self.spherical_radius = congruence.checkStrictlyPositiveNumber(self.spherical_radius, "Spherical radius")
                   elif self.graphical_options.is_toroidal:
                       self.torus_major_radius = congruence.checkStrictlyPositiveNumber(self.torus_major_radius, "Torus major radius")
                       self.torus_minor_radius = congruence.checkStrictlyPositiveNumber(self.torus_minor_radius, "Torus minor radius")
                   elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                       self.ellipse_hyperbola_semi_major_axis = congruence.checkStrictlyPositiveNumber(self.ellipse_hyperbola_semi_major_axis, "Semi major axis")
                       self.ellipse_hyperbola_semi_minor_axis = congruence.checkStrictlyPositiveNumber(self.ellipse_hyperbola_semi_minor_axis, "Semi minor axis")
                       self.angle_of_majax_and_pole = congruence.checkPositiveNumber(self.angle_of_majax_and_pole, "Angle of MajAx and Pole")
                   elif self.graphical_options.is_paraboloid:
                       self.paraboloid_parameter = congruence.checkNumber(self.paraboloid_parameter, "Paraboloid parameter")

            if self.graphical_options.is_mirror:
                if not self.reflectivity_type == 0:
                    if self.source_of_reflectivity == 0:
                        ShadowCongruence.checkPreReflFile(congruence.checkFile(self.file_prerefl))
                    elif self.source_of_reflectivity == 2:
                        ShadowCongruence.checkPreMLayerFile(congruence.checkFile(self.file_prerefl_m))
                    elif self.source_of_reflectivity == 3:
                        ShadowCongruence.check2ColumnFormatFile(congruence.checkFile(self.file_reflectivity), "Mirror reflectivity")
            elif self.graphical_options.is_crystal:
                if self.diffraction_calculation == 1:
                    ShadowCongruence.check2ColumnFormatFile(congruence.checkFile(self.file_diffraction_profile), "Diffraction profile")
                    congruence.checkStrictlyPositiveAngle(self.user_defined_bragg_angle, "Bragg Angle")
                    congruence.checkNumber(self.user_defined_h, "User Defined Milled Index h")
                    congruence.checkNumber(self.user_defined_k, "User Defined Milled Index k")
                    congruence.checkNumber(self.user_defined_l, "User Defined Milled Index l")
                else:
                    ShadowCongruence.checkBraggFile(congruence.checkFile(self.file_crystal_parameters))

                    if not self.crystal_auto_setting == 0:
                        if self.units_in_use == 0:
                            self.photon_energy = congruence.checkPositiveNumber(self.photon_energy, "Photon Energy")
                        elif self.units_in_use == 1:
                            self.photon_wavelength = congruence.checkPositiveNumber(self.photon_wavelength,
                                                                                   "Photon Wavelength")

                    if self.mosaic_crystal == 1:
                        self.seed_for_mosaic = congruence.checkPositiveNumber(self.seed_for_mosaic,
                                                                             "Crystal: Seed for mosaic")
                        self.angle_spread_FWHM = congruence.checkPositiveNumber(self.angle_spread_FWHM,
                                                                               "Crystal: Angle spread FWHM")
                        self.thickness = congruence.checkPositiveNumber(self.thickness, "Crystal: thickness")
                    else:
                        if self.asymmetric_cut == 1:
                            self.thickness = congruence.checkPositiveNumber(self.thickness, "Crystal: thickness")
                        if self.johansson_geometry == 1:
                            self.johansson_radius = congruence.checkPositiveNumber(self.johansson_radius,
                                                                                  "Crystal: Johansson radius")
            elif self.graphical_options.is_grating:
                if not self.grating_auto_setting == 0:
                    if self.grating_units_in_use == 0:
                        self.grating_photon_energy = congruence.checkPositiveNumber(self.grating_photon_energy, "Photon Energy")
                    elif self.grating_units_in_use == 1:
                        self.grating_photon_wavelength = congruence.checkPositiveNumber(self.grating_photon_wavelength, "Photon Wavelength")

                    if self.grating_mount_type == 4:
                        self.grating_hunter_monochromator_length = congruence.checkPositiveNumber(self.grating_hunter_monochromator_length, "Monochromator length")
                        self.grating_hunter_distance_between_beams = congruence.checkPositiveNumber(self.grating_hunter_distance_between_beams, "Distance between beams")

                if self.grating_ruling_type == 0 or self.grating_ruling_type == 1 or self.grating_ruling_type == 3:
                    self.grating_ruling_density = congruence.checkPositiveNumber(self.grating_ruling_density, "Ruling Density")
                elif self.grating_ruling_type == 2:
                    self.grating_holo_recording_wavelength = congruence.checkPositiveNumber(self.grating_holo_recording_wavelength, "Recording Wavelength")
                elif self.grating_ruling_type == 4:
                    self.grating_ruling_density = congruence.checkPositiveNumber(self.grating_ruling_density, "Polynomial Line Density coeff.: 0th")

                if self.grating_use_efficiency == 1:
                    ShadowCongruence.check2ColumnFormatFile(congruence.checkFile(self.grating_file_efficiency), "Grating Efficiency")

            elif self.graphical_options.is_refractor:
                if self.optical_constants_refraction_index == 0:
                    self.refractive_index_in_object_medium = congruence.checkPositiveNumber(self.refractive_index_in_object_medium, "Refractive Index in Object Medium")
                    self.attenuation_in_object_medium = congruence.checkNumber(self.attenuation_in_object_medium, "Refractive Index in Object Medium")
                    self.refractive_index_in_image_medium = congruence.checkPositiveNumber(self.refractive_index_in_image_medium, "Refractive Index in Image Medium")
                    self.attenuation_in_image_medium = congruence.checkNumber(self.attenuation_in_image_medium, "Refractive Index in Image Medium")
                elif self.optical_constants_refraction_index == 1:
                    congruence.checkFile(self.file_prerefl_for_object_medium)
                    self.refractive_index_in_image_medium = congruence.checkPositiveNumber(self.refractive_index_in_image_medium, "Refractive Index in Image Medium")
                    self.attenuation_in_image_medium = congruence.checkNumber(self.attenuation_in_image_medium, "Refractive Index in Image Medium")
                elif self.optical_constants_refraction_index == 2:
                    self.refractive_index_in_object_medium = congruence.checkPositiveNumber(self.refractive_index_in_object_medium, "Refractive Index in Object Medium")
                    self.attenuation_in_object_medium = congruence.checkNumber(self.attenuation_in_object_medium, "Refractive Index in Object Medium")
                    congruence.checkFile(self.file_prerefl_for_image_medium)
                elif self.optical_constants_refraction_index == 3:
                    congruence.checkFile(self.file_prerefl_for_object_medium)
                    congruence.checkFile(self.file_prerefl_for_image_medium)

            if not self.is_infinite == 0:
               self.dim_y_plus = congruence.checkPositiveNumber(self.dim_y_plus, "Dimensions: y plus")
               self.dim_y_minus = congruence.checkPositiveNumber(self.dim_y_minus, "Dimensions: y minus")
               self.dim_x_plus = congruence.checkPositiveNumber(self.dim_x_plus, "Dimensions: x plus")
               self.dim_x_minus = congruence.checkPositiveNumber(self.dim_x_minus, "Dimensions: x minus")

            if self.mirror_orientation_angle == 4:
                self.mirror_orientation_angle_user_value = congruence.checkNumber(self.mirror_orientation_angle_user_value, "O.E. Orientation Angle [deg]")

            #####################################
            # ADVANCED SETTING
            #####################################

            if self.modified_surface == 1:
                 if self.ms_type_of_defect == 0:
                     self.ms_ripple_ampli_x = congruence.checkPositiveNumber(self.ms_ripple_ampli_x , "Modified Surface: Ripple Amplitude x")
                     self.ms_ripple_wavel_x = congruence.checkPositiveNumber(self.ms_ripple_wavel_x , "Modified Surface: Ripple Wavelength x")
                     self.ms_ripple_ampli_y = congruence.checkPositiveNumber(self.ms_ripple_ampli_y , "Modified Surface: Ripple Amplitude y")
                     self.ms_ripple_wavel_y = congruence.checkPositiveNumber(self.ms_ripple_wavel_y , "Modified Surface: Ripple Wavelength y")
                 else:
                     ShadowCongruence.checkErrorProfileFile(congruence.checkFile(self.ms_defect_file_name))
            elif self.modified_surface == 2:
                congruence.checkFile(self.ms_file_facet_descr)
                self.ms_facet_width_x = congruence.checkPositiveNumber(self.ms_facet_width_x, "Modified Surface: Facet width x")
                self.ms_facet_phase_x = congruence.checkPositiveAngle(self.ms_facet_phase_x, "Modified Surface: Facet phase x")
                self.ms_dead_width_x_minus = congruence.checkPositiveNumber(self.ms_dead_width_x_minus, "Modified Surface: Dead width x minus")
                self.ms_dead_width_x_plus = congruence.checkPositiveNumber(self.ms_dead_width_x_plus, "Modified Surface: Dead width x plus")
                self.ms_facet_width_y = congruence.checkPositiveNumber(self.ms_facet_width_y, "Modified Surface: Facet width y")
                self.ms_facet_phase_y = congruence.checkPositiveAngle(self.ms_facet_phase_y, "Modified Surface: Facet phase y")
                self.ms_dead_width_y_minus = congruence.checkPositiveNumber(self.ms_dead_width_y_minus, "Modified Surface: Dead width y minus")
                self.ms_dead_width_y_plus = congruence.checkPositiveNumber(self.ms_dead_width_y_plus, "Modified Surface: Dead width y plus")
            elif self.modified_surface == 3:
                congruence.checkFile(self.ms_file_surf_roughness)
                self.ms_roughness_rms_x = congruence.checkPositiveNumber(self.ms_roughness_rms_x, "Modified Surface: Roughness rms x")
                self.ms_roughness_rms_y = congruence.checkPositiveNumber(self.ms_roughness_rms_y, "Modified Surface: Roughness rms y")
            elif self.modified_surface == 4:
                if self.ms_specify_rz2==0: congruence.checkFile(self.ms_file_with_parameters_rz)
                if self.ms_specify_rz2==0: congruence.checkFile(self.ms_file_with_parameters_rz2)
            elif self.modified_surface == 5:
                congruence.checkFile(self.ms_file_orientations)
                congruence.checkFile(self.ms_file_polynomial)
                self.ms_number_of_segments_x = congruence.checkPositiveNumber(self.ms_number_of_segments_x, "Modified Surface: Number of segments x")
                self.ms_number_of_segments_y = congruence.checkPositiveNumber(self.ms_number_of_segments_y, "Modified Surface: Number of segments y")
                self.ms_length_of_segments_x = congruence.checkPositiveNumber(self.ms_length_of_segments_x, "Modified Surface: Length of segments x")
                self.ms_length_of_segments_y = congruence.checkPositiveNumber(self.ms_length_of_segments_y, "Modified Surface: Length of segments y")

            if self.source_movement == 1:
                if self.sm_distance_from_mirror < 0: raise Exception("Source Movement: Distance from O.E.")

    def writeCalculatedFields(self, shadow_oe):
        if self.surface_shape_parameters == 0:
            if self.graphical_options.is_spheric:
                self.spherical_radius = round(shadow_oe._oe.RMIRR, 4)
            elif self.graphical_options.is_toroidal:
                self.torus_major_radius = round(shadow_oe._oe.R_MAJ + shadow_oe._oe.R_MIN, 4)
                self.torus_minor_radius = round(shadow_oe._oe.R_MIN, 4)
            elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                self.ellipse_hyperbola_semi_major_axis = round(shadow_oe._oe.AXMAJ, 4)
                self.ellipse_hyperbola_semi_minor_axis = round(shadow_oe._oe.AXMIN, 4)
                self.angle_of_majax_and_pole = shadow_oe._oe.ELL_THE
            elif self.graphical_options.is_paraboloid:
                self.paraboloid_parameter = round(shadow_oe._oe.PARAM, 4)

        if self.diffraction_calculation == 0 and self.crystal_auto_setting == 1:
            self.incidence_angle_mrad = round((numpy.pi*0.5-shadow_oe._oe.T_INCIDENCE)*1000, 2)
            self.reflection_angle_mrad = round((numpy.pi*0.5-shadow_oe._oe.T_REFLECTION)*1000, 2)
            self.calculate_incidence_angle_deg()
            self.calculate_reflection_angle_deg()
        elif self.grating_auto_setting == 1:
            self.reflection_angle_mrad = round((numpy.pi*0.5-shadow_oe._oe.T_REFLECTION)*1000, 2)
            self.calculate_reflection_angle_deg()

        self.conic_coefficient_0 = shadow_oe._oe.CCC[0]
        self.conic_coefficient_1 = shadow_oe._oe.CCC[1]
        self.conic_coefficient_2 = shadow_oe._oe.CCC[2]
        self.conic_coefficient_3 = shadow_oe._oe.CCC[3]
        self.conic_coefficient_4 = shadow_oe._oe.CCC[4]
        self.conic_coefficient_5 = shadow_oe._oe.CCC[5]
        self.conic_coefficient_6 = shadow_oe._oe.CCC[6]
        self.conic_coefficient_7 = shadow_oe._oe.CCC[7]
        self.conic_coefficient_8 = shadow_oe._oe.CCC[8]
        self.conic_coefficient_9 = shadow_oe._oe.CCC[9]

    def completeOperations(self, shadow_oe=None):
        self.setStatusMessage("Running SHADOW")

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

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

        if self.graphical_options.is_ideal_lens:
            beam_out = ShadowBeam.traceIdealLensOE(self.input_beam,
                                                   shadow_oe,
                                                   widget_class_name=type(self).__name__)

            footprint_beam = None
        else:

            write_start_file, write_end_file = self.get_write_file_options()

            beam_out = ShadowBeam.traceFromOE(self.input_beam,
                                              shadow_oe,
                                              write_start_file=write_start_file,
                                              write_end_file=write_end_file,
                                              widget_class_name=type(self).__name__)

            if self.graphical_options.is_crystal and self.diffraction_calculation == 1:
                beam_out = self.apply_user_diffraction_profile(beam_out)
            elif self.graphical_options.is_mirror and self.reflectivity_type > 0 and self.source_of_reflectivity == 3:
                beam_out = self.apply_user_reflectivity(beam_out)
            elif self.graphical_options.is_grating and self.grating_use_efficiency == 1:
                beam_out = self.apply_user_grating_efficiency(beam_out)

            self.writeCalculatedFields(shadow_oe)

            footprint_beam = None

            if self.send_footprint_beam and self.isFootprintEnabled():
                footprint_beam = ShadowBeam()
                if beam_out._oe_number < 10:
                    footprint_beam.loadFromFile(file_name="mirr.0" + str(beam_out._oe_number))
                else:
                    footprint_beam.loadFromFile(file_name="mirr." + str(beam_out._oe_number))

                footprint_beam.setScanningData()

        if self.trace_shadow:
            grabber.stop()

            for row in grabber.ttyData:
               self.writeStdOut(row)

        self.setStatusMessage("Plotting Results")

        self.plot_results(beam_out, footprint_beam=footprint_beam)

        self.setStatusMessage("")

        self.send("Beam", beam_out)
        if self.send_footprint_beam and self.isFootprintEnabled(): self.send("Footprint", [beam_out, footprint_beam])
        self.send("Trigger", TriggerIn(new_object=True))

    def get_write_file_options(self):
        write_start_file = 0
        write_end_file = 0

        if self.file_to_write_out == 4:
            write_start_file = 1
            write_end_file = 1

        return write_start_file, write_end_file

    def apply_user_diffraction_profile(self, input_beam):
        return ShadowPreProcessor.apply_user_diffraction_profile(self.CRYSTALS[self.user_defined_crystal],
                                                                 self.user_defined_h,
                                                                 self.user_defined_k,
                                                                 self.user_defined_l,
                                                                 self.user_defined_asymmetry_angle,
                                                                 self.file_diffraction_profile,
                                                                 input_beam)

    def apply_user_reflectivity(self, input_beam):
        return ShadowPreProcessor.apply_user_reflectivity(self.user_defined_file_type,
                                                          self.user_defined_angle_units,
                                                          self.user_defined_energy_units,
                                                          self.file_reflectivity,
                                                          input_beam)

    def apply_user_grating_efficiency(self, input_beam):
        return ShadowPreProcessor.apply_user_grating_efficiency(self.grating_file_efficiency,
                                                                input_beam)

    def traceOpticalElement(self):
        try:
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    self.checkFields()

                    shadow_oe = self.instantiateShadowOE()

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
                                       str(exception), QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

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

    def setBeam(self, input_beam):
        self.not_interactive = self.check_not_interactive_conditions(input_beam)

        self.onReceivingInput()

        if ShadowCongruence.checkEmptyBeam(input_beam):
            self.input_beam = input_beam

            if self.is_automatic_run:
                self.traceOpticalElement()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.bragg_data_file != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_crystal:
                    self.file_crystal_parameters=data.bragg_data_file
                    self.diffraction_calculation = 0

                    self.set_DiffractionCalculation()
                else:
                    QtWidgets.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a crystal: bragg parameter will be ignored",
                              QtWidgets.QMessageBox.Ok)

            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_mirror:
                    self.file_prerefl=data.prerefl_data_file
                    self.reflectivity_type = 1
                    self.source_of_reflectivity = 0

                    self.set_Refl_Parameters()
                elif self.graphical_options.is_screen_slit:
                    self.absorption = 1
                    self.opt_const_file_name = data.prerefl_data_file

                    self.set_Absorption()
                else:
                    QtWidgets.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a mirror or screen/slit: prerefl parameter will be ignored",
                              QtWidgets.QMessageBox.Ok)

            if data.m_layer_data_file_dat != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_mirror:
                    self.file_prerefl_m=data.m_layer_data_file_dat

                    self.reflectivity_type = 1
                    self.source_of_reflectivity = 2

                    self.set_Refl_Parameters()
                else:
                    QtWidgets.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a mirror: prerefl_m parameter will be ignored",
                              QtWidgets.QMessageBox.Ok)

            if data.error_profile_data_file != ShadowPreProcessorData.NONE:
                if self.graphical_options.is_mirror or self.graphical_options.is_grating or self.graphical_options.is_crystal:
                    self.ms_defect_file_name = data.error_profile_data_file
                    self.modified_surface = 1
                    self.ms_type_of_defect = 2

                    self.set_ModifiedSurface()

                    if self.is_infinite == 1:
                        changed = False

                        if self.dim_x_plus > data.error_profile_x_dim/2 or \
                           self.dim_x_minus > data.error_profile_x_dim/2 or \
                           self.dim_y_plus > data.error_profile_y_dim/2 or \
                           self.dim_y_minus > data.error_profile_y_dim/2:
                            changed = True

                        if changed:
                            if QtWidgets.QMessageBox.information(self, "Confirm Modification",
                                                          "Dimensions of this O.E. must be changed in order to ensure congruence with the error profile surface, accept?",
                                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                                if self.dim_x_plus > data.error_profile_x_dim/2:
                                    self.dim_x_plus = data.error_profile_x_dim/2
                                if self.dim_x_minus > data.error_profile_x_dim/2:
                                    self.dim_x_minus = data.error_profile_x_dim/2
                                if self.dim_y_plus > data.error_profile_y_dim/2:
                                    self.dim_y_plus = data.error_profile_y_dim/2
                                if self.dim_y_minus > data.error_profile_y_dim/2:
                                    self.dim_y_minus = data.error_profile_y_dim/2

                                QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                                              "Dimensions of this O.E. were changed",
                                                              QtWidgets.QMessageBox.Ok)
                    else:
                        if QtWidgets.QMessageBox.information(self, "Confirm Modification",
                                                      "This O.E. must become rectangular with finite dimensions in order to ensure congruence with the error surface, accept?",
                                                      QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                            self.is_infinite = 1
                            self.mirror_shape = 0
                            self.dim_x_plus = data.error_profile_x_dim/2
                            self.dim_x_minus = data.error_profile_x_dim/2
                            self.dim_y_plus = data.error_profile_y_dim/2
                            self.dim_y_minus = data.error_profile_y_dim/2

                            QtWidgets.QMessageBox.warning(self, "Warning",
                                                          "Dimensions of this O.E. were changed",
                                                          QtWidgets.QMessageBox.Ok)

                    self.set_Dim_Parameters()
                else:
                    QtWidgets.QMessageBox.warning(self, "Warning",
                              "This O.E. is not a mirror, grating or crystal: surface error file will be ignored",
                              QtWidgets.QMessageBox.Ok)

    def acceptExchangeData(self, exchangeData):
        try:
            if not exchangeData is None:
                if exchangeData.get_program_name() == "XOPPY":
                    if exchangeData.get_widget_name() == "XCRYSTAL" or exchangeData.get_widget_name() == "XINPRO":
                        if exchangeData.get_widget_name() == "XCRYSTAL":
                            if exchangeData.get_content("scan_type") in (1, 2):
                                self.file_diffraction_profile = "xoppy_xcrystal_" + str(id(self)) + ".dat"
                                self.user_defined_bragg_angle = round(exchangeData.get_content("bragg_angle"), 4)
                                self.user_defined_asymmetry_angle  = round(exchangeData.get_content("asymmetry_angle"), 4)

                                self.set_UserDefinedBraggAngle()

                                x_index = 0
                                y_index_s = -1
                                y_index_p = -2
                            else:
                                raise Exception("Only Th-Thb Scan are accepted from CRYSTAL")

                        elif exchangeData.get_widget_name() == "XINPRO" :
                            self.file_diffraction_profile = "xoppy_xinpro_" + str(id(self)) + ".dat"

                            x_index = 0
                            y_index_s = 1
                            y_index_p = 2

                        diffraction_profile = exchangeData.get_content("xoppy_data")
                        conversion_factor = exchangeData.get_content("units_to_degrees")

                        file = open(self.file_diffraction_profile, "w")

                        for index in range(0, diffraction_profile.shape[0]):
                            file.write(str(conversion_factor*diffraction_profile[index, x_index]) + " " + str(diffraction_profile[index, y_index_s]) + " " + str(diffraction_profile[index, y_index_p]) + "\n")

                        file.close()

                        self.diffraction_calculation = 1
                        self.set_DiffractionCalculation()
                    elif exchangeData.get_widget_name() == "MULTILAYER":
                        self.file_reflectivity = "xoppy_mlayer_" + str(id(self)) + ".dat"

                        if exchangeData.has_content_key("data2D_rs"):
                            data2D_s = exchangeData.get_content("data2D_rs")
                            data2D_s[numpy.where(numpy.isnan(data2D_s))] = 0

                            data2D_p = exchangeData.get_content("data2D_rp")
                            data2D_p[numpy.where(numpy.isnan(data2D_p))] = 0

                            energy = exchangeData.get_content("dataX")
                            angle  = exchangeData.get_content("dataY")

                            file = open(self.file_reflectivity, "w")

                            for i in range(energy.shape[0]):
                                for j in range(angle.shape[0]):
                                    file.write(str(energy[i]) + " " + str(angle[j]) + " " + str(data2D_s[i, j]) + " " + str(data2D_p[i, j]) + "\n")

                            file.close()

                            self.user_defined_file_type = 2 # 2D
                        else:
                            x_index = exchangeData.get_content("plot_x_col")
                            y_index = exchangeData.get_content("plot_y_col")

                            reflectivity = exchangeData.get_content("xoppy_data")
                            reflectivity[numpy.where(numpy.isnan(reflectivity))] = 0

                            file = open(self.file_reflectivity, "w")

                            for index in range(0, reflectivity.shape[0]):
                                file.write(str(reflectivity[index, x_index]) + " " + str(reflectivity[index, y_index]) + "\n")

                            file.close()

                        self.reflectivity_type = 1 # full polarization
                        self.source_of_reflectivity = 3

                        self.set_Refl_Parameters()
                    elif exchangeData.get_widget_name() == "XF1F2":
                        self.file_reflectivity = "xoppy_f1f2_" + str(id(self)) + ".dat"

                        if exchangeData.has_content_key("data2D"):
                            data2D = exchangeData.get_content("data2D")
                            data2D[numpy.where(numpy.isnan(data2D))] = 0
                            energy = exchangeData.get_content("dataX")
                            angle = exchangeData.get_content("dataY")

                            file = open(self.file_reflectivity, "w")

                            for i in range(energy.shape[0]):
                                for j in range(angle.shape[0]):
                                    file.write(str(energy[i]) + " " + str(angle[j]) + " " + str(data2D[i, j]) + "\n")

                            file.close()

                            self.user_defined_file_type = 2 # 2D
                        else:
                            x_index = exchangeData.get_content("plot_x_col")
                            y_index = exchangeData.get_content("plot_y_col")

                            reflectivity = exchangeData.get_content("xoppy_data")
                            reflectivity[numpy.where(numpy.isnan(reflectivity))]

                            file = open(self.file_reflectivity, "w")

                            for index in range(0, reflectivity.shape[0]):
                                file.write(str(reflectivity[index, x_index]) + " " + str(reflectivity[index, y_index]) + "\n")

                            file.close()

                        self.reflectivity_type = 1  # full polarization
                        self.source_of_reflectivity = 3

                        self.set_Refl_Parameters()
                    else:
                        raise Exception("Xoppy data not recognized")

                elif exchangeData.get_program_name() == "XRAYSERVER":
                    if exchangeData.get_widget_name() == "X0H" or exchangeData.get_widget_name() == "GID_SL":
                        if exchangeData.get_widget_name() == "X0H" :
                            self.file_diffraction_profile     = "xrayserver_x0h_" + str(id(self)) + ".dat"
                            self.user_defined_bragg_angle     = 0.0
                            self.user_defined_asymmetry_angle = 0.0

                            diffraction_profile = exchangeData.get_content("x-ray_diffraction_profile_sigma")
                            conversion_factor = exchangeData.get_content("x-ray_diffraction_profile_sigma_units_to_degrees")
                        elif exchangeData.get_widget_name() == "GID_SL" :
                            self.file_diffraction_profile = "xrayserver_gid_sl_" + str(id(self)) + ".dat"

                            diffraction_profile = exchangeData.get_content("x-ray_diffraction_profile")
                            conversion_factor   = exchangeData.get_content("x-ray_diffraction_profile_units_to_degrees")

                        file = open(self.file_diffraction_profile, "w")

                        for index in range(0, len(diffraction_profile[0])):
                            file.write(str(conversion_factor*diffraction_profile[0][index]) + " " + str(diffraction_profile[1][index]) + "\n")

                        file.close()

                        self.diffraction_calculation = 1
                        self.set_DiffractionCalculation()
                    elif exchangeData.get_widget_name() == "TER_SL":
                        self.file_reflectivity = "xrayserver_ter_sl_" + str(id(self)) + ".dat"

                        reflectivity      = exchangeData.get_content("ter_sl_result")
                        conversion_factor = exchangeData.get_content("ter_sl_result_units_to_degrees")

                        file = open(self.file_reflectivity, "w")

                        for index in range(0, len(reflectivity[0])):
                            file.write(str(conversion_factor*reflectivity[0][index]) + " " + str(reflectivity[1][index]) + "\n")

                        file.close()

                        self.reflectivity_type = 1 # full polarization
                        self.source_of_reflectivity = 3

                        self.set_Refl_Parameters()
                    else:
                        raise Exception("X-Ray Server data not recognized")

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def deserialize(self, shadow_file):
        if self.graphical_options.is_screen_slit:
            raise Exception("Operation non supported for Screen/Slit Widget")
        elif self.graphical_options.is_ideal_lens:
            raise Exception("Operation non supported for Ideal Lens Widget")
        else:
            try:
                self.source_plane_distance = float(shadow_file.getProperty("T_SOURCE"))
                self.image_plane_distance = float(shadow_file.getProperty("T_IMAGE"))
                self.incidence_angle_deg = float(shadow_file.getProperty("T_INCIDENCE"))
                self.reflection_angle_deg = float(shadow_file.getProperty("T_REFLECTION"))
                if float(shadow_file.getProperty("ALPHA")) in [0.0,90.0,180.0,270.0]:
                    self.mirror_orientation_angle = int(float(shadow_file.getProperty("ALPHA"))/90)
                else:
                    self.mirror_orientation_angle = 4
                    self.mirror_orientation_angle_user_value = float(shadow_file.getProperty("ALPHA"))
                self.angles_respect_to = 0

                if self.graphical_options.is_curved:
                    if not (self.graphical_options.is_toroidal or self.graphical_options.is_conic_coefficients):
                        self.is_cylinder = int(shadow_file.getProperty("FCYL"))

                        if self.is_cylinder == 1:
                            self.cylinder_orientation = int(float(shadow_file.getProperty("CIL_ANG"))/90)

                    if self.graphical_options.is_conic_coefficients:
                        self.conic_coefficient_0 = float(shadow_file.getProperty("CCC(1)"))
                        self.conic_coefficient_1 = float(shadow_file.getProperty("CCC(2)"))
                        self.conic_coefficient_2 = float(shadow_file.getProperty("CCC(3)"))
                        self.conic_coefficient_3 = float(shadow_file.getProperty("CCC(4)"))
                        self.conic_coefficient_4 = float(shadow_file.getProperty("CCC(5)"))
                        self.conic_coefficient_5 = float(shadow_file.getProperty("CCC(6)"))
                        self.conic_coefficient_6 = float(shadow_file.getProperty("CCC(7)"))
                        self.conic_coefficient_7 = float(shadow_file.getProperty("CCC(8)"))
                        self.conic_coefficient_8 = float(shadow_file.getProperty("CCC(9)"))
                        self.conic_coefficient_9 = float(shadow_file.getProperty("CCC(10)"))
                    else:
                        self.surface_shape_parameters = int(shadow_file.getProperty("F_EXT"))

                        if self.surface_shape_parameters == 0:

                            if int(shadow_file.getProperty("F_DEFAULT")) == 1:
                                self.focii_and_continuation_plane = 0
                            elif int(shadow_file.getProperty("F_DEFAULT")) == 0:
                                self.focii_and_continuation_plane = 1

                            if self.focii_and_continuation_plane == 1:
                                self.object_side_focal_distance =  float(shadow_file.getProperty("SSOUR"))
                                self.image_side_focal_distance = float(shadow_file.getProperty("SIMAG"))
                                self.incidence_angle_respect_to_normal = float(shadow_file.getProperty("THETA"))

                            if self.graphical_options.is_paraboloid: self.focus_location = float(shadow_file.getProperty("F_SIDE"))
                        else:
                           if self.graphical_options.is_spheric:
                               self.spherical_radius = float(shadow_file.getProperty("RMIRR"))
                           elif self.graphical_options.is_toroidal:
                               self.torus_major_radius = float(shadow_file.getProperty("R_MAJ"))
                               self.torus_minor_radius = float(shadow_file.getProperty("R_MIN"))
                           elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                               self.ellipse_hyperbola_semi_major_axis = float(shadow_file.getProperty("AXMAJ"))
                               self.ellipse_hyperbola_semi_minor_axis = float(shadow_file.getProperty("AXMIN"))
                               self.angle_of_majax_and_pole = float(shadow_file.getProperty("ELL_THE"))
                           elif self.graphical_options.is_paraboloid:
                               self.paraboloid_parameter = float(shadow_file.getProperty("PARAM"))

                    if self.graphical_options.is_toroidal: self.toroidal_mirror_pole_location = int(shadow_file.getProperty("F_TORUS"))

                    self.surface_curvature == int(shadow_file.getProperty("F_CONVEX"))

                if self.graphical_options.is_mirror:
                    self.reflectivity_type = int(shadow_file.getProperty("F_REFLEC"))

                    if self.reflectivity_type > 0:
                        self.source_of_reflectivity = int(shadow_file.getProperty("F_REFL"))

                        if self.source_of_reflectivity == 0:
                            self.file_prerefl = shadow_file.getProperty("FILE_REFL")
                        elif self.source_of_reflectivity == 1:
                            self.alpha = float(shadow_file.getProperty("ALFA"))
                            self.gamma = float(shadow_file.getProperty("GAMMA"))
                        elif self.source_of_reflectivity == 2:
                            self.file_prerefl_m = shadow_file.getProperty("FILE_REFL")
                            self.m_layer_tickness = float(shadow_file.getProperty("F_THICK"))
                elif self.graphical_options.is_crystal:
                    self.diffraction_calculation = 0
                    self.diffraction_geometry = int(shadow_file.getProperty("F_REFRAC"))
                    self.file_crystal_parameters = shadow_file.getProperty("FILE_REFL")

                    self.crystal_auto_setting = int(shadow_file.getProperty("F_CENTRAL"))
                    self.mosaic_crystal = int(shadow_file.getProperty("F_MOSAIC"))
                    self.asymmetric_cut = int(shadow_file.getProperty("F_BRAGG_A"))
                    self.johansson_geometry = int(shadow_file.getProperty("F_JOHANSSON"))

                    if self.crystal_auto_setting == 1:
                        self.units_in_use = int(shadow_file.getProperty("F_PHOT_CENT"))
                        self.photon_energy = float(shadow_file.getProperty("PHOT_CENT"))
                        self.photon_wavelength = float(shadow_file.getProperty("R_LAMBDA"))

                    if self.mosaic_crystal==1:
                        self.seed_for_mosaic = int(shadow_file.getProperty("MOSAIC_SEED"))
                        self.angle_spread_FWHM = float(shadow_file.getProperty("SPREAD_MOS"))
                        self.thickness = float(shadow_file.getProperty("THICKNESS"))
                    else:
                        if self.asymmetric_cut == 1:
                            self.planes_angle = float(shadow_file.getProperty("A_BRAGG"))
                            self.below_onto_bragg_planes = float(shadow_file.getProperty("ORDER"))
                            self.thickness = float(shadow_file.getProperty("THICKNESS"))
                        if self.johansson_geometry == 1:
                            self.johansson_radius = float(shadow_file.getProperty("R_JOHANSSON"))
                elif self.graphical_options.is_grating:
                    f_ruling = int(shadow_file.getProperty("F_RULING"))

                    if f_ruling == 4:
                        raise Exception("Grating with ruling type not supported: F_RULING=4")
                    else:
                        if f_ruling == 5:
                            self.grating_ruling_type = 4
                        else:
                            self.grating_ruling_type = f_ruling

                    if self.grating_ruling_type == 0 or self.grating_ruling_type == 1:
                        self.grating_ruling_density = float(shadow_file.getProperty("RULING"))
                    elif self.grating_ruling_type == 2:
                        self.grating_holo_left_distance         = float(shadow_file.getProperty("HOLO_R1"))
                        self.grating_holo_right_distance        = float(shadow_file.getProperty("HOLO_R2"))
                        self.grating_holo_left_incidence_angle  = float(shadow_file.getProperty("HOLO_DEL"))
                        self.grating_holo_right_incidence_angle = float(shadow_file.getProperty("HOLO_GAM"))
                        self.grating_holo_recording_wavelength  = float(shadow_file.getProperty("HOLO_W"))
                        self.grating_holo_left_azimuth_from_y   = float(shadow_file.getProperty("HOLO_RT1"))
                        self.grating_holo_right_azimuth_from_y  = float(shadow_file.getProperty("HOLO_RT2"))
                        self.grating_holo_pattern_type = int(shadow_file.getProperty("F_PW"))
                        self.grating_holo_cylindrical_source = int(shadow_file.getProperty("F_PW_C"))
                        self.grating_holo_source_type = int(shadow_file.getProperty("F_VIRTUAL"))
                    elif self.grating_ruling_type == 3:
                        self.grating_groove_pole_azimuth_from_y = float(shadow_file.getProperty("AZIM_FAN"))
                        self.grating_groove_pole_distance = float(shadow_file.getProperty("DIST_FAN"))
                        self.grating_coma_correction_factor = float(shadow_file.getProperty("COMA_FAC"))
                    elif self.grating_ruling_type == 4:
                        self.grating_ruling_density = float(shadow_file.getProperty("RULING"))
                        self.grating_poly_coeff_1   = float(shadow_file.getProperty("RUL_A1"))
                        self.grating_poly_coeff_2   = float(shadow_file.getProperty("RUL_A2"))
                        self.grating_poly_coeff_3   = float(shadow_file.getProperty("RUL_A3"))
                        self.grating_poly_coeff_4   = float(shadow_file.getProperty("RUL_A4"))
                        self.grating_poly_signed_absolute = int(shadow_file.getProperty("F_RUL_ABS"))

                    self.grating_auto_setting = int(shadow_file.getProperty("F_CENTRAL"))

                    if self.grating_auto_setting == 1:
                        self.grating_mount_type = int(shadow_file.getProperty("F_MONO"))
                        self.grating_units_in_use = int(shadow_file.getProperty("F_PHOT_CENT"))
                        self.grating_photon_energy = float(shadow_file.getProperty("PHOT_CENT"))
                        self.grating_photon_wavelength = float(shadow_file.getProperty("R_LAMBDA"))

                        if self.grating_mount_type == 4:
                            self.grating_hunter_grating_selected = int(shadow_file.getProperty("F_HUNT"))-1
                            self.grating_hunter_distance_between_beams = float(shadow_file.getProperty("HUNT_H"))
                            self.grating_hunter_monochromator_length   = float(shadow_file.getProperty("HUNT_L"))
                            self.grating_hunter_blaze_angle            = float(shadow_file.getProperty("BLAZE"))

                self.is_infinite = int(shadow_file.getProperty("FHIT_C"))

                if self.is_infinite == 1:
                    self.mirror_shape = int(shadow_file.getProperty("FSHAPE")) - 1
                    self.dim_y_plus  = float(shadow_file.getProperty("RLEN1"))
                    self.dim_y_minus = float(shadow_file.getProperty("RLEN2"))
                    self.dim_x_plus  = float(shadow_file.getProperty("RWIDX1"))
                    self.dim_x_minus = float(shadow_file.getProperty("RWIDX2"))

                #####################################
                # ADVANCED SETTING
                #####################################

                self.modified_surface = 0

                if int(shadow_file.getProperty("F_RIPPLE")) == 1: self.modified_surface = 1
                elif int(shadow_file.getProperty("F_FACET")) == 1: self.modified_surface = 2
                elif int(shadow_file.getProperty("F_ROUGHNESS")) == 1: self.modified_surface = 3
                elif int(shadow_file.getProperty("F_KOMA")) == 1: self.modified_surface = 4
                elif int(shadow_file.getProperty("F_SEGMENT")) == 1: self.modified_surface = 5

                if self.modified_surface == 1:
                     self.ms_type_of_defect = int(shadow_file.getProperty("F_G_S"))

                     if self.ms_type_of_defect == 0:
                         self.ms_ripple_ampli_x = float(shadow_file.getProperty("X_RIP_AMP"))
                         self.ms_ripple_wavel_x = float(shadow_file.getProperty("X_RIP_WAV"))
                         self.ms_ripple_phase_x = float(shadow_file.getProperty("X_PHASE"))
                         self.ms_ripple_ampli_y = float(shadow_file.getProperty("Y_RIP_AMP"))
                         self.ms_ripple_wavel_y = float(shadow_file.getProperty("Y_RIP_WAV"))
                         self.ms_ripple_phase_y = float(shadow_file.getProperty("Y_PHASE"))
                     else:
                         self.ms_defect_file_name = shadow_file.getProperty("FILE_RIP")
                elif self.modified_surface == 2:
                     self.ms_file_facet_descr = shadow_file.getProperty("FILE_FAC")
                     self.ms_lattice_type = int(shadow_file.getProperty("F_FAC_LATT"))
                     self.ms_orientation = int(shadow_file.getProperty("F_FAC_ORIENT"))
                     self.ms_lattice_type = int(shadow_file.getProperty("F_POLSEL"))-1
                     self.ms_facet_width_x = float(shadow_file.getProperty("RFAC_LENX"))
                     self.ms_facet_phase_x = float(shadow_file.getProperty("RFAC_PHAX"))
                     self.ms_dead_width_x_minus = float(shadow_file.getProperty("RFAC_DELX1"))
                     self.ms_dead_width_x_plus = float(shadow_file.getProperty("RFAC_DELX2"))
                     self.ms_facet_width_y = float(shadow_file.getProperty("RFAC_LENY"))
                     self.ms_facet_phase_y = float(shadow_file.getProperty("RFAC_PHAY"))
                     self.ms_dead_width_y_minus = float(shadow_file.getProperty("RFAC_DELY1"))
                     self.ms_dead_width_y_plus = float(shadow_file.getProperty("RFAC_DELY2"))
                elif self.modified_surface == 3:
                    self.ms_file_surf_roughness = shadow_file.getProperty("FILE_ROUGH")
                    self.ms_roughness_rms_x = float(shadow_file.getProperty("ROUGH_X"))
                    self.ms_roughness_rms_y = float(shadow_file.getProperty("ROUGH_Y"))
                elif self.modified_surface == 4:
                    self.ms_specify_rz2 = int(shadow_file.getProperty("F_KOMA_CA"))
                    self.ms_file_with_parameters_rz = shadow_file.getProperty("FILE_KOMA")
                    self.ms_file_with_parameters_rz2 = shadow_file.getProperty("FILE_KOMA_CA")
                    self.ms_save_intercept_bounces = int(shadow_file.getProperty("F_KOMA_BOUNCE"))
                elif self.modified_surface == 5:
                    self.ms_number_of_segments_x = int(shadow_file.getProperty("ISEG_XNUM"))
                    self.ms_number_of_segments_y = int(shadow_file.getProperty("ISEG_YNUM"))
                    self.ms_length_of_segments_x = float(shadow_file.getProperty("SEG_LENX"))
                    self.ms_length_of_segments_y = float(shadow_file.getProperty("SEG_LENY"))
                    self.ms_file_orientations = shadow_file.getProperty("FILE_SEGMENT")
                    self.ms_file_polynomial = shadow_file.getProperty("FILE_SEGP")

                self.mirror_movement = int(shadow_file.getProperty("F_MOVE"))

                if self.mirror_movement == 1:
                     self.mm_mirror_offset_x = float(shadow_file.getProperty("OFFX"))
                     self.mm_mirror_offset_y = float(shadow_file.getProperty("OFFY"))
                     self.mm_mirror_offset_z = float(shadow_file.getProperty("OFFZ"))
                     self.mm_mirror_rotation_x = float(shadow_file.getProperty("X_ROT"))
                     self.mm_mirror_rotation_y = float(shadow_file.getProperty("Y_ROT"))
                     self.mm_mirror_rotation_z = float(shadow_file.getProperty("Z_ROT"))

                self.source_movement = int(shadow_file.getProperty("FSTAT"))

                if self.source_movement == 1:
                     self.sm_angle_of_incidence = float(shadow_file.getProperty("RTHETA"))
                     self.sm_distance_from_mirror = float(shadow_file.getProperty("RDSOUR"))
                     self.sm_z_rotation = float(shadow_file.getProperty("ALPHA_S"))
                     self.sm_offset_x_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUX"))
                     self.sm_offset_y_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUY"))
                     self.sm_offset_z_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUZ"))
                     self.sm_offset_x_source_ref_frame = float(shadow_file.getProperty("X_SOUR"))
                     self.sm_offset_y_source_ref_frame = float(shadow_file.getProperty("Y_SOUR"))
                     self.sm_offset_z_source_ref_frame = float(shadow_file.getProperty("Z_SOUR"))
                     self.sm_rotation_around_x = float(shadow_file.getProperty("X_SOUR_ROT"))
                     self.sm_rotation_around_y = float(shadow_file.getProperty("Y_SOUR_ROT"))
                     self.sm_rotation_around_z = float(shadow_file.getProperty("Z_SOUR_ROT"))

                self.file_to_write_out = int(shadow_file.getProperty("FWRITE"))
                self.write_out_inc_ref_angles = int(shadow_file.getProperty("F_ANGLE"))
            except Exception as exception:
                raise BlockingIOError("O.E. failed to load, bad file format: " + exception.args[0])
                
            self.setupUI()

    def copy_oe_parameters(self):
        global shadow_oe_to_copy

        shadow_oe_to_copy = self.instantiateShadowOE()

        self.populateFields(shadow_oe_to_copy)

    def paste_oe_parameters(self):
        global shadow_oe_to_copy

        if not shadow_oe_to_copy is None:
            if QtWidgets.QMessageBox.information(self, "Confirm Operation",
                                          "Confirm Paste Operation?",
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                try:
                    if self.graphical_options.is_ideal_lens:
                        self.source_plane_distance = shadow_oe_to_copy._oe.T_SOURCE
                        self.image_plane_distance = shadow_oe_to_copy._oe.T_IMAGE

                        try:
                            self.focal_x = shadow_oe_to_copy._oe.focal_x
                            self.focal_z = shadow_oe_to_copy._oe.focal_z
                        except:
                            pass
                    else:
                        shadow_temp_file = congruence.checkFileName("tmp_oe_buffer.dat")
                        shadow_oe_to_copy._oe.write(shadow_temp_file)

                        shadow_file, type = ShadowFile.readShadowFile(shadow_temp_file)

                        self.deserialize(shadow_file)

                        os.remove(shadow_temp_file)
                except Exception as exception:
                    QtWidgets.QMessageBox.critical(self, "Error", str(exception),  QtWidgets.QMessageBox.Ok)

    def setupUI(self):
        if self.graphical_options.is_screen_slit or self.graphical_options.is_empty:
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            if self.graphical_options.is_screen_slit:
                self.set_Aperturing()
                self.set_Absorption()

            self.set_SourceMovement()
        elif self.graphical_options.is_ideal_lens:
            pass
        else:
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            if self.graphical_options.is_curved:
                if not self.graphical_options.is_conic_coefficients:
                    self.set_IntExt_Parameters()
                    if not self.graphical_options.is_toroidal:
                        self.set_isCyl_Parameters()

            if self.graphical_options.is_mirror:
                self.set_Refl_Parameters()
            elif self.graphical_options.is_crystal:
                self.set_Mosaic()
                self.set_BraggLaue()
                self.set_DiffractionCalculation()
            elif self.graphical_options.is_grating:
                self.set_GratingAutosetting()
                self.set_GratingRulingType()
            elif self.graphical_options.is_refractor:
                self.set_RefrectorOpticalConstants()

            self.set_Dim_Parameters()
            self.set_ModifiedSurface()
            self.set_MirrorMovement()
            self.set_SourceMovement()
            self.set_Footprint()

    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                beamline_element = data.get_beamline_element_at(-1)

                optical_element = beamline_element.get_optical_element()
                coordinates = beamline_element.get_coordinates()

                if not optical_element is None:
                    if self.graphical_options.is_screen_slit: # SCREEN-SLIT
                        if isinstance(optical_element, beam_stopper.BeamStopper) or \
                           isinstance(optical_element, slit.Slit):
                            self.absorption = 0
                            self.aperturing = 1
                            self.open_slit_solid_stop = 0 if isinstance(optical_element, slit.Slit) else 1

                            if isinstance(optical_element._boundary_shape, Rectangle):
                                self.aperture_shape = 0

                            elif isinstance(optical_element._boundary_shape, Ellipse):
                                self.aperture_shape = 1

                            left, right, bottom, top = optical_element._boundary_shape.get_boundaries()

                            self.slit_width_xaxis = round((numpy.abs(right - left))/ self.workspace_units_to_m, 4)
                            self.slit_height_zaxis = round((numpy.abs(top - bottom))/ self.workspace_units_to_m, 4)
                            self.slit_center_xaxis = round(((right + left) / 2)/ self.workspace_units_to_m, 4)
                            self.slit_center_zaxis = round(((top + bottom) / 2)/ self.workspace_units_to_m, 4)

                        elif isinstance(optical_element, filter.Filter):
                            self.absorption = 1
                            self.aperturing = 0

                            self.thickness = optical_element._thickness / self.workspace_units_to_m
                            self.opt_const_file_name = "<File for " + optical_element._material + ">"
                        elif isinstance(optical_element, screen.Screen):
                            self.absorption = 0
                            self.aperturing = 0
                        else:
                            raise ValueError("Syned optical element not congruent")

                        self.source_plane_distance = round(coordinates.p() / self.workspace_units_to_m, 4)
                        self.image_plane_distance = round(coordinates.q() / self.workspace_units_to_m, 4)

                        self.set_Aperturing()
                        self.set_Absorption()
                    elif self.graphical_options.is_ideal_lens: # IDEAL LENS
                        self.source_plane_distance = round(coordinates.p() / self.workspace_units_to_m, 4)
                        self.image_plane_distance = round(coordinates.q() / self.workspace_units_to_m, 4)
                        self.focal_x = round(optical_element._focal_x / self.workspace_units_to_m, 4)
                        self.focal_z = round(optical_element._focal_y / self.workspace_units_to_m, 4)
                    else:
                        if self.graphical_options.is_mirror:
                            if not isinstance(optical_element, mirror.Mirror):
                                raise ValueError("Syned optical element not congruent: not a Mirror")
                        elif self.graphical_options.is_crystal:
                            if not isinstance(optical_element, crystal.Crystal):
                                raise ValueError("Syned optical element not congruent: not a Crystal")
                        elif self.graphical_options.is_grating:
                            if not isinstance(optical_element, grating.Grating):
                                raise ValueError("Syned optical element not congruent: not a Grating")

                        self.source_plane_distance = round(coordinates.p() / self.workspace_units_to_m, 4)
                        self.image_plane_distance = round(coordinates.q() / self.workspace_units_to_m, 4)
                        self.incidence_angle_mrad = round((0.5*numpy.pi - coordinates.angle_radial())*1e3, 2)

                        if self.graphical_options.is_mirror:
                            self.reflection_angle_mrad = round((0.5*numpy.pi - coordinates.angle_radial())*1e3, 2)
                        if self.graphical_options.is_crystal and self.crystal_auto_setting == 0:
                            self.reflection_angle_mrad = round((0.5*numpy.pi - coordinates.angle_radial())*1e3, 2)

                        self.calculate_incidence_angle_deg()
                        self.calculate_reflection_angle_deg()

                        if numpy.degrees(coordinates.angle_azimuthal()) in [0.90,180,270]:
                            self.mirror_orientation_angle = int(numpy.degrees(coordinates.angle_azimuthal())/90)
                        else:
                            self.mirror_orientation_angle = 4
                            self.mirror_orientation_angle_user_value = numpy.degrees(coordinates.angle_azimuthal())

                        if optical_element._boundary_shape is None:
                            self.is_infinite = 0
                        else:
                            self.is_infinite = 1

                            left, right, bottom, top = optical_element._boundary_shape.get_boundaries()

                            self.dim_x_plus = round(numpy.abs(right / self.workspace_units_to_m), 4)
                            self.dim_x_minus = round(numpy.abs(left / self.workspace_units_to_m), 4)
                            self.dim_y_plus = round(numpy.abs(top / self.workspace_units_to_m), 4)
                            self.dim_y_minus = round(numpy.abs(bottom / self.workspace_units_to_m), 4)

                            if isinstance(optical_element._boundary_shape, Rectangle):
                                self.mirror_shape = 0
                            elif isinstance(optical_element._boundary_shape, Ellipse):
                                self.mirror_shape = 1

                        if isinstance(optical_element._surface_shape, Plane):
                            if self.graphical_options.is_curved:
                                raise ValueError("Syned optical element surface shape not congruent")

                        elif isinstance(optical_element._surface_shape, Ellipsoid):
                            if self.graphical_options.is_ellipsoidal:
                                self.surface_shape_parameters = 1
                                self.ellipse_hyperbola_semi_major_axis = round(optical_element._surface_shape._maj_axis/(2*self.workspace_units_to_m), 4)
                                self.ellipse_hyperbola_semi_minor_axis = round(optical_element._surface_shape._min_axis/(2*self.workspace_units_to_m), 4)

                                self.set_angle_of_majax_and_pole(coordinates, optical_element)

                                self.surface_curvature = optical_element._surface_shape._convexity

                                if isinstance(optical_element._surface_shape, EllipticalCylinder):
                                    self.is_cylinder = 1
                                    self.cylinder_orientation = optical_element._surface_shape._cylinder_direction
                                    self.set_isCyl_Parameters()
                                else:
                                    self.is_cylinder = 0
                            else:
                                raise ValueError("Syned optical element surface shape not congruent")
                        elif isinstance(optical_element._surface_shape, Hyperboloid):
                            if self.graphical_options.is_hyperboloid:
                                self.surface_shape_parameters = 1

                                self.ellipse_hyperbola_semi_major_axis = round(optical_element._surface_shape._maj_axis/(2*self.workspace_units_to_m), 4)
                                self.ellipse_hyperbola_semi_minor_axis = round(optical_element._surface_shape._min_axis/(2*self.workspace_units_to_m), 4)

                                self.angle_of_majax_and_pole = -1 # TODO: not yet calculated in syned

                                self.surface_curvature = optical_element._surface_shape._convexity

                                if isinstance(optical_element._surface_shape, HyperbolicCylinder):
                                    self.is_cylinder = 1
                                    self.cylinder_orientation = optical_element._surface_shape._cylinder_direction
                                    self.set_isCyl_Parameters()
                                else:
                                    self.is_cylinder = 0
                            else:
                                raise ValueError("Syned optical element surface shape not congruent")
                        elif isinstance(optical_element._surface_shape, Sphere):
                            if self.graphical_options.is_spheric:
                                self.surface_shape_parameters = 1

                                self.spherical_radius = round(optical_element._surface_shape.get_radius()/self.workspace_units_to_m, 4)

                                self.surface_curvature = optical_element._surface_shape._convexity

                                if isinstance(optical_element._surface_shape, SphericalCylinder):
                                    self.is_cylinder = 1
                                    self.cylinder_orientation = optical_element._surface_shape._cylinder_direction
                                    self.set_isCyl_Parameters()
                                else:
                                    self.is_cylinder = 0
                            else:
                                raise ValueError("Syned optical element surface shape not congruent")
                        elif isinstance(optical_element._surface_shape, Paraboloid):
                            if self.graphical_options.is_paraboloid:
                                self.surface_shape_parameters = 1

                                self.paraboloid_parameter = round(optical_element._surface_shape._parabola_parameter/self.workspace_units_to_m, 4)

                                self.surface_curvature = optical_element._surface_shape._convexity

                                if isinstance(optical_element._surface_shape, ParabolicCylinder):
                                    self.is_cylinder = 1
                                    self.cylinder_orientation = optical_element._surface_shape._cylinder_direction
                                    self.set_isCyl_Parameters()
                                else:
                                    self.is_cylinder = 0
                            else:
                                raise ValueError("Syned optical element surface shape not congruent")
                        elif isinstance(optical_element._surface_shape, Toroidal):
                            if self.graphical_options.is_toroidal:
                                self.surface_shape_parameters = 1

                                self.torus_major_radius = round(optical_element._surface_shape._maj_radius/self.workspace_units_to_m, 4)
                                self.torus_minor_radius = round(optical_element._surface_shape._min_radius/self.workspace_units_to_m, 4)

                                self.surface_curvature = optical_element._surface_shape._convexity
                            else:
                                raise ValueError("Syned optical element surface shape not congruent")
                        elif isinstance(optical_element._surface_shape, Conic):
                            if self.graphical_options.is_conic_coefficients:
                                self.surface_shape_parameters = 1
                                self.conic_coefficient_0 = optical_element._surface_shape._conic_coefficients[0]/self.workspace_units_to_m
                                self.conic_coefficient_1 = optical_element._surface_shape._conic_coefficients[1]/self.workspace_units_to_m
                                self.conic_coefficient_2 = optical_element._surface_shape._conic_coefficients[2]/self.workspace_units_to_m
                                self.conic_coefficient_3 = optical_element._surface_shape._conic_coefficients[3]/self.workspace_units_to_m
                                self.conic_coefficient_4 = optical_element._surface_shape._conic_coefficients[4]/self.workspace_units_to_m
                                self.conic_coefficient_5 = optical_element._surface_shape._conic_coefficients[5]/self.workspace_units_to_m
                                self.conic_coefficient_6 = optical_element._surface_shape._conic_coefficients[6]/self.workspace_units_to_m
                                self.conic_coefficient_7 = optical_element._surface_shape._conic_coefficients[7]/self.workspace_units_to_m
                                self.conic_coefficient_8 = optical_element._surface_shape._conic_coefficients[8]/self.workspace_units_to_m
                                self.conic_coefficient_9 = optical_element._surface_shape._conic_coefficients[9]/self.workspace_units_to_m
                            else:
                                raise ValueError("Syned optical element surface shape not congruent")

                        self.set_Dim_Parameters()
                        if self.graphical_options.is_curved: self.set_IntExt_Parameters()


                        if self.graphical_options.is_mirror:
                            self.reflectivity_type = 1
                            self.source_of_reflectivity = 0
                            if self.file_prerefl == "reflec.dat":
                                self.file_prerefl = "<File for " + optical_element._coating + ">.dat"

                            self.set_Refl_Parameters()
                        elif self.graphical_options.is_crystal:
                            self.diffraction_geometry = optical_element._diffraction_geometry
                            if self.diffraction_calculation == 0:
                                if self.file_crystal_parameters == "bragg.dat":
                                    self.file_crystal_parameters = "<File for " + optical_element._material + ">.dat"
                            elif self.diffraction_calculation == 1:
                                if self.file_diffraction_profile == "diffraction_profile.dat":
                                    self.file_diffraction_profile = "<File for " + optical_element._material + ">.dat"

                            if optical_element._asymmetry_angle != 0.0:
                                self.asymmetric_cut = 1
                                self.planes_angle = round(numpy.degrees(optical_element._asymmetry_angle), 6)
                            else:
                                self.asymmetric_cut = 0
                                self.planes_angle = 0.0

                            self.thickness = round(optical_element._thickness/self.workspace_units_to_m, 6)

                            self.set_BraggLaue()
                            self.set_AsymmetricCut()

                        elif self.graphical_options.is_grating:
                            self.grating_ruling_type = 0
                            self.grating_ruling_density = optical_element._ruling*self.workspace_units_to_m
                else:
                    raise ValueError("Syned data not correct: optical element not present")
            else:
                raise ValueError("Syned data not correct")

    def set_angle_of_majax_and_pole(self, coordinates, optical_element):
        grazing_angle = 0.5 * numpy.pi - coordinates.angle_radial()
        p, q = optical_element._surface_shape.get_p_q(grazing_angle)
        zp, xp = OpticalElement.get_shadow_pole_coordinates_from_p_q(p, q, grazing_angle)

        self.angle_of_majax_and_pole = round(OpticalElement.get_shadow_angle_of_majax_and_pole(xp, zp), 4)

    def mirror_orientation_angle_user(self):

        if self.mirror_orientation_angle < 4:
            self.mirror_orientation_angle_user_value_le.setVisible(False)
        else:
            self.mirror_orientation_angle_user_value_le.setVisible(True)

    @classmethod
    def get_shadow_pole_coordinates_from_p_q(cls, p=2.0, q=1.0, grazing_angle=0.003):
        min_ax, maj_ax = Ellipsoid.get_axis_from_p_q(p, q, grazing_angle)
        c = 0.5*numpy.sqrt(p**2 + q**2 - 2*p*q*numpy.cos(numpy.pi - 2*grazing_angle))

        a = maj_ax/2
        b = min_ax/2
        eccentricity = c/a

        # see calculation of ellipse center in shadow_kernel.f90 row 3621
        xp = 0.5*(p-q)/eccentricity
        yp = -numpy.sqrt(1-(xp**2)/(a**2))*b

        return xp, yp

    @classmethod
    def get_shadow_angle_of_majax_and_pole(cls, xp, zp):
        return numpy.degrees(abs(numpy.arctan(zp/xp)))

if __name__=="__main__":

    widget = OpticalElement()

    print(widget.alpha)

    print(getattr(widget, "alpha"))

    setattr(widget, "alpha", 90)
