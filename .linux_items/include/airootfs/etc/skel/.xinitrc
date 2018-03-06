#!/bin/sh

dbus-update-activation-environment --systemd DISPLAY
xrdb -merge $HOME/.Xresources
xset s off
xset -dpms
eval $(ssh-agent)
export SSH_AUTH_SOCK
compton &
sleep 1s
conky -d
nm-applet &
cbatticon &
volumeicon &
connect-to-network &
(sleep 5s && killall dunst) &
$HOME/.urxvt_default_res &
$HOME/.update_wallpaper &
$HOME/.update_conky &
exec openbox-session
