#!/usr/bin/env python3

import time
from litex.tools.remote.comm_uart import CommUART


class FPGA_Connect:

    def __init__(self, comm):
        self.comm = comm

    @property
    def debug(self):
        if self.comm is None:
            return False
        if hasattr(self.comm, "debug"):
            return self.debug
        return False

    @debug.setter
    def debug(self, value):
        if self.comm is None:
            return
        if hasattr(self.comm, "debug"):
            self.comm.debug = value

    @property
    def bases(self):
        if self.comm is None:
            return None
        if hasattr(self.comm, "bases"):
            return self.comm.bases
        return None

    @property
    def regs(self):
        if self.comm is None:
            return None
        if hasattr(self.comm, "regs"):
            return self.comm.regs
        return None

    @property
    def mems(self):
        if self.comm is None:
            return None
        if hasattr(self.comm, "mems"):
            return self.comm.mems
        return None

    def open(self):
        if self.comm is None:
            return
        self.comm.open()

    def close(self):
        if self.comm is None:
            return
        self.comm.close()

    def read(self, addr, length=1, burst="incr"):
        if self.comm is None:
            return []
        return self.comm.read(addr, length=length, burst=burst)

    def write(self, addr, data):
        if self.comm is None:
            return
        data = data if isinstance(data, list) else [data]
        self.comm.write(addr, data)

# # #

debug = False
uart_port = "/dev/ttyUSB2"
uart_baudrate = 115200

comm = FPGA_Connect(CommUART(uart_port, baudrate=uart_baudrate,
                             csr_csv="csr.csv", debug=debug))
comm.open()
time.sleep(.3)

# get identifier
fpga_id = ""
for i in range(256):
    c = chr(int.from_bytes(comm.read(comm.bases.identifier_mem + 4*i, 1,
                                     "incr"), "big") & 0xff)
    fpga_id += c
    if c == "\0":
        break
print("fpga_id: " + fpga_id)

# # #

comm.close()

