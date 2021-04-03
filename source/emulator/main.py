#!/usr/bin/python3

import sys
sys.path.append('..')
import os
import argparse
import struct
from emulator.ebpf.vm import *
#from scapy.all import *


def load_program(file_name):
    # Read 8 byte (64 bit) unsigned integers (expect big endian for the
    # moment) from ebpf binary compiled file.
    data = b""

    # Some sanity checks.
    sr = os.stat(file_name)
    if sr.st_size > MAX_PGM_MEM:
        raise Exception("Program size ({} bytes) larger than "
            "allowed size ({} bytes)".format(sr.st_size, MAX_PGM_MEM))

    if (sr.st_size % 8) != 0:
        raise Exception("Program size ({}) must be an "
            "integer divisible by 8".format(sr.st_size))

    # Read the whole file at once into memory.
    with open(file_name, "rb") as binary_file:
        data = binary_file.read()

    # Create list of unsigned 8 byte integers from binary file content.
    fmt = ">{}Q".format(len(data) // 8)
    return list(struct.unpack(fmt, data))


def main():
    try:
        bo = "{}-endian".format(sys.byteorder)
        parser = argparse.ArgumentParser(description="ebpf Python3 VM (" + bo + ")")
        parser.add_argument('--program', default='ebpf.bin',
                              help='Binary file with compiled ebpf bytecode')
        parser.add_argument('--data', default=None,
                              help='Binary file with loaded into data memory')
        parser.add_argument('--step', action='store_true',
                              help='Single step through program')
        args = parser.parse_args()

        # Load program into memory
        mem = load_program(args.program)

        data_mem = None

        # Data memory can also be filled with sample packets created
        # with scapy
        # Prepare sample IP4 or IPv6 network packet for data RAM.

        # packet_ipv4 = \
        #     Ether(src='00:01:bb:47:11', dst='00:00:11:11:11') / \
        #     IP(src='192.168.1.10', dst='10.16.77.66') / \
        #     UDP(dport=22)
        # data_mem = bytearray(bytes(packet_ipv4))

        # packet_ipv6 = \
        #     Ether(src='00:01:bb:47:11', dst='00:00:11:11:11') / \
        #     IPv6(src='2001:db8:1000::1', dst='2001:db8:2000::2') / \
        #     TCP(dport=22,flags='S')
        # data_mem = bytearray(bytes(packet_ipv6))

        # Load data memory
        if args.data is not None:
            # with open(args.data, "wb") as file:
            #     file.write(data_mem)
            with open(args.data, "rb") as binary_file:
                data_mem = binary_file.read()


        # Instantiate VM
        vm = VM(mem=mem, debug=True, swap_endian=True)
        if data_mem is not None:
            vm.data_mem = data_mem

        if args.step:
            while vm.exit_val is None:
                vm.step()
                input("> ")
        else:
            vm.start()

        print("Exit value: 0x{:016x}".format(vm.exit_val))

        return 0

    except KeyboardInterrupt:
        pass
    except Exception as err:
        print(err, file=sys.stderr)
        print("For help use --help option.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
