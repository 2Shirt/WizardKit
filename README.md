# Wizard Kit #

A collection of scripts to help technicians service Windows systems.

## Layout ##

* Root
  * Main script launchers:
* `.bin`
  * Extracted programs: As compressed tools are run they will be extracted here.
  * `Scripts`
    * "Real" scripts live here and are run via their respective launchers.
* `.cbin`
  * This folder holds the compressed and encrypted tool archives. They are extracted at runtime as needed.
* `Data Recovery`
  * This folder is not copied by `Copy WizardKit.cmd` to help discourage recovering data to the same drive.
* `Data Transfers`
* `Diagnostics`
* `Drivers`
* `Installers`
* `Misc`
* `Repairs`
* `Uninstallers`

## Setup ##

* Replace ConEmu.png if desired
* Run `Build Kit.cmd` which will do the following:
  * Download 7-Zip, ConEmu, Notepad++, and Python (including wheel packages)
  * Open `.bin\Scripts\settings\main.py` in Notepad++ for configuration
  * Update the rest of the tools with the `.bin\Scripts\update_kit.py` script