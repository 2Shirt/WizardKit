# Wizard Kit #

A collection of scripts to help technicians service Windows systems.

## Main Kit ##

### Build Requirements ###

* PowerShell 3.0 or newer<sup>1</sup>
* 6 Gb disk space

### Initial Setup ###

* Replace artwork as desired
* Run `Build Kit.cmd` which will do the following:
  * Download 7-Zip, ConEmu, Notepad++, and Python (including wheel packages)
  * Open `main.py` in Notepad++ for configuration
  * Update the rest of the tools with the `.bin\Scripts\update_kit.py` script

### Layout ###

* Root
  * Main script launchers:
* `.bin`
  * Extracted programs: As compressed tools are run they will be extracted here.
  * `Scripts`
    * "Real" scripts live here and are run via their respective launchers.
* `.cbin`
  * This folder holds the compressed and encrypted tool archives.
  * They are extracted at runtime as needed.
* `Data Recovery`
  * This folder is not copied by `Copy WizardKit.cmd` to help discourage
  * recovering data to the same drive.
* `Data Transfers`
* `Diagnostics`
* `Drivers`
* `Installers`
* `Misc`
* `Repairs`
* `Uninstallers`

## Windows PE ##

### Build Requirements ###

* Windows Assessment and Deployment Kit for Windows 10
* PowerShell 3.0 or newer
* 2 Gb disk space

### Initial Setup ###

* Replace artwork as desired (if not already done above)
* Run `Build PE.cmd` which will do the following:
  * Load the WADK environment
  * Open `main.py` in notepad for configuration
  * Download all tools
  * Build both 32-bit & 64-bit PE images (exported as ISO files)

## Notes ##
1. PowerShell 6.0 on Windows 7 is not supported by the build script.
