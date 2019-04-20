#!/usr/bin/env bash
#
## Wizard Kit: UFD Build Tool
#
# Based on a template by BASH3 Boilerplate v2.3.0
# http://bash3boilerplate.sh/#authors
#
# The MIT License (MIT)
# Copyright (c) 2013 Kevin van Zonneveld and contributors
# You are not obligated to bundle the LICENSE file with your b3bp projects as long
# as you leave these references intact in the header comments of your source files.

# Exit on error. Append "|| true" if you expect an error.
set -o errexit
# Exit on error inside any functions or subshells.
set -o errtrace
# Do not allow use of undefined vars. Use ${VAR:-} to use an undefined VAR
set -o nounset
# Catch the error in case mysqldump fails (but gzip succeeds) in `mysqldump |gzip`
set -o pipefail
# Turn on traces, useful while debugging but commented out by default
# set -o xtrace

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  __i_am_main_script="0" # false

  if [[ "${__usage+x}" ]]; then
    if [[ "${BASH_SOURCE[1]}" = "${0}" ]]; then
      __i_am_main_script="1" # true
    fi

    __b3bp_external_usage="true"
    __b3bp_tmp_source_idx=1
  fi
else
  __i_am_main_script="1" # true
  [[ "${__usage+x}" ]] && unset -v __usage
  [[ "${__helptext+x}" ]] && unset -v __helptext
fi

# Set magic variables for current file, directory, os, etc.
__dir="$(cd "$(dirname "${BASH_SOURCE[${__b3bp_tmp_source_idx:-0}]}")" && pwd)"
__file="${__dir}/$(basename "${BASH_SOURCE[${__b3bp_tmp_source_idx:-0}]}")"
__base="$(basename "${__file}" .sh)"
__wd="$(pwd)"
__usage_example="Usage: sudo $(basename "${0}") --ufd-device [device] --linux-iso [path] --main-kit [path] --winpe-iso [path]"
__all_args=""
for a in "${@}"; do
    if [[ "${a:0:1}" == "-" ]]; then
        __all_args="${__all_args} ${a}"
    else
        __all_args="${__all_args} \"${a}\""
    fi
done


# Define the environment variables (and their defaults) that this script depends on
LOG_LEVEL="${LOG_LEVEL:-6}" # 7 = debug -> 0 = emergency
NO_COLOR="${NO_COLOR:-}"    # true = disable color. otherwise autodetected


### Functions
##############################################################################

function __b3bp_log () {
  local log_level="${1}"
  shift

  # shellcheck disable=SC2034
  local color_debug="\x1b[35m"
  # shellcheck disable=SC2034
  local color_info="\x1b[32m"
  # shellcheck disable=SC2034
  local color_notice="\x1b[34m"
  # shellcheck disable=SC2034
  local color_warning="\x1b[33m"
  # shellcheck disable=SC2034
  local color_error="\x1b[31m"
  # shellcheck disable=SC2034
  local color_critical="\x1b[1;31m"
  # shellcheck disable=SC2034
  local color_alert="\x1b[1;33;41m"
  # shellcheck disable=SC2034
  local color_emergency="\x1b[1;4;5;33;41m"

  local colorvar="color_${log_level}"

  local color="${!colorvar:-${color_error}}"
  local color_reset="\x1b[0m"

  if [[ "${NO_COLOR:-}" = "true" ]] || ( [[ "${TERM:-}" != *"256color"* ]] && [[ "${TERM:-}" != "xterm"* ]] && [[ "${TERM:-}" != "screen"* ]] ) || [[ ! -t 2 ]]; then
    if [[ "${NO_COLOR:-}" != "false" ]]; then
      # Don't use colors on pipes or non-recognized terminals
      color=""; color_reset=""
    fi
  fi

  # all remaining arguments are to be printed
  local log_line=""

  while IFS=$'\n' read -r log_line; do
    echo -e "$(date -u +"%Y-%m-%d %H:%M:%S UTC") ${color}$(printf "[%9s]" "${log_level}")${color_reset} ${log_line}" 1>&2
  done <<< "${@:-}"
}

function emergency () {                                __b3bp_log emergency "${@}"; exit 1; }
function alert ()     { [[ "${LOG_LEVEL:-0}" -ge 1 ]] && __b3bp_log alert "${@}"; true; }
function critical ()  { [[ "${LOG_LEVEL:-0}" -ge 2 ]] && __b3bp_log critical "${@}"; true; }
function error ()     { [[ "${LOG_LEVEL:-0}" -ge 3 ]] && __b3bp_log error "${@}"; true; }
function warning ()   { [[ "${LOG_LEVEL:-0}" -ge 4 ]] && __b3bp_log warning "${@}"; true; }
function notice ()    { [[ "${LOG_LEVEL:-0}" -ge 5 ]] && __b3bp_log notice "${@}"; true; }
function info ()      { [[ "${LOG_LEVEL:-0}" -ge 6 ]] && __b3bp_log info "${@}"; true; }
function debug ()     { [[ "${LOG_LEVEL:-0}" -ge 7 ]] && __b3bp_log debug "${@}"; true; }

function help () {
  echo "" 1>&2
  echo " ${*}" 1>&2
  echo "" 1>&2
  echo "  ${__usage:-No usage available}" 1>&2
  echo "" 1>&2

  if [[ "${__helptext:-}" ]]; then
    echo " ${__helptext}" 1>&2
    echo "" 1>&2
  fi

  exit 1
}


### Parse commandline options
##############################################################################

# Commandline options. This defines the usage page, and is used to parse cli
# opts & defaults from. The parsing is unforgiving so be precise in your syntax
# - A short option must be preset for every long option; but every short option
#   need not have a long option
# - `--` is respected as the separator between options and arguments
# - We do not bash-expand defaults, so setting '~/app' as a default will not resolve to ${HOME}.
#   you can use bash variables to work around this (so use ${HOME} instead)

# shellcheck disable=SC2015
[[ "${__usage+x}" ]] || read -r -d '' __usage <<-'EOF' || true # exits non-zero when EOF encountered
  OPTIONS:
  -u --ufd-device [arg] Device to which the kit will be applied
  -l --linux-iso  [arg] Path to the Linux ISO

  -e --extra-dir  [arg] Path to the Extra folder (optional)
  -m --main-kit   [arg] Path to the Main Kit (optional)
  -w --winpe-iso  [arg] Path to the WinPE ISO (optional)
  -h --help             This page

  ADVANCED:
  -d --debug            Enable debug mode
  -v --verbose          Enable verbose mode
  -M --use-mbr          Use real MBR instead of GPT w/ Protective MBR
  -F --force            Bypass all confirmation messages. USE WITH EXTREME CAUTION!
EOF

# shellcheck disable=SC2015
[[ "${__helptext+x}" ]] || read -r -d '' __helptext <<-'EOF' || true # exits non-zero when EOF encountered
 Paths can be relative to the current working directory or absolute
EOF

# Translate usage string -> getopts arguments, and set $arg_<flag> defaults
while read -r __b3bp_tmp_line; do
  if [[ "${__b3bp_tmp_line}" =~ ^- ]]; then
    # fetch single character version of option string
    __b3bp_tmp_opt="${__b3bp_tmp_line%% *}"
    __b3bp_tmp_opt="${__b3bp_tmp_opt:1}"

    # fetch long version if present
    __b3bp_tmp_long_opt=""

    if [[ "${__b3bp_tmp_line}" = *"--"* ]]; then
      __b3bp_tmp_long_opt="${__b3bp_tmp_line#*--}"
      __b3bp_tmp_long_opt="${__b3bp_tmp_long_opt%% *}"
    fi

    # map opt long name to+from opt short name
    printf -v "__b3bp_tmp_opt_long2short_${__b3bp_tmp_long_opt//-/_}" '%s' "${__b3bp_tmp_opt}"
    printf -v "__b3bp_tmp_opt_short2long_${__b3bp_tmp_opt}" '%s' "${__b3bp_tmp_long_opt//-/_}"

    # check if option takes an argument
    if [[ "${__b3bp_tmp_line}" =~ \[.*\] ]]; then
      __b3bp_tmp_opt="${__b3bp_tmp_opt}:" # add : if opt has arg
      __b3bp_tmp_init=""  # it has an arg. init with ""
      printf -v "__b3bp_tmp_has_arg_${__b3bp_tmp_opt:0:1}" '%s' "1"
    elif [[ "${__b3bp_tmp_line}" =~ \{.*\} ]]; then
      __b3bp_tmp_opt="${__b3bp_tmp_opt}:" # add : if opt has arg
      __b3bp_tmp_init=""  # it has an arg. init with ""
      # remember that this option requires an argument
      printf -v "__b3bp_tmp_has_arg_${__b3bp_tmp_opt:0:1}" '%s' "2"
    else
      __b3bp_tmp_init="0" # it's a flag. init with 0
      printf -v "__b3bp_tmp_has_arg_${__b3bp_tmp_opt:0:1}" '%s' "0"
    fi
    __b3bp_tmp_opts="${__b3bp_tmp_opts:-}${__b3bp_tmp_opt}"
  fi

  [[ "${__b3bp_tmp_opt:-}" ]] || continue

  if [[ "${__b3bp_tmp_line}" =~ (^|\.\ *)Default= ]]; then
    # ignore default value if option does not have an argument
    __b3bp_tmp_varname="__b3bp_tmp_has_arg_${__b3bp_tmp_opt:0:1}"

    if [[ "${!__b3bp_tmp_varname}" != "0" ]]; then
      __b3bp_tmp_init="${__b3bp_tmp_line##*Default=}"
      __b3bp_tmp_re='^"(.*)"$'
      if [[ "${__b3bp_tmp_init}" =~ ${__b3bp_tmp_re} ]]; then
        __b3bp_tmp_init="${BASH_REMATCH[1]}"
      else
        __b3bp_tmp_re="^'(.*)'$"
        if [[ "${__b3bp_tmp_init}" =~ ${__b3bp_tmp_re} ]]; then
          __b3bp_tmp_init="${BASH_REMATCH[1]}"
        fi
      fi
    fi
  fi

  if [[ "${__b3bp_tmp_line}" =~ (^|\.\ *)Required\. ]]; then
    # remember that this option requires an argument
    printf -v "__b3bp_tmp_has_arg_${__b3bp_tmp_opt:0:1}" '%s' "2"
  fi

  printf -v "arg_${__b3bp_tmp_opt:0:1}" '%s' "${__b3bp_tmp_init}"
done <<< "${__usage:-}"

# run getopts only if options were specified in __usage
if [[ "${__b3bp_tmp_opts:-}" ]]; then
  # Allow long options like --this
  __b3bp_tmp_opts="${__b3bp_tmp_opts}-:"

  # Reset in case getopts has been used previously in the shell.
  OPTIND=1

  # start parsing command line
  set +o nounset # unexpected arguments will cause unbound variables
                 # to be dereferenced
  # Overwrite $arg_<flag> defaults with the actual CLI options
  while getopts "${__b3bp_tmp_opts}" __b3bp_tmp_opt; do
    [[ "${__b3bp_tmp_opt}" = "?" ]] && help "Invalid use of script: ${*} "

    if [[ "${__b3bp_tmp_opt}" = "-" ]]; then
      # OPTARG is long-option-name or long-option=value
      if [[ "${OPTARG}" =~ .*=.* ]]; then
        # --key=value format
        __b3bp_tmp_long_opt=${OPTARG/=*/}
        # Set opt to the short option corresponding to the long option
        __b3bp_tmp_varname="__b3bp_tmp_opt_long2short_${__b3bp_tmp_long_opt//-/_}"
        printf -v "__b3bp_tmp_opt" '%s' "${!__b3bp_tmp_varname}"
        OPTARG=${OPTARG#*=}
      else
        # --key value format
        # Map long name to short version of option
        __b3bp_tmp_varname="__b3bp_tmp_opt_long2short_${OPTARG//-/_}"
        printf -v "__b3bp_tmp_opt" '%s' "${!__b3bp_tmp_varname}"
        # Only assign OPTARG if option takes an argument
        __b3bp_tmp_varname="__b3bp_tmp_has_arg_${__b3bp_tmp_opt}"
        printf -v "OPTARG" '%s' "${@:OPTIND:${!__b3bp_tmp_varname}}"
        # shift over the argument if argument is expected
        ((OPTIND+=__b3bp_tmp_has_arg_${__b3bp_tmp_opt}))
      fi
      # we have set opt/OPTARG to the short value and the argument as OPTARG if it exists
    fi
    __b3bp_tmp_varname="arg_${__b3bp_tmp_opt:0:1}"
    __b3bp_tmp_default="${!__b3bp_tmp_varname}"

    __b3bp_tmp_value="${OPTARG}"
    if [[ -z "${OPTARG}" ]] && [[ "${__b3bp_tmp_default}" = "0" ]]; then
      __b3bp_tmp_value="1"
    fi

    printf -v "${__b3bp_tmp_varname}" '%s' "${__b3bp_tmp_value}"
    debug "cli arg ${__b3bp_tmp_varname} = (${__b3bp_tmp_default}) -> ${!__b3bp_tmp_varname}"
  done
  set -o nounset # no more unbound variable references expected

  shift $((OPTIND-1))

  if [[ "${1:-}" = "--" ]] ; then
    shift
  fi
fi


### Automatic validation of required option arguments
##############################################################################

for __b3bp_tmp_varname in ${!__b3bp_tmp_has_arg_*}; do
  # validate only options which required an argument
  [[ "${!__b3bp_tmp_varname}" = "2" ]] || continue

  __b3bp_tmp_opt_short="${__b3bp_tmp_varname##*_}"
  __b3bp_tmp_varname="arg_${__b3bp_tmp_opt_short}"
  [[ "${!__b3bp_tmp_varname}" ]] && continue

  __b3bp_tmp_varname="__b3bp_tmp_opt_short2long_${__b3bp_tmp_opt_short}"
  printf -v "__b3bp_tmp_opt_long" '%s' "${!__b3bp_tmp_varname}"
  [[ "${__b3bp_tmp_opt_long:-}" ]] && __b3bp_tmp_opt_long=" (--${__b3bp_tmp_opt_long//_/-})"

  help "Option -${__b3bp_tmp_opt_short}${__b3bp_tmp_opt_long:-} requires an argument"
done


### Cleanup Environment variables
##############################################################################

for __tmp_varname in ${!__b3bp_tmp_*}; do
  unset -v "${__tmp_varname}"
done

unset -v __tmp_varname


### Externally supplied __usage. Nothing else to do here
##############################################################################

if [[ "${__b3bp_external_usage:-}" = "true" ]]; then
  unset -v __b3bp_external_usage
  return
fi


### Signal trapping and backtracing
##############################################################################

function __b3bp_cleanup_before_exit () {
  if [[ "$EUID" -eq 0 ]]; then
    for d in Dest Linux WinPE; do
      if [[ -d "/mnt/${d}" ]]; then
        umount "/mnt/${d}" || true
        rmdir "/mnt/${d}" || true
      fi
    done
  fi
  if [[ "${?}" != "0" ]]; then
    info "Sources unmounted"
  fi
  if [[ ${arg_F:-} == 0 && "${SILENT:-False}" == "False" ]]; then
    read -r -p "Press Enter to exit... " ignored_var 2>&1
  fi
}
trap __b3bp_cleanup_before_exit EXIT

# requires `set -o errtrace`
__b3bp_err_report() {
    local error_code
    error_code=${?}
    error "Error in ${__file} in function ${1} on line ${2}"
    exit ${error_code}
}
# Uncomment the following line for always providing an error backtrace
trap '__b3bp_err_report "${FUNCNAME:-.}" ${LINENO}' ERR


### Command-line argument switches (like -d for debugmode, -h for showing helppage)
##############################################################################

# debug mode
if [[ "${arg_d:?}" = "1" ]]; then
  set -o xtrace
  LOG_LEVEL="7"
  # Enable error backtracing
  trap '__b3bp_err_report "${FUNCNAME:-.}" ${LINENO}' ERR
fi

# verbose mode
if [[ "${arg_v:?}" = "1" ]]; then
  set -o verbose
fi


### Validation. Error out if the things required for your script are not present
##############################################################################

if [[ "${arg_F:?}" == 1 ]]; then
    SILENT="True"
else
    SILENT="False"
fi
if [[ "${arg_M:?}" == 1 ]]; then
    USE_MBR="True"
else
    USE_MBR="False"
fi

if [[ "${arg_h:?}" == 1 ]]; then
    help "${__usage_example}"
else
    # Print warning line
    [[ "${arg_u:-}" ]] || echo " -u or --ufd-device is required"
    [[ "${arg_l:-}" ]] || echo " -l or --linux-iso is required"

    # Bail if necessary
    [[ "${arg_u:-}" ]] || help "${__usage_example}"
    [[ "${arg_l:-}" ]] || help "${__usage_example}"
fi
[[ "${LOG_LEVEL:-}" ]] || emergency "Cannot continue without LOG_LEVEL. "


### More functions
##############################################################################

function abort () {
    local abort_message="Aborted"
    [[ "${1:-}" ]] && abort_message="${1}" || true
    error "${abort_message}"
    #echo -e "${YELLOW}${abort_message}${CLEAR}"
    exit 1
}

function ask() {
    if [[ "${SILENT}" == "True" ]]; then
        echo -e "${1:-} Yes ${BLUE}(Silent)${CLEAR}"
        return 0
    fi
    while :; do
        read -p "${1:-} [Y/N] " -r answer
        if echo "$answer" | egrep -iq '^(y|yes|sure)$'; then
            return 0
        elif echo "$answer" | egrep -iq '^(n|no|nope)$'; then
            return 1
        fi
    done
}


### Runtime
##############################################################################

# VARIABLES
DEST_DEV="${arg_u}"
DEST_PAR="${DEST_DEV}1"
LOG_FILE="$(getent passwd "$SUDO_USER" | cut -d: -f6)/Logs/build-ufd_${DEST_DEV##*/}_$(date +%Y-%m-%d_%H%M_%z).log"
MAIN_PY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/settings/main.py"
RSYNC_ARGS="-hrtuvS --modify-window=1 --progress"
MAIN_KIT="$(realpath "${arg_m:-}" 2>/dev/null || true)"
LINUX_ISO="$(realpath "${arg_l:-}" 2>/dev/null || true)"
WINPE_ISO="$(realpath "${arg_w:-}" 2>/dev/null || true)"
EXTRA_DIR="$(realpath "${arg_e:-}" 2>/dev/null || true)"
mkdir -p "$(dirname "$LOG_FILE")"
chown "$SUDO_USER:$SUDO_USER" -R "$(dirname "$LOG_FILE")"

# COLORS
CLEAR="\e[0m"
RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"

# Load main.py settings
if [ ! -f "${MAIN_PY}" ]; then
    echo -e "${RED}ERROR${CLEAR}: ${MAIN_PY} not found."
    abort
fi
while read line; do
    if echo "${line}" | egrep -q "^\w+='"; then
        line="$(echo "${line}" | sed -r 's/[\r\n]+//')"
        eval "${line}"
    fi
done < "${MAIN_PY}"
if [ -z ${KIT_NAME_FULL+x} ]; then
    # KIT_NAME_FULL is not set, assume main.py missing or malformatted
    echo -e "${RED}ERROR${CLEAR}: failed to load settings from ${MAIN_PY}"
    abort
fi
ISO_LABEL="${KIT_NAME_SHORT}_LINUX"
UFD_LABEL="${KIT_NAME_SHORT}_UFD"

# Check if root
if [[ "$EUID" -ne 0 ]]; then
    echo -e "${RED}ERROR${CLEAR}: This script must be run as root."
    abort
fi

# Check if in tmux
if ! tmux list-session 2>/dev/null | grep -q "build-ufd"; then
    # Reload in tmux
    eval tmux new-session -s "build-ufd" "${0:-}" ${__all_args}
    SILENT="True" # avoid two "Press Enter to exit..." prompts
    exit 0
fi

# Header
echo -e "${GREEN}${KIT_NAME_FULL}${CLEAR}: UFD Build Tool"
echo ""

# Verify sources
[[ -b "${DEST_DEV}" ]] || abort "${DEST_DEV} is not a valid device."
[[ -e "${LINUX_ISO}" ]] || abort "Linux ISO not found."
if [[ ! -z "${arg_m:-}" ]]; then
  [[ -d "${MAIN_KIT}/.bin" ]] || abort "Invalid Main Kit, ${MAIN_KIT}/.bin not found."
fi
if [[ ! -z "${arg_w:-}" ]]; then
  [[ -e "${WINPE_ISO}" ]] || abort "WinPE ISO not found."
fi
if [[ ! -z "${arg_e:-}" ]]; then
    [[ -d "${EXTRA_DIR}" ]] || abort "Extra Dir not found."
fi

# Print Info
echo -e "${BLUE}Sources${CLEAR}" | tee -a "${LOG_FILE}"
echo "Main Kit:  ${MAIN_KIT}" | tee -a "${LOG_FILE}"
echo "Linux ISO: ${LINUX_ISO}" | tee -a "${LOG_FILE}"
echo "WinPE ISO: ${WINPE_ISO}" | tee -a "${LOG_FILE}"
echo "Extra Dir: ${EXTRA_DIR:-(Not Specified)}" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"
echo -e "${BLUE}Destination${CLEAR}" | tee -a "${LOG_FILE}"
lsblk -n -o NAME,LABEL,SIZE,MODEL,SERIAL "${DEST_DEV}" | tee -a "${LOG_FILE}"
if [[ "${USE_MBR}" == "True" ]]; then
    echo -e "${YELLOW}Formatting using legacy MBR${CLEAR}" | tee -a "${LOG_FILE}"
fi
echo "" | tee -a "${LOG_FILE}"

# Ask before starting job
echo ""
if ask "Is the above information correct?"; then
    echo ""
    echo -e "${YELLOW}SAFETY CHECK${CLEAR}"
    echo "All data will be DELETED from the disk and partition(s) listed above."
    echo -e "This is irreversible and will lead to ${RED}DATA LOSS.${CLEAR}"
    if ! ask "Asking again to confirm, is this correct?"; then
        abort
    fi
else
    abort
fi

# Start Build
echo "" | tee -a "${LOG_FILE}"
echo -e "${GREEN}Building Kit${CLEAR}" | tee -a "${LOG_FILE}"
touch "${LOG_FILE}"
tmux split-window -dl 10 tail -f "${LOG_FILE}"

# Zero beginning of device
dd bs=4M count=16 if=/dev/zero of="${DEST_DEV}" >> "${LOG_FILE}" 2>&1

# Format
echo "Formatting drive..." | tee -a "${LOG_FILE}"
if [[ "${USE_MBR}" == "True" ]]; then
    parted "${DEST_DEV}" --script -- mklabel msdos mkpart primary fat32 4MiB -1s >> "${LOG_FILE}" 2>&1
    parted "${DEST_DEV}" set 1 boot on >> "${LOG_FILE}" 2>&1
else
    parted "${DEST_DEV}" --script -- mklabel gpt mkpart primary fat32 4MiB -4MiB >> "${LOG_FILE}" 2>&1
    parted "${DEST_DEV}" set 1 legacy_boot on >> "${LOG_FILE}" 2>&1
    #parted "${DEST_DEV}" disk_set pmbr_boot on >> "${LOG_FILE}" 2>&1
    # pmbr_boot breaks detection on some UEFI MOBOs
fi
mkfs.vfat -F 32 -n "${UFD_LABEL}" "${DEST_PAR}" >> "${LOG_FILE}" 2>&1

# Mount sources and dest
echo "Mounting sources and destination..." | tee -a "${LOG_FILE}"
mkdir /mnt/{Dest,Linux,WinPE} -p >> "${LOG_FILE}" 2>&1
mount ${DEST_PAR} /mnt/Dest >> "${LOG_FILE}" 2>&1
mount "${LINUX_ISO}" /mnt/Linux -r >> "${LOG_FILE}" 2>&1
if [[ ! -z "${arg_w:-}" ]]; then
  mount "${WINPE_ISO}" /mnt/WinPE -r >> "${LOG_FILE}" 2>&1
fi

# Find WinPE source
w_boot="$(find /mnt/WinPE -iwholename "/mnt/WinPE/Boot")"
w_boot_bcd="$(find /mnt/WinPE -iwholename "/mnt/WinPE/Boot/BCD")"
w_boot_sdi="$(find /mnt/WinPE -iwholename "/mnt/WinPE/Boot/boot.sdi")"
w_bootmgr="$(find /mnt/WinPE -iwholename "/mnt/WinPE/bootmgr")"
w_bootmgr_efi="$(find /mnt/WinPE -iwholename "/mnt/WinPE/bootmgr.efi")"
w_efi_boot="$(find /mnt/WinPE -iwholename "/mnt/WinPE/EFI/Boot")"
w_efi_microsoft="$(find /mnt/WinPE -iwholename "/mnt/WinPE/EFI/Microsoft")"
w_en_us="$(find /mnt/WinPE -iwholename "/mnt/WinPE/en-us")"
w_sources="$(find /mnt/WinPE -iwholename "/mnt/WinPE/sources")"

# Copy files
echo "Copying Linux files..." | tee -a "${LOG_FILE}"
rsync ${RSYNC_ARGS} /mnt/Linux/* /mnt/Dest/ >> "${LOG_FILE}" 2>&1
sed -i "s/${ISO_LABEL}/${UFD_LABEL}/" /mnt/Dest/EFI/boot/refind.conf
sed -i "s/${ISO_LABEL}/${UFD_LABEL}/" /mnt/Dest/arch/boot/syslinux/*cfg

echo "Copying WinPE files..." | tee -a "${LOG_FILE}"
if [[ ! -z "${arg_w:-}" ]]; then
  if [[ ! -z "${w_bootmgr:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_bootmgr}" /mnt/Dest/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_bootmgr_efi:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_bootmgr_efi}" /mnt/Dest/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_en_us:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_en_us}" /mnt/Dest/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_boot:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_boot}"/* /mnt/Dest/Boot/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_efi_boot:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_efi_boot}"/* /mnt/Dest/EFI/Microsoft/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_efi_microsoft:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_efi_microsoft}"/* /mnt/Dest/EFI/Microsoft/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_boot_bcd:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_boot_bcd}" /mnt/Dest/sources/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_boot_sdi:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_boot_sdi}" /mnt/Dest/sources/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_bootmgr:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_bootmgr}" /mnt/Dest/sources/ >> "${LOG_FILE}" 2>&1
  fi
  if [[ ! -z "${w_sources:-}" ]]; then
    rsync ${RSYNC_ARGS} "${w_sources}"/* /mnt/Dest/sources/ >> "${LOG_FILE}" 2>&1
  fi

  # Uncomment boot entries
  sed -i "s/#UFD-WINPE#//" /mnt/Dest/EFI/boot/refind.conf
  sed -i "s/#UFD-WINPE#//" /mnt/Dest/arch/boot/syslinux/*cfg
fi

echo "Copying Main Kit..." | tee -a "${LOG_FILE}"
if [[ ! -z "${arg_m:-}" ]]; then
  rsync ${RSYNC_ARGS} \
    "${MAIN_KIT}/" \
    "/mnt/Dest/${KIT_NAME_FULL}/" >> "${LOG_FILE}" 2>&1
fi

if [[ ! -z "${EXTRA_DIR:-}" ]]; then
    echo "Copying Extra files..." | tee -a "${LOG_FILE}"
    rsync ${RSYNC_ARGS} \
      "${EXTRA_DIR}"/ \
      /mnt/Dest/ >> "${LOG_FILE}" 2>&1
fi

# Install syslinux
echo "Copying Syslinux files..." | tee -a "${LOG_FILE}"
rsync ${RSYNC_ARGS} /usr/lib/syslinux/bios/*.c32 /mnt/Dest/arch/boot/syslinux/ >> "${LOG_FILE}" 2>&1
syslinux --install -d /arch/boot/syslinux/ ${DEST_PAR} >> "${LOG_FILE}" 2>&1

echo "Unmounting destination..." | tee -a "${LOG_FILE}"
umount /mnt/Dest >> "${LOG_FILE}" 2>&1
rmdir /mnt/Dest >> "${LOG_FILE}" 2>&1
sync

echo "Installing Syslinux MBR..." | tee -a "${LOG_FILE}"
if [[ "${USE_MBR}" == "True" ]]; then
    dd bs=440 count=1 if=/usr/lib/syslinux/bios/mbr.bin of=${DEST_DEV} >> "${LOG_FILE}" 2>&1
else
    dd bs=440 count=1 if=/usr/lib/syslinux/bios/gptmbr.bin of=${DEST_DEV} >> "${LOG_FILE}" 2>&1
fi
sync

# Cleanup
echo "Hiding boot files..." | tee -a "${LOG_FILE}"
echo "drive s: file=\"${DEST_PAR}\"" > /root/.mtoolsrc
echo 'mtools_skip_check=1' >> /root/.mtoolsrc
for item in arch Boot bootmgr{,.efi} EFI en-us images isolinux sources "${KIT_NAME_FULL}"/{.bin,.cbin}; do
    yes | mattrib +h "S:/${item}" >> "${LOG_FILE}" 2>&1 || true
done
sync

# Unmount Sources
echo "Unmounting sources..." | tee -a "${LOG_FILE}"
for d in Linux WinPE; do
    umount "/mnt/${d}" >> "${LOG_FILE}" 2>&1 || true
    rmdir "/mnt/${d}" >> "${LOG_FILE}" 2>&1 || true
done

# Close progress pane
pkill -f "tail.*${LOG_FILE}"

# Done
echo "" | tee -a "${LOG_FILE}"
echo "Done." | tee -a "${LOG_FILE}"
echo ""
exit 0
