import efbutils
import pytest
from pathlib import Path
import string
import subprocess


CORE_FILE = string.Template("""CAPI=2:
name: cr1901:efbutils:gentest-${module}:0.0.1
description: EFBUtils Generator test

filesets:
    generators:
        depend:
            - ${generator_lib}

targets:
  default: &default
    toplevel: top
    filesets: [generators]
    default_tool: diamond
    generate: [${module}]
    tools:
        diamond:
            part: LCMXO2-1200HC-4SG32C


generate:
  ${module}:
    generator: ${generator_name}
    parameters: ${params}
""")

# Module: (generator_lib, generator_name)
SUBSTS = {
    "page_buffer": {
        "module": "page_buffer",
        "generator_lib": "cr1901:efbutils:ufm_reader",
        "generator_name": "page_buffer_gen",
        "params": "{}"
    },
    "demo_lcmxo2_7000he_b_evn": {
        "module": "demo_lcmxo2_7000he_b_evn",
        "generator_lib": "cr1901:efbutils:ufm_reader",
        "generator_name": "demo_gen",
        # Since YAML is whitespace sensitive, put the nested map all on one
        # line for tests.
        "params": "{ num_leds: 8, " +
                  "efb_config: { dev_density: 7000L, efb_wb_clk_freq: 24.18 }, " +  # noqa: E501
                  "ufm_config: { init_mem: init.mem, start_page: 2042, num_pages: 4, zero_mem: false } }"  # noqa: E501
    },
    "lcmxo2_7000he_b_evn": {
        "core_file": "cr1901:efbutils:ufm_reader"
    }
}


@pytest.fixture
def fusesoc_init(tmp_path):
    efb_path = Path(efbutils.__file__).resolve().parent.parent.parent / "cores"
    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "library", "add", "efbutils", efb_path])
    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "library", "add", "gentest", tmp_path])


@pytest.mark.parametrize("core", ["page_buffer", "demo_lcmxo2_7000he_b_evn"])
def test_fusesoc_generator(fusesoc_init, tmp_path, core):
    p = (tmp_path / core).with_suffix(".core")
    p.write_text(CORE_FILE.substitute(SUBSTS[core]))
    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "run", "--setup", "--work-root", tmp_path / "build",
                           f"cr1901:efbutils:gentest-{core}"])


# TODO: test_fusesoc_build for open toolchain as EFB support becomes ready.
@pytest.mark.parametrize("core", ["lcmxo2_7000he_b_evn"])
def test_fusesoc_setup(fusesoc_init, tmp_path, core):
    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "run", "--setup", "--work-root", tmp_path / "build",
                           "--target", core, SUBSTS[core]["core_file"]])
