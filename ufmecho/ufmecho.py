import os

from nmigen import *
from nmigen_boards.tinyfpga_ax2 import *

from nmigen.build import *
from nmigen_boards.resources import *

class UFMEcho(Elaboratable):
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
        plat.add_resources([UARTResource(0, rx="16", tx="14")])
        uart = plat.request("uart")

        out_data = Signal(8)
        uart_wr = Signal()
        tx_empty = Signal()
        counter = Signal(24)

        page_loaded = Signal()

        cmd = Signal(3)
        ufm_page = Signal(11)
        go = Signal(1)
        busy = Signal(1)

        mem_addr = Signal(4)
        rd_data = Signal(8)

        m = Module()
        m.submodules += self.mk_osch_clk()
        m.submodules += Instance("uart", i_out_data=out_data,
            o_tx=uart.tx, i_rx=Const(0), i_wr=uart_wr, i_rd=Const(0),
            o_tx_empty=tx_empty, i_sys_clk=ClockSignal("osch"),
            i_sys_rst=Const(0))
        m.submodules += Instance("UFM_WB", i_clk_i=ClockSignal("osch"),
            i_rst_n=Const(1), i_cmd=cmd, i_ufm_page=ufm_page, i_GO=go,
            o_BUSY=busy, i_mem_clk=ClockSignal("osch"), i_mem_we=Const(0),
            i_mem_ce=Const(1), i_mem_addr=mem_addr, o_mem_rd_data=rd_data)

        m.d.osch += counter.eq(counter + 1)

        with m.If(counter == 8000000):
            with m.If(~busy & ~page_loaded):
                m.d.comb += go.eq(1)
                m.d.osch += page_loaded.eq(1)

        with m.If(counter == 16000000):
            with m.If(tx_empty & ~busy):
                m.d.comb += uart_wr.eq(1)
                # Data from one cycle ago.
                m.d.osch += out_data.eq(rd_data)
                m.d.osch += mem_addr.eq(mem_addr + 1)

        return m


plat = TinyFPGAAX2Platform()

for dep in ["uart.v", "efb_define_def.v", "EFB_UFM.v", "init.mem",
    "ufm_wb_top.v", "USR_MEM.v"]:
    with open(os.path.join("..", "deps", dep)) as fp:
        plat.add_file(dep, fp)

plan = plat.build(UFMEcho(), do_build=False)
prod = plan.execute_local(run_script=True)
