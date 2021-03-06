from . import known_devices as kd
import serial
import serial.tools.list_ports

def print_available_devices():
    print("Available devices:")
    for device, desc, hwid in sorted(serial.tools.list_ports.comports()):
        #TODO check if this is the same for windows
        if desc=='n/a' and hwid=='n/a':
            continue
    else:
        print("{}: {} [{}]".format(device, desc, hwid))

def get_available_devices():
    return [x for x in serial.tools.list_ports.comports() if x.hwid!='n/a' and x.description!='n/a']            

class mySerial:
    def __init__(self, mydev):
        self.port=self.get_port(mydev['preferred_port_type'])
        self.baudrate=mydev['baud']
        self.timeout=mydev['timeout']
        self.cmd_start=mydev['cmd_start1'] #TODO what if there are two (there are for gStrength)
        self.rate=mydev['rate_start1'] #TODO again what if there are two (there are for gStrength)
        self.cmd_zero=mydev['cmd_zero']
        self.cmd_stop=mydev['cmd_stop']
        self.chunk_parser=mydev['chunk_parser']
        self.line_parser=mydev['line_parser']
        self.ser=None
        self.buffer=None
    
    def get_port(self, preferred_port_type_str):
        # ports=[port for ports, desc, hwid in sorted(serial.tools.list_ports.comports())]
        # for port in ports:
        #     if preferred_port_type_str in device:
        #         return port
        #TODO handle if port isn't in there
        for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
            if preferred_port_type_str in hwid:
                return port
    
    def __setup_connection__(self):
        self.ser=serial.Serial()
        self.ser.port=self.port
        self.ser.baudrate=self.baudrate
        self.ser.timeout=self.timeout
    
    def open(self):
        self.__setup_connection__()
        try:
            self.ser.open()
        except serial.serialutil.SerialException:
            raise ConnectionError(f'Could not connect to {self.ser}')
    
    def close(self):
        self.ser.close()
    
    def start_stream(self):
        self.ser.write(self.cmd_start)
    
    def zero_stream(self):
        self.ser.write(self.cmd_zero)
    
    def stop_stream(self):
        self.ser.write(self.cmd_stop)
        self.flush()
    
    def get_all(self):
        latest=self.ser.read(self.ser.inWaiting())
        processed, self.buffer = self.chunk_parser(latest,self.buffer)
        return processed

    def get_line(self):
        line = self.ser.readline()
        return self.line_parser(line)

    def flush(self):
        self.ser.flushInput()
        self.ser.flushOutput()




