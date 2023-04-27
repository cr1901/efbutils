// `default_nettype none
`include "baudrates.v"

module top(rx, tx, leds [7:0]);
input wire rx;
output wire tx;
output wire [7:0] leds;
parameter BAUDRATE = `B9600;

wire clk, clk_i, rst;
wire [7:0] data_in;
wire reader_ready, tx_ready, stb, ufm_data_valid;

wire tx_data_valid;
wire [7:0] data_out;

assign leds[0] = rx;
assign leds[1] = tx;
assign leds[2] = ~tx_data_valid;
assign leds[3] = ~rst;
// assign leds[7:4] = 4'b1111;

wire [7:0] dummy_rx_data;
wire dummy_rx_valid;
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
	.o_tx_ready(tx_ready),


	/////////////RX ports///////////////
	.i_rx_serial(rx),
	.o_rx_data(dummy_rx_data),
	.o_rx_data_valid(dummy_rx_valid)
);

defparam OSCH_inst.NOM_FREQ = "24.18";	
OSCH OSCH_inst( .STDBY(1'b0 ), 		// 0=Enabled, 1=Disabled also Disabled with Bandgap=OFF
                .OSC(clk_i),
                .SEDSTDBY());		//  this signal is not required if not using SED - see TN1199 for more details.
								
CLKDIVC CLKDIVC_inst(.CLKI(clk_i),
					.CDIVX(clk));
					
por por(.clk(clk),
		.rst(rst));


/* ufm_reader ufm_reader(.clk(clk),
					  .rst(rst),
					  .start(stb),
					  .stall(1'b0),
					  .addr(addr),
					  .data(data_in),
					  .data_stb(ufm_data_valid),
					  .ready(reader_ready)); */

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

wait_timer wait_timer(.clk(clk),
					  .rst(rst),
					  .stb(stb));

/* wire [3:0] dummy_leds;
led_test led_test(.clk(clk),
				  .rst(rst),
				  .stb(stb),
				  .leds({dummy_leds, leds[7:4]})); */


/* assign leds[4] = ~seq_stb_seen;
assign leds[6:5] = ~addr[5:4];
assign leds[7] = ~tx_data_valid; */

reg [3:0] seq_stb_cnt = 0;
assign leds[7:4] = ~addr[3:0];
always @ (posedge clk) begin
	if(rst) begin
		addr <= 6'b0;
		seq_stb_cnt <= 0;
		// seq_stb_seen <= 0;
	end else begin
		if(seq_stb) begin
			seq_stb_cnt <= seq_stb_cnt + 1;
		end
		/* if(seq_stb) begin
			seq_stb_seen <= 1;
		end */

		if(tx_data_valid && tx_ready) begin
			addr <= addr + 6'b1;
			/* if(addr[3:0] == 15) begin
				seq_stb_seen <= 0;
			end */
		end
	end
end
endmodule

module led_test(clk, rst, stb, leds);
	input wire clk;
	input wire rst;
	input wire stb;
	output reg [7:0] leds = 8'b0;
	
	always @ (posedge clk) begin
		if(rst) begin
			leds <= 8'b0;
		end else begin
			if(stb) begin
				leds <= leds + 8'b1;
			end
		end
	end
endmodule

module wait_timer(clk, rst, stb);
	input wire clk;
	input wire rst;
	output wire stb;

	reg [23:0] cnt = 24'b0;
	
	assign stb = (cnt == 24'd12090000);
	
	always @ (posedge clk) begin
		if(rst) begin
			cnt <= 24'b0;
		end else begin
			if(cnt == 24'd12090000) begin
				cnt <= 24'b0;
			end else begin
				cnt <= cnt + 24'b1;
			end
		end
	end
endmodule


module por(clk, rst);
	input wire clk;
	output wire rst;
	
	reg [7:0] cnt = 8'b0;
	
	assign rst = !(cnt == 8'hFF);
	
	always @ (posedge clk) begin
		if(cnt != 8'hFF) begin
			cnt <= cnt + 1'b1;
		end
	end	
endmodule
