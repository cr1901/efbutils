import importlib
from pathlib import Path
import sys

from fusesoc.utils import yaml_fread

# Provide path to actual efbutils module for convenience.
sys.path += [str(Path(__file__).resolve().parent.parent)]

generator_to_module_map = {
    ("cr1901", "efbutils", "ufm_reader-demo_lcmxo2_7000he_b_evn"):
        "efbutils.gen.ufm.demo"
}


if __name__ == "__main__":
    data = yaml_fread(sys.argv[1])
    vlnv = data.get("vlnv")
    vendor, lib, name, _version = vlnv.split(":")[:]

    gen_mod = importlib.import_module(generator_to_module_map[vendor, lib, name])  # noqa: E501
    gen_mod.main(data)
