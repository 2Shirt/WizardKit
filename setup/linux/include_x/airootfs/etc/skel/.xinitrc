#!/bin/sh

dbus-update-activation-environment --systemd DISPLAY
eval $(ssh-agent)
export SSH_AUTH_SOCK
xrdb -merge $HOME/.Xresources
exec openbox-session

