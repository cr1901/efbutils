module page_buffer(clk, rst, data_seq, addr, read_en, flush, seq_valid, data_rand, rand_valid, seq_stb);
	input wire clk, rst;
	input wire [7:0] data_seq;
	input wire [14:0] addr;
	// For now: once read_en is asserted, it needs to be kept
	// asserted until rand_valid strobes. Unspecified what happens
	// otherwise.
	input wire read_en;
	input wire flush;
	input wire seq_valid;
	
	output wire [7:0] data_rand;
	output wire rand_valid;
	output reg seq_stb;


	wire [10:0] page_addr;
	reg buf_valid,  buf_filling, read_en_delayed;
	reg [10:0] curr_page;
	reg [7:0] page_buf [15:0];
	reg [3:0] curr_byte_wr, curr_byte_rd;
	
	assign page_addr = addr[14:4];
	
	// Reads are registered, so it takes one cycle before
	// they're actually valid.
	assign rand_valid = read_en_delayed && buf_valid;
	always @(posedge clk) begin
		read_en_delayed <= read_en;
	end
	
	assign data_rand = page_buf[curr_byte_rd];
	
	// FSM for filling buffer/reading.
	always @(posedge clk) begin
		if(rst) begin
			curr_byte_rd <= 0;
			curr_byte_wr <= 0;
			buf_valid <= 0;
			buf_filling <= 0;
			curr_page <= 0;
			seq_stb <= 0;
		end else begin
			seq_stb <= 0;
			curr_byte_rd <= addr[3:0];
			
			if(buf_valid) begin
				if(read_en) begin
					if(page_addr != curr_page) begin
						curr_page <= page_addr;
						buf_valid <= 0;
						buf_filling <= 1;
						seq_stb <= 1;
					end
				/* Current read takes priority over flush. */
				end else if(flush) begin
					buf_valid <= 0;
				end
			end else if(buf_filling) begin
				if(seq_valid) begin
					page_buf[curr_byte_wr] <= data_seq;
					curr_byte_wr <= curr_byte_wr + 4'b1;

					if(curr_byte_wr == 15) begin
						buf_valid <= 1;
						buf_filling <= 0;
					end

					seq_stb <= 1;
				end
			end else begin
				if(read_en) begin
					curr_page <= page_addr;
					buf_filling <= 1;
					seq_stb <= 1;
				end
			end
		end
	end

	// Warnings are safe to ignore: https://stackoverflow.com/a/22395232
	`ifdef __ICARUS__
		initial begin
			for(integer i = 0; i < 16; i = i+1) begin
				$dumpvars(0, page_buf[i]);
			end
		end
	`endif
endmodule
