from .amgen import AmaranthGenerator

from amaranth_stdio import serial


class UartGenerator(AmaranthGenerator):
    output_file = "uart.v"
    module_name = "uart"

    def __init__(self):
        super().__init__()
        self.divisor = self.config.get('divisor', None)

    # Generate a core to be included in another project.
    def create_module(self):
        m = serial.AsyncSerial(divisor=self.divisor)

        m.tx.o.name = "tx"
        m.tx.ack.name = "tx_ack"
        m.tx.rdy.name = "tx_rdy"
        m.tx.data.name = "tx_data"
        m.rx.i.name = "rx"
        m.rx.ack.name = "rx_ack"
        m.rx.rdy.name = "rx_rdy"
        m.rx.data.name = "rx_data"

        ios = [m.tx.o, m.rx.i, m.tx.ack, m.tx.rdy, m.tx.data,
               m.rx.ack, m.rx.rdy, m.rx.data]

        return (m, ios)


if __name__ == "__main__":
    UartGenerator().generate()
