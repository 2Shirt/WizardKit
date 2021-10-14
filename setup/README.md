# WizardKit: Setup #

Build the various parts of the project.

## Requirements ##

* Linux
  * 8 GB of RAM<sup>1</sup>
  * 10 GB of free storage space<sup>2</sup>
  * Arch Linux installed with internet access enabled
  * The [Arch Linux Wiki](https://wiki.archlinux.org/) is a great resource
* macOS
  * 10 GB of free storage space
  * El Capitan, High Sierra, or Catalina installed
* WinPE
  * _(Currently under development)_
* Windows Kit
  * 10 GB of free storage space
  * A recent version of Windows 10<sup>3</sup>

## Setup ##

Run the build script in this directory for the part you're looking for

## Notes ##
1. The Linux image is built under a tmpfs, overriding that may allow a lower RAM requirement.
2. Required free storage space can _probably_ be lower but 10 GB should be a safe starting point.
3. Building the Windows Kit under an older OS is not supported by these scripts
