import os.path
from dataclasses import dataclass
import json
from pathlib import Path

from amaranth import Signal, Module, Instance, ClockSignal, ResetSignal, C
from amaranth.lib.wiring import In, Component

from .sequencer import EfbWishbone


@dataclass
class BaseConfig:
    """Base class to create EFB config classes.

    The constructor can create configs from a JSON string, dict, or
    kwargs, and verifies the arguments against subclass' annotations."""

    def __init__(self, *args, **kwargs):
        self.enabled = False

        if args and isinstance(args[0], str):
            argdict = json.loads(args[0])

            # If "null", the component is disabled. Replace with empty
            # dict for later.
            if not argdict:
                argdict = {}
        elif args and isinstance(args[0], dict):
            argdict = args[0]
        else:
            argdict = kwargs

        # if "empty", the component is disabled.
        if not argdict:
            return

        self.enabled = True
        for k, v in self.__annotations__.items():
            try:
                self.__dict__[k] = argdict[k]
            except KeyError as e:
                raise ValueError("expected input argument {} of type {} not received"  # noqa: E501
                                 .format(k, v)) from e

    # Truth value indicates whether component is enabled or not.
    def __bool__(self):
        return self.enabled


@dataclass(init=False)
class UFMConfig(BaseConfig):
    """UFM Config, used by the EFB class."""
    init_mem: Path
    zero_mem: bool
    start_page: int
    num_pages: int


@dataclass(init=False)
class EFBConfig(BaseConfig):
    """Base EFB Config, used by the EFB class."""
    dev_density: str
    wb_clk_freq: str


@dataclass(init=False)
class TCConfig(BaseConfig):
    """Timer Config, used by the EFB class."""


@dataclass(init=False)
class SPIConfig(BaseConfig):
    """SPI Config, used by the EFB class."""


@dataclass(init=False)
class I2C1Config(BaseConfig):
    """I2C1 Config, used by the EFB class."""


@dataclass(init=False)
class I2C2Config(BaseConfig):
    """I2C2 Config, used by the EFB class."""


class SimpleUFMConfig(UFMConfig):
    """Automatically configure UFM Parameters based on input file.

    End of file will automatically be placed at top of UFM, growing
    downward."""

    end_page = {
        "7000L": 2045,
        "4000L": 766,
        "2000U": 766,
        "2000L": 638,
        "1200U": 638,
        "1200L": 510,
        "640U": 510,
        "640L": 190
    }

    def __init__(self, *, filename, device):
        filename = Path(filename) if filename else ""
        zero_mem = bool(filename)

        if filename and not filename.exists():
            raise FileNotFoundError(filename)

        if filename:
            if os.path.getsize(filename) % 16 == 0:
                num_pages = os.path.getsize(self.filename) // 16
            else:
                num_pages = os.path.getsize(self.filename) // 16 + 1
        else:
            num_pages = self.end_page[device] + 1

        if zero_mem:
            start_page = 0
        else:
            start_page = self.end_page[self.device] - num_pages + 1

        super().__init__(init_mem=filename,
                         zero_mem=zero_mem,
                         start_page=start_page,
                         num_pages=num_pages)


class EFB(Component):
    """EFB class that can be used with Amaranth's CLI to generate Verilog.

    Create JSON dictionaries on the command-line for each "-p" parameter
    to "amaranth generate", e.g.::

        amaranth generate efbutils.ufm.reader.efb:EFB \
        -p efb_config '{ "dev_density": "7000L", "wb_clk_freq": "12.08" }' \
        -p ufm_config '{ "init_mem": null, "zero_mem": true, "start_page": 0, "num_pages": 2046}' \
        -p tc_config null \
        -p spi_config null \
        -p i2c1_config null \
        -p i2c2_config null \
        verilog -v -

    All parameters must be included. You can disable parts of the EFB by using
    a JSON "null" for the relevant config.
    """  # noqa: E501
    bus: In(EfbWishbone)

    def __init__(self, *, efb_config: EFBConfig,
                 ufm_config: UFMConfig,
                 tc_config: TCConfig,
                 spi_config: SPIConfig,
                 i2c1_config: I2C1Config,
                 i2c2_config: I2C2Config):
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
        self.map_tc_config()
        self.map_spi_config()
        self.map_i2c1_config()
        self.map_i2c2_config()

    def elaborate(self, plat):
        m = Module()

        self.map_ports(m)
        m.submodules.efb = Instance("EFB", **self.params, **self.ports)

        return m

    def map_efb_config(self):
        if not self.efb_config:
            raise ValueError("an EFB Config must be provided")

        self.params.update({
            "p_DEV_DENSITY": self.efb_config.dev_density,
            "p_EFB_WB_CLK_FREQ": self.efb_config.wb_clk_freq
        })

    def map_ufm_config(self):
        if not self.ufm_config:
            return

        self.params.update({
            "p_UFM_INIT_FILE_NAME": self.ufm_config.init_mem if self.ufm_config.init_mem else "",  # noqa: E501  # .UFM_INIT_FILE_NAME({0{1'b0}}) ?!
            "p_UFM_INIT_ALL_ZEROS": "ENABLED" if self.ufm_config.zero_mem else "DISABLED",  # noqa: E501
            "p_UFM_INIT_START_PAGE": self.ufm_config.start_page,
            "p_UFM_INIT_PAGES": self.ufm_config.num_pages,
            "p_EFB_UFM": "ENABLED"
        })

    def map_tc_config(self):
        if not self.tc_config:
            return

        raise NotImplementedError("Timer config for EFB has not been implemented yet.")  # noqa: E501

    def map_spi_config(self):
        if not self.spi_config:
            return

        raise NotImplementedError("SPI config for EFB has not been implemented yet.")  # noqa: E501

    def map_i2c1_config(self):
        if not self.i2c1_config:
            return

        raise NotImplementedError("I2C1 config for EFB has not been implemented yet.")  # noqa: E501

    def map_i2c2_config(self):
        if not self.i2c2_config:
            return

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
            "i_PLL0DATI7": C(0),
            "i_PLL0DATI6": C(0),
            "i_PLL0DATI5": C(0),
            "i_PLL0DATI4": C(0),
            "i_PLL0DATI3": C(0),
            "i_PLL0DATI2": C(0),
            "i_PLL0DATI1": C(0),
            "i_PLL0DATI0": C(0),
            "i_PLL0ACKI": C(0),
            "i_PLL1DATI7": C(0),
            "i_PLL1DATI6": C(0),
            "i_PLL1DATI5": C(0),
            "i_PLL1DATI4": C(0),
            "i_PLL1DATI3": C(0),
            "i_PLL1DATI2": C(0),
            "i_PLL1DATI1": C(0),
            "i_PLL1DATI0": C(0),
            "i_PLL1ACKI": C(0),
            "i_I2C1SCLI": C(0),
            "i_I2C1SDAI": C(0),
            "i_I2C2SCLI": C(0),
            "i_I2C2SDAI": C(0),
            "i_SPISCKI": C(0),
            "i_SPIMISOI": C(0),
            "i_SPIMOSII": C(0),
            "i_SPISCSN": C(0),
            "i_TCCLKI": C(0),
            "i_TCRSTN": C(0),
            "i_TCIC": C(0),
            "i_UFMSN": C(1),  # TODO: Not clear to me what this is for.
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
