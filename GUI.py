# Import libraries
import numpy as np
import pandas as pd
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

        self.device = None
        self.available_devices = []

        self.xdata=[]
        self.ydata=[]

        self.setupUI()


    def setupUI(self):
        # Setup timers
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.setInterval(25) # 25 ms - this is approximately 30 Hz and we can't see anything much faster I don't think
        self.plot_timer.timeout.connect(self.update_plot)

        self.refresh_avail_devices_timer = QtCore.QTimer()
        self.refresh_avail_devices_timer.setInterval(5000) # 5 s
        self.refresh_avail_devices_timer.timeout.connect(self.refresh_available_devices)
        self.refresh_avail_devices_timer.start() #TODO shouldn't run while the plot is running?

        self.stats_timer = QtCore.QTimer()
        self.stats_timer.setInterval(25) # ms
        self.stats_timer.timeout.connect(self.update_stats)

        # Window properties
        self.setWindowTitle("Flex tester")
        # self.resize(1000,800) # This works though

        # Setup group for session control buttons
        session_ctrl_group = QtGui.QGroupBox() # Can put a string in here for a title
        session_ctrl_group_layout = QtGui.QGridLayout()

        # Add session control elements
        self.start_btn = QtGui.QPushButton('Start')
        self.start_btn.setToolTip('Begin streaming data')
        self.start_btn.clicked.connect(self.start_btn_pushed)
        self.start_btn.setEnabled(False)
        session_ctrl_group_layout.addWidget(self.start_btn)

        self.zero_btn = QtGui.QPushButton('Zero')
        self.zero_btn.setToolTip('Tare (zero) the device')
        self.zero_btn.clicked.connect(self.zero_btn_pushed)
        self.zero_btn.setEnabled(False)
        session_ctrl_group_layout.addWidget(self.zero_btn)

        self.stop_btn = QtGui.QPushButton('Stop')
        self.stop_btn.setToolTip('Stop streaming data')
        self.stop_btn.clicked.connect(self.stop_btn_pushed)
        self.stop_btn.setEnabled(False)
        session_ctrl_group_layout.addWidget(self.stop_btn)

        self.reset_btn = QtGui.QPushButton('Reset')
        self.reset_btn.setToolTip('Erase data and prepare to start again')
        self.reset_btn.clicked.connect(self.reset_btn_pushed)
        self.reset_btn.setEnabled(False)
        session_ctrl_group_layout.addWidget(self.reset_btn)

        # Assign layout to session_gtrl_group
        session_ctrl_group.setLayout(session_ctrl_group_layout)


        # Setup group for plot and plot control buttons
        plot_group = QtGui.QGroupBox()
        plot_group_layout = QtGui.QGridLayout()

        self.plot = pg.PlotWidget()
        self.plot_format={
            'pen':pg.mkPen(width=3, color=(0, 0, 0) ),
            'axis-label-styles':{'color':(0,0,0), 'font-size':30},
            'left-label': 'Weight (kg)',
            'bottom-label': 'Time (s)'
            }
        self.plot.setLabel('left', self.plot_format['left-label'], **self.plot_format['axis-label-styles'])
        self.plot.setLabel('bottom', self.plot_format['bottom-label'], **self.plot_format['axis-label-styles'])
        # self.plot.setMouseEnabled(x=True, y=False)
        self.curve = self.plot.plot(pen=self.plot_format['pen'])
        plot_group_layout.addWidget(self.plot)

        self.save_btn = QtGui.QPushButton('Save data')
        self.save_btn.setToolTip('Save raw data to CSV file')
        self.save_btn.clicked.connect(self.save_btn_pushed)
        self.save_btn.setEnabled(False)
        plot_group_layout.addWidget(self.save_btn)

        self.set_yaxis_btn = QtGui.QPushButton('Set y-axis options')
        self.set_yaxis_btn.setToolTip('Options for how the y-axis is plotted')
        self.set_yaxis_btn.clicked.connect(self.set_yaxis_options)
        self.set_yaxis_btn.setEnabled(True)
        plot_group_layout.addWidget(self.set_yaxis_btn)

        # Assign layout to plot_group
        plot_group.setLayout(plot_group_layout)

        # Setup group for configuration items
        configuration_group = QtGui.QGroupBox('Device configuration')
        configuration_group_layout = QtGui.QGridLayout()


        self.change_device_dropdown = QtGui.QComboBox()
        self.refresh_available_devices()
        self.change_device_dropdown.setCurrentIndex(-1)
        self.change_device_dropdown.currentIndexChanged.connect(self.choose_device)
        self.change_device_dropdown.setEnabled(True)
        configuration_group_layout.addWidget(self.change_device_dropdown)

        # Assign layout to configuration group
        configuration_group.setLayout(configuration_group_layout)

        # Setup group for stats pane
        stats_group = QtGui.QGroupBox('Statistics')
        # stats_group_layout = QtGui.QGridLayout()
        stats_form = QtGui.QFormLayout()

        self.stats_max_value_label = QtGui.QLabel('Max value (kg): ')

        self.stats_max_value_disp = QtGui.QLCDNumber()
        self.stats_max_value_disp.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.stats_max_value_disp.setMinimumHeight(40)

        stats_form.addRow(self.stats_max_value_label, self.stats_max_value_disp)

        # Assign layout to stats group
        stats_group.setLayout(stats_form)


        # Setup a layout of the widgets
        main_layout = QtGui.QGridLayout()

        # Give organize main layout
        main_layout.addWidget(configuration_group,0,0,1,1)
        main_layout.addWidget(session_ctrl_group,1,0,4,1)
        main_layout.addWidget(plot_group,0,1,5,5)
        main_layout.addWidget(stats_group,0,6,5,5)

        self.setLayout(main_layout)

        # Make the window appear
        self.show()


    def choose_device(self, i):
        initial_device = self.device
        self.device = sd.mySerial(self.available_devices[i])
        if initial_device != self.device:
            if initial_device!=None and initial_device.is_open:
                initial_device.close()

            self.reset_btn_pushed()
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
        newypoints = self.device.get_all()
        xstart=self.xdata[-1]+self.device.rate if len(self.xdata)>0 else 0
        newxpoints = np.linspace(xstart,xstart+(len(newypoints)-1)*self.device.rate,len(newypoints)).tolist() 

        self.ydata.extend(newypoints)
        self.xdata.extend(newxpoints)
        self.curve.setData(self.xdata,self.ydata)
        # curve.setPos(ptr,0) # might be useful if I want a moving window.
    
    def update_stats(self):
        self.stats_max_value_disp.display(max(self.ydata))

    def start_btn_pushed(self):
        self.start_btn.setEnabled(False)
        self.zero_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.change_device_dropdown.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

        self.device.start_stream()
        self.plot_timer.start()
        self.stats_timer.start()
    
    def reset_btn_pushed(self):
        self.xdata=[]
        self.ydata=[]
        self.curve.setData(self.ydata, self.xdata)

        self.zero_btn.setEnabled(False)
        self.start_btn.setText('Start')
        self.start_btn.setEnabled(True)
        self.change_device_dropdown.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def zero_btn_pushed(self):
        self.device.zero_stream()

    def stop_btn_pushed(self):
        self.stop_btn.setEnabled(False)
        self.zero_btn.setEnabled(False)
        self.start_btn.setText('Continue')
        self.start_btn.setEnabled(True)
        self.change_device_dropdown.setEnabled(True)
        self.reset_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        self.plot_timer.stop()
        self.stats_timer.stop()
        self.device.stop_stream()

    def save_btn_pushed(self):
        names = QtGui.QFileDialog.getSaveFileName(self, 'Save data as CSV')
        if names[0] == '':
            return
        elif names[0][-4:]=='.csv': #TODO endswidth is not working?
            fname=names[0]
        else:
            fname=names[0]+'.csv'
        df = pd.DataFrame(data={"t": self.xdata, "kg": self.ydata})
        df.to_csv(fname, sep=',',index=False)

    def cleanup(self):
        self.device.close()
        self.refresh_avail_devices_timer.stop()

    def set_yaxis_options(self):
        yaxis_modal = QtGui.QDialog(self)

        yaxis_modal.exec_()

def main():

    app = QtGui.QApplication([])
    myw = MyWidget()
    sys.exit(app.exec_())

    myw.cleanup()




if __name__ == "__main__":
    main()