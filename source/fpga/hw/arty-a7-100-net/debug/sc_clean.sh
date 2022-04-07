#!/bin/bash

if (( $EUID != 0 )); then
    if whereis sudo &>/dev/null; then
        sudo -H $0 $*
        exit
    else
        echo "'sudo' utility not found."
        echo "You will need to run this script as root."
        exit 1
    fi
fi

# Change parameters to match device connected to Arty-A7
HOST_DEV="enx0050b61972e1"
TARGET_IP4="10.0.10.50"
TARGET_IP6="2001:db8:10::50"
TARGET_MAC="00:18:3e:03:ab:53"

sudo ip neigh del "$TARGET_IP4" lladdr "$TARGET_MAC" dev "$HOST_DEV"
ip addr flush dev "$HOST_DEV"

sudo ip -6 neigh del "$TARGET_IP6" lladdr "$TARGET_MAC" dev "$HOST_DEV"
ip -6 addr flush dev "$HOST_DEV"

ip link set "$HOST_DEV" down

