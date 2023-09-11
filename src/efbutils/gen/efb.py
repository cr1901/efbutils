from .amgen import AmaranthGenerator

from ..ufm.reader.efb import EFB, EFBConfig, UFMConfig, TCConfig, SPIConfig, \
    I2C1Config, I2C2Config


class EFBGenerator(AmaranthGenerator):
    output_file = "efb.v"
    module_name = "EFBUtils_EFB"

    def __init__(self, data=None):
        super().__init__(data)
        self.efb_config = self.config.get("efb_config", None)
        self.ufm_config = self.config.get("ufm_config", None)
        self.tc_config = self.config.get("tc_config", None)
        self.spi_config = self.config.get("spi_config", None)
        self.i2c1_config = self.config.get("i2c1_config", None)
        self.i2c2_config = self.config.get("i2c2_config", None)

    # Generate a core to be included in another project.
    def create_module(self):
        return EFB(efb_config=EFBConfig(self.efb_config),
                   ufm_config=UFMConfig(self.ufm_config),
                   tc_config=TCConfig(self.tc_config),
                   spi_config=SPIConfig(self.spi_config),
                   i2c1_config=I2C1Config(self.i2c1_config),
                   i2c2_config=I2C2Config(self.i2c2_config))


def main(data=None):
    EFBGenerator(data).generate()


if __name__ == "__main__":
    main()
