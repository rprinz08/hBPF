#!/bin/bash

P=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
S="${P}/$(basename $0)"
KEEP_GENERATED_FILES="no"

XIL_BASE=/opt/Xilinx
XIL_VER=2018.2

SDK_HOME="${XIL_BASE}/SDK/${XIL_VER}"
SDK_SETTINGS="${SDK_HOME}/settings64.sh"

VIVADO_HOME="${XIL_BASE}/Vivado/${XIL_VER}"
VIVADO_SETTINGS="${VIVADO_HOME}/settings64.sh"
VIVADO="${VIVADO_HOME}/bin/vivado"

FPGA_TARGET="ARM*#1"
FPGA_INIT="zynq"

BURN="${P}/burn.sh"

VIVADO_PRJ_PATH="${P}/../build"
BITSTREAM="${VIVADO_PRJ_PATH}/gateware/top.bit"
XSDB_INI="${P}/xsdb.ini"

# check if vivado project exists
if [ ! -d "${VIVADO_PRJ_PATH}" ]; then
	echo "Vivado project not found; create it first!"
	exit 1
fi

# check if fpga bitstream exists
if [ ! -f "${BITSTREAM}" ]; then
	echo "FPGA bitstream not found (${BITSTREAM}); build it first!"
	exit 1
fi

# check xilinx SDK settings
if [ ! -f "${SDK_SETTINGS}" ]; then
	echo "Xilinx SDK settings (${SDK_SETTINGS}) not found!"
	exit 1
fi
source "${SDK_SETTINGS}"

# create programming parameter file
cat << EOM > "${XSDB_INI}"
connect
targets -filter {name =~ "${FPGA_TARGET}"} -set
fpga -f ${BITSTREAM}

source ps7_init.tcl
ps7_init
ps7_post_config
exit
EOM

# program fpga
cat << EOM > "${BURN}"
#!/bin/bash
source "${SDK_SETTINGS}"
xsdb -interactive
EOM
chmod 755 "${BURN}"
"${BURN}"

# remove parameter file
if [ "${KEEP_GENERATED_FILES}" != "yes" ]; then
	rm -f "${BURN}"
	rm -f "${XSDB_INI}"
fi

