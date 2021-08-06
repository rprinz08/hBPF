import sys
sys.path.insert(0, '..')

from migen import *


# This call handler provides three extensions to a hBPF CPU via the `call`
# opcode. The function is selected via hBPF register R1.
# It provides functions to read and write up to 5 64-bit values and a function
# to set some LEDs.
class CallHandler(Module):

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

        self.IP4_led = IP4_led = Signal()
        self.IPv6_led = IPv6_led = Signal()
        self.pkt_err_led = pkt_err_led = Signal()

        # # #

        # Store for 5 64-bit values
        self.specials.mem = mem = Memory(64, 5)
        self.specials.port = port = mem.get_port(has_re=False, write_capable=True)
        self.wait = wait = Signal()

        self.sync += [
            ack.eq(0),
            err.eq(0),

            If(stb,
                Case(func, {

                    # Extension to set IP4, IPv6 or packet error LED based on
                    # R1 bits 0 - 2
                    0xff000001: [
                        IP4_led.eq(r1[0]),
                        IPv6_led.eq(r1[1]),
                        pkt_err_led.eq(r1[2]),
                        ack.eq(1)
                    ],

                    # Extension to store some values
                    0xff000002: [
                        If(~port.we,
                            port.adr.eq(r1),
                            port.dat_w.eq(r2),
                            port.we.eq(1)
                        ).Else(
                            If(~wait,
                                wait.eq(1),
                            ).Else(
                                wait.eq(0),
                                port.we.eq(0),
                                ack.eq(1)
                            )
                        )
                    ],

                    # Extension to read values from store
                    0xff000003: [
                        If(~wait,
                            port.adr.eq(r1),
                            wait.eq(1)
                        ).Else(
                            wait.eq(0),
                            ret.eq(port.dat_r),
                            ack.eq(1)
                        )
                    ],

                    "default": [
                        err.eq(1),
                        ack.eq(1)
                    ]
                })
            )
        ]
