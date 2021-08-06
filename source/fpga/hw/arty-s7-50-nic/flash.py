#!/usr/bin/env python3
import os
from migen import *
#from litex_boards.platforms import arty_s7
from litex.build.openocd import OpenOCD


base_path = os.path.dirname(os.path.realpath(__file__))
prog_path = os.path.join(base_path, 'prog')
bitstream = os.path.join(base_path, 'build', 'gateware', 'top.bit')

print("*** LOADING BITSTREAM (%s) INTO FPGA" % bitstream)

# Standard programmer for this platform is OpenOCD with a predefined
# configuration. To override this configuration witha custom one comment
# out the following 3 lines and create the OpenOCD programmer yourself
# specifying your own, custom configuration

#platform = arty_s7.Platform()
#prog = platform.create_programmer()
#prog.load_bitstream(bitstream)

bscan_spi = 'bscan_spi_xc7s50.bit'  # xc7s50
#bscan_spi = 'bscan_spi_xc7s25.bit'  # xc7s20
prog = OpenOCD(os.path.join(prog_path, 'openocd_xc7_ft2232.cfg'), bscan_spi)
prog.flash(0, bitstream)

print("*** LOAD DONE")

