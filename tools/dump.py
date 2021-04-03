#!/usr/bin/python3

import sys
import struct

if len(sys.argv) < 2:
    sys.exit(1)
filename = sys.argv[1]
with open(filename, 'rb') as f:
    df = f.read()
    format = '>{:d}Q'.format(len(df) // 8)
    d = struct.unpack(format, df)
    for i in d:
        print('0x{:016x}'.format(i))

