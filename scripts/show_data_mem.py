#!/usr/bin/env python3

# Shows a hardware targets data memory as hex dump.
# richard.prinz@min.at 2022

import sys
import traceback
import argparse
from litex import RemoteClient
from wb_lib import *

DEFAULT_DATA_MEM_SIZE = 2048

def main():
    parser = argparse.ArgumentParser(description="Dump hBPF CPU data memory")
    wb_add_std_args(parser)
    parser.add_argument("--size", "-s", type=int, default=DEFAULT_DATA_MEM_SIZE, required=False,
        help=f"How many bytes to dump (integer > 0), defaults to ({DEFAULT_DATA_MEM_SIZE})")
    args = parser.parse_args()

    if args.size < 0:
        parser.print_help()
        print("\nError: Size must be > 0\n")
        sys.exit(1)

    wb = wb_open(args.host, args.port, args.csr, parser=parser)

    print("Show hBPF data memory ...\n")

    wb_dump(wb, wb.bases.hbpf_data_mem,
            args.size, bytes_per_word=1,
            page_reg=wb.regs.hbpf_data_mem_page.addr,
            page_base=wb.bases.hbpf_data_mem,
            page_size=0x200)

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

