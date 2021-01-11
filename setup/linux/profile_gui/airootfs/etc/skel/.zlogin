setterm -blank 0 -powerdown 0 2>/dev/null
if [ "$(fgconsole 2>/dev/null)" -eq "1" ]; then
    # Connect to network and update hostname
    "${HOME}/.update_network"

    # Start X or HW-diags
    if ! fgrep -q "nox" /proc/cmdline; then
        # Show freeze warning
        echo ""
        echo "NOTE: Not all GPUs/displays are supported."
        echo "      If the system is frozen on this screen"
        echo "      please restart and try CLI mode instead"
        echo ""

        # Start x
        echo "Starting X..."
        startx >/dev/null 2>&1
    else
        hw-diags --cli
    fi
fi
