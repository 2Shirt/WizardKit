setterm -blank 0 -powerdown 0
if [ "$(fgconsole 2>/dev/null)" -eq "1" ]; then
    if ! fgrep -q "nox" /proc/cmdline; then
        if fgrep -q "i3" /proc/cmdline; then
            sed -i -r 's/#(own_window_type override)/\1/' ~/.conkyrc
            sed -i -r 's/openbox-session/i3/' ~/.xinitrc
        fi
        startx
    else
        hw-diags cli
    fi
fi

