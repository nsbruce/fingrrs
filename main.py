import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np
import re


# class mySerial():
#     def __init__(self):
#         self.ser=serial.Serial()

#         self.ser.timeout=10 # probably should be way faster
    
#     def set_baudrate(self, baudrate):
#         self.ser.baudrate = baudrate
    
#     def set_timeout(self, timeout):
#         self.ser.timeout=timeout

#     def set_port(self, port):
#         self.ser.port=port

    
# def list_devices(self):
def list_devices():
    print("Available devices:")
    for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
        print("{}: {} [{}]".format(port, desc, hwid))


def main():

    ser=serial.Serial()
    ser.baudrate=115200
    # ser.timeout=None
    ser.port='No device found'#/dev/cu.usbmodem1442301'
    try:
        ser.open()
    except serial.serialutil.SerialException:
        list_devices()
    # ser.write(bytes(b'q')) # 26 ms max effort data stream
    ser.write(bytes(b'e')) # 12 ms raw data stream




    # ser.write(bytes(b't')) # tare (zero) but must be running (q/e) to do this

    # Create figure for plotting
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xs = [] #store trials here (n)
    ys = [] #store relative frequency here

    # This function is called periodically from FuncAnimation
    def animate(i, xs, ys, buf):

        # Aquire and parse data from serial port
        latest=ser.read(ser.inWaiting())
        valslist=[]

        for val in latest.split(b'\r\n'):

            if val == b'':
                continue

            if len(buf)>0 and re.search(b'^-?[0-9]*\.[0-9]{3}$', buf[0]+val):
                print(f'Joining {buf[0]} and {val}!')
                val=buf[0]+val
                buf.pop()
            elif len(buf)>0 and re.search(b'^-?[0-9]*\.[0-9]{3}$', buf[0]+val):
                print(f'Tossing out buffer {buf[0]} since it does not fit with {val}')
                buf.pop()
            elif len(buf)==0 and not re.search(b'^-?[0-9]*\.[0-9]{3}$', val):
                buf.append(val)
                print(f"Added {val} to buffer")
                continue

            valslist.append(float(val))


        
        # Add x and y to lists
        # xs.append(i)
        # xval+=xstep
        ys.extend(valslist)

        # Limit x and y lists to 20 items
        #xs = xs[-20:]
        #ys = ys[-20:]

        # Draw x and y lists
        ax.clear()
        # ax.plot(xs, ys, label="kg")
        ax.plot(ys)

        # Format plot
        # plt.xticks(rotation=45, ha='right')
        # plt.subplots_adjust(bottom=0.30)
        plt.title('gStrength output')
        plt.ylabel('Mass')
        # plt.legend()
        plt.axis([0, None, None, None]) #Use for arbitrary number of trials



    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Set up plot to call animate() function periodically
    buf=[]
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys, buf), interval=12)
    plt.show()

    ser.write(bytes(b'w')) # stop

    ser.close()


if __name__ == "__main__":
    main()