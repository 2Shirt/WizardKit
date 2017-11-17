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

* Edit the `.bin\Scripts\settings\main.py` file to your liking.
* _**(Broken)**_ Run the `_Update Kit.cmd` file to populate `.bin` and `.cbin`.