#=========================================================================
# Primetime Power Analysis
#=========================================================================

#-------------------------------------------------------------------------
# Interface to the build system
#-------------------------------------------------------------------------

set pt_design_name              $::env(design_name)

set pt_flow_dir                 $::env(pt_flow_dir)
set pt_plugins_dir              $::env(pt_plugins_dir)
set pt_logs_dir                 $::env(pt_logs_dir)
set pt_reports_dir              $::env(pt_reports_dir)
set pt_results_dir              $::env(pt_results_dir)
set pt_collect_dir              $::env(pt_collect_dir)

set pt_extra_link_libraries [glob -nocomplain $pt_collect_dir/*.db]

#-------------------------------------------------------------------------
# commands
#-------------------------------------------------------------------------

set_app_var target_library "$env(ECE5745_STDCELLS)/stdcells.db"
set_app_var link_library   "* $env(ECE5745_STDCELLS)/stdcells.db $pt_extra_link_libraries"

set power_enable_analysis true
set power_analysis_mode   averaged

read_verilog "handoff/innovus-signoff/${pt_design_name}.vcs.v"

current_design ${pt_design_name}

link_design

source handoff/dc-synthesis/${pt_design_name}.mapped.saif.namemap

# The "Annotating RTL Activity in PrimeTime PX" said on Page 9: "When
# annotating netlists from IC Compiler, users should set the variables
# to disable exact-name matching to prevent annotation of RTL activity
# on same-name nets and hierarchical ports." Not quite sure what these
# variables do though.

set power_disable_exact_name_matching_to_nets      true
set power_disable_exact_name_matching_to_hier_pins true

read_saif "activity-scaled.saif" -strip_path "TOP/${pt_design_name}"

read_parasitics -format spef "handoff/innovus-signoff/typical.spef.gz"

report_annotated_parasitics -check

read_sdc "handoff/dc-synthesis/${pt_design_name}.mapped.sdc"
source clk-def.tcl
set_propagated_clock [all_clocks]

update_timing -full

check_power
update_power

report_switching_activity

report_power -nosplit > ${pt_reports_dir}/power-summary.rpt
report_power -nosplit -hierarchy > ${pt_reports_dir}/power-hierarchy.rpt

exit
