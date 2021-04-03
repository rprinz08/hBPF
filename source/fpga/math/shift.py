from migen import *


class Shifter(Module):

    def __init__(self, data_width=64):

        self.stb = stb = Signal()
        self.arith = arith = Signal()
        self.left = left = Signal()
        self.value = value = Signal(data_width)
        self.shift = shift = Signal(max=data_width)
        self.out = out = Signal(data_width)
        self.ack = ack = Signal()

        # # #

        state = Signal()
        tmp1 = Signal(data_width)
        tmp2 = Signal(data_width)

        self.sync += [
            If(ack,
                ack.eq(0),
                state.eq(0)
            ).Elif(state,
                If(~left & arith & value[data_width-1],
                    out.eq(tmp1 | tmp2)
                ).Else(
                    out.eq(tmp2)
                ),
                ack.eq(1)
            ).Elif(stb,
                If(~left,
                    tmp1.eq(~(Replicate(1, data_width) >> shift)),
                    tmp2.eq(value >> shift),
                ).Else(
                    tmp2.eq(value << shift),
                ),
                state.eq(1)
            )
        ]


######################
# Divider testbench: #
######################
# Keep track of test pass / fail rates.
p = 0
f = 0

def arsh_test(arsh, value, shift, expected):
    global p, f

    for i in range(5):
        yield

    yield arsh.value.eq(value)
    yield arsh.shift.eq(shift)
    yield arsh.stb.eq(1)
    yield arsh.arith.eq(1)
    yield arsh.left.eq(0)
    yield

    yield arsh.stb.eq(0)
    yield

    c = 1
    while (yield arsh.ack) == 0 and c < 100:
        yield
        c += 1

    actual = yield arsh.out
    if expected != actual:
        f += 1
        print("\033[31mFAIL:\033[0m ARSH( %08d, %03d ) = "
            "%08d (got: %08d)"
            %(value, shift, expected, actual))
    else:
        p += 1
        print("\033[32mPASS:\033[0m ARSH( %08d, %03d ) = "
            "%08d"
            %(value, shift, expected))


def arsh_test64(arsh):
    global p, f

    # Print a test header.
    print("--- Arithmetic Right Shift 32 ---")

    yield from arsh_test(arsh, 0x1000, 1, 0x0800)
    yield from arsh_test(arsh, 1, 1, 0)
    yield from arsh_test(arsh, 0x8000000000000080, 4, 0xf800000000000008)
    yield from arsh_test(arsh, 0x8000000000000000, 60, 0xfffffffffffffff8)

    # Done.
    yield
    print("ARSH Tests: %d Passed, %d Failed"%(p, f))


# 'main' method to run a basic testbench.
if __name__ == "__main__":
    dut = Shifter(data_width=64)
    run_simulation(dut, arsh_test64(dut), vcd_name="math.vcd")
