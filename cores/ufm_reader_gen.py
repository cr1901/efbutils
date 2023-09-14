import sys
from pathlib import Path

# Provide path to actual efbutils module for convenience.
sys.path += [str(Path(__file__).resolve().parent.parent / "src")]
from efbutils.gen import amgen

if __name__ == "__main__":
    amgen.generate(sys.argv[1], output_file="reader.v",
                   module_name="reader",
                   module_path="efbutils.ufm.reader.reader:Reader",
                   params_cls=amgen.UFMReaderParams)
