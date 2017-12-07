#!/bin/sh

xrdb -merge $HOME/.Xresources
compton &
sleep 1s
conky -d
$HOME/.network_start &
$HOME/.urxvt_default_res &
$HOME/.update_wallpaper &
exec i3
