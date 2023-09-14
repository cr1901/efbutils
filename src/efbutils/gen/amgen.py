from dataclasses import dataclass, field, InitVar, asdict

import amaranth_cli
import json
from fusesoc.capi2.generator import Generator
from fusesoc.utils import yaml_fread


def generate(yaml_fn, *, output_file, module_name, module_path, params_cls):
    yaml_file = yaml_fread(yaml_fn)
    gen = Generator(yaml_file)
    cli = AmaranthCliInvocation(output_file, module_name, module_path,
                                generator_cfg=gen.config,
                                params_cls=params_cls)
    amaranth_cli.main(["generate", cli.module_path, "-n",
                       cli.module_name, *cli.params.expand_cli(), "verilog",
                       "-v", cli.output_file])

    files = [{cli.output_file: {"file_type": "verilogSource"}}]
    gen.add_files(files)
    gen.write()


@dataclass
class GeneratorParams:
    def __init__(self, fusesoc_cfg):
        if not hasattr(self, "__annotations__"):
            return

        for k, v in self.__annotations__.items():
            try:
                # TODO: User may wish to flatten a dict into its constituent
                # parameters. Can this be done generically?
                # Right now, dicts get converted to JSON strings and None
                # to JSON "null".
                if not fusesoc_cfg[k] or isinstance(fusesoc_cfg[k], dict):
                    self.__dict__[k] = json.dumps(fusesoc_cfg[k])
                else:
                    self.__dict__[k] = str(fusesoc_cfg[k])
            except KeyError as e:
                raise ValueError("expected input argument {} of type {} not received"  # noqa: E501
                                 .format(k, v)) from e

    def expand_cli(self):
        cli_params = []
        for k, v in asdict(self).items():
            cli_params.extend(["-p", k, v])

        return cli_params


@dataclass
class AmaranthCliInvocation:
    output_file: str
    module_name: str
    module_path: str
    generator_cfg: InitVar[Generator]
    params_cls: InitVar[type]
    params: GeneratorParams = field(init=False)

    def __post_init__(self, generator_cfg, params_cls):
        self.params = params_cls(generator_cfg)


@dataclass(init=False)
class ReaderDemoParams(GeneratorParams):
    num_leds: str
    efb_config: str
    ufm_config: str


@dataclass(init=False)
class EFBParams(GeneratorParams):
    efb_config: str
    ufm_config: str
    tc_config: str
    spi_config: str
    i2c1_config: str
    i2c2_config: str


@dataclass(init=False)
class PageBufferParams(GeneratorParams):
    pass


@dataclass(init=False)
class UFMReaderParams(GeneratorParams):
    pass
