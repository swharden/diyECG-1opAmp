"""
diyECG GUI for monitoring live ECG through sound card input (by Scott Harden).
If you haven't built the circuit, test this software by playing demo_ecg.wav
while you run this software. If you don't use a virtual audio cable to connect
the output (speaker jack) to the input (default microphone jack), consider
running an actual cable to connect these two.
"""

from PyQt4 import QtGui,QtCore
import sys
import ui_main
import numpy as np
import pyqtgraph
import swhear
import time
import pyqtgraph.exporters
import webbrowser

class ExampleApp(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        pyqtgraph.setConfigOption('background', 'w') #before loading widget
        super(ExampleApp, self).__init__(parent)
        self.setupUi(self)
        self.grECG.plotItem.showGrid(True, True, 0.7)
        self.btnSave.clicked.connect(self.saveFig)
        self.btnSite.clicked.connect(self.website)
        stamp="DIY ECG by Scott Harden"
        self.stamp = pyqtgraph.TextItem(stamp,anchor=(-.01,1),color=(150,150,150),
                                        fill=pyqtgraph.mkBrush('w'))
        self.ear = swhear.Ear(chunk=int(100)) # determines refresh rate
        if len(self.ear.valid_input_devices()):
            self.ear.stream_start()
            self.lblDevice.setText(self.ear.msg)
            self.update()

    def closeEvent(self, event):
        self.ear.close()
        event.accept()

    def saveFig(self):
        fname="ECG_%d.png"%time.time()
        exp = pyqtgraph.exporters.ImageExporter(self.grECG.plotItem)
        exp.parameters()['width'] = 1000
        exp.export(fname)
        print("saved",fname)

    def update(self):
        t1,timeTook=time.time(),0
        if len(self.ear.data) and not self.btnPause.isChecked():
            freqHighCutoff=0
            if self.spinLowpass.value()>0:
                freqHighCutoff=self.spinLowpass.value()
            data=self.ear.getFiltered(freqHighCutoff)
            if self.chkInvert.isChecked():
                data=np.negative(data)
            if self.chkAutoscale.isChecked():
                self.Yscale=np.max(np.abs(data))*1.1
            self.grECG.plotItem.setRange(xRange=[0,self.ear.maxMemorySec],
                            yRange=[-self.Yscale,self.Yscale],padding=0)
            self.grECG.plot(np.arange(len(data))/float(self.ear.rate),data,clear=True,
                            pen=pyqtgraph.mkPen(color='r'),antialias=True)
            self.grECG.plotItem.setTitle(self.lineTitle.text(),color=(0,0,0))
            self.stamp.setPos(0,-self.Yscale)
            self.grECG.plotItem.addItem(self.stamp)
            timeTook=(time.time()-t1)*1000
            print("plotting took %.02f ms"%(timeTook))
        msTillUpdate=int(self.ear.chunk/self.ear.rate*1000)-timeTook
        QtCore.QTimer.singleShot(max(0,msTillUpdate), self.update)

    def website(self):
        webbrowser.open("http://www.SWHarden.com")

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    app.exec_()
