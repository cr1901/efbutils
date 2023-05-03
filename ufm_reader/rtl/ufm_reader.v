module ufm_reader(
    clk, rst, stall, byte_addr, read_en, data_out, valid,
	
	// To EFB
	cyc, stb, we, adr,
    data_i, data_o, wb_ack
);
    input wire clk, rst, stall, read_en;
    output wire [7:0] data_out;
    input wire [14:0] byte_addr;
    output wire valid;

	// WB EFB connections.
	output wire cyc;
	output wire stb;
	output wire we;
	output wire [7:0] adr; 
	input wire [7:0] data_i;
	output wire [7:0] data_o;
	input wire wb_ack;

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
						  
						  .cyc(cyc),
						  .stb(stb),
						  .we(we),
						  .adr(adr), 
						  .data_i(data_i),
						  .data_o(data_o),
						  .wb_ack(wb_ack));

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
