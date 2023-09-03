from amgen import AmaranthGenerator

from ufm_reader.demo import Demo


class DemoGenerator(AmaranthGenerator):
    output_file = "demo.v"
    module_name = "top"

    def __init__(self):
        super().__init__()
        self.num_leds = self.config.get("num_leds", 1)
        self.efb_config = self.config.get("efb_config", None)
        self.ufm_config = self.config.get("ufm_config", None)

    # Generate a core to be included in another project.
    def create_module(self):
        m = Demo(num_leds=self.num_leds,
                 efb_config=self.efb_config,
                 ufm_config=self.ufm_config)
        ios = [m.tx, m.rx, m.leds]

        return (m, ios)


if __name__ == "__main__":
    DemoGenerator().generate()
