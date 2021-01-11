#!/bin/sh

dbus-update-activation-environment --systemd DISPLAY
export DISPLAY_SESSION="Openbox"
export PATH="$HOME/.config/rofi/bin:$PATH"
eval $(ssh-agent)
export SSH_AUTH_SOCK
xrdb -merge $HOME/.Xresources
exec openbox-session

