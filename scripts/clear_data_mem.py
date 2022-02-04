#!/usr/bin/env python3

# Clear a hBPF CPU data memory.
# richard.prinz@min.at 2022

import sys
import traceback
import argparse
from wb_lib import *

DEFAULT_DATA_MEM_SIZE = 2048

def main():
    parser = argparse.ArgumentParser(description="Clear hBPF CPU data memory")
    wb_add_std_args(parser)
    parser.add_argument("--size", "-s", type=int, default=DEFAULT_DATA_MEM_SIZE, required=False,
        help=f"Number of bytes to clear of data memory, defaults to ({DEFAULT_DATA_MEM_SIZE})")
    args = parser.parse_args()

    print(f"Clear ({args.size}) bytes of hBPF CPU data memory ...")

    wb = wb_open(args.host, args.port, args.csr, parser=parser)

    data = [0] * args.size
    wb_load(wb, wb.bases.hbpf_data_mem,
            data,
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

