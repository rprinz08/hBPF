import sys
sys.path.insert(0, '..')

from migen import *
from litex.soc.interconnect.csr import *
from fpga.constants import *
from fpga.ram import *
from fpga.ram64 import *
from fpga.math.divide import Divider
from fpga.math.shift import Shifter


class CPU(Module, AutoCSR):

    MAX_REGS = 11
    MAX_PGM_WORDS = 4096
    MAX_DATA_WORDS = 2048

    # CPU states.
    STATE_OP_FETCH = 0
    STATE_DECODE = 1
    STATE_DATA_FETCH = 2
    STATE_DIV_PENDING = 3
    STATE_CALL_PENDING = 4
    STATE_HALT = 5

    def __init__(self,
            pgm_init=None, max_pgm_words=MAX_PGM_WORDS,
            data_init=None, max_data_words=MAX_DATA_WORDS,
            debug=False, call_handler=None, simulation=False):

        # Direct CPU status and control signals.
        self.reset_n = reset_n = Signal()
        self.error = error = Signal()
        self.halt = halt = Signal()
        self.ticks = ticks = Signal(64)
        self.debug = Signal()

        # CSR registers
        # Status register of CPU including all status flags:
        # bit 0 - reset_n
        #     1 - halt
        #     2 - error
        #     7 - debug
        self.csr_status = csr_status = CSRStatus(8)

        # Result register R0.
        self.csr_r0 = csr_r0 = CSRStatus(64)

        # Input registers.
        self.csr_r1 = csr_r1 = CSRStorage(64)
        self.csr_r2 = csr_r2 = CSRStorage(64)
        self.csr_r3 = csr_r3 = CSRStorage(64)
        self.csr_r4 = csr_r4 = CSRStorage(64)
        self.csr_r5 = csr_r5 = CSRStorage(64)

        # Output registers.
        self.csr_r6 = csr_r6 = CSRStatus(64)
        self.csr_r7 = csr_r7 = CSRStatus(64)
        self.csr_r8 = csr_r8 = CSRStatus(64)
        self.csr_r9 = csr_r9 = CSRStatus(64)
        self.csr_r10 = csr_r10 = CSRStatus(64)

        # Clock ticks between reset going high and halt going high.
        self.csr_ticks = csr_ticks = CSRStatus(64)

        # Control register for CPU.
        # bit 0 - reset_n
        self.csr_ctl = csr_ctl = CSRStorage(8)

        # Create register bank with direct accessors for each register in bank.
        self.regs = regs = Array(Signal(64) for i in range(self.MAX_REGS))
        for i in range(self.MAX_REGS):
            setattr(self, "r{}".format(i), regs[i])

        # Call handler
        if isinstance(call_handler, Module):
            self.submodules.call_handler = call_handler

        # # #

        reset_n_int = Signal()
        state = Signal(self.STATE_HALT.bit_length())
        data_ack = Signal()
        div64_ack = Signal()

        # Represents an ebpf instruction.
        # See https://www.kernel.org/doc/Documentation/networking/filter.txt
        # for more information.

        # Layout of an ebpf instruction. VM internally works with
        # little-endian byte-order.

        # MSB                                                        LSB
        # +------------------------+----------------+----+----+--------+
        # |immediate               |offset          |src |dst |opcode  |
        # +------------------------+----------------+----+----+--------+
        # 63                     32               16   12    8        0

        instruction = Signal(64)
        opcode = Signal(8)
        opclass = Signal(3)
        dst = Signal(4)
        src = Signal(4)
        offset = Signal(16)
        offset_s = Signal((16, True))
        immediate = Signal(32)
        immediate_s = Signal((32, True))
        keep_op = Signal(8)
        keep_dst = Signal(4)

        src_reg = Signal(64)
        src_reg_s = Signal((64, True))
        src_reg_32 = Signal(32)
        src_reg_32_s = Signal((32, True))

        dst_reg = Signal(64)
        dst_reg_s = Signal((64, True))
        dst_reg_32 = Signal(32)
        dst_reg_32_s = Signal((32, True))

        ip = Signal(32)
        ip_next = Signal(32)

        # hbpf program memory.
        self.submodules.pgm = pgm = RAM64(
                                max_words=max_pgm_words,
                                init=pgm_init,
                                debug=debug)

        # hbpf data memory (e.g packet data).
        self.submodules.data = data = RAM(max_words=max_data_words,
                                init=data_init, write_capable=True,
                                csr_access=True,
                                debug=debug)

        # Math divider for 32 and 64 bit.
        self.submodules.div64 = div64 = Divider(data_width=64)

        # Logic and arithmetic shifter.
        self.submodules.arsh64 = arsh64 = Shifter(data_width=64)

        #region Combinatorial logic.
        self.comb += [
            # Set/get CPU CSR status registers.
            csr_status.status[0].eq(reset_n_int),
            csr_status.status[1].eq(halt),
            csr_status.status[2].eq(error),
            csr_status.status[7].eq(self.debug),
            csr_r0.status.eq(self.r0),

            # r1 - r5 are in sync block

            csr_r6.status.eq(self.r6),
            csr_r7.status.eq(self.r7),
            csr_r8.status.eq(self.r8),
            csr_r9.status.eq(self.r9),
            csr_r10.status.eq(self.r10),

            csr_ticks.status.eq(ticks),
            reset_n_int.eq(reset_n | csr_ctl.storage[0]),

            div64.reset_n.eq(reset_n_int),

            # MSB                                                        LSB
            # | Byte 8 | Byte 7  | Byte 5-6       | Byte 1-4               |
            # +--------+----+----+----------------+------------------------+
            # |opcode  | src| dst|          offset|               immediate|
            # +--------+----+----+----------------+------------------------+
            # 63     56   52   48               32                        0

            immediate.eq(Cat(instruction[24:32],
                         instruction[16:24],
                         instruction[8:16],
                         instruction[0:8])),
            If(keep_op == 0,
                offset.eq(Cat(instruction[40:48],
                          instruction[32:40])),
                src.eq(instruction[52:56]),
                dst.eq(instruction[48:52]),
                opcode.eq(instruction[56:64])
            ).Else(
                opcode.eq(keep_op),
                dst.eq(keep_dst)
            ),
            opclass.eq(opcode[0:3]),

            offset_s.eq(offset),
            immediate_s.eq(immediate),

            src_reg.eq(regs[src]),
            src_reg_s.eq(regs[src]),
            src_reg_32.eq(regs[src]),
            src_reg_32_s.eq(regs[src]),

            dst_reg.eq(regs[dst]),
            dst_reg_s.eq(regs[dst]),
            dst_reg_32.eq(regs[dst]),
            dst_reg_32_s.eq(regs[dst]),

            pgm.adr.eq(ip_next),
        ]
        #endregion

        #region CALL_HANDLER
        # If a call handler is provided for this CPU instance ...
        call_handler_actions = [
            error.eq(1),
            halt.eq(1)
        ]
        call_handler_state = []
        if hasattr(self, 'call_handler'):
            call_handler_actions = [
                self.call_handler.r1.eq(self.r1),
                self.call_handler.r2.eq(self.r2),
                self.call_handler.r3.eq(self.r3),
                self.call_handler.r4.eq(self.r4),
                self.call_handler.r5.eq(self.r5),
                self.call_handler.func.eq(immediate),
                self.call_handler.stb.eq(1),
                state.eq(self.STATE_CALL_PENDING)
            ]
            call_handler_state = [
                If(self.call_handler.ack,
                    self.call_handler.stb.eq(0),
                    If(self.call_handler.err,
                        error.eq(1),
                        halt.eq(1)
                    ).Else(
                        self.r0.eq(self.call_handler.ret),
                        state.eq(self.STATE_DECODE),
                        ip_next.eq(ip_next + 1),
                        ip.eq(ip_next),
                        instruction.eq(pgm.dat_r),
                    )
                )
            ]
        #endregion

        #region Simulation only
        if simulation:
            self.state = state
            self.opcode = opcode
            self.instruction = instruction
            self.ip = Signal(32)
            self.comb += [
                self.ip.eq(ip),
            ]
        #endregion

        # Sync logic.
        self.sync += [

            # Reset state.
            If(~reset_n_int,
                ticks.eq(0),
                error.eq(0),
                halt.eq(0),

                ip_next.eq(0),
                ip.eq(0),
                instruction.eq(pgm.dat_r),
                state.eq(self.STATE_OP_FETCH),

                keep_op.eq(0),
                keep_dst.eq(0),

                self.r0.eq(0),

                # r1 - r5 are used as input arguments and thus are not cleared
                # but set from CSR
                self.r1.eq(csr_r1.storage),
                self.r2.eq(csr_r2.storage),
                self.r3.eq(csr_r3.storage),
                self.r4.eq(csr_r4.storage),
                self.r5.eq(csr_r5.storage),

                self.r6.eq(0), self.r7.eq(0),
                self.r8.eq(0), self.r9.eq(0),

            # If halt signal high, stop CPU.
            ).Elif(halt,
                state.eq(self.STATE_HALT),

            # Check invalid source register.
            ).Elif(src >= self.MAX_REGS,
                error.eq(1),
                halt.eq(1)

            # Check invalid destination register.
            ).Elif(dst >= self.MAX_REGS,
                error.eq(1),
                halt.eq(1)

            # Check for incomplete LDDW instruction.
            ).Elif((keep_op & instruction[56:64]) != 0,
                error.eq(1),
                halt.eq(1)

            # Process opcodes.
            ).Else(
                ticks.eq(ticks + 1),

                csr_r1.storage.eq(self.r1),
                csr_r2.storage.eq(self.r2),
                csr_r3.storage.eq(self.r3),
                csr_r4.storage.eq(self.r4),
                csr_r5.storage.eq(self.r5),

                Case(state, {
                    #region STATE_OP_FETCH
                    self.STATE_OP_FETCH: [
                        ip_next.eq(ip_next + 1),
                        ip.eq(ip_next),
                        instruction.eq(pgm.dat_r),
                        state.eq(self.STATE_DECODE)
                    ],
                    #endregion

                    #region STATE_DECODE
                    # Decode instructions.
                    self.STATE_DECODE: [
                        keep_op.eq(0),

                        Case(opclass, {
                            #region OPC_LD
                            OPC_LD: [
                                Case(opcode, {
                                    #region OP_LDDW
                                    EBPF_OP_LDDW: [
                                        If(keep_op == 0,
                                            regs[dst].eq(immediate),
                                            keep_op.eq(opcode),
                                            keep_dst.eq(dst)
                                        ).Else(
                                            regs[dst][32:64].eq(immediate)
                                        ),
                                        ip_next.eq(ip_next + 1),
                                        ip.eq(ip_next),
                                        instruction.eq(pgm.dat_r),
                                    ],
                                    #endregion
                                    "default": [
                                        error.eq(1),
                                        halt.eq(1)
                                    ]
                                })
                            ],
                            #endregion
                            #region OPC_LDX
                            OPC_LDX: [
                                If(~data_ack,
                                    data.adr.eq(regs[src] + offset),
                                    state.eq(self.STATE_DATA_FETCH)
                                ).Else(
                                    Case(opcode, {
                                        #region OP_LDXB
                                        EBPF_OP_LDXB: [
                                            regs[dst].eq(data.dat_r)
                                        ],
                                        #endregion
                                        #region OP_LDXH
                                        EBPF_OP_LDXH: [
                                            regs[dst].eq(data.dat_r2)
                                        ],
                                        #endregion
                                        #region OP_LDXW
                                        EBPF_OP_LDXW: [
                                            regs[dst].eq(data.dat_r4)
                                        ],
                                        #endregion
                                        #region OP_LDXDW
                                        EBPF_OP_LDXDW: [
                                            regs[dst].eq(data.dat_r8)
                                        ],
                                        #endregion
                                        "default": [
                                            error.eq(1),
                                            halt.eq(1)
                                        ]
                                    }),
                                    ip_next.eq(ip_next + 1),
                                    ip.eq(ip_next),
                                    instruction.eq(pgm.dat_r),
                                )
                            ],
                            #endregion
                            #region OPC_ST
                            OPC_ST: [
                                If(~data_ack,
                                    data.adr.eq(regs[dst] + offset),
                                    data.we.eq(1),
                                    Case(opcode, {
                                        #region OP_STB
                                        EBPF_OP_STB: [
                                            data.ww.eq(1),
                                            data.dat_w.eq(immediate[0:8])
                                        ],
                                        #endregion
                                        #region OP_STH
                                        EBPF_OP_STH: [
                                            data.ww.eq(2),
                                            data.dat_w.eq(immediate[0:16])
                                        ],
                                        #endregion
                                        #region OP_STW
                                        EBPF_OP_STW: [
                                            data.ww.eq(4),
                                            data.dat_w.eq(immediate[0:32])
                                        ],
                                        #endregion
                                        #region OP_STDW
                                        EBPF_OP_STDW: [
                                            data.ww.eq(8),
                                            data.dat_w.eq(immediate)
                                        ],
                                        #endregion
                                        "default": [
                                            error.eq(1),
                                            halt.eq(1)
                                        ]
                                    }),
                                    state.eq(self.STATE_DATA_FETCH)
                                ).Else(
                                    ip_next.eq(ip_next + 1),
                                    ip.eq(ip_next),
                                    instruction.eq(pgm.dat_r),
                                )
                            ],
                            #endregion
                            #region OPC_STX
                            OPC_STX: [
                                If(~data_ack,
                                    data.adr.eq(regs[dst] + offset),
                                    data.we.eq(1),
                                    Case(opcode, {
                                        #region OP_STXB
                                        EBPF_OP_STXB: [
                                            data.ww.eq(1),
                                            data.dat_w.eq(regs[src][0:8])
                                        ],
                                        #endregion
                                        #region OP_STXH
                                        EBPF_OP_STXH: [
                                            data.ww.eq(2),
                                            data.dat_w.eq(regs[src][0:16])
                                        ],
                                        #endregion
                                        #region OP_STXW
                                        EBPF_OP_STXW: [
                                            data.ww.eq(4),
                                            data.dat_w.eq(regs[src][0:32])
                                        ],
                                        #endregion
                                        #region OP_STXDW
                                        EBPF_OP_STXDW: [
                                            data.ww.eq(8),
                                            data.dat_w.eq(regs[src])
                                        ],
                                        #endregion
                                        "default": [
                                            error.eq(1),
                                            halt.eq(1)
                                        ]
                                    }),
                                    state.eq(self.STATE_DATA_FETCH)
                                ).Else(
                                    ip_next.eq(ip_next + 1),
                                    ip.eq(ip_next),
                                    instruction.eq(pgm.dat_r),
                                )
                            ],
                            #endregion
                            #region OPC_ALU
                            OPC_ALU: [
                                div64_ack.eq(0),
                                Case(opcode, {
                                    #region OP_DIV_IMM
                                    EBPF_OP_DIV_IMM: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst] & 0xffffffff),
                                            div64.divisor.eq(immediate & 0xffffffff),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.quotient),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_DIV_REG
                                    EBPF_OP_DIV_REG: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst] & 0xffffffff),
                                            div64.divisor.eq(regs[src] & 0xffffffff),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.quotient),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_MOD_IMM
                                    EBPF_OP_MOD_IMM: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst] & 0xffffffff),
                                            div64.divisor.eq(immediate & 0xffffffff),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.remainder),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_MOD_REG
                                    EBPF_OP_MOD_REG: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst] & 0xffffffff),
                                            div64.divisor.eq(regs[src] & 0xffffffff),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.remainder),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_ARSH_IMM
                                    EBPF_OP_ARSH_IMM: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(Cat(
                                                regs[dst][0:32],
                                                Replicate(regs[dst][31], 32),
                                            )),
                                            arsh64.shift.eq(immediate),
                                            arsh64.arith.eq(1),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out & 0xffffffff),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_ARSH_REG
                                    EBPF_OP_ARSH_REG: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(Cat(
                                                regs[dst][0:32],
                                                Replicate(regs[dst][31], 32),
                                            )),
                                            arsh64.shift.eq(regs[src] & 0xffffffff),
                                            arsh64.arith.eq(1),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out & 0xffffffff),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_LSH_IMM
                                    EBPF_OP_LSH_IMM: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst] & 0xffffffff),
                                            arsh64.shift.eq(immediate),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(1),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out & 0xffffffff),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_LSH_REG
                                    EBPF_OP_LSH_REG: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst] & 0xffffffff),
                                            arsh64.shift.eq(regs[src] & 0xffffffff),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(1),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out & 0xffffffff),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_RSH_IMM
                                    EBPF_OP_RSH_IMM: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst] & 0xffffffff),
                                            arsh64.shift.eq(immediate),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out & 0xffffffff),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_RSH_REG
                                    EBPF_OP_RSH_REG: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst] & 0xffffffff),
                                            arsh64.shift.eq(regs[src] & 0xffffffff),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out & 0xffffffff),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    "default": [
                                        Case(opcode, {
                                            #region OP_ADD_IMM
                                            EBPF_OP_ADD_IMM: [
                                                regs[dst].eq((regs[dst] + immediate) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_ADD_REG
                                            EBPF_OP_ADD_REG: [
                                                regs[dst].eq((regs[dst] + regs[src]) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_SUB_IMM
                                            EBPF_OP_SUB_IMM: [
                                                regs[dst].eq((regs[dst] - immediate) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_SUB_REG
                                            EBPF_OP_SUB_REG: [
                                                regs[dst].eq((regs[dst] - regs[src]) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_MUL_IMM
                                            EBPF_OP_MUL_IMM: [
                                                regs[dst].eq((regs[dst] * immediate) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_MUL_REG
                                            EBPF_OP_MUL_REG: [
                                                regs[dst].eq((regs[dst] * regs[src]) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_OR_IMM
                                            EBPF_OP_OR_IMM: [
                                                regs[dst].eq((regs[dst] | immediate) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_OR_REG
                                            EBPF_OP_OR_REG: [
                                                regs[dst].eq((regs[dst] | regs[src]) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_AND_IMM
                                            EBPF_OP_AND_IMM: [
                                                regs[dst].eq((regs[dst] & immediate) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_AND_REG
                                            EBPF_OP_AND_REG: [
                                                regs[dst].eq((regs[dst] & regs[src]) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_NEG
                                            EBPF_OP_NEG: [
                                                regs[dst].eq(-regs[dst] & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_XOR_IMM
                                            EBPF_OP_XOR_IMM: [
                                                regs[dst].eq((regs[dst] ^ immediate) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_XOR_REG
                                            EBPF_OP_XOR_REG: [
                                                regs[dst].eq((regs[dst] ^ regs[src]) & 0xffffffff)
                                            ],
                                            #endregion
                                            #region OP_MOV_IMM
                                            EBPF_OP_MOV_IMM: [
                                                regs[dst].eq(immediate),
                                            ],
                                            #endregion
                                            #region OP_MOV_REG
                                            EBPF_OP_MOV_REG: [
                                                regs[dst].eq(regs[src]),
                                            ],
                                            #endregion
                                            #region OP_LE
                                            EBPF_OP_LE: [
                                                Case(immediate, {
                                                    16: [
                                                        regs[dst].eq(Cat(
                                                            regs[dst][0:8],
                                                            regs[dst][8:16]))
                                                    ],
                                                    32: [
                                                        regs[dst].eq(Cat(
                                                            regs[dst][0:8],
                                                            regs[dst][8:16],
                                                            regs[dst][16:24],
                                                            regs[dst][24:32]))
                                                    ],
                                                    64: [
                                                        regs[dst].eq(Cat(
                                                            regs[dst][0:8],
                                                            regs[dst][8:16],
                                                            regs[dst][16:24],
                                                            regs[dst][24:32],
                                                            regs[dst][32:40],
                                                            regs[dst][40:48],
                                                            regs[dst][48:56],
                                                            regs[dst][56:64]))
                                                    ],
                                                    "default": [
                                                        error.eq(1),
                                                        halt.eq(1)
                                                    ]
                                                })
                                            ],
                                            #endregion
                                            #region OP_BE
                                            EBPF_OP_BE: [
                                                Case(immediate, {
                                                    16: [
                                                        regs[dst].eq(Cat(
                                                            regs[dst][8:16],
                                                            regs[dst][0:8]))
                                                    ],
                                                    32: [
                                                        regs[dst].eq(Cat(
                                                            regs[dst][24:32],
                                                            regs[dst][16:24],
                                                            regs[dst][8:16],
                                                            regs[dst][0:8]))
                                                    ],
                                                    64: [
                                                        regs[dst].eq(Cat(
                                                            regs[dst][56:64],
                                                            regs[dst][48:56],
                                                            regs[dst][40:48],
                                                            regs[dst][32:40],
                                                            regs[dst][24:32],
                                                            regs[dst][16:24],
                                                            regs[dst][8:16],
                                                            regs[dst][0:8]))
                                                    ],
                                                    "default": [
                                                        error.eq(1),
                                                        halt.eq(1)
                                                    ]
                                                })
                                            ],
                                            #endregion
                                            "default": [
                                                error.eq(1),
                                                halt.eq(1)
                                            ]
                                        }),
                                        ip_next.eq(ip_next + 1),
                                        ip.eq(ip_next),
                                        instruction.eq(pgm.dat_r),
                                    ]
                                })
                            ],
                            #endregion
                            #region OPC_JMP
                            OPC_JMP: [
                                Case(opcode, {
                                    #region OP_CALL
                                    EBPF_OP_CALL: call_handler_actions,
                                    #endregion
                                    "default": [
                                        state.eq(self.STATE_OP_FETCH),
                                        Case(opcode, {
                                            #region OP_JA
                                            EBPF_OP_JA: [
                                                ip_next.eq(ip_next + offset_s),
                                            ],
                                            #endregion
                                            #region OP_JEQ_IMM
                                            EBPF_OP_JEQ_IMM: [
                                                If(regs[dst] == immediate,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JEQ_REG
                                            EBPF_OP_JEQ_REG: [
                                                If(regs[dst] == regs[src],
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JGT_IMM
                                            EBPF_OP_JGT_IMM: [
                                                If(regs[dst] > immediate,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JGT_REG
                                            EBPF_OP_JGT_REG: [
                                                If(regs[dst] > regs[src],
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JGE_IMM
                                            EBPF_OP_JGE_IMM: [
                                                If(regs[dst] >= immediate,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JGE_REG
                                            EBPF_OP_JGE_REG: [
                                                If(regs[dst] >= regs[src],
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSET_IMM
                                            EBPF_OP_JSET_IMM: [
                                                If(regs[dst] & immediate,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSET_REG
                                            EBPF_OP_JSET_REG: [
                                                If(regs[dst] & regs[src],
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JNE_IMM
                                            EBPF_OP_JNE_IMM: [
                                                If(regs[dst] != immediate,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JNE_REG
                                            EBPF_OP_JNE_REG: [
                                                If(regs[dst] != regs[src],
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSGT_IMM
                                            EBPF_OP_JSGT_IMM: [
                                                If(dst_reg_32_s > immediate_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSGT_REG
                                            EBPF_OP_JSGT_REG: [
                                                If(dst_reg_32_s > src_reg_32_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSGE_IMM
                                            EBPF_OP_JSGE_IMM: [
                                                If(dst_reg_32_s >= immediate_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSGE_REG
                                            EBPF_OP_JSGE_REG: [
                                                If(dst_reg_32_s >= src_reg_32_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_EXIT
                                            EBPF_OP_EXIT: [
                                                halt.eq(1),
                                            ],
                                            #endregion
                                            #region OP_JLT_IMM
                                            EBPF_OP_JLT_IMM: [
                                                If(regs[dst] < immediate,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JLT_REG
                                            EBPF_OP_JLT_REG: [
                                                If(regs[dst] < regs[src],
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JLE_IMM
                                            EBPF_OP_JLE_IMM: [
                                                If(regs[dst] <= immediate,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JLE_REG
                                            EBPF_OP_JLE_REG: [
                                                If(regs[dst] <= regs[src],
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSLT_IMM
                                            EBPF_OP_JSLT_IMM: [
                                                If(dst_reg_32_s < immediate_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSLT_REG
                                            EBPF_OP_JSLT_REG: [
                                                If(dst_reg_32_s < src_reg_32_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSLE_IMM
                                            EBPF_OP_JSLE_IMM: [
                                                If(dst_reg_32_s <= immediate_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            #region OP_JSLE_REG
                                            EBPF_OP_JSLE_REG: [
                                                If(dst_reg_32_s <= src_reg_32_s,
                                                    ip_next.eq(ip_next + offset_s),
                                                )
                                            ],
                                            #endregion
                                            "default": [
                                                error.eq(1),
                                                halt.eq(1)
                                            ]
                                        }),
                                        ip.eq(ip_next),
                                    ]
                                })
                            ],
                            #endregion
                            #region OPC_RES
                            OPC_RES: [
                                error.eq(1),
                                halt.eq(1)
                            ],
                            #endregion
                            #region OPC_ALU64
                            OPC_ALU64: [
                                div64_ack.eq(0),
                                Case(opcode, {
                                    #region OP_DIV64_IMM
                                    EBPF_OP_DIV64_IMM: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst]),
                                            div64.divisor.eq(immediate),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.quotient),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_DIV64_REG
                                    EBPF_OP_DIV64_REG: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst]),
                                            div64.divisor.eq(regs[src]),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.quotient),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_MOD64_IMM
                                    EBPF_OP_MOD64_IMM: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst]),
                                            div64.divisor.eq(immediate),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.remainder),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_MOD64_REG
                                    EBPF_OP_MOD64_REG: [
                                        If(~div64_ack,
                                            div64.dividend.eq(regs[dst]),
                                            div64.divisor.eq(regs[src]),
                                            state.eq(self.STATE_DIV_PENDING),
                                            div64.stb.eq(1),
                                        ).Else(
                                            regs[dst].eq(div64.remainder),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_ARSH64_IMM
                                    EBPF_OP_ARSH64_IMM: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst]),
                                            arsh64.shift.eq(immediate),
                                            arsh64.arith.eq(1),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_ARSH64_REG
                                    EBPF_OP_ARSH64_REG: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst]),
                                            arsh64.shift.eq(regs[src]),
                                            arsh64.arith.eq(1),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_LSH64_IMM
                                    EBPF_OP_LSH64_IMM: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst]),
                                            arsh64.shift.eq(immediate),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(1),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_LSH64_REG
                                    EBPF_OP_LSH64_REG: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst]),
                                            arsh64.shift.eq(regs[src]),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(1),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_RSH64_IMM
                                    EBPF_OP_RSH64_IMM: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst]),
                                            arsh64.shift.eq(immediate),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    #region OP_RSH64_REG
                                    EBPF_OP_RSH64_REG: [
                                        If(~arsh64.ack,
                                            arsh64.value.eq(regs[dst]),
                                            arsh64.shift.eq(regs[src]),
                                            arsh64.arith.eq(0),
                                            arsh64.left.eq(0),
                                            arsh64.stb.eq(1)
                                        ).Else(
                                            regs[dst].eq(arsh64.out),
                                            arsh64.stb.eq(0),
                                            ip_next.eq(ip_next + 1),
                                            ip.eq(ip_next),
                                            instruction.eq(pgm.dat_r),
                                        )
                                    ],
                                    #endregion
                                    "default": [
                                        Case(opcode, {
                                            #region OP_ADD64_IMM
                                            EBPF_OP_ADD64_IMM: [
                                                regs[dst].eq(regs[dst] + immediate)
                                            ],
                                            #endregion
                                            #region OP_ADD64_REG
                                            EBPF_OP_ADD64_REG: [
                                                regs[dst].eq(regs[dst] + regs[src])
                                            ],
                                            #endregion
                                            #region OP_SUB64_IMM
                                            EBPF_OP_SUB64_IMM: [
                                                regs[dst].eq(regs[dst] - immediate)
                                            ],
                                            #endregion
                                            #region OP_SUB64_REG
                                            EBPF_OP_SUB64_REG: [
                                                regs[dst].eq(regs[dst] - regs[src])
                                            ],
                                            #endregion
                                            #region OP_MUL64_IMM
                                            EBPF_OP_MUL64_IMM: [
                                                regs[dst].eq(regs[dst] * immediate)
                                            ],
                                            #endregion
                                            #region OP_MUL64_REG
                                            EBPF_OP_MUL64_REG: [
                                                regs[dst].eq(regs[dst] * regs[src])
                                            ],
                                            #endregion
                                            #region OP_OR64_IMM
                                            EBPF_OP_OR64_IMM: [
                                                regs[dst].eq(regs[dst] | immediate)
                                            ],
                                            #endregion
                                            #region OP_OR64_REG
                                            EBPF_OP_OR64_REG: [
                                                regs[dst].eq(regs[dst] | regs[src])
                                            ],
                                            #endregion
                                            #region OP_AND64_IMM
                                            EBPF_OP_AND64_IMM: [
                                                regs[dst].eq(regs[dst] & immediate)
                                            ],
                                            #endregion
                                            #region OP_AND64_REG
                                            EBPF_OP_AND64_REG: [
                                                regs[dst].eq(regs[dst] & regs[src])
                                            ],
                                            #endregion
                                            #region OP_NEG64
                                            EBPF_OP_NEG64: [
                                                regs[dst].eq(-regs[dst])
                                            ],
                                            #endregion
                                            #region OP_XOR64_IMM
                                            EBPF_OP_XOR64_IMM: [
                                                regs[dst].eq(regs[dst] ^ immediate)
                                            ],
                                            #endregion
                                            #region OP_XOR64_REG
                                            EBPF_OP_XOR64_REG: [
                                                regs[dst].eq(regs[dst] ^ regs[src])
                                            ],
                                            #endregion
                                            #region OP_MOV64_IMM
                                            EBPF_OP_MOV64_IMM: [
                                                regs[dst].eq(immediate),
                                            ],
                                            #endregion
                                            #region OP_MOV64_REG
                                            EBPF_OP_MOV64_REG: [
                                                regs[dst].eq(regs[src]),
                                            ],
                                            #endregion
                                            "default": [
                                                error.eq(1),
                                                halt.eq(1)
                                            ]
                                        }),
                                        ip_next.eq(ip_next + 1),
                                        ip.eq(ip_next),
                                        instruction.eq(pgm.dat_r),
                                    ]
                                })
                            ]
                            #endregion
                        }),

                        data_ack.eq(0)
                    ],
                    #endregion

                    #region STATE_DATA_FETCH
                    # Fetch from data memory.
                    self.STATE_DATA_FETCH: [
                        data.stb.eq(1),
                        If(data.ack,
                            data.stb.eq(0),
                            data.we.eq(0),
                            state.eq(self.STATE_DECODE),
                            data_ack.eq(1)
                        )
                    ],
                    #endregion

                    #region STATE_DIV_PENDING
                    # Exec math divide.
                    self.STATE_DIV_PENDING: [
                        If(div64.stb,
                            div64.stb.eq(0)
                        ).Else(
                            If(div64.ack,
                                If(div64.err,
                                    regs[dst].eq(0xffffffffffffffff),
                                    error.eq(1),
                                    halt.eq(1)
                                ).Else(
                                    state.eq(self.STATE_DECODE),
                                    div64_ack.eq(1),
                                )
                            )
                        )
                    ],
                    #endregion

                    #region STATE_CALL_PENDING
                    # Call pending.
                    self.STATE_CALL_PENDING: call_handler_state,
                    #endregion
                })
            )
        ]


##################
# CPU testbench: #
##################

# No actual tests. These are performed using unittests from test directory.
# This instead just starts the CPU and executes the sample program and
# generates a VCD file for inspection.

# Top-level CPU test method.
def cpu_test(cpu):

    # Print a test header.
    print("--- CPU Test ---")

    yield cpu.reset_n.eq(0)
    for i in range(5):
        yield

    yield cpu.reset_n.eq(1)
    for i in range(200):
        yield

    # Done.
    yield


# 'main' method to run a basic testbench.
if __name__ == "__main__":
    # Instantiate a CPU module.
    dut = CPU(pgm_init="../../tests/samples/test_pgm_mem.bin",
            data_init="../../tests/samples/test_data_mem.bin")

    # Run the tests.
    run_simulation(dut, cpu_test(dut), vcd_name="cpu.vcd")
