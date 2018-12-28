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
        # Kill Xorg after 30 seconds if it doesn't fully initialize
        (sleep 30s; if ! [[ -f "/tmp/x_ok" ]]; then pkill '(Xorg|startx)'; fi) &

        # Try starting X
        startx >/dev/null

        # Run Hw-Diags CLI if necessary
        if ! [[ -f "/tmp/x_ok" ]]; then
            echo "There was an issue starting Xorg, starting CLI interface..."
            sleep 2s
            hw-diags --cli
        fi
    else
        hw-diags --cli
    fi
fi
