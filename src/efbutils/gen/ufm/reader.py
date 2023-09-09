from ..amgen import AmaranthGenerator

from ...ufm.reader.reader import Reader


class ReaderGenerator(AmaranthGenerator):
    output_file = "reader.v"
    module_name = "reader"

    def __init__(self, data=None):
        super().__init__(data)

    # Generate a core to be included in another project.
    def create_module(self):
        return Reader()


def main(data=None):
    ReaderGenerator(data).generate()


if __name__ == "__main__":
    main()
