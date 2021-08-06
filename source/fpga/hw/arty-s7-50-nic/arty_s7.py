# This file is Copyright (c) 2020 Richard Prinz <richard.prinz@min.at>
# License: BSD

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, XC3SProg, VivadoProgrammer
from litex.build.openocd import OpenOCD

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk100", 0, Pins("R2"), IOStandard("SSTL135")),
    ("cpu_reset", 0, Pins("C18"), IOStandard("LVCMOS33")),

    # Leds
    ("user_led", 0, Pins("E18"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("F13"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("E13"), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins("H15"), IOStandard("LVCMOS33")),

    ("leds", 0, Pins("E18 F13 E13 H15"),
        IOStandard("LVCMOS33")),

    ("rgb_led", 0,
        Subsignal("r", Pins("J15")),
        Subsignal("g", Pins("G17")),
        Subsignal("b", Pins("F15")),
        IOStandard("LVCMOS33")
    ),

    ("rgb_led", 1,
        Subsignal("r", Pins("E15")),
        Subsignal("g", Pins("F18")),
        Subsignal("b", Pins("E14")),
        IOStandard("LVCMOS33")
    ),

    # Switches
    ("user_sw", 0, Pins("H14"), IOStandard("LVCMOS33")),
    ("user_sw", 1, Pins("H18"), IOStandard("LVCMOS33")),
    ("user_sw", 2, Pins("G18"), IOStandard("LVCMOS33")),
    ("user_sw", 3, Pins("M5"), IOStandard("SSTL135")),

    ("user_btn", 0, Pins("G15"), IOStandard("LVCMOS33")),
    ("user_btn", 1, Pins("K16"), IOStandard("LVCMOS33")),
    ("user_btn", 2, Pins("J16"), IOStandard("LVCMOS33")),
    ("user_btn", 3, Pins("H13"), IOStandard("LVCMOS33")),

    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("R12")),
        Subsignal("rx", Pins("V12")),
        IOStandard("LVCMOS33")),

    # Unavailable; used for Ethernet
    # SPI
    #("spi", 0,
    #    Subsignal("clk",  Pins("G16")),
    #    Subsignal("cs_n", Pins("H16")),
    #    Subsignal("mosi", Pins("H17")),
    #    Subsignal("miso", Pins("K14")),
    #    IOStandard("LVCMOS33")
    #),

    # When using an Arduino Wireless SD shield
    # https://store.arduino.cc/arduino-wireless-sd-shield
    #("spisdcard", 0,
    #    Subsignal("clk", Pins("G16")),
    #    Subsignal("cs_n", Pins("T14")), # CK_IO4
    #    Subsignal("mosi", Pins("H17")),
    #    Subsignal("miso", Pins("K14")),
    #    IOStandard("LVCMOS33")
    #),

    # For digilent PMOD SD-Card on PMOD-D
    # https://store.digilentinc.com/pmod-microsd-microsd-card-slot/
    #("spisdcard", 0,
    #    Subsignal("clk", Pins("T12")),
    #    Subsignal("cs_n", Pins("V15")),
    #    Subsignal("mosi", Pins("U12")),
    #    Subsignal("miso", Pins("V13")),
    #    IOStandard("LVCMOS33")
    #),

    # For digilent PMOD SD-Card on Arty-S7-50-MultiNet shield
    # https://store.digilentinc.com/pmod-microsd-microsd-card-slot/
    ("spisdcard", 0,
        Subsignal("clk", Pins("U12")),
        Subsignal("cs_n", Pins("U15")),
        Subsignal("mosi", Pins("V16")),
        Subsignal("miso", Pins("V15")),
        IOStandard("LVCMOS33")
    ),

    # SPIFlash
    ("spiflash", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("M13")),
        Subsignal("clk",  Pins("D11")),
        Subsignal("mosi", Pins("K17")),
        Subsignal("miso", Pins("K18")),
        Subsignal("wp",   Pins("L14")),
        Subsignal("hold", Pins("M15")),
        IOStandard("LVCMOS33")
    ),
    ("spiflash4x", 0,  # clock needs to be accessed through STARTUPE2
        Subsignal("cs_n", Pins("M13")),
        Subsignal("clk",  Pins("D11")),
        Subsignal("dq", Pins("K17", "K18", "L14", "M15")),
        IOStandard("LVCMOS33")
    ),

    # DDR3 SDRAM
    ("ddram", 0,
        Subsignal("a", Pins(
            "U2 R4 V2 V4 T3 R7 V6 T6",
            "U7 V7 P6 T5 R6 U6"),
            IOStandard("SSTL135")),
        Subsignal("ba", Pins("V5 T1 U3"), IOStandard("SSTL135")),
        Subsignal("ras_n", Pins("U1"), IOStandard("SSTL135")),
        Subsignal("cas_n", Pins("V3"), IOStandard("SSTL135")),
        Subsignal("we_n",  Pins("P7"), IOStandard("SSTL135")),
        Subsignal("cs_n",  Pins("R3"), IOStandard("SSTL135")),
        Subsignal("dm", Pins("K4 M3"), IOStandard("SSTL135")),
        Subsignal("dq", Pins(
            "K2 K3 L4 M6 K6 M4 L5 L6",
            "N4 R1 N1 N5 M2 P1 M1 P2"),
            IOStandard("SSTL135"),
            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("dqs_p", Pins("K1 N3"),
            IOStandard("DIFF_SSTL135"),
            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("dqs_n", Pins("L1 N2"),
            IOStandard("DIFF_SSTL135"),
            Misc("IN_TERM=UNTUNED_SPLIT_40")),
        Subsignal("clk_p", Pins("R5"), IOStandard("DIFF_SSTL135")),
        Subsignal("clk_n", Pins("T4"), IOStandard("DIFF_SSTL135")),
        Subsignal("cke",   Pins("T2"), IOStandard("SSTL135")),
        Subsignal("odt",   Pins("P5"), IOStandard("SSTL135")),
        Subsignal("reset_n", Pins("J6"), IOStandard("SSTL135")),
        Misc("SLEW=FAST"),
    ),

    # PMOD A
    ("pmoda", 0, Pins("L17 L18 M14 N14 M16 M17 M18 N18"),
        IOStandard("LVCMOS33")),

    # PMOD B
    ("pmodb", 0, Pins("P17 P18 R18 T18 P14 P15 N15 P16"),
        IOStandard("LVCMOS33")),

    # PMOD C
    ("pmodc", 0, Pins("U15 V16 U17 U18 U16 P13 R13 V14"),
        IOStandard("LVCMOS33")),

    # PMOD D
    ("pmodd", 0, Pins("V15 U12 V13 T12 T13 R11 T11 U11"),
        IOStandard("LVCMOS33")),

	# Ethernet 0
	("eth_clocks_ext", 0,
		Subsignal("ref_clk", Pins("R16")),
		IOStandard("LVCMOS33")
	),
	("eth", 0,
		Subsignal("mdio", Pins("J14")),
		Subsignal("mdc", Pins("J13")),

		Subsignal("crs_dv", Pins("L13")),
		Subsignal("rx_data", Pins("N13 L16")),
		Subsignal("tx_data", Pins("R17 V17")),
		Subsignal("tx_en", Pins("T14")),
		IOStandard("LVCMOS33")
	),

	# Ethernet 1
	("eth_clocks_ext", 1,
		Subsignal("ref_clk", Pins("G16")),
		IOStandard("LVCMOS33")
	),
	("eth", 1,
        # connected to MDIO bus of eth0
		Subsignal("crs_dv", Pins("R15")),
		Subsignal("rx_data", Pins("T15 H16")),
		Subsignal("tx_data", Pins("K14 K13")),
		Subsignal("tx_en", Pins("H17")),
		IOStandard("LVCMOS33")
	),

	# Ethernet 2
	("eth_clocks_ext", 2,
		Subsignal("ref_clk", Pins("D14")),
		IOStandard("LVCMOS33")
	),
	("eth", 2,
        # connected to MDIO bus of eth0
		Subsignal("crs_dv", Pins("U17")),
		Subsignal("rx_data", Pins("U18 U16")),
		Subsignal("tx_data", Pins("R13 V14")),
		Subsignal("tx_en", Pins("P13")),
		IOStandard("LVCMOS33")
	),

	# Ethernet 3
	("eth_clocks_ext", 3,
		Subsignal("ref_clk", Pins("R14")),
		IOStandard("LVCMOS33")
	),
	("eth", 3,
        # connected to MDIO bus of eth0
		Subsignal("crs_dv", Pins("V13")),
		Subsignal("rx_data", Pins("T12 T13")),
		Subsignal("tx_data", Pins("T11 U11")),
		Subsignal("tx_en", Pins("R11")),
		IOStandard("LVCMOS33")
	)
]

# Connectors ---------------------------------------------------------------------------------------

_connectors = [
    ("pmoda", "L17 L18 M14 N14 M16 M17 M18 N18"),
    ("pmodb", "P17 P18 R18 T18 P14 P15 N15 P16"),
    ("pmodc", "U15 V16 U17 U18 U16 P13 R13 V14"),
    ("pmodd", "V15 U12 V13 T12 T13 R11 T11 U11"),
    ("ck_io", {
        # Outer Digital Header
        "ck_io0"  : "L13",
        "ck_io1"  : "N13",
        "ck_io2"  : "L16",
        "ck_io3"  : "R14",
        "ck_io4"  : "T14",
        "ck_io5"  : "R16",
        "ck_io6"  : "R17",
        "ck_io7"  : "V17",
        "ck_io8"  : "R15",
        "ck_io9"  : "T15",
        "ck_io10" : "H16", # SS
        "ck_io11" : "H17", # MOSI
        "ck_io12" : "K14", # MISO
        "ck_io13" : "G16", # SCK

        # Inner Digital Header
        "ck_io26" : "U11", # JD10
        "ck_io27" : "T11", # JD9
        "ck_io28" : "R11", # JD8
        "ck_io29" : "T13", # JD7
        "ck_io30" : "T12", # JD4
        "ck_io31" : "V13", # JD3
        "ck_io32" : "U12", # JD2
        "ck_io33" : "V15", # JD1
        "ck_io34" : "V14", # JC10
        "ck_io35" : "R13", # JC9
        "ck_io36" : "P13", # JC8
        "ck_io37" : "U16", # JC7
        "ck_io38" : "U18", # JC4
        "ck_io39" : "U17", # JC3
        "ck_io40" : "V16", # JC2
        "ck_io41" : "U15", # JC1

        # Outer Analog Header as Digital IO
        "ck_a0" : "G13",
        "ck_a1" : "B16",
        "ck_a2" : "A16",
        "ck_a3" : "C13",
        "ck_a4" : "C14",
        "ck_a5" : "D18",

        # Inner Analog Header as Digital IO
        "ck_a6"  : "B14", # AD8_P
        "ck_a7"  : "A14", # AD8_N
        "ck_a8"  : "D16", # AD3_P
        "ck_a9"  : "D17", # AD3_N
        "ck_a10" : "D14",
        "ck_a11" : "D15"
        }
    ),
    ("XADC", {
        # Outer Analog Header
        "vaux0_p"  : "B13",
        "vaux0_n"  : "A13",
        "vaux1_p"  : "B15",
        "vaux1_n"  : "A15",
        "vaux9_p"  : "E12",
        "vaux9_n"  : "D12",
        "vaux2_p"  : "B17",
        "vaux2_n"  : "A17",
        "vaux10_p" : "C17",
        "vaux10_n" : "B18",
        "vaux11_p" : "E16",
        "vaux11_n" : "E17",

        # Inner Analog Header
        "vaux8_p" : "B14",
        "vaux8_n" : "A14",
        "vaux3_p" : "D16",
        "vaux3_n" : "D17",
        }
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name = "clk100"
    default_clk_period = 1e9/100e6

    def __init__(self, variant="s7-50",
                 toolchain="vivado", programmer="vivado"):
        # Arty-S7 is available in two versions with different FPGA devices
        device = {
            "s7-50": "xc7s50csga324-1",
            "s7-25": "xc7s25csga324-1"
        }[variant]
        self.device_variant = variant

        XilinxPlatform.__init__(self, device, _io, _connectors,
                                toolchain=toolchain)
        self.toolchain.bitstream_commands = \
            ["set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]"]
        self.toolchain.additional_commands = \
            ["write_cfgmem -force -format bin -interface spix4 -size 16 "
             "-loadbit \"up 0x0 {build_name}.bit\" -file {build_name}.bin"]
        self.programmer = programmer
        self.add_platform_command("set_property INTERNAL_VREF 0.675 [get_iobanks 34]")

    def create_programmer(self, **kwargs):
        # For xc3sprog
        # See also http://xc3sprog.sourceforge.net
        # get source with: svn checkout https://svn.code.sf.net/p/xc3sprog/code/trunk xc3sprog
        if self.programmer == "xc3sprog":
            # to program the configuration flash, the FPGA must first be
            # programmed with a bitstream which provides a way to foward
            # data to flash. This is called a "flash proxy". Flash proxies
            # for some parts are already included in xc3sprog. Additional
            # ones can be found e.g. https://github.com/quartiq/bscan_spi_bitstreams

            # defines which flash proxy bitstream to use for which part
            flash_proxy = {
                "s7-50": "bscan_spi_xc7s50.bit",
                "s7-25": "bscan_spi_xc7s25.bit"
            }[self.device_variant]
            programmer = XC3SProg("jtaghs1_fast", flash_proxy_basename=flash_proxy)
            # search part where to find proxy bitsreams. If not specified
            # defaults to one of:
            #    "~/.migen", "/usr/local/share/migen", "/usr/share/migen",
            #    "~/.mlabs", "/usr/local/share/mlabs", "/usr/share/mlabs",
            #    "~/.litex", "/usr/local/share/litex", "/usr/share/litex"
            programmer.set_flash_proxy_dir("../../../../bin/bscan")
            return programmer

        # For Xilinx Vivado programmer
        # Vivado also uses flash proxy bitstreams but they are already shipped
        # with Vivado and are used automatically. Flash_part specifies the
        # exact part used in the Arty-S7 Rev. E
        elif self.programmer == "vivado":
            return VivadoProgrammer(flash_part="mt25ql128-spi-x1_x2_x4")

        # For OpenOCD
        elif self.programmer == "openocd":
            bscan_spi = "bscan_spi_xc7s50.bit" \
                    if "xc7s50" in self.device \
                    else "bscan_spi_xc7a25.bit"
            programmer = OpenOCD("openocd_xilinx.cfg", bscan_spi)
            programmer.set_flash_proxy_dir("../../../../bin/bscan")
            return programmer

        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request(
            self.default_clk_name, loose=True), self.default_clk_period)

