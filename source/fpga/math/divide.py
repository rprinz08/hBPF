#!/usr/bin/env python3

import sys
# add search paths when run from inside folder
# (used when running test directly)
sys.path.insert(0, '..')

import os
import random
import struct
import math
from migen import *
from migen.fhdl.bitcontainer import bits_for


class Divider(Module):
    STATE_IDLE = 0
    STATE_PREPARE = 1
    STATE_SHIFT = 2
    STATE_SUB = 3
    STATE_DONE = 4

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

        state = Signal(bits_for(self.STATE_DONE))
        dd = Signal(dw)
        dr = Signal(dw)
        q = Signal(dw)
        r = Signal(dw)
        bits = Signal(dw)

        self.sync += [
            If(~reset_n,
                dd.eq(0),
                dr.eq(0),
                q.eq(0),
                r.eq(0),
                ack.eq(0),
                err.eq(0),
                state.eq(self.STATE_IDLE)
            ).Else(
                Case(state, {
                    self.STATE_IDLE: [
                        ack.eq(0),
                        If(stb,
                            dd.eq(dividend),
                            dr.eq(divisor),
                            state.eq(self.STATE_PREPARE)
                        )
                    ],
                    self.STATE_PREPARE: [
                        q.eq(0),
                        r.eq(0),
                        bits.eq(dw),
                        state.eq(self.STATE_SHIFT),
                        # division by 0 (divisor == 0)
                        If(dr == 0,
                            q.eq(1),
                            r.eq(1),
                            err.eq(1),
                            state.eq(self.STATE_DONE)
                        # dividend < divisor
                        ).Elif(dd < dr,
                            r.eq(dd),
                            state.eq(self.STATE_DONE)
                        # dividend == divisor
                        ).Elif(dr == dd,
                            q.eq(1),
                            state.eq(self.STATE_DONE)
                        )
                    ],
                    self.STATE_SHIFT: [
                        If(Cat(dd[dw-1], r[0:dw-1]) < dr,
                            bits.eq(bits - 1),
                            r.eq(Cat(dd[dw-1], r[0:dw-1])),
                            dd.eq(Cat(0, dd[0:dw-1])),
                        ).Else(
                            state.eq(self.STATE_SUB)
                        )
                    ],
                    self.STATE_SUB: [
                        If(bits > 0,
                            r.eq(Cat(dd[dw-1], r[0:dw-1])),
                            dd.eq(Cat(0, dd[0:dw-1])),

                            If((Cat(dd[dw-1], r[0:dw-1]) - dr)[dw-1] == 0,
                                q.eq(Cat(1, q[0:dw-1])),
                                r.eq(Cat(dd[dw-1], r[0:dw-1]) - dr)
                            ).Else(
                                q.eq(Cat(0, q[0:dw-1]))
                            ),

                            bits.eq(bits - 1)
                        ).Else(
                            state.eq(self.STATE_DONE)
                        )
                    ],
                    self.STATE_DONE: [
                        ack.eq(1),
                        quotient.eq(q),
                        remainder.eq(r),
                        If(~stb,
                            state.eq(self.STATE_IDLE)
                        )
                    ],
                    "default": [
                        state.eq(self.STATE_IDLE)
                    ]
                })
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
    run_simulation(dut, div_test8(dut), vcd_name="math_divide.vcd")

    dut = Divider(data_width=32)
    run_simulation(dut, div_test32(dut), vcd_name="math_divide.vcd")
