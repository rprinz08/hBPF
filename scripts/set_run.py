#!/usr/bin/env python3

# Start hwardware target.
# richard.prinz@min.at 2022

import sys
import traceback
import argparse
from litex import RemoteClient
from wb_lib import *

def main():
    parser = argparse.ArgumentParser(description="Start hBPF CPU")
    wb_add_std_args(parser)
    args = parser.parse_args()

    wb = wb_open(args.host, args.port, args.csr, parser=parser)

    print("Start target (set reset high) ...")

    wb.write(wb.regs.hbpf_csr_ctl.addr, 0x01)

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

