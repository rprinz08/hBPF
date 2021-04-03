#!/usr/bin/env python3
from migen import *
#from migen.build.openocd import OpenOCD
#from litex_boards.platforms import zybo_z7
import zybo_z7_20 as zybo_z7

import os
from pprint import pprint

base_path = os.path.dirname(os.path.realpath(__file__))
prog_path = os.path.join(base_path, 'prog')

bitstream = os.path.join(base_path, 'build', 'gateware', 'top.bit')
print("*** LOADING BITSTREAM (%s) INTO FPGA" % bitstream)

platform = zybo_z7.Platform()
prog = platform.create_programmer()
prog.load_bitstream(bitstream,
                    #target="localhost:3121/xilinx_tcf/Digilent/210351A6B239A",
                    device=1)

#bscan_spi = 'bscan_spi_xc7s50.bit'  # xc7s50
##bscan_spi = 'bscan_spi_xc7s25.bit'  # xc7s20
#prog = OpenOCD(os.path.join(prog_path, 'zybo-z7-20.cfg'))
##prog = OpenOCD(os.path.join(prog_path, 'openocd_xc7_ft2232.cfg'), bscan_spi)
##prog = OpenOCD(os.path.join(prog_path, 'zynq_7000.cfg'))
#prog.set_flash_proxy_dir(prog_path)
#prog.load_bitstream(bitstream)

print("*** LOAD DONE")

