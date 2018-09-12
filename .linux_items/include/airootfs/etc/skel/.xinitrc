#!/bin/sh

dbus-update-activation-environment --systemd DISPLAY
xrdb -merge $HOME/.Xresources
xset s off
xset -dpms
eval $(ssh-agent)
export SSH_AUTH_SOCK
compton --backend xrender --xrender-sync --xrender-sync-fence &
sleep 1s
conky -d
nm-applet &
cbatticon &
volumeicon &
$HOME/.update_hostname
connect-to-network &
(sleep 5s && killall dunst) &
$HOME/.urxvt_default_res &
$HOME/.update_wallpaper &
exec openbox-session
