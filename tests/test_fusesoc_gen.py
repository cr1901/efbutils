import efbutils
import pytest
from pathlib import Path
import subprocess
import yaml


# Module: (generator_lib, generator_name)
SUBSTS = {
    "ufm_reader": {
        "depend": ["cr1901:efbutils:ufm_reader"],
        "generator": "ufm_reader_gen",
        "params": {}
    },
    "page_buffer": {
        "depend": ["cr1901:efbutils:page_buffer"],
        "generator": "page_buffer_gen",
        "params": {}
    },
    "efb": {
        "depend": ["cr1901:efbutils:efb"],
        "generator": "efb_gen",
        "params": {
            "efb_config": {"dev_density": "7000L", "wb_clk_freq": 24.18},
            "ufm_config": {"init_mem": "init.mem",
                           "start_page": 2042,
                           "num_pages": 4,
                           "zero_mem": False}
        }
    },
    "demo_lcmxo2_7000he_b_evn": {
        "depend": ["cr1901:efbutils:reader_demo"],
        "generator": "demo_gen",
        "params": {
            "num_leds": 8,
            "efb_config": {"dev_density": "7000L", "wb_clk_freq": 24.18},
            "ufm_config": {"init_mem": "init.mem",
                           "start_page": 2042,
                           "num_pages": 4,
                           "zero_mem": False}
        },
    },
    "lcmxo2_7000he_b_evn": {
        "core_file": "cr1901:efbutils:reader_demo"
    }
}


@pytest.fixture
def fusesoc_init(tmp_path):
    efb_path = Path(efbutils.__file__).resolve().parent.parent.parent / "cores"
    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "library", "add", "efbutils", efb_path])
    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "library", "add", "gentest", tmp_path])


@pytest.fixture
def gentest_core(request):
    core_file = Path(request.module.__file__).parent / "data" / "gentest.core"
    with open(core_file) as f:
        config = yaml.safe_load(f)
    return config


@pytest.mark.parametrize("core", ["page_buffer",
                                  "ufm_reader",
                                  "efb",
                                  "demo_lcmxo2_7000he_b_evn"])
def test_fusesoc_generator(gentest_core, fusesoc_init, tmp_path, core):
    gentest_core["name"] = f"cr1901:efbutils:gentest-{core}:0.0.1"
    gentest_core["filesets"]["generators"]["depend"] = SUBSTS[core]["depend"]
    gentest_core["generate"]["module"]["generator"] = SUBSTS[core]["generator"]
    gentest_core["generate"]["module"]["parameters"] = SUBSTS[core]["params"]

    with open(tmp_path / "gentest.core", 'w') as f:
        yaml.dump(gentest_core, f)

    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "run", "--setup", "--work-root", tmp_path / "build",
                           f"cr1901:efbutils:gentest-{core}"])


# TODO: test_fusesoc_build for open toolchain as EFB support becomes ready.
@pytest.mark.parametrize("core", ["lcmxo2_7000he_b_evn"])
def test_fusesoc_setup(fusesoc_init, tmp_path, core):
    subprocess.check_call(["fusesoc", "--config", tmp_path / "fusesoc.conf",
                           "run", "--setup", "--work-root", tmp_path / "build",
                           "--target", core, SUBSTS[core]["core_file"]])
