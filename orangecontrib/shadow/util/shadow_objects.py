
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
                                merged_history_element._input_beam = ShadowBeam.mergeBeams(history_element_1._input_beam, history_element_2._input_beam, which_flux, merge_history=0)
                            else:
                                merged_history_element._input_beam = ShadowBeam.mergeBeams(history_element_1._input_beam, history_element_2._input_beam, which_flux, merge_history=1)
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
    def traceFromOE(cls, input_beam, shadow_oe, write_start_file=0, write_end_file=0, history=True, widget_class_name=None, recursive_history=True):
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
                                                                     input_beam=input_beam.duplicate(history=recursive_history),
                                                                     shadow_oe_start=history_shadow_oe_start,
                                                                     shadow_oe_end=history_shadow_oe_end,
                                                                     widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number]=ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                      input_beam=input_beam.duplicate(history=recursive_history),
                                                                      shadow_oe_start=history_shadow_oe_start,
                                                                      shadow_oe_end=history_shadow_oe_end,
                                                                      widget_class_name=widget_class_name)

        return __shadow_beam

    @classmethod
    def traceIdealLensOE(cls, input_beam, shadow_oe, history=True, widget_class_name=None, recursive_history=True):
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
                                                                     input_beam=input_beam.duplicate(history=recursive_history),
                                                                     shadow_oe_start=history_shadow_oe_start,
                                                                     shadow_oe_end=history_shadow_oe_end,
                                                                     widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number]=ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                                        input_beam=input_beam.duplicate(history=recursive_history),
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
                            widget_class_name=None,
                            recursive_history=True):
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
                                                                     input_beam=input_beam.duplicate(history=recursive_history),
                                                                     shadow_oe_start=history_shadow_oe_start,
                                                                     shadow_oe_end=history_shadow_oe_end,
                                                                     widget_class_name=widget_class_name))
                else:
                    __shadow_beam.history[__shadow_beam._oe_number] = ShadowOEHistoryItem(oe_number=__shadow_beam._oe_number,
                                                                                          input_beam=input_beam.duplicate(history=recursive_history),
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
        new_src.src = self.src.duplicate()

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
        if isinstance(self._oe, Shadow.IdealLensOE): new_oe = ShadowOpticalElement.create_ideal_lens()
        else:                                        new_oe = ShadowOpticalElement.create_empty_oe()

        new_oe._oe = self._oe.duplicate()

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
