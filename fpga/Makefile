synth: proc.sv
	vivado -mode batch -source run.tcl
proc.sv:
	mkdir -p ../build
	cd ../build; ../lizard/gen_verilog.py
	cp ../build/$@ .
clean:
	rm -rf proc.sv
