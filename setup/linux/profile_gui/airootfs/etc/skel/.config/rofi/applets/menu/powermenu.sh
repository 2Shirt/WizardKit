#!/usr/bin/env bash

## Author  : Aditya Shakya
## Mail    : adi1090x@gmail.com
## Github  : @adi1090x
## Twitter : @adi1090x

style="$($HOME/.config/rofi/applets/menu/style.sh)"

dir="$HOME/.config/rofi/applets/menu/configs/$style"
rofi_command="rofi -theme $dir/powermenu.rasi"

uptime=$(uptime -p | sed -e 's/up //g')
cpu=$($HOME/.config/rofi/bin/usedcpu)
memory=$($HOME/.config/rofi/bin/usedram)

# Options
shutdown=""
reboot=""
lock=""
suspend=""
logout=""

# Variable passed to rofi
options="$shutdown\n$reboot\n$logout"

chosen="$(echo -e "$options" | $rofi_command -p "  $uptime  |     $cpu  |  ﬙  $memory " -dmenu)"
case $chosen in
    $shutdown)
        wk-power-command poweroff
        ;;
    $reboot)
        wk-power-command reboot
        ;;
    $logout)
        wk-power-command logout
        ;;
esac
