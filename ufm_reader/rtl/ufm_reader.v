module ufm_reader(
    clk, rst, stall, byte_addr, read_en, data_out, valid,
	
	// To EFB
	efb_cyc_o, efb_stb_o, efb_we_o, efb_adr_o,
    efb_dat_i, efb_dat_o, efb_ack_i
);
    input wire clk, rst, stall, read_en;
    output wire [7:0] data_out;
    input wire [14:0] byte_addr;
    output wire valid;

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
	assign flash_addr = byte_addr[14:4];

	ufm_streamer ufm_streamer(.clk(clk),
						  .rst(rst),
						  .start(streamer_stb),
						  .stall(1'b0),
						  .addr(flash_addr),
						  .data(streamer_data),
						  .data_stb(streamer_data_valid),
						  .ready(reader_ready),
						  
						  .efb_cyc_o(efb_cyc_o),
						  .efb_stb_o(efb_stb_o),
						  .efb_we_o(efb_we_o),
						  .efb_adr_o(efb_adr_o), 
						  .efb_dat_i(efb_dat_i),
						  .efb_dat_o(efb_dat_o),
						  .efb_ack_i(efb_ack_i));

	page_buffer page_buffer(.clk(clk),
							.rst(rst),
							.data_seq(streamer_data),
							.addr(byte_addr),
							.read_en(read_en),
							.flush(1'b0),
							.seq_valid(streamer_data_valid),
							.data_rand(data_out),
							.rand_valid(valid),
							.seq_stb(streamer_stb));
endmodule
