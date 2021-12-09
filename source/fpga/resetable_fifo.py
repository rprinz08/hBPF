from migen import *
from migen.genlib.fifo import _FIFOInterface, _inc


class ResetableSyncFIFO(Module, _FIFOInterface):
    """Resetable Synchronous FIFO (first in, first out)

    Read and write interfaces are accessed from the same clock domain.
    If different clock domains are needed, use :class:`AsyncFIFO`.

    {interface}
    level : out
        Number of unread entries.
    replace : in
        Replaces the last entry written into the FIFO with `din`. Does nothing
        if that entry has already been read (i.e. the FIFO is empty).
        Assert in conjunction with `we`.
    clear : in
        Resets to FIFO to an empty state.
    """
    __doc__ = __doc__.format(interface=_FIFOInterface.__doc__)

    def __init__(self, width, depth, fwft=True):
        _FIFOInterface.__init__(self, width, depth)

        self.replace = Signal()
        self.reset = Signal()

        self.level = Signal(max=depth+1)

        # # #

        produce = Signal(max=depth)
        consume = Signal(max=depth)
        storage = Memory(self.width, depth)
        self.specials += storage

        wrport = storage.get_port(write_capable=True, mode=READ_FIRST)
        self.specials += wrport
        self.comb += [
            If(self.replace,
                wrport.adr.eq(produce-1)
            ).Else(
                wrport.adr.eq(produce)
            ),
            wrport.dat_w.eq(self.din),
            wrport.we.eq(self.we & (self.writable | self.replace))
        ]
        self.sync += [
            If(self.reset,
                produce.eq(0)
            ).Elif(self.we & self.writable & ~self.replace,
                _inc(produce, depth)
            )
        ]

        do_read = Signal()
        self.comb += do_read.eq(self.readable & self.re)

        rdport = storage.get_port(async_read=fwft, has_re=not fwft, mode=READ_FIRST)
        self.specials += rdport
        self.comb += [
            rdport.adr.eq(consume),
            self.dout.eq(rdport.dat_r)
        ]
        if not fwft:
            self.comb += rdport.re.eq(do_read)
        self.sync += [
            If(self.reset,
                consume.eq(0)
            ).Elif(do_read,
                _inc(consume, depth)
            )
        ]

        self.sync += [
            If(self.reset,
                self.level.eq(0)
            ).Elif(self.we & self.writable & ~self.replace,
                If(~do_read,
                    self.level.eq(self.level + 1)
                )
            ).Elif(do_read,
                self.level.eq(self.level - 1)
            )
        ]
        self.comb += [
            self.writable.eq(self.level != depth),
            self.readable.eq(self.level != 0)
        ]
