from amaranth import Signal, Module, Elaboratable, ClockDomain, \
    ClockSignal, ResetSignal, Instance, C
from amaranth.lib.data import ArrayLayout
from amaranth.lib.wiring import Signature, In, Out, Component
from amaranth_stdio import serial

from .efb import EFB
from .reader import Reader


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

    def elaborate(self, plat):
        m = Module()
        m.domains += ClockDomain("cd_por2x", reset_less=True)

        divisor = int((self.efb_config["efb_wb_clk_freq"] * 1e6) // 9600)
        m.submodules.por = POR()
        m.submodules.serial = serial.AsyncSerial(divisor=divisor)
        m.submodules.clkdiv = Instance("CLKDIVC",
                                       i_CLKI=ClockSignal("por2x"),
                                       o_CDIVX=ClockSignal("por"))
        m.submodules.osch = \
            Instance("OSCH",
                     p_NOM_FREQ=self.efb_config["efb_wb_clk_freq"],
                     i_STDBY=C(0),
                     o_OSC=ClockSignal("por2x"))
        m.submodules.wait = wait = WaitTimer(self.efb_config["efb_wb_clk_freq"])

        cnt = Signal(8)

        m.d.comb += [self.leds.eq(cnt)]

        with m.If(wait.stb):
            m.d.sync += cnt.eq(cnt+1)

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
