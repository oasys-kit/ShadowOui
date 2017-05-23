import sys

from PyQt5.QtWidgets import QTextEdit, QApplication, QMessageBox
from PyQt5.QtGui import QTextCursor, QIntValidator, QDoubleValidator
from Shadow.ShadowPreprocessorsXraylib import bragg
from oasys.widgets.widget import OWWidget
from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream
try:
    from ..tools.xoppy_calc import xoppy_doc
except ImportError:
    #print("Error importing: xoppy_doc")
    #raise
    pass
except SystemError:
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData

class OWxsh_bragg(OWWidget):
    name = "Bragg"
    id = "xsh_bragg"
    description = "Calculation of crystal diffraction profile"
    icon = "icons/bragg.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 1
    category = ""
    keywords = ["oasys", "bragg"]

    outputs = [{"name":"PreProcessor_Data",
                "type":ShadowPreProcessorData,
                "doc":"PreProcessor Data",
                "id":"PreProcessor_Data"}]

    want_main_area = False

    DESCRIPTOR = Setting(0)
    H_MILLER_INDEX = Setting(1)
    K_MILLER_INDEX = Setting(1)
    L_MILLER_INDEX = Setting(1)
    TEMPERATURE_FACTOR = Setting(1.0)
    E_MIN = Setting(5000.0)
    E_MAX = Setting(15000.0)
    E_STEP = Setting(100.0)
    SHADOW_FILE = Setting("bragg.dat")

    crystals = [
        "Si",
        "Si_NIST",
        "Si2",
        "Ge",
        "Diamond",
        "GaAs",
        "GaSb",
        "GaP",
        "InAs",
        "InP",
        "InSb",
        "SiC",
        "NaCl",
        "CsF",
        "LiF",
        "KCl",
        "CsCl",
        "Be",
        "Graphite",
        "PET",
        "Beryl",
        "KAP",
        "RbAP",
        "TlAP",
        "Muscovite",
        "AlphaQuartz",
        "Copper",
        "LiNbO3",
        "Platinum",
        "Gold",
        "Sapphire",
        "LaB6",
        "LaB6_NIST",
        "KTP",
        "AlphaAlumina",
        "Aluminum",
        "Iron",
        "Titanium"
    ]


    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        self.setFixedWidth(500)
        self.setFixedHeight(520)

        idx = -1 
        
        gui.separator(self.controlArea)

        box0 = oasysgui.widgetBox(self.controlArea, "",orientation="horizontal")
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Help", callback=self.help1)
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        #widget index 0
        idx += 1 
        box = oasysgui.widgetBox(self.controlArea, "Crystal Parameters", orientation="vertical")
        gui.comboBox(box, self, "DESCRIPTOR",
                     label=self.unitLabels()[idx], addSpace=True,
                     items=self.crystals, sendSelectedValue=False,
                     valueType=int, orientation="horizontal", labelWidth=350)
        self.show_at(self.unitFlags()[idx], box)
        
        #widget index 1 
        idx += 1 
        box_miller = oasysgui.widgetBox(box, "", orientation = "horizontal")
        oasysgui.lineEdit(box_miller, self, "H_MILLER_INDEX",
                     label="Miller Indices [h k l]", addSpace=True,
                    valueType=int, validator=QIntValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box_miller)
        
        #widget index 2 
        idx += 1 
        oasysgui.lineEdit(box_miller, self, "K_MILLER_INDEX", addSpace=True,
                    valueType=int, validator=QIntValidator())
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 3 
        idx += 1 
        oasysgui.lineEdit(box_miller, self, "L_MILLER_INDEX",
                     addSpace=True,
                    valueType=int, validator=QIntValidator(), orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 

        gui.separator(box)

        #widget index 4 
        idx += 1 
        oasysgui.lineEdit(box, self, "TEMPERATURE_FACTOR",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 5 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_MIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 6 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_MAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 7 
        idx += 1 
        oasysgui.lineEdit(box, self, "E_STEP",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 8 
        idx += 1
        box_2 = oasysgui.widgetBox(box, "", addSpace=True, orientation="horizontal")

        self.le_SHADOW_FILE = oasysgui.lineEdit(box_2, self, "SHADOW_FILE",
                                                 label=self.unitLabels()[idx], addSpace=True, labelWidth=180, orientation="horizontal")

        gui.button(box_2, self, "...", callback=self.selectFile)

        self.show_at(self.unitFlags()[idx], box)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(self.controlArea, "System Output", addSpace=True, orientation="horizontal", height=150)
        out_box.layout().addWidget(self.shadow_output)

        self.process_showers()

        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Crystal descriptor','H miller index','K miller index','L miller index','Temperature factor','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]','File name (for SHADOW)']


    def unitFlags(self):
         return ['True','True','True','True','True','True','True','True','True']

    def selectFile(self):
        self.le_SHADOW_FILE.setText(oasysgui.selectFileFromDialog(self, self.SHADOW_FILE, "Select Output File"))

    def compute(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.checkFields()

            tmp = bragg(interactive=False,
                        DESCRIPTOR=self.crystals[self.DESCRIPTOR],
                        H_MILLER_INDEX=self.H_MILLER_INDEX,
                        K_MILLER_INDEX=self.K_MILLER_INDEX,
                        L_MILLER_INDEX=self.L_MILLER_INDEX,
                        TEMPERATURE_FACTOR=self.TEMPERATURE_FACTOR,
                        E_MIN=self.E_MIN,
                        E_MAX=self.E_MAX,
                        E_STEP=self.E_STEP,
                        SHADOW_FILE=congruence.checkFileName(self.SHADOW_FILE))

            self.send("PreProcessor_Data", ShadowPreProcessorData(bragg_data_file=self.SHADOW_FILE))
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 str(exception),
                                 QMessageBox.Ok)

    def checkFields(self):
        if type(self.DESCRIPTOR) == str: # back compatibility with old version
            try:
                self.DESCRIPTOR = self.crystals.index(self.DESCRIPTOR)
            except:
                self.DESCRIPTOR = 0

        self.H_MILLER_INDEX = congruence.checkNumber(self.H_MILLER_INDEX, "H miller index")
        self.K_MILLER_INDEX = congruence.checkNumber(self.K_MILLER_INDEX, "K miller index")
        self.L_MILLER_INDEX = congruence.checkNumber(self.L_MILLER_INDEX, "L miller index")
        self.TEMPERATURE_FACTOR = congruence.checkNumber(self.TEMPERATURE_FACTOR, "Temperature factor")
        self.E_MIN  = congruence.checkPositiveNumber(self.E_MIN , "Minimum energy")
        self.E_MAX  = congruence.checkStrictlyPositiveNumber(self.E_MAX , "Maximum Energy")
        self.E_STEP = congruence.checkStrictlyPositiveNumber(self.E_STEP, "Energy step")
        congruence.checkLessOrEqualThan(self.E_MIN, self.E_MAX, "From Energy", "To Energy")
        congruence.checkDir(self.SHADOW_FILE)

    def defaults(self):
         self.resetSettings()
         self.compute()
         return

    def help1(self):
        print("help pressed.")
        try:
            xoppy_doc('xsh_bragg')
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
    w = OWxsh_bragg()
    w.show()
    app.exec()
    w.saveSettings()
