# Wizard Kit #

A collection of scripts to help technicians service Windows systems.

## Main Kit ##

### Build Requirements ###

* PowerShell 3.0 or newer<sup>1</sup>
* 10 Gb disk space

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

## Live Linux ##

### Build Requirements ###

* Arch Linux
* 6 Gb disk space

### Initial Setup ###

* Replace artwork as desired
* Install Arch Linux in a virtual machine ([VirtualBox](https://www.virtualbox.org/) is a good option for Windows systems).
  * See the [installation guide](https://wiki.archlinux.org/index.php/Installation_guide) for details.
* Add a standard user to the Arch Linux installation.
  * See the [wiki page](https://wiki.archlinux.org/index.php/Users_and_groups#User_management) for details.
* Install git # `pacman -Syu git`
* _(Recommended)_ Install and configure `sudo`
  * See the [wiki page](https://wiki.archlinux.org/index.php/Sudo) for details.
* Login to the user added above
* Download the Github repo $ `git clone https://github.com/2Shirt/WizardKit.git`
* Run the build script
  * $ `cd WizardKit`
  * $ `./Build\ Linux -b`
  * The build script does the following:
    * Installs missing dependencies via `pacman`
    * Opens `main.py` in `nano` for configuration
    * Downloads, builds, and adds AUR packages to a local repo
    * Builds the Live Linux ISO

### Notes ###

* The WinPE boot options require files to be copied from a completed WinPE build.
  * This is done below for the Combined UFD

## Windows PE ##

### Build Requirements ###

* Windows Assessment and Deployment Kit for Windows 10
  * Deployment Tools
  * Windows Preinstallation Environment (Windows PE)
  * _All other features are not required_
* PowerShell 3.0 or newer
* 8 Gb disk space

### Initial Setup ###

* Replace artwork as desired
* Run `Build PE.cmd` which will do the following:
  * Load the WADK environment
  * Open `main.py` in notepad for configuration
  * Download all tools
  * Build both 32-bit & 64-bit PE images (exported as ISO files)

## Combined Wizard Kit ##

### Build Requirements ###

* 64-bit system or virtual machine
* 4 Gb RAM
* 8 Gb USB flash drive _(16 Gb or larger recommended)_

### Overview ###

There's a `build-ufd` script which does the following:

* Checks for the presence if the Linux ISO and the (64-bit) WinPE ISO.
* Formats the selected UFD using FAT32.
  * All data will be deleted from the UFD resulting in **DATA LOSS**.
* Copies the required files from the Linux ISO, WinPE ISO, and Main Kit folder to the UFD.
* Installs Syslinux to the UFD making it bootable on legacy systems.
* Sets the boot files/folders to be hidden under Windows.

### Setup ###

* Boot to a Live Linux ISO built following the instructions above.
  * You can apply it to a UFD using [rufus](https://rufus.akeo.ie/) for physical systems.
  * Virtual machines should be able to use the Linux ISO directly.
* Mount the device(s) or network share(s) that contain the Linux ISO, WinPE ISO, and Main Kit folder.
* Connect the UFD but don't mount it.
* Get the device name of the UFD.
  * You can use $ `hw-drive-info` to help.
* $ `sudo build-ufd --ufd-device [device] --linux-iso [path] --main-kit [path] --winpe-iso [path]`
  * **2nd Warning**: All data will be erased from the UFD resulting in **DATA LOSS**.
  * NOTE: The Main Kit folder will be renamed on the UFD using `$KIT_NAME_FULL`
    * `$KIT_NAME_FULL` defaults to "Wizard Kit" but can be changed in `main.py`
  * You can include extra items by using the `--extra-dir` option
    * _(e.g. $ `sudo build-ufd --ufd-device [device] --linux-iso [path] --main-kit [path] --winpe-iso [path] --extra-dir [path]`)_
  * To include images for the WinPE Setup section, put the files in "Extras/images".
    * WinPE Setup will recognize ESD, WIM, and SWM<sup>2</sup> images.
    * The filenames should be "Win7", "Win8", or "Win10"

## Notes ##
1. PowerShell 6.0 on Windows 7 is not supported by the build script.
2. See [wimlib-imagex](https://wimlib.net/) for details about split WIM images.
