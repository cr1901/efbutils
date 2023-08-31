`default_nettype none

module ufm_streamer(
	clk, rst, start, stall, page_addr, ufm_data_rd, ufm_rd_stb, ready,
	
	// Wishbone
	efb_cyc_o, efb_stb_o, efb_we_o, efb_adr_o, 
    efb_dat_i, efb_dat_o, efb_ack_i
	);
	input wire clk;
	input wire rst;
	
	// User-visible FSM Inputs
	input wire start, stall; // stall input not functional yet!
	input wire [10:0] page_addr;
	
	// User-visible FSM Outputs
	output wire ufm_rd_stb, ready;
	output wire [7:0] ufm_data_rd;

	// WB inputs and outputs
	output wire efb_cyc_o;
    output wire efb_stb_o;
    output wire efb_we_o;
    output wire [7:0] efb_adr_o;
    output wire [7:0] efb_dat_o;
    input wire [7:0] efb_dat_i;
    input wire efb_ack_i;
	
	// Hack to simulate enum
	localparam [3:0] IDLE = 4'd0,
					 ENABLE_CONFIG = 4'd1,
					 POLL_STATUS_1 = 4'd2,
					 POLL_STATUS_2 = 4'd3,
					 POLL_STATUS_3 = 4'd4,
					 POLL_STATUS_4 = 4'd5,
					 POLL_STATUS_5 = 4'd6,
					 SET_UFM_ADDR = 4'd7,
					 READ_UFM = 4'd8,
					 DISABLE_CONFIG = 4'd9,
					 BYPASS = 4'd10;

	// Internal FSM inputs.
	wire frame_done, data_rd_stb;
	reg ufm_busy;
	
	// Internal FSM outputs. TODO: Make data_rd and data_wr symmetrical size.
	wire xfer_req;
	reg [7:0] cmd;
	reg [23:0] ops;
	reg [1:0] op_len;
	reg [5:0] data_len;
	reg [31:0] data_wr;
	reg xfer_is_wr;

	wire [7:0] data_rd;
	// Only valid when qualified with ufm_rd_stb.
	assign ufm_data_rd = data_rd;

	wire dummy_wr_ready;

	sequencer sequencer(.clk(clk),
						.rst(rst),
						.ctl__req(xfer_req),
						.ctl__cmd__cmd(cmd),
						.ctl__cmd__ops(ops),
						.ctl__op_len(op_len),
						.ctl__data_len(data_len),
						.ctl__xfer_is_wr(xfer_is_wr),
						.ctl__done(frame_done),

						.wr__data(data_wr),
						.wr__ready(dummy_wr_ready),
						.wr__valid(1'b0),

						.rd__data(data_rd),
						.rd__stb(data_rd_stb),

						.efb__cyc(efb_cyc_o),
						.efb__stb(efb_stb_o),
						.efb__we(efb_we_o),
						.efb__adr(efb_adr_o), 
						.efb__dat_w(efb_dat_o),
						.efb__dat_r(efb_dat_i),
						.efb__ack(efb_ack_i)); 

	// State transition driver
	reg [3:0] state;
	reg [3:0] prev;
	reg [3:0] next;

	always @(posedge clk) begin
		if(rst) begin
			state <= 0;
			ufm_busy <= 0;
			// data <= 8'h30;
		end else begin
			state <= next;
			prev <= state;
			
			if(state == POLL_STATUS_3) begin
				if(data_rd_stb) begin
					// Busy bit is bit 12 of the status register. MSByte
					// received first, so 3rd data bit, bit 4 is the 12th
					// bit.
					ufm_busy <= data_rd[4];
				end
			end
		end
	end
	
	// State transitions
	task next_state_if_asserted(input stim, input [3:0] state);
		if(stim) begin
			next = state;
		end
	endtask
	
	always @(state or start or frame_done or data_rd_stb or ufm_busy) begin
		next = state;
		case(state)
			IDLE: next_state_if_asserted(start, ENABLE_CONFIG);
			ENABLE_CONFIG: next_state_if_asserted(frame_done, POLL_STATUS_1);
			// Bleh... easier to make each data strobe an individual state.
			POLL_STATUS_1: next_state_if_asserted(data_rd_stb, POLL_STATUS_2);
			POLL_STATUS_2: next_state_if_asserted(data_rd_stb, POLL_STATUS_3);
			POLL_STATUS_3: next_state_if_asserted(data_rd_stb, POLL_STATUS_4);
			POLL_STATUS_4: next_state_if_asserted(data_rd_stb, POLL_STATUS_5);
			POLL_STATUS_5: begin
				if(frame_done) begin
					next = SET_UFM_ADDR;
					next_state_if_asserted(ufm_busy, POLL_STATUS_1);
				end
			end
			SET_UFM_ADDR: next_state_if_asserted(frame_done, READ_UFM);
			READ_UFM: next_state_if_asserted(frame_done, DISABLE_CONFIG);
			DISABLE_CONFIG: next_state_if_asserted(frame_done, BYPASS);
			BYPASS: begin
				if(frame_done) begin
					next = IDLE;
					next_state_if_asserted(start, ENABLE_CONFIG);
				end
			end
		endcase
	end


	// Outputs
	always @(state, page_addr) begin
		case(state)
			IDLE: begin
				cmd = 0; ops = 0; op_len = 0; data_wr = 0; data_len = 0; xfer_is_wr = 1;
			end			
			ENABLE_CONFIG: begin
				cmd = 8'h74; ops = 24'h080000; op_len = 2'd3; data_wr = 0; data_len = 0; xfer_is_wr = 1;
			end				
			POLL_STATUS_1, POLL_STATUS_2, POLL_STATUS_3, POLL_STATUS_4, POLL_STATUS_5:  begin
				cmd = 8'h3C; ops = 24'h000000; op_len = 2'd3; data_wr = 0; data_len = 5'd4; xfer_is_wr = 0;
			end		
			SET_UFM_ADDR: begin
				cmd = 8'hB4; ops = 24'h000000; op_len = 2'd3;
				// Apparently page addresses are 14-bit, but MachXO2 UFM only goes up to 11-bits.
				// Bit 30 is 1 to indicate UFM.
				data_wr = {18'b0100_0000_0000_0000_00, 3'b000, page_addr}; data_len = 5'd4; xfer_is_wr = 1;
			end
			READ_UFM: begin
				cmd = 8'hCA; ops = 24'h100001; op_len = 2'd3; data_wr = 0; data_len = 5'd16; xfer_is_wr = 0;
			end
			DISABLE_CONFIG: begin
				cmd = 8'h26; ops = 24'h000000; op_len = 2'd2; data_wr = 0; data_len = 0; xfer_is_wr = 1;
			end
			BYPASS: begin
				cmd = 8'hFF; ops = 24'h000000; op_len = 0; data_wr = 0; data_len = 0; xfer_is_wr = 1;
			end
			default: begin
				cmd = 0; ops = 0; op_len = 0; data_wr = 0; data_len = 0; xfer_is_wr = 0;
			end
		endcase
	end

	// For most states, xfer_req should strobe as soon as we enter another state
	// to start a WB xfer. But the IDLE and POLL_ intermediate states are not
	// the beginning of a WB xfer.
	assign xfer_req = ((state != IDLE) &&
		(state != POLL_STATUS_2) &&
		(state != POLL_STATUS_3) &&
		(state != POLL_STATUS_4) &&
		(state != POLL_STATUS_5) &&
		(state != prev)); 
	assign ufm_rd_stb = (state == READ_UFM) && data_rd_stb;
	assign ready = (state == IDLE || (next == IDLE));
endmodule
