# `efbutils`

`efbutils` is a set HDL code for easier interfacing to the MachXO2/3 Embedded
Function Block (EFB), written in amaranth and Verilog. More detailed descriptions
will come as the project develops.

## Experiments
In addition to the python package `efbutils`, the following projects
are provided for me to test `amaranth` and MachXO2:

* `blinky`- Test instantiating an `OSCH` as a non-default clock.
* `ufmecho`- A hybrid of amaranth and verilog code to verify I can access
  and read back the `UFM`.

## `ufm_reader`
`ufm_reader` is a [FuseSoC](https://github.com/olofk/fusesoc/)- compatible
core for interfacing to the MachXO2/3 User Flash Memory.

Although the core works, it is not at all ready yet. I currently use it as part of
testing various free tools for MachXO2 ([`nextpnr-machxo2`](https://github.com/YosysHQ/nextpnr/),
[`openFPGALoader`](https://github.com/trabucayre/openFPGALoader), etc).

A quickstart for the [MachXO2 Evaluation Board](https://www.latticesemi.com/products/developmentboardsandkits/machxo2breakoutboard)
may look like the following (use `export PATH=/c/lscc/diamond/3.12/bin/lin64:$PATH`
on Linux systems):

```
fusesoc library add efbutils cores/
export PATH=/c/lscc/diamond/3.12/bin/nt64:$PATH
fusesoc run --target lcmxo2_7000he_b_evn cr1901:efbutils:ufm_reader
```
