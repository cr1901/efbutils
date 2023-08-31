from amaranth import Module
from amaranth.lib.wiring import Signature, In, Out, Component, flipped, \
    connect

from amgen import AmaranthGenerator

from ufm_reader.sequencer import Sequencer, Name, Operands, \
    SeqWriteStreamSignature, SeqReadStreamSignature, EfbWishbone


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
            "xfer_is_wr": Out(1) # Temporary, for compatibility with Verilog ports.  # noqa: E501
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


class SequencerGenerator(AmaranthGenerator):
    output_file = "sequencer.v"
    module_name = "sequencer"

    def __init__(self):
        super().__init__()

    # Generate a core to be included in another project.
    def create_module(self):
        s = Sequencer()
        m = Wrapper(s)

        ios = [m.ctl.req, m.ctl.cmd.cmd, m.ctl.cmd.ops.as_value(), m.ctl.done,
               m.ctl.op_len, m.ctl.data_len, m.ctl.xfer_is_wr,
               m.wr.data.as_value(), m.wr.ready, m.wr.valid,
               m.rd.data, m.rd.stb, m.efb.cyc, m.efb.stb, m.efb.we,
               m.efb.adr, m.efb.dat_w, m.efb.dat_r, m.efb.ack]
        return (m, ios)


if __name__ == "__main__":
    SequencerGenerator().generate()
