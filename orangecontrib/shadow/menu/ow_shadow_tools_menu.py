__author__ = 'labx'

import math
import os

import xraylib
from PyQt5 import QtWidgets
from oasys.menus.menu import OMenu
from orangecanvas.scheme.link import SchemeLink

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement
import orangecontrib.shadow.widgets.preprocessor.xsh_bragg as xsh_bragg
import orangecontrib.shadow.widgets.preprocessor.xsh_pre_mlayer as xsh_pre_mlayer
import orangecontrib.shadow.widgets.preprocessor.xsh_prerefl as xsh_prerefl
import orangecontrib.shadow.widgets.preprocessor.xsh_waviness as xsh_waviness
import orangecontrib.shadow.widgets.preprocessor.height_profile_simulator as height_profile_simulator
import orangecontrib.shadow.widgets.preprocessor.dabam_height_profile as dabam_height_profile

from orangecontrib.shadow.widgets.plots.ow_plot_xy import PlotXY
from orangecontrib.shadow.widgets.plots.ow_histogram import Histogram
from orangecontrib.shadow.widgets.plots.ow_info import Info
from orangecontrib.shadow.widgets.plots.ow_focnew import FocNew

from orangecontrib.shadow.util.shadow_objects import ShadowFile

class ShadowToolsMenu(OMenu):
    is_weird_shadow_bug_fixed = False

    OMIT_WIDGET = "OMIT_WIDGET"
    ABORT_IMPORT = "ABORT_IMPORT"

    default_dir = None

    def __init__(self):
        super().__init__(name="Shadow")

        self.openContainer()
        self.addContainer("Import")
        self.addSubMenu("Import Shadow File")
        self.addSubMenu("Import Shadow Workspace")
        self.closeContainer()
        self.openContainer()
        self.addContainer("Plotting")
        self.addSubMenu("Enable all the Plotting widgets")
        self.addSubMenu("Disable all the Plotting widgets")
        self.addSeparator()
        self.addSubMenu("Select Detailed Plots on all Source and O.E. widgets")
        self.addSubMenu("Select Preview Plots on all Source and O.E. widgets")
        self.addSubMenu("Select No Plots on all Source and O.E. widgets")
        self.addSeparator()
        self.addSubMenu("Clear all the cumulated plots")
        self.closeContainer()
        self.addSubMenu("Execute all the Preprocessor widgets")
        self.addSeparator()
        self.addSubMenu("Go to ShadowOui Tutorials Page")

    def fixWeirdShadowBug(self):
        if not self.is_weird_shadow_bug_fixed:
            try:
                xraylib.Refractive_Index_Re("LaB6", 10000, 4)
            except:
                pass

            self.is_weird_shadow_bug_fixed = True

    def executeAction_1(self, action):
        try:
            if self.default_dir == None:
                self.default_dir = os.getcwd()

            filenames = QtWidgets.QFileDialog.getOpenFileNames(None, 'Open Shadow OE file', self.default_dir, "SHADOW Input File (start.*)")[0]

            if not filenames:
                return

            if len(filenames) == 0:
                return

            self.default_dir = os.path.dirname(filenames[0])

            for filename in filenames:
                nodes, messages = self.manageShadowFile(filename)
                self.createLinks(nodes)

                if len(messages) > 0:
                    total_message = "Messages:\n\n"

                    for message in messages: total_message = total_message + message + "\n"
                    self.showWarningMessage(total_message)

        except Exception as exception:
            self.showWarningMessage(exception.args[0])

    def executeAction_2(self, action):
        try:
            shadow_system_filename = QtWidgets.QFileDialog.getOpenFileName(None, 'Select Shadow File: systemfile.dat', self.default_dir, "systemfile.dat")[0]

            if not shadow_system_filename:
                return

            self.default_dir = os.path.dirname(shadow_system_filename)

            if not os.path.exists(shadow_system_filename):
                self.showWarningMessage("File systemfile.dat not present in the directory: run SHADOW simulation first. Import Aborted.")
            else:
                shadow_system_file = open(shadow_system_filename, "r")

                rows = shadow_system_file.readlines()
                rows.insert(0, "start.00")

                nodes = []
                messages = []

                for filename in rows:
                    abort_import = False

                    filename_complete = os.path.join(self.default_dir, str(filename).strip())

                    if os.path.exists(filename_complete):
                        print("filename_complete", filename_complete)

                        tmp_nodes, tmp_messages = self.manageShadowFile(filename_complete)

                        messages = messages + tmp_messages

                        for node in tmp_nodes:
                            if not (isinstance(node, str) and node == ShadowToolsMenu.ABORT_IMPORT):
                                nodes.append(node)
                            else:
                                abort_import = True
                                break

                        if abort_import: break
                    else:
                        ret = self.showConfirmMessage("File " + str(filename).strip() + " doesn't exist")

                        if ret == QtWidgets.QMessageBox.No: break
                        else:
                            nodes.append(ShadowToolsMenu.OMIT_WIDGET)
                            messages.append("File " + str(filename).strip() + " doesn't exist")

                self.createLinks(nodes)

            if len(messages) > 0:
                total_message = "Messages:\n\n"

                for message in messages: total_message = total_message + message + "\n"

                QtWidgets.QMessageBox.warning(None, "Warning",
                    total_message,
                    QtWidgets.QMessageBox.Ok)

        except Exception as exception:
            QtWidgets.QMessageBox.critical(None, "Error",
                exception.args[0],
                QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def __set_preprocessor_enabled(self, enabled):
        try:
            for link in self.canvas_main_window.current_document().scheme().links:
                if link.enabled != enabled:
                    widget = self.canvas_main_window.current_document().scheme().widget_for_node(link.sink_node)
                    if isinstance(widget, (PlotXY, Histogram, FocNew, Info)): link.set_enabled(enabled)
        except Exception as exception:
            super(ShadowToolsMenu, self).showCriticalMessage(message=exception.args[0])

    #ENABLE PLOTS
    def executeAction_3(self, action): self.__set_preprocessor_enabled(True)

    def executeAction_4(self, action): self.__set_preprocessor_enabled(False)

    def __set_plot_visibility(self, vt, pg):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, AutomaticElement):
                    if hasattr(widget, "view_type") and hasattr(widget, "set_PlotQuality"):
                        widget.view_type = vt
                        widget.set_PlotQuality()
                    if hasattr(widget, "plot_graph") and hasattr(widget, "set_PlotGraphs"):
                        widget.plot_graph = pg
                        widget.set_PlotGraphs()
        except Exception as exception:
            super(ShadowToolsMenu, self).showCriticalMessage(message=exception.args[0])

    def executeAction_5(self, action): self.__set_plot_visibility(0, 1)

    def executeAction_6(self, action): self.__set_plot_visibility(1, 1)

    def executeAction_7(self, action): self.__set_plot_visibility(2, 0)

    def executeAction_8(self, action):
        try:
            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, AutomaticElement):
                    if hasattr(widget, "clearResults"):
                        widget.clearResults(interactive=False)
        except Exception as exception:
            QtWidgets.QMessageBox.critical(None, "Error",
                exception.args[0],
                QtWidgets.QMessageBox.Ok)

    def executeAction_9(self, action):
        try:
            self.fixWeirdShadowBug()

            for node in self.canvas_main_window.current_document().scheme().nodes:
                widget = self.canvas_main_window.current_document().scheme().widget_for_node(node)

                if isinstance(widget, xsh_bragg.OWxsh_bragg) or \
                        isinstance(widget, xsh_prerefl.OWxsh_prerefl) or \
                        isinstance(widget, xsh_pre_mlayer.OWxsh_pre_mlayer):
                    widget.compute()
                elif isinstance(widget, xsh_waviness.OWxsh_waviness):
                    widget.calculate_waviness(not_interactive_mode=True)
                    widget.generate_waviness_file(not_interactive_mode=True)
                elif isinstance(widget, height_profile_simulator.OWheight_profile_simulator):
                    widget.calculate_heigth_profile(not_interactive_mode=True)
                    widget.generate_heigth_profile_file(not_interactive_mode=True)
                elif isinstance(widget, dabam_height_profile.OWdabam_height_profile):
                    QtWidgets.QMessageBox.warning(None, "Warning",
                        "DABAM Widget must be executed interactively",
                        QtWidgets.QMessageBox.Ok)

        except Exception as exception:
            QtWidgets.QMessageBox.critical(None, "Error",
                exception.args[0],
                QtWidgets.QMessageBox.Ok)


    def executeAction_10(self, action):
        try:
            import webbrowser
            webbrowser.open("https://github.com/srio/ShadowOui-Tutorial")
        except Exception as exception:
            QtWidgets.QMessageBox.critical(None, "Error",
                exception.args[0],
                QtWidgets.QMessageBox.Ok)

    ###############################################################
    #
    # SHADOW FILE MANAGEMENT
    #
    ###############################################################

    def manageShadowFile(self, filename):
        shadow_file, type = ShadowFile.readShadowFile(filename)
        widget_name, first_messages = self.getWidgetName(shadow_file, type)
        widget_desc = self.getWidgetDesc(widget_name)

        if isinstance(widget_desc, str):
            first_messages.append("File " + os.path.basename(filename).strip() + " not imported: element not valid.")
            return [widget_desc], first_messages
        else:
            if type == ShadowFile.SOURCE:
                nodes, messages = self.createNewNodeAndWidget(shadow_file, widget_desc)
            elif type == ShadowFile.OE:
                nodes, messages = self.analyzeScreenSlit(shadow_file, widget_desc)

            return nodes, first_messages + messages


    #################################################################
    #
    # NAME FACTORY
    #
    #################################################################


    def getWidgetName(self, shadow_file, type):
        widget_name = ""
        messages = []
        try:
            if type == ShadowFile.SOURCE:
                widget_name = "orangecontrib.shadow.widgets.sources."

                if int(shadow_file.getProperty("F_WIGGLER")) == 0:
                    if int(shadow_file.getProperty("FDISTR")) == 4 or int(shadow_file.getProperty("FDISTR")) == 6:
                        widget_name = widget_name + "ow_bending_magnet.BendingMagnet"
                    else:
                        widget_name = widget_name + "ow_geometrical_source.GeometricalSource"
                        if int(shadow_file.getProperty("FGRID")) > 0:
                            messages.append("Geometrical Source: Sampling different from Random/Random are no more supported and switched to Random/Random.\nCheck the generated widget.")
                elif int(shadow_file.getProperty("F_WIGGLER")) == 1:
                    widget_name = widget_name + "ow_wiggler.Wiggler"
                    message = "Wiggler Source: Simulation algorithm has been rewritten, results could be different from the original ones."
                    message = message + "\n\nParameters to be set manually (not contained in the start.00 file): "
                    message = message + "\n'ID wavelength',\n'K value',\n'Number of Periods'\n'Energy Minimum',\n'Energy Maximum'"
                    if int(shadow_file.getProperty("F_BOUND_SOUR")) == 2:
                        message = message + "\n\nParameters to be checked, with new input setup: "
                        message = message + "\n'Optimize Source' with 'Slit/Acceptance' (input file is not needed anymore)"
                    messages.append(message)
                else:
                    raise Exception("Undulator Source Type not supported yet")
            elif type == ShadowFile.OE:
                widget_name = "orangecontrib.shadow.widgets.optical_elements."

                fmirr = int(shadow_file.getProperty("FMIRR"))

                if int(shadow_file.getProperty("F_CRYSTAL")) == 0 and int(shadow_file.getProperty("F_GRATING")) == 0: # MIRRORS
                    if int(shadow_file.getProperty("F_REFRAC")) != 0:
                        if fmirr == 5:
                            widget_name = "orangecontrib.shadow.widgets.special_elements.ow_empty_element.EmptyElement"
                        elif fmirr == 10:
                            widget_name = "orangecontrib.shadow.widgets.special_elements.ow_conic_coefficients_refractor.ConicCoefficientsRefractor"
                        else:
                            raise Exception("Only Refractor OE Type with conic coefficients are supported")
                    else:
                        if  fmirr == 1:
                            widget_name = widget_name + "ow_spheric_mirror.SphericMirror"
                        elif fmirr == 2:
                            widget_name = widget_name + "ow_ellipsoid_mirror.EllipsoidMirror"
                        elif fmirr == 3:
                            widget_name = widget_name + "ow_toroidal_mirror.ToroidalMirror"
                        elif fmirr == 4:
                            widget_name = widget_name + "ow_paraboloid_mirror.ParaboloidMirror"
                        elif fmirr == 5:
                            widget_name = widget_name + "ow_plane_mirror.PlaneMirror"
                        elif fmirr == 6:
                            raise Exception("Unsupported SHADOW element: FMIRR=6")
                        elif fmirr == 7:
                            widget_name = widget_name + "ow_hyperboloid_mirror.HyperboloidMirror"
                        elif fmirr == 8:
                            raise Exception("Unsupported SHADOW element: FMIRR=8")
                        elif fmirr == 9:
                            raise Exception("Unsupported SHADOW element: FMIRR=9")
                        elif fmirr == 10:
                            widget_name = widget_name + "ow_conic_coefficients_mirror.ConicCoefficientsMirror"
                elif int(shadow_file.getProperty("F_CRYSTAL")) == 1: # CRYSTAL
                    if  fmirr == 1:
                        widget_name = widget_name + "ow_spheric_crystal.SphericCrystal"
                    elif fmirr == 2:
                        widget_name = widget_name + "ow_ellipsoid_crystal.EllipsoidCrystal"
                    elif fmirr == 3:
                        widget_name = widget_name + "ow_toroidal_crystal.ToroidalCrystal"
                    elif fmirr == 4:
                        widget_name = widget_name + "ow_paraboloid_crystal.ParaboloidCrystal"
                    elif fmirr == 5:
                        widget_name = widget_name + "ow_plane_crystal.PlaneCrystal"
                    elif fmirr == 6:
                        raise Exception("Unsupported SHADOW element: FMIRR=6")
                    elif fmirr == 7:
                        widget_name = widget_name + "ow_hyperboloid_crystal.HyperboloidCrystal"
                    elif fmirr == 8:
                        raise Exception("Unsupported SHADOW element: FMIRR=8")
                    elif fmirr == 9:
                        raise Exception("Unsupported SHADOW element: FMIRR=9")
                    elif fmirr == 10:
                        widget_name = widget_name + "ow_conic_coefficients_crystal.ConicCoefficientsCrystal"
                elif int(shadow_file.getProperty("F_GRATING")) == 1: # GRATING
                    if  fmirr == 1:
                        widget_name = widget_name + "ow_spheric_grating.SphericGrating"
                    elif fmirr == 2:
                        widget_name = widget_name + "ow_ellipsoid_grating.EllipsoidGrating"
                    elif fmirr == 3:
                        widget_name = widget_name + "ow_toroidal_grating.ToroidalGrating"
                    elif fmirr == 4:
                        widget_name = widget_name + "ow_paraboloid_grating.ParaboloidGrating"
                    elif fmirr == 5:
                        widget_name = widget_name + "ow_plane_grating.PlaneGrating"
                    elif fmirr == 6:
                        raise Exception("Unsupported SHADOW element: FMIRR=6")
                    elif fmirr == 7:
                        widget_name = widget_name + "ow_hyperboloid_grating.HyperboloidGrating"
                    elif fmirr == 8:
                        raise Exception("Unsupported SHADOW element: FMIRR=8")
                    elif fmirr == 9:
                        raise Exception("Unsupported SHADOW element: FMIRR=9")
                    elif fmirr == 10:
                        widget_name = widget_name + "ow_conic_coefficients_grating.ConicCoefficientsGrating"
            else:
                raise Exception("Unrecognized SHADOW element")
        except Exception as exception:
            ret = self.showConfirmMessage(exception.args[0])

            if ret == QtWidgets.QMessageBox.No: widget_name = ShadowToolsMenu.ABORT_IMPORT
            else: widget_name = ShadowToolsMenu.OMIT_WIDGET

        return widget_name, messages

    def showConfirmMessage(self, message):
        return super(ShadowToolsMenu, self).showConfirmMessage(message, informative_text="Element will be omitted.\nDo you want to continue importing procedure (a broken link will appear)?")

    #################################################################
    #
    # SCHEME MANAGEMENT
    #
    #################################################################

    def createLinks(self, nodes):
        super(ShadowToolsMenu, self).createLinks(nodes, excluded_names=[ShadowToolsMenu.OMIT_WIDGET], source_channel="Beam", sink_channel="Input Beam")

    def getWidgetDesc(self, widget_name):
        return super(ShadowToolsMenu, self).getWidgetDesc(widget_name, excluded_names=[ShadowToolsMenu.OMIT_WIDGET, ShadowToolsMenu.ABORT_IMPORT])

    def getWidgetDescFromShadowFile(self, filename):
        shadow_file, type = ShadowFile.readShadowFile(filename)

        widget_name, messages = self.getWidgetName(shadow_file, type)
        return self.getWidgetDesc(widget_name), messages

    def createNewNodeAndWidget(self, shadow_file, widget_desc):
        messages = []
        nodes = []

        try:
            nodes.append(self.createNewNode(widget_desc))
            widget = self.getWidgetFromNode(nodes[0])
            widget.deserialize(shadow_file)
        except Exception as exception:
            messages.append(exception.args[0])

        return nodes, messages

    #################################################################
    #
    # SCREEN/SLITS TREATMENT
    #
    #################################################################

    def analyzeScreenSlit(self, shadow_file, widget_desc):
        nodes = []
        messages = []

        try:
            has_screen_slits = int(shadow_file.getProperty("F_SCREEN")) == 1
            has_exit_slit = int(shadow_file.getProperty("FSLIT")) == 1

            if not has_screen_slits and not has_exit_slit:
                new_nodes, new_messages = self.createNewNodeAndWidget(shadow_file, widget_desc)

                nodes = nodes + new_nodes
                messages = messages + new_messages
            else:
                # ORIGINAL VALUES
                original_source_plane_distance = float(shadow_file.getProperty("T_SOURCE"))
                original_image_plane_distance = float(shadow_file.getProperty("T_IMAGE"))

                n_screen = int(shadow_file.getProperty("N_SCREEN"))

                slits_screen_before = []
                slits_screen_after = []

                mirror_orientation_angle = int(float(shadow_file.getProperty("ALPHA"))/90)

                for index in range(n_screen):
                    try:
                        slit = ScreenSlit()
                        slit.deserialize(shadow_file, index)

                        if slit.aperturing == 0 and slit.absorption == 0: # EMPTY SCREENS ARE OMITTED:
                            position = "AFTER"
                            if slit.before == 1:
                                position = "BEFORE"
                            messages.append("EMPTY SCREEN IN O.E. " + widget_desc.name + " OMITTED - DISTANCE: " + str(slit.absolute_distance_from_mirror) + " cm " + position + " OPTICAL ELEMENT")
                        else:
                            if slit.before == 0: # AFTER
                                if slit.absolute_distance_from_mirror > original_image_plane_distance:
                                    messages.append("SCREEN/SLITS AFTER O.E. " + widget_desc.name + " REFUSED - ABSOLUTE DISTANCE FROM MIRROR > O.E. IMAGE PLANE DISTANCE")
                                    continue

                                if len(slits_screen_after) == 0:
                                    slits_screen_after.append(slit)
                                else:
                                    inserted = False

                                    for index in range(len(slits_screen_after)):
                                        if slit.absolute_distance_from_mirror < slits_screen_after[index].absolute_distance_from_mirror: # CRESCENT
                                            slits_screen_after.insert(index, slit)
                                            inserted = True
                                            break

                                    if not inserted: slits_screen_after.append(slit)
                            elif slit.before == 1: # BEFORE
                                if slit.absolute_distance_from_mirror > original_source_plane_distance:
                                    messages.append("SCREEN/SLITS BEFORE O.E. " + widget_desc.name + " REFUSED - ABSOLUTE DISTANCE FROM MIRROR > O.E. SOURCE PLANE DISTANCE")
                                    continue

                                if mirror_orientation_angle == 1 or mirror_orientation_angle == 3:
                                    #90 or 270 -> x must be inverted with z, slits before has the same reference of previous widget
                                    if slit.aperture_shape == 2:
                                        messages.append("SCREEN/SLITS BEFORE O.E. " + widget_desc.name + " WITH EXTERNAL FILE FOR COORDINATES - OE HAS 90 OR 270deg ORIENTATION ANGLE, COORDINATES SHOULD BE INVERTED")

                                if len(slits_screen_before) == 0:
                                    slits_screen_before.append(slit)
                                else:
                                    inserted = False

                                    for index in range(len(slits_screen_before)):
                                        if slit.absolute_distance_from_mirror > slits_screen_before[index].absolute_distance_from_mirror: # DECRESCENT
                                            slits_screen_before.insert(index, slit)
                                            inserted = True
                                            break

                                    if not inserted: slits_screen_before.append(slit)

                    except Exception as exception:
                        messages.append("Slit not created, because of an exception: " + exception.args[0])


                if has_exit_slit:
                    try:
                        exit_slit = ScreenSlit()
                        exit_slit.aperturing=1
                        exit_slit.aperture_shape=0
                        exit_slit.slit_width_xaxis = float(shadow_file.getProperty("SLLEN"))
                        exit_slit.slit_height_zaxis = float(shadow_file.getProperty("SLWID"))*math.cos(math.radians(float(shadow_file.getProperty("SLTILT"))))
                        exit_slit.absolute_distance_from_mirror = original_image_plane_distance

                        slits_screen_after.append(exit_slit)
                    except Exception as exception:
                        messages.append("Exit Slit not created, because of an exception: " + exception.args[0])

                new_widget_source_plane_distance = original_source_plane_distance
                new_widget_image_plane_distance = original_image_plane_distance

                #BEFORE
                total_screen_before = len(slits_screen_before)

                for index in range(0, total_screen_before):
                    slit_node = self.getNewScreenSlitNode()
                    slit_widget = self.getWidgetFromNode(slit_node)

                    if (index == 0):
                        slit_widget.source_plane_distance = original_source_plane_distance - slits_screen_before[index].absolute_distance_from_mirror
                    else:
                        slit_widget.source_plane_distance = (slits_screen_before[index-1].absolute_distance_from_mirror - slits_screen_before[index].absolute_distance_from_mirror)/2

                    if index == total_screen_before-1:
                        slit_widget.image_plane_distance = slits_screen_before[index].absolute_distance_from_mirror/2
                        new_widget_source_plane_distance = slits_screen_before[index].absolute_distance_from_mirror/2
                    else:
                        slit_widget.image_plane_distance = (slits_screen_before[index].absolute_distance_from_mirror - slits_screen_before[index+1].absolute_distance_from_mirror)/2

                    slit_widget.absorption = slits_screen_before[index].absorption
                    slit_widget.aperturing = slits_screen_before[index].aperturing
                    slit_widget.open_slit_solid_stop = slits_screen_before[index].open_slit_solid_stop
                    slit_widget.aperture_shape = slits_screen_before[index].aperture_shape
                    slit_widget.thickness = slits_screen_before[index].thickness
                    slit_widget.opt_const_file_name = slits_screen_before[index].opt_const_file_name

                    if mirror_orientation_angle == 1 or mirror_orientation_angle == 3:
                        #90 or 270 -> x must be inverted with z, slits before has the same reference of previous widget
                        slit_widget.slit_width_xaxis = slits_screen_before[index].slit_height_zaxis
                        slit_widget.slit_height_zaxis = slits_screen_before[index].slit_width_xaxis
                        slit_widget.slit_center_xaxis  = slits_screen_before[index].slit_center_zaxis
                        slit_widget.slit_center_zaxis  = slits_screen_before[index].slit_center_xaxis
                    else:
                        slit_widget.slit_width_xaxis = slits_screen_before[index].slit_width_xaxis
                        slit_widget.slit_height_zaxis = slits_screen_before[index].slit_height_zaxis
                        slit_widget.slit_center_xaxis  = slits_screen_before[index].slit_center_xaxis
                        slit_widget.slit_center_zaxis  = slits_screen_before[index].slit_center_zaxis

                    slit_widget.external_file_with_coordinate = slits_screen_before[index].external_file_with_coordinate

                    slit_widget.setupUI()

                    nodes.append(slit_node)

                widget_node = self.createNewNode(widget_desc)
                nodes.append(widget_node)

                #AFTER
                total_screen_after = len(slits_screen_after)

                for index in range(0, total_screen_after):
                    slit_node = self.getNewScreenSlitNode()
                    slit_widget = self.getWidgetFromNode(slit_node)

                    if (index == 0):
                        slit_widget.source_plane_distance = slits_screen_after[index].absolute_distance_from_mirror/2
                        new_widget_image_plane_distance = slits_screen_after[index].absolute_distance_from_mirror/2
                    else:
                        slit_widget.source_plane_distance = (slits_screen_after[index].absolute_distance_from_mirror - slits_screen_after[index-1].absolute_distance_from_mirror)/2

                    if index == total_screen_after-1:
                        slit_widget.image_plane_distance =  original_image_plane_distance - slits_screen_after[index].absolute_distance_from_mirror
                    else:
                        slit_widget.image_plane_distance = (slits_screen_after[index+1].absolute_distance_from_mirror - slits_screen_after[index].absolute_distance_from_mirror)/2

                    slit_widget.absorption = slits_screen_after[index].absorption
                    slit_widget.aperturing = slits_screen_after[index].aperturing
                    slit_widget.open_slit_solid_stop = slits_screen_after[index].open_slit_solid_stop
                    slit_widget.aperture_shape = slits_screen_after[index].aperture_shape
                    slit_widget.thickness = slits_screen_after[index].thickness
                    slit_widget.opt_const_file_name = slits_screen_after[index].opt_const_file_name
                    slit_widget.slit_width_xaxis = slits_screen_after[index].slit_width_xaxis
                    slit_widget.slit_height_zaxis = slits_screen_after[index].slit_height_zaxis
                    slit_widget.external_file_with_coordinate = slits_screen_after[index].external_file_with_coordinate
                    slit_widget.slit_center_xaxis  = slits_screen_after[index].slit_center_xaxis
                    slit_widget.slit_center_zaxis  = slits_screen_after[index].slit_center_zaxis

                    slit_widget.setupUI()

                    nodes.append(slit_node)

                widget = self.getWidgetFromNode(widget_node)
                widget.deserialize(shadow_file)
                widget.source_plane_distance = new_widget_source_plane_distance
                widget.image_plane_distance = new_widget_image_plane_distance

        except Exception as exception:
            messages.append("O.E. not loaded because of an exception: " + exception.args[0])

        return nodes, messages

    def getNewScreenSlitNode(self):
        return self.createNewNode(self.getWidgetDesc("orangecontrib.shadow.widgets.optical_elements.ow_screen_slits.ScreenSlits"))

class ScreenSlit:
    before = 0
    absorption = 0
    aperturing = 0
    open_slit_solid_stop = 0
    aperture_shape = 0
    thickness = 0
    opt_const_file_name = ""
    slit_width_xaxis = 0
    slit_height_zaxis = 0
    absolute_distance_from_mirror = 0
    external_file_with_coordinate = ""
    slit_center_xaxis = 0
    slit_center_zaxis = 0  
    
    def __init__(self, before = 0,
                       absorption = 0,
                       aperturing = 0,
                       open_slit_solid_stop = 0,
                       aperture_shape = 0,
                       thickness = 0,
                       opt_const_file_name = "",
                       slit_width_xaxis = 0,
                       slit_height_zaxis = 0,
                       absolute_distance_from_mirror = 0,
                       external_file_with_coordinate = "",
                       slit_center_xaxis = 0,
                       slit_center_zaxis = 0 ):
        self.before = before
        self.absorption    = absorption   
        self.aperturing   = aperturing  
        self.open_slit_solid_stop   = open_slit_solid_stop  
        self.aperture_shape   = aperture_shape  
        self.thickness    = thickness   
        self.opt_const_file_name = opt_const_file_name
        self.slit_width_xaxis  = slit_width_xaxis 
        self.slit_height_zaxis  = slit_height_zaxis 
        self.absolute_distance_from_mirror   = absolute_distance_from_mirror  
        self.external_file_with_coordinate = external_file_with_coordinate
        self.slit_center_xaxis  = slit_center_xaxis 
        self.slit_center_zaxis  = slit_center_zaxis

    def deserialize(self, shadow_file, index):
        self.before = int(shadow_file.getProperty("I_SCREEN(" + str(index+1) + ")"))
        self.absorption    = int(shadow_file.getProperty("I_ABS(" + str(index+1) + ")"))
        self.aperturing   = int(shadow_file.getProperty("I_SLIT(" + str(index+1) + ")"))
        self.open_slit_solid_stop   = int(shadow_file.getProperty("I_STOP(" + str(index+1) + ")"))
        self.aperture_shape   = int(shadow_file.getProperty("K_SLIT(" + str(index+1) + ")"))
        self.thickness    = float(shadow_file.getProperty("THICK(" + str(index+1) + ")"))
        self.opt_const_file_name = str(shadow_file.getProperty("FILE_ABS(" + str(index+1) + ")"))
        self.slit_width_xaxis  = float(shadow_file.getProperty("RX_SLIT(" + str(index+1) + ")"))
        self.slit_height_zaxis  = float(shadow_file.getProperty("RZ_SLIT(" + str(index+1) + ")"))
        self.absolute_distance_from_mirror   = float(shadow_file.getProperty("SL_DIS(" + str(index+1) + ")"))
        self.external_file_with_coordinate = str(shadow_file.getProperty("FILE_SCR_EXT(" + str(index+1) + ")"))
        self.slit_center_xaxis  = float(shadow_file.getProperty("CX_SLIT(" + str(index+1) + ")"))
        self.slit_center_zaxis  = float(shadow_file.getProperty("CZ_SLIT(" + str(index+1) + ")"))

