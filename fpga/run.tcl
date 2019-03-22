set prj fpga-rv64gc
set top proc

create_project ${prj} ${prj} -part xc7z020clg484-1 -force
file mkdir ${prj}/${prj}.srcs/
file mkdir ${prj}/${prj}.runs/synth/
file copy ${top}.sv ${prj}/${prj}.srcs/
add_files ${prj}/${prj}.srcs/
update_compile_order -fileset sources_1
export_ip_user_files -of_objects  [get_files ${prj}/${prj}.srcs/] -no_script -reset -force -quiet
synth_design -top ${top}
report_utilization -file ${prj}/${prj}.runs/synth/${top}_utilization_synth.rpt
