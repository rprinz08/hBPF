import sys
sys.path.insert(0, '..')

from migen import *
from litex.soc.interconnect.csr import AutoCSR
from fpga.constants import *
from fpga.ram64 import *
from fpga.resetable_fifo import *


class CPU_Fetch(Module, AutoCSR):
    """ CPU Instruction Fetch and Cache """

    MAX_PGM_WORDS = 4096
    CACHE_DEPTH = 2

    def __init__(self,
            init=None, max_words=MAX_PGM_WORDS, debug=False):

        # reset
        self.reset_n = reset_n = Signal()

        # input
        self.re = re = Signal()
        self.we = we = Signal()
        self.we_pending = we_pending = Signal()
        self.adr = adr = Signal(32)

        # output
        self.ip = ip = Signal(32)
        self.valid = valid = Signal()
        self.instruction = instruction = Signal(64)

        # # #

        cache_addr = cache_addr = Signal(32)

        self.submodules.cache = cache = ResetableSyncFIFO(
            width=64, depth=self.__class__.CACHE_DEPTH)

        self.submodules.pgm = pgm = RAM64(
                                max_words=max_words,
                                init=init, write_capable=False,
                                debug=debug)

        self.comb += [
            If(reset_n,
                If(~we,
                    cache.re.eq(re),
                    cache.reset.eq(0),
                    valid.eq(cache.readable),
                    pgm.adr.eq(cache_addr),
                ).Else(
                    cache.re.eq(0),
                    cache.reset.eq(1),
                    valid.eq(0),
                    pgm.adr.eq(cache_addr),
                ),
            ).Else(
                cache.re.eq(0),
                cache.reset.eq(1),
                valid.eq(0),
                pgm.adr.eq(0),
            ),

            If(valid, instruction.eq(cache.dout)),
        ]

        self.sync += [
            If(reset_n,
                cache.we.eq(0),
                If(cache.writable,
                    If(~pgm.stb,
                        pgm.stb.eq(1),
                    ).Else(
                        If(pgm.ack,
                            pgm.stb.eq(0),
                            we_pending.eq(0),
                            If(~we & ~we_pending,
                                cache.we.eq(1),
                                cache.din.eq(pgm.dat_r),
                                cache_addr.eq(cache_addr + 1)
                            )
                        )
                    )
                ),
                If(re & valid,
                    ip.eq(ip + 1)
                ),
                If(we,
                    If(pgm.stb & ~pgm.ack,
                        we_pending.eq(1)
                    ),
                    cache_addr.eq(adr),
                    ip.eq(adr)
                )
            ).Else(
                pgm.stb.eq(0),
                cache.we.eq(0),
                cache_addr.eq(0),
                ip.eq(0),
                we_pending.eq(0)
            )
        ]


########################
# CPU_fetch testbench: #
########################

def cpu_fetch_process(dut, instructions, addr=None, reset=False):
    cycles_per_op = 1
    cnt = 0
    wait = 0

    if reset:
        print(f"start with reset")
        yield dut.reset_n.eq(0)
        yield
        yield dut.reset_n.eq(1)
        yield
        cnt += 2

    if isinstance(addr, int):
        print(f"start at address {addr}")
        yield dut.adr.eq(addr)
        yield dut.we.eq(1)
        yield                       # valid = Low
        cnt += 1
        yield dut.we.eq(0)

    while instructions > 0:
        wait = 0
        # ensure cache is valid
        while (yield dut.valid != 1):
            wait += 1
            yield
            cnt += 1
        if wait > 0:
            print(f"Wait ({wait})")

        yield dut.re.eq(1)
        yield
        cnt += 1
        yield dut.re.eq(0)

        # get instruction and ip ...
        instruction = yield dut.instruction
        ip = yield dut.ip

        print("Instruction: {:08x}: {:016x}, clk {:04d}".format(
            ip, instruction, cnt))


        # Simulate instruction processing - n cycles
        for i in range(cycles_per_op):
            yield
            cnt += 1

        instructions -= 1


# Top-level test method.
def cpu_fetch_test(dut):
    global p, f
    addr = 0
    nins = 0

    # Print a test header.
    print("----------- CPU_Fetch Tests -----------")

    # 5 clocks in reset
    yield dut.reset_n.eq(0)
    for i in range(5):
        yield

    # CPU starts processing N instructions after reset
    nins = 5
    yield from cpu_fetch_process(dut, nins, reset=True)

    # Invalidate cache, set new address
    print("---------------------------------------")
    addr = 3
    nins = 5
    yield from cpu_fetch_process(dut, nins, addr=addr)

    # Invalidate cache, set new address
    print("---------------------------------------")
    addr = 2
    nins = 5
    yield from cpu_fetch_process(dut, nins, addr=addr)

    # Invalidate cache, set new address
    print("---------------------------------------")
    addr = 1
    nins = 5
    yield from cpu_fetch_process(dut, nins, addr=addr)

    print("---------------------------------------")
    yield from cpu_fetch_process(dut, nins, reset=True)

    print("---------------------------------------")
    addr = 3
    nins = 5
    yield from cpu_fetch_process(dut, nins, addr=addr)


# 'main' method to run a basic testbench.
if __name__ == "__main__":
    # Instantiate a CPU_IP module.
    dut = CPU_Fetch(init="../../tests/samples/test_pgm_mem.bin")

    # Run the tests.
    run_simulation(dut, cpu_fetch_test(dut), vcd_name="cpu_fetch.vcd")
