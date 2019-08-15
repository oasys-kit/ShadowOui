import sys
import time
import numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

from silx.gui.plot.ScatterView import ScatterView
from silx.gui.colors import Colormap


try:
    import OpenGL
    has_opengl = True
except:
    has_opengl = False

class PlotScatter(AutomaticElement):

    name = "Plot Scatter"
    description = "Display Data Tools: Plot XY"
    icon = "icons/plot_scatter.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 3
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("Input Beam (color)" , ShadowBeam, "setBeamForColor" )]

    IMAGE_WIDTH = 878
    IMAGE_HEIGHT = 635

    want_main_area=1
    plot_canvas=None
    input_beam=None
    input_beam_color = None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    x_column_index=Setting(0)
    y_column_index=Setting(2)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0.0)

    y_range=Setting(0)
    y_range_min=Setting(0.0)
    y_range_max=Setting(0.0)

    color_source = Setting(0) # 0 = same beam , 1 = specific beam
    color_column = Setting(11)
    weight_transparency = Setting(0)


    rays=Setting(1)

    title=Setting("X,Z")

    is_conversion_active = Setting(1)

    if has_opengl:
        backend = 1
    else:
        backend = 0

    def __init__(self):
        super().__init__()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        gui.button(button_box, self, "Refresh", callback=self.plot_results, height=45)


        gui.separator(self.controlArea, 10)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        # graph tab
        tab_set = oasysgui.createTabPage(self.tabs_setting, "Plot Settings")

        screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical", height=130)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                            items=["On Image Plane", "Retraced"], labelWidth=260,
                                            callback=self.set_ImagePlane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)
        self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=False, orientation="vertical", height=50)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250,
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_ImagePlane()

        general_box = oasysgui.widgetBox(tab_set, "Variables Settings", addSpace=True, orientation="vertical", height=360)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="X Column",labelWidth=70,
                                     items=["1: X",
                                            "2: Y",
                                            "3: Z",
                                            "4: X'",
                                            "5: Y'",
                                            "6: Z'",
                                            "7: E\u03c3 X",
                                            "8: E\u03c3 Y",
                                            "9: E\u03c3 Z",
                                            "10: Ray Flag",
                                            "11: Energy",
                                            "12: Ray Index",
                                            "13: Optical Path",
                                            "14: Phase \u03c3",
                                            "15: Phase \u03c0",
                                            "16: E\u03c0 X",
                                            "17: E\u03c0 Y",
                                            "18: E\u03c0 Z",
                                            "19: Wavelength",
                                            "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                            "21: Theta (angle from Y axis)",
                                            "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                            "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                            "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                            "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                            "26: |K|",
                                            "27: K X",
                                            "28: K Y",
                                            "29: K Z",
                                            "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                            "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                            "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                            "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                            "34: Power = Intensity * Energy",
                                     ],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "x_range", label="X Range", labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_XRange, sendSelectedValue=False, orientation="horizontal")

        self.xrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.xrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.xrange_box, self, "x_range_min", "X min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.xrange_box, self, "x_range_max", "X max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_XRange()

        self.y_column = gui.comboBox(general_box, self, "y_column_index", label="Y Column",labelWidth=70,
                                     items=["1: X",
                                            "2: Y",
                                            "3: Z",
                                            "4: X'",
                                            "5: Y'",
                                            "6: Z'",
                                            "7: E\u03c3 X",
                                            "8: E\u03c3 Y",
                                            "9: E\u03c3 Z",
                                            "10: Ray Flag",
                                            "11: Energy",
                                            "12: Ray Index",
                                            "13: Optical Path",
                                            "14: Phase \u03c3",
                                            "15: Phase \u03c0",
                                            "16: E\u03c0 X",
                                            "17: E\u03c0 Y",
                                            "18: E\u03c0 Z",
                                            "19: Wavelength",
                                            "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                            "21: Theta (angle from Y axis)",
                                            "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                            "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                            "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                            "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                            "26: |K|",
                                            "27: K X",
                                            "28: K Y",
                                            "29: K Z",
                                            "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                            "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                            "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                            "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                            "34: Power = Intensity * Energy",
                                     ],

                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "y_range", label="Y Range",labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_YRange, sendSelectedValue=False, orientation="horizontal")

        self.yrange_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)
        self.yrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", height=100)

        oasysgui.lineEdit(self.yrange_box, self, "y_range_min", "Y min", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_range_max", "Y max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_YRange()

        gui.comboBox(general_box, self, "color_source", label="Color source", labelWidth=100,
                     items=["The same beam",
                            "Specific beam"],sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "color_column", label="Color", labelWidth=70,
                                         items=["0: NONE",
                                                "1: X",
                                                "2: Y",
                                                "3: Z",
                                                "4: X'",
                                                "5: Y'",
                                                "6: Z'",
                                                "7: E\u03c3 X",
                                                "8: E\u03c3 Y",
                                                "9: E\u03c3 Z",
                                                "10: Ray Flag",
                                                "11: Energy",
                                                "12: Ray Index",
                                                "13: Optical Path",
                                                "14: Phase \u03c3",
                                                "15: Phase \u03c0",
                                                "16: E\u03c0 X",
                                                "17: E\u03c0 Y",
                                                "18: E\u03c0 Z",
                                                "19: Wavelength",
                                                "20: R = sqrt(X\u00b2 + Y\u00b2 + Z\u00b2)",
                                                "21: Theta (angle from Y axis)",
                                                "22: Magnitude = |E\u03c3| + |E\u03c0|",
                                                "23: Total Intensity = |E\u03c3|\u00b2 + |E\u03c0|\u00b2",
                                                "24: \u03a3 Intensity = |E\u03c3|\u00b2",
                                                "25: \u03a0 Intensity = |E\u03c0|\u00b2",
                                                "26: |K|",
                                                "27: K X",
                                                "28: K Y",
                                                "29: K Z",
                                                "30: S0-stokes = |E\u03c0|\u00b2 + |E\u03c3|\u00b2",
                                                "31: S1-stokes = |E\u03c0|\u00b2 - |E\u03c3|\u00b2",
                                                "32: S2-stokes = 2|E\u03c3||E\u03c0|cos(Phase \u03c3-Phase \u03c0)",
                                                "33: S3-stokes = 2|E\u03c3||E\u03c0|sin(Phase \u03c3-Phase \u03c0)",
                                                "34: Power = Intensity * Energy",
                                         ],
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "weight_transparency", label="Transparency (Weight=col23)", labelWidth=250,
                                         items=["No","Yes"],
                                         sendSelectedValue=False, orientation="horizontal")


        gui.comboBox(general_box, self, "rays", label="Rays", labelWidth=250,
                                     items=["All rays",
                                            "Good Only",
                                            "Lost Only"],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "is_conversion_active", label="Is U.M. conversion active", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "backend", label="render backend", labelWidth=250,
                                         items=["matplotlib", "gl"],
                                         sendSelectedValue=False, orientation="horizontal")


        # self.set_autosave()

        self.main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(self.main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(self.main_tabs, "Output")

        self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)


    def set_autosave(self):
        self.autosave_box_1.setVisible(self.autosave==1)
        self.autosave_box_2.setVisible(self.autosave==0)

        self.cb_autosave_partial_results.setEnabled(self.autosave==1 and self.keep_result==1)

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def set_YRange(self):
        self.yrange_box.setVisible(self.y_range == 1)
        self.yrange_box_empty.setVisible(self.y_range == 0)

    def selectAutosaveFile(self):
        self.le_autosave_file_name.setText(oasysgui.selectFileFromDialog(self, self.autosave_file_name, "Select File", file_extension_filter="HDF5 Files (*.hdf5 *.h5 *.hdf)"))


    def replace_fig(self, beam, var_x, var_y, var_color, title, xtitle, ytitle, xrange, yrange, nolost, xum, yum):

        if self.backend == 0:
            use_backend = 'matplotlib'
        elif self.backend == 1:
            if not has_opengl:
                QMessageBox.information(self, "Plot Scatter Information",
                        "It seems that PyOpenGL is not installed in your system.\n Install it to get much faster scatter plots.",
                        QMessageBox.Ok)
                use_backend = 'matplotlib'
                self.backend = 0
            else:
                use_backend = 'gl'

        if self.plot_canvas is None:
            self.plot_canvas = ScatterView(backend=use_backend)
        else:
            self.image_box.layout().removeWidget(self.plot_canvas)
            self.plot_canvas = None
            self.plot_canvas = ScatterView(backend=use_backend)

        if self.color_column != 0:
            if self.color_source == 0:
                color_array = beam.getshonecol(var_color, nolost=nolost)
            else:
                if self.input_beam_color is None:
                    raise Exception("Undefined specific beam for color")

                color_array = self.input_beam_color._beam.getshonecol(var_color, nolost=False)
                if nolost == 0:
                    pass
                elif nolost == 1:
                    color_good_flags = beam.getshonecol(10, nolost=False)
                    print(">>>>>> color_array before: ",color_array.shape)
                    color_array = color_array[numpy.where(color_good_flags >=0 )]
                    print(">>>>>> color_array before: ", color_array.shape)
                elif nolost == 2:
                    color_good_flags = beam.getshonecol(10, nolost=False)
                    print(">>>>>> color_array before: ",color_array.shape)
                    color_array = color_array[numpy.where(color_good_flags < 0 )]
                    print(">>>>>> color_array before: ", color_array.shape)

        else:
            color_array = beam.getshonecol(1, nolost=nolost) * 0.0

        factor1 = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)
        factor2 = ShadowPlot.get_factor(var_y, self.workspace_units_to_cm)
        factorC = ShadowPlot.get_factor(var_color, self.workspace_units_to_cm)


        if self.weight_transparency == 1:
            self.plot_canvas.setData(
                beam.getshonecol(var_x, nolost=nolost)*factor1,
                beam.getshonecol(var_y, nolost=nolost)*factor2,
                color_array*factorC,
                alpha = beam.getshonecol(23, nolost=nolost) )
        else:
            self.plot_canvas.setData(
                beam.getshonecol(var_x, nolost=nolost)*factor1,
                beam.getshonecol(var_y, nolost=nolost)*factor2,
                color_array*factorC,
                )

        self.plot_canvas.resetZoom()
        self.plot_canvas.setGraphTitle(title)
        self.plot_canvas.setColormap(Colormap('viridis'))

        ax = self.plot_canvas.getPlotWidget().getXAxis()
        if self.x_range == 1:
            ax.setLimits(self.x_range_min,self.x_range_max)
        ax.setLabel(xtitle)

        ay = self.plot_canvas.getPlotWidget().getYAxis()
        if self.y_range == 1:
            ay.setLimits(self.y_range_min,self.y_range_max)
        ay.setLabel(ytitle)

        self.image_box.layout().addWidget(self.plot_canvas)


    def plot_scatter(self, var_x, var_y, var_color, title, xtitle, ytitle, xum, yum):
        beam_to_plot = self.input_beam._beam

        if self.image_plane == 1:
            new_shadow_beam = self.input_beam.duplicate(history=False)

            if self.image_plane_rel_abs_position == 1:  # relative
                dist = self.image_plane_new_position
            else:  # absolute
                if self.input_beam.historySize() == 0:
                    historyItem = None
                else:
                    historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                if historyItem is None: image_plane = 0.0
                elif self.input_beam._oe_number == 0: image_plane = 0.0
                else: image_plane = historyItem._shadow_oe_end._oe.T_IMAGE

                dist = self.image_plane_new_position - image_plane

            self.retrace_beam(new_shadow_beam, dist)

            beam_to_plot = new_shadow_beam._beam

        xrange, yrange = self.get_ranges(beam_to_plot, var_x, var_y)

        self.replace_fig(beam_to_plot, var_x, var_y, var_color,
                         title, xtitle, ytitle, xrange=xrange, yrange=yrange,
                         nolost=self.rays, xum=xum, yum=yum)

    def get_ranges(self, beam_to_plot, var_x, var_y):
        xrange = None
        yrange = None
        factor1 = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)
        factor2 = ShadowPlot.get_factor(var_y, self.workspace_units_to_cm)

        if self.x_range == 0 and self.y_range == 0:
            pass
        else:
            if self.x_range == 1:
                congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")

                xrange = [self.x_range_min / factor1, self.x_range_max / factor1]

            if self.y_range == 1:
                congruence.checkLessThan(self.y_range_min, self.y_range_max, "Y range min", "Y range max")

                yrange = [self.y_range_min / factor2, self.y_range_max / factor2]

        return xrange, yrange


    def plot_results(self):
        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                ShadowPlot.set_conversion_active(self.getConversionActive())

                # self.number_of_bins = congruence.checkStrictlyPositiveNumber(self.number_of_bins, "Number of Bins")

                x, y, c, auto_x_title, auto_y_title, xum, yum = self.get_titles()

                self.plot_scatter(x, y, c, title=self.title, xtitle=auto_x_title, ytitle=auto_y_title, xum=xum, yum=yum)

                plotted = True
            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

            return False

    def get_titles(self):
        auto_x_title = self.x_column.currentText().split(":", 2)[1]
        auto_y_title = self.y_column.currentText().split(":", 2)[1]
        xum = auto_x_title + " "
        yum = auto_y_title + " "
        self.title = auto_x_title + "," + auto_y_title
        x = self.x_column_index + 1
        if x == 1 or x == 2 or x == 3:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "m]"
                auto_x_title = auto_x_title + " [$\mu$m]"
            else:
                xum = xum + " [" + self.workspace_units_label + "]"
                auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 4 or x == 5 or x == 6:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "rad]"
                auto_x_title = auto_x_title + " [$\mu$rad]"
            else:
                xum = xum + " [rad]"
                auto_x_title = auto_x_title + " [rad]"
        elif x == 11:
            xum = xum + "[eV]"
            auto_x_title = auto_x_title + " [eV]"
        elif x == 13:
            xum = xum + "[" + self.workspace_units_label + "]"
            auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 14:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x == 15:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x == 19:
            xum = xum + "[Å]"
            auto_x_title = auto_x_title + " [Å]"
        elif x == 20:
            xum = xum + "[" + self.workspace_units_label + "]"
            auto_x_title = auto_x_title + " [" + self.workspace_units_label + "]"
        elif x == 21:
            xum = xum + "[rad]"
            auto_x_title = auto_x_title + " [rad]"
        elif x >= 25 and x <= 28:
            xum = xum + "[Å-1]"
            auto_x_title = auto_x_title + " [Å-1]"
        y = self.y_column_index + 1
        if y == 1 or y == 2 or y == 3:
            if self.getConversionActive():
                yum = yum + "[" + u"\u03BC" + "m]"
                auto_y_title = auto_y_title + " [$\mu$m]"
            else:
                yum = yum + " [" + self.workspace_units_label + "]"
                auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 4 or y == 5 or y == 6:
            if self.getConversionActive():
                yum = yum + "[" + u"\u03BC" + "rad]"
                auto_y_title = auto_y_title + " [$\mu$rad]"
            else:
                yum = yum + " [rad]"
                auto_y_title = auto_y_title + " [rad]"
        elif y == 11:
            yum = yum + "[eV]"
            auto_y_title = auto_y_title + " [eV]"
        elif y == 13:
            yum = yum + "[" + self.workspace_units_label + "]"
            auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 14:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y == 15:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y == 19:
            yum = yum + "[Å]"
            auto_y_title = auto_y_title + " [Å]"
        elif y == 20:
            yum = yum + "[" + self.workspace_units_label + "]"
            auto_y_title = auto_y_title + " [" + self.workspace_units_label + "]"
        elif y == 21:
            yum = yum + "[rad]"
            auto_y_title = auto_y_title + " [rad]"
        elif y >= 25 and y <= 28:
            yum = yum + "[Å-1]"
            auto_y_title = auto_y_title + " [Å-1]"

        c = self.color_column #+ 1

        return x, y, c, auto_x_title, auto_y_title, xum, yum

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays, bad content, bad limits or axes",
                                           QtWidgets.QMessageBox.Ok)

    def setBeamForColor(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam_color = beam

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays, bad content, bad limits or axes",
                                           QtWidgets.QMessageBox.Ok)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def retrace_beam(self, new_shadow_beam, dist):
            new_shadow_beam._beam.retrace(dist)

    def getConversionActive(self):
        return self.is_conversion_active==1



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    def create_dummy_oe():
        empty_element = ShadowOpticalElement.create_empty_oe()
        empty_element._oe.DUMMY = 1.0  # self.workspace_units_to_cm
        empty_element._oe.T_SOURCE = 0.0
        empty_element._oe.T_IMAGE = 0.0
        empty_element._oe.T_INCIDENCE = 0.0
        empty_element._oe.T_REFLECTION = 180.0
        empty_element._oe.ALPHA = 0.0
        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0
        return empty_element


    app = QApplication(sys.argv)
    w = PlotScatter()

    # load a Beam
    from orangecontrib.shadow.util.shadow_objects import ShadowOEHistoryItem
    beam_out = ShadowBeam()
    beam_out.loadFromFile("/home/manuel/Oasys/mirr.02")
    beam_out.history.append(ShadowOEHistoryItem())  # fake Source
    beam_out._oe_number = 0

    # just to create a safe history for possible re-tracing
    beam_out.traceFromOE(beam_out, create_dummy_oe(), history=True)

    w.workspace_units_to_cm = 1.0

    w.setBeam(beam_out)

    w.show()
    app.exec()
    w.saveSettings()


