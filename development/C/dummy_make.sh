#!/bin/bash

S=`basename $0`
P="$( dirname "$( readlink -f "$0" )" )"
F="dummy"
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

../../tools/dump.py "${F}.bin" >> "${F}.hex"

# or use xxd
#xxd -g 8 "${F}.bin"

