from ..amgen import AmaranthGenerator

from ...ufm.reader.demo import Demo


class DemoGenerator(AmaranthGenerator):
    output_file = "demo.v"
    module_name = "top"

    def __init__(self, data=None):
        super().__init__(data)
        if data:
            self.num_leds = self.config.get("num_leds", 1)
            self.efb_config = self.config.get("efb_config", None)
            self.ufm_config = self.config.get("ufm_config", None)

    # Generate a core to be included in another project.
    def create_module(self):
        return Demo(num_leds=self.num_leds,
                    efb_config=self.efb_config,
                    ufm_config=self.ufm_config)


def main(data=None):
    DemoGenerator(data).generate()


if __name__ == "__main__":
    main()
