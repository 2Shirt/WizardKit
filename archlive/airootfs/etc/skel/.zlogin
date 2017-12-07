setterm -blank 0 -powerdown 0
if [ "$(fgconsole 2>/dev/null)" -eq "1" ]; then
    hw-diags cli
fi
