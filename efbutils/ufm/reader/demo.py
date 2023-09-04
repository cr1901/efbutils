from amaranth import Signal, Module, Elaboratable, ClockDomain, \
    ClockSignal, ResetSignal, Instance, C
from amaranth.lib.wiring import Signature, In, Out, Component, connect
from amaranth.utils import log2_int
from amaranth_stdio import serial

from .efb import EFB
from .reader import Reader, ReaderSignature


def demo_signature(num_leds):
    return Signature({
        "rx": In(1),
        "tx": Out(1),
        "leds": Out(num_leds),
    })


class Demo(Component):
    @property
    def signature(self):
        return demo_signature(self.num_leds)

    def __init__(self, *, num_leds, efb_config, ufm_config):
        self.num_leds = num_leds
        super().__init__()

        self.efb_config = efb_config
        self.ufm_config = ufm_config
        self._rdr = ReaderSignature.create()

    def elaborate(self, plat):
        m = Module()
        m.domains += ClockDomain("cd_por2x", reset_less=True)

        divisor = int((self.efb_config["efb_wb_clk_freq"] * 1e6) // (2*9600))
        m.submodules.por = POR()
        m.submodules.uart = uart = serial.AsyncSerial(divisor=divisor)
        m.submodules.clkdiv = Instance("CLKDIVC",
                                       i_CLKI=ClockSignal("por2x"),
                                       o_CDIVX=ClockSignal("por"))
        m.submodules.osch = \
            Instance("OSCH",
                     p_NOM_FREQ=str(self.efb_config["efb_wb_clk_freq"]),
                     i_STDBY=C(0),
                     o_OSC=ClockSignal("por2x"))
        m.submodules.wait = wait = \
            WaitTimer(self.efb_config["efb_wb_clk_freq"])
        m.submodules.efb = efb = EFB(efb_config=self.efb_config,
                                     ufm_config=self.ufm_config,
                                     tc_config=None,
                                     spi_config=None,
                                     i2c1_config=None,
                                     i2c2_config=None)
        m.submodules.reader = reader = Reader()

        take_break = Signal(1)
        do_read = Signal(1)
        curr_byte_addr = Signal(15, reset=self.ufm_config["start_page"]*16)

        connect(m, reader.bus, self._rdr)
        connect(m, efb.bus, reader.efb)

        if self.num_leds > 0:
            m.d.comb += self.leds[0].eq(self.rx)
        if self.num_leds > 1:
            m.d.comb += self.leds[1].eq(self.tx)
        if self.num_leds > 2:
            m.d.comb += self.leds[2].eq(~self._rdr.valid)
        if self.num_leds > 3:
            m.d.comb += self.leds[3].eq(1)  # Unused right now
        if self.num_leds > 4:
            m.d.comb += self.leds[4].eq(1)  # Unused right now
        if self.num_leds > 5:
            m.d.comb += self.leds[5].eq(~do_read)
        if self.num_leds > 7:
            used_addr_bus_width = log2_int(self.ufm_config["num_pages"]) + 4
            high_addr_bits = ~curr_byte_addr[used_addr_bus_width-2:used_addr_bus_width]  # noqa: E501
            m.d.comb += self.leds[6:8].eq(high_addr_bits)

        m.d.comb += [
            self.tx.eq(uart.tx.o),
            uart.rx.i.eq(self.rx),
        ]
        m.d.comb += [
            uart.tx.data.eq(self._rdr.data),
            uart.tx.ack.eq(self._rdr.valid),
            self._rdr.stall.eq(0),
            self._rdr.addr.eq(curr_byte_addr),
            self._rdr.read_en.eq(do_read),
            do_read.eq(uart.tx.rdy & ~take_break)
        ]

        with m.If(wait.stb):
            m.d.sync += take_break.eq(0)

        with m.If(self._rdr.valid & uart.tx.rdy):
            m.d.sync += curr_byte_addr.eq(curr_byte_addr + 1)

            max_addr = (self.ufm_config["start_page"] +
                        self.ufm_config["num_pages"])*16
            with m.If(curr_byte_addr == max_addr - 1):
                m.d.sync += [
                    curr_byte_addr.eq(self.ufm_config["start_page"]*16),
                    take_break.eq(1)
                ]

        return m


# 1-second wait-timer. Divides by half because the main clock is half the OSCH
# frequency.
class WaitTimer(Elaboratable):
    def __init__(self, freq_mhz):
        self.stb = Signal(1)
        self.freq_mhz = freq_mhz

    def elaborate(self, plat):
        m = Module()

        half_point = int(self.freq_mhz*1e6 // 2)
        cnt = Signal(range(half_point))

        m.d.comb += self.stb.eq(cnt == half_point)

        with m.If(cnt == half_point):
            m.d.sync += cnt.eq(0)
        with m.Else():
            m.d.sync += cnt.eq(cnt + 1)

        return m


class POR(Elaboratable):
    def elaborate(self, plat):
        m = Module()

        cd_por = ClockDomain(reset_less=True)
        cd_sync = ClockDomain()
        m.domains += cd_por, cd_sync

        cnt = Signal(16)
        rst = Signal(1)

        m.d.comb += rst.eq(cnt != 0xffff)
        m.d.comb += [
            ClockSignal("sync").eq(ClockSignal("por")),
            ResetSignal("sync").eq(rst)
        ]

        with m.If(cnt != 0xffff):
            m.d.por += cnt.eq(cnt + 1)

        return m
