# hBPF Op-Codes

An overview of opcodes and the clock cycles they need:

|Ticks|OpCodes|Pct%|
|-----|-------|----|
|1|35|38.46153846153846|
|2|24|26.373626373626372|
|4|12|13.186813186813186|
|14|4|4.395604395604396|
|16|2|2.197802197802198|
|17|2|2.197802197802198|
|19|2|2.197802197802198|
|23|2|2.197802197802198|
|68|8|8.791208791208792|

The following tables lists hBPF opcodes and the clock cycles they need.

## ALU 64-Bit

|Asm|OpCode|Cycles|
|---|---|---|
|add imm|0x07|1|
|add reg|0x0f|1|
|sub imm|0x17|1|
|sub reg|0x1f|1|
|mul imm|0x27|1|
|mul reg|0x2f|1|
|div imm|0x37|68|
|div reg|0x3f|68|
|or imm|0x47|1|
|or reg|0x4f|1|
|and imm|0x57|1|
|and reg|0x5f|1|
|lsh imm|0x67|4|
|lsh reg|0x6f|4|
|rsh imm|0x77|4|
|rsh reg|0x7f|4|
|neg|0x87|1|
|mod imm|0x97|68|
|mod reg|0x9f|68|
|xor imm|0xa7|1|
|xor reg|0xaf|1|
|mov imm|0xb7|1|
|arsh imm|0xc7|4|
|arsh reg|0xcf|4|
|le16|0xd4|1|
|le32|0xd4|1|
|le64|0xd4|1|
|be16|0xdc|1|
|be32|0xdc|1|
|be64|0xdc|1|

## ALU 32-Bit

|Asm|OpCode|Cycles|
|---|---|---|
|add32 imm|0x04|1|
|add32 reg|0x0c|1|
|sub32 imm|0x14|1|
|sub32 reg|0x1c|1|
|mul32 imm|0x24|1|
|mul32 reg|0x2c|1|
|div32 imm|0x34|68|
|div32 reg|0x3c|68|
|or32 imm|0x44|1|
|or32 reg|0x4c|1|
|and32 imm|0x54|1|
|and32 reg|0x5c|1|
|lsh32 imm|0x64|4|
|lsh32 reg|0x6c|4|
|rsh32 imm|0x74|4|
|rsh32 reg|0x7c|4|
|neg32|0x84|1|
|mod32 imm|0x94|68|
|mod32 reg|0x9c|68|
|xor32 imm|0xa4|1|
|xor32 reg|0xac|1|
|mov32 imm|0xb4|1|
|arsh32 imm|0xc4|4|
|arsh32 reg|0xcc|4|

## Load X

Numbers in brackets are using data RAM without CSR support

|Asm|OpCode|Cycles|
|---|---|---|
|ldxb|0x71|14 (6)|
|ldxh|0x69|14 (6)|
|ldxw|0x61|14 (6)|
|ldxdw|0x79|14 (6)|

## Store X

Numbers in brackets are using data RAM without CSR support

|Asm|OpCode|Cycles|
|---|---|---|
|stxb|0x73|16 (8)|
|stxh|0x6b|17 (9)|
|stxw|0x63|19 (11)|
|stxdw|0x7b|23 (15)|

## Load

|Asm|OpCode|Cycles|
|---|---|---|
|lddw|0x18|2|

## Store

Numbers in brackets are using data RAM without CSR support

|Asm|OpCode|Cycles|
|---|---|---|
|stb|0x72|16 (8)|
|sth|0x6a|17 (9)|
|stw|0x62|19 (11)|
|stdw|0x7a|23 (15)|

## Jump

|Asm|OpCode|Cycles|
|---|---|---|
|ja|0x05|2|
|jeq imm|0x15|2|
|jeq reg|0x1d|2|
|jgt imm|0x25|2|
|jgt reg|0x2d|2|
|jge imm|0x35|2|
|jge reg|0x3d|2|
|jset imm|0x45|2|
|jset reg|0x4d|2|
|jne imm|0x55|2|
|jne reg|0x5d|2|
|jsgt imm|0x65|2|
|jsgt reg|0x6d|2|
|jsge imm|0x75|2|
|jsge reg|0x7d|2|
|call|0x85|\*|
|exit|0x95|1|
|jlt imm|0xa5|2|
|jlt reg|0xad|2|
|jle imm|0xb5|2|
|jle reg|0xbd|2|
|jslt imm|0xc5|2|
|jslt reg|0xcd|2|
|jsle imm|0xd5|2|
|jsle reg|0xdd|2|

\* clock cycles for `call` opcode depend on the implemented functionalities in the corresponding call handler but are at least 2 cycles.
