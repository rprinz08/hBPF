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
HOST_IP4="10.0.10.100"
HOST_IP6="2001:db8:10::100"
TARGET_IP4="10.0.10.50"
TARGET_IP6="2001:db8:10::50"
TARGET_MAC="00:18:3e:03:ab:53"

ip addr flush dev "$HOST_DEV"
ip -6 addr flush dev "$HOST_DEV"
ip link set "$HOST_DEV" down

# Set IP4
ip addr add "${HOST_IP4}/24" dev "$HOST_DEV"
ip neigh add "$TARGET_IP4" lladdr "$TARGET_MAC" nud permanent dev "$HOST_DEV"
ip neigh replace "$TARGET_IP4" lladdr "$TARGET_MAC" nud permanent dev "$HOST_DEV"

# Set IPv6
ip -6 addr add "${HOST_IP6}/64" dev "$HOST_DEV"
ip -6 neigh add "$TARGET_IP6" lladdr "$TARGET_MAC" nud permanent dev "$HOST_DEV"
ip -6 neigh replace "$TARGET_IP6" lladdr "$TARGET_MAC" nud permanent dev "$HOST_DEV"

ip link set "$HOST_DEV" up

