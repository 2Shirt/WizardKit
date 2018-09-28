setterm -blank 0 -powerdown 0 2>/dev/null
if [ "$(fgconsole 2>/dev/null)" -eq "1" ]; then
    # Connect to network and update hostname
    $HOME/.update_network

    # Update settings if using i3
    if fgrep -q "i3" /proc/cmdline; then
        sed -i -r 's/#(own_window_type override)/\1/' ~/.conkyrc
        sed -i -r 's/openbox-session/i3/' ~/.xinitrc
    fi

    # Update Conky
    $HOME/.update_conky

    # Start X or HW-diags
    if ! fgrep -q "nox" /proc/cmdline; then
        startx >/dev/null
    else
        hw-diags cli
    fi
fi
