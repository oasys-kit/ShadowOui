import sys
import time
import copy
import numpy

from PyQt4 import QtGui
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui import ow_automatic_element

class Histogram(ow_automatic_element.AutomaticElement):

    name = "Histogram"
    description = "Display Data Tools: Histogram"
    icon = "icons/histogram.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 2
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 640

    want_main_area=1
    plot_canvas=None
    input_beam=None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    x_column_index=Setting(10)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0.0)

    weight_column_index = Setting(23)
    rays=Setting(1)

    number_of_bins=Setting(100)

    title=Setting("Energy")

    keep_result=Setting(0)

    is_conversion_active = Setting(1)

    def __init__(self):
        super().__init__()

        gui.button(self.controlArea, self, "Refresh", callback=self.plot_results, height=45)
        gui.separator(self.controlArea, 10)

        self.tabs_setting = gui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        # graph tab
        tab_set = oasysgui.createTabPage(self.tabs_setting, "Plot Settings")
        tab_gen = oasysgui.createTabPage(self.tabs_setting, "Histogram Settings")

        screen_box = oasysgui.widgetBox(tab_set, "Screen Position Settings", addSpace=True, orientation="vertical", height=110)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                            items=["On Image Plane", "Retraced"], labelWidth=260,
                                            callback=self.set_ImagePlane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", height=110)
        self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", height=110)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250,
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_ImagePlane()

        general_box = oasysgui.widgetBox(tab_set, "General Settings", addSpace=True, orientation="vertical", height=250)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="Column", labelWidth=70,
                                     items=["1: X",
                                            "2: Y",
                                            "3: Z",
                                            "4: X'",
                                            "5: Y'",
                                            "6: Z'",
                                            "7: Es X",
                                            "8: Es Y",
                                            "9: Es Z",
                                            "10: Ray Flag",
                                            "11: Energy",
                                            "12: Ray Index",
                                            "13: Optical Path",
                                            "14: Phase s",
                                            "15: Phase p",
                                            "16: Ep X",
                                            "17: Ep Y",
                                            "18: Ep Z",
                                            "19: Wavelength",
                                            "20: R = sqrt(X^2 + Y^2 + Z^2)",
                                            "21: Theta (angle from Y axis)",
                                            "22: Magnitude = |Es| + |Ep|",
                                            "23: Total Intensity = |Es|^2 + |Ep|^2",
                                            "24: S Intensity = |Es|^2",
                                            "25: P Intensity = |Ep|^2",
                                            "26: |K|",
                                            "27: K X",
                                            "28: K Y",
                                            "29: K Z",
                                            "30: S0-stokes = |Ep|^2 + |Es|^2",
                                            "31: S1-stokes = |Ep|^2 - |Es|^2",
                                            "32: S2-stokes = 2|Es||Ep|cos(Phase s-Phase p)",
                                            "33: S3-stokes = 2|Es||Ep|sin(Phase s-Phase p)",
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

        self.weight_column = gui.comboBox(general_box, self, "weight_column_index", label="Weight", labelWidth=70,
                                         items=["0: No Weight",
                                                "1: X",
                                                "2: Y",
                                                "3: Z",
                                                "4: X'",
                                                "5: Y'",
                                                "6: Z'",
                                                "7: Es X",
                                                "8: Es Y",
                                                "9: Es Z",
                                                "10: Ray Flag",
                                                "11: Energy",
                                                "12: Ray Index",
                                                "13: Optical Path",
                                                "14: Phase s",
                                                "15: Phase p",
                                                "16: Ep X",
                                                "17: Ep Y",
                                                "18: Ep Z",
                                                "19: Wavelength",
                                                "20: R = sqrt(X^2 + Y^2 + Z^2)",
                                                "21: Theta (angle from Y axis)",
                                                "22: Magnitude = |Es| + |Ep|",
                                                "23: Total Intensity = |Es|^2 + |Ep|^2",
                                                "24: S Intensity = |Es|^2",
                                                "25: P Intensity = |Ep|^2",
                                                "26: |K|",
                                                "27: K X",
                                                "28: K Y",
                                                "29: K Z",
                                                "30: S0-stokes = |Ep|^2 + |Es|^2",
                                                "31: S1-stokes = |Ep|^2 - |Es|^2",
                                                "32: S2-stokes = 2|Es||Ep|cos(Phase s-Phase p)",
                                                "33: S3-stokes = 2|Es||Ep|sin(Phase s-Phase p)",
                                         ],
                                         sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "rays", label="Rays", labelWidth=250,
                                     items=["All rays",
                                            "Good Only",
                                            "Lost Only"],
                                     sendSelectedValue=False, orientation="horizontal")
        incremental_box = oasysgui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="horizontal", height=80)

        gui.checkBox(incremental_box, self, "keep_result", "Keep Result")
        gui.button(incremental_box, self, "Clear", callback=self.clearResults)

        histograms_box = oasysgui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=90)

        oasysgui.lineEdit(histograms_box, self, "number_of_bins", "Number of Bins", labelWidth=250, valueType=int, orientation="horizontal")

        gui.comboBox(histograms_box, self, "is_conversion_active", label="Is U.M. conversion active", labelWidth=250,
                                         items=["No", "Yes"],
                                         sendSelectedValue=False, orientation="horizontal")

        self.main_tabs = gui.tabWidget(self.mainArea)
        plot_tab = gui.createTabPage(self.main_tabs, "Plots")
        out_tab = gui.createTabPage(self.main_tabs, "Output")

        self.image_box = gui.widgetBox(plot_tab, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.shadow_output.setFixedHeight(600)
        self.shadow_output.setFixedWidth(600)

    def clearResults(self):
        if ConfirmDialog.confirmed(parent=self):
            self.input_beam = ShadowBeam()
            self.plot_canvas.clear()
            return True
        else:
            return False

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def replace_fig(self, beam, var, xrange, title, xtitle, ytitle, xum):
        if self.plot_canvas is None:
            self.plot_canvas = ShadowPlot.DetailedHistoWidget(y_scale_factor=1.14)
            self.image_box.layout().addWidget(self.plot_canvas)

        try:
            self.plot_canvas.plot_histo(beam, var, self.rays, xrange, self.weight_column_index, title, xtitle, ytitle, nbins=self.number_of_bins, xum=xum, conv=self.workspace_units_to_cm)
        except Exception:
            raise Exception("Data not plottable: No good rays or bad content")

    def plot_histo(self, var_x, title, xtitle, ytitle, xum):
        beam_to_plot = self.input_beam._beam

        if self.image_plane == 1:
            new_shadow_beam = self.input_beam.duplicate(history=False)
            dist = 0.0

            if self.image_plane_rel_abs_position == 1:  # relative
                dist = self.image_plane_new_position
            else:  # absolute
                historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                if historyItem is None: image_plane = 0.0
                elif self.input_beam._oe_number == 0: image_plane = 0.0
                else: image_plane = historyItem._shadow_oe_end._oe.T_IMAGE

                dist = self.image_plane_new_position - image_plane

            self.retrace_beam(new_shadow_beam, dist)

            beam_to_plot = new_shadow_beam._beam

        xrange = self.get_range(beam_to_plot, var_x)

        self.replace_fig(beam_to_plot, var_x, xrange, title, xtitle, ytitle, xum)

    def get_range(self, beam_to_plot, var_x):
        if self.x_range == 0 :
            x_max = 0
            x_min = 0

            x, good_only = beam_to_plot.getshcol((var_x, 10))

            x_to_plot = copy.deepcopy(x)

            go = numpy.where(good_only == 1)
            lo = numpy.where(good_only != 1)

            if self.rays == 0:
                x_max = numpy.array(x_to_plot[0:], float).max()
                x_min = numpy.array(x_to_plot[0:], float).min()
            elif self.rays == 1:
                x_max = numpy.array(x_to_plot[go], float).max()
                x_min = numpy.array(x_to_plot[go], float).min()
            elif self.rays == 2:
                x_max = numpy.array(x_to_plot[lo], float).max()
                x_min = numpy.array(x_to_plot[lo], float).min()

            xrange = [x_min, x_max]
        else:
            congruence.checkLessThan(self.x_range_min, self.x_range_max, "X range min", "X range max")

            factor1 = ShadowPlot.get_factor(var_x, self.workspace_units_to_cm)

            xrange = [self.x_range_min / factor1, self.x_range_max / factor1]

        return xrange

    def plot_results(self):
        #self.error(self.error_id)

        try:
            plotted = False

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                ShadowPlot.set_conversion_active(self.getConversionActive())

                self.number_of_bins = congruence.checkPositiveNumber(self.number_of_bins, "Number of Bins")

                x, auto_title, xum = self.get_titles()

                self.plot_histo(x, title=self.title, xtitle=auto_title, ytitle="Number of Rays", xum=xum)

                plotted = True
            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram

            return plotted
        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception),
                                       QtGui.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

            return False

    def get_titles(self):
        auto_title = self.x_column.currentText().split(":", 2)[1]

        xum = auto_title + " "
        self.title = auto_title
        x = self.x_column_index + 1

        if x == 1 or x == 2 or x == 3:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "m]"
                auto_title = auto_title + " [$\mu$m]"
            else:
                xum = xum + " [" + self.workspace_units_label + "]"
                auto_title = auto_title + " [" + self.workspace_units_label + "]"
        elif x == 4 or x == 5 or x == 6:
            if self.getConversionActive():
                xum = xum + "[" + u"\u03BC" + "rad]"
                auto_title = auto_title + " [$\mu$rad]"
            else:
                xum = xum + " [rad]"
                auto_title = auto_title + " [rad]"
        elif x == 11:
            xum = xum + "[eV]"
            auto_title = auto_title + " [eV]"
        elif x == 13:
            xum = xum + " [" + self.workspace_units_label + "]"
            auto_title = auto_title + " [" + self.workspace_units_label + "]"
        elif x == 14:
            xum = xum + "[rad]"
            auto_title = auto_title + " [rad]"
        elif x == 15:
            xum = xum + "[rad]"
            auto_title = auto_title + " [rad]"
        elif x == 19:
            xum = xum + "[Å]"
            auto_title = auto_title + " [Å]"
        elif x == 20:
            xum = xum + " [" + self.workspace_units_label + "]"
            auto_title = auto_title + " [" + self.workspace_units_label + "]"
        elif x == 21:
            xum = xum + "[rad]"
            auto_title = auto_title + " [rad]"
        elif x >= 25 and x <= 28:
            xum = xum + "[Å-1]"
            auto_title = auto_title + " [Å-1]"

        return x, auto_title, xum

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                if self.keep_result == 1 and not self.input_beam is None:
                    self.input_beam = ShadowBeam.mergeBeams(self.input_beam, beam)
                else:
                    self.input_beam = beam

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)


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
