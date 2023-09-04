`default_nettype none
`timescale 1ns/1ps

module top();
    wire tx;

    reg clk = 0;
    reg rst = 1;
    wire [7:0] data_in;
    wire reader_ready, tx_ready, stb, ufm_data_valid;

    wire tx_data_valid;
    wire [7:0] data_out;

    reg [7:0] rx_data;
    reg rx_valid;
    
    wire [7:0] dummy_rx_data;
    wire dummy_rx_invalid, dummy_tx_ov, dummy_rx_ov;

    uart uart(
		.clk(clk),
		.rst(rst),
		.tx(tx),
		.rx(1'b1),
		.tx_data(data_out),
		.rx_data(dummy_rx_data),
		.tx_rdy(tx_ready),
		.rx_rdy(dummy_rx_invalid),
		.tx_ack(tx_data_valid),
		.rx_ack(1'b0)
	);

    reg [5:0] addr;
    wire seq_stb;
    reg seq_stb_seen;
    wire [10:0] dummy_seq_addr;

    page_buffer page_buffer(.clk(clk),
                            .rst(rst),
                            .seq__data(rx_data),
                            .rand__addr({9'b0, addr}),
                            .rand__read_en(tx_ready),
                            .rand__flush(1'b0),
                            .seq__ack(rx_valid),
                            .rand__data(data_out),
                            .rand__valid(tx_data_valid),
                            .seq__stb(seq_stb),
                            .seq__addr(dummy_seq_addr));

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

        rx_data <= data;
        rx_valid <= 1;

        #83.33 rx_valid <= 0;
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
