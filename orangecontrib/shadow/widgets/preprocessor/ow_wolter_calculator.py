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

from shadow4.devel.wolter.wolter1 import recipe1, recipe2, recipe3, recipe4, rotate_and_shift_quartic
from orangecontrib.shadow.util.shadow_objects import ConicCoefficientsPreProcessorData

from oasys.util.oasys_util import EmittingStream

class OWWolterCalculator(OWWidget):
    name = "Wolter Calculator"
    id = "WolterCalculator"
    description = "Calculation of coefficients for Wolter systems"
    icon = "icons/wolter.png"
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

    setup_type = Setting(2)
    same_angle = Setting(1)

    p1 = Setting(1e11)
    q1 = Setting(3.808047)
    p2 = Setting(1.904995)
    q2 = Setting(10.0)
    distance = Setting(0.3)

    theta1 = Setting(0.0159872)
    theta2 = Setting(0.003)

    ratio_hyp = Setting(3.0)  # ratio_hyp = q_hyp / p_ell > 1.0
    m_hyp = Setting(1 / 3)

    # to send to shadow
    conic_coefficients1 = Setting([0] * 10)
    conic_coefficients2 = Setting([0] * 10)
    source_plane_distance1 = Setting(0.0)
    source_plane_distance2 = Setting(0.0)
    image_plane_distance1 = Setting(0.0)
    image_plane_distance2 = Setting(0.0)
    angles_respect_to1 = Setting(0)
    angles_respect_to2 = Setting(0)
    incidence_angle_deg1 = Setting(0.0)
    incidence_angle_deg2 = Setting(0.0)
    reflection_angle_deg1 = Setting(0.0)
    reflection_angle_deg2 = Setting(0.0)
    mirror_orientation_angle1 = Setting(0)
    mirror_orientation_angle2 = Setting(0)


    tab=[]

    usage_path = os.path.join(resources.package_dirname("orangecontrib.syned.widgets.gui"), "misc", "predabam_usage.png")

    def __init__(self):
        super().__init__()

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
                     items=["Wolter-I variable throw",
                            "Wolter-I fixed throw",
                            "Wolter-I common point",
                            "Wolter-I centered system",
                            ],
                     callback=self.update_panel, sendSelectedValue=False, orientation="horizontal")

        self.w_p1 = oasysgui.lineEdit(box, self, "p1", "Distance focus11-oe1 [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.w_q1 = oasysgui.lineEdit(box, self, "q1", "Distance oe1-focus12 [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.w_p2 = oasysgui.lineEdit(box, self, "p2", "Distance focus21-oe2 [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.w_q2 = oasysgui.lineEdit(box, self, "q2", "Distance oe2-focus22 [m]", labelWidth=260, valueType=float, orientation="horizontal")
        self.w_distance = oasysgui.lineEdit(box, self, "distance", "Distance oe1-oe2 [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.w_ratio_hyp = oasysgui.lineEdit(box, self, "ratio_hyp", "Ratio hyperbola=q2/p2>1", labelWidth=260, valueType=float, orientation="horizontal")
        self.w_m_hyp = oasysgui.lineEdit(box, self, "m_hyp", "Magnification hyperbola=p2/q2", labelWidth=260,
                                             valueType=float, orientation="horizontal")

        gui.separator(box)

        box_2 = oasysgui.widgetBox(tab_step_1, "angles", orientation="vertical")

        gui.comboBox(box_2, self, "same_angle", label="Same grazing angles", labelWidth=260,
                     items=["No",
                            "Yes",
                            ],
                     callback=self.update_panel, sendSelectedValue=False, orientation="horizontal")

        self.w_theta1 = oasysgui.lineEdit(box_2, self, "theta1", "Grazing angle oe1 [rad]", labelWidth=260, valueType=float, orientation="horizontal", callback=self.update_panel)
        self.w_theta2 = oasysgui.lineEdit(box_2, self, "theta2", "Grazing angle oe2 [rad]", labelWidth=260, valueType=float, orientation="horizontal")


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
        self.w_q1.setVisible(True)
        self.w_p2.setVisible(True)
        self.w_q2.setVisible(True)
        self.w_theta1.setVisible  (True)
        self.w_theta2.setVisible  (True)
        self.w_distance.setVisible(True)

        self.w_ratio_hyp.setEnabled(False)
        self.w_m_hyp.setEnabled(False)

        if self.setup_type == 0:
            self.w_p1.setEnabled(True)
            self.w_q1.setEnabled(True)
            self.w_p2.setEnabled(False)
            self.w_q2.setEnabled(False)
            self.w_theta1.setEnabled(True)
            self.w_theta2.setEnabled(True)
            self.w_distance.setEnabled(True)
        elif self.setup_type == 1:
            self.w_p1.setEnabled(True)
            self.w_q1.setEnabled(False)
            self.w_p2.setEnabled(True)
            self.w_q2.setEnabled(False)
            self.w_theta1.setEnabled(True)
            self.w_theta2.setEnabled(True)
            self.w_distance.setEnabled(True)
        elif self.setup_type == 2:
            self.w_p1.setEnabled(True)
            self.w_p2.setEnabled(True)
            self.w_p2.setEnabled(True)
            self.w_q2.setEnabled(False)
            self.w_theta1.setEnabled(True)
            self.same_angle = True
            self.w_distance.setEnabled(False)
        elif self.setup_type == 3:
            self.w_p1.setEnabled(True)
            self.w_q1.setEnabled(False)
            self.w_p2.setEnabled(True)
            self.w_q2.setEnabled(False)
            self.w_theta1.setEnabled(True)
            self.same_angle = True
            self.w_distance.setEnabled(False)
        else:
            raise Exception(NotImplementedError)


        if self.same_angle:
            self.theta2 = self.theta1
            self.w_theta1.setEnabled(True)
            self.w_theta2.setEnabled(False)
        else:
            self.w_theta1.setEnabled(True)
            self.w_theta2.setEnabled(True)

        if self.setup_type == 0:
            self.w_ratio_hyp.setEnabled(True)
            self.w_m_hyp.setEnabled(False)
        elif self.setup_type == 1:
            self.w_ratio_hyp.setEnabled(False)
            self.w_m_hyp.setEnabled(True)
        elif self.setup_type == 2:
            self.w_ratio_hyp.setEnabled(False)
            self.w_m_hyp.setEnabled(False)
            self.q2 = self.q1
            self.distance = 0.0
        elif self.setup_type == 3:
            self.w_ratio_hyp.setEnabled(False)
            self.w_m_hyp.setEnabled(False)
            self.q1 = 0
            self.q2 = 0
            self.distance = 0.0
        else:
            raise Exception(NotImplementedError)


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

            if self.setup_type == 0:
                tkt_ell, tkt_hyp = recipe1(
                    p_ell=self.p1,
                    q_ell=self.q1,
                    distance=self.distance,
                    theta=self.theta1,
                    ratio_hyp=self.ratio_hyp,
                )

                print("\n\n>>>>>\n\n")

                # correct for incidence in the negative Y
                ccc1 = tkt_hyp['ccc']
                ccc2 = rotate_and_shift_quartic(ccc1, omega=0.0, theta=0.0, phi=numpy.pi, )
                print(ccc2)

                self.p2 = tkt_hyp['p']
                self.q2 = tkt_hyp['q']
                self.theta2 = tkt_hyp['theta_grazing']
                self.m_hyp = 1/self.ratio_hyp

                print(tkt_ell)
                print(tkt_hyp)

            elif self.setup_type == 1:
                tkt_ell, tkt_hyp = recipe2(
                    p_ell=self.p1,
                    distance=self.distance,
                    p_hyp=self.p2,
                    theta=self.theta1,
                    m_hyp=self.m_hyp,
                    verbose=1,
                )

                print("\n\n>>>>>\n\n")
                # print(cyl(tkt_ell['ccc']))
                print(tkt_ell['ccc'])
                # correct for incidence in the negative Y
                ccc1 = tkt_hyp['ccc']
                ccc2 = rotate_and_shift_quartic(ccc1, omega=0.0, theta=0.0, phi=numpy.pi, )
                print(ccc2)

                self.q1 = tkt_ell['p']
                self.q2 = tkt_hyp['q']
                self.theta2 = tkt_hyp['theta_grazing']
                self.rat_hyp = 1/self.m_hyp

                print(tkt_ell)
                print(tkt_hyp)

            elif self.setup_type == 2:
                tkt_ell, tkt_hyp = recipe3(
                    p_ell=self.p1,
                    q_ell=self.q1,
                    p_hyp=self.p2,
                    theta=self.theta1,
                    verbose=1,
                )

                self.rat_hyp = self.q2 / self.p2
                self.m_hyp = self.p2 / self.q2

            elif self.setup_type == 3:
                tkt_ell, tkt_hyp = recipe4(
                    f11=self.p1,
                    f12=self.q1,
                    f21=self.p2,
                    f22=self.q2,
                    theta=self.theta1,
                    verbose=1,
                )

                self.rat_hyp = 0 # todo
                self.m_hyp = 0 # todo
            else:
                raise Exception(NotImplementedError)

            try:
                results_txt += "\nellipse a=%f" % tkt_ell['a']
                results_txt += "\nellipse b=%f" % tkt_ell['b']
                results_txt += "\nellipse c=%f" % tkt_ell['c']
                results_txt += "\nhyperbola a=%f" % tkt_hyp['a']
                results_txt += "\nhyperbola b=%f" % tkt_hyp['b']
                results_txt += "\nhyperbola c=%f" % tkt_hyp['c']
            except:
                pass

            ccc_ell = tkt_ell['ccc']
            ccc_hyp = tkt_hyp['ccc']

            self.conic_coefficients1 = ccc_ell
            self.conic_coefficients2 = ccc_hyp

            # ccc_hyp = rotate_and_shift_quartic(ccc_hyp, omega=0.0, theta=0.0, phi=numpy.pi, )

            results_txt += "\n\n\n    oe1(normalized)      oe2(normalized)"
            for i in range(10):
                results_txt += "\nccc[%d]       %10.4g       %10.4g  " % (i,
                                                                    ccc_ell[i]/ccc_ell[0], ccc_hyp[i]/ccc_hyp[0])

            results_txt += "\n\n\n    oe1           oe2 "
            for i in range(10):
                results_txt += "\nccc[%d]       %10.4g       %10.4g  " % (i, ccc_ell[i], ccc_hyp[i])




            #results_txt += "\nthrow=%f m" % (self.p1+self.distance+self.p2)
            self.design_output.setText(results_txt)

            print("\n\n\n\n")
            print("####################################################")
            print("# RAY-TRACING PHASE")
            print("####################################################\n")

            #
            # self.send("PreProcessor_Data", WolterSystemPreProcessorData(
            #     conic_coefficients1 = self.conic_coefficients1,
            #     conic_coefficients2 = self.conic_coefficients2,
            #     source_plane_distance1 = self.source_plane_distance1,
            #     source_plane_distance2 = self.source_plane_distance2,
            #     image_plane_distance1 = self.image_plane_distance1,
            #     image_plane_distance2 = self.image_plane_distance2,
            #     angles_respect_to1 = self.angles_respect_to1,
            #     angles_respect_to2 = self.angles_respect_to2,
            #     incidence_angle_deg1 = self.incidence_angle_deg1,
            #     incidence_angle_deg2 = self.incidence_angle_deg2,
            #     reflection_angle_deg1 = self.reflection_angle_deg1,
            #     reflection_angle_deg2 = self.reflection_angle_deg2,
            #     mirror_orientation_angle1 = self.mirror_orientation_angle1,
            #     mirror_orientation_angle2 = self.mirror_orientation_angle2,
            # ))

            self.send("ConicCoeff_1_PreProcessor_Data", ConicCoefficientsPreProcessorData(
                conic_coefficient_0 = self.conic_coefficients1[0],
                conic_coefficient_1 = self.conic_coefficients1[1],
                conic_coefficient_2 = self.conic_coefficients1[2],
                conic_coefficient_3 = self.conic_coefficients1[3],
                conic_coefficient_4 = self.conic_coefficients1[4],
                conic_coefficient_5 = self.conic_coefficients1[5],
                conic_coefficient_6 = self.conic_coefficients1[6],
                conic_coefficient_7 = self.conic_coefficients1[7],
                conic_coefficient_8 = self.conic_coefficients1[8],
                conic_coefficient_9 = self.conic_coefficients1[9],
                source_plane_distance=None,
                image_plane_distance=None,
                angles_respect_to=None,
                incidence_angle_deg=None,
                reflection_angle_deg=None,
                mirror_orientation_angle=None,
                ))
            self.send("ConicCoeff_2_PreProcessor_Data", ConicCoefficientsPreProcessorData(
                conic_coefficient_0=self.conic_coefficients2[0],
                conic_coefficient_1=self.conic_coefficients2[1],
                conic_coefficient_2=self.conic_coefficients2[2],
                conic_coefficient_3=self.conic_coefficients2[3],
                conic_coefficient_4=self.conic_coefficients2[4],
                conic_coefficient_5=self.conic_coefficients2[5],
                conic_coefficient_6=self.conic_coefficients2[6],
                conic_coefficient_7=self.conic_coefficients2[7],
                conic_coefficient_8=self.conic_coefficients2[8],
                conic_coefficient_9=self.conic_coefficients2[9],
                source_plane_distance=None,
                image_plane_distance=None,
                angles_respect_to=None,
                incidence_angle_deg=None,
                reflection_angle_deg=None,
                mirror_orientation_angle=None,
                ))

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)


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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWWolterCalculator()
    w.show()
    app.exec()
    w.saveSettings()
