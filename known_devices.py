import re


def gStrength_chunk_parser(raw, buf):
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

def gStrength_line_parser(line):
    try:
        return float(line)
    except ValueError:
        pass

gStrength={
    'name': 'gStrength V1',
    'baud': 115200,
    'timeout': None,
    'preferred_port_type': 'usb',
    'cmd_stop': bytes(b'w'),
    'cmd_zero': bytes(b't'),
    'cmd_start1': bytes(b'e'),
    'cmd_start2': bytes(b'q'),
    'chunk_parser': gStrength_chunk_parser,
    'line_parser': gStrength_line_parser
}

simulated_gStrength={
    'name': 'Simulated gStrength V1',
    'baud': 115200,
    'timeout': None,
    'preferred_port_type': 'usb',
    'cmd_stop': bytes(b'w'),
    'cmd_zero': bytes(b't'),
    'cmd_start1': bytes(b'e'),
    'cmd_start2': bytes(b'q'),
    'chunk_parser': gStrength_chunk_parser,
    'line_parser': gStrength_line_parser

}