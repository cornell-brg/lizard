set prj fpga-rv64gc
set top proc

# See: https://www.xilinx.com/support/documentation/sw_manuals/xilinx2013_4/ug894-vivado-tcl-scripting.pdf

# ZedBoard
# create_project ${prj} ${prj} -part xc7z020clg484-1 -force
# Zynq UltraScale+
create_project ${prj} ${prj} -part xczu7ev-ffvf1517-1LV-i -force
file mkdir ${prj}/${prj}.srcs/
file mkdir ${prj}/${prj}.runs/synth/
file copy ${top}.sv ${prj}/${prj}.srcs/
add_files ${prj}/${prj}.srcs/
update_compile_order -fileset sources_1

# Synthesis
synth_design -top ${top}
report_utilization -file ${prj}/${prj}.runs/synth/${top}_utilization_synth.rpt

# fix up ports
place_ports
set_property IOSTANDARD LVCMOS18 [get_ports -of_objects [get_iobanks -filter { BANK_TYPE !~  "BT_MGT" }]]

# Optimize
opt_design

# Place
place_design

# Route
route_design

report_route_status -file ${prj}/${prj}.runs/post_route_status.rpt
report_timing_summary -file ${prj}/${prj}.runs/post_route_timing_summary.rpt
report_power -file ${prj}/${prj}.runs/post_route_power.rpt
report_drc -file ${prj}/${prj}.runs/post_imp_drc.rpt

# Bitstream
# Ignore the missing pin mappings (which map ports on the top level to actual pins on the chip)
set_property SEVERITY {Warning} [get_drc_checks NSTD-1]
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
write_bitstream -force ${prj}/${prj}.runs/${top}.bit
