`default_nettype none
`include "baudrates.v"
`timescale 1ns/1ps

module top();
    wire rx;
    wire tx;
    parameter BAUDRATE = 4; // 3 Megabaud UART

    reg clk = 0;
    reg rst = 1;
    wire [7:0] data_in;
    wire reader_ready, tx_ready, stb, ufm_data_valid;

    wire tx_data_valid;
    wire [7:0] data_out;

    reg [7:0] dummy_rx_data;
    reg dummy_rx_valid;
    uart_tranceiver #(.BAUDRATE(BAUDRATE),
                    .TX_FIFO_MODE(0),
                    .RX_FIFO_MODE(0)
    ) uart_transceiver_u0(
        .clk(clk),
        .resetn(~rst),


        /////////////TX ports///////////////
        .i_tx_data(data_out),
        .i_tx_data_valid(tx_data_valid),
        .o_tx_serial(tx),
        .o_tx_ready(tx_ready)


        /////////////RX ports///////////////
        /* .i_rx_serial(rx),
        .o_rx_data(dummy_rx_data),
        .o_rx_data_valid(dummy_rx_valid) */
    );

    reg [5:0] addr;
    wire seq_stb;
    reg seq_stb_seen;
    page_buffer page_buffer(.clk(clk),
                            .rst(rst),
                            .data_seq(dummy_rx_data),
                            .addr({9'b0, addr}),
                            .read_en(tx_ready),
                            .flush(1'b0),
                            .seq_valid(dummy_rx_valid),
                            .data_rand(data_out),
                            .rand_valid(tx_data_valid),
                            .seq_stb(seq_stb));

    always @ (posedge clk) begin
        if(rst) begin
            addr <= 6'b0;
        end else begin
            if(tx_data_valid && tx_ready) begin
                addr <= addr + 6'b1;
            end
        end
    end

    always begin
        clk = #41.66 ~clk;
    end

    task new_data(input [7:0] data); begin
        $display(seq_stb, data, $time);
        while(~seq_stb) begin
            #83.33;
        end

        #(83.33* 2);

        dummy_rx_data <= data;
        dummy_rx_valid <= 1;

        #83.33 dummy_rx_valid <= 0;
    end 
    endtask

    initial begin
        #(83.33 * 20000);
        $display("simulation reached max time!");
        $finish;

        // Any difference?
        /* #20000 begin
            $display("simulation reached max time!");
            $finish;
        end */
    end

    initial begin
        $dumpvars(0);

        #41.66 rst <= 0; #83.33;

        for(integer i = 0; i < 16; i=i+1) begin
            new_data(15 - i);
        end

        #(83.33 * 10)
        for(integer i = 0; i < 16; i=i+1) begin
            new_data(32 - i);
        end

        #(83.33 * 10)
        for(integer i = 0; i < 16; i=i+1) begin
            new_data(48 - i);
        end

        #(83.33 * 10)
        for(integer i = 0; i < 16; i=i+1) begin
            new_data(64 - i);
        end

		#(83.33 * 1000) $finish; 
	end
endmodule
