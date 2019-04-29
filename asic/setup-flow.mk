#=========================================================================
# setup-flow.mk
#=========================================================================
# The default asic flow has the set of common ASIC steps we will need to
# do architectural design-space exploration. This configuration should
# always work as long as the ASIC design kit (ADK) is set up properly.
#
# Author : Christopher Torng
# Date   : March 26, 2018

# List the steps to use in the default design flow

steps = \
  info \
  cacti-mc \
  vcd2saif \
  dc-synthesis \
  innovus-flowsetup \
  innovus-init \
  innovus-place \
  innovus-cts \
  innovus-postctshold \
  innovus-route \
  innovus-postroute \
  innovus-signoff \
  pt-pwr \

# Step dependency graph

dependencies.info                = seed

dependencies.cacti-mc            = seed
dependencies.vcd2saif            = seed
dependencies.dc-synthesis        = vcd2saif cacti-mc
dependencies.innovus-flowsetup   = dc-synthesis cacti-mc
dependencies.innovus-init        = innovus-flowsetup
dependencies.innovus-place       = innovus-flowsetup innovus-init
dependencies.innovus-cts         = innovus-flowsetup innovus-place
dependencies.innovus-postctshold = innovus-flowsetup innovus-cts
dependencies.innovus-route       = innovus-flowsetup innovus-postctshold
dependencies.innovus-postroute   = innovus-flowsetup innovus-route
dependencies.innovus-signoff     = innovus-flowsetup innovus-postroute
dependencies.pt-pwr              = dc-synthesis innovus-signoff cacti-mc
dependencies.all                 = pt-pwr

#-------------------------------------------------------------------------
# Notes on step dependency graph
#-------------------------------------------------------------------------
# The build system uses the step dependency graph to order the steps. The
# listed dependencies are actually the Makefile prerequisites for each
# step. In addition, the build system takes care of collecting handoff
# files from all dependency steps before executing each step.
#
# Two requirements:
#
# - The first step should depend on "seed", which generates the build env
# - The special "all" target should depend on the last step
#
# Any of the steps in the top-level steps directory can be used as part of
# a custom VLSI flow.
#

