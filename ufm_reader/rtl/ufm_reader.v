module ufm_reader(
    clk, rst, stall, ufm_addr, read_en, ufm_data, ufm_valid,
	
	// To EFB
	efb_cyc_o, efb_stb_o, efb_we_o, efb_adr_o,
    efb_dat_i, efb_dat_o, efb_ack_i
);
    input wire clk, rst, stall, read_en;
    output wire [7:0] ufm_data;
    input wire [14:0] ufm_addr;
    output wire ufm_valid;

	// WB EFB connections.
	output wire efb_cyc_o;
	output wire efb_stb_o;
	output wire efb_we_o;
	output wire [7:0] efb_adr_o; 
	input wire [7:0] efb_dat_i;
	output wire [7:0] efb_dat_o;
	input wire efb_ack_i;

    wire [7:0] streamer_data;
	wire streamer_stb, streamer_data_valid;
    wire reader_ready; /* Presently unused, meant to support double-bufferring
                          down the line. Right now, reader is inactive if
                          read_en is not asserted. */

    wire [10:0] flash_addr;

	streamer ufm_streamer(.clk(clk),
						  .rst(rst),
						  .stream__stb(streamer_stb),
						  .stream__stall(1'b0),
						  .stream__addr(flash_addr),
						  .stream__data(streamer_data),
						  .stream__ack(streamer_data_valid),
						  .stream__ready(reader_ready),
						  
						  .efb__cyc(efb_cyc_o),
						  .efb__stb(efb_stb_o),
						  .efb__we(efb_we_o),
						  .efb__adr(efb_adr_o), 
						  .efb__dat_r(efb_dat_i),
						  .efb__dat_w(efb_dat_o),
						  .efb__ack(efb_ack_i));

	page_buffer page_buffer(.clk(clk),
						.rst(rst),
						.seq__data(streamer_data),
						.rand__addr(ufm_addr),
						.rand__read_en(read_en),
						.rand__flush(1'b0),
						.seq__ack(streamer_data_valid),
						.rand__data(ufm_data),
						.rand__valid(ufm_valid),
						.seq__stb(streamer_stb),
						.seq__addr(flash_addr));
endmodule
