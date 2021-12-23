#!/usr/bin/env python3

from litex import RemoteClient
from wb_lib import *

wb = RemoteClient(host="localhost", port=1234, csr_csv="csr.csv", debug=False)
wb.open()

dump(wb, wb.bases.hbpf_data_mem, 80)

wb.close()
