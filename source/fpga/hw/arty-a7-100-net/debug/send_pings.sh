#!/bin/bash

TARGET_IP4="10.0.10.50"
TARGET_IP6="2001:db8:10::50"

# This script sends ping echo requests for about ~30 seconds in various speeds.

echo "Test 1: Send pings every second"
ping -c 30 -i 1 "$TARGET_IP4"

echo "Test 2: Send pings every 0.5 seconds"
ping6 -c 60 -i 0.5 "$TARGET_IP6"

# everything under 0.200 needs root privileges under Linux
echo "Test 3: Send pings every 100ms"
sudo ping -c 300 -i 0.1 "$TARGET_IP4"

echo "Test 4: Send pings every 50ms"
sudo ping6 -c 600 -i 0.05 "$TARGET_IP6"

echo "Test 5: Send pings every 10ms"
sudo ping -c 2000 -i 0.01 "$TARGET_IP4"

echo "Test 6: Send pings every 5ms"
sudo ping6 -c 3000 -i 0.005 "$TARGET_IP6"

echo "Test 7: Send pings every 1ms"
sudo ping -c 3000 -i 0.001 "$TARGET_IP4"

