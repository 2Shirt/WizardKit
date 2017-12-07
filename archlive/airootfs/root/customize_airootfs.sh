#!/bin/bash

set -e -u

# Set hostname
echo "wk-arch" > /etc/hostname
echo "127.0.1.1      wk-arch.localdomain     wk-arch" >> /etc/hosts

# Set locale
sed -i 's/#\(en_US\.UTF-8\)/\1/' /etc/locale.gen
locale-gen

# Time Settings
ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
sed -i 's/#FallbackNTP/NTP/' /etc/systemd/timesyncd.conf
#timedatectl set-ntp true

# root user settings
usermod -s /usr/bin/zsh root
cp -aT /etc/skel/ /root/
rm /root/.zlogin
chmod 700 /root
echo "root:Abracadabra" | chpasswd

# Add autologin group
groupadd -r autologin

# Add wktech user
useradd -m -s /bin/zsh -G autologin,power,storage,wheel -U wktech
echo "wktech:Abracadabra" | chpasswd

# Enable sudo for %wheel
echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Set mirrorlist. Process:
##  Replace newlines with ~ to treat as single line
##  Uncomment all US mirrors
##  Resetore newlines
##  Rank mirrors to only use the top 10 mirrors
mv -b /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak
tmp_file="$(mktemp)"
tr '\n' '~' < /etc/pacman.d/mirrorlist.bak | sed -r 's/([0-1]\.[0-9], United States)~#/\1~/g' | tr '~' '\n' > "$tmp_file"
rankmirrors -n 10 "$tmp_file" | egrep '^S' > /etc/pacman.d/mirrorlist
rm -v "$tmp_file"

# journald settings (from archiso)
sed -i 's/#\(Storage=\)auto/\1volatile/' /etc/systemd/journald.conf

# logind settings (from archiso)
sed -i 's/#\(HandleSuspendKey=\)suspend/\1ignore/' /etc/systemd/logind.conf
sed -i 's/#\(HandleHibernateKey=\)hibernate/\1ignore/' /etc/systemd/logind.conf
sed -i 's/#\(HandleLidSwitch=\)suspend/\1ignore/' /etc/systemd/logind.conf

#systemctl enable pacman-init.service choose-mirror.service
systemctl set-default graphical.target
