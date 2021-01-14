import re


def __gStrength_chunk_parser__(raw, buf):
    valslist=[]

    for val in raw.split(b'\r\n'):


        if val == b'':
            continue
        
        # If there is something in the buffer and it matches the regex when combined with the latest element
        if buf != None and re.search(b'^-?[0-9]*\.[0-9]{3}$', buf+val):
            # print(f'Joining {buf} and {val}!')
            val=buf+val
            buf=None
        # If there is something in the buffer and it does not match the regex when combined with the latest element
        if buf != None and not re.search(b'^-?[0-9]*\.[0-9]{3}$', buf+val):
            # print(f'Tossing out buffer {buf} since it does not fit with {val}')
            buf=None
        # If there is nothing in the buffer and the latest element does not match the regex on it's own
        if buf==None and not re.search(b'^-?[0-9]*\.[0-9]{3}$', val):
            buf=val
            # print(f"Added {val} to buffer")
            continue

        valslist.append(float(val))
    return valslist, buf

def __gStrength_line_parser__(line):
    try:
        return float(line)
    except ValueError:
        pass

gStrength={
    'name': 'gStrength V1',
    'baud': 115200,
    'timeout': None,
    'preferred_port_type': 'USB',
    # 'preferred_port_type': 'Bluetooth',
    'cmd_stop': bytes(b'w'),
    'cmd_zero': bytes(b't'),
    'rate_start1': 0.0125, # one sample every 12.5 ms
    'cmd_start1': bytes(b'e'),
    'rate_start2': 0.025, # one sample every 25 ms
    'cmd_start2': bytes(b'q'),
    'chunk_parser': __gStrength_chunk_parser__,
    'line_parser': __gStrength_line_parser__,
    'manufacturer':'Adafruit'
}

all_known_devices=[gStrength]