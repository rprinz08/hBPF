# hBPF Op-Codes

An overview of opcodes and the clock cycles they need:

|OpCodes|Cycles|%|
|---|---|---|
|34|2|36.95 %|
|1|4|1.08 %|
|12|5|13.04 %|
|24|6|26.08 %|
|21|>6|22.82 %|

The following tables lists hBPF opcodes and the clock cycles they need.

## ALU 64-Bit

|Asm|OpCode|Cycles|
|---|---|---|
|add imm|0x07|2|
|add reg|0x0f|2|
|sub imm|0x17|2|
|sub reg|0x1f|2|
|mul imm|0x27|2|
|mul reg|0x2f|2|
|div imm|0x37|69|
|div reg|0x3f|69|
|or imm|0x47|2|
|or reg|0x4f|2|
|and imm|0x57|2|
|and reg|0x5f|2|
|lsh imm|0x67|5|
|lsh reg|0x6f|5|
|rsh imm|0x77|5|
|rsh reg|0x7f|5|
|neg|0x87|2|
|mod imm|0x97|69|
|mod reg|0x9f|69|
|xor imm|0xa7|2|
|xor reg|0xaf|2|
|mov imm|0xb7|2|
|arsh imm|0xc7|5|
|arsh reg|0xcf|5|
|le16|0xd4|2|
|le32|0xd4|2|
|le64|0xd4|2|
|be16|0xdc|2|
|be32|0xdc|2|
|be64|0xdc|2|

## ALU 32-Bit

|Asm|OpCode|Cycles|
|---|---|---|
|add32 imm|0x04|2|
|add32 reg|0x0c|2|
|sub32 imm|0x14|2|
|sub32 reg|0x1c|2|
|mul32 imm|0x24|2|
|mul32 reg|0x2c|2|
|div32 imm|0x34|69|
|div32 reg|0x3c|69|
|or32 imm|0x44|2|
|or32 reg|0x4c|2|
|and32 imm|0x54|2|
|and32 reg|0x5c|2|
|lsh32 imm|0x64|5|
|lsh32 reg|0x6c|5|
|rsh32 imm|0x74|5|
|rsh32 reg|0x7c|5|
|neg32|0x84|2|
|mod32 imm|0x94|69|
|mod32 reg|0x9c|69|
|xor32 imm|0xa4|2|
|xor32 reg|0xac|2|
|mov32 imm|0xb4|2|
|arsh32 imm|0xc4|5|
|arsh32 reg|0xcc|5|

## Load X

Numbers in brackets are using data RAM without CSR support

|Asm|OpCode|Cycles|
|---|---|---|
|ldxb|0x71|15 (7)|
|ldxh|0x69|15 (7)|
|ldxw|0x61|15 (7)|
|ldxdw|0x79|15 (7)|

## Store X

Numbers in brackets are using data RAM without CSR support

|Asm|OpCode|Cycles|
|---|---|---|
|stxb|0x73|17 (9)|
|stxh|0x6b|18 (10)|
|stxw|0x63|20 (12)|
|stxdw|0x7b|24 (16)|

## Load

|Asm|OpCode|Cycles|
|---|---|---|
|lddw|0x18|4|

## Store

Numbers in brackets are using data RAM without CSR support

|Asm|OpCode|Cycles|
|---|---|---|
|stb|0x72|17 (9)|
|sth|0x6a|18 (10)|
|stw|0x62|20 (12)|
|stdw|0x7a|24 (16)|

## Jump

|Asm|OpCode|Cycles|
|---|---|---|
|ja|0x05|6|
|jeq imm|0x15|6|
|jeq reg|0x1d|6|
|jgt imm|0x25|6|
|jgt reg|0x2d|6|
|jge imm|0x35|6|
|jge reg|0x3d|6|
|jset imm|0x45|6|
|jset reg|0x4d|6|
|jne imm|0x55|6|
|jne reg|0x5d|6|
|jsgt imm|0x65|6|
|jsgt reg|0x6d|6|
|jsge imm|0x75|6|
|jsge reg|0x7d|6|
|call|0x85|\*|
|exit|0x95|6|
|jlt imm|0xa5|6|
|jlt reg|0xad|6|
|jle imm|0xb5|6|
|jle reg|0xbd|6|
|jslt imm|0xc5|6|
|jslt reg|0xcd|6|
|jsle imm|0xd5|6|
|jsle reg|0xdd|6|

\* clock cycles for `call` opcode depend on the implemented functionalities in the corresponding call handler but are at least 4 cycles.
