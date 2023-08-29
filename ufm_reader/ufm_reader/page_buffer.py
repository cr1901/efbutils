from amaranth import Signal, Module
from amaranth.lib.data import ArrayLayout
from amaranth.lib.wiring import Signature, In, Out, Component


class SeqSignature(Signature):
    def __init__(self):
        return super().__init__({
            "data": In(8),
            "addr": Out(11),
            "stb": Out(1),  # Not a RDY signal like a stream. Only sent once per byte.  # noqa: E501
            "ack": In(1)  # Basically a VALID signal.
        })


class RandSignature(Signature):
    def __init__(self):
        return super().__init__({
            "data": In(8),
            "addr": Out(15),
            "read_en": Out(1),
            "flush": Out(1),
            "valid": In(1)
        })


class PageBuffer(Component):
    rand: In(RandSignature())
    seq: Out(SeqSignature())

    def __init__(self):
        super().__init__()
        self.buf = Signal(ArrayLayout(8, 16), reset_less=True)

    def elaborate(self, plat):
        m = Module()

        read_en_delayed = Signal(1)
        curr_page = Signal(11)
        wr_ptr = Signal(4)
        rd_ptr = Signal.like(wr_ptr)

        # Hook up unconditional interface logic first.
        # RAND
        m.d.comb += self.rand.data.eq(self.buf[rd_ptr])
        m.d.sync += rd_ptr.eq(self.rand.addr)
        # Reads are registered, so it takes one cycle before
        # they're actually valid.
        m.d.sync += read_en_delayed.eq(self.rand.read_en)

        # SEQ
        m.d.comb += self.seq.addr.eq(curr_page)
        m.d.sync += self.seq.stb.eq(0)

        with m.FSM() as fsm:
            with m.State("INIT"):
                with m.If(self.rand.read_en):
                    m.d.sync += [
                        curr_page.eq(self.rand.addr[4:]),
                        self.seq.stb.eq(1),
                    ]
                    m.next = "FILL"

            with m.State("FILL"):
                with m.If(self.seq.ack):
                    m.d.sync += [
                        self.buf[wr_ptr].eq(self.seq.data),
                        wr_ptr.eq(wr_ptr + 1),
                        self.seq.stb.eq(1)
                    ]

                    with m.If(wr_ptr == 15):
                        m.next = "VALID"

            with m.State("VALID"):
                with m.If(self.rand.read_en):
                    with m.If(self.rand.addr[4:] != curr_page):
                        m.d.sync += [
                            curr_page.eq(self.rand.addr[4:]),
                            self.seq.stb.eq(1),
                        ]

                        m.next = "FILL"

            m.d.comb += self.rand.valid.eq(read_en_delayed & fsm.ongoing("VALID"))  # noqa: E501

        return m


if __name__ == "__main__":
    m = PageBuffer()
