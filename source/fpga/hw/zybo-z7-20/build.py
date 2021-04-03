#!/usr/bin/env python3
import sys
from migen import *
#from litex_boards.platforms import zybo_z7
import zybo_z7_20 as zybo_z7

# add search paths when run from inside folder
sys.path.insert(0, '../../../../source')
sys.path.insert(0, '../../../../tools/ubpf')

from top import *


platform = zybo_z7.Platform()
top = Top(platform)

# Convert and build
builder = Builder(top, csr_csv="debug/csr.csv",
    gateware_dir="build/gateware",
    software_dir="build/software")
builder.build(build_name="top")

# Only convert to verilog
#with open('ebpf.v', 'w') as fd:
#    fd.write(str(verilog.convert(top)))

