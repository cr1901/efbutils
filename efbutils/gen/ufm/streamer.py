from ..amgen import AmaranthGenerator

from ...ufm.reader.streamer import Streamer


class StreamerGenerator(AmaranthGenerator):
    output_file = "streamer.v"
    module_name = "streamer"

    def __init__(self):
        super().__init__()

    # Generate a core to be included in another project.
    def create_module(self):
        m = Streamer()
        ios = [m.stream.data, m.stream.addr, m.stream.stb, m.stream.ack,
               m.stream.stall, m.stream.ready, m.efb.cyc, m.efb.stb, m.efb.we,
               m.efb.adr, m.efb.dat_w, m.efb.dat_r, m.efb.ack]

        return (m, ios)


if __name__ == "__main__":
    StreamerGenerator().generate()
