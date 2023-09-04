// half_adder_procedural_tb.v

/* `timescale 1 ns/10 ps  // time-unit = 1 ns, precision = 10 ps

module half_adder_procedural_tb;

    reg a, b;
    wire sum, carry;

    // duration for each bit = 20 * timescale = 20 * 1 ns  = 20ns
    localparam period = 20;  

    half_adder UUT (.a(a), .b(b), .sum(sum), .carry(carry));
reg clk;

// note that sensitive list is omitted in always block
// therefore always-block run forever
// clock period = 2 ns
always 
begin
    clk = 1'b1; 
    #20; // high for 20 * timescale = 20 ns

    clk = 1'b0;
    #20; // low for 20 * timescale = 20 ns
end

always @(posedge clk)
begin
    // values for a and b
    a = 0;
    b = 0;
    #period; // wait for period
    // display message if output not matched
    if(sum != 0 || carry != 0)  
        $display("test failed for input combination 00");

    a = 0;
    b = 1;
    #period; // wait for period 
    if(sum != 1 || carry != 0)
        $display("test failed for input combination 01");

    a = 1;
    b = 0;
    #period; // wait for period 
    if(sum != 1 || carry != 0)
        $display("test failed for input combination 10");

    a = 1;
    b = 1;
    #period; // wait for period 
    if(sum != 0 || carry != 1)
        $display("test failed for input combination 11");

    a = 0;
    b = 1;
    #period; // wait for period 
    if(sum != 1 || carry != 1)
        $display("test failed for input combination 01");

    $stop;   // end of simulation
end
endmodule

module half_adder
(
    input wire a, b,
    output wire sum, carry
);

assign sum = a ^ b;
assign carry = a & b;

endmodule */

/* `timescale 1ns/1ps

module efb_sim();
	`ifndef SYNTHESIS
		GSR GSR_INST ();
		PUR PUR_INST ();
	`endif
	
	wire tx, rx;
	wire [7:0] leds;

	reg clk = 0;

	top dut(tx, rx, leds);

	always begin
		clk <= #20 ~clk;
	end

	always begin
		#1000;
		$stop; 
	end
endmodule */
