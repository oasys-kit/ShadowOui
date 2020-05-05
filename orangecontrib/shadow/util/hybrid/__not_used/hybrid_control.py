import copy
import numpy
from matplotlib import pyplot as plt

from PyQt5.QtWidgets import QMessageBox

from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowPhysics, ShadowPreProcessor

from srxraylib.util.data_structures import ScaledArray, ScaledMatrix
from srxraylib.waveoptics.wavefront import Wavefront1D
from srxraylib.waveoptics.wavefront2D import Wavefront2D
from srxraylib.waveoptics import propagator
from srxraylib.waveoptics import propagator2D
from srxraylib.util.inverse_method_sampler import Sampler2D, Sampler1D

import oasys.util.oasys_util as OU
from scipy.interpolate import RectBivariateSpline

import xraylib
from Shadow import ShadowTools as ST

class HybridNotNecessaryWarning(Exception):
    def __init__(self, *args, **kwargs):
        pass

class HybridInputParameters(object):
    widget=None

    shadow_beam = None
    original_shadow_beam = None

    ghy_n_oe = -1 # not needed, oe number form beam
    ghy_n_screen = -1 # not needed, but kept for compatibility with old

    ghy_diff_plane = 2
    ghy_calcType = 1

    ghy_focallength = -1
    ghy_distance = -1

    ghy_mirrorfile = "mirror.dat"

    ghy_nf = 1

    ghy_nbins_x = 200
    ghy_nbins_z = 200
    ghy_npeak = 20
    ghy_fftnpts = 1e6
    ghy_lengthunit = 1

    file_to_write_out = 0

    ghy_automatic = 1

    absorber_error_profiles = None
    absorber_material = None
    absorber_delta = None
    absorber_scaling_factor = 1.0

    def __init__(self):
        super().__init__()

    def dump(self):
        return self.__dict__

class HybridCalculationParameters(object):
    beam_not_cut_in_z = False
    beam_not_cut_in_x = False

    shadow_oe_end = None

    original_beam_history = None

    image_plane_beam = None
    image_plane_beam_lost = None
    ff_beam = None
    nf_beam = None

    screen_plane_beam = None

    # Screen
    wenergy     = None
    wwavelength = None
    xp_screen   = None
    yp_screen   = None
    zp_screen   = None
    ref_screen  = None
    xx_screen = None
    ghy_x_min = 0.0
    ghy_x_max = 0.0
    zz_screen = None
    ghy_z_min = 0.0
    ghy_z_max = 0.0
    dx_ray = None
    dz_ray = None
    gwavelength = 0.0
    gknum = 0.0

    # Mirror
    xx_mirr = None
    zz_mirr = None
    angle_inc = None
    angle_ref = None

    # Mirror Surface
    w_mirr_1D_values = None
    w_mirr_2D_values = None

    # Mirror Fitted Functions
    wangle_x = None
    wangle_z = None
    wangle_ref_x = None
    wangle_ref_z = None
    wl_x     = None
    wl_z     = None

    xx_focal_ray = None
    zz_focal_ray = None

    w_mirror_lx = None
    w_mirror_lz = None
    w_mirror_l = None

    wIray_x = None
    wIray_z = None
    wIray_2d = None

    do_ff_x = True
    do_ff_z = True

    # Propagation output
    dif_xp = None
    dif_zp = None
    dif_x = None
    dif_z = None
    dif_xpzp = None
    dif_xz = None

    # Conversion Output
    dx_conv = None
    dz_conv = None
    xx_image_ff = None
    zz_image_ff = None
    xx_image_nf = None
    zz_image_nf = None

    absorber_delta = None

##########################################################################

def hy_run(input_parameters=HybridInputParameters()):
    calculation_parameters=HybridCalculationParameters()

    try:
        input_parameters.original_shadow_beam = input_parameters.shadow_beam.duplicate(history=True)

        hy_check_congruence(input_parameters, calculation_parameters)

        input_parameters.widget.status_message("Starting HYBRID calculation")
        input_parameters.widget.set_progress_bar(0)

        hy_readfiles(input_parameters, calculation_parameters)	#Read shadow output files needed by HYBRID

        input_parameters.widget.status_message("Analysis of Input Beam and OE completed")
        input_parameters.widget.set_progress_bar(10)

        if input_parameters.ghy_diff_plane == 4:
            # FIRST: X DIRECTION
            input_parameters.ghy_diff_plane = 1

            hy_init(input_parameters, calculation_parameters)		#Calculate functions needed to construct exit pupil function

            input_parameters.widget.status_message("Sagittal: Initialization completed")
            input_parameters.widget.set_progress_bar(10)

            input_parameters.widget.status_message("Sagittal: Start Wavefront Propagation")
            hy_prop(input_parameters, calculation_parameters)	    #Perform wavefront propagation

            input_parameters.widget.status_message("Sagittal: Start Ray Resampling")
            input_parameters.widget.set_progress_bar(40)

            hy_conv(input_parameters, calculation_parameters)	    #Perform ray resampling

            # SECOND: Z DIRECTION
            input_parameters.ghy_diff_plane = 2

            hy_init(input_parameters, calculation_parameters)		#Calculate functions needed to construct exit pupil function

            input_parameters.widget.status_message("Tangential: Initialization completed")
            input_parameters.widget.set_progress_bar(50)

            input_parameters.widget.status_message("Tangential: Start Wavefront Propagation")
            hy_prop(input_parameters, calculation_parameters)	    #Perform wavefront propagation

            input_parameters.widget.status_message("Tangential: Start Ray Resampling")
            input_parameters.widget.set_progress_bar(80)

            hy_conv(input_parameters, calculation_parameters)	    #Perform ray resampling

            input_parameters.widget.status_message("Both: Creating Output Shadow Beam")

            input_parameters.ghy_diff_plane = 3

            hy_create_shadow_beam(input_parameters, calculation_parameters)

        else:
            hy_init(input_parameters, calculation_parameters)		#Calculate functions needed to construct exit pupil function

            input_parameters.widget.status_message("Initialization completed")
            input_parameters.widget.set_progress_bar(20)

            input_parameters.widget.status_message("Start Wavefront Propagation")
            hy_prop(input_parameters, calculation_parameters)	    #Perform wavefront propagation

            input_parameters.widget.status_message("Start Ray Resampling")
            input_parameters.widget.set_progress_bar(80)

            hy_conv(input_parameters, calculation_parameters)	    #Perform ray resampling

            input_parameters.widget.status_message("Creating Output Shadow Beam")

            hy_create_shadow_beam(input_parameters, calculation_parameters)

    except HybridNotNecessaryWarning as warning:
         QMessageBox.warning(input_parameters.widget, "Error", str(warning), QMessageBox.Ok)

    except Exception as exception:
        raise exception

    return calculation_parameters

##########################################################################

def hy_check_congruence(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    if input_parameters.ghy_n_oe < 0 and input_parameters.shadow_beam._oe_number == 0: # TODO!!!!!
        raise Exception("Source calculation not yet supported")

    beam_after = input_parameters.shadow_beam
    history_entry =  beam_after.getOEHistory(beam_after._oe_number)

    widget_class_name = history_entry._widget_class_name

    if input_parameters.ghy_calcType == 1 and not "ScreenSlits" in widget_class_name:
        raise Exception("Simple Aperture calculation runs for Screen-Slits widgets only")

    if input_parameters.ghy_calcType == 2:
        if not ("Mirror" in widget_class_name or "Grating" in widget_class_name):
            raise Exception("Mirror/Grating calculation runs for Mirror/Grating widgets only")

    if input_parameters.ghy_calcType == 3:
        if not ("Mirror" in widget_class_name):
            raise Exception("Mirror calculation runs for Mirror widgets only")

    if input_parameters.ghy_calcType == 4:
        if not ("Grating" in widget_class_name):
            raise Exception("Grating calculation runs for Gratings widgets only")

    if input_parameters.ghy_calcType in [5, 6]:
        if not ("Lens" in widget_class_name or "CRL" in widget_class_name or "Transfocator"):
            raise Exception("CRL calculation runs for Lens, CRLs or Transfocators widgets only")

    if input_parameters.ghy_calcType == 7:
        if not ("ScreenSlits" in widget_class_name):
            raise Exception("Windows calculation runs for Screen-Slits widgets only")
        oe_before = history_entry._shadow_oe_start.duplicate()

        if not (oe_before._oe.I_ABS[0] == 1 and oe_before._oe.I_SLIT[0] == 0):
            raise Exception("Windows calculation runs for Screen-Slits with no Aperturing and with Absorption")

    if input_parameters.ghy_n_oe < 0:
        beam_before = history_entry._input_beam.duplicate()
        oe_before   = history_entry._shadow_oe_start.duplicate()

        number_of_good_rays_before = len(beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)])
        number_of_good_rays_after  = len(beam_after._beam.rays[numpy.where(beam_after._beam.rays[:, 9] == 1)])

        if number_of_good_rays_before == number_of_good_rays_after:
            calculation_parameters.beam_not_cut_in_x = True
            calculation_parameters.beam_not_cut_in_z = True

            if (not input_parameters.ghy_calcType in [3, 4, 6, 7]) and input_parameters.ghy_automatic == 1:
                calculation_parameters.ff_beam = input_parameters.shadow_beam

                raise HybridNotNecessaryWarning("O.E. contains the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")
        else:
            # displacements analysis
            if input_parameters.ghy_calcType < 5 and oe_before._oe.F_MOVE==1:
                if input_parameters.ghy_calcType == 2 or input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
                    if input_parameters.ghy_diff_plane == 1: #X
                        if oe_before._oe.X_ROT != 0.0 or oe_before._oe.Z_ROT != 0.0:
                            raise Exception("Only rotations around the Y axis are supported for sagittal diffraction plane")
                    elif input_parameters.ghy_diff_plane == 2 or input_parameters.ghy_diff_plane == 3: #Z
                        if oe_before._oe.Y_ROT != 0.0 or oe_before._oe.Z_ROT != 0.0:
                            raise Exception("Only rotations around the X axis are supported for tangential or Both (2D) diffraction planes")
                    elif input_parameters.ghy_diff_plane == 4: #Z
                        if oe_before._oe.Z_ROT != 0.0:
                            raise Exception("Only rotations around the X and Y axis are supported for Both (1D+1D) diffraction planes")
                else:
                    raise Exception("O.E. Movements are not supported for this kind of calculation")

            ticket_tangential = None
            ticket_sagittal = None
            max_tangential = numpy.Inf
            min_tangential = -numpy.Inf
            max_sagittal = numpy.Inf
            min_sagittal = -numpy.Inf
            is_infinite = False

            # CASE SIMPLE APERTURE:
            if input_parameters.ghy_calcType == 1:
                if oe_before._oe.I_SLIT[0] == 0: # NOT APERTURE
                    is_infinite = True
                else:
                    if oe_before._oe.I_STOP[0] == 1: # OBSTRUCTION
                        raise Exception("Simple Aperture calculation runs for apertures only")

                    beam_at_the_slit = beam_before.duplicate(history=False)
                    beam_at_the_slit._beam.retrace(oe_before._oe.T_SOURCE) # TRACE INCIDENT BEAM UP TO THE SLIT

                    # TODO: MANAGE CASE OF ROTATED SLITS (OE MOVEMENT OR SOURCE MOVEMENT)
                    max_tangential = oe_before._oe.CZ_SLIT[0] + oe_before._oe.RZ_SLIT[0]/2
                    min_tangential = oe_before._oe.CZ_SLIT[0] - oe_before._oe.RZ_SLIT[0]/2
                    max_sagittal = oe_before._oe.CX_SLIT[0] + oe_before._oe.RX_SLIT[0]/2
                    min_sagittal = oe_before._oe.CX_SLIT[0] - oe_before._oe.RX_SLIT[0]/2

                    ticket_tangential = beam_at_the_slit._beam.histo1(3, nbins=500, nolost=1, ref=23)
                    ticket_sagittal = beam_at_the_slit._beam.histo1(1, nbins=500, nolost=1, ref=23)
            elif input_parameters.ghy_calcType == 7: # Windows
                is_infinite = True
            elif input_parameters.ghy_calcType in [2, 3, 4]: # MIRRORS/GRATINGS
                if oe_before._oe.FHIT_C == 0: #infinite
                    is_infinite = True
                else:
                    str_n_oe = str(input_parameters.shadow_beam._oe_number)
                    if input_parameters.shadow_beam._oe_number < 10:
                        str_n_oe = "0" + str_n_oe

                    beam_before._beam.rays = beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)] # GOOD ONLY BEFORE THE BEAM

                    oe_before._oe.FWRITE = 1
                    mirror_beam = ShadowBeam.traceFromOE(beam_before, oe_before, history=False)
                    mirror_beam.loadFromFile("mirr." + str_n_oe)

                    max_tangential = oe_before._oe.RLEN1
                    min_tangential = oe_before._oe.RLEN2
                    max_sagittal = oe_before._oe.RWIDX1
                    min_sagittal = oe_before._oe.RWIDX2
                    ticket_tangential = mirror_beam._beam.histo1(2, nbins=500, nolost=0, ref=23) # ALL THE RAYS FOR ANALYSIS
                    ticket_sagittal = mirror_beam._beam.histo1(1, nbins=500, nolost=0, ref=23) # ALL THE RAYS  FOR ANALYSIS

            elif input_parameters.ghy_calcType in [5, 6]: # CRL/LENS/TRANSFOCATOR
                oes_list = history_entry._shadow_oe_end._oe.list

                beam_at_the_slit = beam_before.duplicate(history=False)
                beam_at_the_slit._beam.retrace(oes_list[0].T_SOURCE) # TRACE INCIDENT BEAM UP TO THE SLIT

                is_infinite = True
                max_tangential_list = []
                min_tangential_list = []
                max_sagittal_list = []
                min_sagittal_list = []
                for oe in oes_list:
                    if oe.FHIT_C == 1:
                        is_infinite = False

                        max_tangential_list.append(numpy.abs(oe.RLEN2))
                        min_tangential_list.append(-numpy.abs(oe.RLEN2))
                        max_sagittal_list.append(numpy.abs(oe.RWIDX2))
                        min_sagittal_list.append(-numpy.abs(oe.RWIDX2))

                if not is_infinite:
                    max_tangential = numpy.min(max_tangential_list)
                    min_tangential = numpy.max(min_tangential_list)
                    max_sagittal = numpy.min(max_sagittal_list)
                    min_sagittal = numpy.max(min_sagittal_list)

                ticket_tangential = beam_at_the_slit._beam.histo1(3, nbins=500, nolost=1, ref=23)
                ticket_sagittal = beam_at_the_slit._beam.histo1(1, nbins=500, nolost=1, ref=23)

            ############################################################################

            if is_infinite:
                calculation_parameters.beam_not_cut_in_x = True
                calculation_parameters.beam_not_cut_in_z = True
            else: # ANALYSIS OF THE HISTOGRAMS
                # SAGITTAL
                intensity_sagittal = ticket_sagittal['histogram']
                total_intensity_sagittal = numpy.sum(intensity_sagittal) # should be identical to total_intensity_tangential
                coordinate_sagittal = ticket_sagittal['bin_center']

                cursor_up = numpy.where(coordinate_sagittal < min_sagittal)
                cursor_down = numpy.where(coordinate_sagittal > max_sagittal)
                intensity_sagittal_cut = (numpy.sum(intensity_sagittal[cursor_up]) + numpy.sum(intensity_sagittal[cursor_down]))/total_intensity_sagittal

                # TANGENTIAL
                intensity_tangential = ticket_tangential['histogram']
                total_intensity_tangential = numpy.sum(intensity_tangential)
                coordinate_tangential = ticket_tangential['bin_center']

                cursor_up = numpy.where(coordinate_tangential < min_tangential)
                cursor_down = numpy.where(coordinate_tangential > max_tangential)
                intensity_tangential_cut = (numpy.sum(intensity_tangential[cursor_up]) + numpy.sum(intensity_tangential[cursor_down]))/total_intensity_tangential

                calculation_parameters.beam_not_cut_in_x = intensity_sagittal_cut < 0.05
                calculation_parameters.beam_not_cut_in_z = intensity_tangential_cut < 0.05

            # REQUEST FILTERING OR REFUSING

            if not input_parameters.ghy_calcType in [3, 4, 6, 7]: # no figure/thickness errors
                if input_parameters.ghy_automatic == 1:
                    if input_parameters.ghy_diff_plane == 1 and calculation_parameters.beam_not_cut_in_x :
                        calculation_parameters.ff_beam = input_parameters.original_shadow_beam

                        raise HybridNotNecessaryWarning("O.E. contains almost the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")

                    if input_parameters.ghy_diff_plane == 2 and calculation_parameters.beam_not_cut_in_z:
                        calculation_parameters.ff_beam = input_parameters.original_shadow_beam

                        raise HybridNotNecessaryWarning("O.E. contains almost the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")

                    if input_parameters.ghy_diff_plane == 3 or input_parameters.ghy_diff_plane == 4: # BOTH
                        if calculation_parameters.beam_not_cut_in_x and calculation_parameters.beam_not_cut_in_z:
                            calculation_parameters.ff_beam = input_parameters.original_shadow_beam

                            raise HybridNotNecessaryWarning("O.E. contains almost the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")

                        if calculation_parameters.beam_not_cut_in_x:
                            input_parameters.ghy_diff_plane = 2

                            QMessageBox.warning(input_parameters.widget,
                                                "Warning",
                                                "O.E. does not cut the beam in the Sagittal plane:\nCalculation is done in Tangential plane only",
                                                QMessageBox.Ok)
                        elif calculation_parameters.beam_not_cut_in_z:
                            input_parameters.ghy_diff_plane = 1

                            QMessageBox.warning(input_parameters.widget,
                                                "Warning",
                                                "O.E. does not cut the beam in the Tangential plane:\nCalculation is done in Sagittal plane only",
                                                QMessageBox.Ok)

##########################################################################

def hy_readfiles(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    if input_parameters.ghy_calcType in [5, 6]: #CRL OR LENS
        history_entry =  input_parameters.shadow_beam.getOEHistory(input_parameters.shadow_beam._oe_number)
        compound_oe = history_entry._shadow_oe_end

        last_oe = compound_oe._oe.list[-1]

        if last_oe.FHIT_C == 0: #infinite
            raise Exception("Calculation not possible: lenses have infinite extension")

        image_plane_distance = last_oe.T_IMAGE

        screen_slit = ShadowOpticalElement.create_screen_slit()

        screen_slit._oe.DUMMY = input_parameters.widget.workspace_units_to_cm # Issue #3 : Global User's Unit
        screen_slit._oe.T_SOURCE     = -image_plane_distance
        screen_slit._oe.T_IMAGE      = image_plane_distance
        screen_slit._oe.T_INCIDENCE  = 0.0
        screen_slit._oe.T_REFLECTION = 180.0
        screen_slit._oe.ALPHA        = 0.0

        n_screen = 1
        i_screen = numpy.zeros(10)  # after
        i_abs = numpy.zeros(10)
        i_slit = numpy.zeros(10)
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        i_slit[0] = 1
        k_slit[0] = 1

        rx_slit[0] = numpy.abs(2*last_oe.RWIDX2)
        rz_slit[0] = numpy.abs(2*last_oe.RLEN2)

        screen_slit._oe.set_screens(n_screen,
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

        input_parameters.shadow_beam = ShadowBeam.traceFromOE(input_parameters.shadow_beam, screen_slit)

    str_n_oe = str(input_parameters.shadow_beam._oe_number)
    if input_parameters.shadow_beam._oe_number < 10: str_n_oe = "0" + str_n_oe

    # Before ray-tracing save the original history:
    calculation_parameters.original_beam_history = input_parameters.shadow_beam.getOEHistory()

    history_entry =  input_parameters.shadow_beam.getOEHistory(input_parameters.shadow_beam._oe_number)

    shadow_oe = history_entry._shadow_oe_start.duplicate() # no changes to the original object!
    shadow_oe_input_beam = history_entry._input_beam.duplicate(history=False)
    
    if shadow_oe._oe.F_SCREEN == 1:
        if shadow_oe._oe.N_SCREEN == 10: raise Exception("Hybrid Screen has not been created: O.E. has already 10 screens")

        n_screen     = shadow_oe._oe.N_SCREEN + 1
        i_screen     = shadow_oe._oe.I_SCREEN
        sl_dis       = shadow_oe._oe.SL_DIS
        i_abs        = shadow_oe._oe.I_ABS
        i_slit       = shadow_oe._oe.I_SLIT
        i_stop       = shadow_oe._oe.I_STOP      
        k_slit       = shadow_oe._oe.K_SLIT      
        thick        = shadow_oe._oe.THICK       
        file_abs     = numpy.copy(shadow_oe._oe.FILE_ABS)
        rx_slit      = shadow_oe._oe.RX_SLIT     
        rz_slit      = shadow_oe._oe.RZ_SLIT     
        cx_slit      = shadow_oe._oe.CX_SLIT     
        cz_slit      = shadow_oe._oe.CZ_SLIT     
        file_scr_ext = numpy.copy(shadow_oe._oe.FILE_SCR_EXT)
        
        index = n_screen - 1
        
        i_screen[index] = 0 
        sl_dis[index] = 0       
        i_abs[index] = 0        
        i_slit[index] = 0       
        i_stop[index] = 0       
        k_slit[index] = 0       
        thick[index] = 0        
        rx_slit[index] = 0
        rz_slit[index] = 0      
        cx_slit[index] = 0      
        cz_slit[index] = 0
    else:
        n_screen = 1
        i_screen = numpy.zeros(10)  # after
        i_abs = numpy.zeros(10)
        i_slit = numpy.zeros(10)
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)
        
        #index = 0

    fileShadowScreen = "screen." + str_n_oe + ("0" + str(n_screen)) if n_screen < 10 else "10"

    if input_parameters.ghy_calcType in [1, 5, 6, 7]: # simple aperture or CRLs
        if not (shadow_oe._oe.FMIRR == 5 and \
            shadow_oe._oe.F_CRYSTAL == 0 and \
            shadow_oe._oe.F_REFRAC == 2 and \
            shadow_oe._oe.F_SCREEN == 1 and \
            shadow_oe._oe.N_SCREEN == 1):
            '''
            i_abs[1] = shadow_oe._oe.I_ABS[0]
            i_slit[1] = shadow_oe._oe.I_SLIT[0]

            if shadow_oe._oe.I_SLIT[index-1] == 1:
                i_stop[1] = shadow_oe._oe.I_STOP[0]
                k_slit[1] = shadow_oe._oe.K_SLIT[0]

                if shadow_oe._oe.K_SLIT[0] == 2:
                    file_scr_ext[index] = shadow_oe._oe.FILE_SCR_EXT[0]
                else:
                    rx_slit[1] = shadow_oe._oe.RX_SLIT[0]
                    rz_slit[1] = shadow_oe._oe.RZ_SLIT[0]
                    cx_slit[1] = shadow_oe._oe.CX_SLIT[0]
                    cz_slit[1] = shadow_oe._oe.CZ_SLIT[0]

            if shadow_oe._oe.I_ABS[0] == 1:
                thick[1] = shadow_oe._oe.THICK[0]
                file_abs[1] = shadow_oe._oe.FILE_ABS[0]
        else:
            '''
            raise Exception("Connected O.E. is not a Screen-Slit or CRL widget!")
    elif input_parameters.ghy_calcType == 2: # ADDED BY XIANBO SHI
        shadow_oe._oe.F_RIPPLE = 0
    elif input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4: # mirror/grating + figure error
        if shadow_oe._oe.F_RIPPLE == 1 and shadow_oe._oe.F_G_S == 2:
            input_parameters.ghy_mirrorfile = shadow_oe._oe.FILE_RIP

            # disable slope error calculation for OE, must be done by HYBRID!
            shadow_oe._oe.F_RIPPLE = 0
        else:
            raise Exception("O.E. has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")

    #TODO: check compatibility between hybrid calcualtion and angle of rotations (es. tangential -> rot X, sagittal -> rot Y)

    # tracing must be done without o.e. movements: hybrid is going to take care of that
    x_rot  = shadow_oe._oe.X_ROT
    y_rot  = shadow_oe._oe.Y_ROT
    z_rot  = shadow_oe._oe.Z_ROT

    shadow_oe._oe.X_ROT  = 0.0
    shadow_oe._oe.Y_ROT  = 0.0
    shadow_oe._oe.Z_ROT  = 0.0

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
                              file_scr_ext)

    if input_parameters.ghy_calcType > 0: # THIS WAS RESPONSIBLE OF THE SERIOUS BUG AT SOS WORKSHOP!!!!!
        if shadow_oe._oe.FWRITE > 1 or shadow_oe._oe.F_ANGLE == 0:
            shadow_oe._oe.FWRITE = 0 # all
            shadow_oe._oe.F_ANGLE = 1 # angles

    # need to rerun simulation

    input_parameters.widget.status_message("Creating HYBRID screen: redo simulation with modified O.E.")

    shadow_beam_at_image_plane = ShadowBeam.traceFromOE(shadow_oe_input_beam, shadow_oe, history=False)

    # restore o.e. setting for further calculations
    shadow_oe._oe.X_ROT  = x_rot
    shadow_oe._oe.Y_ROT  = y_rot
    shadow_oe._oe.Z_ROT  = z_rot

    input_parameters.shadow_beam = shadow_beam_at_image_plane

    image_beam, image_beam_lo = read_shadow_beam(shadow_beam_at_image_plane, lost=True) #xshi change from 0 to 1

    calculation_parameters.shadow_oe_end = shadow_oe

    if input_parameters.file_to_write_out == 1:
        image_beam.writeToFile("hybrid_beam_at_image_plane." + str_n_oe)

    calculation_parameters.image_plane_beam = image_beam
    calculation_parameters.image_plane_beam.set_initial_flux(input_parameters.original_shadow_beam.get_initial_flux())
    calculation_parameters.image_plane_beam_lost = image_beam_lo

    # read shadow screen file
    screen_beam= sh_readsh(fileShadowScreen)    #xshi change from 0 to 1

    if input_parameters.file_to_write_out == 1:
        screen_beam.writeToFile("hybrid_beam_at_oe_hybrid_screen." + str_n_oe)

    calculation_parameters.screen_plane_beam = screen_beam

    calculation_parameters.wenergy     = ShadowPhysics.getEnergyFromShadowK(screen_beam._beam.rays[:, 10])
    calculation_parameters.wwavelength = ShadowPhysics.getWavelengthFromShadowK(screen_beam._beam.rays[:, 10])
    calculation_parameters.xp_screen   = screen_beam._beam.rays[:, 3]
    calculation_parameters.yp_screen   = screen_beam._beam.rays[:, 4]
    calculation_parameters.zp_screen   = screen_beam._beam.rays[:, 5]

    genergy = numpy.average(calculation_parameters.wenergy) # average photon energy in eV

    input_parameters.widget.status_message("Using MEAN photon energy [eV]:" + str(genergy))

    calculation_parameters.xx_screen = screen_beam._beam.rays[:, 0]
    calculation_parameters.ghy_x_min = numpy.min(calculation_parameters.xx_screen)
    calculation_parameters.ghy_x_max = numpy.max(calculation_parameters.xx_screen)

    calculation_parameters.zz_screen = screen_beam._beam.rays[:, 2]
    calculation_parameters.ghy_z_min = numpy.min(calculation_parameters.zz_screen)
    calculation_parameters.ghy_z_max = numpy.max(calculation_parameters.zz_screen)

    calculation_parameters.dx_ray = numpy.arctan(calculation_parameters.xp_screen/calculation_parameters.yp_screen) # calculate divergence from direction cosines from SHADOW file  dx = atan(v_x/v_y)
    calculation_parameters.dz_ray = numpy.arctan(calculation_parameters.zp_screen/calculation_parameters.yp_screen) # calculate divergence from direction cosines from SHADOW file  dz = atan(v_z/v_y)

    # Process mirror/grating
	# reads file with mirror height mesh
 	# calculates the function of the "incident angle" and the "mirror height" versus the Z coordinate in the screen.

    if input_parameters.ghy_calcType in [2, 3, 4]:
        mirror_beam = sh_readsh("mirr." + str_n_oe)  #xshi change from 0 to 1

        if input_parameters.file_to_write_out == 1:
            mirror_beam.writeToFile("hybrid_footprint_on_oe." + str_n_oe)

        calculation_parameters.xx_mirr = mirror_beam._beam.rays[:, 0]
        calculation_parameters.yy_mirr = mirror_beam._beam.rays[:, 1]
        calculation_parameters.zz_mirr = mirror_beam._beam.rays[:, 2]

        # read in angle files

        angle_inc, angle_ref = sh_readangle("angle." + str_n_oe, mirror_beam)   #xshi change from 0 to 1

        calculation_parameters.angle_inc = (90.0 - angle_inc)/180.0*1e3*numpy.pi
        calculation_parameters.angle_ref = (90.0 - angle_ref)/180.0*1e3*numpy.pi

        if not input_parameters.ghy_calcType == 2:
            calculation_parameters.w_mirr_2D_values = sh_readsurface(input_parameters.ghy_mirrorfile, dimension=2)

        # generate theta(z) and l(z) curve over a continuous grid

        hy_npoly_angle = 3
        hy_npoly_l = 6

        if numpy.amax(calculation_parameters.xx_screen) == numpy.amin(calculation_parameters.xx_screen):
            if input_parameters.ghy_diff_plane == 1 or input_parameters.ghy_diff_plane == 3: raise Exception("Unconsistend calculation: Diffraction plane is set on X, but the beam has no extention in that direction")
        else:
            calculation_parameters.wangle_x     = numpy.poly1d(numpy.polyfit(calculation_parameters.xx_screen, calculation_parameters.angle_inc, hy_npoly_angle))
            calculation_parameters.wl_x         = numpy.poly1d(numpy.polyfit(calculation_parameters.xx_screen, calculation_parameters.xx_mirr, hy_npoly_l))
            if input_parameters.ghy_calcType == 4: calculation_parameters.wangle_ref_x = numpy.poly1d(numpy.polyfit(calculation_parameters.xx_screen, calculation_parameters.angle_ref, hy_npoly_angle))

        if numpy.amax(calculation_parameters.zz_screen) == numpy.amin(calculation_parameters.zz_screen):
            if input_parameters.ghy_diff_plane == 2 or input_parameters.ghy_diff_plane == 3: raise Exception("Unconsistend calculation: Diffraction plane is set on Z, but the beam has no extention in that direction")
        else:
            calculation_parameters.wangle_z     = numpy.poly1d(numpy.polyfit(calculation_parameters.zz_screen, calculation_parameters.angle_inc, hy_npoly_angle))
            calculation_parameters.wl_z         = numpy.poly1d(numpy.polyfit(calculation_parameters.zz_screen, calculation_parameters.yy_mirr, hy_npoly_l))
            if input_parameters.ghy_calcType == 4: calculation_parameters.wangle_ref_z = numpy.poly1d(numpy.polyfit(calculation_parameters.zz_screen, calculation_parameters.angle_ref, hy_npoly_angle))
    elif input_parameters.ghy_calcType in [6, 7]:
        calculation_parameters.w_mirr_2D_values = [h5_readsurface(thickness_error_file) for thickness_error_file in input_parameters.absorber_error_profiles]

##########################################################################

def hy_init(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    oe_number = input_parameters.shadow_beam._oe_number

    if input_parameters.ghy_calcType > 1:
        simag = calculation_parameters.shadow_oe_end._oe.SIMAG

        if input_parameters.ghy_focallength < 0:
            input_parameters.ghy_focallength = simag
            input_parameters.widget.status_message("Focal length not set (<-1), take from SIMAG" + str(input_parameters.ghy_focallength))

        if input_parameters.ghy_focallength != simag:
            input_parameters.widget.status_message("Defined focal length is different from SIMAG, used the defined focal length = " + str(input_parameters.ghy_focallength))
        else:
            input_parameters.widget.status_message("Focal length = " + str(input_parameters.ghy_focallength))

    if input_parameters.ghy_diff_plane == 1 or input_parameters.ghy_diff_plane == 3:
        calculation_parameters.xx_focal_ray = copy.deepcopy(calculation_parameters.xx_screen) + \
                                              input_parameters.ghy_focallength * numpy.tan(calculation_parameters.dx_ray)


    if input_parameters.ghy_diff_plane == 2 or input_parameters.ghy_diff_plane == 3:
        calculation_parameters.zz_focal_ray = copy.deepcopy(calculation_parameters.zz_screen) + \
                                              input_parameters.ghy_focallength * numpy.tan(calculation_parameters.dz_ray)


    t_image = calculation_parameters.shadow_oe_end._oe.T_IMAGE

    if input_parameters.ghy_distance < 0:
        if oe_number != 0:
            input_parameters.ghy_distance = t_image
            input_parameters.widget.status_message("Distance not set (<-1), take from T_IMAGE" + str(input_parameters.ghy_distance))

    if oe_number != 0:
        if (input_parameters.ghy_distance == t_image):
            input_parameters.widget.status_message("Defined OE star plane distance is different from T_IMAGE, used the defined distance = " + str(input_parameters.ghy_distance))
        else:
            input_parameters.widget.status_message("Propagation distance = " + str(input_parameters.ghy_distance))

    if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4: # mirror/grating with figure error
        shadow_oe = calculation_parameters.shadow_oe_end

        if input_parameters.ghy_diff_plane == 1 or input_parameters.ghy_diff_plane == 3: #X
            offset_y_index =  0.0 if shadow_oe._oe.F_MOVE == 0 else shadow_oe._oe.OFFY/calculation_parameters.w_mirr_2D_values.delta_y()

            np_array = calculation_parameters.w_mirr_2D_values.z_values[:, int(len(calculation_parameters.w_mirr_2D_values.y_coord)/2 - offset_y_index)]

            calculation_parameters.w_mirror_lx = ScaledArray.initialize_from_steps(np_array,
                                                                                   calculation_parameters.w_mirr_2D_values.x_coord[0],
                                                                                   calculation_parameters.w_mirr_2D_values.x_coord[1] - calculation_parameters.w_mirr_2D_values.x_coord[0])

        if input_parameters.ghy_diff_plane == 2 or input_parameters.ghy_diff_plane == 3: #Z
            offset_x_index =  0.0 if shadow_oe._oe.F_MOVE == 0 else shadow_oe._oe.OFFX/calculation_parameters.w_mirr_2D_values.delta_x()

            np_array = calculation_parameters.w_mirr_2D_values.z_values[int(len(calculation_parameters.w_mirr_2D_values.x_coord)/2 - offset_x_index), :]

            calculation_parameters.w_mirror_lz = ScaledArray.initialize_from_steps(np_array,
                                                                                   calculation_parameters.w_mirr_2D_values.y_coord[0],
                                                                                   calculation_parameters.w_mirr_2D_values.y_coord[1] - calculation_parameters.w_mirr_2D_values.y_coord[0])

    # generate intensity profile (histogram): I_ray(z) curve

    if input_parameters.ghy_diff_plane == 1: # 1d in X
        if (input_parameters.ghy_nbins_x < 0):
            input_parameters.ghy_nbins_x = 200

        input_parameters.ghy_nbins_x = min(input_parameters.ghy_nbins_x, round(len(calculation_parameters.xx_screen) / 20)) #xshi change from 100 to 20
        input_parameters.ghy_nbins_x = max(input_parameters.ghy_nbins_x, 10)

        ticket = calculation_parameters.screen_plane_beam._beam.histo1(1,
                                                                       nbins=int(input_parameters.ghy_nbins_x),
                                                                       xrange=[numpy.min(calculation_parameters.xx_screen), numpy.max(calculation_parameters.xx_screen)],
                                                                       nolost=1,
                                                                       ref=23)

        bins = ticket['bins']

        calculation_parameters.wIray_x = ScaledArray.initialize_from_range(ticket['histogram'], bins[0], bins[len(bins)-1])
    elif input_parameters.ghy_diff_plane == 2: # 1d in Z
        if (input_parameters.ghy_nbins_z < 0):
            input_parameters.ghy_nbins_z = 200

        input_parameters.ghy_nbins_z = min(input_parameters.ghy_nbins_z, round(len(calculation_parameters.zz_screen) / 20)) #xshi change from 100 to 20
        input_parameters.ghy_nbins_z = max(input_parameters.ghy_nbins_z, 10)

        ticket = calculation_parameters.screen_plane_beam._beam.histo1(3,
                                                                       nbins=int(input_parameters.ghy_nbins_z),
                                                                       xrange=[numpy.min(calculation_parameters.zz_screen), numpy.max(calculation_parameters.zz_screen)],
                                                                       nolost=1,
                                                                       ref=23)

        bins = ticket['bins']

        calculation_parameters.wIray_z = ScaledArray.initialize_from_range(ticket['histogram'], bins[0], bins[len(bins)-1])
    elif input_parameters.ghy_diff_plane == 3: # 2D
        if (input_parameters.ghy_nbins_x < 0):
            input_parameters.ghy_nbins_x = 50

        if (input_parameters.ghy_nbins_z < 0):
            input_parameters.ghy_nbins_z = 50

        input_parameters.ghy_nbins_x = min(input_parameters.ghy_nbins_x, round(numpy.sqrt(len(calculation_parameters.xx_screen) / 10)))
        input_parameters.ghy_nbins_z = min(input_parameters.ghy_nbins_z, round(numpy.sqrt(len(calculation_parameters.zz_screen) / 10)))

        input_parameters.ghy_nbins_x = max(input_parameters.ghy_nbins_x, 10)
        input_parameters.ghy_nbins_z = max(input_parameters.ghy_nbins_z, 10)

        ticket = calculation_parameters.screen_plane_beam._beam.histo2(col_h=1,
                                                                       col_v=3,
                                                                       nbins_h=int(input_parameters.ghy_nbins_x),
                                                                       nbins_v=int(input_parameters.ghy_nbins_z),
                                                                       xrange=[numpy.min(calculation_parameters.xx_screen), numpy.max(calculation_parameters.xx_screen)],
                                                                       yrange=[numpy.min(calculation_parameters.zz_screen), numpy.max(calculation_parameters.zz_screen)],
                                                                       nolost=1,
                                                                       ref=23)

        bins_h = ticket['bin_h_edges']
        bins_v = ticket['bin_v_edges']
        calculation_parameters.wIray_x = ScaledArray.initialize_from_range(ticket['histogram_h'], bins_h[0], bins_h[len(bins_h)-1])
        calculation_parameters.wIray_z = ScaledArray.initialize_from_range(ticket['histogram_v'], bins_v[0], bins_v[len(bins_v)-1])
        calculation_parameters.wIray_2d = ScaledMatrix.initialize_from_range(ticket['histogram'], bins_h[0], bins_h[len(bins_h)-1], bins_v[0], bins_v[len(bins_v)-1])

    calculation_parameters.gwavelength = numpy.average(calculation_parameters.wwavelength)

    if input_parameters.ghy_lengthunit == 0:
        um = "m"
        calculation_parameters.gwavelength *= 1e-10
    if input_parameters.ghy_lengthunit == 1:
        um = "cm"
        calculation_parameters.gwavelength *= 1e-8
    elif input_parameters.ghy_lengthunit == 2:
        um = "mm"
        calculation_parameters.gwavelength *= 1e-7

    input_parameters.widget.status_message("Using MEAN photon wavelength (" + um + "): " + str(calculation_parameters.gwavelength))

    calculation_parameters.gknum = 2.0*numpy.pi/calculation_parameters.gwavelength #in [user-unit]^-1, wavenumber

    if input_parameters.ghy_calcType in [6, 7]:
        if input_parameters.absorber_delta is None:
            calculation_parameters.absorber_delta = get_delta(input_parameters, calculation_parameters)
        else:
            calculation_parameters.absorber_delta = input_parameters.absorber_delta

##########################################################################

def hy_prop(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):

    # set distance and focal length for the aperture propagation.
    if input_parameters.ghy_calcType in [1, 5, 6, 7]: # simple aperture
        if input_parameters.ghy_diff_plane == 1: # X
            calculation_parameters.ghy_focallength = (calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min)**2/calculation_parameters.gwavelength/input_parameters.ghy_npeak
        elif input_parameters.ghy_diff_plane == 2: # Z
            calculation_parameters.ghy_focallength = (calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min)**2/calculation_parameters.gwavelength/input_parameters.ghy_npeak
        elif input_parameters.ghy_diff_plane == 3: # 2D
            calculation_parameters.ghy_focallength = (max(numpy.abs(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min),
                                                          numpy.abs(calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min)))**2/calculation_parameters.gwavelength/input_parameters.ghy_npeak

        input_parameters.widget.status_message("Focal length set to: " + str(calculation_parameters.ghy_focallength))

    # automatic control of number of peaks to avoid numerical overflow
    if input_parameters.ghy_npeak < 0: # number of bins control
        if input_parameters.ghy_diff_plane == 3:
            input_parameters.ghy_npeak = 10
        else:
            input_parameters.ghy_npeak = 50

    input_parameters.ghy_npeak = max(input_parameters.ghy_npeak, 5)

    if input_parameters.ghy_fftnpts < 0:
        input_parameters.ghy_fftnpts = 4e6
    input_parameters.ghy_fftnpts = min(input_parameters.ghy_fftnpts, 4e6)

    input_parameters.widget.set_progress_bar(25)

    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        propagate_1D_x_direction(calculation_parameters, input_parameters)
    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        propagate_1D_z_direction(calculation_parameters, input_parameters)
    elif input_parameters.ghy_diff_plane == 3: #2D
        propagate_2D(calculation_parameters, input_parameters)

def hy_conv(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        if calculation_parameters.do_ff_x:
            s1d = Sampler1D(calculation_parameters.dif_xp.get_values(), calculation_parameters.dif_xp.get_abscissas())
            pos_dif = s1d.get_n_sampled_points(len(calculation_parameters.xp_screen))

            dx_wave = numpy.arctan(pos_dif) # calculate dx from tan(dx)
            dx_conv = dx_wave + calculation_parameters.dx_ray # add the ray divergence kicks

            calculation_parameters.xx_image_ff = calculation_parameters.xx_screen + input_parameters.ghy_distance*numpy.tan(dx_conv) # ray tracing to the image plane
            calculation_parameters.dx_conv = dx_conv

        if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
            s1d = Sampler1D(calculation_parameters.dif_x.get_values(), calculation_parameters.dif_x.get_abscissas())
            pos_dif = s1d.get_n_sampled_points(len(calculation_parameters.xx_focal_ray))

            calculation_parameters.xx_image_nf = pos_dif + calculation_parameters.xx_focal_ray
    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        if calculation_parameters.do_ff_z:
            s1d = Sampler1D(calculation_parameters.dif_zp.get_values(), calculation_parameters.dif_zp.get_abscissas())
            pos_dif = s1d.get_n_sampled_points(len(calculation_parameters.zp_screen))

            dz_wave = numpy.arctan(pos_dif) # calculate dz from tan(dz)
            dz_conv = dz_wave + calculation_parameters.dz_ray # add the ray divergence kicks

            calculation_parameters.zz_image_ff = calculation_parameters.zz_screen + input_parameters.ghy_distance*numpy.tan(dz_conv) # ray tracing to the image plane
            calculation_parameters.dz_conv = dz_conv

        if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
            s1d = Sampler1D(calculation_parameters.dif_z.get_values(), calculation_parameters.dif_z.get_abscissas())
            pos_dif = s1d.get_n_sampled_points(len(calculation_parameters.zz_focal_ray))

            calculation_parameters.zz_image_nf = pos_dif + calculation_parameters.zz_focal_ray
    elif input_parameters.ghy_diff_plane == 3: #2D
        if calculation_parameters.do_ff_x and calculation_parameters.do_ff_z:
            s2d = Sampler2D(calculation_parameters.dif_xpzp.z_values,
                            calculation_parameters.dif_xpzp.x_coord,
                            calculation_parameters.dif_xpzp.y_coord)

            pos_dif_x, pos_dif_z = s2d.get_n_sampled_points(len(calculation_parameters.zp_screen))

            dx_wave = numpy.arctan(pos_dif_x) # calculate dx from tan(dx)
            dx_conv = dx_wave + calculation_parameters.dx_ray # add the ray divergence kicks

            calculation_parameters.xx_image_ff = calculation_parameters.xx_screen + input_parameters.ghy_distance*numpy.tan(dx_conv) # ray tracing to the image plane
            calculation_parameters.dx_conv = dx_conv

            dz_wave = numpy.arctan(pos_dif_z) # calculate dz from tan(dz)
            dz_conv = dz_wave + calculation_parameters.dz_ray # add the ray divergence kicks

            calculation_parameters.zz_image_ff = calculation_parameters.zz_screen + input_parameters.ghy_distance*numpy.tan(dz_conv) # ray tracing to the image plane
            calculation_parameters.dz_conv = dz_conv

        if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
            s2d = Sampler2D(calculation_parameters.dif_xz.z_values,
                            calculation_parameters.dif_xz.x_coord,
                            calculation_parameters.dif_xz.y_coord)

            pos_dif_x, pos_dif_z = s2d.get_n_sampled_points(len(calculation_parameters.zp_screen))

            calculation_parameters.xx_image_nf = pos_dif_x + calculation_parameters.xx_focal_ray
            calculation_parameters.zz_image_nf = pos_dif_z + calculation_parameters.zz_focal_ray

    elif input_parameters.ghy_diff_plane == 4: #2D - x then Z
        pass
#########################################################################

def hy_create_shadow_beam(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    if do_nf:
        calculation_parameters.nf_beam = calculation_parameters.image_plane_beam.duplicate(history=False)
        calculation_parameters.nf_beam._oe_number = input_parameters.shadow_beam._oe_number

    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        if calculation_parameters.do_ff_x:
            calculation_parameters.ff_beam = calculation_parameters.image_plane_beam.duplicate(history=False)
            calculation_parameters.ff_beam._oe_number = input_parameters.shadow_beam._oe_number

            angle_perpen = numpy.arctan(calculation_parameters.zp_screen/calculation_parameters.yp_screen)
            angle_num = numpy.sqrt(1+(numpy.tan(angle_perpen))**2+(numpy.tan(calculation_parameters.dx_conv))**2)

            calculation_parameters.ff_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_ff)
            calculation_parameters.ff_beam._beam.rays[:, 3] = numpy.tan(calculation_parameters.dx_conv)/angle_num
            calculation_parameters.ff_beam._beam.rays[:, 4] = 1/angle_num
            calculation_parameters.ff_beam._beam.rays[:, 5] = numpy.tan(angle_perpen)/angle_num

            calculation_parameters.ff_beam = ShadowBeam.mergeBeams(calculation_parameters.ff_beam, calculation_parameters.image_plane_beam_lost)
        else:
            calculation_parameters.ff_beam = input_parameters.original_shadow_beam

        if do_nf:
            calculation_parameters.nf_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_nf)

    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        if calculation_parameters.do_ff_z:
            calculation_parameters.ff_beam = calculation_parameters.image_plane_beam.duplicate(history=False)
            calculation_parameters.ff_beam._oe_number = input_parameters.shadow_beam._oe_number

            angle_perpen = numpy.arctan(calculation_parameters.xp_screen/calculation_parameters.yp_screen)
            angle_num = numpy.sqrt(1+(numpy.tan(angle_perpen))**2+(numpy.tan(calculation_parameters.dz_conv))**2)

            calculation_parameters.ff_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_ff)
            calculation_parameters.ff_beam._beam.rays[:, 3] = numpy.tan(angle_perpen)/angle_num
            calculation_parameters.ff_beam._beam.rays[:, 4] = 1/angle_num
            calculation_parameters.ff_beam._beam.rays[:, 5] = numpy.tan(calculation_parameters.dz_conv)/angle_num

            calculation_parameters.ff_beam = ShadowBeam.mergeBeams(calculation_parameters.ff_beam, calculation_parameters.image_plane_beam_lost)
        else:
            calculation_parameters.ff_beam = input_parameters.original_shadow_beam

        if do_nf:
             calculation_parameters.nf_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_nf)

    elif input_parameters.ghy_diff_plane == 3: # 2d calculation
        if calculation_parameters.do_ff_x or calculation_parameters.do_ff_z:
            calculation_parameters.ff_beam = calculation_parameters.image_plane_beam.duplicate(history=False)
            calculation_parameters.ff_beam._oe_number = input_parameters.shadow_beam._oe_number

            angle_num = numpy.sqrt(1+(numpy.tan(calculation_parameters.dz_conv))**2+(numpy.tan(calculation_parameters.dx_conv))**2)

            calculation_parameters.ff_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_ff)
            calculation_parameters.ff_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_ff)
            calculation_parameters.ff_beam._beam.rays[:, 3] = numpy.tan(calculation_parameters.dx_conv)/angle_num
            calculation_parameters.ff_beam._beam.rays[:, 4] = 1/angle_num
            calculation_parameters.ff_beam._beam.rays[:, 5] = numpy.tan(calculation_parameters.dz_conv)/angle_num

            calculation_parameters.ff_beam = ShadowBeam.mergeBeams(calculation_parameters.ff_beam, calculation_parameters.image_plane_beam_lost)
        else:
            calculation_parameters.ff_beam = input_parameters.original_shadow_beam

        if do_nf:
            calculation_parameters.nf_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_nf)
            calculation_parameters.nf_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_nf)

    if do_nf: calculation_parameters.nf_beam = ShadowBeam.mergeBeams(calculation_parameters.nf_beam, calculation_parameters.image_plane_beam_lost)

    if input_parameters.file_to_write_out == 1:

        if input_parameters.ghy_n_oe < 0:
            str_n_oe = str(input_parameters.shadow_beam._oe_number)

            if input_parameters.shadow_beam._oe_number < 10:
                str_n_oe = "0" + str_n_oe
        else: # compatibility with old verion
            str_n_oe = str(input_parameters.ghy_n_oe)

            if input_parameters.ghy_n_oe < 10:
                str_n_oe = "0" + str_n_oe

        calculation_parameters.ff_beam.writeToFile("hybrid_ff_beam." + str_n_oe)
        if do_nf: calculation_parameters.nf_beam.writeToFile("hybrid_nf_beam." + str_n_oe)

    calculation_parameters.ff_beam.history = calculation_parameters.original_beam_history
    if do_nf: calculation_parameters.nf_beam.history = calculation_parameters.original_beam_history

##########################################################################
# 1D PROPAGATION ALGORITHM - X DIRECTION
##########################################################################

def propagate_1D_x_direction(calculation_parameters, input_parameters):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    scale_factor = 1.0

    shadow_oe = calculation_parameters.shadow_oe_end

    global_phase_shift_profile = None

    if shadow_oe._oe.F_MOVE == 1 and shadow_oe._oe.Y_ROT != 0.0:
        if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
            global_phase_shift_profile = calculation_parameters.w_mirror_lx
        elif input_parameters.ghy_calcType == 2:
            global_phase_shift_profile = ScaledArray.initialize_from_range(numpy.zeros(3), shadow_oe._oe.RWIDX2, shadow_oe._oe.RWIDX1)

        global_phase_shift_profile.set_values(global_phase_shift_profile.get_values() +
                                              global_phase_shift_profile.get_abscissas()*numpy.sin(numpy.radians(-shadow_oe._oe.Y_ROT)))
    elif input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
        global_phase_shift_profile = calculation_parameters.w_mirror_lx

    if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
        rms_slope = hy_findrmsslopefromheight(global_phase_shift_profile)

        input_parameters.widget.status_message("Using RMS slope = " + str(rms_slope))

        average_incident_angle = numpy.radians(90-calculation_parameters.shadow_oe_end._oe.T_INCIDENCE)*1e3
        average_reflection_angle = numpy.radians(90-calculation_parameters.shadow_oe_end._oe.T_REFLECTION)*1e3

        if calculation_parameters.beam_not_cut_in_x:
            dp_image = numpy.std(calculation_parameters.xx_focal_ray)/input_parameters.ghy_focallength
            dp_se = 2 * rms_slope * numpy.sin(average_incident_angle/1e3)	# different in x and z
            dp_error = calculation_parameters.gwavelength/2/(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min)

            scale_factor = max(1, 5*min(dp_error/dp_image, dp_error/dp_se))

    # ------------------------------------------
    # far field calculation
    # ------------------------------------------
    if calculation_parameters.do_ff_x:
        focallength_ff = calculate_focal_length_ff(calculation_parameters.ghy_x_min,
                                                   calculation_parameters.ghy_x_max,
                                                   input_parameters.ghy_npeak,
                                                   calculation_parameters.gwavelength)

        if input_parameters.ghy_calcType == 3:
            if not (rms_slope == 0.0 or average_incident_angle == 0.0):
                focallength_ff = min(focallength_ff,(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min) / 16 / rms_slope / numpy.sin(average_incident_angle / 1e3))#xshi changed
        elif input_parameters.ghy_calcType == 4:
            if not (rms_slope == 0.0 or average_incident_angle == 0.0):
                focallength_ff = min(focallength_ff,(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min) / 8 / rms_slope / (numpy.sin(average_incident_angle / 1e3) + numpy.sin(average_reflection_angle / 1e3)))#xshi changed
        elif input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None:
            focallength_ff = min(focallength_ff, input_parameters.ghy_distance*4) #TODO: PATCH to be found with a formula

        fftsize = int(scale_factor * calculate_fft_size(calculation_parameters.ghy_x_min,
                                                        calculation_parameters.ghy_x_max,
                                                        calculation_parameters.gwavelength,
                                                        focallength_ff,
                                                        input_parameters.ghy_fftnpts))

        if do_nf: input_parameters.widget.set_progress_bar(27)
        else: input_parameters.widget.set_progress_bar(30)
        input_parameters.widget.status_message("FF: creating plane wave begin, fftsize = " +  str(fftsize))

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=scale_factor * calculation_parameters.ghy_x_min,
                                                                x_max=scale_factor * calculation_parameters.ghy_x_max)

        if scale_factor == 1.0:
            try:
                wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_x.interpolate_values(wavefront.get_abscissas())))
            except IndexError:
                raise Exception("Unexpected Error during interpolation: try reduce Number of bins for I(Sagittal) histogram")

        wavefront.apply_ideal_lens(focallength_ff)

        if input_parameters.ghy_calcType == 3 or \
                (input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None):
           wavefront.add_phase_shifts(get_mirror_phase_shift(wavefront.get_abscissas(),
                                                             calculation_parameters.gwavelength,
                                                             calculation_parameters.wangle_x,
                                                             calculation_parameters.wl_x,
                                                             global_phase_shift_profile))
        elif input_parameters.ghy_calcType == 4:
           wavefront.add_phase_shifts(get_grating_phase_shift(wavefront.get_abscissas(),
                                                              calculation_parameters.gwavelength,
                                                              calculation_parameters.wangle_x,
                                                              calculation_parameters.wangle_ref_x,
                                                              calculation_parameters.wl_x,
                                                              global_phase_shift_profile))


        if do_nf: input_parameters.widget.set_progress_bar(35)
        else: input_parameters.widget.set_progress_bar(50)
        input_parameters.widget.status_message("calculated plane wave: begin FF propagation (distance = " +  str(focallength_ff) + ")")

        propagated_wavefront = propagator.propagate_1D_fresnel(wavefront, focallength_ff)

        if do_nf: input_parameters.widget.set_progress_bar(50)
        else: input_parameters.widget.set_progress_bar(70)
        input_parameters.widget.status_message("dif_xp: begin calculation")

        shadow_oe = calculation_parameters.shadow_oe_end

        imagesize = min(abs(calculation_parameters.ghy_x_max), abs(calculation_parameters.ghy_x_min)) * 2
        # 2017-01 Luca Rebuffi
        imagesize = min(imagesize,
                        input_parameters.ghy_npeak*2*0.88*calculation_parameters.gwavelength*focallength_ff/abs(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.Y_ROT==0:
            imagesize = max(imagesize, 8*(focallength_ff*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.Y_ROT))) + numpy.abs(shadow_oe._oe.OFFX)))

        imagenpts = int(round(imagesize / propagated_wavefront.delta() / 2) * 2 + 1)

        dif_xp = ScaledArray.initialize_from_range(numpy.ones(propagated_wavefront.size()),
                                                   -(imagenpts - 1) / 2 * propagated_wavefront.delta(),
                                                   (imagenpts - 1) / 2 * propagated_wavefront.delta())


        dif_xp.np_array = numpy.absolute(propagated_wavefront.get_interpolated_complex_amplitudes(dif_xp.scale))**2

        dif_xp.set_scale_from_range(-(imagenpts - 1) / 2 * propagated_wavefront.delta() / focallength_ff,
                                    (imagenpts - 1) / 2 * propagated_wavefront.delta() / focallength_ff)

        calculation_parameters.dif_xp = dif_xp

    if not do_nf: input_parameters.widget.set_progress_bar(80)

    # ------------------------------------------
    # near field calculation
    # ------------------------------------------
    if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:  # near field calculation
        focallength_nf = input_parameters.ghy_focallength

        fftsize = int(scale_factor * calculate_fft_size(calculation_parameters.ghy_x_min,
                                                        calculation_parameters.ghy_x_max,
                                                        calculation_parameters.gwavelength,
                                                        numpy.abs(focallength_nf),
                                                        input_parameters.ghy_fftnpts))

        input_parameters.widget.status_message("NF: creating plane wave begin, fftsize = " +  str(fftsize))
        input_parameters.widget.set_progress_bar(55)

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=scale_factor*calculation_parameters.ghy_x_min,
                                                                x_max=scale_factor*calculation_parameters.ghy_x_max)

        if scale_factor == 1.0:
            try:
                wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_x.interpolate_values(wavefront.get_abscissas())))
            except IndexError:
                raise Exception("Unexpected Error during interpolation: try reduce Number of bins for I(Sagittal) histogram")

        wavefront.apply_ideal_lens(focallength_nf)

        if input_parameters.ghy_calcType == 3 or \
                (input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None):
           wavefront.add_phase_shifts(get_mirror_phase_shift(wavefront.get_abscissas(),
                                                             calculation_parameters.gwavelength,
                                                             calculation_parameters.wangle_x,
                                                             calculation_parameters.wl_x,
                                                             global_phase_shift_profile))
        elif input_parameters.ghy_calcType == 4:
           wavefront.add_phase_shifts(get_grating_phase_shift(wavefront.get_abscissas(),
                                                              calculation_parameters.gwavelength,
                                                              calculation_parameters.wangle_x,
                                                              calculation_parameters.wangle_ref_x,
                                                              calculation_parameters.wl_x,
                                                              global_phase_shift_profile))

        input_parameters.widget.status_message("calculated plane wave: begin NF propagation (distance = " + str(input_parameters.ghy_distance) + ")")
        input_parameters.widget.set_progress_bar(60)

        propagated_wavefront = propagator.propagate_1D_fresnel(wavefront, input_parameters.ghy_distance)

        # ghy_npeak in the wavefront propagation image
        imagesize = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * numpy.abs(focallength_nf) / abs(calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min))
        imagesize = max(imagesize,
                        2 * abs((calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min) * (input_parameters.ghy_distance - numpy.abs(focallength_nf))) / numpy.abs(focallength_nf))

        if input_parameters.ghy_calcType == 3:
            imagesize = max(imagesize,
                            16 * rms_slope * numpy.abs(focallength_nf) * numpy.sin(average_incident_angle / 1e3))
        elif input_parameters.ghy_calcType == 4:
            imagesize = max(imagesize,
                            8 * rms_slope * numpy.abs(focallength_nf) * (numpy.sin(average_incident_angle / 1e3) + numpy.sin(average_reflection_angle / 1e3)))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.Y_ROT==0:
            imagesize = max(imagesize, 8*(input_parameters.ghy_distance*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.Y_ROT))) + numpy.abs(shadow_oe._oe.OFFX)))

        imagenpts = int(round(imagesize / propagated_wavefront.delta() / 2) * 2 + 1)

        input_parameters.widget.set_progress_bar(75)
        input_parameters.widget.status_message("dif_x: begin calculation")

        dif_x = ScaledArray.initialize_from_range(numpy.ones(imagenpts),
                                                  -(imagenpts - 1) / 2 * propagated_wavefront.delta(),
                                                  (imagenpts - 1) / 2 * propagated_wavefront.delta())

        dif_x.np_array *= numpy.absolute(propagated_wavefront.get_interpolated_complex_amplitudes(dif_x.scale))**2

        calculation_parameters.dif_x = dif_x

        input_parameters.widget.set_progress_bar(80)

##########################################################################
# 1D PROPAGATION ALGORITHM - Z DIRECTION
##########################################################################

def propagate_1D_z_direction(calculation_parameters, input_parameters):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    scale_factor = 1.0

    shadow_oe = calculation_parameters.shadow_oe_end

    global_phase_shift_profile = None

    if shadow_oe._oe.F_MOVE == 1 and shadow_oe._oe.X_ROT != 0.0:
        if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
            global_phase_shift_profile = calculation_parameters.w_mirror_lz
        elif input_parameters.ghy_calcType == 2:
            global_phase_shift_profile = ScaledArray.initialize_from_range(numpy.zeros(3), shadow_oe._oe.RLEN2, shadow_oe._oe.RLEN1)

        global_phase_shift_profile.set_values(global_phase_shift_profile.get_values() +
                                              global_phase_shift_profile.get_abscissas()*numpy.sin(numpy.radians(-shadow_oe._oe.X_ROT)))
    elif input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
        global_phase_shift_profile = calculation_parameters.w_mirror_lz

    if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
        rms_slope = hy_findrmsslopefromheight(global_phase_shift_profile)

        input_parameters.widget.status_message("Using RMS slope = " + str(rms_slope))

        if calculation_parameters.beam_not_cut_in_z:
            dp_image = numpy.std(calculation_parameters.zz_focal_ray)/input_parameters.ghy_focallength
            dp_se = 2 * rms_slope # different in x and z
            dp_error = calculation_parameters.gwavelength/2/(calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min)

            scale_factor = max(1, 5*min(dp_error/dp_image, dp_error/dp_se))

    # ------------------------------------------
    # far field calculation
    # ------------------------------------------
    if calculation_parameters.do_ff_z:
        focallength_ff = calculate_focal_length_ff(calculation_parameters.ghy_z_min,
                                                   calculation_parameters.ghy_z_max,
                                                   input_parameters.ghy_npeak,
                                                   calculation_parameters.gwavelength)

        if (input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4) and rms_slope != 0:
            focallength_ff = min(focallength_ff, (calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min) / 16 / rms_slope ) #xshi changed
        elif input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None:
            focallength_ff = min(focallength_ff, input_parameters.ghy_distance*4) #TODO: PATCH to be found with a formula

        fftsize = int(scale_factor * calculate_fft_size(calculation_parameters.ghy_z_min,
                                                        calculation_parameters.ghy_z_max,
                                                        calculation_parameters.gwavelength,
                                                        focallength_ff,
                                                        input_parameters.ghy_fftnpts))

        if do_nf: input_parameters.widget.set_progress_bar(27)
        else: input_parameters.widget.set_progress_bar(30)
        input_parameters.widget.status_message("FF: creating plane wave begin, fftsize = " +  str(fftsize))

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=scale_factor * calculation_parameters.ghy_z_min,
                                                                x_max=scale_factor * calculation_parameters.ghy_z_max)

        if scale_factor == 1.0:
            try:
                wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_z.interpolate_values(wavefront.get_abscissas())))
            except IndexError:
                raise Exception("Unexpected Error during interpolation: try reduce Number of bins for I(Tangential) histogram")

        wavefront.apply_ideal_lens(focallength_ff)

        if input_parameters.ghy_calcType == 3 or \
                (input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None):
           wavefront.add_phase_shifts(get_mirror_phase_shift(wavefront.get_abscissas(),
                                                             calculation_parameters.gwavelength,
                                                             calculation_parameters.wangle_z,
                                                             calculation_parameters.wl_z,
                                                             global_phase_shift_profile))
        elif input_parameters.ghy_calcType == 4:
           wavefront.add_phase_shifts(get_grating_phase_shift(wavefront.get_abscissas(),
                                                              calculation_parameters.gwavelength,
                                                              calculation_parameters.wangle_z,
                                                              calculation_parameters.wangle_ref_z,
                                                              calculation_parameters.wl_z,
                                                              global_phase_shift_profile))


        if do_nf: input_parameters.widget.set_progress_bar(35)
        else: input_parameters.widget.set_progress_bar(50)
        input_parameters.widget.status_message("calculated plane wave: begin FF propagation (distance = " +  str(focallength_ff) + ")")

        propagated_wavefront = propagator.propagate_1D_fresnel(wavefront, focallength_ff)

        if do_nf: input_parameters.widget.set_progress_bar(50)
        else: input_parameters.widget.set_progress_bar(70)
        input_parameters.widget.status_message("dif_zp: begin calculation")

        imagesize = min(abs(calculation_parameters.ghy_z_max), abs(calculation_parameters.ghy_z_min)) * 2
        # 2017-01 Luca Rebuffi
        imagesize = min(imagesize,
                        input_parameters.ghy_npeak*2*0.88*calculation_parameters.gwavelength*focallength_ff/abs(calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.X_ROT==0:
            imagesize = max(imagesize, 8*(focallength_ff*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.X_ROT))) + numpy.abs(shadow_oe._oe.OFFZ)))

        imagenpts = int(round(imagesize / propagated_wavefront.delta() / 2) * 2 + 1)

        dif_zp = ScaledArray.initialize_from_range(numpy.ones(propagated_wavefront.size()),
                                                   -(imagenpts - 1) / 2 * propagated_wavefront.delta(),
                                                   (imagenpts - 1) / 2 * propagated_wavefront.delta())

        dif_zp.np_array *= numpy.absolute(propagated_wavefront.get_interpolated_complex_amplitudes(dif_zp.scale))**2

        dif_zp.set_scale_from_range(-(imagenpts - 1) / 2 * propagated_wavefront.delta() / focallength_ff,
                                    (imagenpts - 1) / 2 * propagated_wavefront.delta() / focallength_ff)

        calculation_parameters.dif_zp = dif_zp

    if not do_nf: input_parameters.widget.set_progress_bar(80)

    # ------------------------------------------
    # near field calculation
    # ------------------------------------------
    if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
        focallength_nf = input_parameters.ghy_focallength

        fftsize = int(scale_factor * calculate_fft_size(calculation_parameters.ghy_z_min,
                                                        calculation_parameters.ghy_z_max,
                                                        calculation_parameters.gwavelength,
                                                        numpy.abs(focallength_nf),
                                                        input_parameters.ghy_fftnpts))

        input_parameters.widget.status_message("NF: creating plane wave begin, fftsize = " +  str(fftsize))
        input_parameters.widget.set_progress_bar(55)

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=scale_factor*calculation_parameters.ghy_z_min,
                                                                x_max=scale_factor*calculation_parameters.ghy_z_max)

        if scale_factor == 1.0:
            try:
                wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_z.interpolate_values(wavefront.get_abscissas())))
            except IndexError:
                raise Exception("Unexpected Error during interpolation: try reduce Number of bins for I(Tangential) histogram")

        wavefront.apply_ideal_lens(focallength_nf)

        if input_parameters.ghy_calcType == 3 or \
                (input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None):
           wavefront.add_phase_shifts(get_mirror_phase_shift(wavefront.get_abscissas(),
                                                             calculation_parameters.gwavelength,
                                                             calculation_parameters.wangle_z,
                                                             calculation_parameters.wl_z,
                                                             global_phase_shift_profile))
        elif input_parameters.ghy_calcType == 4:
           wavefront.add_phase_shifts(get_grating_phase_shift(wavefront.get_abscissas(),
                                                              calculation_parameters.gwavelength,
                                                              calculation_parameters.wangle_z,
                                                              calculation_parameters.wangle_ref_z,
                                                              calculation_parameters.wl_z,
                                                              global_phase_shift_profile))

        input_parameters.widget.status_message("calculated plane wave: begin NF propagation (distance = " + str(input_parameters.ghy_distance) + ")")
        input_parameters.widget.set_progress_bar(60)

        propagated_wavefront = propagator.propagate_1D_fresnel(wavefront, input_parameters.ghy_distance)

        # ghy_npeak in the wavefront propagation image
        imagesize = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * numpy.abs(focallength_nf) / abs(calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min))
        imagesize = max(imagesize,
                        2 * abs((calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min) * (input_parameters.ghy_distance - numpy.abs(focallength_nf))) / numpy.abs(focallength_nf))

        if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
            imagesize = max(imagesize, 16 * rms_slope * numpy.abs(focallength_nf))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.X_ROT==0:
            imagesize = max(imagesize, 8*(input_parameters.ghy_distance*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.X_ROT))) + numpy.abs(shadow_oe._oe.OFFZ)))

        imagenpts = int(round(imagesize / propagated_wavefront.delta() / 2) * 2 + 1)

        input_parameters.widget.set_progress_bar(75)
        input_parameters.widget.status_message("dif_z: begin calculation")

        dif_z = ScaledArray.initialize_from_range(numpy.ones(imagenpts),
                                                  -(imagenpts - 1) / 2 * propagated_wavefront.delta(),
                                                   (imagenpts - 1) / 2 * propagated_wavefront.delta())

        dif_z.np_array *= numpy.absolute(propagated_wavefront.get_interpolated_complex_amplitudes(dif_z.scale)**2)

        calculation_parameters.dif_z = dif_z

        input_parameters.widget.set_progress_bar(80)

##########################################################################
# 2D PROPAGATION ALGORITHM
##########################################################################

def getTransmittance(thickness, alpha, input_parameters):
    return numpy.exp(-alpha * thickness * input_parameters.widget.workspace_units_to_m * 100)

def getLinearAbsorptionCoefficient(chemical_formula, wavelength):
    mu = xraylib.CS_Total_CP(chemical_formula, ShadowPhysics.getEnergyFromWavelength(wavelength)/1000) # energy in KeV
    rho = ShadowPhysics.getMaterialDensity(chemical_formula)

    return mu*rho

#TODO: Implement 2D NF calculation

def propagate_2D(calculation_parameters, input_parameters):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    scale_factor_x = 1.0
    scale_factor_z = 1.0

    shadow_oe = calculation_parameters.shadow_oe_end

    if calculation_parameters.do_ff_z and calculation_parameters.do_ff_x:
        global_phase_shift_profile = None

        if shadow_oe._oe.F_MOVE == 1 and shadow_oe._oe.X_ROT != 0.0:
            if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
                global_phase_shift_profile = calculation_parameters.w_mirr_2D_values
            elif input_parameters.ghy_calcType == 2:
                global_phase_shift_profile = ScaledMatrix.initialize_from_range(numpy.zeros((3, 3)),
                                                                                shadow_oe._oe.RWIDX2, shadow_oe._oe.RWIDX1,
                                                                                shadow_oe._oe.RLEN2,  shadow_oe._oe.RLEN1)

            for x_index in range(global_phase_shift_profile.size_x()):
                global_phase_shift_profile.z_values[x_index, :] += global_phase_shift_profile.get_y_values()*numpy.sin(numpy.radians(-shadow_oe._oe.X_ROT))
        elif input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
            global_phase_shift_profile = calculation_parameters.w_mirr_2D_values

        # only tangential slopes
        if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
            rms_slope = hy_findrmsslopefromheight(ScaledArray(np_array=global_phase_shift_profile.z_values[int(global_phase_shift_profile.size_x()/2), :],
                                                              scale=global_phase_shift_profile.get_y_values()))

            input_parameters.widget.status_message("Using RMS slope = " + str(rms_slope))

            average_incident_angle = numpy.radians(90 - calculation_parameters.shadow_oe_end._oe.T_INCIDENCE) * 1e3
            average_reflection_angle = numpy.radians(90 - calculation_parameters.shadow_oe_end._oe.T_REFLECTION) * 1e3

            if calculation_parameters.beam_not_cut_in_x:
                dp_image = numpy.std(calculation_parameters.xx_focal_ray) / input_parameters.ghy_focallength
                dp_se = 2 * rms_slope * numpy.sin(average_incident_angle / 1e3)  # different in x and z
                dp_error = calculation_parameters.gwavelength / 2 / (calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min)

                scale_factor_x = max(1, 5 * min(dp_error / dp_image, dp_error / dp_se))

            if calculation_parameters.beam_not_cut_in_z:
                dp_image = numpy.std(calculation_parameters.zz_focal_ray) / input_parameters.ghy_focallength
                dp_se = 2 * rms_slope  # different in x and z
                dp_error = calculation_parameters.gwavelength / 2 / (calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min)

                scale_factor_z = max(1, 5 * min(dp_error / dp_image, dp_error / dp_se))

        # ------------------------------------------
        # far field calculation
        # ------------------------------------------
        focallength_ff = calculate_focal_length_ff_2D(calculation_parameters.ghy_x_min,
                                                      calculation_parameters.ghy_x_max,
                                                      calculation_parameters.ghy_z_min,
                                                      calculation_parameters.ghy_z_max,
                                                      input_parameters.ghy_npeak,
                                                      calculation_parameters.gwavelength)

        if (input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4) and rms_slope != 0:
            focallength_ff = min(focallength_ff,(calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min) / 16 / rms_slope ) #xshi changed
        elif input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None:
            focallength_ff = min(focallength_ff, input_parameters.ghy_distance*4) #TODO: PATCH to be found with a formula

        input_parameters.widget.status_message("FF: calculated focal length: " + str(focallength_ff))

        fftsize_x = int(scale_factor_x*calculate_fft_size(calculation_parameters.ghy_x_min,
                                                          calculation_parameters.ghy_x_max,
                                                          calculation_parameters.gwavelength,
                                                          focallength_ff,
                                                          input_parameters.ghy_fftnpts,
                                                          factor=20))

        fftsize_z = int(scale_factor_z*calculate_fft_size(calculation_parameters.ghy_z_min,
                                                          calculation_parameters.ghy_z_max,
                                                          calculation_parameters.gwavelength,
                                                          focallength_ff,
                                                          input_parameters.ghy_fftnpts,
                                                          factor=20))

        if do_nf: input_parameters.widget.set_progress_bar(27)
        else: input_parameters.widget.set_progress_bar(30)
        input_parameters.widget.status_message("FF: creating plane wave begin, fftsize_x = " +  str(fftsize_x) + ", fftsize_z = " +  str(fftsize_z))

        wavefront = Wavefront2D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=(fftsize_x, fftsize_z),
                                                                x_min=scale_factor_x * calculation_parameters.ghy_x_min,
                                                                x_max=scale_factor_x * calculation_parameters.ghy_x_max,
                                                                y_min=scale_factor_z * calculation_parameters.ghy_z_min,
                                                                y_max=scale_factor_z * calculation_parameters.ghy_z_max)

        if input_parameters.ghy_calcType in [6, 7]:
            alpha = getLinearAbsorptionCoefficient(input_parameters.absorber_material, calculation_parameters.gwavelength)

        try:
            for i in range(0, len(wavefront.electric_field_array.x_coord)):
                for j in range(0, len(wavefront.electric_field_array.y_coord)):
                    interpolated = calculation_parameters.wIray_2d.interpolate_value(wavefront.electric_field_array.x_coord[i],
                                                                                     wavefront.electric_field_array.y_coord[j])

                    if input_parameters.ghy_calcType in [6, 7]:
                        for w_mirr_2D_values in calculation_parameters.w_mirr_2D_values:
                            transmittance = getTransmittance(w_mirr_2D_values.interpolate_value(wavefront.electric_field_array.x_coord[i],
                                                                                                wavefront.electric_field_array.y_coord[j]),
                                                             alpha,
                                                             input_parameters)
                            interpolated *= transmittance

                    wavefront.electric_field_array.set_z_value(i, j, numpy.sqrt(0.0 if interpolated < 0 else interpolated))
        except IndexError:
            raise Exception("Unexpected Error during interpolation: try reduce Number of bins for I(Tangential) histogram")

        wavefront.apply_ideal_lens(focallength_ff, focallength_ff)

        shadow_oe = calculation_parameters.shadow_oe_end

        if input_parameters.ghy_calcType == 3 or \
                (input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None):
            input_parameters.widget.status_message("FF: calculating phase shift due to Height Error Profile")

            phase_shifts = numpy.zeros(wavefront.size())

            for index in range(0, phase_shifts.shape[0]):
                np_array = numpy.zeros(global_phase_shift_profile.shape()[1])
                for j in range(0, len(np_array)):
                    np_array[j] = global_phase_shift_profile.interpolate_value(wavefront.get_coordinate_x()[index], calculation_parameters.w_mirr_2D_values.get_y_value(j))

                global_phase_shift_profile_z = ScaledArray.initialize_from_steps(np_array,
                                                                                 global_phase_shift_profile.y_coord[0],
                                                                                 global_phase_shift_profile.y_coord[1] - global_phase_shift_profile.y_coord[0])

                phase_shifts[index, :] = get_mirror_phase_shift(wavefront.get_coordinate_y(),
                                                                calculation_parameters.gwavelength,
                                                                calculation_parameters.wangle_z,
                                                                calculation_parameters.wl_z,
                                                                global_phase_shift_profile_z)
            wavefront.add_phase_shifts(phase_shifts)
        elif input_parameters.ghy_calcType == 4:
            input_parameters.widget.status_message("FF: calculating phase shift due to Height Error Profile")

            phase_shifts = numpy.zeros(wavefront.size())

            for index in range(0, phase_shifts.shape[0]):
                global_phase_shift_profile_z = ScaledArray.initialize_from_steps(global_phase_shift_profile.z_values[index, :],
                                                                                 global_phase_shift_profile.y_coord[0],
                                                                                 global_phase_shift_profile.y_coord[1] - global_phase_shift_profile.y_coord[0])

                phase_shifts[index, :] = get_grating_phase_shift(wavefront.get_coordinate_y(),
                                                                 calculation_parameters.gwavelength,
                                                                 calculation_parameters.wangle_z,
                                                                 calculation_parameters.wangle_ref_z,
                                                                 calculation_parameters.wl_z,
                                                                 global_phase_shift_profile_z)
            wavefront.add_phase_shifts(phase_shifts)
        elif input_parameters.ghy_calcType in [6, 7]:
            for w_mirr_2D_values in calculation_parameters.w_mirr_2D_values:
                phase_shift = get_absorber_phase_shift(w_mirr_2D_values,
                                                       input_parameters,
                                                       calculation_parameters,
                                                       [wavefront.get_coordinate_x(), wavefront.get_coordinate_y()])

                wavefront.add_phase_shift(phase_shift)

        if do_nf: input_parameters.widget.set_progress_bar(35)
        else: input_parameters.widget.set_progress_bar(50)
        input_parameters.widget.status_message("calculated plane wave: begin FF propagation (distance = " +  str(focallength_ff) + ")")

        propagated_wavefront = propagator2D.propagate_2D_fresnel(wavefront, focallength_ff)

        if do_nf: input_parameters.widget.set_progress_bar(50)
        else: input_parameters.widget.set_progress_bar(70)
        input_parameters.widget.status_message("dif_xpzp: begin calculation")

        imagesize_x = min(abs(calculation_parameters.ghy_x_max), abs(calculation_parameters.ghy_x_min)) * 2
        imagesize_x = min(imagesize_x,
                          input_parameters.ghy_npeak*2*0.88*calculation_parameters.gwavelength*focallength_ff/abs(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.Y_ROT==0:
            imagesize_x = max(imagesize_x, 8*(focallength_ff*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.Y_ROT))) + numpy.abs(shadow_oe._oe.OFFX)))

        delta_x = propagated_wavefront.delta()[0]
        imagenpts_x = int(round(imagesize_x/delta_x/2) * 2 + 1)

        imagesize_z = min(abs(calculation_parameters.ghy_z_max), abs(calculation_parameters.ghy_z_min)) * 2
        imagesize_z = min(imagesize_z,
                          input_parameters.ghy_npeak*2*0.88*calculation_parameters.gwavelength*focallength_ff/abs(calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.X_ROT==0:
            imagesize_z = max(imagesize_z, 8*(focallength_ff*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.X_ROT))) + numpy.abs(shadow_oe._oe.OFFZ)))

        delta_z = propagated_wavefront.delta()[1]
        imagenpts_z = int(round(imagesize_z/delta_z/2) * 2 + 1)

        dif_xpzp = ScaledMatrix.initialize_from_range(numpy.ones((imagenpts_x, imagenpts_z)),
                                                      min_scale_value_x = -(imagenpts_x - 1) / 2 * delta_x,
                                                      max_scale_value_x =(imagenpts_x - 1) / 2 * delta_x,
                                                      min_scale_value_y = -(imagenpts_z - 1) / 2 * delta_z,
                                                      max_scale_value_y =(imagenpts_z - 1) / 2 * delta_z)

        for i in range(0, dif_xpzp.shape()[0]):
            for j in range(0, dif_xpzp.shape()[1]):
                dif_xpzp.set_z_value(i, j, numpy.absolute(propagated_wavefront.get_interpolated_complex_amplitude(
                                                               dif_xpzp.x_coord[i],
                                                               dif_xpzp.y_coord[j]))**2
                                                           )

        dif_xpzp.set_scale_from_range(0,
                                      -(imagenpts_x - 1) / 2 * delta_x / focallength_ff,
                                      (imagenpts_x - 1) / 2 * delta_x / focallength_ff)

        dif_xpzp.set_scale_from_range(1,
                                      -(imagenpts_z - 1) / 2 * delta_z / focallength_ff,
                                      (imagenpts_z - 1) / 2 * delta_z / focallength_ff)

        calculation_parameters.dif_xpzp = dif_xpzp

    if not do_nf: input_parameters.widget.set_progress_bar(80)

    # ------------------------------------------
    # near field calculation
    # ------------------------------------------
    if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
        focallength_nf = input_parameters.ghy_focallength

        fftsize_x = int(scale_factor_x * calculate_fft_size(calculation_parameters.ghy_x_min,
                                                            calculation_parameters.ghy_x_max,
                                                            calculation_parameters.gwavelength,
                                                            numpy.abs(focallength_nf),
                                                            input_parameters.ghy_fftnpts))

        fftsize_z = int(scale_factor_z * calculate_fft_size(calculation_parameters.ghy_z_min,
                                                            calculation_parameters.ghy_z_max,
                                                            calculation_parameters.gwavelength,
                                                            numpy.abs(focallength_nf),
                                                            input_parameters.ghy_fftnpts))

        input_parameters.widget.status_message("NF: creating plane wave begin, fftsize_x = " + str(fftsize_x) + ", fftsize_z = " +  str(fftsize_z))
        input_parameters.widget.set_progress_bar(55)

        wavefront = Wavefront2D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=(fftsize_x, fftsize_z),
                                                                x_min=scale_factor_x * calculation_parameters.ghy_x_min,
                                                                x_max=scale_factor_x * calculation_parameters.ghy_x_max,
                                                                y_min=scale_factor_z * calculation_parameters.ghy_z_min,
                                                                y_max=scale_factor_z * calculation_parameters.ghy_z_max)

        if input_parameters.ghy_calcType in [6, 7]:
            alpha = getLinearAbsorptionCoefficient(input_parameters.absorber_material, calculation_parameters.gwavelength)

        try:
            for i in range(0, len(wavefront.electric_field_array.x_coord)):
                for j in range(0, len(wavefront.electric_field_array.y_coord)):
                    interpolated = calculation_parameters.wIray_2d.interpolate_value(wavefront.electric_field_array.x_coord[i],
                                                                                     wavefront.electric_field_array.y_coord[j])

                    if input_parameters.ghy_calcType in [6, 7]:
                        for w_mirr_2D_values in calculation_parameters.w_mirr_2D_values:
                            transmittance = getTransmittance(w_mirr_2D_values.interpolate_value(wavefront.electric_field_array.x_coord[i],
                                                                                                wavefront.electric_field_array.y_coord[j]),
                                                             alpha,
                                                             input_parameters)
                            interpolated *= transmittance

                    wavefront.electric_field_array.set_z_value(i, j, numpy.sqrt(0.0 if interpolated < 0 else interpolated))
        except IndexError:
            raise Exception("Unexpected Error during interpolation: try reduce Number of bins for I(Tangential) histogram")

        wavefront.apply_ideal_lens(focallength_nf, focallength_nf)

        if input_parameters.ghy_calcType == 3 or \
                (input_parameters.ghy_calcType == 2 and not global_phase_shift_profile is None):
            input_parameters.widget.status_message("NF: calculating phase shift due to Height Error Profile")

            phase_shifts = numpy.zeros(wavefront.size())

            for index in range(0, phase_shifts.shape[0]):
                np_array = numpy.zeros(global_phase_shift_profile.shape()[1])
                for j in range(0, len(np_array)):
                    np_array[j] = global_phase_shift_profile.interpolate_value(wavefront.get_coordinate_x()[index], calculation_parameters.w_mirr_2D_values.get_y_value(j))

                global_phase_shift_profile_z = ScaledArray.initialize_from_steps(np_array,
                                                                                 global_phase_shift_profile.y_coord[0],
                                                                                 global_phase_shift_profile.y_coord[1] - global_phase_shift_profile.y_coord[0])

                phase_shifts[index, :] = get_mirror_phase_shift(wavefront.get_coordinate_y(),
                                                                calculation_parameters.gwavelength,
                                                                calculation_parameters.wangle_z,
                                                                calculation_parameters.wl_z,
                                                                global_phase_shift_profile_z)
            wavefront.add_phase_shifts(phase_shifts)
        elif input_parameters.ghy_calcType == 4:
            input_parameters.widget.status_message("NF: calculating phase shift due to Height Error Profile")

            phase_shifts = numpy.zeros(wavefront.size())

            for index in range(0, phase_shifts.shape[0]):
                global_phase_shift_profile_z = ScaledArray.initialize_from_steps(global_phase_shift_profile.z_values[index, :],
                                                                                 global_phase_shift_profile.y_coord[0],
                                                                                 global_phase_shift_profile.y_coord[1] - global_phase_shift_profile.y_coord[0])

                phase_shifts[index, :] = get_grating_phase_shift(wavefront.get_coordinate_y(),
                                                                 calculation_parameters.gwavelength,
                                                                 calculation_parameters.wangle_z,
                                                                 calculation_parameters.wangle_ref_z,
                                                                 calculation_parameters.wl_z,
                                                                 global_phase_shift_profile_z)
            wavefront.add_phase_shifts(phase_shifts)
        elif input_parameters.ghy_calcType in [6, 7]:
            for w_mirr_2D_values in calculation_parameters.w_mirr_2D_values:
                phase_shift = get_absorber_phase_shift(w_mirr_2D_values,
                                                       input_parameters,
                                                       calculation_parameters,
                                                       [wavefront.get_coordinate_x(), wavefront.get_coordinate_y()])

                wavefront.add_phase_shift(phase_shift)

        input_parameters.widget.status_message("calculated plane wave: begin NF propagation (distance = " +  str(focallength_nf) + ")")

        propagated_wavefront = propagator2D.propagate_2D_fresnel(wavefront, focallength_nf)

        if do_nf: input_parameters.widget.set_progress_bar(50)
        else: input_parameters.widget.set_progress_bar(70)

        # ghy_npeak in the wavefront propagation image
        delta_x = propagated_wavefront.delta()[0]
        imagesize_x = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * numpy.abs(focallength_nf) / abs(calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min))
        imagesize_x= max(imagesize_x,
                        2 * abs((calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min) * (input_parameters.ghy_distance - numpy.abs(focallength_nf))) / numpy.abs(focallength_nf))

        if input_parameters.ghy_calcType == 3:
            imagesize_x = max(imagesize_x,
                            16 * rms_slope * numpy.abs(focallength_nf) * numpy.sin(average_incident_angle / 1e3))
        elif input_parameters.ghy_calcType == 4:
            imagesize_x = max(imagesize_x,
                            8 * rms_slope * numpy.abs(focallength_nf) * (numpy.sin(average_incident_angle / 1e3) + numpy.sin(average_reflection_angle / 1e3)))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.Y_ROT==0:
            imagesize_x = max(imagesize_x, 8*(input_parameters.ghy_distance*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.Y_ROT))) + numpy.abs(shadow_oe._oe.OFFX)))

        imagenpts_x = int(round(imagesize_x / delta_x / 2) * 2 + 1)

        delta_z = propagated_wavefront.delta()[1]
        imagesize_z = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * numpy.abs(focallength_nf) / abs(calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min))
        imagesize_z = max(imagesize_z,
                        2 * abs((calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min) * (input_parameters.ghy_distance - numpy.abs(focallength_nf))) / numpy.abs(focallength_nf))

        if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
            imagesize_z = max(imagesize_z, 16 * rms_slope * numpy.abs(focallength_nf))

        # TODO: this is a patch: to be rewritten
        if shadow_oe._oe.F_MOVE==1 and not shadow_oe._oe.X_ROT==0:
            imagesize_z = max(imagesize_z, 8*(input_parameters.ghy_distance*numpy.tan(numpy.radians(numpy.abs(shadow_oe._oe.X_ROT))) + numpy.abs(shadow_oe._oe.OFFZ)))

        imagenpts_z = int(round(imagesize_z / delta_z / 2) * 2 + 1)

        input_parameters.widget.status_message("dif_xz: begin calculation")

        dif_xz = ScaledMatrix.initialize_from_range(numpy.ones((imagenpts_x, imagenpts_z)),
                                                    min_scale_value_x = -(imagenpts_x - 1) / 2 * delta_x,
                                                    max_scale_value_x =(imagenpts_x - 1) / 2 * delta_x,
                                                    min_scale_value_y = -(imagenpts_z - 1) / 2 * delta_z,
                                                    max_scale_value_y =(imagenpts_z - 1) / 2 * delta_z)

        for i in range(0, dif_xz.shape()[0]):
            for j in range(0, dif_xz.shape()[1]):
                dif_xz.set_z_value(i, j, numpy.absolute(propagated_wavefront.get_interpolated_complex_amplitude(dif_xz.x_coord[i], dif_xz.y_coord[j]))**2)

        calculation_parameters.dif_xz = dif_xz

        input_parameters.widget.set_progress_bar(80)

#########################################################
#
# UTILITIES
#
#########################################################

def sh_read_gfile(gfilename):
    return ShadowOpticalElement.create_oe_from_file(congruence.checkFile(gfilename))


def get_delta(input_parameters, calculation_parameters):
    density = xraylib.ElementDensity(xraylib.SymbolToAtomicNumber(input_parameters.absorber_material))

    energy_in_KeV = ShadowPhysics.getEnergyFromWavelength(calculation_parameters.gwavelength*input_parameters.widget.workspace_units_to_m*1e10)/1000
    delta = 1-xraylib.Refractive_Index_Re(input_parameters.absorber_material, energy_in_KeV, density)

    return delta

#########################################################

def read_shadow_beam(shadow_beam, lost=False):
    cursor_go = numpy.where(shadow_beam._beam.rays[:, 9] == 1)

    image_beam_rays = copy.deepcopy(shadow_beam._beam.rays[cursor_go])
    image_beam_rays[:, 11] = numpy.arange(1, len(image_beam_rays) + 1, 1)

    out_beam_go = ShadowBeam()
    out_beam_go._beam.rays = image_beam_rays

    if lost:
        cursor_lo = numpy.where(shadow_beam._beam.rays[:, 9] != 1)

        lost_rays = copy.deepcopy(shadow_beam._beam.rays[cursor_lo])
        lost_rays[:, 11] = numpy.arange(1, len(lost_rays) + 1, 1)

        out_beam_lo = ShadowBeam()
        out_beam_lo._beam.rays = lost_rays

        return out_beam_go, out_beam_lo
    else:
        return out_beam_go

#########################################################

def sh_readsh(shfilename):
    image_beam = ShadowBeam()
    image_beam.loadFromFile(congruence.checkFile(shfilename))

    return read_shadow_beam(image_beam)

#########################################################

def sh_readangle(filename, mirror_beam=None):
    values = numpy.loadtxt(congruence.checkFile(filename))
    dimension = len(mirror_beam._beam.rays)

    angle_inc = numpy.zeros(dimension)
    angle_ref = numpy.zeros(dimension)

    ray_index = 0
    for index in range(0, len(values)):
        if values[index, 3] == 1:
            angle_inc[ray_index] = values[index, 1]
            angle_ref[ray_index] = values[index, 2]

            ray_index += 1

    return angle_inc, angle_ref

#########################################################

def sh_readsurface(filename, dimension):
    if dimension == 1:
        values = numpy.loadtxt(congruence.checkFile(filename))

        return ScaledArray(values[:, 1], values[:, 0])
    elif dimension == 2:
        x_coords, y_coords, z_values = ShadowPreProcessor.read_surface_error_file(filename)

        return ScaledMatrix(x_coords, y_coords, z_values)

def h5_readsurface(filename):
    x_coords, y_coords, z_values = OU.read_surface_file(filename)

    return ScaledMatrix(x_coords, y_coords, z_values.T)


#########################################################

def calculate_function_average_value(function, x_min, x_max, sampling=100):
    sampled_function = ScaledArray.initialize_from_range(numpy.zeros(sampling), x_min, x_max)
    sampled_function.np_array = function(sampled_function.scale)

    return numpy.average(sampled_function.np_array)

#########################################################

def hy_findrmsslopefromheight(wmirror_l):
    array_first_derivative = numpy.gradient(wmirror_l.np_array, wmirror_l.delta())

    return hy_findrmserror(ScaledArray(array_first_derivative, wmirror_l.scale))

#########################################################

def hy_findrmserror(data):
    wfftcol = numpy.absolute(numpy.fft.fft(data.np_array))

    waPSD = (2 * data.delta() * wfftcol[0:int(len(wfftcol)/2)]**2)/data.size() # uniformed with IGOR, FFT is not simmetric around 0
    waPSD[0] /= 2
    waPSD[len(waPSD)-1] /= 2

    fft_scale = numpy.fft.fftfreq(data.size())/data.delta()

    waRMS = numpy.trapz(waPSD, fft_scale[0:int(len(wfftcol)/2)]) # uniformed with IGOR: Same kind of integration, with automatic range assignement

    return numpy.sqrt(waRMS)

#########################################################

# 1D
def calculate_focal_length_ff(min_value, max_value, n_peaks, wavelength):
#    return (min(abs(max_value), abs(min_value))*2)**2/n_peaks/2/0.88/wavelength  #xshi used for now, but will have problem when the aperture is off center
    return (max_value - min_value)**2/n_peaks/2/0.88/wavelength  #xshi suggested, but need to first fix the problem of getting the fake solution of mirror aperture by SHADOW.

def calculate_focal_length_ff_2D(min_x_value, max_x_value, min_z_value, max_z_value, n_peaks, wavelength):
    return (min((max_z_value - min_z_value), (max_x_value - min_x_value)))**2/n_peaks/2/0.88/wavelength

def calculate_fft_size(min_value, max_value, wavelength, propagation_distance, fft_npts, factor=100):
    return int(min(factor * (max_value - min_value) ** 2 / wavelength / propagation_distance / 0.88, fft_npts))

def get_mirror_phase_shift(abscissas,
                           wavelength,
                           w_angle_function,
                           w_l_function,
                           mirror_profile):
    return (-1.0) * 4 * numpy.pi / wavelength * numpy.sin(w_angle_function(abscissas)/1e3) * mirror_profile.interpolate_values(w_l_function(abscissas))

def get_grating_phase_shift(abscissas,
                            wavelength,
                            w_angle_function,
                            w_angle_ref_function,
                            w_l_function,
                            grating_profile):
    return (-1.0) * 2 * numpy.pi / wavelength * (numpy.sin(w_angle_function(abscissas)/1e3) + numpy.sin(w_angle_ref_function(abscissas)/1e3)) * grating_profile.interpolate_values(w_l_function(abscissas))


def get_absorber_phase_shift(thickness_error_profile, input_parameters, calculation_parameters, coordinates):
    coord_x = thickness_error_profile.x_coord
    coord_y = thickness_error_profile.y_coord
    thickness_error = thickness_error_profile.z_values

    interpolator = RectBivariateSpline(coord_x, coord_y, thickness_error, bbox=[None, None, None, None], kx=1, ky=1, s=0)

    wavefront_coord_x = coordinates[0]
    wavefront_coord_y = coordinates[1]

    thickness_error = interpolator(wavefront_coord_x, wavefront_coord_y)
    thickness_error[numpy.where(thickness_error==numpy.nan)] = 0.0
    thickness_error *= input_parameters.absorber_scaling_factor

    return -2 * numpy.pi * calculation_parameters.absorber_delta * thickness_error / calculation_parameters.gwavelength


def showConfirmMessage(title, message):
    msgBox = QMessageBox()
    msgBox.setFixedWidth(500)
    msgBox.setIcon(QMessageBox.Question)
    msgBox.setText(title)
    msgBox.setInformativeText(message)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    return msgBox.exec_()
