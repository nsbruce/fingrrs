# Import libraries
import numpy as np
from scipy.signal import find_peaks
import csv
from itertools import zip_longest
import sys
import time
from dataclasses import dataclass

from PyQt5 import QtGui, QtCore
import pyqtgraph as pg

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

from . import known_devices as kd
from . import serial_device as sd
from . import utils
from . import modals
from . import data_structs as ds



class MyWidget(QtGui.QWidget):
    def __init__(self, *args, **kwargs):
        super(MyWidget, self).__init__(*args, **kwargs)

        self.device = None
        self.available_devices = []

        self.xdata_raw=[]
        self.ydata_raw=[]

        self.is_streaming=False

        self.setup_timers()
        self.setup_UI()

        if len(self.available_devices)==1:
            self.change_device_dropdown.setCurrentIndex(0)

    def setup_timers(self):
        self.refresh_avail_devices_timer = QtCore.QTimer()
        self.refresh_avail_devices_timer.setInterval(5000) # 5 s
        self.refresh_avail_devices_timer.timeout.connect(self.refresh_available_devices)
        self.refresh_avail_devices_timer.start() #TODO shouldn't run while the plot is running?

        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plot)

        self.stats_timer = QtCore.QTimer()
        self.stats_timer.timeout.connect(self.update_stats)

        self.scale_timer = QtCore.QTimer()
        self.scale_timer.timeout.connect(self.check_weight)

        self.data_timer = QtCore.QTimer()
        self.data_timer.timeout.connect(self.update_data)


    def setup_UI(self):
        # Window properties
        self.setWindowTitle("Fingrrs Desktop")
        self.resize(1400,800) # This works though

        # Setup group for session control buttons
        session_ctrl_group = QtGui.QGroupBox('Device controls') 
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

        # Assign layout to session_gtrl_group
        session_ctrl_group.setLayout(session_ctrl_group_layout)


        # Setup group for plot and plot control buttons
        plot_group = QtGui.QGroupBox()
        plot_group_layout = QtGui.QGridLayout()

        #! Must be before self.initialize_plot()
        yaxis_opts_radio_group = QtGui.QGroupBox('y-Axis Options')
        yaxis_opts_radio_group_layout=QtGui.QGridLayout()

        self.yaxis_opts={
            'kg': ds.plotOption(label='kg'),
            '% weight': ds.plotOption(label='% weight'),
            '% max': ds.plotOption(label='% max')
        }
        self.yaxis_opts['kg'].button.setChecked(True)
        for yaxis_opt in self.yaxis_opts.values():
            yaxis_opt.button.toggled.connect(self.set_yaxis_options)
            yaxis_opts_radio_group_layout.addWidget(yaxis_opt.button)
            if yaxis_opt.button.isChecked():
                self.current_yaxis_opt = yaxis_opt
            yaxis_opt.button.setEnabled(False)

        yaxis_opts_radio_group.setLayout(yaxis_opts_radio_group_layout)
        plot_group_layout.addWidget(yaxis_opts_radio_group, 4,0,2,2)

        self.plot = pg.PlotWidget()
        self.plot_format={
            'pen':pg.mkPen(width=3, color=(0, 0, 0) ),
            # 'axis-label-styles':{'color':(0,0,0), 'font-size':30},
            'bottom-label': 'Time (s)',
            'scale-pen':pg.mkPen(width=2, color=(255, 0, 0), style=QtCore.Qt.DashLine ),
            'max-arrow-pen':pg.mkPen(width=2,color=(255,0,0)),
            'max-arrow-brush':pg.mkBrush(color=(255,0,0)),
            'max-arrow-label-color': (255,0,0)
            }

        # self.plot.setLabel('left', self.current_yaxis_opt.label)#, **self.plot_format['axis-label-styles'])
        # self.plot.setLabel('left', self.current_yaxis_opt.label, color=(0,0,0))#, **self.plot_format['axis-label-styles'])

        self.initialize_plot()
        plot_group_layout.addWidget(self.plot,0,0,3,5)

        self.save_btn = QtGui.QPushButton('Save data')
        self.save_btn.setToolTip('Save raw data to CSV file')
        self.save_btn.clicked.connect(self.save_btn_pushed)
        self.save_btn.setEnabled(False)
        plot_group_layout.addWidget(self.save_btn, 4,2,1,3)

        self.clear_plot_btn = QtGui.QPushButton('Clear plot')
        self.clear_plot_btn.setToolTip('Erase plot (does not clear stats')
        self.clear_plot_btn.clicked.connect(self.clear_plot)
        self.clear_plot_btn.setEnabled(False)
        plot_group_layout.addWidget(self.clear_plot_btn,5,2,1,3)

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
        stats_form = QtGui.QFormLayout()
        
        self.stats = {
            'current_val': ds.Stat(name='current_val', qlabel=QtGui.QLabel('Current value (kg):')),
            'user_weight': ds.Stat(name='user_weight', qlabel=QtGui.QLabel('User weight (kg):')),
            'max_pull': ds.Stat(name='max_pull', qlabel=QtGui.QLabel('Max pull (kg):'))
        }

        for stat in self.stats.values():
            stat.display_element.setSegmentStyle(QtGui.QLCDNumber.Flat)
            stat.display_element.setMinimumHeight(40)
            stat.display_element.display(stat.value)
            stats_form.addRow(stat.qlabel, stat.display_element)

        # Assign layout to stats group
        stats_group.setLayout(stats_form)

        # Setup group for mode of use
        mode_group = QtGui.QGroupBox('Mode')
        mode_group_layout = QtGui.QGridLayout()

        self.modes = ['Max pull', 'Weigh user']
        self.mode_dropdown = QtGui.QComboBox()
        self.mode_dropdown.addItems(self.modes)
        self.mode_dropdown.setCurrentIndex(-1)
        mode_group_layout.addWidget(self.mode_dropdown)

        def set_mode(index):
            if index==0: # max pull
                self.max_pull_mode()
            elif index==1: # scale mode
                self.scale_mode()
            
        self.mode_dropdown.currentIndexChanged.connect(set_mode)
        self.mode_dropdown.setEnabled(False)

        mode_group.setLayout(mode_group_layout)

        # Setup a layout of the widgets
        main_layout = QtGui.QGridLayout()

        # Give organize main layout
        main_layout.addWidget(configuration_group,0,0)#,1,1)
        main_layout.addWidget(mode_group,1,0)#,1,1)
        main_layout.addWidget(session_ctrl_group,2,0,2,1)
        main_layout.addWidget(stats_group,4,0)#0,6,5,1)
        main_layout.addWidget(plot_group,0,1,5,5)

        #? For testing
        # test_btn=QtGui.QPushButton('Test')
        # test_btn.clicked.connect(self.update_stat_dialog)
        # main_layout.addWidget(test_btn)

        self.setLayout(main_layout)

        # Make the window appear
        self.show()

    def initialize_plot(self):
        self.plot.setLabel('left', self.current_yaxis_opt.label)#, **self.plot_format['axis-label-styles'])
        self.plot.setLabel('bottom', self.plot_format['bottom-label'])#, **self.plot_format['axis-label-styles'])
        # self.plot.setMouseEnabled(x=True, y=False)
        self.curve = self.plot.plot(pen=self.plot_format['pen'])


    def choose_device(self, i):
        initial_device = self.device
        self.device = sd.mySerial(self.available_devices[i])
        if initial_device != self.device:
            if initial_device!=None and initial_device.is_open:
                initial_device.close()

            self.stop_btn.setEnabled(False)
            self.zero_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.change_device_dropdown.setEnabled(True)
            self.mode_dropdown.setEnabled(True)
            self.mode_dropdown.setCurrentIndex(0)
            self.save_btn.setEnabled(False)

            self.stats['current_val'].value=0

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
        if self.is_streaming==False:
            self.clear_plot()

        if self.mode_dropdown.currentIndex()==0: # max pull
            if 'kg' in self.current_yaxis_opt.label:
                self.curve.setData(self.xdata_raw,self.ydata_raw)
            elif 'weight' in self.current_yaxis_opt.label:
                self.curve.setData(self.xdata_raw, [(x/self.stats['user_weight'].value)*100 for x in self.ydata_raw])
            elif 'max' in self.current_yaxis_opt.label:
                self.curve.setData(self.xdata_raw, [(x/self.stats['max_pull'].value)*100 for x in self.ydata_raw])
        elif self.mode_dropdown.currentIndex()==1: # scale mode
            self.curve.setData(self.xdata_scale, self.ydata_scale)
        # curve.setPos(ptr,0) # might be useful if I want a moving window.


    def update_data(self):
        newypoints = self.device.get_all()
        xstart=self.xdata_raw[-1]+self.device.rate if len(self.xdata_raw)>0 else 0
        newxpoints = np.linspace(xstart,xstart+(len(newypoints)-1)*self.device.rate,len(newypoints)).tolist() 

        self.ydata_raw.extend(newypoints)
        self.xdata_raw.extend(newxpoints)

        if self.mode_dropdown.currentIndex()==1: # scale mode
            scale_window=0.5 # length of rolling window average
            self.ydata_scale = utils.moving_average(self.ydata_raw, int(scale_window/self.device.rate)) # moving average with window 0.5s
            xstart = scale_window/2
            self.xdata_scale = np.linspace(xstart,xstart+(len(self.ydata_scale)-1)*self.device.rate,len(self.ydata_scale)).tolist() 


    def update_stats(self):
        self.stats['current_val'].value=self.ydata_raw[-1]


    def check_weight(self):
        start_samps = int(5/self.device.rate)
        required_samps = int(3/self.device.rate)
        scale_threshold = 1 # kg difference between max and min 
        if len(self.ydata_raw) > start_samps and max(self.ydata_scale[-required_samps:])-min(self.ydata_scale[-required_samps:]) <= scale_threshold:
            self.stop_btn_pushed()


    def max_pull_mode(self):
        self.mode_timers=[self.data_timer, self.plot_timer, self.stats_timer]

        self.yaxis_opts['kg'].button.setEnabled(True)
        if self.stats['max_pull'].value != 0:
            self.yaxis_opts['% max'].button.setEnabled(True)
        if self.stats['user_weight'].value != 0:
            self.yaxis_opts['% weight'].button.setEnabled(True)

    def scale_mode(self):
        self.ydata_scale=[]
        self.xdata_scale=[]

        for yaxis_opt in self.yaxis_opts.values():
            yaxis_opt.button.setEnabled(False)

        self.stop_btn.setEnabled(False)
        self.mode_timers=[self.data_timer, self.plot_timer, self.stats_timer, self.scale_timer]


    def set_start_mode_timers(self, interval):
        for timer in self.mode_timers:
            timer.setInterval(interval)
            timer.start()


    def stop_timers(self):
        for timer in self.mode_timers:
            timer.stop()


    def start_btn_pushed(self):
        buffer=self.device.get_all()
        del buffer

        self.clear_data()
        self.clear_plot()

        self.start_btn.setEnabled(False)
        self.zero_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.change_device_dropdown.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.mode_dropdown.setEnabled(False)

        self.device.start_stream()
        if self.mode_dropdown.currentIndex()==0: # max pull mode
            self.set_start_mode_timers(25)
        elif self.mode_dropdown.currentIndex()==1: # weigh user
            self.set_start_mode_timers(interval=100)
        
        self.is_streaming=True


    def clear_data(self):
        self.xdata_raw=[]
        self.ydata_raw=[]


    def clear_plot(self):
        self.plot.clear()
        self.initialize_plot()


    def zero_btn_pushed(self):
        if self.is_streaming:
            self.device.zero_stream()
        else:
            self.device.start_stream()
            self.device.zero_stream()
            self.device.stop_stream()

        self.device.zero_stream()

    def stop_btn_pushed(self):
        self.stop_btn.setEnabled(False)
        self.zero_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.change_device_dropdown.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.mode_dropdown.setEnabled(True)
        self.clear_plot_btn.setEnabled(True)

        self.stop_timers()
        self.device.stop_stream()
        self.stats['current_val'].value=0
        self.is_streaming=False

        if self.mode_dropdown.currentIndex()==0: # max pull was measured
            temp_max=max(self.ydata_raw)
            time_at_max = self.xdata_raw[self.ydata_raw.index(temp_max)]
            max_arrow = pg.CurveArrow(self.curve, index=self.ydata_raw.index(temp_max), pen=self.plot_format['max-arrow-pen'], brush=self.plot_format['max-arrow-brush'], angle=90)
            max_arrow_label=pg.TextItem(text=f"{time_at_max:.4f} s, {temp_max} kg", border=self.plot_format['max-arrow-pen'], color=self.plot_format['max-arrow-label-color'], anchor=(0,1))
            max_arrow_label.setPos(time_at_max,temp_max)
            self.plot.addItem(max_arrow)
            self.plot.addItem(max_arrow_label)
            self.update_stat_dialog(new_val=temp_max)
        elif self.mode_dropdown.currentIndex()==1: # weighed something
            temp_user_weight=np.average(self.ydata_scale[-int(3/self.device.rate):])
            self.plot.addLine(y=temp_user_weight, pen=self.plot_format['scale-pen'])
            self.update_stat_dialog(new_val=temp_user_weight)


    def update_stat_dialog(self, new_val):
        if self.mode_dropdown.currentIndex()==0: #Max pull
            dlg = modals.UpdateStatDialog(old_val=self.stats['max_pull'].value, new_val=new_val, stat_name='max pull stat')
            if dlg.exec_():
                self.stats['max_pull'].value = new_val
                self.yaxis_opts['% max'].button.setEnabled(True)
        elif self.mode_dropdown.currentIndex()==1: #Weight
            dlg = modals.UpdateStatDialog(old_val=self.stats['user_weight'].value, new_val=new_val, stat_name='user weight stat')
            if dlg.exec_():
                self.stats['user_weight'].value = new_val
                self.mode_dropdown.clear()
                self.modes[1]='Reweigh user'
                self.mode_dropdown.addItems(self.modes)
                self.mode_dropdown.setCurrentIndex(0)

    def save_btn_pushed(self):
        names = QtGui.QFileDialog.getSaveFileName(self, 'Save data as CSV')
        if names[0] == '':
            return
        elif names[0][-4:]=='.csv': #TODO endswidth is not working?
            fname=names[0]
        else:
            fname=names[0]+'.csv'

        header=['time','kg','user_weight','max_pull']
        data = zip_longest(self.xdata_raw,self.ydata_raw,[self.stats['user_weight'].value], [self.stats['max_pull'].value])

        with open(fname,'w') as outfile:
            csv.writer(outfile).writerow(header)
            csv.writer(outfile).writerows(data)


    def cleanup(self):
        self.device.close()
        self.refresh_avail_devices_timer.stop()


    def set_yaxis_options(self):
        for yaxis_opt in self.yaxis_opts.values():
            if yaxis_opt.button.isChecked():
                self.current_yaxis_opt=yaxis_opt
        self.plot.setLabel('left', self.current_yaxis_opt.label)#, **self.plot_format['axis-label-styles'])


        if self.is_streaming==False:
            self.update_plot()



def main():

    app = QtGui.QApplication([])
    myw = MyWidget()
    sys.exit(app.exec_())

    myw.cleanup()




if __name__ == "__main__":
    main()