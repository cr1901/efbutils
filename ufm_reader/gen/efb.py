from amgen import AmaranthGenerator

from ufm_reader.efb import EFB


class EFBGenerator(AmaranthGenerator):
    output_file = "efb.v"
    module_name = "EFBUtils_EFB"

    def __init__(self):
        super().__init__()
        self.efb_config = self.config.get('efb_config', None)
        self.ufm_config = self.config.get('ufm_config', None)

    # Generate a core to be included in another project.
    def create_module(self):
        m = EFB(efb_config=self.efb_config,
                ufm_config=self.ufm_config,
                tc_config=None,
                spi_config=None,
                i2c1_config=None,
                i2c2_config=None)
        ios = [m.bus.cyc, m.bus.stb, m.bus.we, m.bus.adr, m.bus.dat_w,
               m.bus.dat_r, m.bus.ack, m.bus.irq]

        return (m, ios)


if __name__ == "__main__":
    EFBGenerator().generate()
