import os, sys

from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from PyQt5.QtGui import QTextCursor, QIntValidator, QDoubleValidator, QPixmap
from PyQt5.QtCore import Qt
from Shadow.ShadowPreprocessorsXraylib import pre_mlayer

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData
from orangecontrib.shadow.util.shadow_util import ShadowPhysics

class OWxsh_pre_mlayer(OWWidget):
    name = "PreMLayer"
    id = "xsh_pre_mlayer"
    description = "Calculation of multilayer mirror reflectivity profile"
    icon = "icons/premlayer.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 3
    category = ""
    keywords = ["xoppy", "xsh_pre_mlayer"]

    outputs = [{"name":"PreProcessor_Data",
                "type":ShadowPreProcessorData,
                "doc":"PreProcessor Data",
                "id":"PreProcessor_Data"}]

    want_main_area = False

    FILE = Setting("mlayer.dat")
    E_MIN = Setting(5000.0)
    E_MAX = Setting(20000.0)
    S_DENSITY = Setting("2.33")
    S_MATERIAL = Setting("Si")
    E_DENSITY = Setting("2.40")
    E_MATERIAL = Setting("B4C")
    O_DENSITY = Setting("9.40")
    O_MATERIAL = Setting("Ru")
    GRADE_DEPTH = Setting(0)
    N_PAIRS = Setting(70)
    THICKNESS = Setting(33.1)
    GAMMA = Setting(0.483)
    ROUGHNESS_EVEN = Setting(3.3)
    ROUGHNESS_ODD = Setting(3.1)
    FILE_DEPTH = Setting("myfile_depth.dat")
    GRADE_SURFACE = Setting(0)
    FILE_SHADOW = Setting("mlayer1.sha")
    FILE_THICKNESS = Setting("mythick.dat")
    FILE_GAMMA = Setting("mygamma.dat")
    AA0 = Setting(1.0)
    AA1 = Setting(0.0)
    AA2 = Setting(0.0)
    AA3 = Setting(0.0)

    MAX_WIDTH = 700
    MAX_HEIGHT = 560

    CONTROL_AREA_WIDTH = 685
    TABS_AREA_HEIGHT = 455

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "premlayer_usage.png")

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(self.MAX_WIDTH)
        self.setFixedHeight(self.MAX_HEIGHT)

        gui.separator(self.controlArea)

        box0 = gui.widgetBox(self.controlArea, "",orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Help", callback=self.help1)
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_input = oasysgui.createTabPage(tabs_setting, "Basic Settings")
        tab_input_2 = oasysgui.createTabPage(tabs_setting, "Bilayer Settings")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        box = gui.widgetBox(tab_input, "Multilayer Parameters",orientation="vertical")

        idx = -1 
        
        #widget index 0 
        idx += 1 

        box_file = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_FILE = oasysgui.lineEdit(box_file, self, "FILE",
                       label=self.unitLabels()[idx], addSpace=True, labelWidth=380, orientation="horizontal")

        gui.button(box_file, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

        #widget index 1
        idx += 1
        oasysgui.lineEdit(box, self, "E_MIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 2
        idx += 1
        oasysgui.lineEdit(box, self, "E_MAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 4
        idx += 1
        oasysgui.lineEdit(box, self, "S_MATERIAL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=550, orientation="horizontal", callback=self.set_SDensity)
        self.show_at(self.unitFlags()[idx], box)

        #widget index 3
        idx += 1
        oasysgui.lineEdit(box, self, "S_DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 6
        idx += 1
        oasysgui.lineEdit(box, self, "E_MATERIAL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=550, orientation="horizontal", callback=self.set_EDensity)
        self.show_at(self.unitFlags()[idx], box)

        #widget index 5
        idx += 1
        oasysgui.lineEdit(box, self, "E_DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 8
        idx += 1
        oasysgui.lineEdit(box, self, "O_MATERIAL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=550, orientation="horizontal", callback=self.set_ODensity)
        self.show_at(self.unitFlags()[idx], box)

        #widget index 7
        idx += 1
        oasysgui.lineEdit(box, self, "O_DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        box_byl = gui.widgetBox(tab_input_2, "Multilayer Parameters",orientation="vertical")

        #widget index 9
        idx += 1
        gui.comboBox(box_byl, self, "GRADE_DEPTH",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['No (Constant)', 'thicknesses, gamma, rough_even, rough_odd from file '],
                     valueType=int, orientation="horizontal", labelWidth=270)
        self.show_at(self.unitFlags()[idx], box)


        box_2 = oasysgui.widgetBox(box_byl, "",orientation="vertical", height=160)

        #widget index 10
        idx += 1
        oasysgui.lineEdit(box_2, self, "N_PAIRS",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=int, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 11
        idx += 1
        oasysgui.lineEdit(box_2, self, "THICKNESS",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 12
        idx += 1
        oasysgui.lineEdit(box_2, self, "GAMMA",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 13
        idx += 1
        oasysgui.lineEdit(box_2, self, "ROUGHNESS_EVEN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 14
        idx += 1
        oasysgui.lineEdit(box_2, self, "ROUGHNESS_ODD",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_2)

        #widget index 15
        idx += 1
        box_file_depth = oasysgui.widgetBox(box_byl, "", addSpace=True, orientation="horizontal", height=160)

        self.le_FILE_DEPTH = oasysgui.lineEdit(box_file_depth, self, "FILE_DEPTH",
                                               label=self.unitLabels()[idx], addSpace=True, labelWidth=400, orientation="horizontal")

        gui.button(box_file_depth, self, "...", callback=self.selectFileDepth)

        self.show_at(self.unitFlags()[idx], box_file_depth)

        #widget index 16
        idx += 1
        gui.comboBox(box_byl, self, "GRADE_SURFACE",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=['No (Constant)', 'thick and gamma graded (from spline files)', 'thickness graded (from quadratic fit)'],
                     valueType=int, orientation="horizontal", labelWidth=380)
        self.show_at(self.unitFlags()[idx], box)


        box_3_empty = oasysgui.widgetBox(box_byl, "", orientation="vertical", height=100)
        self.show_at("self.GRADE_SURFACE == 0", box_3_empty)

        box_3 = oasysgui.widgetBox(box_byl, "", orientation="vertical", height=100)

        #widget index 17
        idx += 1
        box_file_shadow = oasysgui.widgetBox(box_3, "", addSpace=True, orientation="horizontal")

        self.le_FILE_SHADOW = oasysgui.lineEdit(box_file_shadow, self, "FILE_SHADOW",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=400, orientation="horizontal")

        gui.button(box_file_shadow, self, "...", callback=self.selectFileShadow)

        self.show_at(self.unitFlags()[idx], box_3)

        #widget index 18
        idx += 1
        box_file_thickness = oasysgui.widgetBox(box_3, "", addSpace=True, orientation="horizontal")

        self.le_FILE_THICKNESS = oasysgui.lineEdit(box_file_thickness, self, "FILE_THICKNESS",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=400, orientation="horizontal")

        gui.button(box_file_thickness, self, "...", callback=self.selectFileThickness)

        self.show_at(self.unitFlags()[idx], box_3)

        #widget index 19
        idx += 1
        box_file_gamma = oasysgui.widgetBox(box_3, "", addSpace=True, orientation="horizontal")

        self.le_FILE_GAMMA = oasysgui.lineEdit(box_file_gamma, self, "FILE_GAMMA",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=400, orientation="horizontal")

        gui.button(box_file_gamma, self, "...", callback=self.selectFileGamma)

        self.show_at(self.unitFlags()[idx], box_3)

        box_4 = oasysgui.widgetBox(box_byl, "",orientation="vertical", height=100)

        #widget index 20
        idx += 1
        oasysgui.lineEdit(box_4, self, "AA0",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_4)

        #widget index 21
        idx += 1
        oasysgui.lineEdit(box_4, self, "AA1",
                     label=self.unitLabels()[idx], addSpace=True,
                     valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_4)

        #widget index 22
        idx += 1
        oasysgui.lineEdit(box_4, self, "AA2",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_4)

        #widget index 23
        idx += 1
        oasysgui.lineEdit(box_4, self, "AA3",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, labelWidth=550, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_4)

        self.process_showers()

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Output file (for SHADOW/trace): ',
                 'Min Energy [eV]','Max Energy [eV]',
                 'Material (substrate) (element or formula)',
                 'Density (substrate) [g/cm3]',
                 'Material (even sublayer) (element or formula)',
                 'Density (even "bottom" sublayer) [g/cm3]',
                 'Material (odd sublayer) (element or formula)',
                 'Density (odd "top" sublayer) [g/cm3]',
                 'Bilayer thicknesses graded along the depth? ',
                 'Number of bilayers ',
                 'bilayer thickness t [A]',
                 'gamma ratio [t_even/(t_odd+t_even)]',
                 'Roughness even layer [A]',
                 'Roughness odd layer [A]',
                 'File with list of t_bilayer, gamma, roughness_even, roughness_odd',
                 'Bilayer thicknesses/gamma graded along the surface? ',
                 'Output binary file (for SHADOW) with splines',
                 'File with bilayer thicknesses versus surface (PRESURFACE format)',
                 'File with bilayer gamma versus surface (PRESURFACE format)',
                 'Fit bilayer t(y)/t(y=0) vs y: zero-order coefficient (constant)',
                 'Fit bilayer t(y)/t(y=0) vs y: linear coefficient (slope)',
                 'Fit bilayer t(y)/t(y=0) vs y: 2nd degree coefficient',
                 'Fit bilayer t(y)/t(y=0) vs y: 3rd degree coefficient']


    def unitFlags(self):
         return ['True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'True',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  0',
                 'self.GRADE_DEPTH  ==  1',
                 'True',
                 'self.GRADE_SURFACE  ==  1',
                 'self.GRADE_SURFACE  ==  1',
                 'self.GRADE_SURFACE  ==  1',
                 'self.GRADE_SURFACE  ==  2',
                 'self.GRADE_SURFACE  ==  2',
                 'self.GRADE_SURFACE  ==  2',
                 'self.GRADE_SURFACE  ==  2']

    def set_SDensity(self):
        if not self.S_MATERIAL is None:
            if not self.S_MATERIAL.strip() == "":
                self.S_MATERIAL = self.S_MATERIAL.strip()
                self.S_DENSITY = ShadowPhysics.getMaterialDensity(self.S_MATERIAL)

    def set_EDensity(self):
        if not self.E_MATERIAL is None:
            if not self.E_MATERIAL.strip() == "":
                self.E_MATERIAL = self.E_MATERIAL.strip()
                self.E_DENSITY = ShadowPhysics.getMaterialDensity(self.E_MATERIAL)
                
    def set_ODensity(self):
        if not self.O_MATERIAL is None:
            if not self.O_MATERIAL.strip() == "":
                self.O_MATERIAL = self.O_MATERIAL.strip()
                self.O_DENSITY = ShadowPhysics.getMaterialDensity(self.O_MATERIAL)

    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            if self.GRADE_DEPTH == 0:
                FILE_DEPTH = "NONE"
            else:
                FILE_DEPTH = congruence.checkFileName(self.FILE_DEPTH)

            if self.GRADE_SURFACE == 1:
                FILE_SHADOW    = congruence.checkFileName(self.FILE_SHADOW)
                FILE_THICKNESS = congruence.checkFileName(self.FILE_THICKNESS)
                FILE_GAMMA     = congruence.checkFileName(self.FILE_GAMMA)
            else:
                FILE_SHADOW    = "NONE"
                FILE_THICKNESS = "NONE"
                FILE_GAMMA     = "NONE"

            tmp = pre_mlayer(interactive=False,
                             FILE=congruence.checkFileName(self.FILE),
                             E_MIN=self.E_MIN,
                             E_MAX=self.E_MAX,
                             S_DENSITY=self.S_DENSITY,
                             S_MATERIAL=self.S_MATERIAL,
                             E_DENSITY=self.E_DENSITY,
                             E_MATERIAL=self.E_MATERIAL,
                             O_DENSITY=self.O_DENSITY,
                             O_MATERIAL=self.O_MATERIAL,
                             GRADE_DEPTH=self.GRADE_DEPTH,
                             N_PAIRS=self.N_PAIRS,
                             THICKNESS=self.THICKNESS,
                             GAMMA=self.GAMMA,
                             ROUGHNESS_EVEN=self.ROUGHNESS_EVEN,
                             ROUGHNESS_ODD=self.ROUGHNESS_ODD,
                             FILE_DEPTH=FILE_DEPTH,
                             GRADE_SURFACE=self.GRADE_SURFACE,
                             FILE_SHADOW=FILE_SHADOW,
                             FILE_THICKNESS=FILE_THICKNESS,
                             FILE_GAMMA=FILE_GAMMA,
                             AA0=self.AA0,
                             AA1=self.AA1,
                             AA2=self.AA2,
                             AA3=self.AA3,
                             )

            self.send("PreProcessor_Data", ShadowPreProcessorData(m_layer_data_file_dat=self.FILE, m_layer_data_file_sha=self.FILE_SHADOW))
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

    def checkFields(self):
        congruence.checkDir(self.FILE)
        self.E_MIN  = congruence.checkPositiveNumber(self.E_MIN , "Min Energy")
        self.E_MAX  = congruence.checkStrictlyPositiveNumber(self.E_MAX , "Max Energy")
        congruence.checkLessOrEqualThan(self.E_MIN, self.E_MAX, "Minimum Energy", "Maximum Energy")
        self.S_MATERIAL = ShadowPhysics.checkCompoundName(self.S_MATERIAL)
        self.S_DENSITY = congruence.checkStrictlyPositiveNumber(float(self.S_DENSITY), "Density (substrate)")
        self.E_MATERIAL = ShadowPhysics.checkCompoundName(self.E_MATERIAL)
        self.E_DENSITY = congruence.checkStrictlyPositiveNumber(float(self.E_DENSITY), "Density (even sublayer)")
        self.O_MATERIAL = ShadowPhysics.checkCompoundName(self.O_MATERIAL)
        self.O_DENSITY = congruence.checkStrictlyPositiveNumber(float(self.O_DENSITY), "Density (odd sublayer)")

        if self.GRADE_DEPTH == 0:
            self.N_PAIRS = congruence.checkStrictlyPositiveNumber(int(self.N_PAIRS), "Number of bilayers")
            self.THICKNESS = congruence.checkStrictlyPositiveNumber(float(self.THICKNESS), "bilayer thickness t")
            self.GAMMA = congruence.checkStrictlyPositiveNumber(float(self.GAMMA), "gamma ratio")
            self.ROUGHNESS_EVEN = congruence.checkPositiveNumber(float(self.ROUGHNESS_EVEN), "Roughness even layer")
            self.ROUGHNESS_ODD = congruence.checkPositiveNumber(float(self.ROUGHNESS_ODD), "Roughness odd layer")
        else:
            congruence.checkDir(self.FILE_DEPTH)

        if self.GRADE_SURFACE == 1:
            congruence.checkDir(self.FILE_SHADOW)
            congruence.checkDir(self.FILE_THICKNESS)
            congruence.checkDir(self.FILE_GAMMA)
        elif self.GRADE_SURFACE == 2:
            self.AA0 = congruence.checkNumber(float(self.AA0), "zero-order coefficient")
            self.AA1 = congruence.checkNumber(float(self.AA1), "linear coefficient")
            self.AA2 = congruence.checkNumber(float(self.AA2), "2nd degree coefficient")
            self.AA3 = congruence.checkNumber(float(self.AA3), "3rd degree coefficient")

    def selectFile(self):
        self.le_FILE.setText(oasysgui.selectFileFromDialog(self, self.FILE, "Select Output File", file_extension_filter="Data Files (*.dat)"))

    def selectFileDepth(self):
        self.le_FILE_DEPTH.setText(oasysgui.selectFileFromDialog(self, self.FILE_DEPTH, "Open File with list of t_bilayer,gamma,roughness_even,roughness_odd", file_extension_filter="Data Files (*.dat)"))

    def selectFileThickness(self):
        self.le_FILE_THICKNESS.setText(oasysgui.selectFileFromDialog(self, self.FILE_THICKNESS, "Open File with bilayer thicknesses versus surface (PRESURFACE format)", file_extension_filter="Data Files (*.dat)"))

    def selectFileShadow(self):
        self.le_FILE_SHADOW.setText(oasysgui.selectFileFromDialog(self, self.FILE_SHADOW, "Select Output binary file (for SHADOW) with splines", file_extension_filter="Data Files (*.dat)"))

    def selectFileGamma(self):
        self.le_FILE_GAMMA.setText(oasysgui.selectFileFromDialog(self, self.FILE_GAMMA, "Open File with bilayer gamma versus surface (PRESURFACE format)", file_extension_filter="Data Files (*.dat)"))

    def defaults(self):
         self.resetSettings()
         #self.compute()
         return

    def help1(self):
        print("help pressed.")
        try:
            xoppy_doc('xsh_pre_mlayer')
        except:
            pass

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWxsh_pre_mlayer()
    w.show()
    app.exec_()
    w.saveSettings()
