#!/bin/bash

S=`basename $0`
P="$( dirname "$( readlink -f "$0" )" )"
F="dummy"

clang \
	-target bpf \
	-Wall -O2 \
	-c "${F}.c" \
	-o "${F}.o"

#readelf -x .text "${F}.o"

llvm-objdump-6.0 \
	-disassemble \
	"${F}.o" > "${F}.lst"

llvm-objcopy-6.0 \
	-O binary \
	--only-keep=.text \
	"${F}.o" "${F}.bin"
chmod 644 "${F}.bin"

../../tools/dump.py "${F}.bin" >> "${F}.hex"

# or use xxd
#xxd -g 8 "${F}.bin"

