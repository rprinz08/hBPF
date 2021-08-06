from migen import *

from litex.soc.cores.clock import *
from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer
from litex.soc.cores import uart
from litex.soc.cores.gpio import *

from fpga.ram import *
from fpga.ram64 import *
from fpga.cpu import *
from call_handler import *
import ubpf.assembler
import tools.testdata


# Helpers ----------------------------------------------------------------------
def platform_request_all(platform, name):
    from litex.build.generic_platform import ConstraintError
    r = []
    while True:
        try:
            r += [platform.request(name, len(r))]
        except ConstraintError:
            break
    if r == []:
        raise ValueError
    return r


# CRG --------------------------------------------------------------------------
class _CRG(Module):

    def __init__(self, platform, sys_clk_freq):
        self.rst = Signal()
        self.clock_domains.cd_sys = ClockDomain()

        # # #

        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        self.comb += pll.reset.eq(self.rst)
        pll.register_clkin(platform.request("clk125"), 125e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)


class Top(SoCMini):

    def __init__(self, platform, sys_clk_freq=int(100e6), **kwargs):

        self.platform = platform

        # SoCMini --------------------------------------------------------------
        SoCMini.__init__(self, self.platform, clk_freq=sys_clk_freq,
            ident          = "hBPF (Zybo-Z7) packet core",
            ident_version  = True,
            with_uart = False,
            **kwargs
        )

        # CRG ------------------------------------------------------------------
        self.submodules.crg = _CRG(self.platform, sys_clk_freq)

        # Misc GPIO ------------------------------------------------------------
        leds = platform_request_all(self.platform, "user_led")

        rgb_led_basename = "rgb_led"
        rgb_led_pads = self.platform.request(rgb_led_basename, 0)

        switches = platform_request_all(self.platform, "user_sw")

        # hbpf CPU -------------------------------------------------------------

        #----- Test Data -----

        # Prepare program memory
        #td = tools.testdata.read('../../../../tests/data/prime.test')
        #td = tools.testdata.read('../../../../tests/data/mul64-reg.test')
        td = tools.testdata.read('../../../../tests/data/hw/fpga_mem.test')

        if 'raw' in td:
            code = b''.join(struct.pack('<Q', x) for x in td['raw'])
        else:
            code = ubpf.assembler.assemble(td['asm'])
            td['raw'] = code
        half_words = len(code) // 4
        pgm_mem_data = list(struct.unpack('>{}L'.format(half_words), code))

        # Prepare data memory
        data_mem_test = td.get('mem')
        data_mem_data = None
        if isinstance(data_mem_test, bytes):
            data_mem_data = list(data_mem_test)

        #----------

        call_handler = CallHandler()
        self.submodules.hbpf = CPU(pgm_init=pgm_mem_data, max_pgm_words=1024,
                                    data_init=data_mem_data, max_data_words=2048,
                                    debug=True, call_handler=call_handler)
        self.add_csr("hbpf")
        self.csr.add("hbpf_pgm_mem", use_loc_if_exists=True)
        self.csr.add("hbpf_data_mem", use_loc_if_exists=True)

        counter = Signal(26)
        self.sync += [
            # switch controls hbpf reset_n signal
            self.hbpf.reset_n.eq(switches[0]),

            # green halt led
            leds[0].eq(self.hbpf.halt),

            # red error led
            rgb_led_pads.r.eq(self.hbpf.error),

            # debug led
            leds[1].eq(self.hbpf.debug),

            # simple heartbeat - shows that bitstream is loaded
            # has no other function then blinking a led
            counter.eq(counter + 1),
            leds[3].eq(counter[25])
        ]

        # LiteScope ------------------------------------------------------------
        analyzer_signals = [
            self.hbpf.reset_n,
            self.hbpf.error,
            self.hbpf.halt,
            self.hbpf.debug,
            self.hbpf.r0,
            self.hbpf.r1,
            self.hbpf.r2,
            self.hbpf.r3,
            self.hbpf.r4,
            self.hbpf.r5,
            self.hbpf.r7,
            self.hbpf.r8,
            self.hbpf.r9,
            self.hbpf.r10,
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals,
            depth        = 1024,
            clock_domain = "sys",
            csr_csv      = "debug/analyzer.csv")
        self.add_csr("analyzer")

        # Wishbone bridge ------------------------------------------------------
        uart_bridge = uart.UARTWishboneBridge(
            pads     = platform.request("usb_uart"),
            clk_freq = self.clk_freq,
            baudrate = 115200)
        self.submodules += uart_bridge
        self.add_wb_master(uart_bridge.wishbone)
