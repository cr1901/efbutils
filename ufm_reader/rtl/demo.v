module  top #(parameter osch_freq="24.18", parameter init_mem="init.mem",
	parameter zero_mem=0, parameter start_offset=2042*16, parameter size=64,
	parameter device="7000L")
 	(rx, tx, leds);
	input wire rx;
	output wire tx;
	output wire [7:0] leds;

	// {START, END}_BYTE not currently needed, kept just in case.
	localparam START_PAGE = start_page(start_offset);
	localparam START_BYTE = start_byte(start_offset);
	localparam NUM_PAGES = num_pages(size);
	localparam END_BYTE = end_byte(start_offset, size);
	localparam USED_ADDR_BUS_WIDTH = $clog2(NUM_PAGES) + 4;

	wire clk, clk_i, rst;
	wire [7:0] data_in;
	wire reader_ready, tx_ready, wait_stb, seq_stb,
		ufm_data_valid, tx_data_valid, do_read;

	// WB EFB connections.
	wire wb_cyc_o;
	wire wb_stb_o;
	wire wb_we_o;
	wire [7:0] wb_adr_o; 
	wire [7:0] wb_dat_i;
	wire [7:0] wb_dat_o;
	wire wb_ack_i;

	wire [7:0] data_out;
	reg [14:0] curr_byte_addr;
	reg take_break;

	assign leds[0] = rx;
	assign leds[1] = tx;
	assign leds[2] = ~tx_data_valid;
	assign leds[3] = ~ufm_data_valid;
	assign leds[4] = ~seq_stb;
	assign leds[5] = ~do_read;
	assign leds[7:6] = ~curr_byte_addr[USED_ADDR_BUS_WIDTH - 1:USED_ADDR_BUS_WIDTH - 2];

	wire [7:0] dummy_rx_data;
	wire dummy_rx_valid, dummy_tx_ov, dummy_rx_ov;

	uart uart(
		.clk(clk),
		.rst(rst),
		.tx(tx),
		.rx(rx),
		.tx_data(data_out),
		.rx_data(dummy_rx_data),
		.tx_rdy(tx_ready),
		.rx_rdy(dummy_rx_valid),
		.tx_ack(tx_data_valid),
		.rx_ack(1'b0)
	);

	defparam OSCH_inst.NOM_FREQ = osch_freq;	
	OSCH OSCH_inst( .STDBY(1'b0 ), 		// 0=Enabled, 1=Disabled also Disabled with Bandgap=OFF
					.OSC(clk_i),
					.SEDSTDBY());		//  this signal is not required if not using SED - see TN1199 for more details.

	// TODO: Does not exist on 640 parts.
	CLKDIVC CLKDIVC_inst(.CLKI(clk_i),
						.CDIVX(clk));
						
	por por(.clk(clk),
			.rst(rst));

	wire dummy_irq;
	ufm #(.OSCH_FREQ(osch_freq),
	 		 .INIT_MEM(init_mem),
			 .ZERO_MEM(zero_mem),
    		 .NUM_PAGES(NUM_PAGES),
			 .DEVICE(device),
			 .START_PAGE(START_PAGE))
		ufm (.wb_clk_i(clk),
			 .wb_rst_i(rst),
			 .wb_cyc_i(wb_cyc_o),
			 .wb_stb_i(wb_stb_o),
			 .wb_we_i(wb_we_o),
			 .wb_adr_i(wb_adr_o), 
             .wb_dat_i(wb_dat_o),
			 .wb_dat_o(wb_dat_i),
			 .wb_ack_o(wb_ack_i),
			 .wbc_ufm_irq(dummy_irq));

	assign do_read = tx_ready && !take_break;
	ufm_reader ufm_reader(.clk(clk),
						  .rst(rst),
						  .stall(1'b0),
						  .ufm_addr(curr_byte_addr),
						  .read_en(do_read),
						  .ufm_data(data_out),
						  .ufm_valid(tx_data_valid),
						  
						  .efb_cyc_o(wb_cyc_o),
						  .efb_stb_o(wb_stb_o),
						  .efb_we_o(wb_we_o),
						  .efb_adr_o(wb_adr_o), 
						  .efb_dat_i(wb_dat_i),
						  .efb_dat_o(wb_dat_o),
						  .efb_ack_i(wb_ack_i));

	defparam wait_timer.OSCH_FREQ = osch_freq;
	wait_timer wait_timer(.clk(clk),
						  .rst(rst),
						  .stb(wait_stb));

	always @ (posedge clk) begin
		if(rst) begin
			curr_byte_addr <= start_offset;
			take_break <= 0;
		end else begin
			if(wait_stb) begin
				take_break <= 0;
			end
			
			if(tx_data_valid && tx_ready) begin
				curr_byte_addr <= curr_byte_addr + 15'b1;

				if(curr_byte_addr == (start_offset + size - 1)) begin
					curr_byte_addr <= start_offset;
					take_break <= 1;
				end
			end
		end
	end

	function integer ufm_end_page(input [39:0] device);
		case(device)
			"7000L": ufm_end_page = 2045;
			"4000L", "2000U": ufm_end_page = 766;
			"2000L", "1200U": ufm_end_page = 638;
			"1200L", "640U": ufm_end_page = 510;
			"640L": ufm_end_page = 190;
			// No UFM for 256L.
		endcase
	endfunction

	function integer start_page(input [14:0] start_offset);
		start_page = start_offset[14:4];
	endfunction

	function integer start_byte(input [14:0] start_offset);
		start_byte = start_offset[3:0];
	endfunction

	// Extra bit to accomodate overflowing input.
	function integer num_pages(input [15:0] size);
		if((size % 16) == 0) begin
			num_pages = (size / 16);
		end else begin
			num_pages = (size / 16) + 1;
		end
	endfunction

	function integer end_byte(input [14:0] start_offset, input [14:0] size);
		end_byte = (start_offset + size) % 16;
	endfunction
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
	
	reg [15:0] cnt = 16'b0;
	
	assign rst = !(cnt == 16'hFFFF);
	
	always @ (posedge clk) begin
		if(cnt != 16'hFFFF) begin
			cnt <= cnt + 1'b1;
		end
	end	
endmodule
