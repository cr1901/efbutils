from enum import Enum

from amaranth import Signal, Module, unsigned
from amaranth.lib.data import ArrayLayout, Struct, Union
from amaranth.lib.enum import Enum as EnumWithShape
from amaranth.lib.wiring import Signature, In, Out, Component


class Name(Enum):
    IDLE = 0
    ENABLE_CONFIG = 0x74
    POLL_STATUS = 0x3C
    SET_UFM_ADDR = 0xB4
    READ_UFM = 0xCA
    DISABLE_CONFIG = 0x26
    BYPASS = 0xFF


class ConstantOp(Enum):
    ZEROS = 0x0
    ONE = 0x1
    ENABLE = 0x08_00_00
    ALL_ONES = 0xFF_FF_FF


class DisableRefreshOp(EnumWithShape, shape=unsigned(16)):
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


class SysConfigCmd(Struct):
    cmd: Name
    ops: Operands


class SequencerSignature(Signature):
    def __init__(self):
        return super().__init__({
            "req": Out(1),
            "cmd": Out(SysConfigCmd),
            "done": In(1),
            "op_len": Out(2),  # Temporary, for compatibility with Verilog ports.  # noqa: E501
            "data_len": Out(6),  # Temporary, for compatibility with Verilog ports.  # noqa: E501
            "wr": Out(SeqWriteStreamSignature()),
            "rd": In(SeqReadStreamSignature())
        })


# Currently unused. It'll be used to write to UFM.
class SeqWriteStreamSignature(Signature):
    def __init__(self):
        return super().__init__({
            "data": Out(WriteData),
            "ready": In(1),
            "valid": Out(1)
        })


class SeqReadStreamSignature(Signature):
    def __init__(self):
        return super().__init__({
            "data": Out(8),
            "stb": Out(1),
        })


class EfbWishbone(Signature):
    def __init__(self):
        return super().__init__({
            "cyc": Out(1),
            "stb": Out(1),
            "we": Out(1),
            "adr": Out(8),
            "dat_w": Out(8),
            "dat_r": In(8),
            "ack": In(1)
        })


class Sequencer(Component):
    ctl: In(SequencerSignature())
    efb: Out(EfbWishbone())

    def __init__(self):
        super().__init__()

    def elaborate(self, plat):
        m = Module()

        return m
