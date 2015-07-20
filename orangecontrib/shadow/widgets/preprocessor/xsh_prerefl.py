import sys
from PyQt4.QtGui import QTextEdit, QTextCursor, QDoubleValidator, QApplication
from oasys.widgets import widget
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from Shadow.ShadowPreprocessorsXraylib import prerefl

try:
    from ..tools.xoppy_calc import xoppy_doc
except ImportError:
    #print("Error importing: xoppy_doc")
    #raise
    pass

try:
    from ..tools.xoppy_calc import xoppy_calc_xsh_prerefl
except ImportError:
    #print("compute pressed.")
    #print("Error importing: xoppy_calc_xsh_prerefl")
    #raise
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, EmittingStream
from orangecontrib.shadow.util.shadow_util import ShadowGui

class OWxsh_prerefl(widget.OWWidget):
    name = "xsh_prerefl"
    id = "orange.widgets.preprocessor.xsh_prerefl"
    description = "xoppy application to compute..."
    icon = "icons/prerefl.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 10
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


    def __init__(self):
        super().__init__()

        self.process_showers()

        box = ShadowGui.widgetBox(self.controlArea, "Reflectivity Parameters", orientation="vertical")
        
        idx = -1 
        
        #widget index 0 
        idx += 1 
        ShadowGui.lineEdit(box, self, "SYMBOL",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 1 
        idx += 1 
        ShadowGui.lineEdit(box, self, "DENSITY",
                     label=self.unitLabels()[idx], addSpace=True, valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 2 
        idx += 1 
        ShadowGui.lineEdit(box, self, "SHADOW_FILE",
                     label=self.unitLabels()[idx], addSpace=True, labelWidth=200, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 3 
        idx += 1 
        ShadowGui.lineEdit(box, self, "E_MIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 4 
        idx += 1 
        ShadowGui.lineEdit(box, self, "E_MAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box) 
        
        #widget index 5 
        idx += 1 
        ShadowGui.lineEdit(box, self, "E_STEP",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator(), labelWidth=350, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box)

        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = ShadowGui.widgetBox(self.controlArea, "System Output", addSpace=True, orientation="horizontal", height=150)
        out_box.layout().addWidget(self.shadow_output)

        box0 = gui.widgetBox(self.controlArea, "",orientation="horizontal") 
        #widget buttons: compute, set defaults, help
        button = gui.button(box0, self, "Compute", callback=self.compute)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Defaults", callback=self.defaults)
        button.setFixedHeight(45)
        button = gui.button(box0, self, "Help", callback=self.help1)
        button.setFixedHeight(45)


        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Element/Compound formula','Density [ g/cm3 ]','File for SHADOW (trace):','Minimum energy [eV]','Maximum energy [eV]','Energy step [eV]']


    def unitFlags(self):
         return ['True','True','True','True','True','True']

    def compute(self):
        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        tmp = prerefl(interactive=False,SYMBOL=self.SYMBOL,DENSITY=self.DENSITY,FILE=self.SHADOW_FILE,E_MIN=self.E_MIN,E_MAX=self.E_MAX,E_STEP=self.E_STEP)

        self.send("PreProcessor_Data", ShadowPreProcessorData(prerefl_data_file=self.SHADOW_FILE))

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
