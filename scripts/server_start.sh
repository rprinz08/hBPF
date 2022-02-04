#!/bin/bash

# This script starts a Wishbone server background.
# richard.prinz@min.at 2022

S=`basename $0`
P=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PIDF="/tmp/litex_server.pid"
LOGF="/tmp/litex_server.log"
TARGET_TYPE="uart"
CONFIG="./.config"

_isRunningPid() {
    ps -o pid= "$1" 2>/dev/null | grep -x "$1" >/dev/null 2>&1
}

function usage() {
    cat << EOM

server_start.sh -c config -d -f

    -c config   Specify config file to read. If not specified, (.config)
                in current directory is assumed.
    -d          Enable debugging.
    -f          Start in foreground.
    -h          Shows this help screen.

EOM
}

if [ -f "$PIDF" ]; then
	PID=$(<"$PIDF")
    echo
	echo "Wishbone server with pid (${PID}) already running, pidfile (${PIDF}) found."
    echo
    exit 1
fi

#if (( $EUID != 0 )); then
#    if whereis sudo &>/dev/null; then
#        sudo -H $0 $*
#        exit
#    else
#        echo "'sudo' utility not found."
#        echo "You will need to run this script as root."
#        exit 1
#    fi
#fi

while getopts c:fdh flag
do
    case "${flag}" in
        u) config=${OPTARG};;
        f) foreground=1;;
        d) debug=1;;
        h) help=1;;
        *) usage && exit 1;;
    esac
done
config=${config:-$CONFIG}
if [ ! -f "${config}" ]; then
    usage
    echo "Unable to read config (${config}) - exit"
    exit 1
fi
source "$config"


# Uncomment the following lines to use 'lxserver' as Wishbone proxy
# (ensure that it is on your path)
DEBUG=
if [ ! -z $debug ]; then
    DEBUG=--debug
fi
if [ ! -z "$foreground" ]; then
    lxserver \
        $DEBUG \
        --$TARGET_TYPE --uart-port=$TARGET_PORT --uart-baudrate=$TARGET_SPEED
else
    lxserver \
        $DEBUG \
        --$TARGET_TYPE --uart-port=$TARGET_PORT --uart-baudrate=$TARGET_SPEED \
        >$LOGF 2>&1 </dev/null &
    srv_pid=$!
    sleep 1

    if ! _isRunningPid $srv_pid; then
        echo
        echo "LiteX lxserver did not start, check logfile (${LOGF})"
        echo
        tail -n 20 "$LOGF"
        echo
        exit 1
    fi

    echo
	echo "LiteX lxserver started with pid (${srv_pid})"
    echo

    echo $srv_pid > $PIDF
fi


# Uncomment the following lines to use 'wishbone-tool' as Wishbone proxy.
#WBT="/usr/local/bin/wishbone-tool"
WBT="/home/prinz/.cargo/bin/wishbone-tool"
#if [ ! -z "$foreground" ]; then
#   $WBT \
#       --bind-addr localhost \
#       --wishbone-port 1234 \
#       --serial $TARGET_PORT \
#       --baud $TARGET_SPEED \
#       --csr-csv csr.csv \
#       --server wishbone \
#       --hexdump \
#       --burst-length 8
#else
#   $WBT \
#       --bind-addr localhost \
#       --wishbone-port 1234 \
#       --serial $TARGET_PORT \
#       --baud $TARGET_SPEED \
#       --csr-csv csr.csv \
#       --server wishbone \
#       --hexdump \
#       --burst-length 8 \
#       >$LOGF 2>&1 </dev/null &
#   srv_pid=$!
#   sleep 1
#
#   if ! _isRunningPid $srv_pid; then
#       echo
#       echo "wishbone-tool did not start, check logfile (${LOGF})"
#       echo
#       tail -n 20 "$LOGF"
#       echo
#       exit 1
#   fi
#
#   echo
#   echo "wishbone-tool started with pid (${srv_pid}"
#   echo
#
#    echo $srv_pid > $PIDF
#fi

