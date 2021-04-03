#!/bin/bash

NAME="is_prime"
ASM="$NAME.asm"
BIN="$NAME.bin"
HEX="$NAME.hex"
#PY="$NAME.py"

# Assemble source
python3 ../../tools/ubpf/bin/ubpf-assembler "./$ASM" "./$BIN"

# Output python list
#echo "mem = [" > "$PY"
#cat "$BIN" | \
#       hexdump -v \
#               -e '1/1 "    0x"' \
#               -e '8/1 "%02X"",\n"' >> "$PY"
#echo "]" >> "$PY"

# Hex dump
../../tools/dump.py "$BIN" > "$HEX"

# or use xxd
#xxd -g 8 "$BIN"

