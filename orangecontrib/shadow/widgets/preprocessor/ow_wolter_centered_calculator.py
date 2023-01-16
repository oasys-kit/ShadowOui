import os, sys
import numpy

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget, QLabel, QSizePolicy
from PyQt5.QtGui import QTextCursor,QFont, QPalette, QColor, QPainter, QBrush, QPen, QPixmap

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui

from srxraylib.metrology.dabam import dabam, autocorrelationfunction

from copy import copy
from urllib.request import urlopen

from orangecontrib.shadow.util.shadow_objects import ConicCoefficientsPreProcessorData

from oasys.util.oasys_util import EmittingStream

class OWWolterCenteredCalculator(OWWidget):
    name = "Wolter Calculator"
    id = "WolterCalculator"
    description = "Calculation of coefficients for Wolter systems"
    icon = "icons/wolter2.png"
    author = "Manuel Sanchez del Rio"
    maintainer_email = "srio@esrf.eu"
    priority = 100
    category = ""
    keywords = ["oasys", "wolter", "telescope", "advanced KB"]

    outputs = [{"name":"ConicCoeff_1_PreProcessor_Data",
                "type":ConicCoefficientsPreProcessorData,
                "doc":"ConicCoeff #1 PreProcessor Data",
                "id":"ConicCoeff_1_PreProcessor_Data"},
               {"name": "ConicCoeff_2_PreProcessor_Data",
                "type": ConicCoefficientsPreProcessorData,
                "doc": "ConicCoeff #2 PreProcessor Data",
                "id": "ConicCoeff_2_PreProcessor_Data"},
               ]

    want_main_area = True
    want_control_area = True

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 645

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 650 #18

    #################

    setup_type = Setting(0)

    p1 = Setting(-0.00194644)
    p2 = Setting(1.904995)

    theta1 = Setting(0.0159872)

    tab=[]

    usage_path = os.path.join(resources.package_dirname("orangecontrib.syned.widgets.gui"), "misc", "predabam_usage.png")

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Calculate", self)
        self.runaction.triggered.connect(self.calculate)
        self.addAction(self.runaction)


        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.MAX_WIDTH)),
                               round(min(geom.height() * 0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        gui.separator(self.controlArea)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_calc = oasysgui.createTabPage(tabs_setting, "Calculate")
        tab_out = oasysgui.createTabPage(tabs_setting, "Plot")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")


        #
        #-------------------- calculate
        #

        button = gui.button(tab_calc, self, "Calculate", callback=self.calculate)

        tab_step_1 = oasysgui.widgetBox(tab_calc, "Calculation Parameters", addSpace=True, orientation="vertical", height=600)

        box = oasysgui.widgetBox(tab_step_1, "setup inputs", orientation="vertical")

        gui.comboBox(box, self, "setup_type", label="Setup type", labelWidth=260,
                     items=["Wolter-I",
                            "Wolter-II",
                            "Wolter-III",
                            ],
                     callback=self.update_panel, sendSelectedValue=False, orientation="horizontal")

        self.w_p1 = oasysgui.lineEdit(box, self, "p1", "parabola directrix coordinate (-p)", labelWidth=220, valueType=float, orientation="horizontal")
        self.w_p2 = oasysgui.lineEdit(box, self, "p2", "hyperbola interfocal distance (2c)", labelWidth=220, valueType=float, orientation="horizontal")
        self.w_theta1 = oasysgui.lineEdit(box, self, "theta1", "Grazing angle at principal surface [rad]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.update_panel)


        #
        #-------------------- Output
        #
        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=600)
        self.output_textarea = oasysgui.textArea(height=500,readOnly=False)
        out_box.layout().addWidget(self.output_textarea)

        #
        #-------------------- Use
        #

        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        #
        #
        #
        gui.rubber(self.controlArea)

        self.initializeTabs()

        gui.rubber(self.mainArea)

    def update_panel(self):
        self.w_p1.setVisible(True)
        self.w_p2.setVisible(True)
        self.w_theta1.setVisible  (True)

    def calculate(self):
        try:
            self.shadow_output.setText("")
            self.design_output.setText("")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            results_txt = ""
            print("####################################################")
            print("# DESIGN PHASE")
            print("####################################################\n")

            if True:
                tkt = self.recipe4()
                # tkt = recipe4(
                #     f11=self.p1,
                #     f12=0,
                #     f21=self.p2,
                #     f22=0,
                #     theta=self.theta1,
                #     verbose=1,
                # )

            else:
                raise Exception(NotImplementedError)

            results_txt += "\nparabola p=%f"  % tkt['p']
            results_txt += "\nhyperbola a=%f" % tkt['a']
            results_txt += "\nhyperbola b=%f" % tkt['b']
            results_txt += "\nhyperbola c=%f" % tkt['c']


            results_txt += "\n\n\n    oe1(normalized)      oe2(normalized)"
            for i in range(10):
                results_txt += "\nccc[%d]       %10.4g       %10.4g  " % (i,
                                                                    tkt['ccc1'][i]/tkt['ccc1'][0], tkt['ccc2'][i]/tkt['ccc2'][0])

            results_txt += "\n\n\n    oe1           oe2 "
            for i in range(10):
                results_txt += "\nccc[%d]       %10.4g       %10.4g  " % (i, tkt['ccc1'][i], tkt['ccc2'][i])


            self.design_output.setText(results_txt)


            Pp = None
            Qp = numpy.sqrt(tkt['x_pmin']**2 + tkt['y_pmin'])
            Fp = Qp
            print("\n\nParabola p = NOT DEFINED ")
            print("Parabola q = ", Qp)
            print("Parabola f = ", Qp)

            Ph = Qp
            Qh = numpy.sqrt((tkt['x_pmin']-2*tkt['c'])**2 + tkt['y_pmin'])
            Fh = 1/(1/Ph+1/Qh)
            print("\nHyperbola p = ", Ph)
            print("Hyperbola q = ", Qh)
            print("Hyperbola f = ", Fh)

            F = 1. / (1 / Fp + 1 / Fh)
            print("\nCombined f = ", F)

            #
            # Ellipse###########################################################################
            #
            c_e = 5.0
            Pe = numpy.sqrt((tkt['x_pmin']-2*c_e)**2 + tkt['y_pmin']**2)
            Qe = numpy.sqrt( tkt['x_pmin']       **2 + tkt['y_pmin']**2)
            print("\n\n\nFor ellipse at 2 * c_e = %f" % (2*c_e))
            print("\n\n\nPe = %f; Qe = %f" % (Pe, Qe))
            print("\n ellipse c_e=%f" % c_e)
            b_e = numpy.sqrt(Pe*Qe) * numpy.sin(self.theta1)
            print("\n ellipse b_e=%f" % b_e)
            a_e = numpy.sqrt(c_e**2 + b_e**2)
            print("\n ellipse a_e=%f" % a_e)
            print("\ncheck 1: ", (tkt['x_pmin']-c_e)**2 / a_e**2 + tkt['y_pmin']**2 / b_e**2)
            print("\ncheck y(x_pmin): ", b_e * numpy.sqrt(1 - (tkt['x_pmin'] - c_e) ** 2 / a_e ** 2), tkt['y_pmin'])


            # Delta = Pe**2 - tkt['y_pmin']**2
            # if Delta < 0:
            #     print("\n Cannot calculate ellipse (Delta=%f)...." % Delta)
            # else:
            #     c_e = numpy.abs(0.5 * (tkt['x_pmin'] - numpy.sqrt(Delta)))
            #     print("\n ellipse c_e=%f" % c_e)
            #     b_e = numpy.sqrt(Pe*Qe) * numpy.sin(2*self.theta1)
            #     print("\n ellipse b_e=%f" % b_e)
            #     a_e = numpy.sqrt(c_e**2 + b_e**2)
            #     print("\n ellipse a_e=%f" % a_e)

            # Ellipse
            # (x-c_e)^2/a^2 + y^2/b_e^2 = 1 (Underwood)
            # (z-c_e)^2/a^2 + (y^2+x^2)/b_e^2 = 1 (Shadow)
            # normal incidence (Underwood x->z, y->y  ->x)

            ccc_centered_ellipse = numpy.array([1 / b_e ** 2, 1 / b_e ** 2, 1 / a_e ** 2, \
                                                  0, 0, 0, \
                                                  0, 0, -2 * c_e / a_e ** 2, \
                                                  (c_e / a_e) ** 2 - 1])
            ccc_centered_ellipse /= ccc_centered_ellipse[0]

            print("\n\nEllipse coeff: ", ccc_centered_ellipse)

            #
            # plot data
            #
            self.progressBarInit()
            p = tkt['p']
            x = numpy.linspace(tkt['x_pmin']*1.5, -tkt['x_pmin']*1.5/5, 20000)


            # parabola
            y1a =  numpy.sqrt(2 * p * x + p ** 2)
            y1b = -numpy.sqrt(2 * p * x + p ** 2)

            # hyperbola

            y2a =  tkt['b'] * numpy.sqrt(((x - tkt['c']) / tkt['a']) ** 2 - 1)
            y2b = -tkt['b'] * numpy.sqrt(((x - tkt['c']) / tkt['a']) ** 2 - 1)

            y3a =   b_e * numpy.sqrt(1 - ((x - c_e) / a_e) ** 2)
            y3b =  -b_e * numpy.sqrt(1 - ((x - c_e) / a_e) ** 2)

            # self.plot_multi_data1D([-x,-x], [y1a,y1b],
            #                       10, 2, 0,
            #                       title="parabola", xtitle="-z [m] (along optical axis)", ytitle="x,y [m]",
            #                       ytitles=["1","2"],
            #                       colors=['blue','blue'],
            #                       replace=True,
            #                       control=False,
            #                       xrange=None,
            #                       yrange=None,
            #                       symbol=['',''])

            self.plot_multi_data1D([-x,-x], [y1a,y1b],
                                  10, 2, 0,
                                  title="parabola", xtitle="-z [m] (along optical axis)", ytitle="x,y [m]",
                                  ytitles=["1","2"],
                                  colors=['blue','blue'],
                                  replace=True,
                                  control=False,
                                  xrange=None,
                                  yrange=None,
                                  symbol=['',''])

            self.plot_multi_data1D([-x,-x], [y2a,y2b],
                                  20, 3, 1,
                                  title="hyperbola", xtitle="-z [m] (along optical axis)", ytitle="x,y [m]",
                                  ytitles=["1","2"],
                                  colors=['r','r'],
                                  replace=True,
                                  control=False,
                                  xrange=None,
                                  yrange=None,
                                  symbol=['',''])

            x_c = numpy.array([tkt['x_pmin']*1.5, tkt['x_pmin'], 2*tkt['c'], 2*tkt['c'],  tkt['x_pmin'],  tkt['x_pmin']*1.5])
            y_c = numpy.array([tkt['y_pmin'],     tkt['y_pmin'], 0         , 0         , -tkt['y_pmin'], -tkt['y_pmin']   ])

            # self.plot_multi_data1D([-x,-x,-x,-x, -x_c], [y1a,y1b,y2a,y2b,y_c],
            #                       80, 4, 2,
            #                       title="parabola+hyperbola", xtitle="-z [m] (along optical axis)", ytitle="x,y [m]",
            #                       ytitles=["parabola+","parabola-","hyperbola+","hyperbola-", "ray"],
            #                       colors=['blue','blue','red','red','k'],
            #                       replace=True,
            #                       control=False,
            #                       xrange=None,
            #                       yrange=None,
            #                       symbol=['','','','',''])


            self.plot_multi_data1D([-x,-x,-x,-x, -x_c, -x, -x], [y1a,y1b,y2a,y2b,y_c, y3a, y3b],
                                  80, 4, 2,
                                  title="parabola+hyperbola+ellipse", xtitle="-z [m] (along optical axis)", ytitle="x,y [m]",
                                  ytitles=["parabola+","parabola-","hyperbola+","hyperbola-", "ray", "ell","ell"],
                                  colors=['blue','blue','red','red','k','green','green'],
                                  replace=True,
                                  control=False,
                                  xrange=None,
                                  yrange=None,
                                  symbol=['','','','','','',''])

            #
            # send data
            #
            print("\n\n\n\n")
            print("####################################################")
            print("# RAY-TRACING PHASE")
            print("####################################################\n")


            preprocessor_oe1 = ConicCoefficientsPreProcessorData(
                conic_coefficient_0 = tkt['ccc1'][0],
                conic_coefficient_1 = tkt['ccc1'][1],
                conic_coefficient_2 = tkt['ccc1'][2],
                conic_coefficient_3 = tkt['ccc1'][3],
                conic_coefficient_4 = tkt['ccc1'][4],
                conic_coefficient_5 = tkt['ccc1'][5],
                conic_coefficient_6 = tkt['ccc1'][6],
                conic_coefficient_7 = tkt['ccc1'][7],
                conic_coefficient_8 = tkt['ccc1'][8],
                conic_coefficient_9 = tkt['ccc1'][9],
                source_plane_distance=None,
                image_plane_distance=-tkt['x_pmin'],
                angles_respect_to=0,
                incidence_angle_deg=0.0,
                reflection_angle_deg=0.0,
                mirror_orientation_angle=2, # that means 180 deg
                title="Primary mirror: Parabolic",
                )

            preprocessor_oe2 = ConicCoefficientsPreProcessorData(
                conic_coefficient_0= tkt['ccc2'][0],
                conic_coefficient_1= tkt['ccc2'][1],
                conic_coefficient_2= tkt['ccc2'][2],
                conic_coefficient_3= tkt['ccc2'][3],
                conic_coefficient_4= tkt['ccc2'][4],
                conic_coefficient_5= tkt['ccc2'][5],
                conic_coefficient_6= tkt['ccc2'][6],
                conic_coefficient_7= tkt['ccc2'][7],
                conic_coefficient_8= tkt['ccc2'][8],
                conic_coefficient_9= tkt['ccc2'][9],
                source_plane_distance=tkt['x_pmin'],
                image_plane_distance=2*tkt['c'],
                angles_respect_to=0,
                incidence_angle_deg=0.0,
                reflection_angle_deg=0.0,
                mirror_orientation_angle=0,
                title="Secondary mirror: Hyperbolic",
                )

            for obj in [preprocessor_oe1,preprocessor_oe2]:
                print("\nChanging/setting parameters of shadow conic coefficient mirror: ", obj.title)
                print("conic_coefficient_0",      obj.conic_coefficient_0)
                print("conic_coefficient_1",      obj.conic_coefficient_1)
                print("conic_coefficient_2",      obj.conic_coefficient_2)
                print("conic_coefficient_3",      obj.conic_coefficient_3)
                print("conic_coefficient_4",      obj.conic_coefficient_4)
                print("conic_coefficient_5",      obj.conic_coefficient_5)
                print("conic_coefficient_6",      obj.conic_coefficient_6)
                print("conic_coefficient_7",      obj.conic_coefficient_7)
                print("conic_coefficient_8",      obj.conic_coefficient_8)
                print("conic_coefficient_9",      obj.conic_coefficient_9)
                if obj.source_plane_distance    is not None: print("source_plane_distance",    obj.source_plane_distance)
                if obj.image_plane_distance     is not None: print("image_plane_distance",     obj.image_plane_distance)
                if obj.angles_respect_to        is not None: print("angles_respect_to",        obj.angles_respect_to)
                if obj.incidence_angle_deg      is not None: print("incidence_angle_deg",      obj.incidence_angle_deg)
                if obj.reflection_angle_deg     is not None: print("reflection_angle_deg",     obj.reflection_angle_deg)
                if obj.mirror_orientation_angle is not None: print("mirror_orientation_angle", obj.mirror_orientation_angle)


            self.send("ConicCoeff_1_PreProcessor_Data", preprocessor_oe1)
            self.send("ConicCoeff_2_PreProcessor_Data", preprocessor_oe2)

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

        self.progressBarFinished()


    def initializeTabs(self):
        self.tabs = oasysgui.tabWidget(self.mainArea)

        self.tab = [oasysgui.createTabPage(self.tabs, "Design parameters"),
                    oasysgui.createTabPage(self.tabs, "Output"),
                    oasysgui.createTabPage(self.tabs, "oe1 Profile"),
                    oasysgui.createTabPage(self.tabs, "oe2 Profile"),
                    oasysgui.createTabPage(self.tabs, "join profile"),
        ]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)


        self.design_output = oasysgui.textArea()
        tmp2 = oasysgui.widgetBox(self.tab[0], "Design output", addSpace=True, orientation="horizontal", height = self.IMAGE_HEIGHT-4) #, width=410)
        tmp2.layout().addWidget(self.design_output)

        self.shadow_output = oasysgui.textArea() #height=self.IMAGE_HEIGHT-5, width=400)
        tmp1 = oasysgui.widgetBox(self.tab[1], "System output", addSpace=True, orientation="horizontal", height = self.IMAGE_HEIGHT-4) #, width=410)
        tmp1.layout().addWidget(self.shadow_output)

        #
        self.plot_canvas = [None, None, None]

        self.plot_canvas[0] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[0].setDefaultPlotLines(True)
        self.plot_canvas[0].setActiveCurveColor(color='blue')
        self.plot_canvas[0].setGraphYLabel("Z [nm]")
        self.plot_canvas[0].setGraphTitle("oe1 Profile")
        self.plot_canvas[0].setInteractiveMode(mode='zoom')

        self.plot_canvas[1] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[1].setDefaultPlotLines(True)
        self.plot_canvas[1].setActiveCurveColor(color='blue')
        self.plot_canvas[1].setGraphYLabel("Z [nm]")
        self.plot_canvas[1].setGraphTitle("oe2 Profile")
        self.plot_canvas[1].setInteractiveMode(mode='zoom')

        self.plot_canvas[2] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[2].setDefaultPlotLines(True)
        self.plot_canvas[2].setActiveCurveColor(color='blue')
        self.plot_canvas[2].setGraphYLabel("Z [nm]")
        self.plot_canvas[2].setGraphTitle("Joint Profile")
        self.plot_canvas[2].setInteractiveMode(mode='zoom')


        self.tab[2].layout().addWidget(self.plot_canvas[0])
        self.tab[3].layout().addWidget(self.plot_canvas[1])
        self.tab[4].layout().addWidget(self.plot_canvas[2])

        self.tabs.setCurrentIndex(0)

    def check_fields(self):
        if self.setup_type > 0:
            raise Exception(NotImplementedError)
        else:
            pass

        # self.dimension_x = congruence.checkStrictlyPositiveNumber(self.dimension_x, "Dimension X")
        # self.step_x = congruence.checkStrictlyPositiveNumber(self.step_x, "Step X")
        #
        # congruence.checkLessOrEqualThan(self.step_x, self.dimension_x/2, "Step Width", "Width/2")
        #
        # if self.modify_y == 1 or self.modify_y == 2:
        #     self.new_length = congruence.checkStrictlyPositiveNumber(self.new_length, "New Length")
        #
        # if self.renormalize_y == 1:
        #     self.rms_y = congruence.checkPositiveNumber(self.rms_y, "Rms Y")
        #
        # congruence.checkDir(self.heigth_profile_file_name)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def plot_data1D(self, x, y, progressBarValue, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle="",
                    log_x=False, log_y=False,
                    color='blue',
                    replace=True, control=False, calculate_fwhm=True,
                    xrange=None, yrange=None, symbol=''):

        if tabs_canvas_index is None: tabs_canvas_index = 0 #back compatibility?


        self.tab[tabs_canvas_index].layout().removeItem(self.tab[tabs_canvas_index].layout().itemAt(0))

        self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(parent=None,
                                                                  backend=None,
                                                                  resetzoom=True,
                                                                  autoScale=False,
                                                                  logScale=True,
                                                                  grid=True,
                                                                  curveStyle=True,
                                                                  colormap=False,
                                                                  aspectRatio=False,
                                                                  yInverted=False,
                                                                  copy=True,
                                                                  save=True,
                                                                  print_=True,
                                                                  control=control,
                                                                  position=True,
                                                                  roi=False,
                                                                  mask=False,
                                                                  fit=False)


        self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
        self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)

        # ALLOW FIT BUTTON HERE
        self.plot_canvas[plot_canvas_index].fitAction.setVisible(True)

        # overwrite FWHM and peak values
        if calculate_fwhm:
            try:
                t = numpy.where(y>=max(y)*0.5)
                x_left,x_right =  x[t[0][0]], x[t[0][-1]]

                self.plot_canvas[plot_canvas_index].addMarker(x_left, 0.5*y.max(), legend="G1",
                                                              text="FWHM=%5.2f"%(numpy.abs(x_right-x_left)),
                                                              color="pink",selectable=False, draggable=False,
                                                              symbol="+", constraint=None)
                self.plot_canvas[plot_canvas_index].addMarker(x_right, 0.5*y.max(), legend="G2", text=None, color="pink",
                                                              selectable=False, draggable=False, symbol="+", constraint=None)
            except:
                pass

        self.tab[tabs_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_histo(self.plot_canvas[plot_canvas_index], x, y, title, xtitle, ytitle, color, replace, symbol=symbol)

        self.plot_canvas[plot_canvas_index].setXAxisLogarithmic(log_x)
        self.plot_canvas[plot_canvas_index].setYAxisLogarithmic(log_y)


        if xrange is not None:
            self.plot_canvas[plot_canvas_index].setGraphXLimits(xrange[0],xrange[1])
        if yrange is not None:
            self.plot_canvas[plot_canvas_index].setGraphYLimits(yrange[0],yrange[1])

        if min(y) < 0:
            if log_y:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y)*1.2, max(y)*1.2)
            else:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y)*1.01, max(y)*1.01)
        else:
            if log_y:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y), max(y)*1.2)
            else:
                self.plot_canvas[plot_canvas_index].setGraphYLimits(min(y)*0.99, max(y)*1.01)

        self.progressBarSet(progressBarValue)


    def plot_multi_data1D(self, x_list, y_list,
                    progressBarValue, tabs_canvas_index, plot_canvas_index,
                    title="", xtitle="",
                    ytitle="",
                    ytitles= [""],
                    colors = ['green'],
                    replace=True,
                    control=False,
                    xrange=None,
                    yrange=None,
                    symbol=['']):

        if len(y_list) != len(ytitles):
            ytitles = ytitles * len(y_list)

        if len(y_list) != len(colors):
            colors = colors * len(y_list)
        if len(y_list) != len(symbol):
            symbols = symbol * len(y_list)
        else:
            symbols = symbol

        if tabs_canvas_index is None: tabs_canvas_index = 0 #back compatibility?

        self.tab[tabs_canvas_index].layout().removeItem(self.tab[tabs_canvas_index].layout().itemAt(0))

        self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(parent=None,
                                                                  backend=None,
                                                                  resetzoom=True,
                                                                  autoScale=False,
                                                                  logScale=True,
                                                                  grid=True,
                                                                  curveStyle=True,
                                                                  colormap=False,
                                                                  aspectRatio=False,
                                                                  yInverted=False,
                                                                  copy=True,
                                                                  save=True,
                                                                  print_=True,
                                                                  control=control,
                                                                  position=True,
                                                                  roi=False,
                                                                  mask=False,
                                                                  fit=False)


        self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
        self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)

        self.tab[tabs_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])


        for i in range(len(y_list)):
            print(">>>>>>>>>>>>>>>>>>>> ADDING PLOT INDEX", i, x_list[i].shape, y_list[i].shape,ytitles[i],symbols[i],colors[i])
            self.plot_canvas[plot_canvas_index].addCurve(x_list[i], y_list[i],
                                         ytitles[i],
                                         xlabel=xtitle,
                                         ylabel=ytitle,
                                         symbol=symbols[i],
                                         color=colors[i])
        #
        self.plot_canvas[plot_canvas_index].getLegendsDockWidget().setFixedHeight(150)
        self.plot_canvas[plot_canvas_index].getLegendsDockWidget().setVisible(True)
        self.plot_canvas[plot_canvas_index].setActiveCurve(ytitles[0])
        self.plot_canvas[plot_canvas_index].replot()


        if xrange is not None:
            self.plot_canvas[plot_canvas_index].setGraphXLimits(xrange[0],xrange[1])
        if yrange is not None:
            self.plot_canvas[plot_canvas_index].setGraphYLimits(yrange[0],yrange[1])

        # if numpy.amin(numpy.array(y_list)) < 0:
        #     self.plot_canvas[plot_canvas_index].setGraphYLimits(numpy.amin(numpy.array(y_list))*1.01, numpy.amax(numpy.array(y_list))*1.01)
        # else:
        #     self.plot_canvas[plot_canvas_index].setGraphYLimits(numpy.amin(numpy.array(y_list))*0.99, numpy.amax(numpy.array(y_list))*1.01)

        self.progressBarSet(progressBarValue)


    def plot_data2D(self, data2D, dataX, dataY, progressBarValue, tabs_canvas_index, plot_canvas_index,
                    title="",xtitle="", ytitle=""):

        if self.view_type == 0:
            pass
        elif self.view_type == 1:
            self.plot_data2D_only_image(data2D, dataX, dataY, progressBarValue, tabs_canvas_index,plot_canvas_index,
                         title=title, xtitle=xtitle, ytitle=ytitle)
        elif self.view_type == 2:
            self.plot_data2D_with_histograms(data2D, dataX, dataY, progressBarValue, tabs_canvas_index,plot_canvas_index,
                         title=title, xtitle=xtitle, ytitle=ytitle)

    def recipe4(self,     #  centered system parabola-hyperbola
        # f11 = -0.00194644,
        # f12 = 0.0,
        # f21 = 1.905,
        # f22 = 0.0,
        # theta = 0.0159872,
        # verbose = 1,
                ):
        f11 = self.p1
        f12 = 0.0
        f21 = self.p2
        f22 = 0.0
        theta = self.theta1
        verbose = True

        if f12 != 0.0 or f22 != 0:
            raise Exception("Is your origin at the common focus?")

        p = numpy.abs(f11-f12)

        # intersection point at the parabola matching angle (https://doi.org/10.1107/S1600577522004593)
        c0 = (p / 2) / (numpy.tan(theta)) ** 2 - (p/2)
        # y^2 = 2px + p^2
        c1 = numpy.sqrt( 2 * p * c0 + p**2)

        #
        # hyperbola
        #

        c = f21/2

        # get a from the hyperbola
        # (x-c)/a)^2 - (y/b)^2 = 1
        # b^2 = c^2 - a^2

        A = 1
        B = -c0**2 + 2 * c * c0 - 2 * c**2 - c1**2
        C = c**4 + c**2 * c0**2 - 2 * c**3 * c0
        S1 = numpy.sqrt( (-B + numpy.sqrt(B**2 - 4*A*C)) / (2 * A) )
        S2 = numpy.sqrt( (-B - numpy.sqrt(B ** 2 - 4 * A * C)) / (2 * A) )
        a = numpy.min((S1,S2))
        b = numpy.sqrt(c**2 - a**2)

        #
        # coeffs

        # Parabola
        # y^2 = p(2 * x + p) (Underwood)
        # x^2 + z^2 = 2 p y + p^2 (Shadow)
        ccc_centered_parabola = numpy.array([1, 1, 0, 0, 0, 0, 0, 0, -2 * p, -p ** 2])

        # Hyperbola
        # (x-c)^2/a^2 - y^2/b^2 = 1 (Underwood)
        # (z-c)^2/a^2 - (y^2+x*2)/b^2 = 1 (Shadow)
        # # normal incidence (Underwood x->z, y->y  ->x)

        ccc_centered_hyperbola = numpy.array([-1/b**2, -1/b**2, 1/a**2, \
                                              0, 0, 0, \
                                              0, 0, -2*c/a**2, \
                                              (c/a)**2 - 1])


        if verbose:
            print("f11, f12", f11, f12)
            print("f21, f22", f21, f22)

            print("c0, c1: ", c0, c1)
            print("S1, S2: ", S1, S2)


            print("   theta grazing [deg]: ", theta * 180 / numpy.pi)
            print("   Parabola p [m]:", p)
            print("   Hyperbola a, b, c [m]: ", a, b, c)

            print("\n\nCalculated parameters: ")
            x_pmin = c0
            y_pmin = c1
            print("   ** Origin is at parabola focus (=far hyperbola focus)**")
            print("   Common point: x_pmin, y_pmin: ", x_pmin, y_pmin)
            print(" ")


            print("\n   normalized ccc_centered_parabola", ccc_centered_parabola / ccc_centered_parabola[0])
            print("   normalized ccc_centered_hyperbola", ccc_centered_hyperbola / ccc_centered_hyperbola[0])

            print("\n   ccc_centered_parabola", ccc_centered_parabola)
            print("   ccc_centered_hyperbola", ccc_centered_hyperbola)


        return  {'ccc1':ccc_centered_parabola, 'ccc2':ccc_centered_hyperbola,
                 'p':p, 'a':a, 'b':b, 'c':c, 'x_pmin':x_pmin, 'y_pmin':y_pmin}

    @classmethod
    def plot_histo(cls, plot_window, x, y, title, xtitle, ytitle, color='blue', replace=True, symbol=''):
        import matplotlib
        matplotlib.rcParams['axes.formatter.useoffset']='False'

        plot_window.addCurve(x, y, title, symbol=symbol, color=color, xlabel=xtitle, ylabel=ytitle, replace=replace) #'+', '^', ','

        if not xtitle is None: plot_window.setGraphXLabel(xtitle)
        if not ytitle is None: plot_window.setGraphYLabel(ytitle)
        if not title is None: plot_window.setGraphTitle(title)

        plot_window.resetZoom()
        plot_window.replot()

        plot_window.setActiveCurve(title)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWWolterCenteredCalculator()
    w.show()
    app.exec()
    w.saveSettings()
