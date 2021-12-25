#!/bin/bash

S=`basename $0`
P=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PIDF="${P}/litex_server.pid"

if [ ! -f $PIDF ]; then
    echo "LiteX server NOT running"
    exit 1
fi

if (( $EUID != 0 )); then
    if whereis sudo &>/dev/null; then
        sudo $0 $*
        exit
    else
        echo "'sudo' utility not found."
        echo "You will need to run this script as root."
        exit
    fi
fi

PID=$(<"$PIDF")
#pkill -9 -P $PID
kill -9 $PID

rm -f $PIDF

