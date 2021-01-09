from serial_device import mySerial
from known_devices import gStrength
import time

serial_gs=mySerial(gStrength)

serial_gs.open()
serial_gs.start_stream()

try:
    while True:
        print(serial_gs.get_all())
        time.sleep(0.012)

        # print(serial_gs.get_line())
except KeyboardInterrupt:
    print('Done')
    serial_gs.stop_stream()

    serial_gs.close()

