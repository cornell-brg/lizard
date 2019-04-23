synth: proc.sv
	vivado -mode batch -source run.tcl
proc.sv:
	cd ../build; ../lizard/gen_verilog
	cp ../build/$@ .
clean:
	rm -rf proc.sv
