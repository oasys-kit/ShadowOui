import sys, numpy, copy, time
from PyQt4 import QtGui
from orangewidget import gui
from orangewidget.settings import Setting

from orangecontrib.shadow.util.shadow_util import ShadowGui, ConfirmDialog, ShadowPlot
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement, ShadowCompoundOpticalElement, EmittingStream, TTYGrabber
from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

class PlotXY(AutomaticElement):

    name = "Plot XY"
    description = "Display Data Tools: Plot XY"
    icon = "icons/plot_xy.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 1100
    IMAGE_HEIGHT = 650

    want_main_area=1
    plot_canvas=None
    input_beam=None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    x_column_index=Setting(0)
    y_column_index=Setting(2)

    x_range=Setting(0)
    x_range_min=Setting(0.0)
    x_range_max=Setting(0)

    y_range=Setting(0.0)
    y_range_min=Setting(0.0)
    y_range_max=Setting(0.0)

    rays=Setting(1)
    cartesian_axis=Setting(1)

    number_of_bins=Setting(100)

    title=Setting("X,Z")

    keep_result=Setting(0)

    def __init__(self):
        super().__init__()

        tabs_setting = gui.tabWidget(self.controlArea)
        tabs_setting.setFixedWidth(450)

        gui.button(self.controlArea, self, "Refresh", callback=self.plot_results)

        # graph tab
        tab_gen = ShadowGui.createTabPage(tabs_setting, "General")
        # FOR FUTURE DEVELOPMENTS
        #tab_his = ShadowGui.createTabPage(tabs_setting, "Histograms")
        #tab_col = ShadowGui.createTabPage(tabs_setting, "Color")

        incremental_box = ShadowGui.widgetBox(tab_gen, "Incremental Result", addSpace=True, orientation="horizontal", height=80)

        gui.checkBox(incremental_box, self, "keep_result", "Keep Result")
        gui.button(incremental_box, self, "Clear", callback=self.clearResults)

        screen_box = ShadowGui.widgetBox(tab_gen, "Screen Position Settings", addSpace=True, orientation="vertical", height=140)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                            items=["On Image Plane", "Retraced"],
                                            callback=self.set_ImagePlane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = ShadowGui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", width=350, height=110)
        self.image_plane_box_empty = ShadowGui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", width=350, height=110)

        ShadowGui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250,
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_ImagePlane()

        general_box = ShadowGui.widgetBox(tab_gen, "General Settings", addSpace=True, orientation="vertical", height=350)

        self.x_column = gui.comboBox(general_box, self, "x_column_index", label="X Column",labelWidth=80,
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
                                            "30: S0-stokes = |Es|^2 + |Ep|^2",
                                            "31: S1-stokes = |Es|^2 - |Ep|^2",
                                            "32: S2-stokes = 2|Es||Ep|cos(Phase s-Phase p)",
                                            "33: S3-stokes = 2|Es||Ep|sin(Phase s-Phase p)",
                                     ],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "x_range", label="X Range", labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_XRange, sendSelectedValue=False, orientation="horizontal")

        self.xrange_box = ShadowGui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=420, height=100)
        self.xrange_box_empty = ShadowGui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=420, height=100)

        ShadowGui.lineEdit(self.xrange_box, self, "x_range_min", "X min", labelWidth=220, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.xrange_box, self, "x_range_max", "X max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_XRange()

        self.y_column = gui.comboBox(general_box, self, "y_column_index", label="Y Column",labelWidth=80,
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
                                            "30: S0-stokes = |Es|^2 + |Ep|^2",
                                            "31: S1-stokes = |Es|^2 - |Ep|^2",
                                            "32: S2-stokes = 2|Es||Ep|cos(Phase s-Phase p)",
                                            "33: S3-stokes = 2|Es||Ep|sin(Phase s-Phase p)",
                                     ],

                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "y_range", label="Y Range",labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_YRange, sendSelectedValue=False, orientation="horizontal")

        self.yrange_box = ShadowGui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=420, height=100)
        self.yrange_box_empty = ShadowGui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=420, height=100)

        ShadowGui.lineEdit(self.yrange_box, self, "y_range_min", "Y min", labelWidth=220, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.yrange_box, self, "y_range_max", "Y max", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_YRange()


        gui.comboBox(general_box, self, "rays", label="Rays", labelWidth=250,
                                     items=["All rays",
                                            "Good Only",
                                            "Lost Only"],
                                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(general_box, self, "cartesian_axis", label="Cartesian Axis",labelWidth=300,
                                     items=["No",
                                            "Yes"],
                                     sendSelectedValue=False, orientation="horizontal")


        histograms_box = ShadowGui.widgetBox(tab_gen, "Histograms settings", addSpace=True, orientation="vertical", height=70)

        ShadowGui.lineEdit(histograms_box, self, "number_of_bins", "Number of Bins", labelWidth=250, valueType=int, orientation="horizontal")

        self.image_box = gui.widgetBox(self.mainArea, "Plot Result", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output = QtGui.QTextEdit()

        out_box = gui.widgetBox(self.mainArea, "Shadow Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)
        out_box.setFixedWidth(self.IMAGE_WIDTH)

        self.shadow_output.setFixedHeight(100)
        self.shadow_output.setFixedWidth(self.IMAGE_WIDTH-50)

    def clearResults(self):
        if ConfirmDialog.confirmed(parent=self):
            self.input_beam = None
            self.plot_canvas.clear()

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def set_XRange(self):
        self.xrange_box.setVisible(self.x_range == 1)
        self.xrange_box_empty.setVisible(self.x_range == 0)

    def set_YRange(self):
        self.yrange_box.setVisible(self.y_range == 1)
        self.yrange_box_empty.setVisible(self.y_range == 0)

    def replace_fig(self, beam, var_x, var_y,  title, xtitle, ytitle, xrange, yrange, nbins, nolost, xum, yum):
        if self.plot_canvas is None:
            self.plot_canvas = ShadowPlot.DetailedPlotWidget()
            self.image_box.layout().addWidget(self.plot_canvas)

        try:
            self.plot_canvas.plot_xy(beam, var_x, var_y, title, xtitle, ytitle, xrange=xrange, yrange=yrange, nbins=nbins, nolost=nolost, xum=xum, yum=yum)
        except Exception:
            raise Exception("Data not plottable: No good rays or bad content")

    def plot_xy(self, var_x, var_y, title, xtitle, ytitle, xum, yum):
        beam_to_plot = self.input_beam._beam

        if self.image_plane == 1:
            new_shadow_beam = self.input_beam.duplicate(history=False)

            historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)
            if historyItem is None: raise Exception("Calculation impossible: Beam has no history")

            dist = 0.0

            if self.image_plane_rel_abs_position == 1:  # relative
                image_plane = 0.0

                if type(historyItem._shadow_oe_end) == ShadowOpticalElement:
                    image_plane = historyItem._shadow_oe_end.oe.T_IMAGE
                elif type(historyItem._shadow_oe_end) == ShadowCompoundOpticalElement:
                    image_plane = historyItem._shadow_oe_end.oe.list[historyItem._shadow_oe_end.oe.number_oe() - 1].T_IMAGE

                if self.image_plane_new_position < 0 and abs(self.image_plane_new_position) > image_plane:
                    raise Exception("Image plane new position cannot be before the O.E.")

                dist = self.image_plane_new_position
            else:  # absolute
                ShadowGui.checkPositiveNumber(self.image_plane_new_position, "Image Plane new Position")

                dist = self.image_plane_new_position - historyItem._shadow_oe_end.oe.T_IMAGE

            new_shadow_beam._beam.retrace(dist)

            beam_to_plot = new_shadow_beam._beam

        xrange = None
        yrange = None

        factor1 = ShadowPlot.get_factor(var_x)
        factor2 = ShadowPlot.get_factor(var_y)

        if self.x_range == 0 and self.y_range == 0:
            if self.cartesian_axis == 1:
                x_max = 0
                y_max = 0
                x_min = 0
                y_min = 0

                x, y, good_only = beam_to_plot.getshcol((var_x, var_y, 10))

                x_to_plot = copy.deepcopy(x)
                y_to_plot = copy.deepcopy(y)

                go = numpy.where(good_only == 1)
                lo = numpy.where(good_only != 1)

                if self.rays == 0:
                    x_max = numpy.array(x_to_plot[0:], float).max()
                    y_max = numpy.array(y_to_plot[0:], float).max()
                    x_min = numpy.array(x_to_plot[0:], float).min()
                    y_min = numpy.array(y_to_plot[0:], float).min()
                elif self.rays == 1:
                    x_max = numpy.array(x_to_plot[go], float).max()
                    y_max = numpy.array(y_to_plot[go], float).max()
                    x_min = numpy.array(x_to_plot[go], float).min()
                    y_min = numpy.array(y_to_plot[go], float).min()
                elif self.rays == 2:
                    x_max = numpy.array(x_to_plot[lo], float).max()
                    y_max = numpy.array(y_to_plot[lo], float).max()
                    x_min = numpy.array(x_to_plot[lo], float).min()
                    y_min = numpy.array(y_to_plot[lo], float).min()

                temp = numpy.array([x_max, y_max, x_min, y_min], float)

                xrange = [temp.min(), temp.max()]
                yrange = [temp.min(), temp.max()]
        else:
            if self.x_range == 1:
                if self.x_range_min >= self.x_range_max:
                    raise Exception("X range min cannot be greater or equal than X range max")

                xrange = [self.x_range_min / factor1, self.x_range_max / factor1]

            if self.y_range == 1:
                if self.y_range_min >= self.y_range_max:
                    raise Exception("Y range min cannot be greater or than Y range max")

                yrange = [self.y_range_min / factor2, self.y_range_max / factor1]

        self.replace_fig(beam_to_plot, var_x, var_y, title, xtitle, ytitle, xrange=xrange, yrange=yrange, nbins=int(self.number_of_bins), nolost=self.rays, xum=xum, yum=yum)

    def plot_results(self):
        self.error(self.error_id)

        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            if ShadowGui.checkEmptyBeam(self.input_beam):
                self.number_of_bins = ShadowGui.checkPositiveNumber(self.number_of_bins, "Number of Bins")

                auto_x_title = self.x_column.currentText().split(":", 2)[1]
                auto_y_title = self.y_column.currentText().split(":", 2)[1]

                xum = auto_x_title + " "
                yum = auto_y_title + " "

                self.title = auto_x_title + "," + auto_y_title

                x = self.x_column_index + 1

                if x == 1 or x == 2 or x == 3:
                    xum = xum + "[" + u"\u03BC" + "m]"
                    auto_x_title = auto_x_title + " [$\mu$m]"
                elif x == 4 or x == 5 or x == 6:
                    xum = xum + "[" + u"\u03BC" + "rad]"
                    auto_x_title = auto_x_title + " [$\mu$rad]"
                elif x == 11:
                    xum = xum + "[eV]"
                    auto_x_title = auto_x_title + " [eV]"
                elif x == 13:
                    xum = xum + "[cm]"
                    auto_x_title = auto_x_title + " [cm]"
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
                    xum = xum + "[cm]"
                    auto_x_title = auto_x_title + " [cm]"
                elif x == 21:
                    xum = xum + "[rad]"
                    auto_x_title = auto_x_title + " [rad]"
                elif x >= 25 and x <= 28:
                    xum = xum + "[Å-1]"
                    auto_x_title = auto_x_title + " [Å-1]"

                y = self.y_column_index + 1

                if y == 1 or y == 2 or y == 3:
                    yum = yum + "[" + u"\u03BC" + "m]"
                    auto_y_title = auto_y_title + " [$\mu$m]"
                elif y == 4 or y == 5 or y == 6:
                    yum = yum + "[" + u"\u03BC" + "rad]"
                    auto_y_title = auto_y_title + " [$\mu$rad]"
                elif y == 11:
                    yum = yum + "[eV]"
                    auto_y_title = auto_y_title + " [eV]"
                elif y == 13:
                    yum = yum + "[cm]"
                    auto_y_title = auto_y_title + " [cm]"
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
                    yum = yum + "[cm]"
                    auto_y_title = auto_y_title + " [cm]"
                elif y == 21:
                    yum = yum + "[rad]"
                    auto_y_title = auto_y_title + " [rad]"
                elif y >= 25 and y <= 28:
                    yum = yum + "[Å-1]"
                    auto_y_title = auto_y_title + " [Å-1]"

                self.plot_xy(x, y, title=self.title, xtitle=auto_x_title, ytitle=auto_y_title, xum=xum, yum=yum)

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            time.sleep(0.5)  # prevents a misterious dead lock in the Orange cycle when refreshing the histogram
        except Exception as exception:
            QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                       str(exception),
                                       QtGui.QMessageBox.Ok)

            self.error_id = self.error_id + 1
            self.error(self.error_id, "Exception occurred: " + str(exception))


    def setBeam(self, beam):
        if ShadowGui.checkEmptyBeam(beam):
            if ShadowGui.checkGoodBeam(beam):
                if self.keep_result == 1 and not self.input_beam is None:
                    self.input_beam = ShadowBeam.mergeBeams(self.input_beam, beam)
                else:
                    self.input_beam = beam

                if ShadowGui.checkEmptyBeam(self.input_beam):
                    if (self.input_beam._oe_number == 0):  # IS THE SOURCE
                        self.image_plane = 0
                        self.set_ImagePlane()
                        self.image_plane_combo.setEnabled(False)

                if self.is_automatic_run:
                    self.plot_results()
            else:
                QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                           "Data not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()
