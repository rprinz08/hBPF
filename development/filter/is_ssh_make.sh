#!/bin/bash

NAME="is_ssh"
ASM="$NAME.asm"
BIN="$NAME.bin"
HEX="$NAME.hex"
#PY="$NAME.py"

FILTER="tcp port 22"
#FILTER="tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)"


# Convert filter expression
../../tools/rust-cbpf/target/debug/c2e \
	-d \
	-o "$BIN" \
	"$FILTER" > "$ASM"


# Output python list
#echo "mem = [" > "$PY"
#cat "$BIN" | \
#	hexdump -v \
#		-e '1/1 "    0x"' \
#		-e '8/1 "%02X"",\n"' >> "$PY"
#echo "]" >> "$PY"


# Hex dump
../../tools/dump.py "$BIN" > "$HEX"

# or use xxd
#xxd -g 8 "$BIN"

