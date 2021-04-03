#!/usr/bin/env python3
import os
from migen import *
import zybo_z7_20 as zybo_z7

base_path = os.path.dirname(os.path.realpath(__file__))
prog_path = os.path.join(base_path, 'prog')
bitstream = os.path.join(base_path, 'build', 'top.bit')

print("*** FLASHING BITSTREAM (%s) INTO FPGA" % bitstream)

platform = zybo_z7.Platform()
prog = platform.create_programmer()
prog.flash(0, bitstream, device=1)

print("*** LOAD DONE")

