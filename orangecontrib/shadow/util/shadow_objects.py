
import os, copy, numpy, platform
import Shadow
from .shadow_util import Properties

class ShadowPreProcessorData:

       NONE = "None"

       def __init__(self,
                    bragg_data_file=NONE,
                    m_layer_data_file_dat=NONE,
                    m_layer_data_file_sha=NONE,
                    prerefl_data_file=NONE,
                    error_profile_data_file=NONE,
                    error_profile_x_dim = 0.0,
                    error_profile_y_dim=0.0,
                    error_profile_x_slope=0.0,
                    error_profile_y_slope=0.0):
        super().__init__()

        self.bragg_data_file=bragg_data_file
        self.m_layer_data_file_dat=m_layer_data_file_dat
        self.m_layer_data_file_sha=m_layer_data_file_sha
        self.prerefl_data_file=prerefl_data_file
        self.error_profile_data_file = error_profile_data_file
        self.error_profile_x_dim = error_profile_x_dim
        self.error_profile_y_dim = error_profile_y_dim
        self.error_profile_x_slope = error_profile_x_slope
        self.error_profile_y_slope = error_profile_y_slope

class VlsPgmPreProcessorData:
    def __init__(self,
                 shadow_coeff_0 = 0.0,
                 shadow_coeff_1 = 0.0,
                 shadow_coeff_2 = 0.0,
                 shadow_coeff_3 = 0.0,
                 d_source_plane_to_mirror = 0.0,
                 d_mirror_to_grating = 0.0,
                 d_grating_to_exit_slits = 0.0,
                 alpha = 0.0,
                 beta = 0.0):
        self.shadow_coeff_0 = shadow_coeff_0
        self.shadow_coeff_1 = shadow_coeff_1
        self.shadow_coeff_2 = shadow_coeff_2
        self.shadow_coeff_3 = shadow_coeff_3
        self.d_source_plane_to_mirror  = d_source_plane_to_mirror
        self.d_mirror_to_grating = d_mirror_to_grating
        self.d_grating_to_exit_slits = d_grating_to_exit_slits
        self.alpha=alpha
        self.beta=beta

def adjust_shadow_string(string_to_adjust):
    if string_to_adjust is None:
        return None
    else:
        if len(string_to_adjust) > 1024:
            temp = str(string_to_adjust[:1023])
            if (len(temp) == 1026 and temp[0] == "b" and temp[1] == "'" and temp[1025] == "'"):
                temp = temp[2:1025]

            return bytes(temp.rstrip(), 'utf-8')
        else:
            return string_to_adjust

class ShadowOEHistoryItem(object):

    def __init__(self,
                 oe_number=0,
                 input_beam=None,
                 shadow_source_start=None,
                 shadow_source_end=None,
                 shadow_oe_start=None,
                 shadow_oe_end=None,
                 widget_class_name=None):
        self._oe_number = oe_number
        self._input_beam = input_beam
        self._shadow_source_start = shadow_source_start
        self._shadow_source_end = shadow_source_end
        self._shadow_oe_start = shadow_oe_start
        self._shadow_oe_end = shadow_oe_end
        self._widget_class_name = widget_class_name

    def duplicate(self):
        return ShadowOEHistoryItem(oe_number=self._oe_number,
                                   input_beam=self._input_beam,
                                   shadow_source_start=self._shadow_source_start,
                                   shadow_source_end=self._shadow_source_end,
                                   shadow_oe_start=self._shadow_oe_start,
                                   shadow_oe_end=self._shadow_oe_end,
                                   widget_class_name=self._widget_class_name)

class ShadowFile:

    UNDEFINED = -1
    SOURCE = 0
    OE = 1

    @classmethod
    def readShadowFile(cls, filename):
        file = Properties()
        file.load(open(filename, encoding="utf8"))

        if file.getProperty("FMIRR") is not None:
            type = ShadowFile.OE
        elif file.getProperty("F_WIGGLER") is not None:
            type = ShadowFile.SOURCE
        else:
            type = ShadowFile.UNDEFINED

        return file, type

class ShadowBeam:

    class ScanningData(object):
        def __init__(self,
                     scanned_variable_name,
                     scanned_variable_value,
                     scanned_variable_display_name,
                     scanned_variable_um,
                     additional_parameters={}):
            self.__scanned_variable_name = scanned_variable_name
            self.__scanned_variable_value = scanned_variable_value
            self.__scanned_variable_display_name = scanned_variable_display_name
            self.__scanned_variable_um = scanned_variable_um
            self.__additional_parameters=additional_parameters

        def get_scanned_variable_name(self):
            return self.__scanned_variable_name

        def get_scanned_variable_value(self):
            return self.__scanned_variable_value

        def get_scanned_variable_display_name(self):
            return self.__scanned_variable_display_name

        def get_scanned_variable_um(self):
            return self.__scanned_variable_um

        def has_additional_parameter(self, name):
            return name in self.__additional_parameters.keys()

        def get_additional_parameter(self, name):
            return self.__additional_parameters[name]

    def __new__(cls, oe_number=0, beam=None, number_of_rays=0):
        __shadow_beam = super().__new__(cls)
        __shadow_beam._oe_number = oe_number
        if (beam is None):
            if number_of_rays > 0: __shadow_beam._beam = Shadow.Beam(number_of_rays)
            else:                  __shadow_beam._beam = Shadow.Beam()
        else:
            __shadow_beam._beam = beam

        __shadow_beam.history = []
        __shadow_beam.scanned_variable_data = None
        __shadow_beam.__initial_flux = None

        return __shadow_beam

    def set_initial_flux(self, initial_flux):
        self.__initial_flux = initial_flux

    def get_initial_flux(self):
        return self.__initial_flux

    def get_flux(self, nolost=1):
        if not self._beam is None and not self.__initial_flux is None:
            return (self._beam.intensity(nolost) / self.get_number_of_rays(0)) * self.get_initial_flux()
        else:
            return None

    def get_number_of_rays(self, nolost=0):
        if not hasattr(self._beam, "rays"): return 0
        if nolost==0:     return self._beam.rays.shape[0]
        elif nolost==1:   return self._beam.rays[numpy.where(self._beam.rays[:, 9] > 0)].shape[0]
        elif nolost == 2: return self._beam.rays[numpy.where(self._beam.rays[:, 9] < 0)].shape[0]
        else: raise ValueError("nolost flag value not valid")

    def setBeam(self, beam):
        self._beam = beam

    def setScanningData(self, scanned_variable_data=ScanningData(None, None, None, None)):
        self.scanned_variable_data=scanned_variable_data

    def loadFromFile(self, file_name):
        if not self._beam is None:
            if os.path.exists(file_name):
                self._beam.load(file_name)
            else:
                raise Exception("File " + file_name + " not existing")

    def writeToFile(self, file_name):
        if not self._beam is None:
            self._beam.write(file_name)

    def duplicate(self, copy_rays=True, history=True):
        beam = Shadow.Beam()
        if copy_rays: beam.rays = copy.deepcopy(self._beam.rays)

        new_shadow_beam = ShadowBeam(self._oe_number, beam)
        new_shadow_beam.setScanningData(self.scanned_variable_data)
        new_shadow_beam.set_initial_flux(self.get_initial_flux())

        if history:
            for historyItem in self.history: new_shadow_beam.history.append(historyItem)

        return new_shadow_beam

    @classmethod
    def mergeBeams(cls, beam_1, beam_2, which_flux=3, merge_history=1):
        if beam_1 and beam_2:
            rays_1 = None
            rays_2 = None

            if len(getattr(beam_1._beam, "rays", numpy.zeros(0))) > 0:
                rays_1 = copy.deepcopy(beam_1._beam.rays)
            if len(getattr(beam_2._beam, "rays", numpy.zeros(0))) > 0:
                rays_2 = copy.deepcopy(beam_2._beam.rays)

            #if len(rays_2) != len(rays_1): raise ValueError("The two beams must have the same amount of rays for merging")

            merged_beam = beam_1.duplicate(copy_rays=False, history=True)

            merged_beam._oe_number = beam_1._oe_number
            merged_beam._beam.rays = numpy.append(rays_1, rays_2, axis=0)

            merged_beam._beam.rays[:, 11] = numpy.arange(1, len(merged_beam._beam.rays) + 1, 1) # ray_index

            if which_flux==1:
                if not beam_1.get_initial_flux() is None:
                    merged_beam.set_initial_flux(beam_1.get_initial_flux())
            elif which_flux==2:
                if not beam_2.get_initial_flux() is None:
                    merged_beam.set_initial_flux(beam_2.get_initial_flux())
            else:
                if not beam_1.get_initial_flux() is None and not beam_2.get_initial_flux() is None:
                    merged_beam.set_initial_flux(beam_1.get_initial_flux() + beam_2.get_initial_flux())

            if merge_history > 0:
                if beam_1.history and beam_2.history:
                    if len(beam_1.history) == len(beam_2.history):
                        for index in range(1, beam_1._oe_number + 1):
                            history_element_1 =  beam_1.getOEHistory(index)
                            history_element_2 =  beam_2.getOEHistory(index)

                            merged_history_element = merged_beam.getOEHistory(index)
                            if merge_history == 1:
                                merged_history_element._input_beam = ShadowBeam.mergeBeams(history_element_1._input_beam, history_element_2._input_beam, which_flux, merge_history=False)
                            else:
                                merged_history_element._input_beam = ShadowBeam.mergeBeams(history_element_1._input_beam, history_element_2._input_beam, which_flux, merge_history=True)
                    else:
                        raise ValueError("Histories must have the same path to be merged")
                else:
                    raise ValueError("Both beams must have a history to be merged")

            return merged_beam
        else:
            raise Exception("Both input beams should provided for merging")

    @classmethod
    def traceFromSource(cls, shadow_src, write_begin_file=0, write_start_file=0, write_end_file=0, history=True, widget_class_name=None):
        __shadow_beam = cls.__new__(ShadowBeam, beam=Shadow.Beam())

        shadow_src.self_repair()

        shadow_source_start = shadow_src.duplicate()

        if write_start_file == 1:
            shadow_src.src.write("start.00")

        __shadow_beam._beam.genSource(shadow_src.src)

        shadow_src.self_repair()

        if write_begin_file:
            __shadow_beam.writeToFile("begin.dat")

        if write_end_file == 1:
            shadow_src.src.write("end.00")

        shadow_source_end = shadow_src.duplicate()

        if history:
            __shadow_beam.history.append(ShadowOEHistoryItem(shadow_source_start=shadow_source_start,
                                                    shadow_source_end=shadow_source_end,
                                                    widget_class_name=widget_class_name))

        return __shadow_beam

    @classmethod
    def traceFromOE(cls, input_beam, shadow_oe, write_start_file=0, write_end_file=0, history=True, widget_class_name=None):
        __shadow_beam = cls.initializeFromPreviousBeam(input_beam)

        shadow_oe.self_repair()

        if history: history_shadow_oe_start = shadow_oe.duplicate()
        if write_start_file == 1: shadow_oe._oe.write("start.%02d"%__shadow_beam._oe_number)

        __shadow_beam._beam.traceOE(shadow_oe._oe, __shadow_beam._oe_number)

        shadow_oe.self_repair()

        if write_end_file == 1: shadow_oe._oe.write("end.%02d"%__shadow_beam._oe_number)

        if history:
            history_shadow_oe_end = shadow_oe.duplicate()

            #N.B. history[0] = Source
            if not __shadow_beam._oe_number == 0:
                if len(__shadow_beam.history) - 1 < __shadow_beam._oe_number:
                    __shadow_beam.history.append(ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                            input_beam=input_beam.duplicate(),
                                                            shadow_oe_start=history_shadow_oe_start,
                                                            shadow_oe_end=history_shadow_oe_end, widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number]=ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                      input_beam=input_beam.duplicate(),
                                                                      shadow_oe_start=history_shadow_oe_start,
                                                                      shadow_oe_end=history_shadow_oe_end,
                                                                      widget_class_name=widget_class_name)

        return __shadow_beam

    @classmethod
    def traceIdealLensOE(cls, input_beam, shadow_oe, history=True, widget_class_name=None):
        __shadow_beam = cls.initializeFromPreviousBeam(input_beam)

        shadow_oe.self_repair()

        if history: history_shadow_oe_start = shadow_oe.duplicate()

        __shadow_beam._beam.traceIdealLensOE(shadow_oe._oe, __shadow_beam._oe_number)

        shadow_oe.self_repair()

        if history:
            history_shadow_oe_end = shadow_oe.duplicate()

            #N.B. history[0] = Source
            if not __shadow_beam._oe_number == 0:
                if len(__shadow_beam.history) - 1 < __shadow_beam._oe_number:
                    __shadow_beam.history.append(ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                            input_beam=input_beam.duplicate(),
                                                            shadow_oe_start=history_shadow_oe_start,
                                                            shadow_oe_end=history_shadow_oe_end, widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number]=ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                      input_beam=input_beam.duplicate(),
                                                                      shadow_oe_start=history_shadow_oe_start,
                                                                      shadow_oe_end=history_shadow_oe_end,
                                                                      widget_class_name=widget_class_name)

        return __shadow_beam

    @classmethod
    def traceFromCompoundOE(cls,
                            input_beam,
                            shadow_oe,
                            write_start_files=0,
                            write_end_files=0,
                            write_star_files=0,
                            write_mirr_files=0,
                            history=True,
                            widget_class_name=None):
        __shadow_beam = cls.initializeFromPreviousBeam(input_beam)

        shadow_oe.self_repair()

        if history: history_shadow_oe_start = shadow_oe.duplicate()

        __shadow_beam._beam.traceCompoundOE(shadow_oe._oe,
                                   from_oe=__shadow_beam._oe_number,
                                   write_start_files=write_start_files,
                                   write_end_files=write_end_files,
                                   write_star_files=write_star_files,
                                   write_mirr_files=write_mirr_files)

        shadow_oe.self_repair()

        if history:
            history_shadow_oe_end = shadow_oe.duplicate()

            # N.B. history[0] = Source
            if not __shadow_beam._oe_number == 0:
                if len(__shadow_beam.history) - 1 < __shadow_beam._oe_number:
                    __shadow_beam.history.append(ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                            input_beam=input_beam.duplicate(),
                                                            shadow_oe_start=history_shadow_oe_start,
                                                            shadow_oe_end=history_shadow_oe_end,
                                                            widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number] = ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                        input_beam=input_beam.duplicate(),
                                                                        shadow_oe_start=history_shadow_oe_start,
                                                                        shadow_oe_end=history_shadow_oe_end,
                                                                        widget_class_name=widget_class_name)

        return __shadow_beam

    @classmethod
    def initializeFromPreviousBeam(cls, input_beam):
        __shadow_beam = input_beam.duplicate()
        __shadow_beam._oe_number = input_beam._oe_number + 1

        return __shadow_beam

    def getOEHistory(self, oe_number=None):
        if oe_number is None:
            return self.history
        else:
            return self.history[oe_number]

    def historySize(self):
        return len(self.history)

class ShadowSource:
    def __new__(cls, src=None):
        __shadow_source = super().__new__(cls)
        __shadow_source.src = src
        __shadow_source.source_type = None
        return __shadow_source

    def set_src(self, src):
        self.src = src

    def set_source_type(self, type):
        self.source_type = type

    ####################################################################
    # FOR WEIRD BUG ON LINUX AND MAC - STRING NOT PROPERLY RETURNED BY BINDING
    ####################################################################
    def self_repair(self):
        if platform.system() == 'Linux' or platform.system() == 'Darwin':
            self.src.FILE_TRAJ   = adjust_shadow_string(self.src.FILE_TRAJ)
            self.src.FILE_SOURCE = adjust_shadow_string(self.src.FILE_SOURCE)
            self.src.FILE_BOUND  = adjust_shadow_string(self.src.FILE_BOUND)

    @classmethod
    def create_src(cls):
        __shadow_source = cls.__new__(ShadowSource, src=Shadow.Source())

        __shadow_source.src.OE_NUMBER =  0
        __shadow_source.src.FILE_TRAJ=bytes("NONESPECIFIED", 'utf-8')
        __shadow_source.src.FILE_SOURCE=bytes("NONESPECIFIED", 'utf-8')
        __shadow_source.src.FILE_BOUND=bytes("NONESPECIFIED", 'utf-8')

        return __shadow_source

    @classmethod
    def create_src_from_file(cls, filename):
        __shadow_source = cls.create_src()
        __shadow_source.src.load(filename)

        return __shadow_source

    @classmethod
    def create_bm_src(cls):
        __shadow_source = cls.create_src()

        __shadow_source.src.FSOURCE_DEPTH=4
        __shadow_source.src.F_COLOR=3
        __shadow_source.src.F_PHOT=0
        __shadow_source.src.F_POLAR=1
        __shadow_source.src.NCOL=0
        __shadow_source.src.N_COLOR=0
        __shadow_source.src.POL_DEG=0.0
        __shadow_source.src.SIGDIX=0.0
        __shadow_source.src.SIGDIZ=0.0
        __shadow_source.src.SIGMAY=0.0
        __shadow_source.src.WXSOU=0.0
        __shadow_source.src.WYSOU=0.0
        __shadow_source.src.WZSOU=0.0

        __shadow_source.src.F_WIGGLER = 0

        return __shadow_source

    @classmethod
    def create_undulator_gaussian_src(cls):
        __shadow_source = cls.create_src()

        __shadow_source.src.FDISTR =  3
        __shadow_source.src.FSOUR =  3
        __shadow_source.src.F_COLOR=3
        __shadow_source.src.F_PHOT=0
        __shadow_source.src.F_POLAR=1
        __shadow_source.src.HDIV1 =    0.0
        __shadow_source.src.HDIV2 =    0.0
        __shadow_source.src.VDIV1 =    0.0
        __shadow_source.src.VDIV2 =    0.0

        __shadow_source.src.F_WIGGLER = 0

        return __shadow_source

    @classmethod
    def create_wiggler_src(cls):
        __shadow_source = cls.create_src()

        __shadow_source.src.FDISTR =  0
        __shadow_source.src.FSOUR =  0
        __shadow_source.src.FSOURCE_DEPTH =  0
        __shadow_source.src.F_COLOR=0
        __shadow_source.src.F_PHOT=0
        __shadow_source.src.F_POLAR=1
        __shadow_source.src.F_WIGGLER = 1
        __shadow_source.src.NCOL = 0

        __shadow_source.src.N_COLOR = 0
        __shadow_source.src.IDO_VX = 0
        __shadow_source.src.IDO_VZ = 0
        __shadow_source.src.IDO_X_S = 0
        __shadow_source.src.IDO_Y_S = 0
        __shadow_source.src.IDO_Z_S = 0

        __shadow_source.src.VDIV1 = 1.00000000000000
        __shadow_source.src.VDIV2 = 1.00000000000000
        __shadow_source.src.WXSOU = 0.00000000000000
        __shadow_source.src.WYSOU = 0.00000000000000
        __shadow_source.src.WZSOU = 0.00000000000000

        __shadow_source.src.POL_DEG = 0.00000000000000

        return __shadow_source

    def duplicate(self):
        new_src = ShadowSource.create_src()

        new_src.src.FDISTR            = self.src.FDISTR
        new_src.src.FGRID             = self.src.FGRID
        new_src.src.FSOUR             = self.src.FSOUR
        new_src.src.FSOURCE_DEPTH     = self.src.FSOURCE_DEPTH
        new_src.src.F_COHER           = self.src.F_COHER
        new_src.src.F_COLOR           = self.src.F_COLOR
        new_src.src.F_PHOT            = self.src.F_PHOT
        new_src.src.F_POL             = self.src.F_POL
        new_src.src.F_POLAR           = self.src.F_POLAR
        new_src.src.F_OPD             = self.src.F_OPD
        new_src.src.F_WIGGLER         = self.src.F_WIGGLER
        new_src.src.F_BOUND_SOUR      = self.src.F_BOUND_SOUR
        new_src.src.F_SR_TYPE         = self.src.F_SR_TYPE
        new_src.src.ISTAR1            = self.src.ISTAR1
        new_src.src.NPOINT            = self.src.NPOINT
        new_src.src.NCOL              = self.src.NCOL
        new_src.src.N_CIRCLE          = self.src.N_CIRCLE
        new_src.src.N_COLOR           = self.src.N_COLOR
        new_src.src.N_CONE            = self.src.N_CONE
        new_src.src.IDO_VX            = self.src.IDO_VX
        new_src.src.IDO_VZ            = self.src.IDO_VZ
        new_src.src.IDO_X_S           = self.src.IDO_X_S
        new_src.src.IDO_Y_S           = self.src.IDO_Y_S
        new_src.src.IDO_Z_S           = self.src.IDO_Z_S
        new_src.src.IDO_XL            = self.src.IDO_XL
        new_src.src.IDO_XN            = self.src.IDO_XN
        new_src.src.IDO_ZL            = self.src.IDO_ZL
        new_src.src.IDO_ZN            = self.src.IDO_ZN
        new_src.src.SIGXL1            = self.src.SIGXL1
        new_src.src.SIGXL2            = self.src.SIGXL2
        new_src.src.SIGXL3            = self.src.SIGXL3
        new_src.src.SIGXL4            = self.src.SIGXL4
        new_src.src.SIGXL5            = self.src.SIGXL5
        new_src.src.SIGXL6            = self.src.SIGXL6
        new_src.src.SIGXL7            = self.src.SIGXL7
        new_src.src.SIGXL8            = self.src.SIGXL8
        new_src.src.SIGXL9            = self.src.SIGXL9
        new_src.src.SIGXL10           = self.src.SIGXL10
        new_src.src.SIGZL1            = self.src.SIGZL1
        new_src.src.SIGZL2            = self.src.SIGZL2
        new_src.src.SIGZL3            = self.src.SIGZL3
        new_src.src.SIGZL4            = self.src.SIGZL4
        new_src.src.SIGZL5            = self.src.SIGZL5
        new_src.src.SIGZL6            = self.src.SIGZL6
        new_src.src.SIGZL7            = self.src.SIGZL7
        new_src.src.SIGZL8            = self.src.SIGZL8
        new_src.src.SIGZL9            = self.src.SIGZL9
        new_src.src.SIGZL10           = self.src.SIGZL10
        new_src.src.CONV_FACT         = self.src.CONV_FACT
        new_src.src.CONE_MAX          = self.src.CONE_MAX
        new_src.src.CONE_MIN          = self.src.CONE_MIN
        new_src.src.EPSI_DX           = self.src.EPSI_DX
        new_src.src.EPSI_DZ           = self.src.EPSI_DZ
        new_src.src.EPSI_X            = self.src.EPSI_X
        new_src.src.EPSI_Z            = self.src.EPSI_Z
        new_src.src.HDIV1             = self.src.HDIV1
        new_src.src.HDIV2             = self.src.HDIV2
        new_src.src.PH1               = self.src.PH1
        new_src.src.PH2               = self.src.PH2
        new_src.src.PH3               = self.src.PH3
        new_src.src.PH4               = self.src.PH4
        new_src.src.PH5               = self.src.PH5
        new_src.src.PH6               = self.src.PH6
        new_src.src.PH7               = self.src.PH7
        new_src.src.PH8               = self.src.PH8
        new_src.src.PH9               = self.src.PH9
        new_src.src.PH10              = self.src.PH10
        new_src.src.RL1               = self.src.RL1
        new_src.src.RL2               = self.src.RL2
        new_src.src.RL3               = self.src.RL3
        new_src.src.RL4               = self.src.RL4
        new_src.src.RL5               = self.src.RL5
        new_src.src.RL6               = self.src.RL6
        new_src.src.RL7               = self.src.RL7
        new_src.src.RL8               = self.src.RL8
        new_src.src.RL9               = self.src.RL9
        new_src.src.RL10              = self.src.RL10
        new_src.src.BENER             = self.src.BENER
        new_src.src.POL_ANGLE         = self.src.POL_ANGLE
        new_src.src.POL_DEG           = self.src.POL_DEG
        new_src.src.R_ALADDIN         = self.src.R_ALADDIN
        new_src.src.R_MAGNET          = self.src.R_MAGNET
        new_src.src.SIGDIX            = self.src.SIGDIX
        new_src.src.SIGDIZ            = self.src.SIGDIZ
        new_src.src.SIGMAX            = self.src.SIGMAX
        new_src.src.SIGMAY            = self.src.SIGMAY
        new_src.src.SIGMAZ            = self.src.SIGMAZ
        new_src.src.VDIV1             = self.src.VDIV1
        new_src.src.VDIV2             = self.src.VDIV2
        new_src.src.WXSOU             = self.src.WXSOU
        new_src.src.WYSOU             = self.src.WYSOU
        new_src.src.WZSOU             = self.src.WZSOU
        new_src.src.PLASMA_ANGLE      = self.src.PLASMA_ANGLE
        new_src.src.FILE_TRAJ         = self.src.FILE_TRAJ
        new_src.src.FILE_SOURCE       = self.src.FILE_SOURCE
        new_src.src.FILE_BOUND        = self.src.FILE_BOUND
        new_src.src.OE_NUMBER         = self.src.OE_NUMBER
        new_src.src.NTOTALPOINT       = self.src.NTOTALPOINT
        new_src.src.IDUMMY            = self.src.IDUMMY
        new_src.src.DUMMY             = self.src.DUMMY
        new_src.src.F_NEW             = self.src.F_NEW

        return new_src

class ShadowOpticalElement:
    def __init__(self, oe=None):
        self._oe = oe

    def set_oe(self, oe):
        self._oe = oe

    ####################################################################
    # FOR WEIRD BUG ON LINUX AND MAC - STRING NOT PROPERLY RETURNED BY BINDING
    ####################################################################
    def self_repair(self):
        if not isinstance(self._oe, Shadow.IdealLensOE):
            if platform.system() == 'Linux' or platform.system() == 'Darwin':
                self._oe.FILE_SOURCE      = adjust_shadow_string(self._oe.FILE_SOURCE)
                self._oe.FILE_RIP         = adjust_shadow_string(self._oe.FILE_RIP)
                self._oe.FILE_REFL        = adjust_shadow_string(self._oe.FILE_REFL)
                self._oe.FILE_MIR         = adjust_shadow_string(self._oe.FILE_MIR)
                self._oe.FILE_ROUGH       = adjust_shadow_string(self._oe.FILE_ROUGH)
                self._oe.FILE_R_IND_OBJ   = adjust_shadow_string(self._oe.FILE_R_IND_OBJ)
                self._oe.FILE_R_IND_IMA   = adjust_shadow_string(self._oe.FILE_R_IND_IMA)
                self._oe.FILE_FAC         = adjust_shadow_string(self._oe.FILE_FAC)
                self._oe.FILE_SEGMENT     = adjust_shadow_string(self._oe.FILE_SEGMENT)
                self._oe.FILE_SEGP        = adjust_shadow_string(self._oe.FILE_SEGP)
                self._oe.FILE_KOMA        = adjust_shadow_string(self._oe.FILE_KOMA)
                self._oe.FILE_KOMA_CA     = adjust_shadow_string(self._oe.FILE_KOMA_CA)

                FILE_ABS = [adjust_shadow_string(self._oe.FILE_ABS[0]),
                            adjust_shadow_string(self._oe.FILE_ABS[1]),
                            adjust_shadow_string(self._oe.FILE_ABS[2]),
                            adjust_shadow_string(self._oe.FILE_ABS[3]),
                            adjust_shadow_string(self._oe.FILE_ABS[4]),
                            adjust_shadow_string(self._oe.FILE_ABS[5]),
                            adjust_shadow_string(self._oe.FILE_ABS[6]),
                            adjust_shadow_string(self._oe.FILE_ABS[7]),
                            adjust_shadow_string(self._oe.FILE_ABS[8]),
                            adjust_shadow_string(self._oe.FILE_ABS[9])]

                self._oe.FILE_ABS = numpy.array(FILE_ABS)

                FILE_SCR_EXT = [adjust_shadow_string(self._oe.FILE_SCR_EXT[0]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[1]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[2]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[3]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[4]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[5]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[6]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[7]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[8]),
                                adjust_shadow_string(self._oe.FILE_SCR_EXT[9])]

                self._oe.FILE_SCR_EXT = numpy.array(FILE_SCR_EXT)

    def duplicate(self):
        if isinstance(self._oe, Shadow.IdealLensOE):
            new_oe = ShadowOpticalElement.create_ideal_lens()

            new_oe._oe.T_SOURCE = self._oe.T_SOURCE
            new_oe._oe.T_IMAGE = self._oe.T_IMAGE
            new_oe._oe.IDUMMY = self._oe.IDUMMY
            new_oe._oe.focal_x = self._oe.focal_x
            new_oe._oe.focal_z = self._oe.focal_z
            new_oe._oe.user_units_to_cm = self._oe.user_units_to_cm
        else:
            new_oe = ShadowOpticalElement.create_empty_oe()

            new_oe._oe.FMIRR = self._oe.FMIRR
            new_oe._oe.F_TORUS = self._oe.F_TORUS
            new_oe._oe.FCYL = self._oe.FCYL
            new_oe._oe.F_EXT = self._oe.F_EXT
            new_oe._oe.FSTAT = self._oe.FSTAT
            new_oe._oe.F_SCREEN = self._oe.F_SCREEN
            new_oe._oe.F_PLATE = self._oe.F_PLATE
            new_oe._oe.FSLIT = self._oe.FSLIT
            new_oe._oe.FWRITE = self._oe.FWRITE
            new_oe._oe.F_RIPPLE = self._oe.F_RIPPLE
            new_oe._oe.F_MOVE = self._oe.F_MOVE
            new_oe._oe.F_THICK = self._oe.F_THICK
            new_oe._oe.F_BRAGG_A = self._oe.F_BRAGG_A
            new_oe._oe.F_G_S = self._oe.F_G_S
            new_oe._oe.F_R_RAN = self._oe.F_R_RAN
            new_oe._oe.F_GRATING = self._oe.F_GRATING
            new_oe._oe.F_MOSAIC = self._oe.F_MOSAIC
            new_oe._oe.F_JOHANSSON = self._oe.F_JOHANSSON
            new_oe._oe.F_SIDE = self._oe.F_SIDE
            new_oe._oe.F_CENTRAL = self._oe.F_CENTRAL
            new_oe._oe.F_CONVEX = self._oe.F_CONVEX
            new_oe._oe.F_REFLEC = self._oe.F_REFLEC
            new_oe._oe.F_RUL_ABS = self._oe.F_RUL_ABS
            new_oe._oe.F_RULING = self._oe.F_RULING
            new_oe._oe.F_PW = self._oe.F_PW
            new_oe._oe.F_PW_C = self._oe.F_PW_C
            new_oe._oe.F_VIRTUAL = self._oe.F_VIRTUAL
            new_oe._oe.FSHAPE = self._oe.FSHAPE
            new_oe._oe.FHIT_C = self._oe.FHIT_C
            new_oe._oe.F_MONO = self._oe.F_MONO
            new_oe._oe.F_REFRAC = self._oe.F_REFRAC
            new_oe._oe.F_DEFAULT = self._oe.F_DEFAULT
            new_oe._oe.F_REFL = self._oe.F_REFL
            new_oe._oe.F_HUNT = self._oe.F_HUNT
            new_oe._oe.F_CRYSTAL = self._oe.F_CRYSTAL
            new_oe._oe.F_PHOT_CENT = self._oe.F_PHOT_CENT
            new_oe._oe.F_ROUGHNESS = self._oe.F_ROUGHNESS
            new_oe._oe.F_ANGLE = self._oe.F_ANGLE
            new_oe._oe.NPOINT = self._oe.NPOINT
            new_oe._oe.NCOL = self._oe.NCOL
            new_oe._oe.N_SCREEN = self._oe.N_SCREEN
            new_oe._oe.ISTAR1 = self._oe.ISTAR1
            new_oe._oe.CIL_ANG = self._oe.CIL_ANG
            new_oe._oe.ELL_THE = self._oe.ELL_THE
            new_oe._oe.N_PLATES = self._oe.N_PLATES
            new_oe._oe.IG_SEED = self._oe.IG_SEED
            new_oe._oe.MOSAIC_SEED = self._oe.MOSAIC_SEED
            new_oe._oe.ALPHA = self._oe.ALPHA
            new_oe._oe.SSOUR = self._oe.SSOUR
            new_oe._oe.THETA = self._oe.THETA
            new_oe._oe.SIMAG = self._oe.SIMAG
            new_oe._oe.RDSOUR = self._oe.RDSOUR
            new_oe._oe.RTHETA = self._oe.RTHETA
            new_oe._oe.OFF_SOUX = self._oe.OFF_SOUX
            new_oe._oe.OFF_SOUY = self._oe.OFF_SOUY
            new_oe._oe.OFF_SOUZ = self._oe.OFF_SOUZ
            new_oe._oe.ALPHA_S = self._oe.ALPHA_S
            new_oe._oe.RLEN1 = self._oe.RLEN1
            new_oe._oe.RLEN2 = self._oe.RLEN2
            new_oe._oe.RMIRR = self._oe.RMIRR
            new_oe._oe.AXMAJ = self._oe.AXMAJ
            new_oe._oe.AXMIN = self._oe.AXMIN
            new_oe._oe.CONE_A = self._oe.CONE_A
            new_oe._oe.R_MAJ = self._oe.R_MAJ
            new_oe._oe.R_MIN = self._oe.R_MIN
            new_oe._oe.RWIDX1 = self._oe.RWIDX1
            new_oe._oe.RWIDX2 = self._oe.RWIDX2
            new_oe._oe.PARAM = self._oe.PARAM
            new_oe._oe.HUNT_H = self._oe.HUNT_H
            new_oe._oe.HUNT_L = self._oe.HUNT_L
            new_oe._oe.BLAZE = self._oe.BLAZE
            new_oe._oe.RULING = self._oe.RULING
            new_oe._oe.ORDER = self._oe.ORDER
            new_oe._oe.PHOT_CENT = self._oe.PHOT_CENT
            new_oe._oe.X_ROT = self._oe.X_ROT
            new_oe._oe.D_SPACING = self._oe.D_SPACING
            new_oe._oe.A_BRAGG = self._oe.A_BRAGG
            new_oe._oe.SPREAD_MOS = self._oe.SPREAD_MOS
            new_oe._oe.THICKNESS = self._oe.THICKNESS
            new_oe._oe.R_JOHANSSON = self._oe.R_JOHANSSON
            new_oe._oe.Y_ROT = self._oe.Y_ROT
            new_oe._oe.Z_ROT = self._oe.Z_ROT
            new_oe._oe.OFFX = self._oe.OFFX
            new_oe._oe.OFFY = self._oe.OFFY
            new_oe._oe.OFFZ = self._oe.OFFZ
            new_oe._oe.SLLEN = self._oe.SLLEN
            new_oe._oe.SLWID = self._oe.SLWID
            new_oe._oe.SLTILT = self._oe.SLTILT
            new_oe._oe.COD_LEN = self._oe.COD_LEN
            new_oe._oe.COD_WID = self._oe.COD_WID
            new_oe._oe.X_SOUR = self._oe.X_SOUR
            new_oe._oe.Y_SOUR = self._oe.Y_SOUR
            new_oe._oe.Z_SOUR = self._oe.Z_SOUR
            new_oe._oe.X_SOUR_ROT = self._oe.X_SOUR_ROT
            new_oe._oe.Y_SOUR_ROT = self._oe.Y_SOUR_ROT
            new_oe._oe.Z_SOUR_ROT = self._oe.Z_SOUR_ROT
            new_oe._oe.R_LAMBDA = self._oe.R_LAMBDA
            new_oe._oe.THETA_I = self._oe.THETA_I
            new_oe._oe.ALPHA_I = self._oe.ALPHA_I
            new_oe._oe.T_INCIDENCE = self._oe.T_INCIDENCE
            new_oe._oe.T_SOURCE = self._oe.T_SOURCE
            new_oe._oe.T_IMAGE = self._oe.T_IMAGE
            new_oe._oe.T_REFLECTION = self._oe.T_REFLECTION
            new_oe._oe.FILE_SOURCE = self._oe.FILE_SOURCE
            new_oe._oe.FILE_RIP = self._oe.FILE_RIP
            new_oe._oe.FILE_REFL = self._oe.FILE_REFL
            new_oe._oe.FILE_MIR = self._oe.FILE_MIR
            new_oe._oe.FILE_ROUGH = self._oe.FILE_ROUGH
            new_oe._oe.FZP = self._oe.FZP
            new_oe._oe.HOLO_R1 = self._oe.HOLO_R1
            new_oe._oe.HOLO_R2 = self._oe.HOLO_R2
            new_oe._oe.HOLO_DEL = self._oe.HOLO_DEL
            new_oe._oe.HOLO_GAM = self._oe.HOLO_GAM
            new_oe._oe.HOLO_W = self._oe.HOLO_W
            new_oe._oe.HOLO_RT1 = self._oe.HOLO_RT1
            new_oe._oe.HOLO_RT2 = self._oe.HOLO_RT2
            new_oe._oe.AZIM_FAN = self._oe.AZIM_FAN
            new_oe._oe.DIST_FAN = self._oe.DIST_FAN
            new_oe._oe.COMA_FAC = self._oe.COMA_FAC
            new_oe._oe.ALFA = self._oe.ALFA
            new_oe._oe.GAMMA = self._oe.GAMMA
            new_oe._oe.R_IND_OBJ = self._oe.R_IND_OBJ
            new_oe._oe.R_IND_IMA = self._oe.R_IND_IMA
            new_oe._oe.R_ATTENUATION_OBJ = self._oe.R_ATTENUATION_OBJ
            new_oe._oe.R_ATTENUATION_IMA = self._oe.R_ATTENUATION_IMA
            new_oe._oe.F_R_IND = self._oe.F_R_IND
            new_oe._oe.FILE_R_IND_OBJ = self._oe.FILE_R_IND_OBJ
            new_oe._oe.FILE_R_IND_IMA = self._oe.FILE_R_IND_IMA
            new_oe._oe.RUL_A1 = self._oe.RUL_A1
            new_oe._oe.RUL_A2 = self._oe.RUL_A2
            new_oe._oe.RUL_A3 = self._oe.RUL_A3
            new_oe._oe.RUL_A4 = self._oe.RUL_A4
            new_oe._oe.F_POLSEL = self._oe.F_POLSEL
            new_oe._oe.F_FACET = self._oe.F_FACET
            new_oe._oe.F_FAC_ORIENT = self._oe.F_FAC_ORIENT
            new_oe._oe.F_FAC_LATT = self._oe.F_FAC_LATT
            new_oe._oe.RFAC_LENX = self._oe.RFAC_LENX
            new_oe._oe.RFAC_LENY = self._oe.RFAC_LENY
            new_oe._oe.RFAC_PHAX = self._oe.RFAC_PHAX
            new_oe._oe.RFAC_PHAY = self._oe.RFAC_PHAY
            new_oe._oe.RFAC_DELX1 = self._oe.RFAC_DELX1
            new_oe._oe.RFAC_DELX2 = self._oe.RFAC_DELX2
            new_oe._oe.RFAC_DELY1 = self._oe.RFAC_DELY1
            new_oe._oe.RFAC_DELY2 = self._oe.RFAC_DELY2
            new_oe._oe.FILE_FAC = self._oe.FILE_FAC
            new_oe._oe.F_SEGMENT = self._oe.F_SEGMENT
            new_oe._oe.ISEG_XNUM = self._oe.ISEG_XNUM
            new_oe._oe.ISEG_YNUM = self._oe.ISEG_YNUM
            new_oe._oe.FILE_SEGMENT = self._oe.FILE_SEGMENT
            new_oe._oe.FILE_SEGP = self._oe.FILE_SEGP
            new_oe._oe.SEG_LENX = self._oe.SEG_LENX
            new_oe._oe.SEG_LENY = self._oe.SEG_LENY
            new_oe._oe.F_KOMA = self._oe.F_KOMA
            new_oe._oe.FILE_KOMA = self._oe.FILE_KOMA
            new_oe._oe.F_EXIT_SHAPE = self._oe.F_EXIT_SHAPE
            new_oe._oe.F_INC_MNOR_ANG = self._oe.F_INC_MNOR_ANG
            new_oe._oe.ZKO_LENGTH = self._oe.ZKO_LENGTH
            new_oe._oe.RKOMA_CX = self._oe.RKOMA_CX
            new_oe._oe.RKOMA_CY = self._oe.RKOMA_CY
            new_oe._oe.F_KOMA_CA = self._oe.F_KOMA_CA
            new_oe._oe.FILE_KOMA_CA = self._oe.FILE_KOMA_CA
            new_oe._oe.F_KOMA_BOUNCE = self._oe.F_KOMA_BOUNCE
            new_oe._oe.X_RIP_AMP = self._oe.X_RIP_AMP
            new_oe._oe.X_RIP_WAV = self._oe.X_RIP_WAV
            new_oe._oe.X_PHASE = self._oe.X_PHASE
            new_oe._oe.Y_RIP_AMP = self._oe.Y_RIP_AMP
            new_oe._oe.Y_RIP_WAV = self._oe.Y_RIP_WAV
            new_oe._oe.Y_PHASE = self._oe.Y_PHASE
            new_oe._oe.N_RIP = self._oe.N_RIP
            new_oe._oe.ROUGH_X = self._oe.ROUGH_X
            new_oe._oe.ROUGH_Y = self._oe.ROUGH_Y
            new_oe._oe.OE_NUMBER = self._oe.OE_NUMBER
            new_oe._oe.IDUMMY = self._oe.IDUMMY
            new_oe._oe.DUMMY = self._oe.DUMMY

            new_oe._oe.CX_SLIT = copy.deepcopy(self._oe.CX_SLIT)
            new_oe._oe.CZ_SLIT = copy.deepcopy(self._oe.CZ_SLIT)
            new_oe._oe.D_PLATE = copy.deepcopy(self._oe.D_PLATE)
            new_oe._oe.FILE_ABS = copy.deepcopy(self._oe.FILE_ABS)
            new_oe._oe.FILE_SCR_EXT = copy.deepcopy(self._oe.FILE_SCR_EXT)
            new_oe._oe.I_ABS = copy.deepcopy(self._oe.I_ABS)
            new_oe._oe.I_SCREEN = copy.deepcopy(self._oe.I_SCREEN)
            new_oe._oe.I_SLIT = copy.deepcopy(self._oe.I_SLIT)
            new_oe._oe.I_STOP = copy.deepcopy(self._oe.I_STOP)
            new_oe._oe.K_SLIT = copy.deepcopy(self._oe.K_SLIT)
            new_oe._oe.RX_SLIT = copy.deepcopy(self._oe.RX_SLIT)
            new_oe._oe.RZ_SLIT = copy.deepcopy(self._oe.RZ_SLIT)
            new_oe._oe.SCR_NUMBER = copy.deepcopy(self._oe.SCR_NUMBER)
            new_oe._oe.SL_DIS = copy.deepcopy(self._oe.SL_DIS)
            new_oe._oe.THICK = copy.deepcopy(self._oe.THICK)
            new_oe._oe.CCC = copy.deepcopy(self._oe.CCC)

        return new_oe

    @classmethod
    def create_empty_oe(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=5
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC=2
        __shadow_oe._oe.F_SCREEN=0
        __shadow_oe._oe.N_SCREEN=0

        return __shadow_oe

    @classmethod
    def create_oe_from_file(cls, filename):
        __shadow_oe = cls.create_empty_oe()
        __shadow_oe._oe.load(filename)

        return __shadow_oe

    @classmethod
    def create_screen_slit(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=5
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC=2
        __shadow_oe._oe.F_SCREEN=1
        __shadow_oe._oe.N_SCREEN=1

        return __shadow_oe

    @classmethod
    def create_plane_mirror(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=5
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_spherical_mirror(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=1
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_toroidal_mirror(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=3
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_paraboloid_mirror(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=4
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_ellipsoid_mirror(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=2
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_hyperboloid_mirror(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=7
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_conic_coefficients_mirror(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=10
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_conic_coefficients_refractor(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=10
        __shadow_oe._oe.F_CRYSTAL = 0
        __shadow_oe._oe.F_REFRAC = 1

        return __shadow_oe

    @classmethod
    def create_plane_crystal(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=5
        __shadow_oe._oe.F_CRYSTAL = 1
        __shadow_oe._oe.FILE_REFL = bytes("", 'utf-8')
        __shadow_oe._oe.F_REFLECT = 0
        __shadow_oe._oe.F_BRAGG_A = 0
        __shadow_oe._oe.A_BRAGG = 0.0

        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_spherical_crystal(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=1
        __shadow_oe._oe.F_CRYSTAL = 1
        __shadow_oe._oe.FILE_REFL = bytes("", 'utf-8')
        __shadow_oe._oe.F_REFLECT = 0
        __shadow_oe._oe.F_BRAGG_A = 0
        __shadow_oe._oe.A_BRAGG = 0.0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_toroidal_crystal(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=3
        __shadow_oe._oe.F_CRYSTAL = 1
        __shadow_oe._oe.FILE_REFL = bytes("", 'utf-8')
        __shadow_oe._oe.F_REFLECT = 0
        __shadow_oe._oe.F_BRAGG_A = 0
        __shadow_oe._oe.A_BRAGG = 0.0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_paraboloid_crystal(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=4
        __shadow_oe._oe.F_CRYSTAL = 1
        __shadow_oe._oe.FILE_REFL = bytes("", 'utf-8')
        __shadow_oe._oe.F_REFLECT = 0
        __shadow_oe._oe.F_BRAGG_A = 0
        __shadow_oe._oe.A_BRAGG = 0.0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_ellipsoid_crystal(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=2
        __shadow_oe._oe.F_CRYSTAL = 1
        __shadow_oe._oe.FILE_REFL = bytes("", 'utf-8')
        __shadow_oe._oe.F_REFLECT = 0
        __shadow_oe._oe.F_BRAGG_A = 0
        __shadow_oe._oe.A_BRAGG = 0.0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_hyperboloid_crystal(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=7
        __shadow_oe._oe.F_CRYSTAL = 1
        __shadow_oe._oe.FILE_REFL = bytes("", 'utf-8')
        __shadow_oe._oe.F_REFLECT = 0
        __shadow_oe._oe.F_BRAGG_A = 0
        __shadow_oe._oe.A_BRAGG = 0.0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_conic_coefficients_crystal(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=10
        __shadow_oe._oe.F_CRYSTAL = 1
        __shadow_oe._oe.FILE_REFL = bytes("", 'utf-8')
        __shadow_oe._oe.F_REFLECT = 0
        __shadow_oe._oe.F_BRAGG_A = 0
        __shadow_oe._oe.A_BRAGG = 0.0
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_plane_grating(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=5
        __shadow_oe._oe.F_GRATING = 1
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_spherical_grating(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=1
        __shadow_oe._oe.F_GRATING = 1
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_toroidal_grating(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=3
        __shadow_oe._oe.F_GRATING = 1
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_paraboloid_grating(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=4
        __shadow_oe._oe.F_GRATING = 1
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_ellipsoid_grating(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=2
        __shadow_oe._oe.F_GRATING = 1
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_hyperboloid_grating(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=7
        __shadow_oe._oe.F_GRATING = 1
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_conic_coefficients_grating(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.OE())

        __shadow_oe._oe.FMIRR=10
        __shadow_oe._oe.F_GRATING = 1
        __shadow_oe._oe.F_REFRAC = 0

        return __shadow_oe

    @classmethod
    def create_ideal_lens(cls):
        __shadow_oe = ShadowOpticalElement(oe=Shadow.IdealLensOE())

        return __shadow_oe

    def add_acceptance_slits(self, auto_slit_width_xaxis, auto_slit_height_zaxis, auto_slit_center_xaxis, auto_slit_center_zaxis):
        n_screen = 1
        i_screen = numpy.zeros(10)  # after
        i_abs = numpy.zeros(10)
        i_slit = numpy.zeros(10)
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = ['', '', '', '', '', '', '', '', '', '']
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = ['', '', '', '', '', '', '', '', '', '']
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        i_screen[0] = 1
        i_slit[0] = 1

        rx_slit[0] = auto_slit_width_xaxis
        rz_slit[0] = auto_slit_height_zaxis
        cx_slit[0] = auto_slit_center_xaxis
        cz_slit[0] = auto_slit_center_zaxis

        self._oe.set_screens(n_screen,
                             i_screen,
                             i_abs,
                             sl_dis,
                             i_slit,
                             i_stop,
                             k_slit,
                             thick,
                             numpy.array(file_abs),
                             rx_slit,
                             rz_slit,
                             cx_slit,
                             cz_slit,
                             numpy.array(file_scr_ext))

class ShadowCompoundOpticalElement:
    def __init__(self, oe=None):
        self._oe = oe

    def set_oe(self, oe):
        self._oe = oe

    def duplicate(self):
        return ShadowCompoundOpticalElement(oe=self._oe.duplicate())

    @classmethod
    def create_compound_oe(cls, workspace_units_to_cm=1.0):
        return ShadowCompoundOpticalElement(oe=Shadow.CompoundOE(user_units_to_cm=workspace_units_to_cm))

    ####################################################################
    # FOR WEIRD BUG ON LINUX AND MAC - STRING NOT PROPERLY RETURNED BY BINDING
    ####################################################################
    def self_repair(self):
        if platform.system() == 'Linux' or platform.system() == 'Darwin':
            for index in range(0, self._oe.number_oe()):
                self._oe.list[index].FILE_SOURCE      = adjust_shadow_string(self._oe.list[index].FILE_SOURCE)
                self._oe.list[index].FILE_RIP         = adjust_shadow_string(self._oe.list[index].FILE_RIP)
                self._oe.list[index].FILE_REFL        = adjust_shadow_string(self._oe.list[index].FILE_REFL)
                self._oe.list[index].FILE_MIR         = adjust_shadow_string(self._oe.list[index].FILE_MIR)
                self._oe.list[index].FILE_ROUGH       = adjust_shadow_string(self._oe.list[index].FILE_ROUGH)
                self._oe.list[index].FILE_R_IND_OBJ   = adjust_shadow_string(self._oe.list[index].FILE_R_IND_OBJ)
                self._oe.list[index].FILE_R_IND_IMA   = adjust_shadow_string(self._oe.list[index].FILE_R_IND_IMA)
                self._oe.list[index].FILE_FAC         = adjust_shadow_string(self._oe.list[index].FILE_FAC)
                self._oe.list[index].FILE_SEGMENT     = adjust_shadow_string(self._oe.list[index].FILE_SEGMENT)
                self._oe.list[index].FILE_SEGP        = adjust_shadow_string(self._oe.list[index].FILE_SEGP)
                self._oe.list[index].FILE_KOMA        = adjust_shadow_string(self._oe.list[index].FILE_KOMA)
                self._oe.list[index].FILE_KOMA_CA     = adjust_shadow_string(self._oe.list[index].FILE_KOMA_CA)

                FILE_ABS = [adjust_shadow_string(self._oe.list[index].FILE_ABS[0]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[1]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[2]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[3]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[4]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[5]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[6]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[7]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[8]),
                            adjust_shadow_string(self._oe.list[index].FILE_ABS[9])]

                self._oe.list[index].FILE_ABS = numpy.array(FILE_ABS)

                FILE_SCR_EXT = [adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[0]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[1]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[2]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[3]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[4]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[5]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[6]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[7]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[8]),
                                adjust_shadow_string(self._oe.list[index].FILE_SCR_EXT[9])]

                self._oe.list[index].FILE_SCR_EXT = numpy.array(FILE_SCR_EXT)
