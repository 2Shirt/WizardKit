#!/bin/bash

set -e -u

# Locale
sed -i 's/#\(en_US\.UTF-8\)/\1/' /etc/locale.gen
locale-gen

# Time Settings
ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
#sed -i 's/#FallbackNTP/NTP/' /etc/systemd/timesyncd.conf
#timedatectl set-ntp true

# root user settings
usermod -s /usr/bin/zsh root
cp -aT /etc/skel/ /root/
chmod 700 /root
echo "root:Abracadabra" | chpasswd

# Add autologin group
groupadd -r autologin

# Add wktech user
useradd -m -s /bin/zsh -G autologin,storage,wheel -U wktech
echo "wktech:Abracadabra" | chpasswd

# Enable sudo for %wheel
echo '%wheel ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Set pacman mirrorlist
echo 'Server = http://arch.localmsp.org/arch/$repo/os/$arch' > /etc/pacman.d/mirrorlist
echo 'Server = http://arch.mirrors.ionfish.org/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://lug.mtu.edu/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirror.rit.edu/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist
echo 'Server = http://mirror.us.leaseweb.net/archlinux/$repo/os/$arch' >> /etc/pacman.d/mirrorlist

# journald settings (from archiso)
sed -i 's/#\(Storage=\)auto/\1volatile/' /etc/systemd/journald.conf

# logind settings (from archiso)
sed -i 's/#\(HandleSuspendKey=\)suspend/\1ignore/' /etc/systemd/logind.conf
sed -i 's/#\(HandleHibernateKey=\)hibernate/\1ignore/' /etc/systemd/logind.conf
sed -i 's/#\(HandleLidSwitch=\)suspend/\1ignore/' /etc/systemd/logind.conf

# Startup settings
#systemctl set-default multi-user.target
systemctl set-default graphical.target
