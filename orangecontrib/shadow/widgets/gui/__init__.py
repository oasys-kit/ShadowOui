__author__ = 'labx'

############ ADDED BY LUCA REBUFFI 21-02-2014 - begin
#QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
try:
    from PyQt5 import QtWidgets
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create("Plastique"))
    QtWidgets.QApplication.setPalette(QtWidgets.QApplication.style().standardPalette())
except:
    pass
############ ADDED BY LUCA REBUFFI 21-02-2014 - end


