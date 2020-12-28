# Import libraries
import numpy as np
import sys
import time

from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

from known_devices import gStrength
from serial_device import mySerial


class MyWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(MyWidget, self).__init__(*args, **kwargs)

        self.setWindowTitle("Nick's App")
        self.setGeometry=(1000,800)

        self.data=[]



        self.setupUI()


        
    def choose_device(self):
        self.device = mySerial(gStrength)
        self.connect_to_device()
        # raise NotImplementedError("Must hard set device choice")
    
    def connect_to_device(self):
        self.device.open()

        self.start_btn.setEnabled(True)


    def setupUI(self):

        self.timer = QtCore.QTimer()
        self.timer.setInterval(25) #ms
        self.timer.timeout.connect(self.update_plot)


        # Add widgets

        self.choose_device_btn = QtGui.QPushButton('Choose device')
        self.choose_device_btn.setToolTip('Pick which device to start streaming data from')
        self.choose_device_btn.clicked.connect(self.choose_device)
        self.choose_device_btn.setEnabled(True)

        self.start_btn = QtGui.QPushButton('Start')
        self.start_btn.setToolTip('Begin streaming data')
        self.start_btn.clicked.connect(self.start_btn_pushed)
        self.start_btn.setEnabled(False)

        self.zero_btn = QtGui.QPushButton('Zero')
        self.zero_btn.setToolTip('Tare (zero) the device')
        self.zero_btn.clicked.connect(self.zero_btn_pushed)
        self.zero_btn.setEnabled(False)

        self.stop_btn = QtGui.QPushButton('Stop')
        self.stop_btn.setToolTip('Stop streaming data')
        self.stop_btn.clicked.connect(self.stop_btn_pushed)
        self.stop_btn.setEnabled(False)

        self.plot = pg.PlotWidget()
        self.curve = self.plot.plot()

        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        # Give widgets their places in the layout
        layout.addWidget(self.choose_device_btn, 0, 0)
        layout.addWidget(self.start_btn, 1, 0)
        layout.addWidget(self.zero_btn, 2, 0)
        layout.addWidget(self.stop_btn, 3, 0)
        layout.addWidget(self.plot, 0, 1, 3, 3)

        self.show()

    def update_plot(self):
        self.data.extend(self.device.get_all())
        self.curve.setData(self.data)
        # curve.setPos(ptr,0) # might be useful if I want a moving window.

    def start_btn_pushed(self):
        self.start_btn.setEnabled(False)
        self.zero_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.choose_device_btn.setEnabled(False)

        self.device.start_stream()
        self.timer.start()

    def zero_btn_pushed(self):
        self.device.zero_stream()

    def stop_btn_pushed(self):
        self.stop_btn.setEnabled(False)
        self.zero_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.choose_device_btn.setEnabled(True)

        self.timer.stop()
        self.device.stop_stream()

    def cleanup(self):
        self.device.close()




def main():

    app = QtGui.QApplication([])
    myw = MyWidget()
    sys.exit(app.exec_())

    myw.cleanup()

if __name__ == "__main__":
    main()