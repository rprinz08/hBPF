
# Used to connect to hardware under test. Uses serial link (but can use
# any other medium provided by lites.tools.remote) to communicate with
# Wishbone bridge on target HW.
class HW_Connect:

    def __init__(self, comm):
        self.comm = comm

    @property
    def debug(self):
        if self.comm is None:
            return False
        if hasattr(self.comm, "debug"):
            return self.debug
        return False

    @debug.setter
    def debug(self, value):
        if self.comm is None:
            return
        if hasattr(self.comm, "debug"):
            self.comm.debug = value

    @property
    def bases(self):
        if self.comm is None:
            return None
        if hasattr(self.comm, "bases"):
            return self.comm.bases
        return None

    @property
    def regs(self):
        if self.comm is None:
            return None
        if hasattr(self.comm, "regs"):
            return self.comm.regs
        return None

    @property
    def mems(self):
        if self.comm is None:
            return None
        if hasattr(self.comm, "mems"):
            return self.comm.mems
        return None

    def open(self):
        if self.comm is None:
            return
        self.comm.open()

    def close(self):
        if self.comm is None:
            return
        self.comm.close()

    def read(self, addr, length=1, burst="incr"):
        if self.comm is None:
            return []
        return self.comm.read(addr, length=length, burst=burst)

    def write(self, addr, data):
        if self.comm is None:
            return
        data = data if isinstance(data, list) else [data]
        self.comm.write(addr, data)

    def cpu_reset(self):
        self.write(self.regs.hbpf_csr_ctl.addr, 0x00)

    def cpu_run(self):
        self.write(self.regs.hbpf_csr_ctl.addr, 0x01)

    def cpu_get_status(self):
        data = self.read(self.regs.hbpf_csr_status.addr, length=1)
        return (data[0] & 0xff)

    def cpu_get_R0(self):
        data = self.read(self.regs.hbpf_csr_r0.addr, length=2)
        return (data[0] << 32 | data[1])

    def cpu_get_R6(self):
        data = self.read(self.regs.hbpf_csr_r6.addr, length=2)
        return (data[0] << 32 | data[1])

    def cpu_get_R7(self):
        data = self.read(self.regs.hbpf_csr_r7.addr, length=2)
        return (data[0] << 32 | data[1])

    def cpu_get_R8(self):
        data = self.read(self.regs.hbpf_csr_r8.addr, length=2)
        return (data[0] << 32 | data[1])

    def cpu_get_R9(self):
        data = self.read(self.regs.hbpf_csr_r9.addr, length=2)
        return (data[0] << 32 | data[1])

    def cpu_get_R10(self):
        data = self.read(self.regs.hbpf_csr_r10.addr, length=2)
        return (data[0] << 32 | data[1])

    def cpu_set_R1(self, value):
        self.write(self.regs.hbpf_csr_r1.addr, (value >> 32) & 0xffffffff)
        self.write(self.regs.hbpf_csr_r1.addr + 4, (value & 0xffffffff))

    def cpu_set_R2(self, value):
        self.write(self.regs.hbpf_csr_r2.addr, (value >> 32) & 0xffffffff)
        self.write(self.regs.hbpf_csr_r2.addr + 4, (value & 0xffffffff))

    def cpu_set_R3(self, value):
        self.write(self.regs.hbpf_csr_r3.addr, (value >> 32) & 0xffffffff)
        self.write(self.regs.hbpf_csr_r3.addr + 4, (value & 0xffffffff))

    def cpu_set_R4(self, value):
        self.write(self.regs.hbpf_csr_r4.addr, (value >> 32) & 0xffffffff)
        self.write(self.regs.hbpf_csr_r4.addr + 4, (value & 0xffffffff))

    def cpu_set_R5(self, value):
        self.write(self.regs.hbpf_csr_r5.addr, (value >> 32) & 0xffffffff)
        self.write(self.regs.hbpf_csr_r5.addr + 4, (value & 0xffffffff))

    def cpu_get_ticks(self):
        data = self.read(self.regs.hbpf_csr_ticks.addr, length=2)
        return (data[0] << 32 | data[1])

    def cpu_load_pgm(self, data):
        self.write(self.bases.hbpf_pgm_mem, data)

    def cpu_load_data(self, data):
        self.write(self.bases.hbpf_data_mem, data)
