#=========================================================================
# configure.mk
#=========================================================================
# This file will be included inside the Makefile in the build directory

#-------------------------------------------------------------------------
# Step Description
#-------------------------------------------------------------------------

descriptions.cacti-mc = \
	"Generate SRAMs using CACTI"

#-------------------------------------------------------------------------
# ASCII art
#-------------------------------------------------------------------------

define ascii.cacti-mc
	@echo -e $(echo_green)
	@echo '#################################################################################'
	@echo '#               _____          _____ _______ _____   __  __  _____              #'
	@echo '#              / ____|   /\   / ____|__   __|_   _| |  \/  |/ ____|             #'
	@echo '#             | |       /  \ | |       | |    | |   | \  / | |                  #'
	@echo '#             | |      / /\ \| |       | |    | |   | |\/| | |                  #'
	@echo '#             | |____ / ____ \ |____   | |   _| |_  | |  | | |____              #'
	@echo '#              \_____/_/    \_\_____|  |_|  |_____| |_|  |_|\_____|             #'
	@echo '#                                                                               #'
	@echo '#################################################################################'
	@echo -e $(echo_nocolor)
endef

#-------------------------------------------------------------------------
# Alias -- short name for this step
#-------------------------------------------------------------------------

abbr.cacti-mc = memgen

#-------------------------------------------------------------------------
# Make variables
#-------------------------------------------------------------------------

sram_dirs := $(patsubst %, %,     $(srams))
sram_dbs  := $(patsubst %, %.db,  $(srams))
sram_lefs := $(patsubst %, %.lef, $(srams))
sram_libs := $(patsubst %, %.lib, $(srams))
sram_mws  := $(patsubst %, %.mw,  $(srams))

#-------------------------------------------------------------------------
# Primary command target
#-------------------------------------------------------------------------
# These are the commands run when executing this step. These commands are
# included into the build Makefile.

define commands.cacti-mc
	mkdir -p $(handoff_dir.cacti-mc)
	for sram in $(srams); do \
    rm -rf $${sram}; \
    cacti-mc $(srams_dir)/$${sram}.cfg; \
    mv $${sram}/*.db  $(handoff_dir.cacti-mc); \
    mv $${sram}/*.lef $(handoff_dir.cacti-mc); \
    mv $${sram}/*.lib $(handoff_dir.cacti-mc); \
    mv $${sram}/*.mw  $(handoff_dir.cacti-mc); \
  done
endef

#-------------------------------------------------------------------------
# Extra targets
#-------------------------------------------------------------------------
# These are extra useful targets when working with this step. These
# targets are included into the build Makefile.

# Clean

clean-cacti-mc:
	rm -rf $(srams)
	rm -rf ./$(VPATH)/cacti-mc
	rm -rf ./$(collect_dir.cacti-mc)
	rm -rf ./$(handoff_dir.cacti-mc)

