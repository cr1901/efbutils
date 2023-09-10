import pytest
import amaranth_cli


MODNAME = {
    "page_buffer": "efbutils.ufm.reader.page_buffer:PageBuffer",
    "ufm_reader": "efbutils.ufm.reader.reader:Reader",
    "efb": "efbutils.ufm.reader.efb:VerilogEFB",
    "demo_lcmxo2_7000he_b_evn": "efbutils.ufm.reader.demo:VerilogDemo",
}
PARAMS = {
    "page_buffer": [],
    "ufm_reader": [],
    "efb": [
        ("efb_config", '{ "dev_density": "7000L", "wb_clk_freq": 12.08 }'),
        ("ufm_config", '{ "init_mem": null, "zero_mem": true, "start_page": 0, "num_pages": 2046}')  # noqa: E501
    ],
    "demo_lcmxo2_7000he_b_evn": [
        ("num_leds", "8"),
        ("efb_config", '{ "dev_density": "7000L", "wb_clk_freq": 12.08 }'),
        ("ufm_config", '{ "init_mem": null, "zero_mem": true, "start_page": 0, "num_pages": 2046}')  # noqa: E501
    ]
}


@pytest.fixture
def full_cli(request, tmp_path):
    flat_params = (p for p_tup in PARAMS[request.param] for p in ("-p",) + p_tup)  # noqa: E501
    return ["generate", MODNAME[request.param], *flat_params,
            "verilog", "-v", str((tmp_path / request.param).with_suffix(".v"))]


@pytest.mark.parametrize("full_cli", ["page_buffer", "ufm_reader", "efb",
                                      "demo_lcmxo2_7000he_b_evn"],
                         indirect=True)
def test_amaranth_verilog_generation(full_cli):
    amaranth_cli.main(full_cli)
