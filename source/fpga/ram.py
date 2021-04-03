#!/usr/bin/env python3

import sys
# add search paths when run from inside folder
# (used when running test directly)
sys.path.insert(0, '..')

import os
from migen import *
from litex.soc.interconnect.csr import AutoCSR, _make_gatherer, memprefix
from tools.common import *


class RAM(Module):

    def __init__(self, max_words=None,
                init=None, endianness="big", write_capable=False,
                csr_access=False, debug=False):

        self.init = None
        self.words = None

        # Depending on r/w mode and if additional CSR access to RAM is enabled,
        # different types of r/w memory ports and access strategies are used.
        # E.g. Xilinx, according to UG901 for Vivado 2019.1 Pages 116 - 150
        # (https://www.xilinx.com/support/documentation/sw_manuals/xilinx2019_1/ug901-vivado-synthesis.pdf)
        # only supports some RAM access scenarios (Templates). In case this RAM
        # is read-only (write_capable=False) and read-write CSR access is
        # allowed (csr_access=True) multiple read ports and one write ports are
        # supported. This no longer works when RAM is read-write in which case
        # only two read-write ports are supported. The typical Vivado error
        # messages in this case are:
        # [Synth 8-2914] Unsupported RAM template ... and
        # ERROR: [Synth 8-5743] Unable to infer RAMs due to unsupported pattern.
        # Multiple read AND multiple write ports only work in simulator and are
        # not supported in this implementation.
        # Multiple read ports give best performance because all supported data
        # widths (1, 2, 4 and 8 Bytes) are read in 2 cycles. Fallback is to read
        # more then 1 byte in a loop requiring more cycles.
        # Writes are always done in loop form.
        self.write_capable = write_capable
        self.csr_access = csr_access

        if isinstance(max_words, int):
            self.words = max_words

        self.stb = Signal()
        self.ack = Signal()

        self.dat_r = Signal(8)
        self.dat_r2 = Signal(8*2)
        self.dat_r4 = Signal(8*4)
        self.dat_r8 = Signal(8*8)

        # Keep write signals even if module is not write capable
        # so that interface does not change
        #if write_capable:
        self.we = Signal()
        self.ww = Signal(4)
        self.dat_w = Signal(8*8)

        # # #

        wcnt = Signal(4)
        wait = Signal(2)

        if debug:
            print("-"*50)
            print("RAM")

        init_words = None

        if isinstance(init, Memory):
            self.specials.mem = init
            init_words = mem.depth
        else:
            # Read binary data into memory if specified
            if isinstance(init, str):
                init_file = os.path.abspath(os.path.dirname(__file__))
                init_file = os.path.join(init_file, init)
                self.init = get_data(init_file, data_width_bits=8,
                    endianness=endianness)
                init_words = len(self.init)
            elif isinstance(init, list):
                self.init = init
                init_words = len(self.init)

            if debug:
                print("max words:               {}".format(max_words))
                print("init words:              {}".format(init_words))

            if self.words is None:
                self.words = init_words
                if debug:
                    print("instance words:          {}".format(self.words))
            else:
                if debug:
                    print("instance words:          {}".format(self.words))
                if self.init is not None:
                    assert init_words <= self.words, \
                        "Init contents ({} words) does not fit into specified " \
                        "maximum ({} words)".format(init_words, self.words)

            assert self.words is not None, \
                "Either number of words or data must be specified"

            self.specials.mem = Memory(8, self.words, init=self.init)

        self.specials.port = self.mem.get_port(has_re=False,
            write_capable=write_capable)
        self.adr = Signal(min=0, max=self.words)
        addr_t = Signal(min=0, max=self.words)


        # In case of read-only RAM or read-write RAM without
        # additional CSR access, create multiple read ports
        # for different word widths which read simultaneous to main
        # port.
        if not write_capable or not csr_access:
            # Dynamically create additional read-only memory ports.
            cadd = getattr(self.comb, '__iadd__')
            for i in range(2,9):
                port_name = 'port{}'.format(i)
                p = self.mem.get_port(has_re=False, write_capable=False)
                setattr(self.specials, port_name, p)
                cadd(p.adr.eq(self.port.adr + (i-1)))

            self.comb += [
                If(self.ack,
                    self.dat_r.eq(self.port.dat_r),

                    self.dat_r2.eq(Cat(self.port.dat_r, self.port2.dat_r)),

                    self.dat_r4.eq(Cat(self.port.dat_r, self.port2.dat_r,
                                    self.port3.dat_r, self.port4.dat_r)),

                    self.dat_r8.eq(Cat(self.port.dat_r, self.port2.dat_r,
                                    self.port3.dat_r, self.port4.dat_r,
                                    self.port5.dat_r, self.port6.dat_r,
                                    self.port7.dat_r, self.port8.dat_r)),
                )
            ]


        if not write_capable:
            self.sync += [
                If(self.stb,
                    self.port.adr.eq(self.adr),
                    If(~self.ack,
                        If(wait,
                            wait.eq(wait - 1)
                        ).Else(
                            self.ack.eq(1)
                        )
                    )
                ).Else(
                    self.ack.eq(0),
                    wait.eq(1),
                )
            ]
        else:
            if not csr_access:
                self.sync += [
                    If(self.stb,
                        If(self.we,
                            If(wcnt == 0,
                                wcnt.eq(1),
                                addr_t.eq(self.adr),
                            ).Else(
                                self.port.adr.eq(addr_t),
                                self.port.we.eq(1),

                                Case(wcnt, {
                                    1: [ self.port.dat_w.eq(self.dat_w[0:8]) ],
                                    2: [ self.port.dat_w.eq(self.dat_w[8:16]) ],
                                    3: [ self.port.dat_w.eq(self.dat_w[16:24]) ],
                                    4: [ self.port.dat_w.eq(self.dat_w[24:32]) ],
                                    5: [ self.port.dat_w.eq(self.dat_w[32:40]) ],
                                    6: [ self.port.dat_w.eq(self.dat_w[40:48]) ],
                                    7: [ self.port.dat_w.eq(self.dat_w[48:56]) ],
                                    8: [ self.port.dat_w.eq(self.dat_w[56:64]) ],
                                    "default": [
                                        #wcnt.eq(0),
                                        #self.ack.eq(1)
                                    ]
                                }),
                                If(self.ww != wcnt,
                                    addr_t.eq(addr_t + 1),
                                    wcnt.eq(wcnt + 1),
                                ).Else(
                                    self.we.eq(0),
                                )
                            )
                        ).Else(
                            self.port.we.eq(0),
                            self.port.adr.eq(self.adr),
                            If(~self.ack,
                                If(wait,
                                    wait.eq(wait - 1)
                                ).Else(
                                    self.ack.eq(1)
                                )
                            )
                        )
                    ).Else(
                        self.ack.eq(0),
                        wait.eq(1),
                        wcnt.eq(0)
                    )
                ]
            else:
                self.sync += [
                    If(self.stb,
                        If(self.we,
                            If(wcnt == 0,
                                wcnt.eq(1),
                                addr_t.eq(self.adr),
                            ).Else(
                                self.port.adr.eq(addr_t),
                                self.port.we.eq(1),

                                Case(wcnt, {
                                    1: [ self.port.dat_w.eq(self.dat_w[0:8]) ],
                                    2: [ self.port.dat_w.eq(self.dat_w[8:16]) ],
                                    3: [ self.port.dat_w.eq(self.dat_w[16:24]) ],
                                    4: [ self.port.dat_w.eq(self.dat_w[24:32]) ],
                                    5: [ self.port.dat_w.eq(self.dat_w[32:40]) ],
                                    6: [ self.port.dat_w.eq(self.dat_w[40:48]) ],
                                    7: [ self.port.dat_w.eq(self.dat_w[48:56]) ],
                                    8: [ self.port.dat_w.eq(self.dat_w[56:64]) ],
                                    "default": [
                                        #wcnt.eq(0),
                                        #self.ack.eq(1)
                                    ]
                                }),
                                If(self.ww != wcnt,
                                    addr_t.eq(addr_t + 1),
                                    wcnt.eq(wcnt + 1),
                                ).Else(
                                    self.we.eq(0),
                                    wcnt.eq(0)
                                )
                            )
                        ).Else(
                            self.port.we.eq(0),
                            self.port.adr.eq(self.adr),
                            If(~self.ack,
                                If(wcnt == 0,
                                    wcnt.eq(1),
                                    wait.eq(1)
                                ).Else(
                                    If(wait,
                                        wait.eq(0),
                                        self.port.adr.eq(self.port.adr + 1),
                                    ).Else(
                                        Case(wcnt, {
                                            1: [
                                                self.dat_r.eq(self.port.dat_r),
                                                self.dat_r2.eq(self.port.dat_r),
                                                self.dat_r4.eq(self.port.dat_r),
                                                self.dat_r8.eq(self.port.dat_r),
                                            ],
                                            2: [
                                                self.dat_r2[8:16].eq(self.port.dat_r),
                                                self.dat_r4[8:16].eq(self.port.dat_r),
                                                self.dat_r8[8:16].eq(self.port.dat_r),
                                            ],
                                            3: [
                                                self.dat_r4[16:24].eq(self.port.dat_r),
                                                self.dat_r8[16:24].eq(self.port.dat_r),
                                            ],
                                            4: [
                                                self.dat_r4[24:32].eq(self.port.dat_r),
                                                self.dat_r8[24:32].eq(self.port.dat_r),
                                            ],
                                            5: [
                                                self.dat_r8[32:40].eq(self.port.dat_r),
                                            ],
                                            6: [
                                                self.dat_r8[40:48].eq(self.port.dat_r),
                                            ],
                                            7: [
                                                self.dat_r8[48:56].eq(self.port.dat_r),
                                            ],
                                            8: [
                                                self.dat_r8[56:64].eq(self.port.dat_r),
                                            ],
                                            "default": [
                                                #wcnt.eq(0),
                                                #self.ack.eq(1)
                                            ]
                                        }),
                                        If(wcnt != 8,
                                            self.port.adr.eq(self.port.adr + 1),
                                            wcnt.eq(wcnt + 1),
                                        ).Else(
                                            self.ack.eq(1)
                                        )
                                    )
                                )
                            )
                        )
                    ).Else(
                        self.ack.eq(0),
                        wait.eq(1),
                        wcnt.eq(0)
                    )
                ]


    def get_memories(self):
        print("### RAM CSR access {} ###".format("enabled" if self.csr_access else "disabled"))
        if self.csr_access:
            return [self.mem]
        else:
            return []


##################
# RAM testbench: #
##################
# Keep track of test pass / fail rates.
p = 0
f = 0

# Perform an individual RAM write unit test.
def ram_write_ut(mem, address, data, data_width=1):
    global p, f

    # Set addres, 'din', and 'wen' signals.
    yield mem.adr.eq(address)
    yield mem.we.eq(1)
    yield mem.ww.eq(0 if data_width < 1 or data_width > 8 else data_width)
    yield mem.dat_w.eq(data)
    yield mem.stb.eq(1)
    yield

    while (yield mem.ack) == 0:
        yield

    actual = None
    if data_width == 8:
        actual = yield mem.dat_r8
    elif data_width == 4:
        actual = yield mem.dat_r4
    elif data_width == 2:
        actual = yield mem.dat_r2
    else:
        actual = yield mem.dat_r
    if data != actual:
        f += 1
        print("\033[31mFAIL:\033[0m RAM[ 0x%08X ](%02d)  = "
            "0x%08X (got: 0x%08X)"
            %(address, data_width, data, actual))
    else:
        p += 1
        print("\033[32mPASS:\033[0m RAM[ 0x%08X ](%02d)  = 0x%08X"
            %(address, data_width, data))

    yield mem.we.eq(0)
    yield mem.stb.eq(0)
    yield


# Perform an individual RAM read unit test.
def ram_read_ut(mem, address, expected, data_width=1):
    global p, f

    # Set address.
    yield mem.adr.eq(address)
    yield mem.stb.eq(1)
    yield

    while (yield mem.ack) == 0:
        yield

    actual = None
    if data_width == 8:
        actual = yield mem.dat_r8
    elif data_width == 4:
        actual = yield mem.dat_r4
    elif data_width == 2:
        actual = yield mem.dat_r2
    else:
        actual = yield mem.dat_r
    if expected != actual:
        f += 1
        print("\033[31mFAIL:\033[0m RAM[ 0x%08X ](%02d) == "
            "0x%08X (got: 0x%08X)"
            %(address, data_width, expected, actual))
    else:
        p += 1
        print("\033[32mPASS:\033[0m RAM[ 0x%08X ](%02d) == 0x%08X"
            %(address, data_width, expected))

    yield mem.stb.eq(0)
    yield


# Top-level RAM test method.
def ram_test8(mem):
    global p, f

    # Print a test header.
    print("--- RAM Tests 8-Bit bus width ---")
    print("words: {}".format(mem.words))

    if mem.init is not None:
        # Test reading data back out of RAM initialized from demo file
        # yield from ram_read_ut(mem, 0x00, 0x00)
        yield from ram_read_ut(mem, 0x07, 0x01)
        yield from ram_read_ut(mem, 0x08, 0xBB)
        yield from ram_read_ut(mem, 0x09, 0x47)
        yield from ram_read_ut(mem, 0x0a, 0x11)

        yield from ram_read_ut(mem, 0x07, 0xBB01, data_width=2)
        yield from ram_read_ut(mem, 0x07, 0x1147BB01, data_width=4)
        yield from ram_read_ut(mem, 0x07, 0x60DD86001147BB01, data_width=8)

    else:
        if not mem.write_capable:
            print("\033[31mUnable to perform any tests as memory is not "
                "initialized and not write capable\033[0m")
            return

    if mem.write_capable:

        # Test writing data to RAM.
        yield from ram_write_ut(mem, 0x00, 0x01) # 1
        yield from ram_write_ut(mem, 0x01, 0x11)
        yield from ram_write_ut(mem, 0x02, 0x22)
        yield from ram_write_ut(mem, 0x03, 0x33)
        yield from ram_write_ut(mem, 0x04, 0x44)

        yield from ram_write_ut(mem, 0x05, 0x6655, data_width=2) # 2
        yield from ram_write_ut(mem, 0x07, 0x8877, data_width=2)

        yield from ram_write_ut(mem, 0x09, 0xccbbaa99, data_width=4) # 4
        yield from ram_write_ut(mem, 0x0d, 0x00ffeedd, data_width=4)

        yield from ram_write_ut(mem, 0x20, 0x2827262524232221, data_width=8) # 8
        yield from ram_write_ut(mem, 0x30, 0x3837363534333231, data_width=8)

        yield from ram_write_ut(mem, 0xd8, 0xD8)
        yield from ram_write_ut(mem, 0xd9, 0xD9)
        yield from ram_write_ut(mem, 0xda, 0xDA)
        yield from ram_write_ut(mem, 0xffffffff, 0xFA)

        # Test reading data from RAM.
        yield from ram_read_ut(mem, 0x09, 0x99)
        yield from ram_read_ut(mem, 0x0a, 0xaa)
        yield from ram_read_ut(mem, 0x0b, 0xbb)
        yield from ram_read_ut(mem, 0x0c, 0xcc)
        yield from ram_read_ut(mem, 0x0d, 0xdd)
        yield from ram_read_ut(mem, 0x0e, 0xee)
        yield from ram_read_ut(mem, 0x0f, 0xff)
        yield from ram_read_ut(mem, 0x10, 0x00)

        yield from ram_read_ut(mem, 0x05, 0x55)
        yield from ram_read_ut(mem, 0x06, 0x66)
        yield from ram_read_ut(mem, 0x07, 0x77)
        yield from ram_read_ut(mem, 0x08, 0x88)

        yield from ram_read_ut(mem, 0x20, 0x2827262524232221, data_width=8)

        yield from ram_read_ut(mem, 0x30, 0x34333231, data_width=4)
        yield from ram_read_ut(mem, 0x34, 0x3635, data_width=2)
        yield from ram_read_ut(mem, 0x36, 0x3837, data_width=2)

        yield from ram_read_ut(mem, 0x00, 0x01)
        yield from ram_read_ut(mem, 0x01, 0x11)
        yield from ram_read_ut(mem, 0x02, 0x22)
        yield from ram_read_ut(mem, 0x03, 0x33)
        yield from ram_read_ut(mem, 0x04, 0x44)

        yield from ram_read_ut(mem, 0xd8, 0xD8)
        yield from ram_read_ut(mem, 0xd9, 0xD9)
        yield from ram_read_ut(mem, 0xffffffff, 0xFA)
        yield from ram_read_ut(mem, mem.words-1, 0xFA)

        # roll over
        yield from ram_write_ut(mem, 0xffffffff, 0xF8F7F6F5F4F3F2F1, data_width=8)
        yield from ram_read_ut(mem, 0xffffffff, 0xF1)
        yield from ram_read_ut(mem, 0x00, 0xF5F4F3F2, data_width=4)
        yield from ram_read_ut(mem, 0x04, 0xF7F6, data_width=2)
        yield from ram_read_ut(mem, 0x06, 0xF8, data_width=1)

    # Done.
    yield
    print("RAM Tests: %d Passed, %d Failed"%(p, f))


# 'main' method to run a basic testbench.
if __name__ == "__main__":
    dut = RAM(init="../../tests/samples/test_data_mem.bin", max_words=1024,
              write_capable=True, csr_access=True, debug=True)
    run_simulation(dut, ram_test8(dut), vcd_name="ram.vcd")
