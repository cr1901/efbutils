from ..amgen import AmaranthGenerator

from ...ufm.reader.reader import Reader


class ReaderGenerator(AmaranthGenerator):
    output_file = "reader.v"
    module_name = "reader"

    def __init__(self):
        super().__init__()

    # Generate a core to be included in another project.
    def create_module(self):
        return Reader()


if __name__ == "__main__":
    ReaderGenerator().generate()
