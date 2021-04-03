from colorama import Fore, Back, Style
from emulator.ebpf.constants import *


class RegisterDescriptor:
    def __init__(self, reg):
        self._reg = reg

    def __get__(self, instance, owner):
        if instance is not None:
            return instance.regs[self._reg]

    def __set__(self, instance, value):
        if instance is not None:
            instance.regs[self._reg] = value


# https://python-3-patterns-idioms-test.readthedocs.io/en/latest/PythonDecorators.html

# def disassemble(f):
#     def new_f(*args, **kwargs):
#         print("Entering", f.__name__)
#         f(*args, **kwargs)
#         print("Exited", f.__name__)
#     new_f.__name__ = f.__name__
#     return new_f


def disassemble(type, name):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            cls = args[0]
            if cls.vm.debug:
                n = name

                if type == "ALU":
                    cls, op_opr, op_src, insn = args
                    n = n + ("" if insn.op_class == OPC_ALU64 else "32")
                    if n.startswith("neg"):
                        print("{}{}{:8s} r{}".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, insn.destination))
                    elif n.startswith("endc"):
                        n = (op_src == 1 and "be" or "le") + str(insn.immediate)
                        print("{}{}{:8s} r{}".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, insn.destination))
                    elif op_src == 0:
                        print("{}{}{:8s} r{}, 0x{:016x}".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, insn.destination, insn.immediate))
                    else:
                        print("{}{}{:8s} r{}, r{}".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, insn.destination, insn.source))

                elif type == "JMP":
                    cls, op_opr, op_src, insn = args
                    if op_opr == JMP_JA:
                        print("{}{}{:8s} +0x{:016x}".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, insn.offset))
                    elif op_opr == JMP_CALL:
                        print("{}{}{:8s} 0x{:016x}".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, insn.immediate))
                    elif op_opr == JMP_EXIT:
                        print("{}{}{:8s} 0x{:016x}".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, cls.vm.r0))
                    else:
                        if op_src == 0:
                            print("{}{}{:8s} r{}, 0x{:016x}, 0x{:016x}".format(
                                Fore.YELLOW + Style.BRIGHT, IND,
                                n, insn.destination, insn.immediate, insn.offset))
                        else:
                            print("{}{}{:8s} r{}, r{}, 0x{:016x}".format(
                                Fore.YELLOW + Style.BRIGHT, IND,
                                n, insn.destination, insn.source, insn.offset))

                elif type == "LD":
                    cls, op_mod, op_len, insn = args
                    if op_mod == LDST_IMM:
                        print("{}{}{:8s} r{}, [0x{:x}]".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n, insn.destination, insn.immediate))
                    elif op_mod == LDST_ABS:
                        print("{}{}{:8s} r0, [0x{:x}]".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n + ["w", "h", "b", "dw"][op_len],
                            insn.immediate))
                    elif op_mod == LDST_IND:
                        print("{}{}OPL IND".format(
                            Fore.YELLOW + Style.BRIGHT, IND))
                    elif op_mod == LDST_MEM:
                        print("{}{}{:8s} r{}, [r{}+0x{:x}]".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            n + ["w", "h", "b", "dw"][op_len],
                            insn.destination, insn.source, insn.offset))
                    elif op_mod == LDST_XADD:
                        print("{}{}OPL XADD".format(
                            Fore.YELLOW + Style.BRIGHT, IND))

                elif type == "ST":
                    cls, op_mod, op_len, insn = args
                    if op_mod == LDST_IMM:
                        print("{}{}OPS IMM".format(
                            Fore.YELLOW + Style.BRIGHT, IND))
                    elif op_mod == LDST_ABS:
                        print("{}{}OPS ABS".format(
                            Fore.YELLOW + Style.BRIGHT, IND))
                    elif op_mod == LDST_IND:
                        print("{}{}OPS IND".format(
                            Fore.YELLOW + Style.BRIGHT, IND))
                    elif op_mod == LDST_MEM:
                        print("{}{}{:8s} r{}, [r{}+0x{:x}]".format(
                            Fore.YELLOW + Style.BRIGHT, IND,
                            "stx" + ["w", "h", "b", "dw"][op_len],
                            insn.destination, insn.source, insn.offset))
                    elif op_mod == LDST_XADD:
                        print("OPS XADD".format(
                            Fore.YELLOW + Style.BRIGHT, IND))

            return f(*args, **kwargs)
        return wrapped_f
    return wrap


def print_hex_list(lst):
    print("[{}]".format(", ".join(hex(x) for x in lst)))


def arit_rshift(value, n, sign_bit_pos=31):
    s = value & (1 << sign_bit_pos)
    for i in range(0, n):
        value >>= 1
        value |= s
    return value


def int8(value):
    return value & 0x7f if (value & 0x80) == 0 \
        else -((0xff - value) + 1)

def uint8(value):
    return value & 0xff

def int16(value):
    return value & 0x7fff if (value & 0x8000) == 0 \
        else -((0xffff - value) + 1)

def uint16(value):
    return value & 0xffff

def int32(value):
    return value & 0x7fffffff if (value & 0x80000000) == 0 \
        else -((0xffffffff - value) + 1)

def uint32(value):
    return value & 0xffffffff

def int64(value):
    return value & 0x7fffffffffffffff if (value & 0x8000000000000000) == 0 \
        else -((0xffffffffffffffff - value) + 1)

def uint64(value):
    return value & 0xffffffffffffffff
