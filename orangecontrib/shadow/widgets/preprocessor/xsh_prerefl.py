import os, sys

from PyQt5.QtWidgets import QLabel, QApplication, QMessageBox, QSizePolicy
from PyQt5.QtGui import QTextCursor, QPixmap, QDoubleValidator
from PyQt5.QtCore import Qt
from Shadow.ShadowPreprocessorsXraylib import prerefl

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

try:
    from ..tools.xoppy_calc import xoppy_doc
except ImportError:
    pass
except SystemError:
    pass

from oasys.util.oasys_util import EmittingStream
from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData
from orangecontrib.shadow.util.shadow_util import ShadowPhysics

class OWxsh_prerefl(OWWidget):
    name = "PreRefl"
    id = "xsh_prerefl"
    description = "Calculation of mirror reflectivity profile"
    icon = "icons/prerefl.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 2
    category = ""
    keywords = ["xoppy", "xsh_prerefl"]

    outputs = [{"name":"PreProcessor_Data",
                "type":ShadowPreProcessorData,
                "doc":"PreProcessor Data",
                "id":"PreProcessor_Data"}]

    want_main_area = False

    SYMBOL = Setting("SiC")
    DENSITY = Setting(3.217)
    SHADOW_FILE = Setting("reflec.dat")
    E_MIN = Setting(100.0)
    E_MAX = Setting(20000.0)
    E_STEP = Setting(100.0)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui") , "misc", "prerefl_usage.png")

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(550)
        self.setFixedHeight(550)

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

        tab_bas = oasysgui.createTabPage(tabs_setting, "Reflectivity Settings")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        box = oasysgui.widgetBox(tab_bas, "Reflectivity Parameters", orientation="vertical")
        
        idx = -1 
        
        #widget index 0 
        idx += 1 
        oasysgui.lineEdit(box, self, "SYMBOL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal", callback=self.set_Density)
        self.show_at(self.unitFlags()[idx], box)

        #widget index 1
        idx += 1
        oasysgui.lineEdit(box, self, "DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 2
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_SHADOW_FILE = oasysgui.lineEdit(box_2, self, "SHADOW_FILE",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=180, orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

        #widget index 3
        idx += 1
        oasysgui.lineEdit(box, self, "E_MIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 4
        idx += 1
        oasysgui.lineEdit(box, self, "E_MAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        #widget index 5
        idx += 1
        oasysgui.lineEdit(box, self, "E_STEP",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        self.process_showers()

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=400)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Element/Compound formula','Density [ g/cm3 ]','File for SHADOW (trace):','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]']

    def unitFlags(self):
         return ['True','True','True','True','True','True']

    def selectFile(self):
        self.le_SHADOW_FILE.setText(oasysgui.selectFileFromDialog(self, self.SHADOW_FILE, "Select Output File", file_extension_filter="Data Files (*.dat)"))

    def set_Density(self):
        if not self.SYMBOL is None:
            if not self.SYMBOL.strip() == "":
                self.SYMBOL = self.SYMBOL.strip()
                self.DENSITY = ShadowPhysics.getMaterialDensity(self.SYMBOL)


    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            tmp = prerefl(interactive=False,
                          SYMBOL=self.SYMBOL,
                          DENSITY=self.DENSITY,
                          FILE=congruence.checkFileName(self.SHADOW_FILE),
                          E_MIN=self.E_MIN,
                          E_MAX=self.E_MAX,
                          E_STEP=self.E_STEP)

            self.send("PreProcessor_Data", ShadowPreProcessorData(prerefl_data_file=self.SHADOW_FILE))
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

    def checkFields(self):
        self.SYMBOL = ShadowPhysics.checkCompoundName(self.SYMBOL)
        self.DENSITY = congruence.checkStrictlyPositiveNumber(self.DENSITY, "Density")
        self.E_MIN  = congruence.checkPositiveNumber(self.E_MIN , "Minimum Energy")
        self.E_MAX  = congruence.checkStrictlyPositiveNumber(self.E_MAX , "Maximum Energy")
        self.E_STEP = congruence.checkStrictlyPositiveNumber(self.E_STEP, "Energy step")
        congruence.checkLessOrEqualThan(self.E_MIN, self.E_MAX, "Minimum Energy", "Maximum Energy")
        congruence.checkDir(self.SHADOW_FILE)

    def defaults(self):
         self.resetSettings()
         self.compute()
         return

    def help1(self):
        print("help pressed.")
        xoppy_doc('xsh_prerefl')

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWxsh_prerefl()
    w.show()
    app.exec()
    w.saveSettings()
