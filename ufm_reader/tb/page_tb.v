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
		.sys_clk(clk),
		.sys_rst(rst),
		.tx(tx),
		.rx(1'b1),
		.out_data(data_out),
		.in_data(dummy_rx_data),

		.wr(tx_data_valid),
		.rd(1'b0),
		.tx_empty(tx_ready),
		.rx_empty(dummy_rx_invalid),
		.tx_ov(dummy_tx_ov),
		.rx_ov(dummy_rx_ov)
	);

    reg [5:0] addr;
    wire seq_stb;
    reg seq_stb_seen;
    page_buffer page_buffer(.clk(clk),
                            .rst(rst),
                            .data_seq(rx_data),
                            .addr({9'b0, addr}),
                            .read_en(tx_ready),
                            .flush(1'b0),
                            .seq_valid(rx_valid),
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
