# WizardKit #

A collection of scripts to help technicians service computers.

## Overview ##

There are a few main parts to this project and their uses:

* Live Linux image
  * Hardware diagnostics
    * CPU stress tests with temperature monitoring
    * Health checks/tests for storage drives
    * Misc other diagnostics
  * Data recovery
    * General data transfers from many possible filesystems
    * Bit-level drive duplication based on ddrescue
* Live macOS image
  * Hardware diagnostics
    * CPU stress tests with temperature monitoring
    * Health checks/tests for storage drives
  * Data recovery
    * _(Currently under development)_
* Live WinPE image
  * _(Currently under development)_
* Windows Kit _(intended for UFDs)_
  * Automated repairs
    * AV scans
    * Windows health checks
  * Automated setup
    * Install software
    * System configuration

## Combined UFD ##

All parts can be combined onto a single UFD!

* Compatible with most legacy and UEFI bootloaders
* Custom boot menus
* To get started run `build-ufd` under the live Linux image
