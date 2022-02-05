#!/bin/bash

# Stop a running Wishbone server.
# richard.prinz@min.at 2022

S=`basename $0`
P=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PIDF="/tmp/litex_server.pid"

_isRunningPid() {
    ps -o pid= "$1" 2>/dev/null | grep -e '^\s*'"$1" >/dev/null 2>&1
}

if [ ! -f "$PIDF" ]; then
    echo
    echo "Wishbone server NOT running"
    echo
    exit 1
fi

if (( $EUID != 0 )); then
    if whereis sudo &>/dev/null; then
        sudo $0 $*
        exit
    else
        echo "'sudo' utility not found."
        echo "You will need to run this script as root."
        exit 1
    fi
fi

PID=$(<"$PIDF")

echo
if _isRunningPid "$PID"; then
    #pkill -9 -P $PID
    kill -9 $PID
    echo "Wishbone server with pid (${PID}) stopped."
else
    echo "Wishbone server with pid (${PID}) not found, server not running."
fi
echo

rm -f $PIDF

