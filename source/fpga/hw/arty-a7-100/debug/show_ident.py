#!/usr/bin/env python3

from litex import RemoteClient

wb = RemoteClient(host="localhost", port=1234, csr_csv="csr.csv", debug=True)
wb.open()

# # #

# get identifier
fpga_id = ""
for i in range(256):
    c = chr(wb.read(wb.bases.identifier_mem + 4*i) & 0xff)
    fpga_id += c
    if c == "\0":
        break
print("fpga_id: " + fpga_id)

# # #

wb.close()

