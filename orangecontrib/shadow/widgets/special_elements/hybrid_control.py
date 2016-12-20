import copy
import os
import random
import sys
import numpy

from PyQt4.QtGui import QMessageBox

from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowSource, ShadowOpticalElement, ShadowCompoundOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowPhysics, ShadowPreProcessor

from srxraylib.util.data_structures import ScaledArray, ScaledMatrix
from srxraylib.waveoptics.wavefront import Wavefront1D
from srxraylib.waveoptics import propagator

'''
Diffraction Plane
ghy_diff_plane = 1 : X
ghy_diff_plane = 2 : Z
ghy_diff_plane = 3 : X+Z

ghy_nf = 1 generate near-field profile

'''
class HybridNotNecessaryWarning(Exception):
    def __init__(self, *args, **kwargs):
        pass

class HybridInputParameters(object):
    widget=None

    shadow_beam = ShadowBeam()

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
    ff_beam = None
    nf_beam = None

    screen_plane_beam = None

    # Star
    xx_star = None
    zz_star = None

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

    # Mirror Surface
    w_mirr_1D_values = None
    w_mirr_2D_values = None

    # Mirror Fitted Functions
    wangle_x = None
    wangle_z = None
    wl_x     = None
    wl_z     = None

    xx_focal_ray = None
    zz_focal_ray = None

    w_mirror_lx = None
    w_mirror_lz = None

    wIray_x = None
    wIray_z = None
    wIray_2d = None

    # Propagation output
    dif_xp = None
    dif_zp = None
    dif_x = None
    dif_z = None

    # Conversion Output
    dx_conv = None
    dz_conv = None
    xx_image_ff = None
    zz_image_ff = None
    xx_image_nf = None
    zz_image_nf = None

##########################################################################

def hy_run(input_parameters=HybridInputParameters()):
    calculation_parameters=HybridCalculationParameters()

    try:
        hy_check_congruence(input_parameters, calculation_parameters)

        input_parameters.widget.status_message("Starting HYBRID calculation")
        input_parameters.widget.set_progress_bar(0)

        hy_readfiles(input_parameters, calculation_parameters)	#Read shadow output files needed by HYBRID

        input_parameters.widget.status_message("Analysis of Input Beam and OE completed")
        input_parameters.widget.set_progress_bar(10)

        if input_parameters.ghy_diff_plane == 3:
            # FIRST: X DIRECTION
            input_parameters.ghy_diff_plane = 1

            hy_init(input_parameters, calculation_parameters)		#Calculate functions needed to construct exit pupil function

            input_parameters.widget.status_message("X: Initialization completed")
            input_parameters.widget.set_progress_bar(10)

            input_parameters.widget.status_message("X: Start Wavefront Propagation")
            hy_prop(input_parameters, calculation_parameters)	    #Perform wavefront propagation

            input_parameters.widget.status_message("X: Start Ray Resampling")
            input_parameters.widget.set_progress_bar(40)

            hy_conv(input_parameters, calculation_parameters)	    #Perform ray resampling

            input_parameters.widget.status_message("X: Creating Output Shadow Beam")

            hy_create_shadow_beam(input_parameters, calculation_parameters)

            # SECOND: Z DIRECTION
            input_parameters.ghy_diff_plane = 2
            input_parameters.shadow_beam = calculation_parameters.ff_beam

            hy_init(input_parameters, calculation_parameters)		#Calculate functions needed to construct exit pupil function

            input_parameters.widget.status_message("Z: Initialization completed")
            input_parameters.widget.set_progress_bar(50)

            input_parameters.widget.status_message("Z: Start Wavefront Propagation")
            hy_prop(input_parameters, calculation_parameters)	    #Perform wavefront propagation

            input_parameters.widget.status_message("Z: Start Ray Resampling")
            input_parameters.widget.set_progress_bar(80)

            hy_conv(input_parameters, calculation_parameters)	    #Perform ray resampling

            input_parameters.widget.status_message("Z: Creating Output Shadow Beam")

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

    if input_parameters.ghy_calcType == 2 or input_parameters.ghy_calcType == 3:
        if not "Mirror" in widget_class_name:
            raise Exception("Mirror calculation runs for Mirror widgets only")

    if input_parameters.ghy_calcType == 4:
        if not ("Lens" in widget_class_name or "CRL" in widget_class_name):
            raise Exception("CRL calculation runs for Lens or CRL widgets only")

    #TODO: DO SEPARATE ANALYSIS OF THE SITUATION IN H and V, BY USING RAY-TRACING AND HISTOS
    if input_parameters.ghy_n_oe < 0:
        beam_before = history_entry._input_beam.duplicate()
        oe_before = history_entry._shadow_oe_start.duplicate()

        number_of_good_rays_before =  len(beam_before._beam.rays[numpy.where(beam_before._beam.rays[:, 9] == 1)])
        number_of_good_rays_after = len(beam_after._beam.rays[numpy.where(beam_after._beam.rays[:, 9] == 1)])

        if number_of_good_rays_before == number_of_good_rays_after:
            calculation_parameters.beam_not_cut_in_x = True
            calculation_parameters.beam_not_cut_in_z = True

            if input_parameters.ghy_calcType != 3:
                calculation_parameters.ff_beam = input_parameters.shadow_beam

                raise HybridNotNecessaryWarning("O.E. contains the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")
        else:
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

            elif input_parameters.ghy_calcType == 2 or input_parameters.ghy_calcType == 3: # MIRRORS
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

            elif input_parameters.ghy_calcType == 4: # CRL
                first_oe = history_entry._shadow_oe_end._oe.list[0]

                if first_oe.FHIT_C == 0: #infinite
                    is_infinite = True
                else:
                    beam_at_the_slit = beam_before.duplicate(history=False)
                    beam_at_the_slit._beam.retrace(first_oe.T_SOURCE) # TRACE INCIDENT BEAM UP TO THE SLIT

                    max_tangential = numpy.abs(first_oe.RLEN2)
                    min_tangential = -numpy.abs(first_oe.RLEN2)
                    max_sagittal = numpy.abs(first_oe.RWIDX2)
                    min_sagittal = -numpy.abs(first_oe.RWIDX2)

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

                #print("T", calculation_parameters.beam_not_cut_in_z)
                #print("T", min_tangential, max_tangential, min(coordinate_tangential), max(coordinate_tangential))
                #print("T", intensity_tangential_cut, numpy.sum(intensity_tangential[cursor_up]), numpy.sum(intensity_tangential[cursor_down]))
                #print("S", calculation_parameters.beam_not_cut_in_x)
                #print("S", min_sagittal, max_sagittal, min(coordinate_sagittal), max(coordinate_sagittal))
                #print("S", intensity_sagittal_cut, numpy.sum(intensity_sagittal[cursor_up]), numpy.sum(intensity_sagittal[cursor_down]))

            # REQUEST FILTERING OR REFUSING

            if not input_parameters.ghy_calcType == 3:
                if input_parameters.ghy_diff_plane == 1 and calculation_parameters.beam_not_cut_in_x:
                    calculation_parameters.ff_beam = input_parameters.shadow_beam

                    raise HybridNotNecessaryWarning("O.E. contains almost the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")
                elif input_parameters.ghy_diff_plane == 2 and calculation_parameters.beam_not_cut_in_z:
                    calculation_parameters.ff_beam = input_parameters.shadow_beam

                    raise HybridNotNecessaryWarning("O.E. contains almost the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")
                elif input_parameters.ghy_diff_plane == 3: # BOTH
                    if calculation_parameters.beam_not_cut_in_x and calculation_parameters.beam_not_cut_in_z:
                        calculation_parameters.ff_beam = input_parameters.shadow_beam

                        raise HybridNotNecessaryWarning("O.E. contains almost the whole beam, diffraction effects are not expected:\nCalculation aborted, beam remains unaltered")
                    else: # REMOVE UNUSEFUL CALCULATION
                        if calculation_parameters.beam_not_cut_in_x:
                            input_parameters.ghy_diff_plane == 2
                        elif calculation_parameters.beam_not_cut_in_z:
                            input_parameters.ghy_diff_plane == 1


##########################################################################

def hy_readfiles(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    if input_parameters.ghy_calcType == 4: #CRL OR LENS
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
        input_parameters.ghy_calcType = 1


    str_n_oe = str(input_parameters.shadow_beam._oe_number)

    if input_parameters.shadow_beam._oe_number < 10:
        str_n_oe = "0" + str_n_oe

    fileShadowScreen = "screen." + str_n_oe + "01"

    # Before ray-tracing save the original history:

    calculation_parameters.original_beam_history = input_parameters.shadow_beam.getOEHistory()

    history_entry =  input_parameters.shadow_beam.getOEHistory(input_parameters.shadow_beam._oe_number)

    shadow_oe = history_entry._shadow_oe_start.duplicate() # no changes to the original object!
    shadow_oe_input_beam = history_entry._input_beam.duplicate(history=False)

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

    if input_parameters.ghy_calcType == 1: # simple aperture
        if (shadow_oe._oe.FMIRR == 5 and \
            shadow_oe._oe.F_CRYSTAL == 0 and \
            shadow_oe._oe.F_REFRAC == 2 and \
            shadow_oe._oe.F_SCREEN==1 and \
            shadow_oe._oe.N_SCREEN==1):

            i_abs[0] = shadow_oe._oe.I_ABS[0]
            i_slit[0] = shadow_oe._oe.I_SLIT[0]

            if shadow_oe._oe.I_SLIT[0] == 1:
                i_stop[0] = shadow_oe._oe.I_STOP[0]
                k_slit[0] = shadow_oe._oe.K_SLIT[0]

                if shadow_oe._oe.K_SLIT[0] == 2:
                    file_scr_ext[0] = shadow_oe._oe.FILE_SCR_EXT[0]
                else:
                    rx_slit[0] = shadow_oe._oe.RX_SLIT[0]
                    rz_slit[0] = shadow_oe._oe.RZ_SLIT[0]
                    cx_slit[0] = shadow_oe._oe.CX_SLIT[0]
                    cz_slit[0] = shadow_oe._oe.CZ_SLIT[0]

            if shadow_oe._oe.I_ABS[0] == 1:
                thick[0] = shadow_oe._oe.THICK[0]
                file_abs[0] = shadow_oe._oe.FILE_ABS[0]
        else:
            raise Exception("Connected O.E. is not a Screen-Slit widget!")
    elif input_parameters.ghy_calcType == 2: # ADDED BY XIANBO SHI
        shadow_oe._oe.F_RIPPLE = 0
    elif input_parameters.ghy_calcType == 3: # mirror + figure error
        if shadow_oe._oe.F_RIPPLE == 1 and shadow_oe._oe.F_G_S == 2:
            input_parameters.ghy_mirrorfile = shadow_oe._oe.FILE_RIP

            # disable slope error calculation for OE, must be done by HYBRID!
            shadow_oe._oe.F_RIPPLE = 0
        else:
            raise Exception("O.E. has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")

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

    input_parameters.shadow_beam = shadow_beam_at_image_plane

    image_beam = read_shadow_beam(shadow_beam_at_image_plane) #xshi change from 0 to 1

    calculation_parameters.shadow_oe_end = shadow_oe

    if input_parameters.file_to_write_out == 1:
        image_beam.writeToFile("hybrid_beam_at_image_plane." + str_n_oe)

    calculation_parameters.image_plane_beam = image_beam

    calculation_parameters.xx_star = image_beam._beam.rays[:, 0]
    calculation_parameters.zz_star = image_beam._beam.rays[:, 2]

    # read shadow screen file
    screen_beam = sh_readsh(fileShadowScreen)    #xshi change from 0 to 1

    if input_parameters.file_to_write_out == 1:
        screen_beam.writeToFile("hybrid_beam_at_oe_hybrid_screen." + str_n_oe)

    calculation_parameters.screen_plane_beam = screen_beam

    calculation_parameters.wenergy     = ShadowPhysics.getEnergyFromShadowK(screen_beam._beam.rays[:, 10])
    calculation_parameters.wwavelength = ShadowPhysics.getWavelengthfromShadowK(screen_beam._beam.rays[:, 10])
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

    # Process mirror
	# reads file with mirror height mesh
 	# calculates the function of the "incident angle" and the "mirror height" versus the Z coordinate in the screen.

    if input_parameters.ghy_calcType == 3:
        mirror_beam = sh_readsh("mirr." + str_n_oe)  #xshi change from 0 to 1

        if input_parameters.file_to_write_out == 1:
            mirror_beam.writeToFile("hybrid_footprint_on_oe." + str_n_oe)

        calculation_parameters.xx_mirr = mirror_beam._beam.rays[:, 0]
        calculation_parameters.yy_mirr = mirror_beam._beam.rays[:, 1]
        calculation_parameters.zz_mirr = mirror_beam._beam.rays[:, 2]

        # read in angle files

        angle_inc, angle_ref = sh_readangle("angle." + str_n_oe, mirror_beam)   #xshi change from 0 to 1

        calculation_parameters.angle_inc = (90.0 - angle_inc)/180.0*1e3*numpy.pi

        calculation_parameters.w_mirr_2D_values = sh_readsurface(input_parameters.ghy_mirrorfile, dimension=2)

        # generate theta(z) and l(z) curve over a continuous grid

        hy_npoly_angle = 3
        hy_npoly_l = 6

        if numpy.amax(calculation_parameters.xx_screen) == numpy.amin(calculation_parameters.xx_screen):
            if input_parameters.ghy_diff_plane == 1 or input_parameters.ghy_diff_plane == 3: raise Exception("Unconsistend calculation: Diffraction plane is set on X, but the beam has no extention in that direction")
        else:
            calculation_parameters.wangle_x = numpy.poly1d(numpy.polyfit(calculation_parameters.xx_screen, calculation_parameters.angle_inc, hy_npoly_angle))
            calculation_parameters.wl_x     = numpy.poly1d(numpy.polyfit(calculation_parameters.xx_screen, calculation_parameters.xx_mirr, hy_npoly_l))

        if numpy.amax(calculation_parameters.zz_screen) == numpy.amin(calculation_parameters.zz_screen):
            if input_parameters.ghy_diff_plane == 2 or input_parameters.ghy_diff_plane == 3: raise Exception("Unconsistend calculation: Diffraction plane is set on Z, but the beam has no extention in that direction")
        else:

            calculation_parameters.wangle_z = numpy.poly1d(numpy.polyfit(calculation_parameters.zz_screen, calculation_parameters.angle_inc, hy_npoly_angle))
            calculation_parameters.wl_z     = numpy.poly1d(numpy.polyfit(calculation_parameters.zz_screen, calculation_parameters.yy_mirr, hy_npoly_l))

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

    if input_parameters.ghy_diff_plane == 1:
        calculation_parameters.xx_focal_ray = copy.deepcopy(calculation_parameters.xx_screen) + \
                                              input_parameters.ghy_focallength * numpy.tan(calculation_parameters.dx_ray)
    elif input_parameters.ghy_diff_plane == 2:
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

    if input_parameters.ghy_calcType == 3: #mirror with figure error
        if input_parameters.ghy_diff_plane == 1: #X
            np_array = calculation_parameters.w_mirr_2D_values.z_values[:, round(len(calculation_parameters.w_mirr_2D_values.y_coord)/2)]

            calculation_parameters.w_mirror_lx = ScaledArray.initialize_from_steps(np_array,
                                                                                   calculation_parameters.w_mirr_2D_values.x_coord[0],
                                                                                   calculation_parameters.w_mirr_2D_values.x_coord[1] - calculation_parameters.w_mirr_2D_values.x_coord[0])
        elif input_parameters.ghy_diff_plane == 2: #Z
            np_array = calculation_parameters.w_mirr_2D_values.z_values[round(len(calculation_parameters.w_mirr_2D_values.x_coord)/2), :]

            calculation_parameters.w_mirror_lz = ScaledArray.initialize_from_steps(np_array,
                                                                                   calculation_parameters.w_mirr_2D_values.y_coord[0],
                                                                                   calculation_parameters.w_mirr_2D_values.y_coord[1] - calculation_parameters.w_mirr_2D_values.y_coord[0])

    # generate intensity profile (histogram): I_ray(z) curve

    if input_parameters.ghy_diff_plane == 1: # 1d in X
        if (input_parameters.ghy_nbins_x < 0):
            input_parameters.ghy_nbins_x = 200

        input_parameters.ghy_nbins_x = min(input_parameters.ghy_nbins_x, round(len(calculation_parameters.xx_screen) / 20)) #xshi change from 100 to 20

        ticket = calculation_parameters.screen_plane_beam._beam.histo1(1,
                                                                       nbins=input_parameters.ghy_nbins_x,
                                                                       xrange=[numpy.min(calculation_parameters.xx_screen), numpy.max(calculation_parameters.xx_screen)],
                                                                       nolost=1,
                                                                       ref=23)

        bins = ticket['bins']

        calculation_parameters.wIray_x = ScaledArray.initialize_from_range(ticket['histogram'], bins[0], bins[len(bins)-1])
    elif input_parameters.ghy_diff_plane == 2: # 1d in Z
        if (input_parameters.ghy_nbins_z < 0):
            input_parameters.ghy_nbins_z = 200

        input_parameters.ghy_nbins_z = min(input_parameters.ghy_nbins_z, round(len(calculation_parameters.zz_screen) / 20)) #xshi change from 100 to 20

        ticket = calculation_parameters.screen_plane_beam._beam.histo1(3,
                                                                       nbins=input_parameters.ghy_nbins_z,
                                                                       xrange=[numpy.min(calculation_parameters.zz_screen), numpy.max(calculation_parameters.zz_screen)],
                                                                       nolost=1,
                                                                       ref=23)

        bins = ticket['bins']

        calculation_parameters.wIray_z = ScaledArray.initialize_from_range(ticket['histogram'], bins[0], bins[len(bins)-1])

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

##########################################################################

def hy_prop(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):

    # set distance and focal length for the aperture propagation.
    if input_parameters.ghy_calcType == 1: # simple aperture
        if input_parameters.ghy_diff_plane == 1: # X
            calculation_parameters.ghy_focallength = (calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min)**2/calculation_parameters.gwavelength/input_parameters.ghy_npeak
        elif input_parameters.ghy_diff_plane == 2: # Z
            calculation_parameters.ghy_focallength = (calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min)**2/calculation_parameters.gwavelength/input_parameters.ghy_npeak

        input_parameters.widget.status_message("Focal length set to: " + str(calculation_parameters.ghy_focallength))

    # automatic control of number of peaks to avoid numerical overflow
    if input_parameters.ghy_npeak < 0: # number of bins control
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

def hy_conv(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        mDist = hy_CreateCDF1D(calculation_parameters.dif_xp)		#create cumulative distribution function from the angular diffraction profile
        pos_dif = hy_MakeDist1D(calculation_parameters.xp_screen, mDist)	#generate random ray divergence kicks based on the CDF, the number of rays is the same as in the original shadow file

        dx_wave = numpy.arctan(pos_dif) # calculate dx from tan(dx)
        dx_conv = dx_wave + calculation_parameters.dx_ray # add the ray divergence kicks

        calculation_parameters.xx_image_ff = calculation_parameters.xx_screen + input_parameters.ghy_distance*numpy.tan(dx_conv) # ray tracing to the image plane
        calculation_parameters.dx_conv = dx_conv

        if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
            mDist = hy_CreateCDF1D(calculation_parameters.dif_x)
            pos_dif = hy_MakeDist1D(calculation_parameters.xx_focal_ray, mDist)

            calculation_parameters.xx_image_nf = pos_dif + calculation_parameters.xx_focal_ray
    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        mDist = hy_CreateCDF1D(calculation_parameters.dif_zp)		#create cumulative distribution function from the angular diffraction profile
        pos_dif = hy_MakeDist1D(calculation_parameters.zp_screen, mDist)	#generate random ray divergence kicks based on the CDF, the number of rays is the same as in the original shadow file

        dz_wave = numpy.arctan(pos_dif) # calculate dz from tan(dz)
        dz_conv = dz_wave + calculation_parameters.dz_ray # add the ray divergence kicks

        calculation_parameters.zz_image_ff = calculation_parameters.zz_screen + input_parameters.ghy_distance*numpy.tan(dz_conv) # ray tracing to the image plane
        calculation_parameters.dz_conv = dz_conv

        if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
            mDist = hy_CreateCDF1D(calculation_parameters.dif_z)
            pos_dif = hy_MakeDist1D(calculation_parameters.zz_focal_ray, mDist)

            calculation_parameters.zz_image_nf = pos_dif + calculation_parameters.zz_focal_ray

#########################################################################

def hy_create_shadow_beam(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    calculation_parameters.ff_beam = calculation_parameters.image_plane_beam.duplicate(history=False)
    calculation_parameters.ff_beam._oe_number = input_parameters.shadow_beam._oe_number

    if do_nf:
        calculation_parameters.nf_beam = calculation_parameters.screen_plane_beam.duplicate(history=False)
        calculation_parameters.nf_beam._oe_number = input_parameters.shadow_beam._oe_number

    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        angle_perpen = numpy.arctan(calculation_parameters.zp_screen/calculation_parameters.yp_screen)
        angle_num = numpy.sqrt(1+(numpy.tan(angle_perpen))**2+(numpy.tan(calculation_parameters.dx_conv))**2)

        calculation_parameters.ff_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_ff)
        calculation_parameters.ff_beam._beam.rays[:, 3] = numpy.tan(calculation_parameters.dx_conv)/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 4] = 1/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 5] = numpy.tan(angle_perpen)/angle_num

        if do_nf: calculation_parameters.nf_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_nf)

    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        angle_perpen = numpy.arctan(calculation_parameters.xp_screen/calculation_parameters.yp_screen)
        angle_num = numpy.sqrt(1+(numpy.tan(angle_perpen))**2+(numpy.tan(calculation_parameters.dz_conv))**2)

        calculation_parameters.ff_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_ff)
        calculation_parameters.ff_beam._beam.rays[:, 3] = numpy.tan(angle_perpen)/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 4] = 1/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 5] = numpy.tan(calculation_parameters.dz_conv)/angle_num

        if do_nf: calculation_parameters.nf_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_nf)

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

##########################################################################
# 1D PROPAGATION ALGORITHM - X DIRECTION
##########################################################################

def propagate_1D_x_direction(calculation_parameters, input_parameters):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    scale_factor = 1.0

    if input_parameters.ghy_calcType == 3:
        rms_slope = hy_findrmsslopefromheight(calculation_parameters.w_mirror_lx)

        input_parameters.widget.status_message("Using RMS slope = " + str(rms_slope))

        average_incident_angle = numpy.radians(calculation_parameters.shadow_oe_end._oe.T_INCIDENCE)*1e3

        if calculation_parameters.beam_not_cut_in_x:
            dp_image = numpy.std(calculation_parameters.xx_focal_ray)/input_parameters.ghy_focallength
            dp_se = 2 * rms_slope * numpy.sin(average_incident_angle/1e3)	# different in x and z
            dp_error = calculation_parameters.gwavelength/2/(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min)

            scale_factor = max(1, 5*min(dp_error/dp_image, dp_error/dp_se))

    # ------------------------------------------
    # far field calculation
    # ------------------------------------------
    focallength_ff = calculate_focal_length_ff(calculation_parameters.ghy_x_min,
                                               calculation_parameters.ghy_x_max,
                                               input_parameters.ghy_npeak,
                                               calculation_parameters.gwavelength)

    if input_parameters.ghy_calcType == 3:
        if not (rms_slope == 0.0 or average_incident_angle == 0.0):
            focallength_ff = min(focallength_ff,(calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min) / 16 / rms_slope / numpy.sin(average_incident_angle / 1e3))#xshi changed

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
        wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_x.interpolate_values(wavefront.get_abscissas())))

    wavefront.apply_ideal_lens(focallength_ff)

    if input_parameters.ghy_calcType == 3:
       wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                      calculation_parameters.gwavelength,
                                                                      calculation_parameters.wangle_x,
                                                                      calculation_parameters.wl_x,
                                                                      calculation_parameters.w_mirror_lx))

    if do_nf: input_parameters.widget.set_progress_bar(35)
    else: input_parameters.widget.set_progress_bar(50)
    input_parameters.widget.status_message("calculated plane wave: begin FF propagation (distance = " +  str(focallength_ff) + ")")

    intensity = propagator.propagate_1D_fresnel(wavefront, focallength_ff)

    if do_nf: input_parameters.widget.set_progress_bar(50)
    else: input_parameters.widget.set_progress_bar(70)
    input_parameters.widget.status_message("dif_xp: begin calculation")

    imagesize = min(abs(calculation_parameters.ghy_x_max), abs(calculation_parameters.ghy_x_min)) * 2
    imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1


    dif_xp = ScaledArray.initialize_from_range(numpy.ones(intensity.size()),
                                               -(imagenpts - 1) / 2 * intensity.delta(),
                                               (imagenpts - 1) / 2 * intensity.delta())


    dif_xp.np_array = numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_xp.scale))**2

    dif_xp.set_scale_from_range(-(imagenpts - 1) / 2 * intensity.delta() / focallength_ff,
                                (imagenpts - 1) / 2 * intensity.delta() / focallength_ff)

    calculation_parameters.dif_xp = dif_xp

    if not do_nf: input_parameters.widget.set_progress_bar(80)

    # ------------------------------------------
    # near field calculation
    # ------------------------------------------
    if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:  # near field calculation
        fftsize = int(scale_factor * calculate_fft_size(calculation_parameters.ghy_x_min,
                                                        calculation_parameters.ghy_x_max,
                                                        calculation_parameters.gwavelength,
                                                        input_parameters.ghy_focallength,
                                                        input_parameters.ghy_fftnpts))

        input_parameters.widget.status_message("NF: creating plane wave begin, fftsize = " +  str(fftsize))
        input_parameters.widget.set_progress_bar(55)

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=scale_factor*calculation_parameters.ghy_x_min,
                                                                x_max=scale_factor*calculation_parameters.ghy_x_max)

        if scale_factor == 1.0:
            wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_x.interpolate_values(wavefront.get_abscissas())))

        wavefront.apply_ideal_lens(input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
           wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                          calculation_parameters.gwavelength,
                                                                          calculation_parameters.wangle_x,
                                                                          calculation_parameters.wl_x,
                                                                          calculation_parameters.w_mirror_lx))

        input_parameters.widget.status_message("calculated plane wave: begin NF propagation (distance = " + str(input_parameters.ghy_distance) + ")")
        input_parameters.widget.set_progress_bar(60)

        intensity = propagator.propagate_1D_fresnel(wavefront, input_parameters.ghy_distance)

        # ghy_npeak in the wavefront propagation image
        imagesize = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * input_parameters.ghy_focallength / abs(calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min))
        imagesize = max(imagesize,
                        2 * abs((calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min) * (input_parameters.ghy_distance - input_parameters.ghy_focallength)) / input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
            imagesize = max(imagesize,
                            16 * rms_slope * input_parameters.ghy_focallength * numpy.sin(average_incident_angle / 1e3))

        imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1

        input_parameters.widget.set_progress_bar(75)
        input_parameters.widget.status_message("dif_x: begin calculation")

        dif_x = ScaledArray.initialize_from_range(numpy.ones(imagenpts),
                                                  -(imagenpts - 1) / 2 * intensity.delta(),
                                                  (imagenpts - 1) / 2 * intensity.delta())

        dif_x.np_array *= numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_x.scale))**2

        calculation_parameters.dif_x = dif_x

        input_parameters.widget.set_progress_bar(80)

##########################################################################
# 1D PROPAGATION ALGORITHM - Z DIRECTION
##########################################################################

def propagate_1D_z_direction(calculation_parameters, input_parameters):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    scale_factor = 1.0

    if input_parameters.ghy_calcType == 3:
        rms_slope = hy_findrmsslopefromheight(calculation_parameters.w_mirror_lz)

        input_parameters.widget.status_message("Using RMS slope = " + str(rms_slope))

        if calculation_parameters.beam_not_cut_in_z:
            dp_image = numpy.std(calculation_parameters.zz_focal_ray)/input_parameters.ghy_focallength
            dp_se = 2 * rms_slope # different in x and z
            dp_error = calculation_parameters.gwavelength/2/(calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min)

            scale_factor = max(1, 5*min(dp_error/dp_image, dp_error/dp_se))

    # ------------------------------------------
    # far field calculation
    # ------------------------------------------
    focallength_ff = calculate_focal_length_ff(calculation_parameters.ghy_z_min,
                                               calculation_parameters.ghy_z_max,
                                               input_parameters.ghy_npeak,
                                               calculation_parameters.gwavelength)

    if input_parameters.ghy_calcType == 3 and rms_slope != 0:
        focallength_ff = min(focallength_ff,(calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min) / 16 / rms_slope) #xshi changed

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
        wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_z.interpolate_values(wavefront.get_abscissas())))

    wavefront.apply_ideal_lens(focallength_ff)

    if input_parameters.ghy_calcType == 3:
       wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                      calculation_parameters.gwavelength,
                                                                      calculation_parameters.wangle_z,
                                                                      calculation_parameters.wl_z,
                                                                      calculation_parameters.w_mirror_lz))


    if do_nf: input_parameters.widget.set_progress_bar(35)
    else: input_parameters.widget.set_progress_bar(50)
    input_parameters.widget.status_message("calculated plane wave: begin FF propagation (distance = " +  str(focallength_ff) + ")")

    intensity = propagator.propagate_1D_fresnel(wavefront, focallength_ff)

    if do_nf: input_parameters.widget.set_progress_bar(50)
    else: input_parameters.widget.set_progress_bar(70)
    input_parameters.widget.status_message("dif_zp: begin calculation")

    imagesize = min(abs(calculation_parameters.ghy_z_max), abs(calculation_parameters.ghy_z_min)) * 2
    imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1

    dif_zp = ScaledArray.initialize_from_range(numpy.ones(intensity.size()),
                                               -(imagenpts - 1) / 2 * intensity.delta(),
                                               (imagenpts - 1) / 2 * intensity.delta())

    dif_zp.np_array *= numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_zp.scale))**2

    dif_zp.set_scale_from_range(-(imagenpts - 1) / 2 * intensity.delta() / focallength_ff,
                                (imagenpts - 1) / 2 * intensity.delta() / focallength_ff)

    calculation_parameters.dif_zp = dif_zp

    if not do_nf: input_parameters.widget.set_progress_bar(80)

    # ------------------------------------------
    # near field calculation
    # ------------------------------------------
    if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
        fftsize = int(scale_factor * calculate_fft_size(calculation_parameters.ghy_z_min,
                                                        calculation_parameters.ghy_z_max,
                                                        calculation_parameters.gwavelength,
                                                        input_parameters.ghy_focallength,
                                                        input_parameters.ghy_fftnpts))

        input_parameters.widget.status_message("NF: creating plane wave begin, fftsize = " +  str(fftsize))
        input_parameters.widget.set_progress_bar(55)

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelength=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=scale_factor*calculation_parameters.ghy_z_min,
                                                                x_max=scale_factor*calculation_parameters.ghy_z_max)

        if scale_factor == 1.0:
            wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_z.interpolate_values(wavefront.get_abscissas())))

        wavefront.apply_ideal_lens(input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
           wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                          calculation_parameters.gwavelength,
                                                                          calculation_parameters.wangle_z,
                                                                          calculation_parameters.wl_z,
                                                                          calculation_parameters.w_mirror_lz))


        input_parameters.widget.status_message("calculated plane wave: begin NF propagation (distance = " + str(input_parameters.ghy_distance) + ")")
        input_parameters.widget.set_progress_bar(60)

        intensity = propagator.propagate_1D_fresnel(wavefront, input_parameters.ghy_distance)

        # ghy_npeak in the wavefront propagation image
        imagesize = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * input_parameters.ghy_focallength / abs(calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min))
        imagesize = max(imagesize,
                        2 * abs((calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min) * (input_parameters.ghy_distance - input_parameters.ghy_focallength)) / input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
            imagesize = max(imagesize, 16 * rms_slope * input_parameters.ghy_focallength)

        imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1

        input_parameters.widget.set_progress_bar(75)
        input_parameters.widget.status_message("dif_z: begin calculation")

        dif_z = ScaledArray.initialize_from_range(numpy.ones(imagenpts),
                                                  -(imagenpts - 1) / 2 * intensity.delta(),
                                                   (imagenpts - 1) / 2 * intensity.delta())

        dif_z.np_array *= numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_z.scale)**2)

        calculation_parameters.dif_z = dif_z

        input_parameters.widget.set_progress_bar(80)

#########################################################
#
# UTILITIES
#
#########################################################

def sh_read_gfile(gfilename):
    return ShadowOpticalElement.create_oe_from_file(congruence.checkFile(gfilename))

#########################################################

def read_shadow_beam(shadow_beam):
    cursor = numpy.where(shadow_beam._beam.rays[:, 9] == 1)

    image_beam_rays = copy.deepcopy(shadow_beam._beam.rays[cursor])
    image_beam_rays[:, 11] = numpy.arange(1, len(image_beam_rays) + 1, 1)

    out_beam = ShadowBeam()
    out_beam._beam.rays = image_beam_rays

    return out_beam

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

# Create sampling from 2d wave
def hy_CreateCDF1D(data):
    mDist = ScaledArray(data.np_array, data.scale)

    for index in range(1, mDist.size()):
       mDist.np_array[index] += mDist.np_array[index-1] # mDist matrix contains the rows

    mDist.np_array /= mDist.np_array[mDist.size()-1] # Normalizing each row of the matrix

    return mDist

def hy_MakeDist1D(np_array, mDist):
    random_generator = random.Random()
    random_generator.seed(25)

    pos_dif = numpy.zeros(len(np_array))
    for index in range(0, len(np_array)):
        pos_dif[index] = hy_GetOnePoint1D(mDist, random_generator)

    return pos_dif

def hy_GetOnePoint1D(mDist, random_generator, reset=0):
    if reset==1 : random_generator.seed(1)
    return mDist.interpolate_scale_value(random_generator.random()) # Finding vertical x value

# 1D
def calculate_focal_length_ff(min_value, max_value, n_peaks, wavelength):
#    return (min(abs(max_value), abs(min_value))*2)**2/n_peaks/2/0.88/wavelength  #xshi used for now, but will have problem when the aperture is off center
    return (max_value - min_value)**2/n_peaks/2/0.88/wavelength  #xshi suggested, but need to first fix the problem of getting the fake solution of mirror aperture by SHADOW.

def calculate_fft_size(min_value, max_value, wavelength, propagation_distance, fft_npts):
    return int(min(100 * (max_value - min_value) ** 2 / wavelength / propagation_distance / 0.88, fft_npts))

def get_mirror_figure_error_phase_shift(abscissas,
                                        wavelength,
                                        w_angle_function,
                                        w_l_function,
                                        mirror_figure_error):
    return (-1.0) * 4 * numpy.pi / wavelength * numpy.sin(w_angle_function(abscissas)/1e3) * mirror_figure_error.interpolate_values(w_l_function(abscissas))


def showConfirmMessage(title, message):
    msgBox = QMessageBox()
    msgBox.setFixedWidth(500)
    msgBox.setIcon(QMessageBox.Question)
    msgBox.setText(title)
    msgBox.setInformativeText(message)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    return msgBox.exec_()


################################################################
################################################################
# TEST
################################################################
################################################################

import time
from PyQt4.QtGui import QApplication
import matplotlib.pyplot as plt

import PyMca5.PyMcaGui.plotting.PlotWindow as PlotWindow
from PyMca5.PyMcaGui.plotting.ImageView import ImageView


def do_histo(array, bins):
    plt.hist(array, bins)
    plt.show()

def do_1d_plot(scaled_array, title="PROVA"):
    plot_canvas = PlotWindow.PlotWindow(roi=False, control=False, position=True, plugins=False, logx=False, logy=False)
    plot_canvas.setDefaultPlotLines(True)
    plot_canvas.setActiveCurveColor(color='darkblue')
    plot_canvas.setMinimumWidth(800)
    plot_canvas.setMaximumWidth(800)

    plot_canvas.addCurve(scaled_array.scale, scaled_array.np_array, title, symbol='', color='blue', replace=True) #'+', '^', ','
    plot_canvas.setDrawModeEnabled(True, 'rectangle')
    plot_canvas.setZoomModeEnabled(True)

    plot_canvas.show()

def do_2d_plot(scaled_matrix, title="PROVA"):
    plot_canvas = ImageView()

    colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

    plot_canvas._imagePlot.setDefaultColormap(colormap)
    plot_canvas.setMinimumWidth(800)
    plot_canvas.setMaximumWidth(800)

    nbins_x =  scaled_matrix.shape()[0]
    nbins_y =  scaled_matrix.shape()[1]

    xmin, xmax = numpy.min(scaled_matrix.x_coord), numpy.max(scaled_matrix.x_coord)
    ymin, ymax = numpy.min(scaled_matrix.y_coord), numpy.max(scaled_matrix.y_coord)

    origin = (xmin, ymin)
    scale = (abs((xmax-xmin)/nbins_x), abs((ymax-ymin)/nbins_y))

    # PyMCA inverts axis!!!! histogram must be calculated reversed
    data_to_plot = []
    for y_index in range(0, nbins_y):
        x_values = []
        for x_index in range(0, nbins_x):
            x_values.append(scaled_matrix.get_z_value(x_index, y_index))

        data_to_plot.append(x_values)

    plot_canvas.setImage(numpy.array(data_to_plot), origin=origin, scale=scale)

    plot_canvas.show()

if __name__ == "__main__":
    a = QApplication(sys.argv)

    doXianbo = True

    if doXianbo:
        os.chdir("/Users/labx/Desktop/TEMP/XIANBO_IN/")

        input_parameters = HybridInputParameters()

        input_parameters.ghy_n_oe = 1
        input_parameters.ghy_n_screen = 2
        input_parameters.ghy_diff_plane = 2
        input_parameters.ghy_calcType = 3
        input_parameters.ghy_mirrorfile = "mirror.dat"
        input_parameters.ghy_nf = 0
        input_parameters.ghy_nbins_z = 39
        input_parameters.ghy_npeak = 10
        input_parameters.ghy_fftnpts = 1e6
    else:
        os.chdir("/Users/labx/Desktop/TEMP/")

        src = ShadowSource.create_src_from_file(dir + "start.00")

        shadow_beam = ShadowBeam.traceFromSource(src)
        shadow_oe = ShadowOpticalElement.create_oe_from_file(dir + "start.01")
        shadow_beam = ShadowBeam.traceFromOE(shadow_beam, shadow_oe)

        input_parameters = HybridInputParameters()
        input_parameters.shadow_beam = shadow_beam
        input_parameters.ghy_diff_plane = 1
        input_parameters.ghy_calcType = 3
        input_parameters.ghy_mirrorfile = "mirror.dat"
        input_parameters.ghy_nf = 1
        input_parameters.ghy_nbins_z = 39
        input_parameters.ghy_npeak = 10
        input_parameters.ghy_fftnpts = 1e5

    t0 = time.time()

    output_beam, calculation_parameters = hy_run(input_parameters)

    t1 = time.time()

    print("TIME", t1-t0)

    if input_parameters.ghy_calcType == 3:
        #do_2d_plot(calculation_parameters.w_mirr_2D_values, "Slope Error Distribution")
        pass

    if input_parameters.ghy_diff_plane != 3:
        nbins = input_parameters.ghy_npeak*20+1

        if input_parameters.ghy_diff_plane == 1:
            do_1d_plot(calculation_parameters.wIray_x, "Intensity Distribution")
            do_1d_plot(calculation_parameters.dif_xp, "DIF XP")
            do_1d_plot(calculation_parameters.dif_xp, "DIF X")
        elif input_parameters.ghy_diff_plane == 2:
            do_1d_plot(calculation_parameters.wIray_z, "Intensity Distribution")
            do_1d_plot(calculation_parameters.dif_zp, "DIF ZP")
            #do_1d_plot(calculation_parameters.dif_z, "DIF Z")
            #do_histo(calculation_parameters.zz_image_ff, nbins)
            #do_histo(calculation_parameters.zz_image_nf, nbins)


            pass
    else:
        do_2d_plot(calculation_parameters.wIray_2d, "Intensity Distribution")


    output_beam.writeToFile("star_hybrid_godo.01")

    '''
    widget = ShadowPlot.DetailedPlotWidget()
    widget.plot_xy(output_beam._beam,
                   1,
                   3,
                   title="X,Z",
                   xtitle=r'X [$\mu$m]',
                   ytitle=r'Z [$\mu$m]',
                   yrange=[-2000, 2000],
                   xum=("X [" + u"\u03BC" + "m]"),
                   yum=("Z [" + u"\u03BC" + "m]"))
    widget.show()
    '''

    a.exec_()
