import sys
from pathlib import Path

# Provide path to actual efbutils module for convenience.
sys.path += [str(Path(__file__).resolve().parent.parent / "src")]
from efbutils.gen import amgen

if __name__ == "__main__":
    amgen.generate(sys.argv[1], output_file="EFB.v",
                   module_name="EFBUtils_EFB",
                   module_path="efbutils.ufm.reader.efb:EFB",
                   params_cls=amgen.EFBParams)
