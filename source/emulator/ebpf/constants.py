
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
