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
sed -i -r 's/extensions.autoDisableScopes", [0-9]+/extensions.autoDisableScopes", 0/' /usr/lib/firefox/browser/defaults/preferences/vendor.js

# Set mirrorlist
echo "[customize_airootfs] INFO: Setup pacman mirrorlist"
## Process:
##  Replace newlines with ~ to treat as single line
##  Uncomment all US mirrors
##  Resetore newlines
##  Rank mirrors to only use the top 10 mirrors
### BROKEN ###
#mv -bv /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak
#tmp_file="$(mktemp)"
#tr '\n' '~' < /etc/pacman.d/mirrorlist.bak | sed -r 's/([0-1]\.[0-9], United States)~#/\1~/g' | tr '~' '\n' > "$tmp_file"
#rankmirrors -n 10 "$tmp_file" | egrep '^S' > /etc/pacman.d/mirrorlist
#rm -v "$tmp_file"
### List ranked on 2017-06-08 ###
echo 'Server = http://mirror.htnshost.com/archlinux/$repo/os/$arch' > /etc/pacman.d/mirrorlist
echo 'Server = http://ftp.osuosl.org/pub/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = https://mirrors.kernel.org/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirrors.cat.pdx.edu/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirror.lty.me/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirrors.kernel.org/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = https://mirror.lty.me/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirrors.xmission.com/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = https://mirrors.ocf.berkeley.edu/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirrors.ocf.berkeley.edu/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist

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
