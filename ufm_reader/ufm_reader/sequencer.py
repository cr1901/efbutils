from amaranth import Signal, Module, unsigned
from amaranth.lib.data import ArrayLayout, Struct, Union, View
from amaranth.lib.enum import IntEnum
from amaranth.lib.wiring import Signature, In, Out, Component


class Name(IntEnum):
    IDLE = 0
    ENABLE_CONFIG = 0x74
    POLL_STATUS = 0x3C
    SET_UFM_ADDR = 0xB4
    READ_UFM = 0xCA
    DISABLE_CONFIG = 0x26
    BYPASS = 0xFF


class ConstantOp(IntEnum):
    ZEROS = 0x0
    ONE = 0x1
    ENABLE = 0x08_00_00
    ALL_ONES = 0xFF_FF_FF


class DisableRefreshOp(IntEnum, shape=unsigned(16)):
    ZEROS = 0x0


class ReadUfmOp(Struct):
    pages: unsigned(16)
    _1: unsigned(4)
    port: unsigned(1)
    _2: unsigned(3)


class Operands(Union):
    constant: ConstantOp
    read_ufm: ReadUfmOp
    disable: DisableRefreshOp


class SetUfmAddrData(Struct):
    pages: unsigned(16)
    _1: unsigned(14)
    space: unsigned(1)
    _2: unsigned(1)


# All reads are streaming. Writes > 32 bits use streams.
class WriteData(Union):
    stream: unsigned(8)
    set_ufm_addr: SetUfmAddrData


class StatusRegisterByte(Struct):
    _1: unsigned(4)
    busy: unsigned(1)
    status: unsigned(1)
    _2: unsigned(2)


class ReadData(Union):
    stream: unsigned(8)
    status: StatusRegisterByte


class SysConfigCmd(Struct):
    cmd: Name
    ops: Operands


# Currently ready/valid unused. It'll be used to write to UFM.
SeqWriteStreamSignature = Signature({
    "data": Out(WriteData),
    "ready": In(1),
    "valid": Out(1)
})

SeqReadStreamSignature = Signature({
    "data": Out(ReadData),
    "stb": Out(1)
})

SequencerSignature = Signature({
    "req": Out(1),
    "cmd": Out(SysConfigCmd),
    "done": In(1),
    "op_len": Out(2),  # Temporary, for compatibility with Verilog ports.  # noqa: E501
    "data_len": Out(6),  # Temporary, for compatibility with Verilog ports.  # noqa: E501
    "xfer_is_wr": Out(1),  # Temporary, for compatibility with Verilog ports.  # noqa: E501
    "wr": Out(SeqWriteStreamSignature),
    "rd": In(SeqReadStreamSignature)
})

EfbWishbone = Signature({
    "cyc": Out(1),
    "stb": Out(1),
    "we": Out(1),
    "adr": Out(8),
    "dat_w": Out(8),
    "dat_r": In(8),
    "ack": In(1)
})


class Sequencer(Component):
    ctl: In(SequencerSignature)
    efb: Out(EfbWishbone)

    def __init__(self):
        super().__init__()

    def elaborate(self, plat):
        m = Module()
        curr_op = Signal(2)
        curr_data = Signal(6)

        def next_state_if_asserted(stim, state):
            with m.If(stim):
                m.next = state

        def wb_write():
            m.d.comb += [
                self.efb.cyc.eq(1),
                self.efb.stb.eq(1),
                self.efb.we.eq(1),
            ]

        def wb_read():
            m.d.comb += [
                self.efb.cyc.eq(1),
                self.efb.stb.eq(1),
            ]

        def wb_data_slice_ops():
            op_view = View(ArrayLayout(8, 3), self.ctl.cmd.ops)

            with m.Switch(curr_op):
                with m.Case(0):
                    m.d.comb += self.efb.dat_w.eq(op_view[2])
                with m.Case(1):
                    m.d.comb += self.efb.dat_w.eq(op_view[1])
                with m.Case(2):
                    m.d.comb += self.efb.dat_w.eq(op_view[0])
                with m.Default():
                    pass

        def wb_data_slice_data():
            data_view = View(ArrayLayout(8, 4), self.ctl.wr.data)

            with m.Switch(curr_data):
                with m.Case(0):
                    m.d.comb += self.efb.dat_w.eq(data_view[3])
                with m.Case(1):
                    m.d.comb += self.efb.dat_w.eq(data_view[2])
                with m.Case(2):
                    m.d.comb += self.efb.dat_w.eq(data_view[1])
                with m.Case(3):
                    m.d.comb += self.efb.dat_w.eq(data_view[0])
                with m.Default():
                    pass

        with m.FSM() as fsm:  # noqa: F841
            with m.State("IDLE"):
                next_state_if_asserted(self.ctl.req, "WB_ENABLE_1")

            with m.State("WB_ENABLE_1"):
                wb_write()
                m.d.comb += [
                    self.efb.dat_w.eq(0x80),
                    self.efb.adr.eq(0x70)
                ]

                next_state_if_asserted(self.efb.ack, "WB_ENABLE_2")

            with m.State("WB_ENABLE_2"):
                m.d.comb += self.efb.adr.eq(0x70)

                m.next = "WB_CMD_1"

            with m.State("WB_CMD_1"):
                wb_write()
                m.d.comb += [
                    self.efb.dat_w.eq(self.ctl.cmd),
                    self.efb.adr.eq(0x71)
                ]

                next_state_if_asserted(self.efb.ack, "WB_CMD_2")

            with m.State("WB_CMD_2"):
                m.d.comb += [
                    self.efb.dat_w.eq(self.ctl.cmd),
                    self.efb.adr.eq(0x71)
                ]

                with m.If(self.ctl.op_len > 0):
                    m.next = "WB_OPERAND_1"
                with m.Elif(self.ctl.data_len > 0):
                    m.next = "WB_DATA_1"
                with m.Else():
                    m.next = "WB_DISABLE_1"

            with m.State("WB_OPERAND_1"):
                wb_write()
                wb_data_slice_ops()
                m.d.comb += self.efb.adr.eq(0x71)

                next_state_if_asserted(self.efb.ack, "WB_OPERAND_2")

            with m.State("WB_OPERAND_2"):
                wb_data_slice_ops()
                m.d.comb += self.efb.adr.eq(0x71)

                with m.If(curr_op < self.ctl.op_len - 1):
                    m.d.sync += curr_op.eq(curr_op + 1)
                with m.Else():
                    m.d.sync += curr_op.eq(0)

                with m.If(curr_op < self.ctl.op_len - 1):
                    m.next = "WB_OPERAND_1"
                with m.Elif(self.ctl.data_len > 0):
                    m.next = "WB_DATA_1"
                with m.Else():
                    m.next = "WB_DISABLE_1"

            with m.State("WB_DATA_1"):
                wb_data_slice_data()
                with m.If(self.ctl.xfer_is_wr):
                    wb_write()
                    m.d.comb += self.efb.adr.eq(0x71)
                with m.Else():
                    wb_read()
                    m.d.comb += self.efb.adr.eq(0x73)

                with m.If(self.efb.ack):
                    m.d.sync += self.ctl.rd.data.eq(self.efb.dat_r)

                next_state_if_asserted(self.efb.ack, "WB_DATA_2")

            with m.State("WB_DATA_2"):
                wb_data_slice_data()
                with m.If(self.ctl.xfer_is_wr):
                    m.d.comb += self.efb.adr.eq(0x71)
                with m.Else():
                    m.d.comb += self.efb.adr.eq(0x73)
                m.d.comb += self.ctl.rd.stb.eq(1)

                with m.If(curr_data < self.ctl.data_len - 1):
                    m.d.sync += curr_data.eq(curr_data + 1)
                with m.Else():
                    m.d.sync += curr_data.eq(0)

                with m.If(curr_data < self.ctl.data_len - 1):
                    m.next = "WB_DATA_1"
                with m.Else():
                    m.next = "WB_DISABLE_1"

            with m.State("WB_DISABLE_1"):
                wb_write()
                m.d.comb += self.efb.adr.eq(0x70)

                next_state_if_asserted(self.efb.ack, "WB_DISABLE_2")

            with m.State("WB_DISABLE_2"):
                m.next = "IDLE"
                m.d.comb += self.efb.adr.eq(0x70)
                m.d.comb += self.ctl.done.eq(1)

                next_state_if_asserted(self.ctl.req, "WB_ENABLE_1")

        return m
