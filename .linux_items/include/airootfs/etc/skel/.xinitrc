#!/bin/sh

dbus-update-activation-environment --systemd DISPLAY
$HOME/.update_dpi_settings
xrdb -merge $HOME/.Xresources
xset s off
xset -dpms
eval $(ssh-agent)
export SSH_AUTH_SOCK
compton --backend xrender --xrender-sync --xrender-sync-fence &
sleep 1s
conky -d
nm-applet &
volumeicon &
connect-to-network &
$HOME/.update_hostname &
feh --bg-fill "$HOME/.wallpaper" &
x0vncserver -display :0 -passwordfile $HOME/.vnc/passwd -AlwaysShared &
exec openbox-session
