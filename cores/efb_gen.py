import sys
from pathlib import Path
from fusesoc.utils import yaml_fread

# Provide path to actual efbutils module for convenience.
sys.path += [str(Path(__file__).resolve().parent.parent / "src")]
from efbutils.gen import efb  # noqa: E402

if __name__ == "__main__":
    efb.main(yaml_fread(sys.argv[1]))