import random
import math
from migen import *


class Divider(Module):
    def __init__(self, data_width=32):
        self.dw = dw = data_width

        # Inputs
        self.reset_n = reset_n = Signal()

        self.dividend = dividend = Signal(dw)
        self.divisor = divisor = Signal(dw)
        self.stb = stb = Signal()

        # Outputs
        self.quotient = quotient = Signal(dw)
        self.remainder = remainder = Signal(dw)
        self.ack = ack = Signal()
        self.err = err = Signal()

        # # #

        qr = Signal(2*dw)
        counter = Signal(max=dw+1)
        divisor_r = Signal(dw)
        diff = Signal(dw+1)

        self.comb += [
            quotient.eq(qr[:dw]),
            remainder.eq(qr[dw:]),
            ack.eq(counter == 0),
            diff.eq(qr[dw-1:] - divisor_r)
        ]

        self.sync += [
            If(~reset_n,
                counter.eq(~0),
                qr.eq(0),
                err.eq(0),
            ).Else(
                If(stb,
                    err.eq(0),
                    If(divisor == 0,
                        counter.eq(0),
                        qr.eq(Cat(1, Replicate(0, dw-1), 1)),
                        err.eq(1)
                    ).Else(
                        counter.eq(dw),
                        qr.eq(dividend),
                        divisor_r.eq(divisor)
                    )
                ).Elif(~ack,
                    If(diff[dw],
                        qr.eq(Cat(0, qr[:2 * dw - 1]))
                    ).Else(
                        qr.eq(Cat(1, qr[:dw-1], diff[:dw]))
                    ),
                    counter.eq(counter - 1)
                )
            )
        ]


######################
# Divider testbench: #
######################
# Keep track of test pass / fail rates.
p = 0
f = 0

def div_test(divider, dividend, divisor):
    global p, f

    expected_error = False
    result = math.nan
    try:
        result = dividend / divisor
    except ZeroDivisionError:
        pass

    expected_quotioent = 0
    try:
        expected_quotioent = dividend // divisor
    except ZeroDivisionError:
        expected_error = True
        expected_quotioent = 1

    expected_remainder = 0
    try:
        expected_remainder = dividend % divisor
    except ZeroDivisionError:
        expected_error = True
        expected_remainder = 1

    num_dec_digits = int(math.log10(2**divider.dw)) + 1
    fail_fmt = ("\033[31mFAIL:\033[0m Divide(%%%dd / %%%dd) == q: %%%dd, " +
        "r: %%%dd got (q: %%%dd, r: %%d); err: %%d, res: %%%d.6f, " +
        "cycl: (%%3d)") % (
            num_dec_digits, num_dec_digits, num_dec_digits, num_dec_digits,
            num_dec_digits, num_dec_digits + 7)
    pass_fmt = ("\033[32mPASS:\033[0m Divide(%%%dd / %%%dd) == q: %%%dd, " +
        "r: %%%dd, err: %%d, res: %%%d.6f, " +
        "cycl: (%%3d)") % (
            num_dec_digits, num_dec_digits, num_dec_digits, num_dec_digits,
            num_dec_digits + 7)

    yield divider.reset_n.eq(0)
    for i in range(5):
        yield

    yield divider.reset_n.eq(1)
    for i in range(5):
        yield

    yield divider.dividend.eq(dividend)
    yield divider.divisor.eq(divisor)
    yield divider.stb.eq(1)
    yield

    yield divider.stb.eq(0)

    c = 1
    while (yield divider.ack) == 0 and c < 200:
        yield
        c += 1

    actual_quotient = yield divider.quotient
    actual_remainder = yield divider.remainder
    actual_error = yield divider.err
    if expected_quotioent != actual_quotient or \
            expected_remainder != actual_remainder or \
            expected_error != actual_error:
        f += 1
        print(fail_fmt
            %(dividend, divisor,
            expected_quotioent, expected_remainder,
            actual_quotient, actual_remainder, 1 if expected_error else 0,
            result, c))
    else:
        p += 1
        print(pass_fmt
            %(dividend, divisor,
            actual_quotient, actual_remainder, 1 if expected_error else 0,
            result, c))


def div_test8(divider):
    global p, f

    # Print a test header.
    print("--- Divider 8 ---")

    yield from div_test(divider, 13, 2)
    yield from div_test(divider, 8, 2)
    yield from div_test(divider, 42, 7)
    yield from div_test(divider, 23, 9)
    yield from div_test(divider, 88, 6)
    yield from div_test(divider, 255, 2)
    yield from div_test(divider, 255, 3)
    yield from div_test(divider, 255, 4)
    # Special cases
    yield from div_test(divider, 4, 8)
    yield from div_test(divider, 3, 3)
    yield from div_test(divider, 3, 0)
    yield from div_test(divider, 0, 0)
    yield from div_test(divider, 0, 2)
    # some random tests
    m = (2 ** divider.dw) - 1
    for i in range(20):
        yield from div_test(divider, random.randint(0, m), random.randint(0, m))

    # Done.
    yield
    print("Divider Tests: %d Passed, %d Failed"%(p, f))


def div_test32(divider):
    global p, f

    # Print a test header.
    print("--- Divider 32 ---")

    yield from div_test(divider, 13, 2)
    yield from div_test(divider, 1, 0)

    # Done.
    yield
    print("Divider Tests: %d Passed, %d Failed"%(p, f))


# 'main' method to run a basic testbench.
if __name__ == "__main__":
    dut = Divider(data_width=8)
    run_simulation(dut, div_test8(dut), vcd_name="divide.vcd")

    dut = Divider(data_width=32)
    run_simulation(dut, div_test32(dut), vcd_name="divide.vcd")
