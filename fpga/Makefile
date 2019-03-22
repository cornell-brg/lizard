synth: proc.sv
	vivado -mode batch -source run.tcl
proc.sv:
	cd ../build; ../src/gen_verilog
	cp ../build/$@ .
