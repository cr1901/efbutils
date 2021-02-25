# `efbutils`

`efbutils` is a set HDL code for easier interfacing to the MachXO2 EFB
written in nmigen. More detailed descriptions will come as the project
develops.

## Experiments
In addition to the python package `efbutils`, the following projects
are provided for me to test `nmigen` and MachXO2:

* `blinky`- Test instantiating an `OSCH` as a non-default clock.
* `ufmecho`- A hybrid of nmigen and verilog code to verify I can access
  and read back the `UFM`.
