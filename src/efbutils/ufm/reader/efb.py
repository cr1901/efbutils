from amaranth import Signal, Module, Instance, ClockSignal, ResetSignal
from amaranth.lib.wiring import In, Component

from .sequencer import EfbWishbone


class EFB(Component):
    bus: In(EfbWishbone)

    def __init__(self, *, efb_config, ufm_config, tc_config, spi_config,
                 i2c1_config, i2c2_config):
        super().__init__()
        self.efb_config = efb_config
        self.ufm_config = ufm_config
        self.tc_config = tc_config
        self.spi_config = spi_config
        self.i2c1_config = i2c1_config
        self.i2c2_config = i2c2_config
        self.params = {}
        self.ports = {}

        self.map_default_params()
        self.map_efb_config()
        self.map_ufm_config()
        # self.map_tc_config()
        # self.map_spi_config()
        # self.map_i2c1_config()
        # self.map_i2c2_config()

        self.lo = Signal(1)
        self.hi = Signal(1)

    def elaborate(self, plat):
        m = Module()

        self.map_ports(m)
        m.submodules.efb = Instance("EFB", **self.params, **self.ports)

        return m

    def map_efb_config(self):
        if not self.efb_config:
            return

        self.params.update({
            "p_DEV_DENSITY": self.efb_config["dev_density"],
            "p_EFB_WB_CLK_FREQ": str(self.efb_config["efb_wb_clk_freq"])
        })

    def map_ufm_config(self):
        if not self.ufm_config:
            return

        ufm_end_page = {
            "7000L": 2045,
            "4000L": 766,
            "2000U": 766,
            "2000L": 638,
            "1200U": 638,
            "1200L": 510,
            "640U": 510,
            "640L": 190
        }

        start_page = 0 if self.ufm_config["zero_mem"] else \
            self.ufm_config["start_page"]
        init_pages = ufm_end_page[self.efb_config["dev_density"]] if \
            self.ufm_config["zero_mem"] else self.ufm_config["num_pages"]

        self.params.update({
            "p_UFM_INIT_FILE_NAME": self.ufm_config["init_mem"],
            "p_UFM_INIT_ALL_ZEROS": "ENABLED" if self.ufm_config["zero_mem"] else "DISABLED",  # noqa: E501
            "p_UFM_INIT_START_PAGE": start_page,
            "p_UFM_INIT_PAGES": init_pages,
            "p_EFB_UFM": "ENABLED"
        })

    def map_tc_config(self):
        raise NotImplementedError("Timer config for EFB has not been implemented yet.")  # noqa: E501

    def map_spi_config(self):
        raise NotImplementedError("SPI config for EFB has not been implemented yet.")  # noqa: E501

    def map_i2c1_config(self):
        raise NotImplementedError("I2C1 config for EFB has not been implemented yet.")  # noqa: E501

    def map_i2c2_config(self):
        raise NotImplementedError("I2C2 config for EFB has not been implemented yet.")  # noqa: E501

    def map_default_params(self):
        self.params.update({
            "p_UFM_INIT_FILE_FORMAT": "HEX",
            # TODO: The following 5 params may not be correct defaults.
            # Will correct later.
            "p_UFM_INIT_FILE_NAME": "init.mem",
            "p_UFM_INIT_ALL_ZEROS": "DISABLED",
            "p_UFM_INIT_START_PAGE": 2042,
            "p_UFM_INIT_PAGES": 4,
            "p_DEV_DENSITY": "7000L",
            # Remaining parameters should be correct/default.
            "p_EFB_UFM": "DISABLED",
            "p_TC_ICAPTURE": "DISABLED",
            "p_TC_OVERFLOW": "DISABLED",
            "p_TC_ICR_INT": "OFF",
            "p_TC_OCR_INT": "OFF",
            "p_TC_OV_INT": "OFF",
            "p_TC_TOP_SEL": "OFF",
            "p_TC_RESETN": "ENABLED",
            "p_TC_OC_MODE": "TOGGLE",
            "p_TC_OCR_SET": 32767,
            "p_TC_TOP_SET": 65535,
            "p_GSR": "ENABLED",
            "p_TC_CCLK_SEL": 1,
            "p_TC_MODE": "CTCM",
            "p_TC_SCLK_SEL": "PCLOCK",
            "p_EFB_TC_PORTMODE": "WB",
            "p_EFB_TC": "DISABLED",
            "p_SPI_WAKEUP": "DISABLED",
            "p_SPI_INTR_RXOVR": "DISABLED",
            "p_SPI_INTR_TXOVR": "DISABLED",
            "p_SPI_INTR_RXRDY": "DISABLED",
            "p_SPI_INTR_TXRDY": "DISABLED",
            "p_SPI_SLAVE_HANDSHAKE": "DISABLED",
            "p_SPI_PHASE_ADJ": "DISABLED",
            "p_SPI_CLK_INV": "DISABLED",
            "p_SPI_LSB_FIRST": "DISABLED",
            "p_SPI_CLK_DIVIDER": 1,
            "p_SPI_MODE": "MASTER",
            "p_EFB_SPI": "DISABLED",
            "p_I2C2_WAKEUP": "DISABLED",
            "p_I2C2_GEN_CALL": "DISABLED",
            "p_I2C2_CLK_DIVIDER": 1,
            "p_I2C2_BUS_PERF": "100kHz",
            "p_I2C2_SLAVE_ADDR": "0b1000010",
            "p_I2C2_ADDRESSING": "7BIT",
            "p_EFB_I2C2": "DISABLED",
            "p_I2C1_WAKEUP": "DISABLED",
            "p_I2C1_GEN_CALL": "DISABLED",
            "p_I2C1_CLK_DIVIDER": 1,
            "p_I2C1_BUS_PERF": "100kHz",
            "p_I2C1_SLAVE_ADDR": "0b1000001",
            "p_I2C1_ADDRESSING": "7BIT",
            "p_EFB_I2C1": "DISABLED"
        })

    def map_ports(self, m):
        # For parity with autogenerated Lattice code.
        m.submodules.lo = Instance("VLO", o_Z=self.lo)
        m.submodules.hi = Instance("VHI", o_Z=self.hi)

        # Ports and directions are given in Lattice's FPGA Libraries Reference
        # Guide.
        self.ports.update({
            "i_WBCLKI": ClockSignal(),
            "i_WBRSTI": ResetSignal(),
            "i_WBCYCI": self.bus.cyc,
            "i_WBSTBI": self.bus.stb,
            "i_WBWEI": self.bus.we,
            "i_WBADRI7": self.bus.adr[7],
            "i_WBADRI6": self.bus.adr[6],
            "i_WBADRI5": self.bus.adr[5],
            "i_WBADRI4": self.bus.adr[4],
            "i_WBADRI3": self.bus.adr[3],
            "i_WBADRI2": self.bus.adr[2],
            "i_WBADRI1": self.bus.adr[1],
            "i_WBADRI0": self.bus.adr[0],
            "i_WBDATI7": self.bus.dat_w[7],
            "i_WBDATI6": self.bus.dat_w[6],
            "i_WBDATI5": self.bus.dat_w[5],
            "i_WBDATI4": self.bus.dat_w[4],
            "i_WBDATI3": self.bus.dat_w[3],
            "i_WBDATI2": self.bus.dat_w[2],
            "i_WBDATI1": self.bus.dat_w[1],
            "i_WBDATI0": self.bus.dat_w[0],
            "i_PLL0DATI7": self.lo,
            "i_PLL0DATI6": self.lo,
            "i_PLL0DATI5": self.lo,
            "i_PLL0DATI4": self.lo,
            "i_PLL0DATI3": self.lo,
            "i_PLL0DATI2": self.lo,
            "i_PLL0DATI1": self.lo,
            "i_PLL0DATI0": self.lo,
            "i_PLL0ACKI": self.lo,
            "i_PLL1DATI7": self.lo,
            "i_PLL1DATI6": self.lo,
            "i_PLL1DATI5": self.lo,
            "i_PLL1DATI4": self.lo,
            "i_PLL1DATI3": self.lo,
            "i_PLL1DATI2": self.lo,
            "i_PLL1DATI1": self.lo,
            "i_PLL1DATI0": self.lo,
            "i_PLL1ACKI": self.lo,
            "i_I2C1SCLI": self.lo,
            "i_I2C1SDAI": self.lo,
            "i_I2C2SCLI": self.lo,
            "i_I2C2SDAI": self.lo,
            "i_SPISCKI": self.lo,
            "i_SPIMISOI": self.lo,
            "i_SPIMOSII": self.lo,
            "i_SPISCSN": self.lo,
            "i_TCCLKI": self.lo,
            "i_TCRSTN": self.lo,
            "i_TCIC": self.lo,
            "i_UFMSN": self.hi,  # TODO: Not clear to me what this is for.
            "o_WBDATO7": self.bus.dat_r[7],
            "o_WBDATO6": self.bus.dat_r[6],
            "o_WBDATO5": self.bus.dat_r[5],
            "o_WBDATO4": self.bus.dat_r[4],
            "o_WBDATO3": self.bus.dat_r[3],
            "o_WBDATO2": self.bus.dat_r[2],
            "o_WBDATO1": self.bus.dat_r[1],
            "o_WBDATO0": self.bus.dat_r[0],
            "o_WBACKO": self.bus.ack,
            "o_PLLCLKO": Signal(),
            "o_PLLRSTO": Signal(),
            "o_PLL0STBO": Signal(),
            "o_PLL1STBO": Signal(),
            "o_PLLWEO": Signal(),
            "o_PLLADRO4": Signal(),
            "o_PLLADRO3": Signal(),
            "o_PLLADRO2": Signal(),
            "o_PLLADRO1": Signal(),
            "o_PLLADRO0": Signal(),
            "o_PLLDATO7": Signal(),
            "o_PLLDATO6": Signal(),
            "o_PLLDATO5": Signal(),
            "o_PLLDATO4": Signal(),
            "o_PLLDATO3": Signal(),
            "o_PLLDATO2": Signal(),
            "o_PLLDATO1": Signal(),
            "o_PLLDATO0": Signal(),
            "o_I2C1SCLO": Signal(),
            "o_I2C1SCLOEN": Signal(),
            "o_I2C1SDAO": Signal(),
            "o_I2C1SDAOEN": Signal(),
            "o_I2C2SCLO": Signal(),
            "o_I2C2SCLOEN": Signal(),
            "o_I2C2SDAO": Signal(),
            "o_I2C2SDAOEN": Signal(),
            "o_I2C1IRQO": Signal(),
            "o_I2C2IRQO": Signal(),
            "o_SPISCKO": Signal(),
            "o_SPISCKEN": Signal(),
            "o_SPIMISOO": Signal(),
            "o_SPIMISOEN": Signal(),
            "o_SPIMOSIO": Signal(),
            "o_SPIMOSIEN": Signal(),
            "o_SPIMCSN7": Signal(),
            "o_SPIMCSN6": Signal(),
            "o_SPIMCSN5": Signal(),
            "o_SPIMCSN4": Signal(),
            "o_SPIMCSN3": Signal(),
            "o_SPIMCSN2": Signal(),
            "o_SPIMCSN1": Signal(),
            "o_SPIMCSN0": Signal(),
            "o_SPICSNEN": Signal(),
            "o_SPIIRQO": Signal(),
            "o_TCINT": Signal(),
            "o_TCOC": Signal(),
            "o_WBCUFMIRQ": self.bus.irq,
            "o_CFGWAKE": Signal(),
            "o_CFGSTDBY": Signal()
        })
