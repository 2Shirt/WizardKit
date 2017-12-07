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
rm /root/.zlogin
chmod 700 /root

# Add wktech user
useradd -m -s /bin/zsh -G wheel -U wktech
echo "wktech:Abracadabra" | chpasswd

# Enable sudo for %wheel
echo '%wheel ALL=(ALL) ALL' >> /etc/sudoers

# Enable firewall
ufw enable

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

# Startup settings (from archiso)
systemctl enable pacman-init.service choose-mirror.service
systemctl enable NetworkManager.service
systemctl set-default multi-user.target
