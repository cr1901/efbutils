from amaranth import Signal, Module
from amaranth.lib.wiring import Signature, In, Out, Component, connect, \
    flipped

from .page_buffer import PageBuffer
from .streamer import Streamer
from .sequencer import EfbWishbone


ReaderSignature = Signature({
    "data": In(8),
    "addr": Out(15),
    "read_en": Out(1),
    "valid": In(1),
    "stall": Out(1),  # Unused, for compatibility with Verilog ports.
})


class Reader(Component):
    bus: In(ReaderSignature)
    efb: Out(EfbWishbone)

    def __init__(self):
        super().__init__()
        self.pagemod = PageBuffer()
        self.streammod = Streamer()

    def elaborate(self, plat):
        m = Module()
        m.submodules.pagemod = self.pagemod
        m.submodules.streammod = self.streammod

        reader_ready = Signal(1)  # Presently unused, meant to support
        # double-bufferring down the line. Right now, reader is inactive
        # if read_en is not asserted.

        connect(m, flipped(self.efb), self.streammod.efb)

        # connect(m, self.streammod.stream, self.pagemod.seq) if stall or ready
        # were not part of stream signature.
        m.d.comb += [
            self.pagemod.seq.data.eq(self.streammod.stream.data),
            self.streammod.stream.addr.eq(self.pagemod.seq.addr),
            self.streammod.stream.stb.eq(self.pagemod.seq.stb),
            self.pagemod.seq.ack.eq(self.streammod.stream.ack),
            self.streammod.stream.stall.eq(0),
            reader_ready.eq(self.streammod.stream.ready)
        ]

        # "connect(m, flipped(self.pagemod.rand), self.bus)" if stall was not
        # part of bus signature, and flush was.
        m.d.comb += [
            self.bus.data.eq(self.pagemod.rand.data),
            self.pagemod.rand.addr.eq(self.bus.addr),
            self.pagemod.rand.read_en.eq(self.bus.read_en),
            self.pagemod.rand.flush.eq(0),
            self.bus.valid.eq(self.pagemod.rand.valid),
        ]

        return m


if __name__ == "__main__":
    m = Reader()
