#!/usr/bin/env python3

# Displays a hardware targets identification string.
# richard.prinz@min.at 2022

import sys
import traceback
import argparse
from litex import RemoteClient
from wb_lib import *

def main():
    parser = argparse.ArgumentParser(description="Show hBPF CPU identifier")
    wb_add_std_args(parser)
    args = parser.parse_args()

    wb = wb_open(args.host, args.port, args.csr, parser=parser)

    print("Show hBPF identifier ...\n")

    fpga_id = ""
    for i in range(256):
        c = chr(wb.read(wb.bases.identifier_mem + 4*i) & 0xff)
        fpga_id += c
        if c == "\0":
            break
    print("FPGA ID: " + fpga_id)

    wb_close(wb)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("User Interrupted")
        sys.exit(2)
    except Exception as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    sys.exit(0)

