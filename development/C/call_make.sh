#!/bin/bash

S=`basename $0`
P="$( dirname "$( readlink -f "$0" )" )"
F="call"
objdump="llvm-objdump"
objcopy="llvm-objcopy"

clang \
	-target bpf \
	-Wall -O2 \
	-c "${F}.c" \
	-o "${F}.o"

#readelf -x .text "${F}.o"

$objdump \
	--disassemble \
	"${F}.o" > "${F}.lst"

$objcopy \
	-O binary \
	--only-section=.text \
	"${F}.o" "${F}.bin"
chmod 644 "${F}.bin"

#cat "${F}.bin" | \
#        hexdump -v \
#                -e '1/1 "0x"' \
#                -e '8/1 "%02X""\n"'
#echo

../../tools/dump.py "${F}.bin" >> "${F}.hex"

# or use xxd
#xxd -g 8 "${F}.bin"

