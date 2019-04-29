#=========================================================================
# configure.mk
#=========================================================================
# This file will be included inside the Makefile in the build directory

#-------------------------------------------------------------------------
# Step Description
#-------------------------------------------------------------------------

descriptions.vcd2saif = \
	"VCD to SAIF for power analysis"

#-------------------------------------------------------------------------
# ASCII art
#-------------------------------------------------------------------------

define ascii.vcd2saif
	@echo -e $(echo_green)
	@echo '#################################################################################'
	@echo '#       __      __  _____   _____   ___    _____           _____   ______       #'
	@echo '#       \ \    / / / ____| |  __ \ |__ \  / ____|   /\    |_   _| |  ____|      #'
	@echo '#        \ \  / / | |      | |  | |   ) || (___    /  \     | |   | |__         #'
	@echo '#         \ \/ /  | |      | |  | |  / /  \___ \  / /\ \    | |   |  __|        #'
	@echo '#          \  /   | |____  | |__| | / /_  ____) |/ ____ \  _| |_  | |           #'
	@echo '#           \/     \_____| |_____/ |____||_____//_/    \_\|_____| |_|           #'
	@echo '#                                                                               #'
	@echo '#################################################################################'
	@echo -e $(echo_nocolor)
endef

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

define commands.vcd2saif
	vcd2saif -input $(activity_vcd) -output activity.saif
	mkdir -p $(handoff_dir.vcd2saif)
	mv activity.saif $(handoff_dir.vcd2saif)
endef

#-------------------------------------------------------------------------
# Extra targets
#-------------------------------------------------------------------------
# These are extra useful targets when working with this step. These
# targets are included into the build Makefile.

# Clean

clean-vcd2saif:
	rm -rf ./$(VPATH)/vcd2saif
	rm -rf ./$(collect_dir.vcd2saif)
	rm -rf ./$(handoff_dir.vcd2saif)

