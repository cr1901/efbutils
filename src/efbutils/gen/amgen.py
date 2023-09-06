from amaranth.back import verilog
from fusesoc.capi2.generator import Generator


class AmaranthGenerator(Generator):
    output_file = "top.v"
    module_name = "top"

    def __init__(self, data=None):
        super().__init__(data)

    def create_module(self):
        raise NotImplementedError("Subclasses are expected to generate an Amaranth module.")  # noqa: E501

    def generate(self):
        (module, ios) = self.create_module()

        with open(self.output_file, "w") as fp:
            fp.write(str(verilog.convert(module,
                                         name=self.module_name,
                                         ports=ios)))

        files = [{self.output_file: {"file_type": "verilogSource"}}]
        self.add_files(files)
        self.write()
