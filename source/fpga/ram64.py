import sys
sys.path.insert(0, '..')

import os
import math
from migen import *
from litex.soc.interconnect.csr import AutoCSR
from tools.common import *


class RAM64(Module, AutoCSR):

    def __init__(self, max_words=None,
                init=None, endianness="big",
                debug=False):

        self.init = None
        self.words = None
        self.half_words = None

        if isinstance(max_words, int):
            self.words = max_words
            self.half_words = self.words * 2

        self.adr = Signal(31)

        self.dat_r = Signal(64)

        # # #

        adr_hold = Signal(31)

        if debug:
            print("-"*50)
            print("RAM64")

        # 'words' specify the number of 64bit entities (words). 'half_words'
        # specify the number of 32bit entities. They can either be specified
        # when instantiating or be determined from a given data content.
        # If both are specified the given word size cannot be less then
        # required words to fit the file contents.
        init_words = None
        init_half_words = None

        if isinstance(init, Memory):
            assert init.width == 32, \
                "Only 32-Bit width memory supported"

            self.specials.mem = init
            init_half_words = init.width
            init_words = math.ceil(init_half_words / 2)
        else:
            # Read a binary data into memory if specified
            if isinstance(init, str):
                init_file = os.path.abspath(os.path.dirname(__file__))
                init_file = os.path.join(init_file, init)
                #ebpf_file_size = os.stat(ebpf_file).st_size
                #self.init = init_file
                self.init = get_data(init_file, data_width_bits=32, endianness=endianness)
                init_half_words = len(self.init)
                init_words = math.ceil(init_half_words / 2)
                if debug:
                    print("init from file:          {}".format(init_file))
            elif isinstance(init, list):
                self.init = init
                init_half_words = len(self.init)
                init_words = math.ceil(init_half_words / 2)
                if debug:
                    print("init from list:      len {}".format(len(self.init)))

            if debug:
                print("max words:               {}".format(max_words))
                print("file words:              {}".format(init_words))
                print("file half-words:         {}".format(init_words))

            if self.words is None:
                self.words = init_words
                self.half_words = init_half_words
                if debug:
                    print("instance words:          {}".format(self.words))
                    print("instance half-words:     {}".format(self.half_words))
            else:
                if debug:
                    print("instance words:          {}".format(self.words))
                    print("instance half-words:     {}".format(self.half_words))
                if self.init is not None:
                    assert init_words <= self.words, \
                        "File contents ({} words) does not fit into specified " \
                        "maximum ({} words)".format(init_words, self.words)

            assert self.words is not None, \
                "Either number of words or data must be specified"

            self.specials.mem = Memory(32, self.words, init=self.init)

        self.specials.port = self.mem.get_port(has_re=True, async_read=True,
            write_capable=False)

        # Get next half word based on current word address
        self.specials.port2 = self.mem.get_port(has_re=True, async_read=True,
                                write_capable=False, we_granularity=0,
                                mode=READ_FIRST)

        self.comb += [
            self.port2.adr.eq(self.port.adr + 1),
            self.dat_r.eq(Cat(self.port2.dat_r, self.port.dat_r)),
        ]

        self.comb += [
            self.port.adr.eq(self.adr << 1),
        ]

        self.sync += [
            self.port.re.eq(0),
            If(~self.port.re,
                adr_hold.eq(self.adr),
                self.port.re.eq(1)
            )
        ]

##################
# RAM testbench: #
##################
# Keep track of test pass / fail rates.
p = 0
f = 0

# Perform an individual RAM read unit test.
def ram_read_ut(mem, address, expected):
    global p, f

    # Set address.
    yield mem.adr.eq(address)
    yield

    actual = yield mem.dat_r
    if expected != actual:
        f += 1
        print("\033[31mFAIL:\033[0m RAM[ 0x%08X ] == "
            "0x%08X (got: 0x%016X)"
            %(address, expected, actual))
    else:
        p += 1
        print("\033[32mPASS:\033[0m RAM[ 0x%08X ] == 0x%016X"
            %(address, expected))

    yield


# Top-level RAM test method.
def ram_test(mem):
    global p, f

    # Print a test header.
    print("--- RAM Tests ---")

    if mem.init is not None:
        # Test reading data back out of RAM initialized from demo file
        yield from ram_read_ut(mem, 0x00, 0xB400000000000000)
        yield from ram_read_ut(mem, 0x02, 0x69100C0000000000)
        yield from ram_read_ut(mem, 0x01, 0xB406000000000000)
        yield from ram_read_ut(mem, 0x03, 0xDC00000010000000)

    # Continuos read
    # Set address.
    addr = 0
    cnt = 5
    yield mem.adr.eq(addr)
    yield

    while cnt > 0:
        addr += 1
        cnt -= 1
        yield mem.adr.eq(addr)
        yield

    for i in range(5):
        yield

    # Done.
    yield
    print("RAM Tests: %d Passed, %d Failed"%(p, f))


# 'main' method to run a basic testbench.
if __name__ == "__main__":
    # Instantiate a read only Mem module.
    dut = RAM64(init="../../tests/samples/test_pgm_mem.bin")

    # Run the tests.
    run_simulation(dut, ram_test(dut), vcd_name="ram64.vcd")
