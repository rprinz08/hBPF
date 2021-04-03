from migen import *


class CPU_IP(Module):
    """ CPU Instruction Pointer """

    def __init__(self):

        self.reset_n = reset_n = Signal()
        self.enable = enable = Signal()
        self.val = ip = Signal(32)
        self.adj = adj = Signal((32, True))

        ###

        self.sync += [
            If(~reset_n,
                ip.eq(0)
            ).Else(
                If(enable,
                    ip.eq(ip + adj)
                )
            )
        ]


#####################
# CPU_IP testbench: #
#####################
# Keep track of test pass / fail rates.
p = 0
f = 0

def cpu_ip_compare(cpu_ip, value):
    global p, f

    ip = yield cpu_ip.val
    if ip != value:
        f += 1
        print("\033[31mFAIL:\033[0m CPU IP = 0x%08X (got 0x%08X)" % (ip, value))
    else:
        p += 1
        print("\033[32mPASS:\033[0m CPU IP = 0x%08X (got 0x%08X)" % (ip, value))


# Top-level CPU_IP test method.
def cpu_ip_test(cpu_ip):
    global p, f

    # Print a test header.
    print("--- CPU_IP Tests ---")

    # in reset
    yield cpu_ip.reset_n.eq(0)
    for i in range(5):
        yield
    yield from cpu_ip_compare(cpu_ip, 0)

    # enable but adj = 0
    yield cpu_ip.reset_n.eq(1)
    for i in range(5):
        yield
    yield from cpu_ip_compare(cpu_ip, 0)

    # enable and adj = 1
    yield cpu_ip.adj.eq(1)
    yield cpu_ip.enable.eq(1)
    yield
    for i in range(5):
        yield cpu_ip.enable.eq(i < 4)
        yield
    yield from cpu_ip_compare(cpu_ip, 5)

    # enable and adj = 2
    yield cpu_ip.adj.eq(2)
    yield cpu_ip.enable.eq(1)
    yield
    for i in range(5):
        yield cpu_ip.enable.eq(i < 4)
        yield
    yield from cpu_ip_compare(cpu_ip, 15)

    # enable and adj = -1
    yield cpu_ip.adj.eq(-1)
    yield cpu_ip.enable.eq(1)
    yield
    for i in range(5):
        yield cpu_ip.enable.eq(i < 4)
        yield
    yield from cpu_ip_compare(cpu_ip, 10)

    # enable and adj = -2
    yield cpu_ip.adj.eq(-2)
    yield cpu_ip.enable.eq(1)
    yield
    for i in range(5):
        yield cpu_ip.enable.eq(i < 4)
        yield
    yield from cpu_ip_compare(cpu_ip, 0)

    # Done.
    yield
    print("CPU_IP Tests: %d Passed, %d Failed" % (p, f))


# 'main' method to run a basic testbench.
if __name__ == "__main__":
    # Instantiate a CPU_IP module.
    dut = CPU_IP()

    # Run the tests.
    run_simulation(dut, cpu_ip_test(dut), vcd_name="cpu_ip.vcd")

