from amgen import AmaranthGenerator

from ufm_reader.reader import Reader


class ReaderGenerator(AmaranthGenerator):
    output_file = "reader.v"
    module_name = "reader"

    def __init__(self):
        super().__init__()

    # Generate a core to be included in another project.
    def create_module(self):
        m = Reader()
        ios = [m.bus.data, m.bus.addr, m.bus.read_en, m.bus.valid,
               m.bus.stall, m.efb.cyc, m.efb.stb, m.efb.we, m.efb.adr,
               m.efb.dat_w, m.efb.dat_r, m.efb.ack]

        return (m, ios)


if __name__ == "__main__":
    ReaderGenerator().generate()
