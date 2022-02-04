#!/usr/bin/env python3

# Load binary into hBPF CPU program memory.
# richard.prinz@min.at 2022

import sys
import traceback
import argparse
import struct
from wb_lib import *

DEFAULT_PGM_FILE = "pgm_mem.bin"

def main():
    parser = argparse.ArgumentParser(description="Load binary into hBPF CPU program memory")
    wb_add_std_args(parser)
    parser.add_argument("--file", "-f", type=str, default=DEFAULT_PGM_FILE, required=False,
                        help=f"Binary file to load into target, defaults to ({DEFAULT_PGM_FILE})")
    args = parser.parse_args()

    wb_check_file(args.csr, parser=parser, rtc=1)
    wb_check_file(args.file, parser=parser, rtc=2)

    print(f"Load binary file ({args.file}) into hBPF CPU program memory ...")

    wb = wb_open(args.host, args.port, args.csr, parser=parser)

    with open(args.file, mode='rb') as file:
        data = file.read()
        len_bytes = len(data)
        len_words = len_bytes // 4
        pgm_mem = list(struct.unpack('>{}L'.format(len_words), data))
        wb_load(wb, wb.bases.hbpf_pgm_mem,
                pgm_mem,
                page_reg=wb.regs.hbpf_pgm_mem_page.addr,
                page_base=wb.bases.hbpf_pgm_mem,
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

