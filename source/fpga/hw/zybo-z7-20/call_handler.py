import sys
sys.path.insert(0, '..')

from migen import *
from litedram.frontend.bist import LFSR


class CallHandler(Module):

    PRBS31 = [27, 30]
    PRBS23 = [17, 22]
    PRBS15 = [13, 14]
    PRBS7  = [ 5,  6]

    def __init__(self):
        self.func = func = Signal(64)
        self.r1 = r1 = Signal(64)
        self.r2 = r2 = Signal(64)
        self.r3 = r3 = Signal(64)
        self.r4 = r4 = Signal(64)
        self.r5 = r5 = Signal(64)
        self.ret = ret = Signal(64)
        self.stb = stb = Signal()
        self.ack = ack = Signal()
        self.err = err = Signal()

        # # #

        self.submodules.lfsr = lfsr = LFSR(31, n_state=31, taps=self.__class__.PRBS31)

        self.sync += [
            ack.eq(0),
            err.eq(0),
            If(stb,
                Case(func, {
                    0: [
                        ret.eq(
                            ((r1 & 0xff) << 32) |
                            ((r2 & 0xff) << 24) |
                            ((r3 & 0xff) << 16) |
                            ((r4 & 0xff) << 8) |
                            r5
                        )
                    ],
                    #6: [],
                    7: [
                        ret.eq(lfsr.o)
                    ],
                    "default": [
                        err.eq(1)
                    ]
                }),
                ack.eq(1)
            )
        ]
