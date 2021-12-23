
# Size of program memory (bytes)
MAX_PGM_MEM = 4096
# Size of context memory (bytes)
MAX_DATA_MEM = 2048
# Max stack size (bytes)
MAX_STACK = 512
# Number of registers
MAX_REGS = 11

# Default output indentation for some debug messages
IND = " " * 8

# Maximum values for various unsigned integers
MAX_UINT8  = 0xff
MAX_UINT16 = 0xffff
MAX_UINT32 = 0xffffffff
MAX_UINT64 = 0xffffffffffffffff

#  +----------------+--------+--------------------+
#  |   4 bits       |  1 bit |   3 bits           |
#  | operation code | source | instruction class  |
#  +----------------+--------+--------------------+
#  (MSB)                                      (LSB)

# OpCode Classes
OPC_LD    = 0x00    # load from immediate
OPC_LDX   = 0x01    # load from register
OPC_ST    = 0x02    # store immediate
OPC_STX   = 0x03    # store value from register
OPC_ALU   = 0x04    # 32 bits arithmetic operation
OPC_JMP   = 0x05    # jump
OPC_RES   = 0x06    # unused, reserved for future use
OPC_ALU64 = 0x07    # 64 bits arithmetic operation

# Operation codes (OPC_ALU or OPC_ALU64).
ALU_ADD  = 0x00     # addition
ALU_SUB  = 0x01     # subtraction
ALU_MUL  = 0x02     # multiplication
ALU_DIV  = 0x03     # division
ALU_OR   = 0x04     # or
ALU_AND  = 0x05     # and
ALU_LSH  = 0x06     # left shift
ALU_RSH  = 0x07     # right shift
ALU_NEG  = 0x08     # negation
ALU_MOD  = 0x09     # modulus
ALU_XOR  = 0x0a     # exclusive or
ALU_MOV  = 0x0b     # move
ALU_ARSH = 0x0c     # sign extending right shift
ALU_ENDC = 0x0d     # endianess conversion

#  +--------+--------+-------------------+
#  | 3 bits | 2 bits |   3 bits          |
#  |  mode  |  size  | instruction class |
#  +--------+--------+-------------------+
#  (MSB)                             (LSB)

# Load/Store Modes
LDST_IMM  = 0x00    # immediate value
LDST_ABS  = 0x01    # absolute
LDST_IND  = 0x02    # indirect
LDST_MEM  = 0x03    # load from / store to memory
          # 0x04    # reserved
          # 0x05    # reserved
LDST_XADD = 0x06    # exclusive add

# Sizes
LEN_W   = 0x00      # word (4 bytes)
LEN_H   = 0x01      # half-word (2 bytes)
LEN_B   = 0x02      # byte (1 byte)
LEN_DW  = 0x03      # double word (8 bytes)

EBPF_SIZE_W    = LEN_W  << 3 # 0x00
EBPF_SIZE_H    = LEN_H  << 3 # 0x08
EBPF_SIZE_B    = LEN_B  << 3 # 0x10
EBPF_SIZE_DW   = LEN_DW << 3 # 0x18

# Operation codes (OPC_JMP)
JMP_JA   = 0x00     # jump
JMP_JEQ  = 0x01     # jump if equal
JMP_JGT  = 0x02     # jump if greater than
JMP_JGE  = 0x03     # jump if greater or equal
JMP_JSET = 0x04     # jump if `src`& `reg`
JMP_JNE  = 0x05     # jump if not equal
JMP_JSGT = 0x06     # jump if greater than (signed)
JMP_JSGE = 0x07     # jump if greater or equal (signed)
JMP_CALL = 0x08     # helper function call
JMP_EXIT = 0x09     # return from program
JMP_JLT  = 0x0a     # jump if lower than
JMP_JLE  = 0x0b     # jump if lower ir equal
JMP_JSLT = 0x0c     # jump if lower than (signed)
JMP_JSLE = 0x0d     # jump if lower or equal (signed)

# Sources
JMP_K    = 0x00     # 32-bit immediate value
JMP_X    = 0x01     # `src` register

EBPF_SRC_IMM       = 0x00
EBPF_SRC_REG       = 0x08

EBPF_MODE_IMM      = 0x00
EBPF_MODE_MEM      = 0x60

EBPF_OP_ADD_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x00)
EBPF_OP_ADD_REG    = (OPC_ALU|EBPF_SRC_REG|0x00)
EBPF_OP_SUB_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x10)
EBPF_OP_SUB_REG    = (OPC_ALU|EBPF_SRC_REG|0x10)
EBPF_OP_MUL_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x20)
EBPF_OP_MUL_REG    = (OPC_ALU|EBPF_SRC_REG|0x20)
EBPF_OP_DIV_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x30)
EBPF_OP_DIV_REG    = (OPC_ALU|EBPF_SRC_REG|0x30)
EBPF_OP_OR_IMM     = (OPC_ALU|EBPF_SRC_IMM|0x40)
EBPF_OP_OR_REG     = (OPC_ALU|EBPF_SRC_REG|0x40)
EBPF_OP_AND_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x50)
EBPF_OP_AND_REG    = (OPC_ALU|EBPF_SRC_REG|0x50)
EBPF_OP_LSH_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x60)
EBPF_OP_LSH_REG    = (OPC_ALU|EBPF_SRC_REG|0x60)
EBPF_OP_RSH_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x70)
EBPF_OP_RSH_REG    = (OPC_ALU|EBPF_SRC_REG|0x70)
EBPF_OP_NEG        = (OPC_ALU|0x80)
EBPF_OP_MOD_IMM    = (OPC_ALU|EBPF_SRC_IMM|0x90)
EBPF_OP_MOD_REG    = (OPC_ALU|EBPF_SRC_REG|0x90)
EBPF_OP_XOR_IMM    = (OPC_ALU|EBPF_SRC_IMM|0xa0)
EBPF_OP_XOR_REG    = (OPC_ALU|EBPF_SRC_REG|0xa0)
EBPF_OP_MOV_IMM    = (OPC_ALU|EBPF_SRC_IMM|0xb0)
EBPF_OP_MOV_REG    = (OPC_ALU|EBPF_SRC_REG|0xb0)
EBPF_OP_ARSH_IMM   = (OPC_ALU|EBPF_SRC_IMM|0xc0)
EBPF_OP_ARSH_REG   = (OPC_ALU|EBPF_SRC_REG|0xc0)
EBPF_OP_LE         = (OPC_ALU|EBPF_SRC_IMM|0xd0)
EBPF_OP_BE         = (OPC_ALU|EBPF_SRC_REG|0xd0)

EBPF_OP_ADD64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x00)
EBPF_OP_ADD64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x00)
EBPF_OP_SUB64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x10)
EBPF_OP_SUB64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x10)
EBPF_OP_MUL64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x20)
EBPF_OP_MUL64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x20)
EBPF_OP_DIV64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x30)
EBPF_OP_DIV64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x30)
EBPF_OP_OR64_IMM   = (OPC_ALU64|EBPF_SRC_IMM|0x40)
EBPF_OP_OR64_REG   = (OPC_ALU64|EBPF_SRC_REG|0x40)
EBPF_OP_AND64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x50)
EBPF_OP_AND64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x50)
EBPF_OP_LSH64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x60)
EBPF_OP_LSH64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x60)
EBPF_OP_RSH64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x70)
EBPF_OP_RSH64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x70)
EBPF_OP_NEG64      = (OPC_ALU64|0x80)
EBPF_OP_MOD64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0x90)
EBPF_OP_MOD64_REG  = (OPC_ALU64|EBPF_SRC_REG|0x90)
EBPF_OP_XOR64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0xa0)
EBPF_OP_XOR64_REG  = (OPC_ALU64|EBPF_SRC_REG|0xa0)
EBPF_OP_MOV64_IMM  = (OPC_ALU64|EBPF_SRC_IMM|0xb0)
EBPF_OP_MOV64_REG  = (OPC_ALU64|EBPF_SRC_REG|0xb0)
EBPF_OP_ARSH64_IMM = (OPC_ALU64|EBPF_SRC_IMM|0xc0)
EBPF_OP_ARSH64_REG = (OPC_ALU64|EBPF_SRC_REG|0xc0)

EBPF_OP_LDXW       = (OPC_LDX|EBPF_MODE_MEM|EBPF_SIZE_W)
EBPF_OP_LDXH       = (OPC_LDX|EBPF_MODE_MEM|EBPF_SIZE_H)
EBPF_OP_LDXB       = (OPC_LDX|EBPF_MODE_MEM|EBPF_SIZE_B)
EBPF_OP_LDXDW      = (OPC_LDX|EBPF_MODE_MEM|EBPF_SIZE_DW)
EBPF_OP_STW        = (OPC_ST|EBPF_MODE_MEM|EBPF_SIZE_W)
EBPF_OP_STH        = (OPC_ST|EBPF_MODE_MEM|EBPF_SIZE_H)
EBPF_OP_STB        = (OPC_ST|EBPF_MODE_MEM|EBPF_SIZE_B)
EBPF_OP_STDW       = (OPC_ST|EBPF_MODE_MEM|EBPF_SIZE_DW)
EBPF_OP_STXW       = (OPC_STX|EBPF_MODE_MEM|EBPF_SIZE_W)
EBPF_OP_STXH       = (OPC_STX|EBPF_MODE_MEM|EBPF_SIZE_H)
EBPF_OP_STXB       = (OPC_STX|EBPF_MODE_MEM|EBPF_SIZE_B)
EBPF_OP_STXDW      = (OPC_STX|EBPF_MODE_MEM|EBPF_SIZE_DW)
EBPF_OP_LDDW       = (OPC_LD|EBPF_MODE_IMM|EBPF_SIZE_DW)

EBPF_OP_JA         = (OPC_JMP|0x00)
EBPF_OP_JEQ_IMM    = (OPC_JMP|EBPF_SRC_IMM|0x10)
EBPF_OP_JEQ_REG    = (OPC_JMP|EBPF_SRC_REG|0x10)
EBPF_OP_JGT_IMM    = (OPC_JMP|EBPF_SRC_IMM|0x20)
EBPF_OP_JGT_REG    = (OPC_JMP|EBPF_SRC_REG|0x20)
EBPF_OP_JGE_IMM    = (OPC_JMP|EBPF_SRC_IMM|0x30)
EBPF_OP_JGE_REG    = (OPC_JMP|EBPF_SRC_REG|0x30)
EBPF_OP_JSET_IMM   = (OPC_JMP|EBPF_SRC_IMM|0x40)
EBPF_OP_JSET_REG   = (OPC_JMP|EBPF_SRC_REG|0x40)
EBPF_OP_JNE_IMM    = (OPC_JMP|EBPF_SRC_IMM|0x50)
EBPF_OP_JNE_REG    = (OPC_JMP|EBPF_SRC_REG|0x50)
EBPF_OP_JSGT_IMM   = (OPC_JMP|EBPF_SRC_IMM|0x60)
EBPF_OP_JSGT_REG   = (OPC_JMP|EBPF_SRC_REG|0x60)
EBPF_OP_JSGE_IMM   = (OPC_JMP|EBPF_SRC_IMM|0x70)
EBPF_OP_JSGE_REG   = (OPC_JMP|EBPF_SRC_REG|0x70)
EBPF_OP_CALL       = (OPC_JMP|0x80)
EBPF_OP_EXIT       = (OPC_JMP|0x90)
EBPF_OP_JLT_IMM    = (OPC_JMP|EBPF_SRC_IMM|0xa0)
EBPF_OP_JLT_REG    = (OPC_JMP|EBPF_SRC_REG|0xa0)
EBPF_OP_JLE_IMM    = (OPC_JMP|EBPF_SRC_IMM|0xb0)
EBPF_OP_JLE_REG    = (OPC_JMP|EBPF_SRC_REG|0xb0)
EBPF_OP_JSLT_IMM   = (OPC_JMP|EBPF_SRC_IMM|0xc0)
EBPF_OP_JSLT_REG   = (OPC_JMP|EBPF_SRC_REG|0xc0)
EBPF_OP_JSLE_IMM   = (OPC_JMP|EBPF_SRC_IMM|0xd0)
EBPF_OP_JSLE_REG   = (OPC_JMP|EBPF_SRC_REG|0xd0)
