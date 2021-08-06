from migen import *

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer
from litex.soc.cores import uart
from litex.soc.cores.gpio import *
from liteeth.common import *
from liteeth.phy.rmii import LiteEthPHYRMII
from liteeth.mac import LiteEthMACCore

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

    def __init__(self, platform, sys_clk_freq,
            eth0_clock):

        self.rst = Signal()
        self.clock_domains.cd_sys = ClockDomain()

        # # #

        self.cd_sys.clk.attr.add("keep")

        clk100 = platform.request("clk100")
        platform.add_period_constraint(clk100, 1e9/100e6)

        self.clock_domains.cd_eth0      = ClockDomain()

        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        self.comb += pll.reset.eq(self.rst)
        pll.register_clkin(clk100, 100e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)

        # external eth ref clocks
        self.comb += self.cd_eth0.clk.eq(eth0_clock.ref_clk)


# Top --------------------------------------------------------------------------
class Top(SoCMini):

    def __init__(self, platform, sys_clk_freq=int(100e6), **kwargs):

        self.platform = platform

        # SoCMini --------------------------------------------------------------
        SoCMini.__init__(self, self.platform, clk_freq=sys_clk_freq,
            ident          = "hBPF (Arty-S7 MultiNet) packet test",
            ident_version  = True,
            with_uart = False,
            **kwargs
        )

        self.mem_map = {**self.mem_map, **{
            "ethmac":       0xb0_000_000,
            "csr":          0xf0_000_000
        }}

        # CRG ------------------------------------------------------------------
        eth0_clock = self.platform.request("eth_clocks_ext", 0)
        self.submodules.crg = _CRG(self.platform, sys_clk_freq,
                                    eth0_clock)

        # Misc GPIO ------------------------------------------------------------
        leds = platform_request_all(self.platform, "user_led")

        rgb_led_basename = "rgb_led"
        rgb_led1_pads = self.platform.request(rgb_led_basename, 0)
        rgb_led2_pads = self.platform.request(rgb_led_basename, 1)


        # hbpf CPU -------------------------------------------------------------

        # Prepare initial program memory
        td = tools.testdata.read('../../../../tests/data/hw/fpga_ping_seq.test')

        if 'raw' in td:
            code = b''.join(struct.pack('<Q', x) for x in td['raw'])
        else:
            code = ubpf.assembler.assemble(td['asm'])
            td['raw'] = code
        half_words = len(code) // 4
        pgm_mem_data = list(struct.unpack('>{}L'.format(half_words), code))

        # Add a custom call handler to extend the CPU
        call_handler = CallHandler()

        # Instantiate the CPU
        self.submodules.hbpf = CPU(pgm_init=pgm_mem_data, max_pgm_words=1024,
                                    data_init=None, max_data_words=2048,
                                    debug=True, call_handler=call_handler)
        self.add_csr("hbpf")
        self.csr.add("hbpf_pgm_mem", use_loc_if_exists=True)
        self.csr.add("hbpf_data_mem", use_loc_if_exists=True)

        # Connect CPU signals
        counter = Signal(26)
        processing_led_delay = Signal(26)

        self.sync += [
            # green, CPU halt LED
            leds[0].eq(self.hbpf.halt),

            # red, CPU error LED
            rgb_led1_pads.r.eq(self.hbpf.error),

            If(~self.hbpf.error,
                # green, packet class 1 (e.g. IPv4) LED
                leds[1].eq(call_handler.IP4_led),

                # green, packet class 2 (e.g. IPv6) LED
                leds[2].eq(call_handler.IPv6_led),

                # red, packet error LED
                rgb_led2_pads.r.eq(call_handler.pkt_err_led),

                # blue, packet processing LED
                If(self.hbpf.reset_n & ~self.hbpf.halt,
                    processing_led_delay.eq(0x300_000)
                ),
                If(processing_led_delay > 0,
                    processing_led_delay.eq(processing_led_delay - 1)
                ),
                rgb_led1_pads.b.eq(processing_led_delay > 0)
            ).Else (
                leds[1].eq(0),
                leds[2].eq(0),
                rgb_led1_pads.g.eq(0),
                rgb_led1_pads.b.eq(0),
                rgb_led2_pads.r.eq(0),
                rgb_led2_pads.g.eq(0),
                rgb_led2_pads.b.eq(0),
            ),

            # simple heartbeat - shows that bitstream is loaded
            # has no other function then blinking a led
            counter.eq(counter + 1),
            leds[3].eq(counter[25])
        ]

        # Ethernet ------------------------------------------------------------
        # Ethernet interface 0 PHY.
        self.submodules.ethphy = LiteEthPHYRMII(
            clock_pads = None,
            pads       = self.platform.request("eth", 0),
            with_hw_init_reset=True, refclk_cd="eth0")
        self.add_csr("ethphy")

        self.platform.add_period_constraint(
            self.ethphy.crg.cd_eth_rx.clk, 1e9/self.ethphy.rx_clk_freq)
        self.platform.add_period_constraint(
            self.ethphy.crg.cd_eth_tx.clk, 1e9/self.ethphy.tx_clk_freq)

        dw = 8

        # Add a LiteEthMACCore as source ...
        self.submodules.ethmac = LiteEthMACCore(self.ethphy, dw, with_preamble_crc=True)
        self.add_csr("ethmac")

        # ... and define a sink which transfers
        # received packets from MAC into hBPF packet memory.
        self.sink = stream.Endpoint(eth_phy_description(dw))
        self.comb += self.ethmac.source.connect(self.sink)
        last = Signal()

        self.sync += [
            # Stop everything on hBPF CPU error - needs hard reset
            If(~self.hbpf.error,
                If(self.hbpf.halt | ~self.hbpf.reset_n,
                    If(self.hbpf.halt,
                        # hBPF finished processing of packet
                        # reset for next packet
                        self.hbpf.data.adr.eq(0),
                        self.hbpf.csr_r1.storage.eq(0)
                    ),
                    self.hbpf.reset_n.eq(0),

                    If(~self.hbpf.data.stb,
                        self.sink.ready.eq(1),
                        If(self.sink.valid,
                            self.hbpf.data.ww.eq(1),
                            self.hbpf.data.dat_w.eq(self.sink.data),
                            self.hbpf.data.we.eq(1),
                            self.hbpf.data.stb.eq(1),
                            self.sink.ready.eq(0),

                            # Place length of received packet into hBPF CPU register R1
                            If(self.sink.last,
                                last.eq(1),
                                self.hbpf.csr_r1.storage.eq(self.hbpf.data.adr + 1),
                            )
                        )
                    ).Else(
                        If(self.hbpf.data.ack,
                            self.hbpf.data.stb.eq(0),
                            If(last & ~self.sink.last,
                                last.eq(0),
                                # Packet fully received, start hBPF,
                                # length of captured packet is provided to CPU in R1
                                self.hbpf.data.adr.eq(0),
                                self.hbpf.reset_n.eq(1),
                            ).Else(
                                self.hbpf.data.adr.eq(self.hbpf.data.adr + 1),
                                self.sink.ready.eq(1),
                            )
                        )
                    )
                )
            )
        ]

        # LiteScope ------------------------------------------------------------
        analyzer_signals = [
            # hBPF CPU signals
            self.hbpf.reset_n,
            self.hbpf.error,
            self.hbpf.halt,
            self.hbpf.debug,
            self.hbpf.r0,
            self.hbpf.r1,

            # MAC to hBPF packet memory signals
            self.ethmac.source,
            self.ethmac.sink,
            self.sink,
            self.hbpf.data.stb,
            self.hbpf.data.ack,
            self.hbpf.data.dat_w,
            self.hbpf.data.ww,
            self.hbpf.data.we,
            self.hbpf.data.adr,
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals,
            depth        = 4096,
            #clock_domain = "sys",
            clock_domain = "eth_rx",
            csr_csv      = "debug/analyzer.csv")
        self.add_csr("analyzer")

        # Wishbone bridge ------------------------------------------------------
        uart_bridge = uart.UARTWishboneBridge(
            pads     = platform.request("serial"),
            clk_freq = self.clk_freq,
            baudrate = 115200)
        self.submodules += uart_bridge
        self.add_wb_master(uart_bridge.wishbone)
