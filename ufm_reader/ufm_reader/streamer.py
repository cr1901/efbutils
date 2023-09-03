from amaranth import Signal, Module
from amaranth.lib.wiring import Signature, In, Out, Component, connect, \
    flipped

from .page_buffer import SeqSignature as PageBufSignature
from .sequencer import SequencerSignature, EfbWishbone, Sequencer, Name


StreamerSignature = Signature({
    **PageBufSignature.members,
    "stall": Out(1),  # Unused, for compatibility with Verilog ports.  # noqa: E501
    "ready": In(1),  # Unused, for compatibility with Verilog ports.  # noqa: E501
})


class Streamer(Component):
    stream: In(StreamerSignature)
    efb: Out(EfbWishbone)

    def __init__(self):
        super().__init__()
        self.seqmod = Sequencer()
        self._seq = SequencerSignature.create()

    def elaborate(self, plat):
        m = Module()
        m.submodules.seqmod = self.seqmod

        ufm_busy = Signal(2)
        just_entered = Signal(1)

        connect(m, self.seqmod.ctl, self._seq)
        connect(m, flipped(self.efb), self.seqmod.efb)

        m.d.comb += self.stream.data.eq(self._seq.rd.data.stream)

        def drive_sequencer_poll_status():
            m.d.comb += [
                self._seq.cmd.cmd.eq(Name.POLL_STATUS),
                self._seq.cmd.ops.eq(0),
                self._seq.op_len.eq(3),
                self._seq.wr.data.eq(0),
                self._seq.data_len.eq(4),
                self._seq.xfer_is_wr.eq(0)
            ]

        with m.FSM() as fsm:  # noqa: F841
            with m.State("IDLE"):
                m.d.comb += self.stream.ready.eq(1)
                m.d.comb += [
                    self._seq.cmd.cmd.eq(Name.IDLE),
                    self._seq.cmd.ops.constant.eq(0),
                    self._seq.op_len.eq(0),
                    self._seq.wr.data.eq(0),
                    self._seq.data_len.eq(0),
                    self._seq.xfer_is_wr.eq(1)
                ]

                with m.If(self.stream.stb):
                    m.next = "ENABLE_CONFIG"

            with m.State("ENABLE_CONFIG"):
                m.d.comb += self._seq.req.eq(just_entered)
                m.d.comb += [
                    self._seq.cmd.cmd.eq(Name.ENABLE_CONFIG),
                    self._seq.cmd.ops.eq(0x080000),
                    self._seq.op_len.eq(3),
                    self._seq.wr.data.eq(0),
                    self._seq.data_len.eq(0),
                    self._seq.xfer_is_wr.eq(1)
                ]

                with m.If(self._seq.done):
                    m.next = "POLL_STATUS_1"

            # Bleh... easier to make each data strobe an individual state.
            with m.State("POLL_STATUS_1"):
                m.d.comb += self._seq.req.eq(just_entered)
                drive_sequencer_poll_status()

                with m.If(self._seq.rd.stb):
                    m.next = "POLL_STATUS_2"

            with m.State("POLL_STATUS_2"):
                drive_sequencer_poll_status()

                with m.If(self._seq.rd.stb):
                    m.next = "POLL_STATUS_3"

            with m.State("POLL_STATUS_3"):
                drive_sequencer_poll_status()
                with m.If(self._seq.rd.stb):
                    m.d.sync += ufm_busy.eq(self._seq.rd.data.status.busy)

                with m.If(self._seq.rd.stb):
                    m.next = "POLL_STATUS_4"

            with m.State("POLL_STATUS_4"):
                drive_sequencer_poll_status()

                with m.If(self._seq.rd.stb):
                    m.next = "POLL_STATUS_5"

            with m.State("POLL_STATUS_5"):
                drive_sequencer_poll_status()

                with m.If(self._seq.done):
                    m.next = "SET_UFM_ADDR"
                    with m.If(ufm_busy):
                        m.next = "POLL_STATUS_1"

            with m.State("SET_UFM_ADDR"):
                m.d.comb += self._seq.req.eq(just_entered)
                m.d.comb += [
                    self._seq.cmd.cmd.eq(Name.SET_UFM_ADDR),
                    self._seq.cmd.ops.eq(0),
                    self._seq.op_len.eq(3),
                    self._seq.wr.data.set_ufm_addr.pages.eq(self.stream.addr),
                    self._seq.wr.data.set_ufm_addr.space.eq(1),
                    self._seq.data_len.eq(4),
                    self._seq.xfer_is_wr.eq(1)
                ]

                with m.If(self._seq.done):
                    m.next = "READ_UFM"

            with m.State("READ_UFM"):
                m.d.comb += self._seq.req.eq(just_entered)
                m.d.comb += self.stream.ack.eq(self._seq.rd.stb)
                m.d.comb += [
                    self._seq.cmd.cmd.eq(Name.READ_UFM),
                    self._seq.cmd.ops.read_ufm.pages.eq(1),
                    self._seq.cmd.ops.read_ufm.port.eq(1),
                    self._seq.op_len.eq(3),
                    self._seq.wr.data.eq(0),
                    self._seq.data_len.eq(16),
                    self._seq.xfer_is_wr.eq(0)
                ]

                with m.If(self._seq.done):
                    m.next = "DISABLE_CONFIG"

            with m.State("DISABLE_CONFIG"):
                m.d.comb += self._seq.req.eq(just_entered)
                m.d.comb += [
                    self._seq.cmd.cmd.eq(Name.DISABLE_CONFIG),
                    self._seq.cmd.ops.disable.eq(0),
                    self._seq.op_len.eq(2),
                    self._seq.wr.data.eq(0),
                    self._seq.data_len.eq(0),
                    self._seq.xfer_is_wr.eq(1)
                ]

                with m.If(self._seq.done):
                    m.next = "BYPASS"

            with m.State("BYPASS"):
                m.d.comb += self._seq.req.eq(just_entered)
                with m.If(self._seq.done & ~self.stream.stb):
                    m.d.comb += self.stream.ready.eq(1)
                m.d.comb += [
                    self._seq.cmd.cmd.eq(Name.BYPASS),
                    self._seq.cmd.ops.eq(0),
                    self._seq.op_len.eq(0),
                    self._seq.wr.data.eq(0),
                    self._seq.data_len.eq(0),
                    self._seq.xfer_is_wr.eq(1)
                ]

                with m.If(self._seq.done):
                    m.next = "IDLE"
                    with m.If(self.stream.stb):
                        m.next = "ENABLE_CONFIG"

        prev_state = Signal.like(fsm.state)
        m.d.sync += prev_state.eq(fsm.state)
        m.d.comb += just_entered.eq(prev_state != fsm.state)

        return m
