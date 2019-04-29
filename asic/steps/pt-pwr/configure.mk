#=========================================================================
# configure.mk
#=========================================================================
# This file will be included inside the Makefile in the build directory

#-------------------------------------------------------------------------
# Step Description
#-------------------------------------------------------------------------

descriptions.pt-pwr = \
	"Power analysis"

#-------------------------------------------------------------------------
# ASCII art
#-------------------------------------------------------------------------

define ascii.pt-pwr
	@echo -e $(echo_green)
	@echo '#################################################################################'
	@echo '#                  _____    ____ __          __ ______   _____	                 #'
	@echo '#                 |  __ \  / __ \\ \        / /|  ____| |  __ \                 #'
	@echo '#                 | |__) || |  | |\ \  /\  / / | |__    | |__) |                #'
	@echo '#                 |  ___/ | |  | | \ \/  \/ /  |  __|   |  _  /                 #'
	@echo '#                 | |     | |__| |  \  /\  /   | |____  | | \ \                 #'
	@echo '#                 |_|      \____/    \/  \/    |______| |_|  \_\                #'
	@echo '#                                                                               #'
	@echo '#################################################################################'
	@echo -e $(echo_nocolor)
endef

#-------------------------------------------------------------------------
# Alias -- short name for this step
#-------------------------------------------------------------------------

abbr.pt-pwr = power

#-------------------------------------------------------------------------
# Interface to run.tcl
#-------------------------------------------------------------------------

export pt_flow_dir     = $(flow_dir.pt-pwr)
export pt_plugins_dir  = $(plugins_dir.pt-pwr)
export pt_logs_dir     = $(logs_dir.pt-pwr)
export pt_reports_dir  = $(reports_dir.pt-pwr)
export pt_results_dir  = $(results_dir.pt-pwr)
export pt_collect_dir  = $(collect_dir.pt-pwr)

#-------------------------------------------------------------------------
# Extra dependencies
#-------------------------------------------------------------------------
# The build system takes care of any step dependencies, but you can draw
# up any additional custom dependencies for this step here (e.g., extra
# files not visible to the build sytem).

# extra_dependencies.vcd2saif = none

#-------------------------------------------------------------------------
# Primary command target
#-------------------------------------------------------------------------
# These are the commands run when executing this step. These commands are
# included into the build Makefile.

define commands.pt-pwr

	rm -rf ./$(logs_dir.pt-pwr)
	rm -rf ./$(reports_dir.pt-pwr)
	rm -rf ./$(results_dir.pt-pwr)

	mkdir -p $(logs_dir.pt-pwr)
	mkdir -p $(reports_dir.pt-pwr)
	mkdir -p $(results_dir.pt-pwr)

	vcd2saif -input $(activity_vcd) -output activity.saif
	$(flow_dir.pt-pwr)/preprocess-saif $(clock_period) activity.saif activity-scaled.saif clk-def.tcl
	pt_shell -file $(flow_dir.pt-pwr)/run.tcl

	$(flow_dir.pt-pwr)/summarize-results \
    $(clock_period) \
    $(design_v) \
    $(activity_vcd) \
    reports/innovus/signoff.summaryReport.rpt \
    reports/innovus/signoff.summary.gz \
    activity-scaled.saif \
    reports/pt-pwr/power-summary.rpt | tee summary-power.txt

endef

#-------------------------------------------------------------------------
# Extra targets
#-------------------------------------------------------------------------
# These are extra useful targets when working with this step. These
# targets are included into the build Makefile.

# Clean

clean-pt-pwr:
	rm -rf ./$(VPATH)/pt-pwr
	rm -rf ./$(collect_dir.pt-pwr)
	rm -rf ./$(handoff_dir.pt-pwr)
	rm -rf ./summary-power.txt ./activity-scaled.saif ./activity.saif
	rm -rf ./clk-def.tcl ./parasitics_command.log ./pt_shell_command.log
	rm -rf ./power.rpt

