#!/usr/bin/env python3

# Show hBPF CPU state
# richard.prinz@min.at 2022

import sys
import traceback
import argparse
from litex import RemoteClient
from wb_lib import *

def main():
    parser = argparse.ArgumentParser(description="Show hBPF CPU status and registers")
    wb_add_std_args(parser)
    args = parser.parse_args()

    wb = wb_open(args.host, args.port, args.csr, parser=parser)

    print("Show hBPF status ...\n")

    status = wb.read(wb.regs.hbpf_csr_status.addr)
    print(f"Status: 0x{status:08x}")

    th = wb.read(wb.regs.hbpf_csr_ticks.addr)
    tl = wb.read(wb.regs.hbpf_csr_ticks.addr+4)
    print(f"Ticks:  0x{th:08x}{tl:08x}")

    print("Registers R0 - R10")
    addr = wb.regs.hbpf_csr_r0
    for i in range(11):
        rh = wb.read(wb.regs.hbpf_csr_r0.addr + (i * 8))
        rl = wb.read(wb.regs.hbpf_csr_r0.addr + (i * 8) + 4)
        print(f"R{str(i):2s}:    0x{rh:08x}{rl:08x}")

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

