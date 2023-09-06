from .amgen import AmaranthGenerator

from ..ufm.reader.page_buffer import PageBuffer


class PageBufferGenerator(AmaranthGenerator):
    output_file = "page_buffer.v"
    module_name = "page_buffer"

    def __init__(self, data=None):
        super().__init__(data)

    # Generate a core to be included in another project.
    def create_module(self):
        return PageBuffer()


def main(data=None):
    PageBufferGenerator(data).generate()


if __name__ == "__main__":
    main()
