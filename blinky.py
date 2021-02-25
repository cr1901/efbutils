from nmigen import *
from nmigen_boards.tinyfpga_ax2 import *

from nmigen.build import *
from nmigen_boards.resources import *
# from nmigen.vendor.lattice_machxo2 import *

class Blinky(Elaboratable):
    def __init__(self):
        pass

    def mk_osch_clk(self):
        # Taken from LatticeMachXO2Platform w/ changes not yet upstream.
        clk_i = Signal()
        rst_i = Const(0)
        gsr0 = Signal()
        gsr1 = Signal()
        m = Module()

        m.submodules += [
            Instance("FD1S3AX", p_GSR="DISABLED", i_CK=clk_i, i_D=~rst_i, o_Q=gsr0),
            Instance("FD1S3AX", p_GSR="DISABLED", i_CK=clk_i, i_D=gsr0,   o_Q=gsr1),
            Instance("SGSR", i_CLK=clk_i, i_GSR=gsr1),
        ]

        m.domains += ClockDomain("osch", reset_less=True)
        m.d.comb += ClockSignal("osch").eq(clk_i)
        m.submodules += Instance("OSCH", p_NOM_FREQ="16.63", i_STDBY=Const(0), o_OSC=clk_i, o_SEDSTDBY=Signal())

        return m

    def elaborate(self, plat):
        plat.add_resources(LEDResources(pins="13", invert=False, attrs=Attrs(IO_STANDARD="LVTTL")))
        led = plat.request("led")

        m = Module()
        m.submodules += self.mk_osch_clk()
        counter = Signal(24)
        m.d.comb += led.eq(counter[-1])
        m.d.osch += counter.eq(counter + 1)
        return m

plan = TinyFPGAAX2Platform().build(Blinky(), do_build=False)
prod = plan.execute_local(run_script=True)
