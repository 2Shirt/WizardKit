setterm -blank 0 -powerdown 0 2>/dev/null
if [ "$(fgconsole 2>/dev/null)" -eq "1" ]; then
    # Connect to network and update hostname
    $HOME/.update_network

    # Start HW-diags
    hw-diags --cli
fi
