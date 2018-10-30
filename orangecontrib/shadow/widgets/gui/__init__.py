__author__ = 'labx'

from PyQt5 import QtWidgets

############ ADDED BY LUCA REBUFFI 21-02-2014 - begin
#QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
try:
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Plastique"))
    QtWidgets.QApplication.setPalette(QtWidgets.QApplication.style().standardPalette())
except:
    pass
############ ADDED BY LUCA REBUFFI 21-02-2014 - end


