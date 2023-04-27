module ufm_reader(clk, rst, start, stall, addr [10:0], data [7:0], data_stb, ready);
	input wire clk;
	input wire rst;
	
	// User-visible FSM Inputs
	input wire start, stall; // stall input not functional yet!
	input wire [10:0] addr;
	
	// User-visible FSM Outputs
	output wire data_stb, ready;
	output wire [7:0] data;
	
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
	wire ack, wb_data_stb;
	reg ufm_busy;
	
	// Internal FSM outputs.
	wire req;
	reg [7:0] cmd;
	reg [23:0] ops;
	reg [1:0] op_len;
	reg [5:0] data_len;
	reg [31:0] data_wr;
	reg wr;

	wb_sequencer sequencer(.clk(clk),
						   .rst(rst),
						   .req(req),
						   .cmd(cmd),
						   .ops(ops),
						   .op_len(op_len),
						   .data_wr(data_wr),
						   .data_len(data_len),
						   .wr(wr),
						   .data(data),
						   .data_stb(wb_data_stb),
						   .ack(ack));
	
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
				if(wb_data_stb) begin
					// Busy bit is bit 12 of the status register. MSByte
					// received first, so 3rd data bit, bit 4 is the 12th
					// bit.
					ufm_busy <= data[4];
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
	
	always @(state or start or ack) begin
		next = state;
		case(state)
			IDLE: next_state_if_asserted(start, ENABLE_CONFIG);
			ENABLE_CONFIG: next_state_if_asserted(ack, POLL_STATUS_1);
			// Bleh... easier to make each data strobe an individual state.
			POLL_STATUS_1: next_state_if_asserted(wb_data_stb, POLL_STATUS_2);
			POLL_STATUS_2: next_state_if_asserted(wb_data_stb, POLL_STATUS_3);
			POLL_STATUS_3: next_state_if_asserted(wb_data_stb, POLL_STATUS_4);
			POLL_STATUS_4: next_state_if_asserted(wb_data_stb, POLL_STATUS_5);			
			POLL_STATUS_5: begin
				if(ack) begin
					next = SET_UFM_ADDR;
					next_state_if_asserted(ufm_busy, POLL_STATUS_1);
				end
			end
			SET_UFM_ADDR: next_state_if_asserted(ack, READ_UFM);
			READ_UFM: next_state_if_asserted(ack, DISABLE_CONFIG);
			DISABLE_CONFIG: next_state_if_asserted(ack, BYPASS);
			BYPASS: begin
				if(ack) begin
					next = IDLE;
					next_state_if_asserted(start, ENABLE_CONFIG);
				end
			end
		endcase
	end


	// Outputs
	always @(state, addr) begin
		case(state)
			IDLE: begin
				cmd = 0; ops = 0; op_len = 0; data_wr = 0; data_len = 0; wr = 1;
			end			
			ENABLE_CONFIG: begin
				cmd = 8'h74; ops = 24'h080000; op_len = 2'd3; data_wr = 0; data_len = 0; wr = 1;
			end				
			POLL_STATUS_1, POLL_STATUS_2, POLL_STATUS_3, POLL_STATUS_4, POLL_STATUS_5:  begin
				cmd = 8'h3C; ops = 24'h000000; op_len = 2'd3; data_wr = 0; data_len = 5'd4; wr = 0;
			end		
			SET_UFM_ADDR: begin
				cmd = 8'hB4; ops = 24'h000000; op_len = 2'd3;
				// Apparently page addresses are 14-bit, but MachXO2 UFM only goes up to 11-bits.
				// Bit 30 is 1 to indicate UFM.
				data_wr = {18'b0100_0000_0000_0000_00, 3'b000, addr}; data_len = 5'd4; wr = 1;
			end
			READ_UFM: begin
				cmd = 8'hCA; ops = 24'h100001; op_len = 2'd3; data_len = 5'd16; wr = 0;
			end
			DISABLE_CONFIG: begin
				cmd = 8'h26; ops = 24'h000000; op_len = 2'd2; data_len = 0; wr = 1;
			end
			BYPASS: begin
				cmd = 8'hFF; ops = 24'h000000; op_len = 0; data_len = 0; wr = 1;
			end
		endcase
	end

	// For most states, req should strobe as soon as we enter another state
	// to start a WB xfer. But the IDLE and POLL_ intermediate states are not
	// the beginning of a WB xfer.
	assign req = ((state != IDLE) &&
		(state != POLL_STATUS_2) &&
		(state != POLL_STATUS_3) &&
		(state != POLL_STATUS_4) &&
		(state != POLL_STATUS_5) &&
		(state != prev)); 
	assign data_stb = (state == READ_UFM) && wb_data_stb;
	assign ready = (state == IDLE || (next == IDLE));
endmodule


module wb_sequencer(clk, rst, req,
	cmd [7:0], ops [23:0], op_len [1:0],
	data_wr [31:0], data_len [5:0], wr,
	data [7:0], data_stb, ack);
	input wire clk;
	input wire rst;

	// Port FSM Inputs
	input wire req;
	input wire [7:0] cmd;
	input wire [23:0] ops;
	input wire [1:0] op_len;
	input wire [31:0] data_wr; // For WB operations requiring a write. Reuses data_len.
	input wire [5:0] data_len; // TODO: Support more than page read.
	input wire wr;
	
	// Port FSM outputs
	output reg [7:0] data;
	output wire data_stb;
	output wire ack;
	
	
	// Hack to simulate enum
	localparam [5:0] IDLE = 5'd0,
					 WB_ENABLE_1 = 5'd1,
					 WB_ENABLE_2 = 5'd2,
					 WB_CMD_1 = 5'd3,
					 WB_CMD_2 = 5'd4,
					 WB_OPERAND_1 = 5'd5,
					 WB_OPERAND_2 = 5'd6,
					 WB_DATA_1 = 5'd7,
					 WB_DATA_2 = 5'd8,
					 WB_DISABLE_1 = 5'd9,
					 WB_DISABLE_2 = 5'd10,
					 ERROR = 5'd11;
	
	// Internal FSM Outputs
	reg cyc, stb, we;
	wire [7:0] data_o, adr;
	
	// Internal FSM Inputs
	wire [7:0] data_i;
	wire wb_ack;

	wire dummy_irq;
	ufm ufm(.wb_clk_i(clk),
			.wb_rst_i(rst),
			.wb_cyc_i(cyc),
			.wb_stb_i(stb),
			.wb_we_i(we),
			.wb_adr_i(adr), 
			.wb_dat_i(data_o),
			.wb_dat_o(data_i),
			.wb_ack_o(wb_ack),
			.wbc_ufm_irq(dummy_irq));

	// State transition driver
	reg [3:0] state;
	reg [3:0] next;
	reg [1:0] curr_op;
	reg [5:0] curr_data;

	always @(posedge clk) begin
		if(rst) begin
			state <= IDLE;
			curr_op <= 0;
			curr_data <= 0;
			// data <= 8'h30;
		end else begin
			state <= next;

			if(state == WB_OPERAND_2) begin
				// FIXME: High potential for off-by-one error. Ask how I know.
				if(curr_op < op_len - 1) begin
					curr_op <= curr_op + 1;
				end else begin
					curr_op <= 0;
				end
			end
			
			if(state == WB_DATA_1) begin
				if(wb_ack) begin
					data <= data_i;
				end
			end
			
			if(state == WB_DATA_2) begin
				if(curr_data < data_len - 1) begin
					curr_data <= curr_data + 1;
				end else begin
					curr_data <= 0;
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

	always @(state or req or ack or curr_op or curr_data or wr) begin
		next = state;
		default_wb;
		case(state)
			IDLE: begin
				next_state_if_asserted(req, WB_ENABLE_1);
			end
	
			WB_ENABLE_1: begin
				wb_write;
				next_state_if_asserted(wb_ack, WB_ENABLE_2);
			end
			
			WB_ENABLE_2: begin
				next = WB_CMD_1;
			end
			
			WB_CMD_1: begin
				wb_write;
				next_state_if_asserted(wb_ack, WB_CMD_2);
			end
			
			WB_CMD_2: begin
				if(op_len > 0) begin
					next = WB_OPERAND_1;
				end else if(data_len > 0) begin
					next = WB_DATA_1;
				end else begin
					next = WB_DISABLE_1;
				end
			end
			
			WB_OPERAND_1: begin
				wb_write;
				next_state_if_asserted(wb_ack, WB_OPERAND_2);
			end
			
			WB_OPERAND_2: begin
				if(curr_op < op_len - 1) begin
					next = WB_OPERAND_1;
				end else if(data_len > 0) begin
					next = WB_DATA_1;
				end else begin
					next = WB_DISABLE_1;
				end
			end

			
			WB_DATA_1: begin
				if(wr) begin
					wb_write;
				end else begin
					wb_read;
				end
				
				next_state_if_asserted(wb_ack, WB_DATA_2);
			end
			
			WB_DATA_2: begin
				if(curr_data < data_len - 1) begin
					next = WB_DATA_1;
				end else begin
					next = WB_DISABLE_1;
				end
			end
			
			WB_DISABLE_1: begin
				wb_write;
				next_state_if_asserted(wb_ack, WB_DISABLE_2);
			end
			
			WB_DISABLE_2: begin
				next = IDLE;
				next_state_if_asserted(req, WB_ENABLE_1);
			end
			
			ERROR: begin
				
			end

			default: begin
				next = ERROR;
			end
		endcase
	end
	
	// Outputs
	// Task outputs embedded into state transition block
	/* TODO: For higher clk speeds, we may need to add a wait state
	   between sending READ_UFM cmd and end of first op.

	   Max speed w/o wait states is 16.6 MHz. This seems to come
	   from 4 cycles between _start_ of ACK of cmd and _end_ of ACK of
	   first op.

	   1000/16.6 * 4 = ~240 ns, min waiting time for 2000-devices and above
	   (360ns for smaller).
	   
	   See 10.6 in TN-02155 and Table 80 in TN1246.
	*/
	task default_wb;
		begin
			cyc = 0;
			stb = 0;
			we = 0;
		end
	endtask
	
	task wb_write;
		begin
			cyc = 1'b1;
			stb = 1'b1;
			we = 1'b1;
		end
	endtask
	
	task wb_read;
		begin
			cyc = 1'b1;
			stb = 1'b1;
			we = 1'b0;
		end
	endtask
	
	/* assign data_valid = (state == WB_1); */
	assign data_stb = (state == WB_DATA_2);
	assign ack = (state == WB_DISABLE_2);
	assign data_o = data_payload(state, cmd, ops, curr_op, wr, data_wr, curr_data);
	assign adr = addr_payload(state, wr);
	
	function [7:0] data_payload(input [3:0] state, input [7:0] cmd,
		input [23:0] ops, input [1:0] curr_op,
		input wr, input [31:0] data_wr, input [5:0] curr_data);
		case(state)
			WB_ENABLE_1: data_payload = 8'h80;
			WB_CMD_1, WB_CMD_2: data_payload = cmd;
			WB_OPERAND_1, WB_OPERAND_2: begin
				case(curr_op)
					2'h0: data_payload = ops[23:16];
					2'h1: data_payload = ops[15:8];
					2'h2: data_payload = ops[7:0];
					default: data_payload = 8'b0; 
				endcase
			end
			WB_DATA_1, WB_DATA_2: begin
				case(curr_data)
					6'd0: data_payload = data_wr[31:24];
					6'd1: data_payload = data_wr[23:16];
					6'd2: data_payload = data_wr[15:8];
					6'd3: data_payload = data_wr[7:0];
					default: data_payload = 8'b0; 
				endcase
			end
			default: data_payload = 8'b0;
		endcase		
	endfunction
	
	function [7:0] addr_payload(input [3:0] state, input wr);
		case(state)
			WB_ENABLE_1, WB_ENABLE_2, WB_DISABLE_1, WB_ENABLE_2: addr_payload = 8'h70;
			WB_CMD_1, WB_CMD_2, WB_OPERAND_1, WB_OPERAND_2: addr_payload = 8'h71;
			WB_DATA_1, WB_DATA_2: begin 
				if(wr) begin
					addr_payload = 8'h71;
				end else begin
					addr_payload = 8'h73;
				end
			end
			default: addr_payload = 8'b0;
		endcase		
	endfunction
endmodule
