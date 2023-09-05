import pytest
from amaranth.sim import Passive
from amaranth import Module
from amaranth.lib.wiring import Signature, In, Out, Component, flipped, \
    connect

from efbutils.ufm.reader.sequencer import Sequencer, ConstantOp, \
    Name, Operands, SeqWriteStreamSignature, SeqReadStreamSignature, \
    EfbWishbone


SysConfigCmdSplitter = Signature({
    "cmd": Out(Name),
    "ops": Out(Operands)
})


class Wrapper(Component):
    signature = Signature({
        "ctl": Out(Signature({
            "req": Out(1),
            "cmd": Out(SysConfigCmdSplitter),
            "done": In(1),
            "op_len": Out(2),  # Temporary, for compatibility with Verilog ports.  # noqa: E501
            "data_len": Out(6),  # Temporary, for compatibility with Verilog ports.  # noqa: E501
            "xfer_is_wr": Out(1)  # Temporary, for compatibility with Verilog ports.  # noqa: E501
        })),
        "wr": Out(SeqWriteStreamSignature),
        "rd": In(SeqReadStreamSignature),
        "efb": Out(EfbWishbone)
    })

    def __init__(self, s):
        super().__init__()
        self.s = s

    def elaborate(self, plat):
        m = Module()

        m.submodules += self.s

        connect(m, self.wr, self.s.ctl.wr)
        connect(m, self.rd, self.s.ctl.rd)
        connect(m, flipped(self.efb), self.s.efb)

        m.d.comb += [
            self.s.ctl.req.eq(self.ctl.req),
            self.s.ctl.cmd.cmd.eq(self.ctl.cmd.cmd),
            self.s.ctl.cmd.ops.eq(self.ctl.cmd.ops),
            self.ctl.done.eq(self.s.ctl.done),
            self.s.ctl.op_len.eq(self.ctl.op_len),
            self.s.ctl.data_len.eq(self.ctl.data_len),
            self.s.ctl.cmd.ops.eq(self.ctl.cmd.ops),
            self.s.ctl.xfer_is_wr.eq(self.ctl.xfer_is_wr),
        ]

        return m


@pytest.mark.module(Wrapper(Sequencer()))
@pytest.mark.clks((1.0 / 12e6,))
def test_wrapper_write(sim_mod):
    sim, seq = sim_mod

    def in_proc():
        def yieldn(n):
            for _ in range(n):
                yield

        yield seq.ctl.req.eq(1)
        yield seq.ctl.cmd.cmd.eq(Name.SET_UFM_ADDR)
        yield seq.ctl.cmd.ops.constant.eq(ConstantOp.ZEROS)
        yield seq.ctl.op_len.eq(3)
        yield seq.ctl.data_len.eq(4)
        yield seq.ctl.xfer_is_wr.eq(1)
        yield seq.wr.data.set_ufm_addr.pages.eq(2044)
        yield seq.wr.data.set_ufm_addr.space.eq(1)

        # Request is a strobe
        yield
        yield seq.ctl.req.eq(0)
        yield

        # Enable
        assert (yield seq.efb.dat_w) == 0x80
        assert (yield seq.efb.adr) == 0x70

        yield from yieldn(3)

        # Command
        assert (yield seq.efb.dat_w) == Name.SET_UFM_ADDR
        assert (yield seq.efb.adr) == 0x71

        # Operands
        for _ in range(3):
            yield from yieldn(3)

            assert (yield seq.efb.dat_w) == 0x00
            assert (yield seq.efb.adr) == 0x71

        yield from yieldn(3)

        assert (yield seq.efb.dat_w) == 0x40  # Bit 30 must be "1" for UFM addr space.  # noqa: E501
        assert (yield seq.efb.adr) == 0x71

        yield from yieldn(3)

        assert (yield seq.efb.dat_w) == 0x00
        assert (yield seq.efb.adr) == 0x71

        yield from yieldn(3)

        assert (yield seq.efb.dat_w) == ((2044 & 0x3f00) >> 8)  # Only 14 bits are used.  # noqa: E501
        assert (yield seq.efb.adr) == 0x71

        yield from yieldn(3)

        assert (yield seq.efb.dat_w) == (2044 & 0xff)
        assert (yield seq.efb.adr) == 0x71

        yield from yieldn(3)

        assert (yield seq.efb.dat_w) == 0
        assert (yield seq.efb.adr) == 0x70

        yield from yieldn(2)

        assert (yield seq.ctl.done) == 1  # After WB ACK, we strobe done.
        yield

        assert (yield seq.ctl.done) == 0

    def ack_proc():
        yield Passive()

        while True:
            yield seq.efb.ack.eq(0)
            if (yield seq.efb.stb) and (yield seq.efb.cyc) and not (yield seq.efb.ack):  # noqa: E501
                yield seq.efb.ack.eq(1)
            yield

    sim.run(sync_processes=[in_proc, ack_proc])
