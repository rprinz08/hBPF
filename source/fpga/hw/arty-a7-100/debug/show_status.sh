#!/bin/bash

. ./wb_lib

echo "hbpf status"
mem hbpf_csr_status
echo

echo "hbpf ticks"
mem 0x0000005c
mem 0x00000060
echo

echo "hbpf R0"
mem 0x00000004
mem 0x00000008
echo

regs_base=0x00000004
for (( i=1; i<=10; i++ )); do
	echo "R${i}"
	mem $(( regs_base + ( 8 * i ) ))
	mem $(( regs_base + ( 8 * i ) + 4 ))
done
echo

