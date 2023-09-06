from .amgen import AmaranthGenerator

from ..ufm.reader.page_buffer import PageBuffer


class PageBufferGenerator(AmaranthGenerator):
    output_file = "page_buffer.v"
    module_name = "page_buffer"

    def __init__(self, data=None):
        super().__init__(data)

    # Generate a core to be included in another project.
    def create_module(self):
        m = PageBuffer()
        ios = [m.rand.data, m.rand.addr, m.rand.read_en,
               m.rand.flush, m.rand.valid, m.seq.data,
               m.seq.addr, m.seq.stb, m.seq.ack]

        return (m, ios)


def main(data=None):
    PageBufferGenerator(data).generate()


if __name__ == "__main__":
    main()
