__author__ = 'labx'

from orangewidget import widget
from orangecontrib.shadow.widgets.gui import ow_generic_element


class Source(ow_generic_element.GenericElement):

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box)

        self.runaction = widget.OWAction("Run Shadow/Source", self)
        self.runaction.triggered.connect(self.run)
        self.addAction(self.runaction)

    def run(self):
        self.runShadowSource()

    def runShadowSource(self):
        pass
