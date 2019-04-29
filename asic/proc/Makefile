default: proc.sv vcd

proc.sv:
	cd ../../fpga; make proc.sv
	cp ../../fpga/proc.sv .
vcd:
	cd ../../app; ./setup
	cd ../../app/build; make
	cd ../../build; ../lizard/sim --verilate --vcd ../app/build/ubmark-vvadd
	cp ../../build/ubmark-vvadd-verilate.verilator.vcd .
clean:
	rm -rf proc.sv
	rm -rf *.vcd
	cd ../../fpga; make clean
