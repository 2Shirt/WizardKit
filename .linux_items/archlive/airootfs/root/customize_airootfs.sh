#!/bin/bash

set -e -u

# Set hostname
echo "[customize_airootfs] INFO: Set hostname"
echo "wk-arch" > /etc/hostname
echo "127.0.1.1      wk-arch.localdomain     wk-arch" >> /etc/hosts

# Set locale
echo "[customize_airootfs] INFO: Set locale"
sed -i 's/#\(en_US\.UTF-8\)/\1/' /etc/locale.gen
locale-gen

# Time Settings
echo "[customize_airootfs] INFO: Set time"
ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
sed -i 's/#FallbackNTP/NTP/' /etc/systemd/timesyncd.conf
#timedatectl set-ntp true

# root user settings
echo "[customize_airootfs] INFO: Setup root user"
usermod -s /usr/bin/zsh root
cp -aT /etc/skel/ /root/
rm /root/.ssh/id*
rm /root/.zlogin
chmod 700 /root
echo "root:Abracadabra" | chpasswd

# wktech user settings
echo "[customize_airootfs] INFO: Setup wktech user"
groupadd -r autologin
useradd -m -s /bin/zsh -G autologin,power,storage,wheel -U wktech
echo "wktech:Abracadabra" | chpasswd

# Enable sudo for %wheel
echo "[customize_airootfs] INFO: Enable sudo"
echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Misc
echo "[customize_airootfs] INFO: Misc Settings"
#sed -i -r 's/extensions.autoDisableScopes", [0-9]+/extensions.autoDisableScopes", 0/' /usr/lib/firefox/browser/defaults/preferences/vendor.js
mkdir /media

# Set mirrorlist
echo "[customize_airootfs] INFO: Setup pacman mirrorlist"
# Ranked on 2017-10-19
echo 'Server = http://mirrors.cat.pdx.edu/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
echo 'Server = http://mirrors.advancedhosters.com/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://archlinux.surlyjake.com/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirrors.acm.wpi.edu/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = https://archlinux.surlyjake.com/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://ca.us.mirror.archlinux-br.org/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = https://arlm.tyzoid.com/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirror.rackspace.com/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://il.us.mirror.archlinux-br.org/$repo/os/$arch' >> /etc/pacman.d/mirrorlist

# journald settings (from archiso)
echo "[customize_airootfs] INFO: Setup journald"
sed -i 's/#\(Storage=\)auto/\1volatile/' /etc/systemd/journald.conf

# logind settings (from archiso)
echo "[customize_airootfs] INFO: Setup logind"
sed -i 's/#\(HandleSuspendKey=\)suspend/\1ignore/' /etc/systemd/logind.conf
sed -i 's/#\(HandleHibernateKey=\)hibernate/\1ignore/' /etc/systemd/logind.conf
sed -i 's/#\(HandleLidSwitch=\)suspend/\1ignore/' /etc/systemd/logind.conf

echo "[customize_airootfs] INFO: Setup systemd"
#systemctl enable pacman-init.service choose-mirror.service
#systemctl set-default graphical.target

echo "[customize_airootfs] INFO: Completed."
