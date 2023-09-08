import pytest
from amaranth import Module, Memory, Elaboratable, Signal

from efbutils.ufm.reader.page_buffer import PageBuffer


class DUT(Elaboratable):
    def __init__(self, *, sync_read=False):
        self.sync_read = sync_read
        self.pb = PageBuffer()
        self.mem = Memory(width=8, depth=64, init=[
            *(i for i in reversed(range(16))),
            *(i for i in reversed(range(16, 32))),
            *(i for i in reversed(range(32, 48))),
            *(i for i in reversed(range(48, 64))),
        ])

    def elaborate(self, plat):
        m = Module()
        m.submodules.pb = self.pb
        m.submodules.rd = rd = self.mem.read_port()
        # m.submodules.wr = wr = self.mem.write_port()

        m.d.sync += self.pb.seq.ack.eq(0)
        count = Signal(4)

        m.d.comb += rd.addr.eq(self.pb.seq.addr*16 + count)

        if not self.sync_read:
            m.d.comb += self.pb.seq.data.eq(rd.data)
        else:
            m.d.sync += self.pb.seq.data.eq(rd.data)

        with m.If(self.pb.seq.stb & ~self.pb.seq.ack):
            m.d.sync += [
                self.pb.seq.ack.eq(1),
                count.eq(count + 1)
            ]

        return m


@pytest.mark.module(DUT(sync_read=False))
@pytest.mark.clks((1.0 / 12e6,))
def test_page_buffer_read(sim_mod):
    sim, dut = sim_mod

    def main_proc():
        def yieldn(n):
            for _ in range(n):
                yield

        yield dut.pb.rand.addr.eq(0)
        yield dut.pb.rand.read_en.eq(1)
        yield
        yield  # If cache was already filled, then valid data would be here
        # at this cycle.
        assert (yield dut.pb.rand.valid) == 0

        for j in range(4):
            yield from yieldn(32)
            assert (yield dut.pb.rand.valid) == 1

            for i in range(16*j, 16*(j+1)):
                yield
                assert (yield dut.pb.rand.valid) == 1
                assert (yield dut.pb.rand.data) == (yield dut.mem[i])

                yield dut.pb.rand.addr.eq(i + 1)
                yield

            yield   # Normally one clk latency for reads. We exited the loop
            # before we take that one cycle.
            assert (yield dut.pb.rand.valid) == 0

        yield from yieldn(32)
        assert (yield dut.pb.rand.valid) == 1
        assert (yield dut.pb.rand.data) == (yield dut.mem[0])

    sim.run(sync_processes=[main_proc])
