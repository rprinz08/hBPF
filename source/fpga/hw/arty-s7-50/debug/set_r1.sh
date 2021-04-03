#!/bin/bash

. ./wb_lib

echo "current ebpf R1 reg."
mem 0x0000180c
mem 0x00001810
echo

echo "ebpf R1 set"
mem 0x0000180c 0
mem 0x00001810 100
echo

echo "new ebpf R1 reg."
mem 0x0000180c
mem 0x00001810
echo

