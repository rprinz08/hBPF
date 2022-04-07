#!/bin/bash

# Use:
# ./arty.py --build --load
# lxserver --udp (for LiteScope over UDP)
# litescope_cli: will trigget an immediate capture!
# litescope_cli --help: list the available trigger option.
# litescope_cli --list: list the signals that can be used as triggers.
# litescope_cli -v main_count 128: trigger on count value == 128.
# litescope_cli -r litescopesoc_cpu_ibus_stb: trigger in ibus_stb rising edge
# For more information: https://github.com/enjoy-digital/litex/wiki/Use-LiteScope-To-Debug-A-SoC

litescope_cli --list

litescope_cli \
	--csv analyzer.csv \
	--dump dump.vcd \
	--offset 32 \
	-f ethmac_source_ready

# -r rx_cdc_source_source_valid

