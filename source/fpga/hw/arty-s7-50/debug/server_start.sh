#!/bin/bash

S=`basename $0`
P=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PIDF="${P}/litex_server.pid"
LOGF="${P}/litex_server.log"
TARGET_TYPE="uart"

. ./wb_lib

if [ -f $PIDF ]; then
	echo "LiteX Server already running. Pidfile (${PIDF}) found."
    exit 1
fi

#if (( $EUID != 0 )); then
#    if whereis sudo &>/dev/null; then
#        sudo -H $0 $*
#        exit
#    else
#        echo "'sudo' utility not found."
#        echo "You will need to run this script as root."
#        exit
#    fi
#fi


# Uncomment the following lines to use 'litex_server' as Wishbone proxy
# (ensure that it is on your path)
DEBUG=--debug
if [ "$1x" == "fgx" ]; then
	lxserver \
		$DEBUG \
		--$TARGET_TYPE --uart-port=$TARGET_PORT --uart-baudrate=$TARGET_SPEED
else
	lxserver \
		$DEBUG \
		--$TARGET_TYPE --uart-port=$TARGET_PORT --uart-baudrate=$TARGET_SPEED \
		>$LOGF 2>&1 </dev/null &
	echo $! > $PIDF
fi


## Uncomment the following lines to use 'wishbone-tool' as Wishbone proxy.
#WBT="/usr/local/bin/wishbone-tool"
#if [ "$1x" == "fgx" ]; then
#	$WBT \
#		--bind-addr localhost \
#		--wishbone-port 1234 \
#		--serial $TARGET_PORT \
#		--baud $TARGET_SPEED \
#		--csr-csv csr.csv \
#		--server wishbone \
#		--hexdump \
#		--burst-length 8
#else
#	$WBT \
#		--bind-addr localhost \
#		--wishbone-port 1234 \
#		--serial $TARGET_PORT \
#		--baud $TARGET_SPEED \
#		--csr-csv csr.csv \
#		--server wishbone \
#		--hexdump \
#		--burst-length 8 \
#		>$LOGF 2>&1 </dev/null &
#	echo $! > $PIDF
#fi

