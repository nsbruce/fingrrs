# Import libraries
import numpy as np
import sys
import time

from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import known_devices as kd
import serial_device as sd



class MyWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(MyWidget, self).__init__(*args, **kwargs)

        self.setWindowTitle("Nick's App")
        # self.setGeometry=(1000,800)

        self.device = None
        self.available_devices = []

        self.xdata=[]
        self.ydata=[]


        self.setupUI()




    def setupUI(self):

        self.plot_timer = QtCore.QTimer()
        self.plot_timer.setInterval(25) #ms - this is approximately 30 Hz and we can't see anything much faster I don't think
        self.plot_timer.timeout.connect(self.update_plot)

        self.refresh_avail_devices_timer = QtCore.QTimer()
        self.refresh_avail_devices_timer.setInterval(5000) # 5 s
        self.refresh_avail_devices_timer.timeout.connect(self.refresh_available_devices)
        self.refresh_avail_devices_timer.start() #TODO shouldn't run while the plot is running?

        # Add widgets

        self.start_btn = QtGui.QPushButton('Start')
        self.start_btn.setToolTip('Begin streaming data')
        self.start_btn.clicked.connect(self.start_btn_pushed)
        self.start_btn.setVisible(False)

        self.zero_btn = QtGui.QPushButton('Zero')
        self.zero_btn.setToolTip('Tare (zero) the device')
        self.zero_btn.clicked.connect(self.zero_btn_pushed)
        self.zero_btn.setVisible(False)

        self.stop_btn = QtGui.QPushButton('Stop')
        self.stop_btn.setToolTip('Stop streaming data')
        self.stop_btn.clicked.connect(self.stop_btn_pushed)
        self.stop_btn.setVisible(False)

        self.reset_btn = QtGui.QPushButton('Reset')
        self.reset_btn.setToolTip('Erase data and prepare to start again')
        self.reset_btn.clicked.connect(self.reset_btn_pushed)
        self.reset_btn.setVisible(False)

        self.plot = pg.PlotWidget()
        pen = pg.mkPen(width=3, color=(0, 0, 0) )
        styles = {'color':(0,0,0), 'font-size':30}
        self.plot.setLabel('left', 'Weight (kg)', **styles)
        self.plot.setLabel('bottom', 'Time (s)', **styles)
        # self.plot.setMouseEnabled(x=True, y=False)
        self.curve = self.plot.plot(pen=pen)


        self.change_device_label = QtGui.QLabel('Choose device')
        self.change_device_dropdown = QtGui.QComboBox()
        self.refresh_available_devices()
        # self.change_device_dropdown.setPlaceholderText('placeholder') # doesn't work anyway
        self.change_device_dropdown.setCurrentIndex(-1)
        self.change_device_dropdown.currentIndexChanged.connect(self.choose_device)

        self.change_device_dropdown.setVisible(True)
        self.change_device_label.setVisible(True)


        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        # Give widgets their places in the layout
        layout.addWidget(self.change_device_label)
        layout.addWidget(self.change_device_dropdown)#, 0, 0)
        layout.addWidget(self.start_btn)#, 1, 0)
        layout.addWidget(self.zero_btn)#, 2, 0)
        layout.addWidget(self.stop_btn)#, 3, 0)
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.plot)#, 0, 1, 3, 3)

        self.show()

    def choose_device(self, i):
        initial_device = self.device
        self.device = sd.mySerial(self.available_devices[i])
        if initial_device != self.device:
            if initial_device!=None and initial_device.is_open:
                initial_device.close()

            self.reset_btn_pushed()
            self.change_device_label.setText('Change device')
            self.device.open()

    
    def refresh_available_devices(self):   
        newly_availably_devices=[]
        for avail_dev in sd.get_available_devices():
            for known_dev in kd.all_known_devices:
                if known_dev['preferred_port_type'] in avail_dev.device and known_dev['manufacturer']==avail_dev.manufacturer:
                    newly_availably_devices.append(known_dev)
                #TODO if not a known device, offer ability to set baud etc. Will need generic known dev item
        if self.available_devices != newly_availably_devices:
            self.available_devices=newly_availably_devices
            self.change_device_dropdown.clear()
            self.change_device_dropdown.addItems([dev['name'] for dev in self.available_devices])

    def update_plot(self):
        newxpoints = self.device.get_all()
        ystart=self.ydata[-1] if len(self.ydata)>0 else 0
        #TODO the timing may be off.
        newypoints = np.linspace(ystart,ystart+len(newxpoints)*self.device.rate,len(newxpoints)).tolist() 
        # newypoints=[ystart + x*(ystart+len(newxpoints)*self.device.rate-ystart)/(len(newxpoints)-1) for x in range(len(newxpoints))]

        self.ydata.extend(newypoints)
        self.xdata.extend(newxpoints)
        self.curve.setData(self.ydata,self.xdata)
        # curve.setPos(ptr,0) # might be useful if I want a moving window.

    def start_btn_pushed(self):
        self.start_btn.setVisible(False)
        self.zero_btn.setVisible(True)
        self.stop_btn.setVisible(True)
        self.change_device_label.setVisible(False)
        self.change_device_dropdown.setVisible(False)
        self.reset_btn.setVisible(False)

        self.device.start_stream()
        self.plot_timer.start()
    
    def reset_btn_pushed(self):
        self.xdata=[]
        self.ydata=[]
        self.curve.setData(self.ydata, self.xdata)

        self.zero_btn.setVisible(False)
        self.start_btn.setText('Start')
        self.start_btn.setVisible(True)
        self.change_device_label.setVisible(True)
        self.change_device_dropdown.setVisible(True)
        self.stop_btn.setVisible(False)
        self.reset_btn.setVisible(False)

    def zero_btn_pushed(self):
        self.device.zero_stream()

    def stop_btn_pushed(self):
        self.stop_btn.setVisible(False)
        self.zero_btn.setVisible(False)
        self.start_btn.setText('Continue')
        self.start_btn.setVisible(True)
        self.change_device_label.setVisible(True)
        self.change_device_dropdown.setVisible(True)
        self.reset_btn.setVisible(True)

        self.plot_timer.stop()
        self.device.stop_stream()

    def cleanup(self):
        self.device.close()
        self.refresh_avail_devices_timer.stop()




def main():

    app = QtGui.QApplication([])
    myw = MyWidget()
    sys.exit(app.exec_())

    myw.cleanup()

if __name__ == "__main__":
    main()