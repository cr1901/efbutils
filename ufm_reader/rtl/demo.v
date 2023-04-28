module  top #(parameter OSCH_FREQ="24.18") (rx, tx, leds [7:0]);
	input wire rx;
	output wire tx;
	output wire [7:0] leds;

	wire clk, clk_i, rst;
	wire [7:0] data_in;
	wire reader_ready, tx_ready, wait_stb, seq_stb,
		ufm_data_valid, tx_data_valid, do_read;

	wire [7:0] data_out;
	reg [5:0] addr;
	reg take_break;

	assign leds[0] = rx;
	assign leds[1] = tx;
	assign leds[2] = ~tx_data_valid;
	assign leds[3] = ~ufm_data_valid;
	assign leds[4] = ~seq_stb;
	assign leds[5] = ~do_read;
	assign leds[7:6] = ~addr[5:4];

	wire [7:0] dummy_rx_data;
	wire dummy_rx_valid, dummy_tx_ov, dummy_rx_ov;

	uart uart(
		.sys_clk(clk),
		.sys_rst(rst),
		.tx(tx),
		.rx(rx),
		.out_data(data_out),
		.in_data(dummy_rx_data),

		.wr(tx_data_valid),
		.rd(1'b0),
		.tx_empty(tx_ready),
		.rx_empty(dummy_rx_valid),
		.tx_ov(dummy_tx_ov),
		.rx_ov(dummy_rx_ov)
	);

	defparam OSCH_inst.NOM_FREQ = OSCH_FREQ;	
	OSCH OSCH_inst( .STDBY(1'b0 ), 		// 0=Enabled, 1=Disabled also Disabled with Bandgap=OFF
					.OSC(clk_i),
					.SEDSTDBY());		//  this signal is not required if not using SED - see TN1199 for more details.
									
	CLKDIVC CLKDIVC_inst(.CLKI(clk_i),
						.CDIVX(clk));
						
	por por(.clk(clk),
			.rst(rst));


	wire [10:0] flash_addr;
	assign flash_addr = 11'd2042 + addr[5:4];
	ufm_reader ufm_reader(.clk(clk),
						  .rst(rst),
						  .start(seq_stb),
						  .stall(1'b0),
						  .addr(flash_addr),
						  .data(data_in),
						  .data_stb(ufm_data_valid),
						  .ready(reader_ready));


	assign do_read = tx_ready && !take_break;
	page_buffer page_buffer(.clk(clk),
							.rst(rst),
							.data_seq(data_in),
							.addr({9'b0, addr}),
							.read_en(do_read),
							.flush(1'b0),
							.seq_valid(ufm_data_valid),
							.data_rand(data_out),
							.rand_valid(tx_data_valid),
							.seq_stb(seq_stb));

	defparam wait_timer.OSCH_FREQ = OSCH_FREQ;
	wait_timer wait_timer(.clk(clk),
						  .rst(rst),
						  .stb(wait_stb));

	always @ (posedge clk) begin
		if(rst) begin
			addr <= 6'b0;
			take_break <= 0;
		end else begin
			if(wait_stb) begin
				take_break <= 0;
			end
			
			if(tx_data_valid && tx_ready) begin
				addr <= addr + 6'b1;

				if(addr == 6'd63) begin
					take_break <= 1;
				end
			end
		end
	end
endmodule



module wait_timer #(parameter OSCH_FREQ="24.18") (clk, rst, stb);
	input wire clk;
	input wire rst;
	output wire stb;

	reg [31:0] cnt = 32'b0;
	
	assign stb = (cnt == osch_str_to_int(OSCH_FREQ) / 2);
	
	always @ (posedge clk) begin
		if(rst) begin
			cnt <= 32'b0;
		end else begin
			if(cnt == osch_str_to_int(OSCH_FREQ) / 2) begin
				cnt <= 32'b0;
			end else begin
				cnt <= cnt + 32'b1;
			end
		end
	end

	function [31:0] osch_str_to_int(input [47:0] freq);
		case(freq)
			"12.09": osch_str_to_int = 32'd12090000;
			"24.18": osch_str_to_int = 32'd24180000;
		endcase
	endfunction
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
